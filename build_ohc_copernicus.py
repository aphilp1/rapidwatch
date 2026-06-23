"""
build_ohc_copernicus.py — real D26 for the 2024 storms via Copernicus Marine
═══════════════════════════════════════════════════════════════════════════
HYCOM has no public archive for Sep–Oct 2024, so Helene & Milton come from
the Copernicus Marine "Global Ocean Physics Analysis and Forecast" product
(GLOBAL_ANALYSISFORECAST_PHY_001_024), 1/12°, daily-mean potential temperature
(thetao). We subset a Gulf box for the storm's RI date, then compute D26 with
the same logic as build_ohc_hycom and write the identical JSON format so the
map's makeRealD26Layer() can render it.

Requires: a logged-in copernicusmarine session (run copernicusmarine.login once).

Usage:  python build_ohc_copernicus.py
"""

import json, pathlib
from datetime import datetime
import numpy as np
import netCDF4 as nc
import copernicusmarine as cm

from build_ohc_hycom import ri_windows, d26_profile   # reuse

DIR     = pathlib.Path(__file__).parent
OUT     = DIR / 'data' / 'ohc'
RAW     = OUT / 'raw'
RAW.mkdir(parents=True, exist_ok=True)

DATASET = 'cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m'   # daily-mean potential temp
LAT_MIN, LAT_MAX = 15.0, 32.0
LON_MIN, LON_MAX = -100.0, -74.0

def pull_storm(s):
    out = OUT / f"{s['name']}_d26.json"
    if out.exists():
        print(f"  [skip] {out.name} exists"); return str(out)
    mid = s['ri_start'] + (s['ri_end'] - s['ri_start']) / 2
    day = mid.strftime('%Y-%m-%d')
    ncfile = RAW / f"{s['name']}_thetao.nc"
    print(f"  {s['name']} ({s['year']}) RI {s['ri_start'].date()}–{s['ri_end'].date()} · day {day}")
    try:
        cm.subset(
            dataset_id=DATASET, variables=['thetao'],
            minimum_longitude=LON_MIN, maximum_longitude=LON_MAX,
            minimum_latitude=LAT_MIN, maximum_latitude=LAT_MAX,
            minimum_depth=0, maximum_depth=300,
            start_datetime=f"{day}T00:00:00", end_datetime=f"{day}T00:00:00",
            output_filename=ncfile.name, output_directory=str(RAW),
            overwrite=True, disable_progress_bar=True,
        )
    except Exception as e:
        print(f"    SUBSET FAILED: {e}"); return None
    if not ncfile.exists():
        print("    no file written"); return None

    ds = nc.Dataset(ncfile)
    lat = ds.variables['latitude'][:]; lon = ds.variables['longitude'][:]
    depth = ds.variables['depth'][:]
    th = ds.variables['thetao']
    tv = ds.variables['time']
    tstr = str(nc.num2date(tv[0], tv.units, only_use_cftime_datetimes=False,
                           only_use_python_datetimes=True))
    block = np.asarray(th[0])                       # (depth, lat, lon)
    block = np.where(np.isfinite(block), block, np.nan)
    block = np.where((block < -5) | (block > 45), np.nan, block)
    ny, nx = block.shape[1], block.shape[2]
    d26 = np.full((ny, nx), np.nan)
    for i in range(ny):
        for j in range(nx):
            d26[i, j] = d26_profile(block[:, i, j], depth)
    ds.close()

    valid = d26[~np.isnan(d26)]
    if valid.size:
        print(f"    D26 m: min={valid.min():.0f} max={valid.max():.0f} "
              f"mean={valid.mean():.0f} (n={valid.size})")
    payload = {
        'storm': s['name'], 'year': s['year'], 'time_utc': tstr,
        'source': 'Copernicus Marine GLOBAL_ANALYSISFORECAST_PHY_001_024 (thetao)',
        'lats': [round(float(v), 3) for v in lat],
        'lons': [round(float(v), 3) for v in lon],
        'd26':  [[None if np.isnan(v) else round(float(v), 1) for v in row] for row in d26],
    }
    out.write_text(json.dumps(payload))
    print(f"    saved -> {out.name} ({out.stat().st_size//1024} KB)")
    return str(out)

def main():
    print("build_ohc_copernicus.py — real D26 for 2024 storms (Copernicus GLORYS analysis)\n")
    storms = [s for s in ri_windows() if s['year'] >= 2024]
    results = {}
    for s in storms:
        results[s['name']] = pull_storm(s)
    ok = [k for k, v in results.items() if v]
    print(f"\n{len(ok)}/{len(storms)} storms: {ok}")

if __name__ == '__main__':
    main()
