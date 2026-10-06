"""
build_argo.py — RapidWatch REAL Argo float positions + latest profiles (Gulf of Mexico)
================================================================================
Pulls the ACTUAL recent Argo profiling-float locations from the Argo GDAC
ERDDAP (Ifremer) — no fake / "representative" fallback. If no floats are in the
box, the output is an empty FeatureCollection and the map shows nothing.

Since 2026-10-05 it also pulls each float's LATEST profile (pressure, temperature,
salinity, good-QC levels only) and stores it on the feature, together with the
near-surface values, the float-derived D26 (26 C isotherm depth) and the
mixed-layer depth, so the Live Sensor Systems tab can show the data behind the
marker. If a profile fetch fails for a float, that float keeps position only
(the page then says "profile unavailable") — nothing is invented.

Output: data/argo/argo_gulf.geojson  (one Point per float, at its latest fix)
Source: https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats
Run:    python build_argo.py   (re-runnable / refreshable)

Depth note: Argo reports pressure in decibars; 1 dbar is within ~2% of 1 m over
the upper 2000 m, and the page labels the axis "depth m (~dbar)".
"""
import json, csv, io, ssl, pathlib, time, urllib.request, urllib.error, datetime

DIR = pathlib.Path(__file__).parent
OUT = DIR / 'data' / 'argo' / 'argo_gulf.geojson'
OUT.parent.mkdir(parents=True, exist_ok=True)

LAT0, LAT1, LON0, LON1 = 18, 31, -98, -80      # Gulf box
DAYS = 45                                       # "recent" window
BASE = "https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.csv"
GOOD_QC = {'1', '2'}                            # Argo QC flags: 1 good, 2 probably good
SURF_M = 15.0                                   # near-surface cutoff for the surface readings
CTX = ssl.create_default_context()


class NoRows(Exception):
    """ERDDAP answers HTTP 404 when a query matches nothing (e.g. a cycle whose
    position is indexed but whose measurements have not arrived yet)."""


def fetch_csv(url, timeout=45, tries=3):
    """GET with retries: the Ifremer ERDDAP drops connections intermittently
    (WinError 10060 / timeouts seen 2026-10-05), and a 404 means 'no rows'."""
    last = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=timeout, context=CTX) as r:
                text = r.read().decode('utf-8')
            return list(csv.reader(io.StringIO(text)))[2:]     # skip names + units rows
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise NoRows(url)
            last = e
        except Exception as e:                                # timeouts, resets
            last = e
        time.sleep(3 * (attempt + 1))
    raise last


