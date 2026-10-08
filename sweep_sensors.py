"""
sweep_sensors.py — record EVERY sensor along an active storm's track, every run
================================================================================
Written 2026-10-08 for Hurricane Isaias (AL092026) after the nearest-sensor design
proved too thin. Called by track_storm.py each run (hourly from the live-data Action);
also runs by hand:  python sweep_sensors.py AL092026

The track = NHC best track so far (ATCF b-deck in this archive) + current advisory
position + the latest forecast points. A sensor is "along the track" when it lies
within CORRIDOR_KM of any segment of that track, or within CENTER_KM of the current
center. Everything inside is recorded, not only the nearest.

Output root: data/storms/<STORMID>/sensors/
  stations.csv                  every NDBC station in the corridor: id, name, lat, lon, type,
                                owner, distance to track (km), distance to center (km), files held
  ndbc/<station>.txt.csv        standard met observations (wind, gust, waves, pressure, air/water
                                temperature, dew point, pressure tendency), every row since the
                                storm started, merged each run from NDBC's 45-day real-time file
  ndbc/<station>.spec.csv       spectral wave summary        (only where NDBC serves it)
  ndbc/<station>.cwind.csv      continuous winds             (only where NDBC serves it)
  ndbc/<station>.ocean.csv      ocean (water temperature/salinity at depth) (only where served)
  argo.csv                      one row per float profile inside the corridor (platform, time,
                                position, surface T/S, D26, MLD, distances); profile curves in
                                argo_profiles/<platform>_<cycle>.json
  gliders.csv                   one row per glider report inside the corridor (same idea);
                                profile curves in glider_profiles/<id>_<time>.json
  hycom_track.csv               HYCOM SST / D26 / current sampled at EVERY track point (past
                                6-hourly fixes, current center, forecast points) each run
  sst_mur.csv                   satellite SST (MUR 1 km analysis, NOAA CoastWatch ERDDAP) at the
                                current center and every forecast point, each run
  SENSOR_LOG.md                 one entry per run: counts, what was new, buoys nearest the center
                                with their latest observation

Nothing is estimated. Every value is copied from the source named in the file.
"""
import csv, datetime, json, math, pathlib, re, sys, urllib.request, urllib.error

DIR = pathlib.Path(__file__).resolve().parent
DATA = DIR / "data"
UA = {"User-Agent": "RapidWatch storm sensor sweep (aphilp1@gmail.com)"}
CORRIDOR_KM = 300.0        # either side of the track line (past + forecast)
CENTER_KM = 500.0          # disk around the current center
NDBC_RT = "https://www.ndbc.noaa.gov/data/realtime2/"
NDBC_STATIONS = "https://www.ndbc.noaa.gov/activestations.xml"
NDBC_TYPES = ["txt", "spec", "cwind", "ocean"]
MUR = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.csv"


def get(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def km(la1, lo1, la2, lo2):
    """Great-circle distance in km."""
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = math.radians(la2 - la1), math.radians(lo2 - lo1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def dist_to_segment(la, lo, a, b):
    """Distance (km) from a point to the segment a-b, in a local equirectangular frame."""
    k = math.cos(math.radians((a[0] + b[0]) / 2))
    px, py = (lo - a[1]) * 111 * k, (la - a[0]) * 111
    bx, by = (b[1] - a[1]) * 111 * k, (b[0] - a[0]) * 111
    L2 = bx * bx + by * by
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, (px * bx + py * by) / L2))
    return math.hypot(px - t * bx, py - t * by)


def dist_to_track(la, lo, track):
    if len(track) == 1:
        return km(la, lo, track[0][0], track[0][1])
    return min(dist_to_segment(la, lo, track[i], track[i + 1]) for i in range(len(track) - 1))


# ---------------------------------------------------------------- track
def bdeck_points(root, sid):
    """Best-track fixes from the archived ATCF b-deck: list of (lat, lon, 'YYYYMMDDHH', vmax, mslp)."""
    out, seen = [], set()
    p = root / "atcf" / f"b{sid.lower()}.dat"
    if not p.exists():
        return out
    for line in p.read_text(errors="replace").splitlines():
        f = [x.strip() for x in line.split(",")]
        if len(f) < 9 or f[4] != "BEST":
            continue
        dtg = f[2]
        if dtg in seen:
            continue
        seen.add(dtg)
        la = int(f[6][:-1]) / 10 * (1 if f[6].endswith("N") else -1)
        lo = int(f[7][:-1]) / 10 * (-1 if f[7].endswith("W") else 1)
        out.append((la, lo, dtg, f[8], f[9] if len(f) > 9 else ""))
    return out


