"""
check_health.py — backend health check for the RapidWatch live site
================================================================================
Runs in the 30-min "Refresh live data" Action after the snapshots and the storm
archive are built, and locally at the start of a work session. It looks at the
files the bots have ALREADY written and answers one question: is anything stale,
missing or malformed right now? The result goes to data/health.json, which the
Live Event page reads into its DATA STATUS panel as the "Backend health" row, so
a problem is visible on the public site the day it starts.

Why it exists (2026-11-03): three bugs sat on the public site for weeks before a
person noticed them — Pacific storms archived under unreadable 'adv00?' file
names, the buoy row stuck at 0/6 fresh because one feed lagged, and a buoy popup
with no temperatures. Each would have turned this row yellow or red within 30
minutes of starting.

Checks (state ok / warn / fail, each with a one-line detail):
  filenames      every path under data/storms is portable (no ? * : < > " | or
                 trailing dot/space) and every per-advisory GIS file carries a
                 numeric advisory number
  storm-archive  every storm NHC lists as active (AL/EP/CP) has a folder; every
                 storm archived in the last 36 h (not STOPPED) has text
                 advisories and an ATCF best track
  ndbc-buoys     each buoy snapshot has an observation < 3 h old (warn < 6 h)
                 and an air/sea temperature within 3 h of it; 42040 is known
                 offline since 2026-06-17 and only warns
  nws-lag        api.weather.gov vs the NDBC snapshot for one buoy — the page
                 now uses the newer of the two, so this is informational: warn
                 when NWS trails by more than 3 h (network; warn if unreachable)
  ocean-state    HYCOM SST grid time_utc age: ok < 9 h, warn < 30 h, else fail
                 (the 6-h HYCOM job fails on their server about half the time)
  gliders        newest glider fix: ok < 24 h, warn < 48 h, else fail
  argo           newest Argo profile: ok < 15 d, warn < 30 d, else fail

Exit code is always 0 — health is reported, never allowed to block the data
commit. data/health.json is rewritten only when a check changes or the file is
more than an hour old, so quiet runs do not create commits by themselves.

Run: python check_health.py            (add --no-network to skip the NWS probe)
"""
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.request

DIR = pathlib.Path(__file__).parent
DATA = DIR / "data"
OUT = DATA / "health.json"
BUOYS = ["42001", "42002", "42036", "42039", "42040", "42055"]     # same list as build_live_data.py
KNOWN_OFFLINE = {"42040": "offline since 2026-06-17"}
H = 3600.0

now = dt.datetime.now(dt.timezone.utc)
checks = []


def add(name, state, detail):
    checks.append({"name": name, "state": state, "detail": detail})


def age_h(t):
    """Hours between now and t (aware datetime)."""
    return (now - t).total_seconds() / H


def parse_iso(s):
    s = str(s).strip().replace(" ", "T")
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    t = dt.datetime.fromisoformat(s)
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def fmt_age(h):
    return f"{h*60:.0f} min" if h < 1 else (f"{h:.1f} h" if h < 48 else f"{h/24:.1f} d")


# ── 1. file names ────────────────────────────────────────────────────────────
def check_filenames():
    bad, badadv = [], []
    storms = DATA / "storms"
    if not storms.exists():
        add("filenames", "ok", "no storm archive yet")
        return
    for p in storms.rglob("*"):
        rel = p.relative_to(storms).as_posix()
        if re.search(r'[?*:<>"|]', rel) or any(part.endswith((" ", ".")) for part in rel.split("/")):
            bad.append(rel)
        # advNNN_ or, for NHC intermediate advisories, advNNA_ (e.g. adv05A = advisory 5A)
        if p.parent.name == "gis" and p.name.startswith("adv") and not re.match(r"adv\d{2,3}[A-Za-z]?_", p.name):
            badadv.append(rel)
    if bad:
        add("filenames", "fail", f"{len(bad)} unportable path(s), e.g. {bad[0]}")
    elif badadv:
        add("filenames", "fail", f"{len(badadv)} GIS file(s) without a numeric advisory, e.g. {badadv[0]}")
    else:
        add("filenames", "ok", "all storm-archive paths portable")


