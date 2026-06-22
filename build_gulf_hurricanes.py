"""
build_gulf_hurricanes.py — RapidWatch historical Gulf hurricane track library
═════════════════════════════════════════════════════════════════════════════
Parses NOAA HURDAT2 (Atlantic best-track, 1851–present) and extracts EVERY
hurricane whose track entered the Gulf of Mexico.

Source file (download once):
  https://www.nhc.noaa.gov/data/hurdat/  →  hurdat2-1851-2025-02272026.txt
  saved locally as  data/hurdat2-atlantic.txt

"Hurricane that entered the Gulf" is defined as a storm that:
  (a) attained hurricane status (HU, sustained wind >= 64 kt) at any point in
      its life, AND
  (b) has at least one best-track fix inside the Gulf-of-Mexico polygon below.

Outputs:
  data/gulf_hurricanes.geojson  — one LineString feature per storm (full track),
                                  rich properties for the RapidWatch map
  data/gulf_hurricanes.json     — compact summary list (id/name/year/peak/etc.)
  prints a console summary (totals, by-decade, strongest)

HURDAT2 format reference:
  header:  AL092011,              IRENE,     51,
  data:    20110821, 0000,  , TS, 15.0N,  59.0W,  45, 1006, ...
           date      time  RI  st  lat     lon    kt  mb
  status codes: TD TS HU EX SD SS LO WV DB
"""

import json, pathlib, sys
from datetime import datetime

DIR    = pathlib.Path(__file__).parent
SRC    = DIR / 'data' / 'hurdat2-atlantic.txt'
GEOOUT = DIR / 'data' / 'gulf_hurricanes.geojson'
SUMOUT = DIR / 'data' / 'gulf_hurricanes.json'
INTOUT = DIR / 'data' / 'gulf_intensification.geojson'   # run-up-to-peak segments

# ── Gulf of Mexico polygon (lon, lat), approx water body incl. Bay of Campeche ─
# Drawn to exclude the open Atlantic (east of the Florida Straits) and the
# Caribbean (south of the Yucatan Channel) so Atlantic/Caribbean-only hurricanes
# are not falsely counted.
GULF_POLY = [
    (-97.2, 25.9),   # Rio Grande mouth (TX/MX border)
    (-97.0, 28.0),
    (-95.6, 28.7),
    (-94.0, 29.7),   # upper Texas coast
    (-91.5, 29.3),   # Louisiana
    (-89.2, 29.0),   # Mississippi delta
    (-87.5, 30.3),   # Alabama / FL panhandle
    (-84.0, 30.0),   # Big Bend FL
    (-82.7, 28.5),   # west-central FL
    (-81.2, 25.3),   # SW Florida / start of Straits
    (-81.0, 24.4),   # Florida Keys (south edge of Straits)
    (-84.0, 22.2),   # open-water cut toward Yucatan Channel
    (-86.8, 21.2),   # NE Yucatan (Cancun)
    (-90.5, 19.6),   # Campeche bank
    (-94.0, 18.2),   # Bay of Campeche (south)
    (-96.5, 19.6),   # Veracruz
    (-97.5, 22.5),   # Tampico
    (-97.2, 25.9),   # close
]