def forecast_points(root):
    """Latest archived forecast points: list of (lat, lon, tau_h, validtime, maxwind)."""
    files = sorted((root / "gis").glob("adv*_points.geojson"), key=lambda p: p.stat().st_mtime)
    files = [p for p in files if "past" not in p.name]
    if not files:
        return [], ""
    # newest advisory number wins (names are adv007A_points, adv008_points ...)
    def advkey(p):
        m = re.match(r"adv(\d+)([A-Z]?)_", p.name)
        return (int(m.group(1)), m.group(2)) if m else (0, "")
    best = max(files, key=advkey)
    g = json.loads(best.read_text(encoding="utf-8"))
    pts = []
    for f in g.get("features", []):
        pr = f.get("properties", {})
        c = f["geometry"]["coordinates"]
        try:
            tau = int(pr.get("tau", 0))
        except Exception:
            tau = 0
        pts.append((round(c[1], 2), round(c[0], 2), tau, pr.get("validtime", ""), pr.get("maxwind", "")))
    pts.sort(key=lambda x: x[2])
    return pts, best.name


# ---------------------------------------------------------------- NDBC
def ndbc_stations():
    x = get(NDBC_STATIONS).decode("utf-8", "replace")
    out = []
    for m in re.finditer(r"<station ([^>]*)/>", x):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        try:
            out.append({"id": a["id"], "name": a.get("name", ""), "lat": float(a["lat"]), "lon": float(a["lon"]),
                        "type": a.get("type", ""), "owner": a.get("owner", ""), "pgm": a.get("pgm", ""),
                        "met": a.get("met", ""), "currents": a.get("currents", ""), "waterquality": a.get("waterquality", "")})
        except (KeyError, ValueError):
            pass
    return out


def parse_ndbc(text):
    """NDBC real-time text -> (header fields, rows as dicts with 'time_utc' first). Rows newest-first in source."""
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) < 2 or not lines[0].startswith("#"):
        return None, []
    hdr = lines[0].lstrip("#").split()
    units = lines[1].lstrip("#").split() if lines[1].startswith("#") else []
    rows = []
    for l in lines[2:] if units else lines[1:]:
        f = l.split()
        if len(f) < 5:
            continue
        try:
            t = f"{int(f[0]):04d}-{int(f[1]):02d}-{int(f[2]):02d}T{int(f[3]):02d}:{int(f[4]):02d}Z"
        except ValueError:
            continue
        row = {"time_utc": t}
        for k, v in zip(hdr[5:], f[5:]):
            row[k] = "" if v == "MM" else v
        rows.append(row)
    return (["time_utc"] + hdr[5:], rows)


def merge_csv(path, fields, rows, key="time_utc", since=None):
    """Union-merge rows into a CSV keyed on `key`; keeps every old row; returns number of new rows."""
    old = {}
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            rd = csv.DictReader(f)
            for r in rd:
                old[r[key]] = r
            fields = list(dict.fromkeys(list(rd.fieldnames or []) + list(fields)))
    new = 0
    for r in rows:
        if since and r[key] < since:
            continue
        if r[key] not in old:
            new += 1
        merged = {**old.get(r[key], {}), **r}
        if old.get(r[key], {}).get("first_seen_run"):
            merged["first_seen_run"] = old[r[key]]["first_seen_run"]
        old[r[key]] = merged
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for k in sorted(old):
            w.writerow({c: old[k].get(c, "") for c in fields})
    return new


