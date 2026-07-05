"""
build_ohc.py — RapidWatch ocean-heat content pipeline
═══════════════════════════════════════════════════════
Step 1  Pull raw D26 / OHC from NESDIS SOHCS (ERDDAP)   ← THIS STEP
Step 2  Regrid to RapidWatch Gulf canvas grid             (future)
Step 3  Export JS lookup table                            (future)
Step 4  Inject into rapidwatch-gulf-map.html              (future)

Data source (re-pointed 2026-07-05 — see OHC_SOURCE_NOTES.md)
  NESDIS Satellite Ocean Heat Content Suite (SOHCS)
  Derived from satellite altimetry + climatological T/S profiles.
  The old CoastWatch ERDDAP id `nesdisVHsohcsDaily` at
  https://coastwatch.noaa.gov/erddap now returns HTTP 404 (dataset removed
  from that server). The live SOHCS grids are on the NOAA PolarWatch ERDDAP:
    noaacwOHC14na   North Atlantic, 0.25°, 2024-01-15 → present  (Helene, Milton)
    noaacwOHCna     North Atlantic, 0.25°, 2020-04-30 → 2024-01-18
  Variables (renamed from the old OHC/D26):
    iso26C  depth of the 26 °C isotherm  (metres)
    ohc     ocean heat content above D26 (kJ cm⁻²)
  ⚠ COVERAGE TRUTH: no public SOHCS ERDDAP archive reaches 2005 (the old
  header claim of "1993–present" was wrong; AOML's ERDDAP starts 2012,
  PolarWatch 2020). For Katrina/Rita (2005) use build_ohc_hycom.py
  (HYCOM GOFS 3.1 reanalysis → D26), which is verified alive.

Usage
  python build_ohc.py              # pull storms within SOHCS coverage (2024 pair)
  python build_ohc.py --discover   # list ERDDAP dataset IDs and exit
"""

import json, pathlib, sys, argparse, time
import requests, netCDF4 as nc
import numpy as np

# ── retry policy ──────────────────────────────────────────────────────────────
# CoastWatch ERDDAP returns 503 during maintenance/capacity windows and is often
# just slow rather than down. Retry transient failures (503/502/504/timeouts)
# with exponential backoff so a single invocation rides out a flaky window.
RETRYABLE_STATUS = {502, 503, 504}
MAX_RETRIES      = 5
BACKOFF_BASE     = 8        # seconds: 8, 16, 32, 64, 128

# ── paths ─────────────────────────────────────────────────────────────────────
DIR      = pathlib.Path(__file__).parent
RAW      = DIR / 'data' / 'ohc_raw'
GEOJSON  = DIR / 'data' / 'storms.geojson'
RAW.mkdir(parents=True, exist_ok=True)

# ── ERDDAP config ─────────────────────────────────────────────────────────────
# PolarWatch hosts the live SOHCS North Atlantic grids (verified 2026-07-05:
# Gulf-box .nc request returned HTTP 200; ohc 0–230 kJ/cm², iso26C 20–158 m
# for 2024-09-25 — physically sane).
ERDDAP_BASE  = 'https://polarwatch.noaa.gov/erddap'
DATASET_ID   = 'noaacwOHC14na'              # default/current; verify: {ERDDAP_BASE}/griddap/{DATASET_ID}.html
VARIABLES    = ['ohc', 'iso26C']            # kJ/cm² and metres (old names: OHC, D26)

# Dataset coverage windows (RI window must fall inside one of these).
# (dataset_id, first_day, last_day_or_None-for-present)
from datetime import datetime as _dt
DATASET_WINDOWS = [
    ('noaacwOHC14na', _dt(2024, 1, 16), None),
    ('noaacwOHCna',   _dt(2020, 5, 1),  _dt(2024, 1, 17)),
]

def dataset_for(storm):
    """Return the SOHCS dataset id covering a storm's RI window, or None."""
    for did, d0, d1 in DATASET_WINDOWS:
        if storm['ri_start'] >= d0 and (d1 is None or storm['ri_end'] <= d1):
            return did
    return None

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; RapidWatch/1.0; research)'}

# Gulf of Mexico bounding box
LAT_MIN, LAT_MAX =  15.0,  32.0
LON_MIN, LON_MAX = -100.0, -74.0            # negative-east; converted to 0-360 if needed

