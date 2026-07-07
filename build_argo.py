"""
build_argo.py — RapidWatch REAL Argo float positions (Gulf of Mexico)
================================================================================
Pulls the ACTUAL recent Argo profiling-float locations from the Argo GDAC
ERDDAP (Ifremer) — no fake / "representative" fallback. If no floats are in the
box, the output is an empty FeatureCollection and the map shows nothing.

Output: data/argo/argo_gulf.geojson  (one Point per float, at its latest fix)
Source: https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats
Run:    python build_argo.py   (re-runnable / refreshable)
"""
import json, csv, io, ssl, pathlib, urllib.request, datetime

DIR = pathlib.Path(__file__).parent
OUT = DIR / 'data' / 'argo' / 'argo_gulf.geojson'
OUT.parent.mkdir(parents=True, exist_ok=True)

LAT0, LAT1, LON0, LON1 = 18, 31, -98, -80      # Gulf box
DAYS = 45                                       # "recent" window
BASE = "https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.csv"

def main():
    start = (datetime.datetime.utcnow() - datetime.timedelta(days=DAYS)).strftime('%Y-%m-%dT00:00:00Z')
    q = ("?platform_number,latitude,longitude,time,cycle_number"
         f"&time%3E={start}"
         f"&latitude%3E={LAT0}&latitude%3C={LAT1}&longitude%3E={LON0}&longitude%3C={LON1}")
    url = BASE + q
    print("Fetching REAL Argo floats from the Argo GDAC ERDDAP ...")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(url, timeout=120, context=ctx) as r:
            text = r.read().decode('utf-8')
    except Exception as e:
        print("  ERDDAP fetch failed:", e)
        # honest empty output — never fabricate
        OUT.write_text(json.dumps({"type": "FeatureCollection", "features": []}), encoding='utf-8')
        return

    rows = list(csv.reader(io.StringIO(text)))[2:]     # skip names + units rows
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

    feats = [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [round(d['lo'], 4), round(d['la'], 4)]},
        "properties": {"platform": pf, "time": d['t'], "cycle": d['cyc']}
    } for pf, d in latest.items()]

    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats}), encoding='utf-8')
    print(f"{len(feats)} REAL Argo floats in the Gulf (last {DAYS} d)  ->  {OUT}")
    for f in feats[:10]:
        p = f['properties']
        print(f"  float {p['platform']}  @ {f['geometry']['coordinates']}  cycle {p['cycle']}  {p['time'][:10]}")

if __name__ == "__main__":
    main()