# ── 2. storm archive completeness ────────────────────────────────────────────
def check_storm_archive():
    storms = DATA / "storms"
    problems = []
    active_ids = []
    try:
        cs = json.loads((DATA / "nhc_currentstorms.json").read_text())
        active_ids = [str(s.get("id", "")).upper() for s in cs.get("activeStorms", [])
                      if str(s.get("id", "")).upper().startswith(("AL", "EP", "CP"))]
    except Exception as e:
        problems.append(f"nhc_currentstorms.json unreadable ({type(e).__name__})")
    for sid in active_ids:
        if not (storms / sid).exists():
            problems.append(f"{sid} active but not archived")
    recent = 0
    if storms.exists():
        for d in sorted(p for p in storms.iterdir() if p.is_dir()):
            if (d / "STOPPED").exists():
                continue
            runs = sorted((d / "currentstorms").glob("*.json")) if (d / "currentstorms").exists() else []
            if not runs:
                continue
            try:
                last = dt.datetime.strptime(runs[-1].stem, "%Y%m%dT%H%M").replace(tzinfo=dt.timezone.utc)
            except ValueError:
                continue
            if age_h(last) > 36:
                continue
            recent += 1
            if not any((d / "advisories").glob("*.txt")):
                problems.append(f"{d.name}: no text advisories")
            if not any((d / "atcf").glob("b*.dat")):
                problems.append(f"{d.name}: no ATCF best track")
    if problems:
        add("storm-archive", "fail", "; ".join(problems[:3]))
    else:
        add("storm-archive", "ok", f"{len(active_ids)} active storm(s), {recent} archived in last 36 h" if active_ids or recent
            else "no active storms")


# ── 3. NDBC buoy snapshots ───────────────────────────────────────────────────
def read_ndbc(bid):
    rows = []
    for line in (DATA / "ndbc" / f"{bid}.txt").read_text(errors="replace").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        f = line.split()
        if len(f) < 15:
            continue
        t = dt.datetime(int(f[0]), int(f[1]), int(f[2]), int(f[3]), int(f[4]), tzinfo=dt.timezone.utc)
        rows.append((t, f))
    return rows


def check_buoys():
    fresh, warn, fail = 0, [], []
    newest_obs = None
    for bid in BUOYS:
        try:
            rows = read_ndbc(bid)
        except Exception as e:
            fail.append(f"{bid} unreadable ({type(e).__name__})")
            continue
        if not rows:
            fail.append(f"{bid} empty")
            continue
        t0 = rows[0][0]
        a = age_h(t0)
        if bid in KNOWN_OFFLINE and a > 6:
            warn.append(f"{bid} {KNOWN_OFFLINE[bid]}")
            continue
        if a > 6:
            fail.append(f"{bid} newest obs {fmt_age(a)} old")
            continue
        if a > 3:                                    # NDBC itself can post 1-2 h late; the snapshot adds up to 30 min
            warn.append(f"{bid} obs {fmt_age(a)} old")
        # a temperature (air col 13 or water col 14) within 3 h of the newest row
        has_temp = any((f[13] != "MM" or f[14] != "MM") and (t0 - t).total_seconds() <= 3 * H for t, f in rows)
        if not has_temp:
            warn.append(f"{bid} no temperature in last 3 h")
        fresh += 1
        if newest_obs is None or t0 > newest_obs:
            newest_obs = t0
    state = "fail" if fail else ("warn" if warn else "ok")
    detail = f"{fresh}/{len(BUOYS)} fresh"
    if newest_obs:
        detail += f" · newest {fmt_age(age_h(newest_obs))} ago"
    if fail or warn:
        detail += " · " + "; ".join((fail + warn)[:3])
    add("ndbc-buoys", state, detail)
    return newest_obs