# ── derive RI windows from storms.geojson ────────────────────────────────────
def ri_windows():
    """
    Read rapid_intensifying fixes from storms.geojson and return one dict
    per storm with the date span covering all RI fixes.
    """
    gj = json.loads(GEOJSON.read_text())
    storms = {}
    for feat in gj['features']:
        p = feat['properties']
        if p.get('kind') != 'fix' or not p.get('rapid_intensifying'):
            continue
        name = p['name'].lower()
        # time_utc is like "Aug 27 0600Z" — attach the year
        year = p['year']
        from datetime import datetime
        raw = p['time_utc'].replace('Z', '')          # "Aug 27 0600"
        dt  = datetime.strptime(f"{raw} {year}", "%b %d %H%M %Y")
        if name not in storms:
            storms[name] = {'name': name, 'year': year,
                            'ri_start': dt, 'ri_end': dt,
                            'fixes': []}
        else:
            if dt < storms[name]['ri_start']:
                storms[name]['ri_start'] = dt
            if dt > storms[name]['ri_end']:
                storms[name]['ri_end'] = dt
        coord = feat['geometry']['coordinates']
        storms[name]['fixes'].append({'lon': coord[0], 'lat': coord[1],
                                      'time': dt.isoformat()})
    return list(storms.values())

# ── ERDDAP URL builder ────────────────────────────────────────────────────────
def _erddap_lon(lon_deg):
    """ERDDAP datasets sometimes use 0-360; return both conventions."""
    return lon_deg if lon_deg >= 0 else lon_deg + 360

def erddap_nc_url(storm, dataset_id=DATASET_ID, use_360=False):
    """
    Build an ERDDAP griddap .nc URL for a storm's full RI window,
    clipped to the Gulf bounding box.
    """
    t0 = storm['ri_start'].strftime('%Y-%m-%dT12:00:00Z')
    t1 = storm['ri_end'].strftime('%Y-%m-%dT12:00:00Z')

    if use_360:
        lon0 = _erddap_lon(LON_MIN)
        lon1 = _erddap_lon(LON_MAX)
    else:
        lon0, lon1 = LON_MIN, LON_MAX

    constraint = f"[({t0}):1:({t1})][({LAT_MIN}):1:({LAT_MAX})][({lon0}):1:({lon1})]"
    var_str    = ','.join(f"{v}{constraint}" for v in VARIABLES)
    return f"{ERDDAP_BASE}/griddap/{dataset_id}.nc?{var_str}"

# ── download one storm ────────────────────────────────────────────────────────
def pull_storm(storm, dataset_override=None):
    out = RAW / f"{storm['name']}_ohc.nc"
    if out.exists():
        print(f"  [skip] {out.name} already on disk ({out.stat().st_size//1024} KB)")
        return True

    # Pick the SOHCS dataset whose archive covers this storm's RI window
    # (or honour an explicit --dataset override).
    dataset_id = dataset_override or dataset_for(storm)
    if dataset_id is None:
        print(f"  {storm['name']} ({storm['year']}): outside SOHCS ERDDAP coverage "
              f"(earliest archive 2020-04-30) — use build_ohc_hycom.py for this storm")
        return None                                 # no-coverage, not a failure

    # Try negative-east longitude first; fall back to 0-360
    for use_360, label in [(False, '-180/180'), (True, '0/360')]:
        url = erddap_nc_url(storm, dataset_id=dataset_id, use_360=use_360)
        print(f"  {storm['name']}  ({storm['ri_start'].date()} to {storm['ri_end'].date()})")
        print(f"    GET {url[:120]}…")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                r = requests.get(url, timeout=120, stream=True, headers=HEADERS)
                if r.status_code == 200:
                    with open(out, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=65536):
                            f.write(chunk)
                    print(f"    saved -> {out.name}  ({out.stat().st_size//1024} KB)")
                    return True
                elif r.status_code == 404 and not use_360:
                    print(f"    HTTP 404 with {label} — retrying with 0-360 longitudes …")
                    break                                   # try the other longitude convention
                elif r.status_code in RETRYABLE_STATUS:
                    wait = BACKOFF_BASE * (2 ** (attempt - 1))
                    print(f"    HTTP {r.status_code} (server busy/maintenance) — "
                          f"attempt {attempt}/{MAX_RETRIES}, retrying in {wait}s …")
                    if attempt < MAX_RETRIES:
                        time.sleep(wait)
                        continue
                    print(f"    gave up after {MAX_RETRIES} attempts — ERDDAP still unavailable")
                    return False
                else:
                    print(f"    HTTP {r.status_code}: {r.text[:200]}")
                    return False
            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError) as e:
                wait = BACKOFF_BASE * (2 ** (attempt - 1))
                kind = 'timeout' if isinstance(e, requests.exceptions.Timeout) else 'network error'
                print(f"    {kind} — attempt {attempt}/{MAX_RETRIES}, retrying in {wait}s …")
                if attempt < MAX_RETRIES:
                    time.sleep(wait)
                    continue
                print(f"    gave up after {MAX_RETRIES} attempts: {e}")
                return False
    return False