def fv(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def r3(x):
    return None if x is None else round(x, 3)


def bin_profile(levels):
    """levels: list of (pres, temp, psal). Bin 5 m to 300 m, then 20 m to the bottom."""
    if not levels:
        return None
    levels.sort(key=lambda a: a[0])
    bins = {}
    for p, t, s in levels:
        w = 5.0 if p <= 300 else 20.0
        key = round(p / w) * w
        bins.setdefault(key, []).append((t, s))
    depth, temp, sal = [], [], []
    for k in sorted(bins):
        ts = [a[0] for a in bins[k] if a[0] is not None]
        ss = [a[1] for a in bins[k] if a[1] is not None]
        depth.append(int(k) if float(k).is_integer() else k)
        temp.append(r3(sum(ts) / len(ts)) if ts else None)
        sal.append(r3(sum(ss) / len(ss)) if ss else None)
    return {"depth": depth, "temperature": temp, "salinity": sal}


def d26_of(profile):
    d, t = profile["depth"], profile["temperature"]
    for i in range(len(d) - 1):
        if t[i] is not None and t[i + 1] is not None and t[i] >= 26 and t[i + 1] < 26:
            f = (t[i] - 26) / (t[i] - t[i + 1])
            return round(d[i] + (d[i + 1] - d[i]) * f, 1)
    return None


def mld_of(profile):
    d, t = profile["depth"], profile["temperature"]
    surf = next((x for x in t if x is not None), None)
    if surf is None:
        return None
    for i in range(len(d)):
        if t[i] is not None and surf - t[i] >= 0.5:
            return d[i]
    return None


def fetch_profile(platform, cycle):
    """Latest cycle's good-QC levels for one float. Returns dict or None."""
    q = ("?time,pres,temp,psal,pres_qc,temp_qc,psal_qc"
         f"&platform_number=%22{platform}%22&cycle_number={int(cycle)}")
    rows = fetch_csv(BASE + q)
    levels, ptime = [], None
    for row in rows:
        if len(row) < 7:
            continue
        ptime = ptime or row[0]
        p, t, s = fv(row[1]), fv(row[2]), fv(row[3])
        pq, tq, sq = row[4].strip(), row[5].strip(), row[6].strip()
        if p is None or pq not in GOOD_QC:
            continue
        if tq not in GOOD_QC:
            t = None
        if sq not in GOOD_QC:
            s = None
        if t is None and s is None:
            continue
        levels.append((p, t, s))
    if len(levels) < 5:
        return None
    prof = bin_profile(levels)
    surf_t = [a[1] for a in levels if a[0] <= SURF_M and a[1] is not None]
    surf_s = [a[2] for a in levels if a[0] <= SURF_M and a[2] is not None]
    return {
        "profile_time": ptime,
        "profile": prof,
        "surface": {"temperature": r3(sum(surf_t) / len(surf_t)) if surf_t else None,
                    "salinity": r3(sum(surf_s) / len(surf_s)) if surf_s else None},
        "n_levels": len(levels),
        "maxDepth": round(max(a[0] for a in levels), 1),
        "d26": d26_of(prof),
        "mld": mld_of(prof),
    }


def main():
    start = (datetime.datetime.utcnow() - datetime.timedelta(days=DAYS)).strftime('%Y-%m-%dT00:00:00Z')
    q = ("?platform_number,latitude,longitude,time,cycle_number"
         f"&time%3E={start}"
         f"&latitude%3E={LAT0}&latitude%3C={LAT1}&longitude%3E={LON0}&longitude%3C={LON1}"
         "&orderByMax(%22platform_number,time%22)")      # server-side: latest row per float (2 s vs ~20 s)
    print("Fetching REAL Argo floats from the Argo GDAC ERDDAP ...")
    try:
        rows = fetch_csv(BASE + q)
    except Exception as e:
        print("  ERDDAP fetch failed:", e)
        # honest empty output — never fabricate
        OUT.write_text(json.dumps({"type": "FeatureCollection", "features": []}), encoding='utf-8')
        return

    latest = {}
    for row in rows:
        if len(row) < 4:
            continue
        pf = row[0]
        try:
            la, lo = float(row[1]), float(row[2])
        except ValueError:
            continue
        t = row[3]
        if pf not in latest or t > latest[pf]['t']:
            latest[pf] = {'la': la, 'lo': lo, 't': t, 'cyc': row[4] if len(row) > 4 else ''}

    feats = []
    got, missed = 0, 0
    for pf, d in latest.items():
        props = {"platform": pf, "time": d['t'], "cycle": d['cyc']}
        prof, used_cycle = None, None
        # latest cycle first; if its measurements are not on the server yet (404 = no rows),
        # fall back once to the previous cycle so the float still shows a real profile
        for cyc in ([int(d['cyc']), int(d['cyc']) - 1] if d['cyc'].strip().lstrip('-').isdigit() else []):
            try:
                prof = fetch_profile(pf, cyc)
            except NoRows:
                print(f"  float {pf} cycle {cyc}: no measurement rows yet")
                continue
            except Exception as e:
                print(f"  profile fetch failed for float {pf} cycle {cyc}: {e}")
                break
            if prof:
                used_cycle = cyc
                break
        if prof:
            props.update(prof)
            props["profile_cycle"] = used_cycle
            got += 1
        else:
            missed += 1
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(d['lo'], 4), round(d['la'], 4)]},
            "properties": props,
        })

    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats}), encoding='utf-8')
    print(f"{len(feats)} REAL Argo floats in the Gulf (last {DAYS} d); profiles for {got}, "
          f"position-only {missed}  ->  {OUT}")
    for f in feats[:10]:
        p = f['properties']
        extra = (f"  {p['n_levels']} levels to {p['maxDepth']} m, surf T {p['surface']['temperature']}, "
                 f"D26 {p['d26']}") if 'profile' in p else "  (profile unavailable)"
        print(f"  float {p['platform']}  @ {f['geometry']['coordinates']}  cycle {p['cycle']}  {p['time'][:10]}{extra}")


if __name__ == "__main__":
    main()