def sweep_ndbc(out, track, center, since, missing, run_ts):
    stations = ndbc_stations()
    inside = []
    for s in stations:
        dt = dist_to_track(s["lat"], s["lon"], track)
        dc = km(s["lat"], s["lon"], center[0], center[1])
        if dt <= CORRIDOR_KM or dc <= CENTER_KM:
            s["dist_track_km"] = round(dt); s["dist_center_km"] = round(dc)
            inside.append(s)
    inside.sort(key=lambda s: s["dist_center_km"])
    new_rows, held, latest = 0, {}, {}
    for s in inside:
        files = []
        for ext in NDBC_TYPES:
            tag = f"{s['id'].upper()}.{ext}"          # NDBC real-time files are named by UPPERCASE station id
            if tag in missing and (run_ts[:8] == missing[tag][:8]):
                continue                                # 404'd today already; retried tomorrow
            try:
                txt = get(f"{NDBC_RT}{tag}", timeout=30).decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    missing[tag] = run_ts
                continue
            except Exception:
                continue
            fields, rows = parse_ndbc(txt)
            if not fields:
                continue
            n = merge_csv(out / "ndbc" / f"{tag}.csv", fields, rows, since=since)
            new_rows += n
            files.append(ext)
            if ext == "txt" and rows:
                latest[s["id"]] = rows[0]
        held[s["id"]] = files
    with open(out / "stations.csv", "w", newline="", encoding="utf-8") as f:
        cols = ["id", "name", "lat", "lon", "type", "owner", "pgm", "met", "currents", "waterquality",
                "dist_track_km", "dist_center_km", "files"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for s in inside:
            w.writerow({**s, "files": " ".join(held.get(s["id"], []))})
    return inside, new_rows, latest


# ---------------------------------------------------------------- Argo / gliders
def load_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def sweep_argo(out, track, center, run_ts):
    g = load_json(DATA / "argo" / "argo_gulf.geojson") or {"features": []}
    rows, newp = [], 0
    for f in g["features"]:
        if f["geometry"]["type"] != "Point":
            continue
        lo, la = f["geometry"]["coordinates"][:2]
        p = f["properties"]
        dt = dist_to_track(la, lo, track); dc = km(la, lo, center[0], center[1])
        if dt > CORRIDOR_KM and dc > CENTER_KM:
            continue
        surf = p.get("surface") or {}
        pt = p.get("profile_time") or p.get("time") or ""
        rows.append({"platform": p.get("platform"), "profile_time": pt, "cycle": p.get("profile_cycle", p.get("cycle")),
                     "lat": round(la, 3), "lon": round(lo, 3), "surface_t_c": surf.get("temperature"),
                     "surface_s_psu": surf.get("salinity"), "d26_m": p.get("d26"), "mld_m": p.get("mld"),
                     "max_depth_m": p.get("maxDepth"), "n_levels": p.get("n_levels"),
                     "dist_track_km": round(dt), "dist_center_km": round(dc), "first_seen_run": run_ts})
        if "profile" in p:
            pp = out / "argo_profiles" / f"{p.get('platform')}_{p.get('profile_cycle', p.get('cycle'))}.json"
            if not pp.exists():
                pp.parent.mkdir(parents=True, exist_ok=True)
                pp.write_text(json.dumps({"platform": p.get("platform"), "time": pt, "lat": la, "lon": lo,
                                          "profile": p["profile"]}), encoding="utf-8")
                newp += 1
    fields = ["platform", "profile_time", "cycle", "lat", "lon", "surface_t_c", "surface_s_psu", "d26_m", "mld_m",
              "max_depth_m", "n_levels", "dist_track_km", "dist_center_km", "first_seen_run"]
    for r in rows:
        r["key"] = f"{r['platform']}|{r['profile_time']}"
    n = merge_csv(out / "argo.csv", ["key"] + fields, rows, key="key")
    return len(rows), n, newp


def sweep_gliders(out, track, center, run_ts):
    g = load_json(DATA / "gliders" / "gliders_gulf.geojson") or {"features": []}
    rows, newp = [], 0
    for f in g["features"]:
        p = f["properties"]
        if p.get("kind") != "now" or f["geometry"]["type"] != "Point":
            continue
        lo, la = f["geometry"]["coordinates"][:2]
        dt = dist_to_track(la, lo, track); dc = km(la, lo, center[0], center[1])
        if dt > CORRIDOR_KM and dc > CENTER_KM:
            continue
        surf = p.get("surface") or {}
        rows.append({"glider": p.get("id"), "time": p.get("time"), "operator": p.get("operator"), "dataset": p.get("dataset"),
                     "lat": round(la, 3), "lon": round(lo, 3), "surface_t_c": surf.get("temperature"),
                     "surface_s_psu": surf.get("salinity"), "surface_density": surf.get("density"),
                     "max_depth_m": p.get("maxDepth"), "dist_track_km": round(dt), "dist_center_km": round(dc),
                     "first_seen_run": run_ts})
        if "profile" in p:
            safe = re.sub(r"[^0-9A-Za-z]", "", str(p.get("time")))
            pp = out / "glider_profiles" / f"{p.get('id')}_{safe}.json"
            if not pp.exists():
                pp.parent.mkdir(parents=True, exist_ok=True)
                pp.write_text(json.dumps({"glider": p.get("id"), "time": p.get("time"), "lat": la, "lon": lo,
                                          "profile": p["profile"]}), encoding="utf-8")
                newp += 1
    fields = ["glider", "time", "operator", "dataset", "lat", "lon", "surface_t_c", "surface_s_psu", "surface_density",
              "max_depth_m", "dist_track_km", "dist_center_km", "first_seen_run"]
    for r in rows:
        r["key"] = f"{r['glider']}|{r['time']}"
    n = merge_csv(out / "gliders.csv", ["key"] + fields, rows, key="key")
    return len(rows), n, newp


# ---------------------------------------------------------------- HYCOM + MUR along the track
def sample(grid, key, la, lo):
    if not grid:
        return ""
    lats, lons, g = grid["lats"], grid["lons"], grid[key]
    ri = min(range(len(lats)), key=lambda i: abs(lats[i] - la))
    ci = min(range(len(lons)), key=lambda i: abs(lons[i] - lo))
    v = g[ri][ci]
    return "" if v is None else v


def sweep_hycom(out, past, center_row, fc, run_ts):
    sst = load_json(DATA / "ocean" / "hycom_sst.json"); d26 = load_json(DATA / "ocean" / "hycom_d26.json")
    cur = load_json(DATA / "ocean" / "hycom_currents.json")
    ht = (sst or {}).get("time_utc", "")
    rows = []
    def add(kind, label, la, lo, vmax):
        u, v = sample(cur, "u", la, lo), sample(cur, "v", la, lo)
        spd = round(math.hypot(u, v), 2) if u != "" and v != "" else ""
        rows.append({"key": f"{run_ts}|{kind}|{label}", "run_utc": run_ts, "point": kind, "label": label,
                     "lat": la, "lon": lo, "vmax_kt": vmax, "hycom_time": ht,
                     "sst_c": sample(sst, "sst", la, lo), "d26_m": sample(d26, "d26", la, lo), "current_ms": spd})
    for la, lo, dtg, vmax, _ in past:
        add("best_track", dtg, la, lo, vmax)
    add("center", center_row[2], center_row[0], center_row[1], center_row[3])
    for la, lo, tau, vt, mw in fc:
        add("forecast", f"+{tau}h {vt}", la, lo, mw)
    fields = ["key", "run_utc", "point", "label", "lat", "lon", "vmax_kt", "hycom_time", "sst_c", "d26_m", "current_ms"]
    merge_csv(out / "hycom_track.csv", fields, rows, key="key")
    return len(rows)


def mur_point(la, lo):
    url = f"{MUR}?analysed_sst%5B(last)%5D%5B({la})%5D%5B({lo})%5D"
    try:
        txt = get(url, timeout=40).decode("utf-8", "replace").strip().splitlines()
        t, y, x, v = txt[-1].split(",")
        fv = float(v)
        return t, ("" if math.isnan(fv) else fv)
    except Exception:
        return "", ""


def sweep_mur(out, center_row, fc, run_ts):
    rows = []
    t, v = mur_point(center_row[0], center_row[1])
    rows.append({"key": f"{run_ts}|center", "run_utc": run_ts, "point": "center", "label": center_row[2],
                 "lat": center_row[0], "lon": center_row[1], "mur_time": t, "sst_c": v})
    for la, lo, tau, vt, mw in fc:
        t, v = mur_point(la, lo)
        rows.append({"key": f"{run_ts}|forecast|{tau}", "run_utc": run_ts, "point": "forecast", "label": f"+{tau}h {vt}",
                     "lat": la, "lon": lo, "mur_time": t, "sst_c": v})
    fields = ["key", "run_utc", "point", "label", "lat", "lon", "mur_time", "sst_c"]
    merge_csv(out / "sst_mur.csv", fields, rows, key="key")
    return sum(1 for r in rows if r["sst_c"] != "")


# ---------------------------------------------------------------- driver
def run(sid, s, root, run_ts=None):
    """s = NHC CurrentStorms entry for the storm. Returns a summary string for the archive log."""
    run_ts = run_ts or utcnow().strftime("%Y%m%dT%H%M")
    out = root / "sensors"
    out.mkdir(parents=True, exist_ok=True)
    la, lo = float(s["latitudeNumeric"]), float(s["longitudeNumeric"])
    past = bdeck_points(root, sid)
    fc, fc_file = forecast_points(root)
    track = [(p[0], p[1]) for p in past] + [(la, lo)] + [(p[0], p[1]) for p in fc]
    since = ""
    if past:
        d = past[0][2]
        since = f"{d[:4]}-{d[4:6]}-{d[6:8]}T00:00Z"        # first best-track day, 00Z
    center_row = (la, lo, s.get("lastUpdate", ""), s.get("intensity", ""))

    missing_p = out / "_ndbc_missing.json"
    missing = load_json(missing_p) or {}
    if not isinstance(missing, dict):
        missing = {}
    stations, new_obs, latest = sweep_ndbc(out, track, (la, lo), since, missing, run_ts)
    missing_p.write_text(json.dumps(missing, sort_keys=True), encoding="utf-8")
    n_argo, new_argo, new_argo_prof = sweep_argo(out, track, (la, lo), run_ts)
    n_gl, new_gl, new_gl_prof = sweep_gliders(out, track, (la, lo), run_ts)
    n_hy = sweep_hycom(out, past, center_row, fc, run_ts)
    n_mur = sweep_mur(out, center_row, fc, run_ts)

    # log entry
    logp = out / "SENSOR_LOG.md"
    if not logp.exists():
        logp.write_text(
            f"# {s.get('name')} ({sid}) — sensor sweep log\n\n"
            f"One entry per run (UTC). Corridor: {CORRIDOR_KM:.0f} km either side of the best track + current center + "
            f"latest forecast points, or {CENTER_KM:.0f} km from the current center. Files beside this log hold every "
            f"observation; this log only summarizes each run.\n\n", encoding="utf-8")
    near = [st for st in stations if st["id"] in latest][:6]
    lines = [f"## {run_ts} UTC · center {la:.1f}N {abs(lo):.1f}W · {s.get('classification')} {s.get('intensity')} kt · forecast file {fc_file or 'none'}",
             f"- Track points: {len(past)} best-track + center + {len(fc)} forecast. Corridor stations: {len(stations)} "
             f"({sum(1 for st in stations if st['id'] in latest)} reporting standard met). New NDBC observation rows merged: {new_obs}.",
             f"- Argo floats in corridor: {n_argo} ({new_argo} new profiles, {new_argo_prof} profile files written). "
             f"Gliders in corridor: {n_gl} ({new_gl} new reports, {new_gl_prof} profile files written).",
             f"- HYCOM sampled at {n_hy} track points; MUR satellite SST returned at {n_mur} of {1 + len(fc)} points.",
             "- Nearest reporting buoys/stations (latest standard-met row):"]
    for st in near:
        r = latest[st["id"]]
        lines.append(f"  - {st['id']} {st['name']} · {st['dist_center_km']} km from center · {r['time_utc']} · "
                     f"wind {r.get('WDIR','')}° {r.get('WSPD','')} m/s gust {r.get('GST','')} · pres {r.get('PRES','')} hPa · "
                     f"air {r.get('ATMP','')} °C · water {r.get('WTMP','')} °C · wave {r.get('WVHT','')} m")
    with open(logp, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n\n")
    summary = (f"sensors: {len(stations)} stations/{new_obs} new obs, argo {n_argo}/{new_argo} new, "
               f"gliders {n_gl}/{new_gl} new, hycom {n_hy} pts, mur {n_mur} pts")
    print(summary)
    return summary


def main(only=None):
    cs = json.loads(get("https://www.nhc.noaa.gov/CurrentStorms.json"))
    storms = [s for s in cs.get("activeStorms", []) if str(s.get("id", "")).upper().startswith("AL")]
    if only:
        storms = [s for s in storms if str(s.get("id", "")).upper() == only.upper()]
    if not storms:
        print("no matching active Atlantic storm"); return
    for s in storms:
        sid = str(s["id"]).upper()
        root = DATA / "storms" / sid
        if not root.exists():
            print(f"{sid}: no archive folder yet (run track_storm.py first)"); continue
        run(sid, s, root)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
