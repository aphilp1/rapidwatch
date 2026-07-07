"""
build_gliders.py — RapidWatch "Live Sensor Systems"
================================================================================
Fetch the active Gulf-of-Mexico Slocum glider missions from the IOOS National
Glider Data Assembly Center (ERDDAP) and emit ONE compact GeoJSON the map reads.

Per glider it writes two features:
  - a "track"  LineString (subsampled path) with per-vertex NEAR-SURFACE values
    of all four variables, so the map can colour the track by any of them;
  - a "now"    Point at the latest position, with the latest surface readings,
    dive stats, and the most-recent depth profile (depth vs the four variables).

Variables: temperature (C), salinity, density (kg/m3), electrical conductivity (S/m).
Source: https://gliders.ioos.us/erddap  (IOOS National Glider DAC)

Run:  python build_gliders.py
Refreshable — re-run any time to pull the latest fixes.
"""
import json, csv, io, ssl, pathlib, urllib.request

DIR = pathlib.Path(__file__).parent
OUT = DIR / 'data' / 'gliders' / 'gliders_gulf.geojson'
OUT.parent.mkdir(parents=True, exist_ok=True)

ERDDAP = ("https://gliders.ioos.us/erddap/tabledap/{id}.csv"
          "?time,latitude,longitude,depth,temperature,salinity,density,conductivity")

# The three active Gulf Slocum missions (discovered from the DAC allDatasets catalog).
GLIDERS = [
    {"id": "ng1260-20260626T0000",     "name": "ng1260",   "operator": "US Navy (NAVOCEANO)",      "color": "#ff8a3d"},
    {"id": "usf-stella-20260626T0000", "name": "stella",    "operator": "Univ. of South Florida",   "color": "#46cfd6"},
    {"id": "unit_541-20260630T0000",   "name": "unit_541",  "operator": "Texas A&M University",      "color": "#c98bff"},
]
VARS   = ["temperature", "salinity", "density", "conductivity"]
NBINS  = 300      # track vertices (subsample the dense profile stream)
SURF_M = 15.0     # "near surface" depth cutoff (m) for track colouring / surface readings

_CTX = ssl.create_default_context()

def fetch_rows(gid):
    with urllib.request.urlopen(ERDDAP.format(id=gid), timeout=240, context=_CTX) as r:
        text = r.read().decode('utf-8')
    rows = list(csv.reader(io.StringIO(text)))
    out = []
    for row in rows[2:]:                       # rows[0]=names, rows[1]=units
        if len(row) < 8:
            continue
        def fv(x):
            try:
                v = float(x)
                return None if v != v else v      # v != v  ->  NaN
            except (ValueError, TypeError):
                return None
        la, lo, dp = fv(row[1]), fv(row[2]), fv(row[3])
        if la is None or lo is None:
            continue
        out.append({"t": row[0], "la": la, "lo": lo, "dp": dp,
                    "temperature": fv(row[4]), "salinity": fv(row[5]),
                    "density": fv(row[6]), "conductivity": fv(row[7])})
    out.sort(key=lambda r: r["t"])
    return out

def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None

def r3(x):
    return round(x, 3) if x is not None else None

def shallowest(rows, frac=0.2):
    """The shallowest fraction of a set of fixes — robust 'near surface' sample
    even when a bin lands mid-dive (avoids deep values leaking into surface stats)."""
    rr = sorted((r for r in rows if r["dp"] is not None), key=lambda r: r["dp"])
    if not rr:
        return rows
    return rr[:max(1, int(len(rr) * frac))]

def build_glider(g):
    rows = fetch_rows(g["id"])
    n = len(rows)
    if not n:
        raise RuntimeError(f"no rows for {g['id']}")

    # normalise conductivity to S/m — some operators report mS/cm (~10x); detect by magnitude
    cvals = sorted(r["conductivity"] for r in rows if r["conductivity"] is not None)
    cond_unit = "S m-1"
    if cvals and cvals[len(cvals) // 2] > 20:          # median > 20 -> mS/cm
        cond_unit = "mS/cm -> S m-1 (/10)"
        for r in rows:
            if r["conductivity"] is not None:
                r["conductivity"] /= 10.0

    # ── track: bin the time-ordered stream into ~NBINS vertices ──
    coords, vals, times = [], {v: [] for v in VARS}, []
    step = max(1, n // NBINS)
    for i in range(0, n, step):
        chunk = rows[i:i + step]
        la, lo = mean([c["la"] for c in chunk]), mean([c["lo"] for c in chunk])
        if la is None or lo is None:
            continue
        coords.append([round(lo, 4), round(la, 4)])
        times.append(chunk[len(chunk) // 2]["t"][:16])      # representative fix time for this point
        surf = shallowest(chunk)
        for v in VARS:
            vals[v].append(r3(mean([c[v] for c in surf])))

    # ── most-recent dive: last ~600 fixes binned by 5 m depth ──
    prof_rows = rows[-600:]
    profile = {"depth": [], **{v: [] for v in VARS}}
    for d in sorted(set(int(r["dp"] // 5) * 5 for r in prof_rows if r["dp"] is not None)):
        seg = [r for r in prof_rows if r["dp"] is not None and int(r["dp"] // 5) * 5 == d]
        profile["depth"].append(d)
        for v in VARS:
            profile[v].append(r3(mean([r[v] for r in seg])))

    surf_latest = shallowest(prof_rows)
    surface = {v: r3(mean([r[v] for r in surf_latest])) for v in VARS}
    last = rows[-1]
    max_depth = max((r["dp"] for r in rows if r["dp"] is not None), default=None)

    track = {"type": "Feature",
             "geometry": {"type": "LineString", "coordinates": coords},
             "properties": {"kind": "track", "id": g["name"], "operator": g["operator"],
                            "color": g["color"], "dataset": g["id"], "vals": vals, "times": times}}
    now = {"type": "Feature",
           "geometry": {"type": "Point", "coordinates": [round(last["lo"], 4), round(last["la"], 4)]},
           "properties": {"kind": "now", "id": g["name"], "operator": g["operator"],
                          "color": g["color"], "dataset": g["id"], "time": last["t"],
                          "n": n, "maxDepth": round(max_depth, 1) if max_depth else None,
                          "surface": surface, "profile": profile}}
    return track, now, {"id": g["name"], "n": n, "time": last["t"]}

def main():
    feats = []
    print("Fetching Gulf Slocum gliders from IOOS DAC ...")
    for g in GLIDERS:
        tr, nw, s = build_glider(g)
        feats += [tr, nw]
        print(f"  {s['id']:10s}  {s['n']:6d} fixes   latest {s['time']}")
    fc = {"type": "FeatureCollection", "features": feats}
    OUT.write_text(json.dumps(fc), encoding='utf-8')
    print(f"Written -> {OUT}  ({OUT.stat().st_size // 1024} KB)")

if __name__ == "__main__":
    main()
