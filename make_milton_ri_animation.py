#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
make_milton_ri_animation.py
EXPERIMENT: reconstruct Hurricane Milton (2024) going through rapid intensification
from real GOES-16 ABI Band-13 (clean longwave IR) imagery on AWS, with the HURDAT2
best track overlaid frame-by-frame.

  python make_milton_ri_animation.py            # render ONE test frame (peak) -> verify look
  python make_milton_ri_animation.py --full     # download window + render all frames + encode mp4

Data: s3://noaa-goes16/ABI-L2-CMIPC (public, unsigned). Track: data/storms.geojson.
"""
import os, sys, json, math, datetime as dt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "goes_cache")
FRAMES = os.path.join(HERE, "data", "milton_frames")
os.makedirs(CACHE, exist_ok=True); os.makedirs(FRAMES, exist_ok=True)

# ---- Gulf crop (lon/lat) ----
LON0, LON1, LAT0, LAT1 = -98.0, -80.0, 16.5, 28.5
BUCKET = "noaa-goes16"
PRODUCT = "ABI-L2-CMIPC"   # CONUS sector, 5-min, ~4 MB/band
BAND = "C13"

# ---- palette (RapidWatch) ----
NAVY = "#0A182B"; INK = "#ECF3FB"; MUTE = "#9CB6D2"
AMBER = "#FFB24D"; RED = "#FF3B5C"; TEAL = "#3CDDC9"; CYAN="#7FE3FF"

# ===================== GOES helpers =====================
import boto3
from botocore import UNSIGNED
from botocore.config import Config
_S3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))


def _fname_start(key):
    tok = key.split("_s")[1]
    yr = int(tok[0:4]); doy = int(tok[4:7]); hh = int(tok[7:9]); mm = int(tok[9:11]); ss = int(tok[11:13])
    return dt.datetime(yr, 1, 1) + dt.timedelta(days=doy - 1, hours=hh, minutes=mm, seconds=ss)


def nearest_key(target):
    """Find the CMIPC C13 file whose scan start is nearest `target` (searches its hour +/- 1h)."""
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
    if not (os.path.exists(local) and os.path.getsize(local) > 10000):
        _S3.download_file(BUCKET, key, local)
    return local


# ---- ABI fixed grid -> lat/lon (computed once; grid is identical across files) ----
_GEO = {}


def latlon_grid(ds):
    p = ds["goes_imager_projection"]
    H = p.perspective_point_height + p.semi_major_axis
    req = p.semi_major_axis; rpol = p.semi_minor_axis
    lon0 = math.radians(p.longitude_of_projection_origin)
    x = ds["x"].values * 1.0  # scan angle (rad), already scaled by xarray
    y = ds["y"].values * 1.0
    X, Y = np.meshgrid(x, y)
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
    """Return cropped lon2d, lat2d, brightnessC for the Gulf box (cache slice indices)."""
    import xarray as xr
    ds = xr.open_dataset(local)
    if "rows" not in _GEO:
        lat, lon = latlon_grid(ds)
        m = (lon >= LON0) & (lon <= LON1) & (lat >= LAT0) & (lat <= LAT1)
        rows = np.where(m.any(axis=1))[0]; cols = np.where(m.any(axis=0))[0]
        r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
        _GEO.update(rows=(r0, r1), cols=(c0, c1),
                    lat=lat[r0:r1, c0:c1], lon=lon[r0:r1, c0:c1])
    (r0, r1) = _GEO["rows"]; (c0, c1) = _GEO["cols"]
    cmi = ds["CMI"].values[r0:r1, c0:c1] - 273.15  # K -> C
    ds.close()
    return _GEO["lon"], _GEO["lat"], cmi


# ===================== IR enhancement colormap =====================
def ir_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    vmax, vmin = 40.0, -90.0
    anchors = [(40, "#000000"), (20, "#171717"), (-20, "#c9c9c9"), (-31, "#ffffff"),
               (-41, "#00b44b"), (-53, "#f4e000"), (-63, "#ff7a00"),
               (-70, "#d40000"), (-76, "#ff45ff"), (-83, "#5a14a8"), (-90, "#ffffff")]
    # match pcolormesh normalization: position = (value - vmin)/(vmax - vmin)
    stops = sorted(((T - vmin) / (vmax - vmin), col) for T, col in anchors)
    return LinearSegmentedColormap.from_list("ir_bd", stops), vmin, vmax


# ===================== track =====================
def milton_fixes():
    g = json.load(open(os.path.join(HERE, "data", "storms.geojson")))
    pts = []
    for ft in g["features"]:
        p = ft["properties"]
        if str(p.get("name", "")).upper() == "MILTON" and ft["geometry"]["type"] == "Point":
            lon, lat = ft["geometry"]["coordinates"]
            t = dt.datetime.strptime(f"2024 {p['time_utc']}", "%Y %b %d %H%MZ")
            pts.append(dict(t=t, lat=lat, lon=lon, kt=p["wind_kt"], mb=p.get("pressure_mb"),
                            cat=p["category"], ri=bool(p.get("rapid_intensifying"))))
    pts.sort(key=lambda d: d["t"])
    return pts


def cat_color(kt):
    if kt >= 137: return RED        # Cat5
    if kt >= 113: return "#ff6b3d"  # Cat4
    if kt >= 96:  return AMBER      # Cat3
    if kt >= 83:  return "#ffe05a"  # Cat2
    if kt >= 64:  return "#fff2a8"  # Cat1
    if kt >= 34:  return TEAL       # TS
    return CYAN                     # TD


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


# ===================== geo lines =====================
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


# ===================== render one frame =====================
def render(t, fixes, lines, cmap, vmin, vmax, outpath, dpi=130):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    key = nearest_key(t)
    local = download(key)
    lon, lat, cmi = load_crop(local)
    actual = _fname_start(key)

    fig = plt.figure(figsize=(11.5, 8.0), dpi=dpi)
    fig.patch.set_facecolor(NAVY)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0]); ax.set_facecolor(NAVY)
    ax.set_xlim(LON0, LON1); ax.set_ylim(LAT0, LAT1)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_aspect(1.0 / math.cos(math.radians((LAT0 + LAT1) / 2)))  # equal-area-ish

    ax.pcolormesh(lon, lat, cmi, cmap=cmap, vmin=vmin, vmax=vmax, shading="auto", zorder=1)
    for arr in lines:
        ax.plot(arr[:, 0], arr[:, 1], color="#5d7da0", lw=0.8, alpha=0.75, zorder=2)

    past = [f for f in fixes if f["t"] <= t]
    if len(past) >= 2:
        ax.plot([f["lon"] for f in past], [f["lat"] for f in past],
                color="white", lw=1.6, alpha=0.85, zorder=3)
    for f in past:  # past fixes as small dots, colored by intensity & RI-ringed
        ax.plot(f["lon"], f["lat"], "o", ms=4.5, color=cat_color(f["kt"]),
                mec=(RED if f["ri"] else "white"), mew=1.1 if f["ri"] else 0.5, zorder=4)
    clon, clat, ckt = interp_pos(fixes, t)
    ax.plot(clon, clat, "o", ms=15, mfc="none", mec="white", mew=2.0, zorder=5)
    ax.plot(clon, clat, "o", ms=8, color=cat_color(ckt), zorder=6)

    # ---- HUD ----
    def cat_label(kt):
        for thr, nm in [(137, "CAT 5"), (113, "CAT 4"), (96, "CAT 3"),
                        (83, "CAT 2"), (64, "CAT 1"), (34, "TROP STORM"), (0, "TROP DEPR")]:
            if kt >= thr: return nm
        return ""
    in_ri = any(f["ri"] for f in fixes if abs((f["t"] - t).total_seconds()) <= 3 * 3600)
    txtkw = dict(transform=ax.transAxes, family="DejaVu Sans", zorder=10)
    ax.text(0.025, 0.95, "HURRICANE MILTON  ·  2024", color=INK, fontsize=17, fontweight="bold", **txtkw)
    ax.text(0.025, 0.915, "GOES-16 ABI Band 13 (clean longwave IR)", color=MUTE, fontsize=10, **txtkw)
    ax.text(0.025, 0.075, f"{actual:%b %d, %Y   %H:%M} UTC", color=INK, fontsize=14, fontweight="bold", **txtkw)
    col = cat_color(ckt)
    ax.text(0.025, 0.035, f"{cat_label(ckt)}   ·   {round(ckt)} kt", color=col, fontsize=14, fontweight="bold", **txtkw)
    if in_ri:
        ax.text(0.975, 0.035, "● RAPIDLY INTENSIFYING", color=RED, fontsize=13, fontweight="bold",
                ha="right", **txtkw)
    # colorbar-ish legend caption
    ax.text(0.975, 0.95, "RapidWatch", color=AMBER, fontsize=12, fontweight="bold", ha="right", **txtkw)

    fig.savefig(outpath, facecolor=NAVY)
    plt.close(fig)
    return actual


# ===================== clean georeferenced overlay (for the map) =====================
def render_clean(t, cmap, vmin, vmax, outpath, mask_warmer_than=-10.0, dpi=100):
    """Transparent IR-only frame, lon/lat linear, mapped exactly to [LON0,LON1]x[LAT0,LAT1]
    so it can ride on the RapidWatch map as an L.videoOverlay. Clear sky -> transparent."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    key = nearest_key(t); local = download(key)
    lon, lat, cmi = load_crop(local)
    cmi = np.where(cmi > mask_warmer_than, np.nan, cmi)   # hide clear/warm -> transparent
    fig = plt.figure(figsize=(9.0, 6.0), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.set_xlim(LON0, LON1); ax.set_ylim(LAT0, LAT1); ax.set_aspect("auto")
    ax.pcolormesh(lon, lat, cmi, cmap=cmap, vmin=vmin, vmax=vmax, shading="auto")
    fig.savefig(outpath, transparent=True)
    plt.close(fig)
    return _fname_start(key)


def build_overlay():
    """Render the clean window and encode milton_ir.webm (VP9 alpha) + .mp4 (opaque fallback)."""
    import subprocess, glob
    cmap, vmin, vmax = ir_cmap()
    cdir = os.path.join(HERE, "data", "milton_overlay_frames"); os.makedirs(cdir, exist_ok=True)
    outdir = os.path.join(HERE, "data", "overlays"); os.makedirs(outdir, exist_ok=True)
    start = dt.datetime(2024, 10, 5, 12, 0); end = dt.datetime(2024, 10, 8, 0, 0)
    step = dt.timedelta(minutes=30)
    times = []; t = start
    while t <= end:
        times.append(t); t += step
    print(f"Clean overlay: {len(times)} frames")
    for i, t in enumerate(times):
        op = os.path.join(cdir, f"c{i:04d}.png")
        try:
            render_clean(t, cmap, vmin, vmax, op)
            if i % 20 == 0 or i == len(times) - 1:
                print(f"  [{i+1}/{len(times)}] {t:%b %d %H%MZ}")
        except Exception as e:
            print(f"  SKIP {t:%b %d %H%MZ}: {type(e).__name__} {e}")
    exe = __import__("imageio_ffmpeg").get_ffmpeg_exe()
    pat = os.path.join(cdir, "c%04d.png")
    webm = os.path.join(outdir, "milton_ir.webm")
    mp4 = os.path.join(outdir, "milton_ir.mp4")
    # VP9 with alpha (transparent clear sky)
    r1 = subprocess.run([exe, "-y", "-framerate", "12", "-i", pat, "-c:v", "libvpx-vp9",
                         "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "34", "-an", webm],
                        capture_output=True, text=True)
    print("webm exit", r1.returncode, "bytes", os.path.getsize(webm) if os.path.exists(webm) else "-")
    if r1.returncode: print(r1.stderr[-800:])
    # opaque mp4 fallback: composite transparent frames over dark navy
    from PIL import Image
    W, H = Image.open(sorted(glob.glob(os.path.join(cdir, "c*.png")))[0]).size
    r2 = subprocess.run([exe, "-y", "-f", "lavfi", "-i", f"color=c=0x0A182B:s={W}x{H}:r=12",
                         "-framerate", "12", "-i", pat,
                         "-filter_complex", "[0:v][1:v]overlay=shortest=1,format=yuv420p",
                         "-c:v", "libx264", "-crf", "23", "-movflags", "+faststart", mp4],
                        capture_output=True, text=True)
    print("mp4  exit", r2.returncode, "bytes", os.path.getsize(mp4) if os.path.exists(mp4) else "-")
    if r2.returncode: print(r2.stderr[-800:])
    print("bounds for Leaflet: [[%.1f,%.1f],[%.1f,%.1f]]" % (LAT0, LON0, LAT1, LON1))


# ===================== main =====================
def main():
    if "--overlay" in sys.argv:
        build_overlay(); return
    full = "--full" in sys.argv
    fixes = milton_fixes()
    lines = geo_lines()
    cmap, vmin, vmax = ir_cmap()

    if not full:
        t = dt.datetime(2024, 10, 7, 18, 0)  # peak RI / Cat 5
        out = os.path.join(HERE, "milton_test_frame.png")
        a = render(t, fixes, lines, cmap, vmin, vmax, out, dpi=130)
        print("TEST frame ->", out, "| GOES scan", a)
        return

    # full window: TD through Cat 5
    start = dt.datetime(2024, 10, 5, 12, 0)
    end = dt.datetime(2024, 10, 8, 0, 0)
    step = dt.timedelta(minutes=30)
    times = []
    t = start
    while t <= end:
        times.append(t); t += step
    print(f"Rendering {len(times)} frames {start:%b %d %H%MZ} -> {end:%b %d %H%MZ}")
    paths = []
    for i, t in enumerate(times):
        op = os.path.join(FRAMES, f"f{i:04d}.png")
        try:
            a = render(t, fixes, lines, cmap, vmin, vmax, op, dpi=120)
            paths.append(op)
            if i % 10 == 0 or i == len(times) - 1:
                print(f"  [{i+1}/{len(times)}] {t:%b %d %H%MZ}  (GOES {a:%H:%M})")
        except Exception as e:
            print(f"  SKIP {t:%b %d %H%MZ}: {type(e).__name__} {e}")

    # encode mp4 (hold last frame a beat)
    import imageio.v2 as imageio
    os.environ.setdefault("IMAGEIO_FFMPEG_EXE", __import__("imageio_ffmpeg").get_ffmpeg_exe())
    mp4 = os.path.join(HERE, "milton_RI_2024.mp4")
    with imageio.get_writer(mp4, fps=12, codec="libx264", quality=8,
                            macro_block_size=None) as w:
        for p in paths:
            w.append_data(imageio.imread(p))
        for _ in range(18):
            w.append_data(imageio.imread(paths[-1]))
    print("MP4 ->", mp4, "frames:", len(paths))


if __name__ == "__main__":
    main()
