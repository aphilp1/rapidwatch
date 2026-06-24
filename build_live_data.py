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

    # ── NHC active-storm cone / track / points ────────────────────────────────
    try:
        cs_raw = get("https://www.nhc.noaa.gov/CurrentStorms.json")
        cs = json.loads(cs_raw)
        save_if_ok(DATA / "nhc_currentstorms.json", cs_raw, 2)
        ok.append("nhc_currentstorms.json")
        storms = cs.get("activeStorms", []) or []
        for s in storms:
            sid = str(s.get("id", "")).upper()
            if not sid:
                continue
            for kind in ("pgn", "lin", "pts"):
                url = f"https://www.nhc.noaa.gov/storm_graphics/api/{sid}_5day_{kind}.geojson"
                try:
                    g = get(url)
                    if save_if_ok(DATA / "nhc" / f"{sid}_5day_{kind}.geojson", g, 2):
                        ok.append(f"nhc/{sid}_{kind}")
                except Exception as e:
                    kept.append(f"nhc/{sid}_{kind} ({type(e).__name__})")
        print(f"  NHC active storms: {len(storms)}")
    except Exception as e:
        kept.append(f"nhc_currentstorms ({type(e).__name__})")

    print("  fetched OK :", ", ".join(ok) or "none")
    print("  skipped    :", ", ".join(kept) or "none")

if __name__ == "__main__":
    main()
