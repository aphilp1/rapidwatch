"""
build_ocean_state.py — RapidWatch LIVE ocean-state pipeline, HYCOM edition
═══════════════════════════════════════════════════════════════════════════
Pulls the CURRENT (nearest-to-now) HYCOM/GOFS ocean state for the Gulf of
Mexico via OPeNDAP and writes compact JSON grids for a "live ocean model"
layer set on the RapidWatch Live Sensor Systems map: SST, D26 (depth of the
26 °C isotherm / ocean heat content proxy), and surface currents.

Companion to build_ohc_hycom.py, which does the same D26 computation but for
FIXED historical storm RI windows. This script instead grabs the FMRC "best"
time-series nearest to *right now* — the same server blends analysis with a
short forecast, so "nearest to now" is effectively the live/nowcast state.

Data sources (HYCOM THREDDS, https://tds.hycom.org — verified reachable):
  water_temp (40 z-levels)  FMRC_ESPC-D-V02_t3z_best.ncd   var 'water_temp'
  surface u                 FMRC_ESPC-D-V02_u3z_best.ncd   var 'water_u'
  surface v                 FMRC_ESPC-D-V02_v3z_best.ncd   var 'water_v'
All three share the same lat/lon/time grid (native ~1/12° lon x ~1/25° lat
near Gulf latitudes; time is 3-hourly). Longitude is 0-360 on the server side
(subtract 360 to get °W). We stride the native grid down to ~0.16-0.2° so
files stay small (~65 x 75 points over the Gulf box).

Output (data/ocean/):
  hycom_sst.json       {lats, lons, sst:[[°C]],      time_utc, source}
  hycom_d26.json       {lats, lons, d26:[[m]],       time_utc, source}
  hycom_currents.json  {lats, lons, u:[[m/s]], v:[[m/s]], time_utc, source}

Masked / land / fill values are written as JSON null (matches the pattern
consumed by makeRealD26Layer() in rapidwatch-gulf-map.html).

Usage:  python build_ocean_state.py
Re-runnable: always re-pulls the latest time and overwrites the 3 files.
"""

import json, pathlib, time
from datetime import datetime, timezone
import numpy as np
import netCDF4 as nc

DIR = pathlib.Path(__file__).parent
OUT = DIR / 'data' / 'ocean'
OUT.mkdir(parents=True, exist_ok=True)

# Gulf box (matches build_ohc_hycom's spirit, tightened per the ask)
LAT_MIN, LAT_MAX = 18.0, 31.0
LON_MIN, LON_MAX = -98.0, -80.0

# Native grid near Gulf latitudes is ~0.04° lat x ~0.08° lon.
# These strides bring it to ~0.20° lat x ~0.16° lon -> ~65 x 76 points.
LAT_STRIDE, LON_STRIDE = 5, 3

T3Z_URL = 'https://tds.hycom.org/thredds/dodsC/FMRC_ESPC-D-V02_t3z/FMRC_ESPC-D-V02_t3z_best.ncd'
U3Z_URL = 'https://tds.hycom.org/thredds/dodsC/FMRC_ESPC-D-V02_u3z/FMRC_ESPC-D-V02_u3z_best.ncd'
V3Z_URL = 'https://tds.hycom.org/thredds/dodsC/FMRC_ESPC-D-V02_v3z/FMRC_ESPC-D-V02_v3z_best.ncd'
SOURCE_LABEL = 'HYCOM ESPC-D-V02 (FMRC best time series, tds.hycom.org)'

# ── D26: depth of the 26 °C isotherm from a single profile (same logic as
#    build_ohc_hycom.d26_profile) ─────────────────────────────────────────────
def d26_profile(T, z):
    """T: temps (°C) at increasing depths z (m). Returns D26 in metres or nan."""
    T = np.asarray(T, float); z = np.asarray(z, float)
    good = ~np.isnan(T)
    if good.sum() < 2:
        return np.nan
    T, z = T[good], z[good]
    if T[0] < 26:                      # surface already below 26 -> no warm layer
        return 0.0
    for k in range(len(z) - 1):
        if T[k] >= 26 >= T[k + 1]:
            f = (T[k] - 26) / (T[k] - T[k + 1]) if T[k] != T[k + 1] else 0.0
            return float(z[k] + f * (z[k + 1] - z[k]))
    return float(z[-1])                # warm all the way down (cap at deepest level read)

def time_values(ds):
    tv = ds.variables['time']
    return nc.num2date(tv[:], tv.units,
                       only_use_cftime_datetimes=False, only_use_python_datetimes=True)

def nearest_time_idx(times, target):
    diffs = [abs((t - target).total_seconds()) for t in times]
    i = int(np.argmin(diffs))
    return i, times[i]

