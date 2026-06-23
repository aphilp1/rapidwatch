"""
build_ohc_hycom.py — RapidWatch real ocean-heat pipeline, HYCOM edition
═══════════════════════════════════════════════════════════════════════
Replaces the (dead) NESDIS-ERDDAP approach in build_ohc.py. Pulls real 3-D
ocean temperature from HYCOM/GOFS via OPeNDAP and computes D26 — the depth of
the 26 °C isotherm — for each of the four RapidWatch storms, over the Gulf box.

Data sources (HYCOM THREDDS, https://tds.hycom.org):
  2005 (Katrina, Rita)   GLBv0.08/expt_53.X  GOFS 3.1 reanalysis (1994-2015)
  2024 (Helene, Milton)  ESPC-D-V02 t3z FMRC "best" time series   (if it
                         still covers Sep–Oct 2024; verified at runtime)

For each storm we take the HYCOM time step nearest the middle of its RI window,
subset water_temp over the Gulf box at all depths, and compute D26 at every grid
point. Output is a compact JSON grid the RapidWatch map can render directly —
collapsing the old Steps 1–3 (pull, regrid, export) into one.

Output:
  data/ohc/<storm>_d26.json   {lats, lons, d26[][], date, source}
  data/ohc/manifest.json

Usage:  python build_ohc_hycom.py
"""

import json, pathlib, sys
from datetime import datetime, timedelta
import numpy as np
import netCDF4 as nc

DIR     = pathlib.Path(__file__).parent
GEOJSON = DIR / 'data' / 'storms.geojson'
OUT     = DIR / 'data' / 'ohc'
OUT.mkdir(parents=True, exist_ok=True)

# Gulf box
LAT_MIN, LAT_MAX = 15.0, 32.0
LON_MIN, LON_MAX = -100.0, -74.0

def hycom_source(year):
    """OPeNDAP base URL + human label for a storm year."""
    if year <= 2015:
        return (f'https://tds.hycom.org/thredds/dodsC/GLBv0.08/expt_53.X/data/{year}',
                f'HYCOM GOFS 3.1 reanalysis (GLBv0.08/expt_53.X) {year}')
    # 2024 etc. — ESPC-D-V02 best time series
    return ('https://tds.hycom.org/thredds/dodsC/FMRC_ESPC-D-V02_t3z/FMRC_ESPC-D-V02_t3z_best.ncd',
            'HYCOM ESPC-D-V02 t3z (best time series)')

# ── RI windows (same logic as build_ohc.py) ──────────────────────────────────
def ri_windows():
    gj = json.loads(GEOJSON.read_text())
    storms = {}
    for feat in gj['features']:
        p = feat['properties']
        if p.get('kind') != 'fix' or not p.get('rapid_intensifying'):
            continue
        name = p['name'].lower(); year = p['year']
        raw = p['time_utc'].replace('Z', '')
        dt = datetime.strptime(f"{raw} {year}", "%b %d %H%M %Y")
        s = storms.setdefault(name, {'name': name, 'year': year, 'ri_start': dt, 'ri_end': dt})
        s['ri_start'] = min(s['ri_start'], dt)
        s['ri_end']   = max(s['ri_end'], dt)
    return list(storms.values())

# ── D26: depth of the 26 °C isotherm from a single profile ────────────────────
def d26_profile(T, z):
    """T: temps (°C) at increasing depths z (m). Returns D26 in metres or nan."""
    T = np.asarray(T, float); z = np.asarray(z, float)
    good = ~np.isnan(T)
    if good.sum() < 2:
        return np.nan
    T, z = T[good], z[good]
    if T[0] < 26:                      # surface already below 26 → no warm layer
        return 0.0
    for k in range(len(z) - 1):
        if T[k] >= 26 >= T[k + 1]:
            f = (T[k] - 26) / (T[k] - T[k + 1]) if T[k] != T[k + 1] else 0.0
            return float(z[k] + f * (z[k + 1] - z[k]))
    return float(z[-1])                # warm all the way down (cap at deepest level read)

# ── time index helpers ────────────────────────────────────────────────────────
def time_values(ds):
    tv = ds.variables['time']
    return nc.num2date(tv[:], tv.units,
                       only_use_cftime_datetimes=False, only_use_python_datetimes=True)