def in_gulf(lon, lat):
    """Ray-casting point-in-polygon test against GULF_POLY."""
    inside = False
    n = len(GULF_POLY)
    j = n - 1
    for i in range(n):
        xi, yi = GULF_POLY[i]
        xj, yj = GULF_POLY[j]
        if ((yi > lat) != (yj > lat)) and \
           (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

# ── Saffir-Simpson category from sustained wind (kt) ──────────────────────────
def category(kt):
    if kt >= 137: return 5
    if kt >= 113: return 4
    if kt >= 96:  return 3
    if kt >= 83:  return 2
    if kt >= 64:  return 1
    return 0

def fix_dt(p):
    return datetime.strptime(p['date'] + p['time'].zfill(4), '%Y%m%d%H%M')

def intensification_to_peak(track):
    """
    Find the continuous strengthening stretch that culminates at a storm's
    lifetime maximum wind — i.e. 'the process of reaching maximum intensity'.

    Returns a dict describing that segment, or None if there is no usable
    run-up (peaked at genesis, or too few valid wind fixes).
    """
    pts = [p for p in track if p['wind'] is not None]
    if len(pts) < 2:
        return None
    peakw = max(p['wind'] for p in pts)
    peak_i = next(i for i, p in enumerate(pts) if p['wind'] == peakw)   # first peak
    # walk back over the contiguous non-decreasing run leading to the peak
    s = peak_i
    while s > 0 and pts[s - 1]['wind'] <= pts[s]['wind']:
        s -= 1
    seg = pts[s:peak_i + 1]
    if len(seg) < 2:
        return None

    start, peak = seg[0], seg[-1]
    hours = (fix_dt(peak) - fix_dt(start)).total_seconds() / 3600.0

    # peak rate of intensification over any window <= 24 h within the run-up
    max24 = 0
    for a in range(len(seg)):
        for b in range(a):
            dt = (fix_dt(seg[a]) - fix_dt(seg[b])).total_seconds() / 3600.0
            if 0 < dt <= 24:
                max24 = max(max24, seg[a]['wind'] - seg[b]['wind'])

    return {
        'coords':    [[p['lon'], p['lat']] for p in seg],
        'start_wind': start['wind'], 'peak_wind': peak['wind'],
        'delta_kt':   peak['wind'] - start['wind'],
        'hours':      round(hours, 1),
        'max_24h_kt': max24,
        'rapid':      max24 >= 30,                 # NOAA RI threshold
        'peak_date':  peak['date'], 'peak_time': peak['time'],
        'peak_lat':   peak['lat'], 'peak_lon': peak['lon'],
    }

def parse_latlon(s):
    s = s.strip()
    val = float(s[:-1])
    hemi = s[-1]
    if hemi in ('S', 'W'):
        val = -val
    return val

# ── parse HURDAT2 ─────────────────────────────────────────────────────────────
def parse_hurdat(path):
    storms = []
    lines = path.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        parts = [p.strip() for p in line.split(',')]
        # header line: AL092011, IRENE, 51
        sid   = parts[0]
        name  = parts[1]
        ntrack = int(parts[2])
        year  = int(sid[4:8])
        track = []
        for k in range(1, ntrack + 1):
            rec = [p.strip() for p in lines[i + k].split(',')]
            date, time, rid, status = rec[0], rec[1], rec[2], rec[3]
            lat = parse_latlon(rec[4])
            lon = parse_latlon(rec[5])
            wind = int(rec[6])
            pres = int(rec[7])
            track.append({
                'date': date, 'time': time, 'rid': rid, 'status': status,
                'lat': lat, 'lon': lon, 'wind': wind if wind != -999 else None,
                'pres': pres if pres != -999 else None,
            })
        storms.append({'id': sid, 'name': name.strip(), 'year': year, 'track': track})
        i += ntrack + 1
    return storms

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    if not SRC.exists():
        print(f"ERROR: {SRC} not found. Download HURDAT2 first:")
        print("  https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-02272026.txt")
        sys.exit(1)

    storms = parse_hurdat(SRC)
    print(f"Parsed {len(storms)} total Atlantic systems (1851-2025).")

    features = []
    summary  = []
    intens   = []          # intensification-to-peak segments
    for s in storms:
        ever_hu   = any(p['status'] == 'HU' for p in s['track'])
        gulf_pts  = [p for p in s['track'] if in_gulf(p['lon'], p['lat'])]
        if not (ever_hu and gulf_pts):
            continue

        winds = [p['wind'] for p in s['track'] if p['wind'] is not None]
        peak_wind = max(winds) if winds else None
        pressures = [p['pres'] for p in s['track'] if p['pres'] is not None]
        min_pres  = min(pressures) if pressures else None
        peak_cat  = category(peak_wind) if peak_wind else 0

        # peak intensity WHILE in the Gulf
        gulf_winds = [p['wind'] for p in gulf_pts if p['wind'] is not None]
        gulf_peak_wind = max(gulf_winds) if gulf_winds else None
        gulf_peak_cat  = category(gulf_peak_wind) if gulf_peak_wind else 0

        first_gulf = gulf_pts[0]
        coords = [[p['lon'], p['lat']] for p in s['track']]

        name = s['name'] if s['name'] != 'UNNAMED' else f"(unnamed {s['year']})"

        props = {
            'id': s['id'], 'name': name, 'year': s['year'],
            'peak_wind_kt': peak_wind, 'peak_category': peak_cat,
            'min_pressure_mb': min_pres,
            'gulf_peak_wind_kt': gulf_peak_wind, 'gulf_peak_category': gulf_peak_cat,
            'gulf_entry_date': first_gulf['date'], 'gulf_fix_count': len(gulf_pts),
            'track_fix_count': len(s['track']),
        }
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'LineString', 'coordinates': coords},
            'properties': props,
        })
        summary.append(props)

        # ── run-up to maximum intensity ────────────────────────────────────────
        ramp = intensification_to_peak(s['track'])
        if ramp:
            intens.append({
                'type': 'Feature',
                'geometry': {'type': 'LineString', 'coordinates': ramp['coords']},
                'properties': {
                    'id': s['id'], 'name': name, 'year': s['year'],
                    'start_wind_kt': ramp['start_wind'], 'peak_wind_kt': ramp['peak_wind'],
                    'peak_category': category(ramp['peak_wind']),
                    'delta_kt': ramp['delta_kt'], 'hours': ramp['hours'],
                    'max_24h_kt': ramp['max_24h_kt'], 'rapid': ramp['rapid'],
                    'peak_lat': ramp['peak_lat'], 'peak_lon': ramp['peak_lon'],
                },
            })

    summary.sort(key=lambda r: (r['year'], r['id']))
    features.sort(key=lambda f: (f['properties']['year'], f['properties']['id']))
    intens.sort(key=lambda f: (f['properties']['year'], f['properties']['id']))

    GEOOUT.write_text(json.dumps(
        {'type': 'FeatureCollection',
         'meta': {'source': 'NOAA HURDAT2 1851-2025 (02272026 release)',
                  'definition': 'reached hurricane status AND entered Gulf of Mexico polygon',
                  'count': len(features)},
         'features': features}, indent=1))
    SUMOUT.write_text(json.dumps(summary, indent=1))
    n_rapid = sum(1 for f in intens if f['properties']['rapid'])
    INTOUT.write_text(json.dumps(
        {'type': 'FeatureCollection',
         'meta': {'source': 'NOAA HURDAT2 1851-2025 (02272026 release)',
                  'definition': 'continuous strengthening run-up culminating at each storm\'s '
                                'lifetime maximum wind; rapid=true if it gained >=30 kt in any 24 h',
                  'count': len(intens), 'rapid_count': n_rapid},
         'features': intens}, indent=1))

    # ── console report ────────────────────────────────────────────────────────
    print(f"\nGulf hurricanes found: {len(summary)}\n")

    # by decade
    from collections import Counter
    dec = Counter((r['year'] // 10) * 10 for r in summary)
    print("By decade:")
    for d in sorted(dec):
        print(f"  {d}s: {dec[d]:3d}  {'#' * dec[d]}")

    # strongest at Gulf peak
    cat5 = [r for r in summary if r['gulf_peak_category'] == 5]
    print(f"\nReached Category 5 while in the Gulf: {len(cat5)}")
    for r in sorted(cat5, key=lambda r: -(r['gulf_peak_wind_kt'] or 0)):
        print(f"  {r['year']}  {r['name']:18s} {r['gulf_peak_wind_kt']} kt"
              f"  ({r['min_pressure_mb']} mb lifetime min)")

    print(f"\nIntensification-to-peak run-ups: {len(intens)}  "
          f"({n_rapid} qualified as RAPID intensification, >=30 kt/24h)")

    print(f"\nWrote {GEOOUT.name}  ({GEOOUT.stat().st_size//1024} KB)")
    print(f"Wrote {SUMOUT.name}  ({SUMOUT.stat().st_size//1024} KB)")
    print(f"Wrote {INTOUT.name}  ({INTOUT.stat().st_size//1024} KB)")

if __name__ == '__main__':
    main()
