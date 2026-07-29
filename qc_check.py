"""
qc_check.py — sanity-check the moving-asset feeds before they get committed
================================================================================
Gliders and Argo floats are pulled raw from ERDDAP/OPeNDAP. Those feeds
occasionally include a single bad GPS fix (sensor/GPS-lock glitch, corrupted
row) that a per-source bbox filter can miss or that could get reintroduced if
a source script regresses. This is the last line of defense: it re-validates
the ALREADY-BUILT geojson outputs and fails loudly (non-zero exit) if a point
is outside plausible Gulf territory or a track jumps further than a Slocum
glider (~1 kt) could physically travel between subsampled fixes.

Run after build_gliders.py / build_argo.py, before the Action commits. A
non-zero exit here MUST block the commit step — publishing nothing is always
better than publishing a broken track.

Run: python qc_check.py
"""
import json, math, pathlib, sys

DIR = pathlib.Path(__file__).parent

# Generous — wide enough to never false-positive on a real Gulf mission,
# tight enough to catch "wrong ocean" errors like ng1260's 2026-07-29 jump
# to 144.6E/13.5N (Guam).
CHECK_BBOX = {"lat": (10.0, 35.0), "lon": (-100.0, -75.0)}
MAX_JUMP_KM = 200.0   # generous multiple of a Slocum's ~44 km/day cruise speed

FILES = [
    ("gliders", DIR / "data/gliders/gliders_gulf.geojson"),
    ("argo",    DIR / "data/argo/argo_gulf.geojson"),
]

def haversine_km(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * 6371 * math.asin(math.sqrt(h))

def in_bbox(lon, lat):
    return (CHECK_BBOX["lat"][0] <= lat <= CHECK_BBOX["lat"][1]
            and CHECK_BBOX["lon"][0] <= lon <= CHECK_BBOX["lon"][1])

def check_file(label, path):
    problems = []
    if not path.exists():
        return problems   # nothing to check yet (e.g. empty Argo box is valid)
    fc = json.loads(path.read_text(encoding="utf-8"))
    for feat in fc.get("features", []):
        pid = (feat.get("properties") or {}).get("id") or (feat.get("properties") or {}).get("platform") or "?"
        geom = feat["geometry"]
        if geom["type"] == "Point":
            lon, lat = geom["coordinates"]
            if not in_bbox(lon, lat):
                problems.append(f"[{label}:{pid}] point outside plausible box: lon={lon} lat={lat}")
        elif geom["type"] == "LineString":
            coords = geom["coordinates"]
            for i, (lon, lat) in enumerate(coords):
                if not in_bbox(lon, lat):
                    problems.append(f"[{label}:{pid}] track vertex {i} outside plausible box: lon={lon} lat={lat}")
            for i in range(1, len(coords)):
                d = haversine_km(coords[i-1], coords[i])
                if d > MAX_JUMP_KM:
                    problems.append(f"[{label}:{pid}] implausible jump vertex {i-1}->{i}: {d:.0f} km "
                                     f"({coords[i-1]} -> {coords[i]})")
    return problems

def main():
    all_problems = []
    for label, path in FILES:
        all_problems += check_file(label, path)
    if all_problems:
        print("QC FAILED — refusing to let this data ship:")
        for p in all_problems:
            print("  " + p)
        sys.exit(1)
    print("QC passed — gliders + argo positions look physically plausible.")

if __name__ == "__main__":
    main()
