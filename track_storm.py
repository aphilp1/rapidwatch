"""
track_storm.py — archive EVERYTHING about an active NHC storm, every run
================================================================================
Written 2026-10-07 for Tropical Storm Isaias (AL092026). Re-runnable; each run
adds only what is new (content-hashed), so it is safe every 30 min from the
live-data Action or by hand.

Archive root: data/storms/<STORMID>/
  currentstorms/<UTC>.json        NHC CurrentStorms entry for the storm (every run it changes)
  advisories/<product>_<advnum>.txt
                                  public advisory (TCP), forecast advisory (TCM), discussion
                                  (TCD), wind-speed probabilities (PWS) — one file per advisory
  gis/adv<advnum>_<kind>.geojson  cone / track / points / watch-warning / past track, per advisory
  ships/<cycle>AL<nn><yy>_ships.txt
                                  every operational SHIPS text (predictors + SHIPS-RII/DTOPS)
  recon/<file>                    every new HDOB (AHONT1) and vortex data message (REPNT2/URNT12)
                                  from the NHC recon archive since the storm started
  environment.csv                 one row per run: center fix + HYCOM SST/D26/current under the
                                  center + nearest Argo float / glider (from this repo's data)
  LOG.md                          one line per run, newest last

Sources (all public): nhc.noaa.gov CurrentStorms.json, text/refresh products, NOAA IDP
MapServer (same as build_live_data.py), ftp.nhc.noaa.gov/atcf/stext, nhc.noaa.gov/archive/recon.

Run:  python track_storm.py AL092026        (or no arg = every active Atlantic storm)
"""
import csv, datetime, hashlib, json, math, pathlib, re, sys, urllib.request

DIR = pathlib.Path(__file__).resolve().parent
DATA = DIR / "data"
UA = {"User-Agent": "RapidWatch storm archiver (aphilp1@gmail.com)"}
MAPSRV = ("https://mapservices.weather.noaa.gov/tropical/rest/services/"
          "tropical/NHC_tropical_weather/MapServer")
NHC_KINDS = {"Forecast Cone": "cone", "Forecast Track": "track", "Forecast Points": "points",
             "Watch-Warning": "ww", "Past Track": "past_track", "Past Points": "past_points"}
TEXT_PRODUCTS = {"TCP": "public_advisory", "TCM": "forecast_advisory", "TCD": "discussion", "PWS": "wind_probabilities"}
RECON_DIRS = ["AHONT1", "REPNT2", "URNT12"]       # HDOB, vortex data message, vortex data message (alt header)