# ── quick peek at a downloaded file ──────────────────────────────────────────
def summarise(storm):
    out = RAW / f"{storm['name']}_ohc.nc"
    if not out.exists():
        return
    ds = nc.Dataset(out)
    print(f"\n  {storm['name'].upper()} — {out.name}")
    for vname in VARIABLES:
        if vname in ds.variables:
            v    = ds.variables[vname]
            data = v[:].compressed() if hasattr(v[:], 'compressed') else v[:].flatten()
            data = data[~np.isnan(data)]
            if len(data):
                print(f"    {vname:4s}  min={data.min():.1f}  max={data.max():.1f}"
                      f"  mean={data.mean():.1f}  ({v.units if hasattr(v,'units') else '?'})")
    # grid info
    lats = ds.variables.get('latitude') or ds.variables.get('lat')
    lons = ds.variables.get('longitude') or ds.variables.get('lon')
    if lats is not None and lons is not None:
        print(f"    grid  {len(lats)}x{len(lons)}  "
              f"lat {float(lats[0]):.1f} to {float(lats[-1]):.1f}  "
              f"lon {float(lons[0]):.1f} to {float(lons[-1]):.1f}")
    ds.close()

# ── discover mode (list available ERDDAP datasets) ───────────────────────────
def discover():
    url = f"{ERDDAP_BASE}/griddap/index.json?page=1&itemsPerPage=500"
    print(f"Fetching dataset list from {ERDDAP_BASE} ...")
    try:
        r = requests.get(url, timeout=90, headers=HEADERS)
        data = r.json()
        cols  = data['table']['columnNames']           # find column indices
        i_id  = cols.index('Dataset ID')
        i_ttl = cols.index('Title')
        rows  = data['table']['rows']
        keywords = ('ohc', 'sohcs', 'heat', 'd26', 'tchp', 'nesdis')
        hits = [row for row in rows
                if any(kw in str(row).lower() for kw in keywords)]
        print(f"\nFound {len(hits)} matching dataset(s):\n")
        for row in hits[:30]:
            did   = str(row[i_id]).encode('ascii', 'replace').decode()
            title = str(row[i_ttl]).encode('ascii', 'replace').decode()[:60]
            print(f"  {did:42s}  {title}")
        if not hits:
            print("  (none matched -- browse manually at "
                  f"{ERDDAP_BASE}/griddap/index.html)")
    except Exception as e:
        print(f"  Error: {e}")

# ── main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='RapidWatch OHC pipeline — Step 1')
    parser.add_argument('--discover', action='store_true',
                        help='List ERDDAP OHC datasets and exit')
    parser.add_argument('--dataset', default=DATASET_ID,
                        help=f'ERDDAP dataset ID (default: {DATASET_ID})')
    args = parser.parse_args()

    if args.discover:
        discover()
        return

    print("RapidWatch build_ohc.py — Step 1: pull raw D26 / OHC")
    print(f"ERDDAP:   {ERDDAP_BASE}/griddap/{args.dataset}")
    print(f"Output:   {RAW}\n")

    storms  = ri_windows()
    results = {}

    override = args.dataset if args.dataset != DATASET_ID else None
    for s in storms:
        ok = pull_storm(s, dataset_override=override)
        results[s['name']] = ok

    print("\n-- Summary --------------------------------------------------")
    for s in storms:
        summarise(s)

    print()
    passed     = [k for k, v in results.items() if v]
    nocoverage = [k for k, v in results.items() if v is None]      # pre-2020 storms
    failed     = [k for k, v in results.items() if v is False]     # real errors
    eligible   = len(results) - len(nocoverage)
    print(f"\n{len(passed)}/{eligible} SOHCS-eligible storms pulled: {passed}")
    if nocoverage:
        print(f"Outside SOHCS archive (use build_ohc_hycom.py): {nocoverage}")

    if failed:
        print(f"Failed: {failed}")
        print("\nTroubleshooting:")
        print(f"  1. Verify dataset ID:  {ERDDAP_BASE}/griddap/{args.dataset}.html")
        print(f"  2. Browse all datasets: python build_ohc.py --discover")
        print(f"  3. Override dataset:    python build_ohc.py --dataset <ID>")
        sys.exit(1)

    manifest = {s['name']: str(RAW / f"{s['name']}_ohc.nc")
                for s in storms if results[s['name']]}
    (RAW / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(f"Manifest -> data/ohc_raw/manifest.json")

if __name__ == '__main__':
    main()