def idx_range(coord, lo, hi):
    """Index range covering [lo, hi] in a coord array that may be ascending or descending."""
    asc = coord[0] < coord[-1]
    c = coord if asc else coord[::-1]
    i0 = int(np.searchsorted(c, lo)); i1 = int(np.searchsorted(c, hi))
    if not asc:
        n = len(coord); i0, i1 = n - i1, n - i0
    return max(0, i0 - 1), min(len(coord), i1 + 1)

def clean(block, fill=None, lo=-5, hi=45):
    """Mask fill value / out-of-range / non-finite entries to NaN."""
    block = np.asarray(block, dtype=float)
    block = np.where(np.isfinite(block), block, np.nan)
    if fill is not None:
        block = np.where(np.isclose(block, fill), np.nan, block)
    block = np.where((block < lo) | (block > hi), np.nan, block)
    return block

def to_json_grid(arr, ndigits):
    return [[None if np.isnan(v) else round(float(v), ndigits) for v in row] for row in arr]

# ── open a dataset, find nearest-to-now time + Gulf-box index ranges ─────────
def open_and_locate(url, label):
    print(f"  opening {label} ...")
    ds = nc.Dataset(url)
    lat = ds.variables['lat'][:]; lon = ds.variables['lon'][:]
    lon360 = lon.max() > 180
    qlo = LON_MIN + 360 if lon360 else LON_MIN
    qhi = LON_MAX + 360 if lon360 else LON_MAX
    times = time_values(ds)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ti, tused = nearest_time_idx(times, now)
    la0, la1 = idx_range(lat, LAT_MIN, LAT_MAX)
    lo0, lo1 = idx_range(lon, qlo, qhi)
    print(f"    latest usable time: {tused} UTC (target now={now}, "
          f"diff={abs((tused-now).total_seconds())/3600:.1f}h)")
    return ds, lat, lon, lon360, la0, la1, lo0, lo1, ti, tused

def gulf_latlon(lat, lon, lon360, la0, la1, lo0, lo1):
    lats = np.asarray(lat[la0:la1:LAT_STRIDE], float)
    lons = np.asarray(lon[lo0:lo1:LON_STRIDE], float)
    if lon360:
        lons = np.where(lons > 180, lons - 360, lons)
    return lats, lons

# ── SST + D26 from t3z (water_temp) ───────────────────────────────────────────
def pull_sst_and_d26():
    print("\n[1/2] water_temp (SST + full profile for D26) from t3z ...")
    t0 = time.time()
    ds, lat, lon, lon360, la0, la1, lo0, lo1, ti, tused = open_and_locate(T3Z_URL, 't3z')
    depth = np.asarray(ds.variables['depth'][:], float)
    wt = ds.variables['water_temp']
    fill = getattr(wt, '_FillValue', None)

    lats, lons = gulf_latlon(lat, lon, lon360, la0, la1, lo0, lo1)
    ny, nx = len(lats), len(lons)
    print(f"    grid {ny} x {nx} (lat x lon), {len(depth)} depth levels, t-index {ti}")

    # surface layer (depth[0] == 0 m) -> SST
    sst2d = clean(np.asarray(wt[ti, 0, la0:la1:LAT_STRIDE, lo0:lo1:LON_STRIDE]), fill)

    # full depth profile -> D26 (slower OPeNDAP pull; ~40 levels)
    prof = clean(np.asarray(wt[ti, :, la0:la1:LAT_STRIDE, lo0:lo1:LON_STRIDE]), fill)
    ds.close()

    d26 = np.full((ny, nx), np.nan)
    for i in range(ny):
        for j in range(nx):
            d26[i, j] = d26_profile(prof[:, i, j], depth)

    dt = time.time() - t0
    print(f"    done in {dt:.1f}s")

    time_utc = str(tused)
    sst_payload = {
        'lats': [round(float(v), 3) for v in lats],
        'lons': [round(float(v), 3) for v in lons],
        'sst': to_json_grid(sst2d, 2),
        'time_utc': time_utc,
        'source': SOURCE_LABEL + ' — water_temp @ 0 m',
    }
    d26_payload = {
        'lats': [round(float(v), 3) for v in lats],
        'lons': [round(float(v), 3) for v in lons],
        'd26': to_json_grid(d26, 1),
        'time_utc': time_utc,
        'source': SOURCE_LABEL + ' — D26 from water_temp profile',
    }
    return sst_payload, d26_payload, sst2d, d26, lats, lons