# ── 4. NWS API lag (informational) ───────────────────────────────────────────
def check_nws_lag(ndbc_newest, network=True):
    if not network:
        add("nws-lag", "ok", "skipped (--no-network)")
        return
    bid = "42001"
    try:
        req = urllib.request.Request(f"https://api.weather.gov/stations/{bid}/observations/latest",
                                     headers={"User-Agent": "RapidWatch health check (+https://github.com/aphilp1/rapidwatch)",
                                              "Accept": "application/geo+json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            ts = parse_iso(json.load(r)["properties"]["timestamp"])
    except Exception as e:
        add("nws-lag", "warn", f"api.weather.gov unreachable ({type(e).__name__})")
        return
    try:
        nd = read_ndbc(bid)[0][0]
    except Exception:
        nd = ndbc_newest
    if nd is None:
        add("nws-lag", "warn", f"NWS {fmt_age(age_h(ts))} old; no NDBC row to compare")
        return
    lag = (nd - ts).total_seconds() / H
    if lag > 3:
        add("nws-lag", "warn", f"NWS trails NDBC by {fmt_age(lag)} on {bid} (page uses the newer feed)")
    else:
        add("nws-lag", "ok", f"NWS within {fmt_age(abs(lag))} of NDBC on {bid}")


# ── 5-7. ocean state, gliders, Argo ──────────────────────────────────────────
def check_aged(name, newest, ok_h, warn_h, label):
    if newest is None:
        add(name, "fail", f"no {label} time found")
        return
    a = age_h(newest)
    state = "ok" if a < ok_h else ("warn" if a < warn_h else "fail")
    add(name, state, f"newest {label} {fmt_age(a)} ago")


def check_ocean():
    try:
        t = parse_iso(json.loads((DATA / "ocean" / "hycom_sst.json").read_text())["time_utc"])
    except Exception as e:
        add("ocean-state", "fail", f"hycom_sst.json unreadable ({type(e).__name__})")
        return
    check_aged("ocean-state", t, 9, 30, "HYCOM grid")


def check_gliders():
    try:
        g = json.loads((DATA / "gliders" / "gliders_gulf.geojson").read_text())
        times = [parse_iso(f["properties"]["time"]) for f in g["features"]
                 if f["properties"].get("kind") == "now" and f["properties"].get("time")]
    except Exception as e:
        add("gliders", "fail", f"gliders_gulf.geojson unreadable ({type(e).__name__})")
        return
    check_aged("gliders", max(times) if times else None, 24, 48, "glider fix")


def check_argo():
    try:
        g = json.loads((DATA / "argo" / "argo_gulf.geojson").read_text())
        times = [parse_iso(f["properties"]["time"]) for f in g["features"] if f["properties"].get("time")]
    except Exception as e:
        add("argo", "fail", f"argo_gulf.geojson unreadable ({type(e).__name__})")
        return
    check_aged("argo", max(times) if times else None, 15 * 24, 30 * 24, "Argo profile")


# ── run + write ──────────────────────────────────────────────────────────────
def main():
    network = "--no-network" not in sys.argv
    check_filenames()
    check_storm_archive()
    newest = check_buoys()
    check_nws_lag(newest, network)
    check_ocean()
    check_gliders()
    check_argo()

    rank = {"ok": 0, "warn": 1, "fail": 2}
    overall = max((c["state"] for c in checks), key=lambda s: rank[s])
    result = {"generated_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "overall": overall, "checks": checks}

    for c in checks:
        print(f"  {c['state']:4}  {c['name']:14} {c['detail']}")
    print(f"overall: {overall}")

    # rewrite only when something changed or the file is > 1 h old, so quiet runs add no commits
    write = True
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text())
            same = prev.get("checks") == checks
            fresh = age_h(parse_iso(prev["generated_utc"])) < 1
            write = not (same and fresh)
        except Exception:
            write = True
    if write:
        OUT.write_text(json.dumps(result, indent=1) + "\n")
        print(f"wrote {OUT.relative_to(DIR).as_posix()}")
    else:
        print("health unchanged, file kept")
    return 0


if __name__ == "__main__":
    sys.exit(main())
