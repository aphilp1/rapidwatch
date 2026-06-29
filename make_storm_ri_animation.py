#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
make_storm_ri_animation.py  — generalized GOES RI animation pipeline (RapidWatch)

Reconstruct a hurricane's rapid intensification from real GOES ABI Band-13 (clean IR)
imagery + the HURDAT2 best track. Enhancements: 10-min cadence, D26 ocean-heat underlay,
and an intensity-vs-time trace.

  python make_storm_ri_animation.py <storm> --test     # one HUD frame (near peak) -> verify
  python make_storm_ri_animation.py <storm> --full      # HUD video <storm>_RI_<year>.mp4
  python make_storm_ri_animation.py <storm> --overlay    # data/overlays/<storm>_ir.{webm,mp4}

<storm> in: milton helene  (katrina/rita = GOES-12, TODO data source)
"""
import os, sys, json, math, datetime as dt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- per-storm config ----
STORMS = {
    "milton": dict(name="Milton", year=2024, source="abi", bucket="noaa-goes16",
                   start=(2024, 10, 5, 12), end=(2024, 10, 10, 8),   # through Florida landfall (Oct 10)
                   bounds=(-98.0, -80.0, 16.5, 28.5), d26="data/ohc/milton_d26.json"),
    "helene": dict(name="Helene", year=2024, source="abi", bucket="noaa-goes16",
                   start=(2024, 9, 24, 6), end=(2024, 9, 27, 6),
                   bounds=(-91.0, -79.0, 16.5, 32.0), d26="data/ohc/helene_d26.json"),
    # 2005 storms = GOES-12 era -> GridSat-GOES (NCEI, anonymous HTTPS, hourly, var ch4)
    "katrina": dict(name="Katrina", year=2005, source="gridsat", sat="goes12",
                    start=(2005, 8, 26, 0), end=(2005, 8, 29, 18),   # through LA/MS landfall (Aug 29)
                    bounds=(-92.0, -79.0, 22.5, 31.0), d26="data/ohc/katrina_d26.json"),
    "rita": dict(name="Rita", year=2005, source="gridsat", sat="goes12",
                 start=(2005, 9, 19, 18), end=(2005, 9, 24, 12),     # through TX/LA landfall (Sep 24)
                 bounds=(-94.5, -78.0, 21.5, 30.5), d26="data/ohc/rita_d26.json"),
}

# ---- palette ----
NAVY = "#0A182B"; INK = "#ECF3FB"; MUTE = "#9CB6D2"
AMBER = "#FFB24D"; RED = "#FF3B5C"; TEAL = "#3CDDC9"; CYAN = "#7FE3FF"

# ---- globals set per run ----
LON0 = LON1 = LAT0 = LAT1 = None
BUCKET = None
PRODUCT = "ABI-L2-CMIPC"; BAND = "C13"
CACHE = None
SOURCE = "abi"; SAT = "goes12"

import requests
import boto3
from botocore import UNSIGNED
from botocore.config import Config
_S3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
_GEO = {}


def setup(cfg):
    global LON0, LON1, LAT0, LAT1, BUCKET, CACHE, SOURCE, SAT
    LON0, LON1, LAT0, LAT1 = cfg["bounds"]
    BUCKET = cfg.get("bucket")
    SOURCE = cfg.get("source", "abi")
    SAT = cfg.get("sat", "goes12")
    CACHE = os.path.join(HERE, "data", "goes_cache")
    os.makedirs(CACHE, exist_ok=True)
    _GEO.clear()


GRIDSAT_BASE = "https://www.ncei.noaa.gov/data/gridsat-goes/access/goes"


# ===================== GOES helpers =====================
def _fname_start(key):
    if "GridSat" in key:                       # GridSat-GOES.goesNN.YYYY.MM.DD.HHMM.v01.nc
        p = key.split("/")[-1].split(".")
        return dt.datetime(int(p[2]), int(p[3]), int(p[4]), int(p[5][:2]), int(p[5][2:]))
    tok = key.split("_s")[1]
    yr = int(tok[0:4]); doy = int(tok[4:7]); hh = int(tok[7:9]); mm = int(tok[9:11]); ss = int(tok[11:13])
    return dt.datetime(yr, 1, 1) + dt.timedelta(days=doy - 1, hours=hh, minutes=mm, seconds=ss)


def _gridsat_url(t):
    return f"{GRIDSAT_BASE}/{t:%Y}/{t:%m}/GridSat-GOES.{SAT}.{t:%Y}.{t:%m}.{t:%d}.{t:%H}00.v01.nc"


def nearest_key(target):
    if SOURCE == "gridsat":                    # hourly; round to nearest hour, search outward
        base = target.replace(minute=0, second=0, microsecond=0)
        if target.minute >= 30:
            base += dt.timedelta(hours=1)
        for off in (0, -1, 1, -2, 2, 3, -3):
            url = _gridsat_url(base + dt.timedelta(hours=off))
            try:
                if requests.head(url, timeout=25).status_code == 200:
                    return url
            except Exception:
                pass
        return None
    cands = []
    for off in (-1, 0, 1):
        t = target + dt.timedelta(hours=off)
        pre = f"{PRODUCT}/{t:%Y}/{t.timetuple().tm_yday:03d}/{t:%H}/"
        r = _S3.list_objects_v2(Bucket=BUCKET, Prefix=pre, MaxKeys=400)
        for o in r.get("Contents", []):
            if f"-M6{BAND}_" in o["Key"] or f"-M3{BAND}_" in o["Key"]:
                cands.append(o["Key"])
    if not cands:
        return None
    return min(cands, key=lambda k: abs((_fname_start(k) - target).total_seconds()))


def download(key):
    local = os.path.join(CACHE, key.split("/")[-1])
    if os.path.exists(local) and os.path.getsize(local) > 10000:
        return local
    if SOURCE == "gridsat":
        r = requests.get(key, timeout=300); r.raise_for_status()
        open(local, "wb").write(r.content)
    else:
        _S3.download_file(BUCKET, key, local)
    return local


def latlon_grid(ds):
    p = ds["goes_imager_projection"]
    H = p.perspective_point_height + p.semi_major_axis
    req = p.semi_major_axis; rpol = p.semi_minor_axis
    lon0 = math.radians(p.longitude_of_projection_origin)
    X, Y = np.meshgrid(ds["x"].values, ds["y"].values)
    sinx, cosx = np.sin(X), np.cos(X); siny, cosy = np.sin(Y), np.cos(Y)
    a = sinx**2 + cosx**2 * (cosy**2 + (req**2 / rpol**2) * siny**2)
    b = -2 * H * cosx * cosy
    c = H**2 - req**2
    disc = b**2 - 4 * a * c
    with np.errstate(invalid="ignore"):
        rs = (-b - np.sqrt(disc)) / (2 * a)
        sx = rs * cosx * cosy; sy = -rs * sinx; sz = rs * cosx * siny
        lat = np.degrees(np.arctan((req**2 / rpol**2) * sz / np.sqrt((H - sx) ** 2 + sy**2)))
        lon = np.degrees(lon0 - np.arctan(sy / (H - sx)))
    lat[disc < 0] = np.nan; lon[disc < 0] = np.nan
    return lat, lon


def load_crop(local):
    import xarray as xr
    ds = xr.open_dataset(local)
    if SOURCE == "gridsat":                    # regular lat/lon grid; var ch4 (Kelvin)
        if "rows" not in _GEO:
            lat1 = ds["lat"].values; lon1 = ds["lon"].values
            ri = np.where((lat1 >= LAT0) & (lat1 <= LAT1))[0]
            ci = np.where((lon1 >= LON0) & (lon1 <= LON1))[0]
            r0, r1, c0, c1 = ri.min(), ri.max() + 1, ci.min(), ci.max() + 1
            lon2d, lat2d = np.meshgrid(lon1[c0:c1], lat1[r0:r1])
            _GEO.update(rows=(r0, r1), cols=(c0, c1), lat=lat2d, lon=lon2d)
        (r0, r1) = _GEO["rows"]; (c0, c1) = _GEO["cols"]
        cmi = np.asarray(ds["ch4"].values).squeeze()[r0:r1, c0:c1] - 273.15
        ds.close()
        return _GEO["lon"], _GEO["lat"], cmi
    if "rows" not in _GEO:
        lat, lon = latlon_grid(ds)
        m = (lon >= LON0) & (lon <= LON1) & (lat >= LAT0) & (lat <= LAT1)
        rows = np.where(m.any(axis=1))[0]; cols = np.where(m.any(axis=0))[0]
        r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
        _GEO.update(rows=(r0, r1), cols=(c0, c1),
                    lat=lat[r0:r1, c0:c1], lon=lon[r0:r1, c0:c1])
    (r0, r1) = _GEO["rows"]; (c0, c1) = _GEO["cols"]
    cmi = ds["CMI"].values[r0:r1, c0:c1] - 273.15
    ds.close()
    return _GEO["lon"], _GEO["lat"], cmi


# ===================== colormaps =====================
def ir_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    vmax, vmin = 40.0, -90.0
    anchors = [(40, "#000000"), (20, "#171717"), (-20, "#c9c9c9"), (-31, "#ffffff"),
               (-41, "#00b44b"), (-53, "#f4e000"), (-63, "#ff7a00"),
               (-70, "#d40000"), (-76, "#ff45ff"), (-83, "#5a14a8"), (-90, "#ffffff")]
    stops = sorted(((T - vmin) / (vmax - vmin), col) for T, col in anchors)
    return LinearSegmentedColormap.from_list("ir_bd", stops), vmin, vmax


def d26_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    # shallow (teal) -> deep warm water (red), 0..180 m
    stops = [(0.0, "#0b2a3a"), (0.25, "#147d96"), (0.5, "#33c0b0"),
             (0.7, "#ffd24d"), (0.85, "#ff7a2c"), (1.0, "#ff2e3f")]
    return LinearSegmentedColormap.from_list("d26", stops)


_D26 = {}


def load_d26(path):
    p = os.path.join(HERE, path)
    if not os.path.exists(p):
        return None
    if p in _D26:
        return _D26[p]
    d = json.load(open(p))
    lats = np.array(d["lats"]); lons = np.array(d["lons"]); g = np.array(d["d26"], dtype=float)
    _D26[p] = (lons, lats, g)
    return _D26[p]


# ===================== track =====================
def load_fixes(stormname):
    g = json.load(open(os.path.join(HERE, "data", "storms.geojson")))
    pts = []
    for ft in g["features"]:
        p = ft["properties"]
        if str(p.get("name", "")).upper() == stormname.upper() and ft["geometry"]["type"] == "Point":
            lon, lat = ft["geometry"]["coordinates"]
            t = dt.datetime.strptime(f"{p['year']} {p['time_utc']}", "%Y %b %d %H%MZ")
            pts.append(dict(t=t, lat=lat, lon=lon, kt=p["wind_kt"], mb=p.get("pressure_mb"),
                            cat=p["category"], ri=bool(p.get("rapid_intensifying"))))
    pts.sort(key=lambda d: d["t"])
    return pts


def cat_color(kt):
    if kt >= 137: return RED
    if kt >= 113: return "#ff6b3d"
    if kt >= 96:  return AMBER
    if kt >= 83:  return "#ffe05a"
    if kt >= 64:  return "#fff2a8"
    if kt >= 34:  return TEAL
    return CYAN


def cat_label(kt):
    for thr, nm in [(137, "CAT 5"), (113, "CAT 4"), (96, "CAT 3"),
                    (83, "CAT 2"), (64, "CAT 1"), (34, "TROP STORM"), (0, "TROP DEPR")]:
        if kt >= thr: return nm
    return ""


def interp_pos(fixes, t):
    if t <= fixes[0]["t"]: return fixes[0]["lon"], fixes[0]["lat"], fixes[0]["kt"]
    if t >= fixes[-1]["t"]: return fixes[-1]["lon"], fixes[-1]["lat"], fixes[-1]["kt"]
    for a, b in zip(fixes, fixes[1:]):
        if a["t"] <= t <= b["t"]:
            f = (t - a["t"]).total_seconds() / (b["t"] - a["t"]).total_seconds()
            return (a["lon"] + f * (b["lon"] - a["lon"]),
                    a["lat"] + f * (b["lat"] - a["lat"]),
                    a["kt"] + f * (b["kt"] - a["kt"]))
    return fixes[-1]["lon"], fixes[-1]["lat"], fixes[-1]["kt"]


def geo_lines():
    out = []
    for f in ("ne_50m_coastline.geojson", "ne_50m_admin0.geojson"):
        p = os.path.join(HERE, "data", "geo", f)
        if not os.path.exists(p): continue
        g = json.load(open(p))
        for ft in g["features"]:
            gm = ft["geometry"]; tp = gm["type"]
            segs = [gm["coordinates"]] if tp == "LineString" else gm["coordinates"]
            for seg in segs:
                arr = np.array(seg)
                if arr.ndim != 2: continue
                m = (arr[:, 0] >= LON0 - 2) & (arr[:, 0] <= LON1 + 2) & \
                    (arr[:, 1] >= LAT0 - 2) & (arr[:, 1] <= LAT1 + 2)
                if m.sum() >= 2:
                    out.append(arr)
    return out


# ===================== HUD frame =====================
def render(t, cfg, fixes, lines, ir, vmin, vmax, d26, dcmap, outpath, dpi=120):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    key = nearest_key(t); local = download(key)
    lon, lat, cmi = load_crop(local)
    cmi_cloud = np.where(cmi > -10.0, np.nan, cmi)      # clouds only; clear sky -> D26 shows through
    actual = _fname_start(key)

    aspect = 1.0 / math.cos(math.radians((LAT0 + LAT1) / 2))
    lon_span = (LON1 - LON0); lat_span = (LAT1 - LAT0)
    fig_w = 11.5
    fig_h = fig_w * (lat_span * aspect) / lon_span
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_facecolor(NAVY)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(NAVY)
    ax.set_xlim(LON0, LON1); ax.set_ylim(LAT0, LAT1); ax.set_xticks([]); ax.set_yticks([])
    ax.set_aspect(aspect)

    # 1) D26 ocean-heat underlay
    if d26 is not None:
        dlon, dlat, dg = d26
        ax.pcolormesh(dlon, dlat, dg, cmap=dcmap, vmin=0, vmax=180, shading="auto",
                      alpha=0.85, zorder=1)
    # 2) coastlines
    for arr in lines:
        ax.plot(arr[:, 0], arr[:, 1], color="#8aa6c4", lw=0.8, alpha=0.7, zorder=2)
    # 3) IR clouds (transparent clear sky)
    ax.pcolormesh(lon, lat, cmi_cloud, cmap=ir, vmin=vmin, vmax=vmax, shading="auto", zorder=3)
    # 4) track
    past = [f for f in fixes if f["t"] <= t]
    if len(past) >= 2:
        ax.plot([f["lon"] for f in past], [f["lat"] for f in past], color="white",
                lw=1.6, alpha=0.85, zorder=4)
    for f in past:
        ax.plot(f["lon"], f["lat"], "o", ms=4.5, color=cat_color(f["kt"]),
                mec=(RED if f["ri"] else "white"), mew=1.1 if f["ri"] else 0.5, zorder=5)
    clon, clat, ckt = interp_pos(fixes, t)
    ax.plot(clon, clat, "o", ms=15, mfc="none", mec="white", mew=2.0, zorder=6)
    ax.plot(clon, clat, "o", ms=8, color=cat_color(ckt), zorder=7)

    # 5) HUD text
    in_ri = any(f["ri"] for f in fixes if abs((f["t"] - t).total_seconds()) <= 3 * 3600)
    tk = dict(transform=ax.transAxes, family="DejaVu Sans", zorder=12)
    ax.text(0.022, 0.95, f"HURRICANE {cfg['name'].upper()}  ·  {cfg['year']}", color=INK,
            fontsize=17, fontweight="bold", **tk)
    src_lbl = ("GOES-12 IR (GridSat-GOES ch4 ~10.7µm)" if SOURCE == "gridsat"
               else "GOES-16 ABI Band 13 (clean longwave IR)")
    ax.text(0.022, 0.915, src_lbl + "  ·  D26 ocean heat beneath",
            color=MUTE, fontsize=9.5, **tk)
    ax.text(0.022, 0.07, f"{actual:%b %d, %Y   %H:%M} UTC", color=INK, fontsize=14, fontweight="bold", **tk)
    ax.text(0.022, 0.032, f"{cat_label(ckt)}   ·   {round(ckt)} kt", color=cat_color(ckt),
            fontsize=14, fontweight="bold", **tk)
    if in_ri:
        ax.text(0.978, 0.955, "● RAPIDLY INTENSIFYING", color=RED, fontsize=12.5,
                fontweight="bold", ha="right", **tk)
    ax.text(0.978, 0.03, "RapidWatch", color=AMBER, fontsize=12, fontweight="bold", ha="right", **tk)

    # 6) intensity-vs-time trace (inset)
    iax = fig.add_axes([0.70, 0.10, 0.275, 0.20])
    iax.set_facecolor((0.04, 0.09, 0.17, 0.72))
    for s in iax.spines.values(): s.set_color("#3a5575")
    h0 = fixes[0]["t"]
    hrs = [(f["t"] - h0).total_seconds() / 3600 for f in fixes]
    kts = [f["kt"] for f in fixes]
    now_h = (t - h0).total_seconds() / 3600
    # RI-flagged span shading
    ri_h = [hh for hh, f in zip(hrs, fixes) if f["ri"]]
    if ri_h:
        iax.axvspan(min(ri_h), max(ri_h), color=RED, alpha=0.16)
    iax.plot(hrs, kts, color="#42597a", lw=1.2)                       # full curve faint
    pn = [(hh, kk) for hh, kk in zip(hrs, kts) if hh <= now_h]
    if pn:
        iax.plot([a for a, _ in pn], [b for _, b in pn], color=AMBER, lw=2.0)
        iax.plot(pn[-1][0], pn[-1][1], "o", ms=6, color=cat_color(pn[-1][1]),
                 mec="white", mew=1.0)
    for thr, c in [(64, "#fff2a8"), (96, AMBER), (137, RED)]:
        iax.axhline(thr, color=c, lw=0.5, alpha=0.35)
    iax.set_xlim(0, max(hrs)); iax.set_ylim(0, max(kts) * 1.12)
    iax.tick_params(colors="#9CB6D2", labelsize=7, length=2)
    iax.set_title("intensity (kt)", color=MUTE, fontsize=8, pad=2)
    iax.set_xlabel("hours", color=MUTE, fontsize=7, labelpad=1)

    fig.savefig(outpath, facecolor=NAVY)
    plt.close(fig)
    return actual


# ===================== clean overlay frame =====================
def render_clean(t, ir, vmin, vmax, outpath, dpi=100):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    key = nearest_key(t); local = download(key)
    lon, lat, cmi = load_crop(local)
    cmi = np.where(cmi > -10.0, np.nan, cmi)
    fig = plt.figure(figsize=(9.0, 9.0 * (LAT1 - LAT0) / (LON1 - LON0)), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.set_xlim(LON0, LON1); ax.set_ylim(LAT0, LAT1); ax.set_aspect("auto")
    ax.pcolormesh(lon, lat, cmi, cmap=ir, vmin=vmin, vmax=vmax, shading="auto")
    fig.savefig(outpath, transparent=True)
    plt.close(fig)
    return _fname_start(key)


# ===================== drivers =====================
def time_steps(cfg, minutes):
    s = dt.datetime(*cfg["start"]); e = dt.datetime(*cfg["end"])
    out = []; t = s
    while t <= e:
        out.append(t); t += dt.timedelta(minutes=minutes)
    return out


def encode_mp4(pattern, out, fps=18):
    import subprocess
    exe = __import__("imageio_ffmpeg").get_ffmpeg_exe()
    r = subprocess.run([exe, "-y", "-framerate", str(fps), "-i", pattern, "-c:v", "libx264",
                        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",   # H.264 needs even dims
                        "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", out],
                       capture_output=True, text=True)
    return r.returncode, r.stderr


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    if not args or args[0] not in STORMS:
        print("usage: make_storm_ri_animation.py <%s> [--test|--full|--overlay]" % "|".join(STORMS))
        return
    key = args[0]; cfg = STORMS[key]; setup(cfg)
    fixes = load_fixes(cfg["name"]); lines = geo_lines()
    ir, vmin, vmax = ir_cmap(); dcmap = d26_cmap(); d26 = load_d26(cfg["d26"])
    is_gridsat = cfg.get("source") == "gridsat"
    CADENCE = 60 if is_gridsat else 10        # GridSat is hourly
    FPS = 6 if is_gridsat else 9              # playback speed (slowed; gridsat has fewer frames)

    if "--overlay" in flags:
        import subprocess, glob
        cdir = os.path.join(HERE, "data", f"{key}_overlay_frames"); os.makedirs(cdir, exist_ok=True)
        outdir = os.path.join(HERE, "data", "overlays"); os.makedirs(outdir, exist_ok=True)
        times = time_steps(cfg, CADENCE)
        print(f"{cfg['name']} overlay: {len(times)} frames @ {CADENCE}-min")
        for i, t in enumerate(times):
            try:
                render_clean(t, ir, vmin, vmax, os.path.join(cdir, f"c{i:04d}.png"))
                if i % 40 == 0 or i == len(times) - 1: print(f"  [{i+1}/{len(times)}] {t:%b %d %H%MZ}")
            except Exception as e:
                print("  SKIP", t, type(e).__name__, e)
        exe = __import__("imageio_ffmpeg").get_ffmpeg_exe()
        pat = os.path.join(cdir, "c%04d.png")
        webm = os.path.join(outdir, f"{key}_ir.webm"); mp4 = os.path.join(outdir, f"{key}_ir.mp4")
        from PIL import Image
        W, H = Image.open(sorted(glob.glob(os.path.join(cdir, "c*.png")))[0]).size
        sW = 820; sH = round(H * 820 / W); sH += sH % 2          # web-optimized size, even dims
        r1 = subprocess.run([exe, "-y", "-framerate", str(FPS), "-i", pat, "-vf", "scale=820:-2",
                             "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0",
                             "-crf", "42", "-an", webm], capture_output=True, text=True)
        r2 = subprocess.run([exe, "-y", "-f", "lavfi", "-i", f"color=c=0x0A182B:s={sW}x{sH}:r={FPS}",
                             "-framerate", str(FPS), "-i", pat, "-filter_complex",
                             "[1:v]scale=820:-2[v];[0:v][v]overlay=shortest=1,format=yuv420p",
                             "-c:v", "libx264", "-crf", "32", "-movflags", "+faststart", mp4],
                            capture_output=True, text=True)
        print("webm", r1.returncode, os.path.getsize(webm) if os.path.exists(webm) else "-",
              "| mp4", r2.returncode, os.path.getsize(mp4) if os.path.exists(mp4) else "-")
        print("bounds: [[%.1f,%.1f],[%.1f,%.1f]]" % (LAT0, LON0, LAT1, LON1))
        return

    if "--full" in flags:
        fdir = os.path.join(HERE, "data", f"{key}_frames"); os.makedirs(fdir, exist_ok=True)
        times = time_steps(cfg, CADENCE)
        print(f"{cfg['name']} HUD: {len(times)} frames @ {CADENCE}-min")
        paths = []
        for i, t in enumerate(times):
            op = os.path.join(fdir, f"f{i:04d}.png")
            try:
                a = render(t, cfg, fixes, lines, ir, vmin, vmax, d26, dcmap, op)
                paths.append(op)
                if i % 40 == 0 or i == len(times) - 1: print(f"  [{i+1}/{len(times)}] {t:%b %d %H%MZ}")
            except Exception as e:
                print("  SKIP", t, type(e).__name__, e)
        out = os.path.join(HERE, f"{key}_RI_{cfg['year']}.mp4")
        rc, err = encode_mp4(os.path.join(fdir, "f%04d.png"), out, fps=FPS)
        print("HUD mp4", rc, os.path.getsize(out) if os.path.exists(out) else "-")
        if rc: print(err[-700:])
        return

    # default: --test, one HUD frame near peak
    peak = max(fixes, key=lambda f: f["kt"])
    out = os.path.join(HERE, f"{key}_test_frame.png")
    a = render(peak["t"], cfg, fixes, lines, ir, vmin, vmax, d26, dcmap, out)
    print(f"TEST {cfg['name']} -> {out} | peak {peak['kt']}kt @ {peak['t']:%b %d %H%MZ} | GOES {a}")


if __name__ == "__main__":
    main()