def nearest_time_idx(times, target):
    diffs = [abs((t - target).total_seconds()) for t in times]
    return int(np.argmin(diffs)), times[int(np.argmin(diffs))]

def idx_range(coord, lo, hi):
    asc = coord[0] < coord[-1]
    c = coord if asc else coord[::-1]
    i0 = int(np.searchsorted(c, lo)); i1 = int(np.searchsorted(c, hi))
    if not asc:
        n = len(coord); i0, i1 = n - i1, n - i0
    return max(0, i0 - 1), min(len(coord), i1 + 1)

# ── pull + compute one storm ──────────────────────────────────────────────────
def pull_storm(s):
    out = OUT / f"{s['name']}_d26.json"
    if out.exists():
        print(f"  [skip] {out.name} exists"); return str(out)
    url, label = hycom_source(s['year'])
    mid = s['ri_start'] + (s['ri_end'] - s['ri_start']) / 2
    print(f"  {s['name']} ({s['year']}) RI {s['ri_start'].date()}–{s['ri_end'].date()} · mid {mid}")
    print(f"    {label}")
    try:
        ds = nc.Dataset(url)
    except Exception as e:
        print(f"    OPEN FAILED: {e}"); return None
    try:
        lat = ds.variables['lat'][:]; lon = ds.variables['lon'][:]; depth = ds.variables['depth'][:]
        lon360 = lon.max() > 180
        qlo = LON_MIN + 360 if lon360 else LON_MIN
        qhi = LON_MAX + 360 if lon360 else LON_MAX
        times = time_values(ds)
        ti, tused = nearest_time_idx(times, mid)
        if abs((tused - mid).total_seconds()) > 36 * 3600:
            print(f"    nearest HYCOM time {tused} is >36h from RI window — coverage gap")
            ds.close(); return None
        la0, la1 = idx_range(lat, LAT_MIN, LAT_MAX)
        lo0, lo1 = idx_range(lon, qlo, qhi)
        print(f"    grid {len(depth)} depths · lat[{la0}:{la1}] lon[{lo0}:{lo1}] · t={tused}")
        wt = ds.variables['water_temp']
        block = np.asarray(wt[ti, :, la0:la1, lo0:lo1])
        fill = getattr(wt, '_FillValue', None)
        block = np.where(np.isfinite(block), block, np.nan)
        if fill is not None:
            block = np.where(block == fill, np.nan, block)
        # scale/offset already applied by netCDF4 for masked arrays; guard extremes
        block = np.where((block < -5) | (block > 45), np.nan, block)
        lats = np.asarray(lat[la0:la1], float)
        lons = np.asarray(lon[lo0:lo1], float)
        if lon360:
            lons = np.where(lons > 180, lons - 360, lons)
        ny, nx = block.shape[1], block.shape[2]
        d26 = np.full((ny, nx), np.nan)
        for i in range(ny):
            for j in range(nx):
                d26[i, j] = d26_profile(block[:, i, j], depth)
        ds.close()
    except Exception as e:
        print(f"    READ/COMPUTE FAILED: {e}"); ds.close(); return None

    valid = d26[~np.isnan(d26)]
    if valid.size:
        print(f"    D26 m: min={valid.min():.0f} max={valid.max():.0f} mean={valid.mean():.0f} "
              f"(n={valid.size})")
    payload = {
        'storm': s['name'], 'year': s['year'], 'time_utc': str(tused),
        'source': label,
        'lats': [round(float(v), 3) for v in lats],
        'lons': [round(float(v), 3) for v in lons],
        'd26':  [[None if np.isnan(v) else round(float(v), 1) for v in row] for row in d26],
    }
    out.write_text(json.dumps(payload))
    print(f"    saved -> {out.name} ({out.stat().st_size//1024} KB)")
    return str(out)

def main():
    print("build_ohc_hycom.py — real D26 from HYCOM\n")
    storms = ri_windows()
    results = {}
    for s in storms:
        results[s['name']] = pull_storm(s)
    ok = [k for k, v in results.items() if v]
    print(f"\n{len(ok)}/{len(storms)} storms: {ok}")
    bad = [k for k, v in results.items() if not v]
    if bad:
        print(f"Failed/no-coverage: {bad}")
    manifest = {k: v for k, v in results.items() if v}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    print(f"manifest -> data/ohc/manifest.json")

if __name__ == '__main__':
    main()