# ── surface currents from u3z / v3z ───────────────────────────────────────────
def pull_currents():
    print("\n[2/2] surface currents (water_u, water_v) from u3z/v3z ...")
    try:
        dsu, lat, lon, lon360, la0, la1, lo0, lo1, tiu, tusedu = open_and_locate(U3Z_URL, 'u3z')
    except Exception as e:
        print(f"    u3z UNREACHABLE: {e} -- skipping currents layer")
        return None
    try:
        dsv, latv, lonv, lon360v, la0v, la1v, lo0v, lo1v, tiv, tusedv = open_and_locate(V3Z_URL, 'v3z')
    except Exception as e:
        print(f"    v3z UNREACHABLE: {e} -- skipping currents layer")
        dsu.close(); return None

    try:
        wu = dsu.variables['water_u']; wv = dsv.variables['water_v']
        fillu = getattr(wu, '_FillValue', None); fillv = getattr(wv, '_FillValue', None)
        lats, lons = gulf_latlon(lat, lon, lon360, la0, la1, lo0, lo1)
        ny, nx = len(lats), len(lons)
        u2d = clean(np.asarray(wu[tiu, 0, la0:la1:LAT_STRIDE, lo0:lo1:LON_STRIDE]), fillu, lo=-5, hi=5)
        v2d = clean(np.asarray(wv[tiv, 0, la0v:la1v:LAT_STRIDE, lo0v:lo1v:LON_STRIDE]), fillv, lo=-5, hi=5)
    finally:
        dsu.close(); dsv.close()

    time_utc = str(tusedu)
    payload = {
        'lats': [round(float(v), 3) for v in lats],
        'lons': [round(float(v), 3) for v in lons],
        'u': to_json_grid(u2d, 3),
        'v': to_json_grid(v2d, 3),
        'time_utc': time_utc,
        'source': SOURCE_LABEL + ' — water_u/water_v @ 0 m',
    }
    return payload, u2d, v2d

def main():
    print("build_ocean_state.py — live HYCOM ocean state for the Gulf\n")

    sst_payload, d26_payload, sst2d, d26, lats, lons = pull_sst_and_d26()

    sst_out = OUT / 'hycom_sst.json'
    sst_out.write_text(json.dumps(sst_payload))
    d26_out = OUT / 'hycom_d26.json'
    d26_out.write_text(json.dumps(d26_payload))

    cur_result = pull_currents()
    if cur_result:
        cur_payload, u2d, v2d = cur_result
        cur_out = OUT / 'hycom_currents.json'
        cur_out.write_text(json.dumps(cur_payload))
    else:
        cur_out = None

    # ── summary ────────────────────────────────────────────────────────────
    ny, nx = len(lats), len(lons)
    ci, cj = ny // 2, nx // 2  # rough Gulf-center cell for a sample value
    print("\n" + "=" * 70)
    print("SUMMARY")
    print(f"  time_utc (SST/D26): {sst_payload['time_utc']}")
    print(f"  grid: {ny} x {nx}  (lat {lats[0]:.2f}..{lats[-1]:.2f}, "
          f"lon {lons[0]:.2f}..{lons[-1]:.2f})")

    sst_valid = sst2d[~np.isnan(sst2d)]
    if sst_valid.size:
        print(f"  SST range: {sst_valid.min():.2f} - {sst_valid.max():.2f} C "
              f"(n={sst_valid.size} ocean points)")
    d26_valid = d26[~np.isnan(d26)]
    if d26_valid.size:
        print(f"  D26 range: {d26_valid.min():.1f} - {d26_valid.max():.1f} m")

    print(f"  Gulf-center sample [{lats[ci]:.2f}N, {lons[cj]:.2f}E]: "
          f"SST={sst2d[ci,cj] if not np.isnan(sst2d[ci,cj]) else 'nan'}, "
          f"D26={d26[ci,cj] if not np.isnan(d26[ci,cj]) else 'nan'}")

    print(f"  hycom_sst.json  -> {sst_out} ({sst_out.stat().st_size//1024} KB)")
    print(f"  hycom_d26.json  -> {d26_out} ({d26_out.stat().st_size//1024} KB)")

    if cur_result:
        cur_payload, u2d, v2d = cur_result
        spd = np.sqrt(u2d**2 + v2d**2)
        spd_valid = spd[~np.isnan(spd)]
        print(f"  currents time_utc: {cur_payload['time_utc']}")
        if spd_valid.size:
            print(f"  current speed range: {spd_valid.min():.3f} - {spd_valid.max():.3f} m/s")
        print(f"  Gulf-center sample currents: u={u2d[ci,cj]:.3f}, v={v2d[ci,cj]:.3f} m/s"
              if not np.isnan(u2d[ci, cj]) else "  Gulf-center sample currents: nan (land/masked)")
        print(f"  hycom_currents.json -> {cur_out} ({cur_out.stat().st_size//1024} KB)")
    else:
        print("  hycom_currents.json -> SKIPPED (u3z/v3z unreachable)")
    print("=" * 70)

if __name__ == '__main__':
    main()