def get(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def sha(b):
    return hashlib.sha1(b).hexdigest()[:12]


def write_new(path, data):
    """Write only if the content differs from the newest file with the same stem. Returns True if written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and sha(path.read_bytes()) == sha(data):
        return False
    path.write_bytes(data)
    return True


def strip_html(b):
    t = b.decode("utf-8", "replace")
    m = re.search(r"<pre[^>]*>(.*?)</pre>", t, re.S)
    t = m.group(1) if m else re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"&lt;", "<", t); t = re.sub(r"&gt;", ">", t); t = re.sub(r"&amp;", "&", t)
    return t.strip() + "\n"


def product_code(storm_num):
    return f"AT{((int(storm_num) - 1) % 5) + 1}"


def sample(grid, key, la, lo):
    if not grid:
        return None
    lats, lons, g = grid["lats"], grid["lons"], grid[key]
    ri = min(range(len(lats)), key=lambda i: abs(lats[i] - la))
    ci = min(range(len(lons)), key=lambda i: abs(lons[i] - lo))
    return g[ri][ci]


def load_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def nearest(features, la, lo, want_profile=False):
    best = None
    for f in features:
        p = f["properties"]
        if want_profile and "profile" not in p:
            continue
        c = f["geometry"]["coordinates"]
        if f["geometry"]["type"] != "Point":
            continue
        d = math.hypot((c[1] - la) * 111, (c[0] - lo) * 111 * math.cos(math.radians(la)))
        if best is None or d < best[0]:
            best = (d, p, c)
    return best


def archive_storm(s, layers, run_ts):
    sid = str(s.get("id", "")).upper()               # AL092026
    name = s.get("name", "?")
    num = sid[2:4]; yy = sid[-2:]
    root = DATA / "storms" / sid
    root.mkdir(parents=True, exist_ok=True)
    added = []

    # 1. CurrentStorms entry
    if write_new(root / "currentstorms" / f"{run_ts}.json", json.dumps(s, indent=1).encode()):
        # drop the file again if identical to the previous run's entry (keep only changes)
        prev = sorted((root / "currentstorms").glob("*.json"))
        if len(prev) >= 2 and sha(prev[-1].read_bytes()) == sha(prev[-2].read_bytes()):
            prev[-1].unlink()
        else:
            added.append("currentstorms")

    # 2. Text products, one file per advisory number
    code = product_code(num)
    adv = "?"
    for prod, label in TEXT_PRODUCTS.items():
        try:
            txt = strip_html(get(f"https://www.nhc.noaa.gov/text/refresh/MIA{prod}{code}+shtml/"))
        except Exception as e:
            added.append(f"{label} (fetch failed: {type(e).__name__})"); continue
        if name.upper() not in txt.upper()[:600]:
            continue                                   # product slot belongs to another storm
        m = re.search(r"(?:Advisory|Discussion|Probabilities) Number\s+(\d+[A-Z]?)", txt, re.I)
        n = m.group(1) if m else "x"
        if prod == "TCP":
            adv = n
        if write_new(root / "advisories" / f"{label}_{n.zfill(3)}.txt", txt.encode()):
            added.append(f"{label} #{n}")

    # 3. GIS layers per advisory
    bin_ = str(s.get("binNumber", "")).upper()
    for lname, suffix in NHC_KINDS.items():
        lid = layers.get(f"{bin_} {lname}")
        if lid is None:
            continue
        try:
            g = get(f"{MAPSRV}/{lid}/query?where=1%3D1&outFields=*&f=geojson")
            gj = json.loads(g)
            if not gj.get("features"):
                continue
            advn = str(gj["features"][0].get("properties", {}).get("advisnum", adv)).zfill(3)
            if write_new(root / "gis" / f"adv{advn}_{suffix}.geojson", g):
                added.append(f"gis {suffix} adv {advn}")
        except Exception as e:
            added.append(f"gis {suffix} (failed: {type(e).__name__})")

    # 3b. Backfill from NHC's archives, so a skipped run (GitHub delays the cron) loses nothing:
    #     every text product ever issued for the storm, every per-advisory GIS zip, and the
    #     ATCF working best track (b-deck) + model guidance (a-deck).
    year = sid[-4:]
    try:
        idx = get(f"https://www.nhc.noaa.gov/archive/{year}/{name.upper()}.shtml").decode("utf-8", "replace")
        prodmap = {"public": "public_advisory", "fstadv": "forecast_advisory", "discus": "discussion", "wndprb": "wind_probabilities"}
        for rel, prod, n in sorted(set(re.findall(rf'href="(/archive/{year}/al{num}/al{num}{year}\.(public|fstadv|discus|wndprb)\.(\d{{3}}[a-z]?)\.shtml)"', idx, re.I))):
            target = root / "advisories" / f"{prodmap[prod.lower()]}_{n.upper()}.txt"
            if target.exists():
                continue
            try:
                write_new(target, strip_html(get("https://www.nhc.noaa.gov" + rel)).encode())
                added.append(f"backfill {prodmap[prod.lower()]} #{n}")
            except Exception:
                pass
    except Exception as e:
        added.append(f"archive index (failed: {type(e).__name__})")
    try:
        idx = get("https://www.nhc.noaa.gov/gis/forecast/archive/").decode("utf-8", "replace")
        for fn in sorted(set(re.findall(rf'href="(al{num}{year}_(?:5day|fcst)_\d{{3}}[A-Za-z]?\.zip)"', idx, re.I))):
            target = root / "gis" / fn
            if not target.exists():
                try:
                    write_new(target, get(f"https://www.nhc.noaa.gov/gis/forecast/archive/{fn}", timeout=90))
                    added.append(f"gis zip {fn}")
                except Exception:
                    pass
    except Exception:
        pass
    for sub, fn in (("btk", f"bal{num}{year}.dat"), ("aid_public", f"aal{num}{year}.dat.gz")):
        try:
            if write_new(root / "atcf" / fn, get(f"https://ftp.nhc.noaa.gov/atcf/{sub}/{fn}", timeout=90)):
                added.append(f"atcf {fn}")
        except Exception:
            pass

    # 4. SHIPS text files
    try:
        idx = get("https://ftp.nhc.noaa.gov/atcf/stext/").decode("utf-8", "replace")
        for fn in sorted(set(re.findall(rf'href="(\d{{8}}AL{num}{yy}_ships\.txt)"', idx))):
            if not (root / "ships" / fn).exists():
                write_new(root / "ships" / fn, get(f"https://ftp.nhc.noaa.gov/atcf/stext/{fn}"))
                added.append(f"ships {fn[:8]}")
    except Exception as e:
        added.append(f"ships (failed: {type(e).__name__})")

    # 5. Recon products since the storm's first archived run
    first = sorted((root / "currentstorms").glob("*.json"))
    since = first[0].stem[:8] if first else run_ts[:8]          # YYYYMMDD
    for d in RECON_DIRS:
        try:
            idx = get(f"https://www.nhc.noaa.gov/archive/recon/{utcnow().year}/{d}/").decode("utf-8", "replace")
        except Exception:
            continue
        for fn in sorted(set(re.findall(rf'href="({d}-[A-Z]{{4}}\.(\d{{12}})\.txt)"', idx))):
            fname, stamp = fn
            if stamp[:8] < since or (root / "recon" / fname).exists():
                continue
            try:
                body = get(f"https://www.nhc.noaa.gov/archive/recon/{utcnow().year}/{d}/{fname}")
                head = body[:400].decode("utf-8", "replace").upper()
                # keep this storm's missions and synoptic-surveillance (G-IV "SURV") flights only
                if name.upper() not in head and "SURV" not in head:
                    continue
                write_new(root / "recon" / fname, body)
                added.append(f"recon {fname}")
            except Exception:
                pass

    # 6. Environment under the center from this repo's ocean data
    la, lo = float(s.get("latitudeNumeric")), float(s.get("longitudeNumeric"))
    sst = load_json(DATA / "ocean" / "hycom_sst.json"); d26 = load_json(DATA / "ocean" / "hycom_d26.json")
    cur = load_json(DATA / "ocean" / "hycom_currents.json")
    u = sample(cur, "u", la, lo); v = sample(cur, "v", la, lo)
    argo = load_json(DATA / "argo" / "argo_gulf.geojson") or {"features": []}
    gl = load_json(DATA / "gliders" / "gliders_gulf.geojson") or {"features": []}
    na = nearest(argo["features"], la, lo, want_profile=True)
    ng = nearest([f for f in gl["features"] if f["properties"].get("kind") == "now"], la, lo)
    ships_rii = ""
    try:
        latest = sorted((root / "ships").glob("*_ships.txt"))[-1].read_text(errors="replace")
        m = re.search(r"SHIPS Prob RI for 30kt/ 24hr RI threshold=\s*(\d+)%", latest)
        ships_rii = m.group(1) if m else ""
    except Exception:
        pass
    row = {"run_utc": run_ts, "advisory": adv, "update": s.get("lastUpdate"), "class": s.get("classification"),
           "lat": la, "lon": lo, "vmax_kt": s.get("intensity"), "mslp_mb": s.get("pressure"),
           "motion": f"{s.get('movementDir')}@{s.get('movementSpeed')}",
           "hycom_time": (sst or {}).get("time_utc", ""), "hycom_sst_c": sample(sst, "sst", la, lo),
           "hycom_d26_m": sample(d26, "d26", la, lo),
           "hycom_current_ms": round(math.hypot(u, v), 2) if u is not None and v is not None else "",
           "argo_id": na[1]["platform"] if na else "", "argo_km": round(na[0]) if na else "",
           "argo_date": na[1]["time"][:10] if na else "", "argo_d26_m": na[1].get("d26") if na else "",
           "argo_surf_c": (na[1].get("surface") or {}).get("temperature") if na else "",
           "glider_id": ng[1]["id"] if ng else "", "glider_km": round(ng[0]) if ng else "",
           "ships_rii_30kt24h_pct": ships_rii}
    envp = root / "environment.csv"
    new = not envp.exists()
    with open(envp, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if new:
            w.writeheader()
        w.writerow(row)

    # 7. Log line
    line = (f"- {run_ts} UTC · adv {adv} · {s.get('classification')} {name} {s.get('intensity')} kt "
            f"{s.get('pressure')} mb at {la:.1f}N {abs(lo):.1f}W moving {s.get('movementDir')}° @ {s.get('movementSpeed')} kt · "
            f"HYCOM SST {row['hycom_sst_c']} °C D26 {row['hycom_d26_m']} m · SHIPS-RII 30kt/24h {ships_rii or '–'}% · "
            f"new: {', '.join(added) if added else 'nothing'}\n")
    logp = root / "LOG.md"
    if not logp.exists():
        logp.write_text(f"# {name} ({sid}) — archive log\n\nOne line per run (UTC). Files under this folder are the raw sources.\n\n", encoding="utf-8")
    with open(logp, "a", encoding="utf-8") as f:
        f.write(line)
    print(line.strip())
    return added


def main(only=None):
    run_ts = utcnow().strftime("%Y%m%dT%H%M")
    cs = json.loads(get("https://www.nhc.noaa.gov/CurrentStorms.json"))
    storms = [s for s in cs.get("activeStorms", []) if str(s.get("id", "")).upper().startswith("AL")]
    if only:
        storms = [s for s in storms if str(s.get("id", "")).upper() == only.upper()]
    if not storms:
        print("no matching active Atlantic storm"); return
    svc = json.loads(get(f"{MAPSRV}?f=json"))
    layers = {l["name"]: l["id"] for l in svc.get("layers", [])}
    for s in storms:
        archive_storm(s, layers, run_ts)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
