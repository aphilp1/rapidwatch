"""
build_live_data.py  —  RapidWatch live-data fetcher (runs in GitHub Actions, server-side).

NDBC buoy obs and NHC active-storm cone/track have NO CORS headers, so a browser
cannot fetch them directly from the GitHub Pages site. This script runs in CI (no
CORS there), downloads them, and saves them as SAME-ORIGIN files in the repo:

    data/ndbc/<id>.txt                      raw NDBC realtime2 (parsed by the page as-is)
    data/nhc_currentstorms.json             NHC CurrentStorms.json (verbatim)
    data/nhc/<ID>_5day_{pgn,lin,pts}.geojson cone / track / points for each active storm

The page fetches these same-origin paths instead of a flaky public CORS proxy.
Resilient by design: if a source is briefly unavailable, the previous file is kept
(last-known-good) rather than overwritten with nothing.
"""
import json, pathlib, urllib.request, urllib.error

DIR  = pathlib.Path(__file__).resolve().parent
DATA = DIR / "data"
UA   = "RapidWatch/1.0 (+https://github.com/aphilp1/rapidwatch)"

BUOYS = ["42001", "42002", "42036", "42039", "42040", "42055"]

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def save_if_ok(path, data, min_bytes=1):
    """Write only if we actually got plausible data; else keep last-known-good."""
    if data and len(data) >= min_bytes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return True
    return False

def main():
    ok, kept = [], []

    # ── NDBC buoys ────────────────────────────────────────────────────────────
    # The raw realtime2 file holds ~45 days of obs (~600 KB). The page only reads
    # the latest row, so trim to the 2 header lines + the 12 most-recent rows
    # (~1 KB) to keep git history small. Newest rows are first in the file.
    for bid in BUOYS:
        out = DATA / "ndbc" / f"{bid}.txt"
        try:
            raw = get(f"https://www.ndbc.noaa.gov/data/realtime2/{bid}.txt")
            lines = raw.split(b"\n")
            headers = [l for l in lines if l.startswith(b"#")]
            rows    = [l for l in lines if l.strip() and not l.startswith(b"#")]
            if b"#YY" in raw[:200] and rows:
                trimmed = b"\n".join(headers + rows[:12]) + b"\n"
                if save_if_ok(out, trimmed, 100):
                    ok.append(f"ndbc/{bid}")
            else:
                kept.append(f"ndbc/{bid} (bad payload)")
        except Exception as e:
            kept.append(f"ndbc/{bid} ({type(e).__name__})")

    # ── NHC active-storm cone / track / points / watches / past track ─────────
    # NHC discontinued the storm_graphics/api/*_5day_*.geojson products (404 since
    # ~2026). Source is now the NOAA IDP ArcGIS MapServer, which serves the same
    # cone/track/points per storm *bin* (AT1..AT5, EP1..) as GeoJSON queries.
    # Output filenames are unchanged so the map pages keep working.
    MAPSRV = ("https://mapservices.weather.noaa.gov/tropical/rest/services/"
              "tropical/NHC_tropical_weather/MapServer")
    # layer-name suffix -> output filename suffix
    NHC_KINDS = {
        "Forecast Cone":   "5day_pgn",
        "Forecast Track":  "5day_lin",
        "Forecast Points": "5day_pts",
        "Watch-Warning":   "ww",
        "Past Track":      "past_lin",
        "Past Points":     "past_pts",
    }
    try:
        cs_raw = get("https://www.nhc.noaa.gov/CurrentStorms.json")
        cs = json.loads(cs_raw)
        save_if_ok(DATA / "nhc_currentstorms.json", cs_raw, 2)
        ok.append("nhc_currentstorms.json")
        storms = cs.get("activeStorms", []) or []
        layers = {}
        if storms:  # bin -> layer-id map, e.g. "AT2 Forecast Cone" -> 34
            svc = json.loads(get(f"{MAPSRV}?f=json"))
            layers = {l["name"]: l["id"] for l in svc.get("layers", [])}
        for s in storms:
            sid = str(s.get("id", "")).upper()
            bin_ = str(s.get("binNumber", "")).upper()
            if not sid or not bin_:
                continue
            for lname, suffix in NHC_KINDS.items():
                lid = layers.get(f"{bin_} {lname}")
                if lid is None:
                    kept.append(f"nhc/{sid}_{suffix} (no layer)")
                    continue
                try:
                    g = get(f"{MAPSRV}/{lid}/query?where=1%3D1&outFields=*&f=geojson")
                    gj = json.loads(g)
                    if suffix == "5day_pts":
                        # legacy prop aliases the Gulf Map popup reads
                        for f_ in gj.get("features", []):
                            p = f_.get("properties", {})
                            p.setdefault("MAXWIND", p.get("maxwind"))
                            p.setdefault("VALIDTIME", p.get("validtime"))
                        g = json.dumps(gj).encode()
                    if gj.get("features") and save_if_ok(
                            DATA / "nhc" / f"{sid}_{suffix}.geojson", g, 2):
                        ok.append(f"nhc/{sid}_{suffix}")
                except Exception as e:
                    kept.append(f"nhc/{sid}_{suffix} ({type(e).__name__})")
        print(f"  NHC active storms: {len(storms)}")
    except Exception as e:
        kept.append(f"nhc_currentstorms ({type(e).__name__})")

    print("  fetched OK :", ", ".join(ok) or "none")
    print("  skipped    :", ", ".join(kept) or "none")

if __name__ == "__main__":
    main()
