"""
ri_event_record.py — build the rapid-intensification record for an archived storm
================================================================================
Reads ONLY what track_storm.py has archived under data/storms/<ID>/ (plus this
repo's ocean/float/glider data and, when available, the git history of the HYCOM
snapshots) and writes, in the same folder:

  ri_timeline.csv       one row per best-track fix: intensity, 24-h change, RI flag,
                        the SHIPS predictors for that cycle (0-h column), NHC's
                        SHIPS-RII / DTOPS / consensus probabilities, our rebuilt-RII
                        probability, HYCOM SST / D26 / current under the fix from the
                        snapshot nearest in time, nearest Argo float and glider
  vortex_fixes.csv      every aircraft center fix (vortex data messages): time,
                        position, minimum pressure, eye, max flight-level wind
  RI_EVENT_RECORD.md    the human-readable record: when RI began and was met by the
                        30 kt / 24 h definition, the measurements at those moments,
                        the factor table across the event, and NHC's own intensity
                        reasoning quoted from each discussion

Re-runnable: regenerates from the archive every time (track_storm.py calls it).
Run:  python ri_event_record.py AL092026
"""
import csv, datetime, json, math, pathlib, re, subprocess, sys

DIR = pathlib.Path(__file__).resolve().parent
DATA = DIR / "data"
COEF = DATA / "ri_model" / "live_rii_coefficients.json"
RI_KT, RI_H = 30, 24


# ── helpers ──────────────────────────────────────────────────────────────────────
def parse_bdeck(path):
    fixes = {}
    for line in path.read_text(errors="replace").splitlines():
        p = [x.strip() for x in line.split(",")]
        if len(p) < 11 or p[4] != "BEST":
            continue
        t = datetime.datetime.strptime(p[2], "%Y%m%d%H").replace(tzinfo=datetime.timezone.utc)
        lat = float(p[6][:-1]) / 10 * (1 if p[6].endswith("N") else -1)
        lon = float(p[7][:-1]) / 10 * (-1 if p[7].endswith("W") else 1)
        fixes[t] = {"time": t, "lat": lat, "lon": lon, "vmax": int(p[8]), "mslp": int(p[9]) if p[9] else None, "type": p[10]}
    return [fixes[k] for k in sorted(fixes)]


def row_vals(text, label):
    m = re.search(r"^\s*" + re.escape(label) + r"\s+(.+)$", text, re.M)
    if not m:
        return None
    out = []
    for tok in m.group(1).split():
        try:
            out.append(float(tok))
        except ValueError:
            out.append(None)
    return out


def parse_ships(path):
    t = path.read_text(errors="replace")
    head = re.search(r"\*\s+(\S+)\s+(AL\d{6})\s+(\d\d)/(\d\d)/(\d\d)\s+(\d\d) UTC", t)
    if not head:
        return None
    mm, dd, yy, hh = head.group(3), head.group(4), head.group(5), head.group(6)
    when = datetime.datetime(2000 + int(yy), int(mm), int(dd), int(hh), tzinfo=datetime.timezone.utc)
    g = lambda lab, i=0: (row_vals(t, lab) or [None])[i] if row_vals(t, lab) else None
    v0 = g("V (KT) NO LAND")
    t12 = re.search(r"T-12 MAX WIND:\s*([-\d.]+)", t)
    d = {"ships_time": when, "vmax": v0, "per12": (v0 - float(t12.group(1))) if (t12 and v0 is not None) else None,
         "shear_kt": g("SHEAR (KT)"), "shear_dir": g("SHEAR DIR"), "sst_c": g("SST (C)"), "mpi_kt": g("POT. INT. (KT)"),
         "pot_kt": (g("POT. INT. (KT)") - v0) if (g("POT. INT. (KT)") is not None and v0 is not None) else None,
         "rh_700_500": g("700-500 MB RH"), "d200": g("200 MB DIV"), "ohc_kjcm2": g("HEAT CONTENT"),
         "vort850": g("850 MB ENV VOR"), "tadv": g("700-850 TADV"), "storm_speed_kt": g("STM SPEED (KT)"),
         "t200_c": g("200 MB T (C)"), "land_km": g("LAND (KM)"),
         "ships_fcst_24h_kt": (row_vals(t, "V (KT) LAND") or [None] * 5)[4]}
    for lab, key in (("GOES IR BRIGHTNESS TEMP. STD DEV.  50-200 KM RAD:", "ir_std"), ("% GOES IR PIXELS WITH T < -20 C    50-200 KM RAD:", "ir_pct_cold")):
        m = re.search(re.escape(lab) + r"\s*([-\d.]+)", t)
        d[key] = float(m.group(1)) if m else None
    cols = ["20/12", "25/24", "30/24", "35/24", "40/24", "45/36", "55/48", "65/72"]
    for line in t.splitlines():
        m = re.match(r"\s*(SHIPS-RII|DTOPS|Consensus):\s*(.+)", line)
        if m:
            vals = [float(x.strip("%")) for x in m.group(2).split()]
            for c, v in zip(cols, vals):
                d[f"nhc_{m.group(1).lower()}_{c.replace('/', 'kt')}h_pct"] = v
    return d


def our_rii(coef, s, thr="30"):
    """Rebuilt SHIPS-RII (gulf-ri-model baseline) on the 0-h predictors of a SHIPS cycle."""
    if not coef or s is None or s.get("shear_kt") is None:
        return None
    x = [s["per12"], s["shear_kt"] * 10, s["d200"], s["rh_700_500"], s["pot_kt"], s["ohc_kjcm2"]]
    if any(v is None for v in x):
        return None
    c = coef["thresholds"][thr]
    z = sum(((xi - m) / sd) * w for xi, m, sd, w in zip(x, c["mean"], c["std"], c["coef"])) + c["intercept"]
    return round(100 / (1 + math.exp(-z)), 1)


def hycom_snapshots():
    """{commit datetime: sha} for data/ocean/hycom_d26.json, newest first (empty if no git history)."""
    try:
        out = subprocess.run(["git", "log", "--format=%H %cI", "--", "data/ocean/hycom_d26.json"], cwd=DIR,
                             capture_output=True, text=True, timeout=60).stdout.split("\n")
        snaps = []
        for line in out:
            if line.strip():
                sha, iso = line.split()
                snaps.append((datetime.datetime.fromisoformat(iso).astimezone(datetime.timezone.utc), sha))
        return snaps
    except Exception:
        return []


_grid_cache = {}


def grid_at(sha, name):
    key = (sha, name)
    if key not in _grid_cache:
        try:
            if sha == "WORKTREE":
                txt = (DATA / "ocean" / name).read_text(encoding="utf-8")
            else:
                txt = subprocess.run(["git", "show", f"{sha}:data/ocean/{name}"], cwd=DIR, capture_output=True, text=True, timeout=60).stdout
            _grid_cache[key] = json.loads(txt)
        except Exception:
            _grid_cache[key] = None
    return _grid_cache[key]


def sample(grid, key, la, lo):
    if not grid:
        return None
    lats, lons, g = grid["lats"], grid["lons"], grid[key]
    ri = min(range(len(lats)), key=lambda i: abs(lats[i] - la))
    ci = min(range(len(lons)), key=lambda i: abs(lons[i] - lo))
    return g[ri][ci]


def hycom_for(t, la, lo, snaps, prior=None):
    """SST/D26/current under (la,lo) from the HYCOM snapshot whose model time is nearest t.
    On a shallow clone (GitHub Actions) there is no history: keep the values a previous full-history
    run already wrote for this fix (prior), and sample the current grid only for fixes newer than it."""
    if prior and prior.get("hycom_time"):
        try:
            pt = datetime.datetime.strptime(prior["hycom_time"], "%Y-%m-%d %HZ").replace(tzinfo=datetime.timezone.utc)
            if abs((pt - t).total_seconds()) <= 12 * 3600 and (not snaps or len(snaps) <= 1):
                return {k: (float(prior[k]) if prior.get(k) not in (None, "") else None) if k != "hycom_time" else prior[k]
                        for k in ("hycom_time", "hycom_sst_c", "hycom_d26_m", "hycom_current_ms")}
        except Exception:
            pass
    best = None
    for ctime, sha in snaps:
        g = grid_at(sha, "hycom_d26.json")
        if not g:
            continue
        mt = datetime.datetime.strptime(g["time_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
        dt = abs((mt - t).total_seconds())
        if best is None or dt < best[0]:
            best = (dt, sha, mt)
        if mt < t - datetime.timedelta(hours=12):
            break
    if best is None:
        sha = "WORKTREE"; g = grid_at(sha, "hycom_d26.json")
        if not g:
            return {}
        mt = datetime.datetime.strptime(g["time_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    else:
        _, sha, mt = best
    sst = grid_at(sha, "hycom_sst.json"); d26 = grid_at(sha, "hycom_d26.json"); cur = grid_at(sha, "hycom_currents.json")
    u, v = sample(cur, "u", la, lo), sample(cur, "v", la, lo)
    return {"hycom_time": mt.strftime("%Y-%m-%d %HZ"), "hycom_sst_c": sample(sst, "sst", la, lo), "hycom_d26_m": sample(d26, "d26", la, lo),
            "hycom_current_ms": round(math.hypot(u, v), 2) if u is not None and v is not None else None}


def nearest_point(features, la, lo, want_profile=False, kind=None):
    best = None
    for f in features:
        p = f["properties"]
        if f["geometry"]["type"] != "Point" or (want_profile and "profile" not in p) or (kind and p.get("kind") != kind):
            continue
        c = f["geometry"]["coordinates"]
        d = math.hypot((c[1] - la) * 111, (c[0] - lo) * 111 * math.cos(math.radians(la)))
        if best is None or d < best[0]:
            best = (d, p)
    return best


def parse_vortex(path):
    t = path.read_text(errors="replace")
    def item(letter):
        m = re.search(rf"^{letter}\.\s*(.+)$", t, re.M)
        return m.group(1).strip() if m else ""
    a = item("A"); b = item("B"); d = item("D"); n = item("N"); o = item("O"); u = item("U")
    mt = re.search(r"(\d\d)/(\d\d):(\d\d):(\d\d)Z", a)
    pos = re.search(r"([\d.]+) deg N ([\d.]+) deg W", b)
    stamp = re.search(r"\.(\d{12})\.", path.name)
    year, month = (stamp.group(1)[:4], stamp.group(1)[4:6]) if stamp else ("", "")
    fix_time = f"{year}-{month}-{mt.group(1)} {mt.group(2)}:{mt.group(3)}Z" if mt else a
    return {"fix_time_utc": fix_time, "lat": float(pos.group(1)) if pos else None, "lon": -float(pos.group(2)) if pos else None,
            "min_slp_mb": int(re.search(r"(\d+) mb", d).group(1)) if re.search(r"(\d+) mb", d) else None,
            "eye": item("F") + (" " + item("G") if item("G") not in ("", "NA") else ""),
            "max_fl_wind_kt": int(re.search(r"(\d+) kt", n).group(1)) if re.search(r"(\d+) kt", n) else None,
            "max_fl_wind_where": o, "mission": u.split("OB")[0].strip(), "file": path.name}


def discussion_intensity_excerpts(adv_dir):
    out = []
    for p in sorted(adv_dir.glob("discussion_*.txt")):
        t = p.read_text(errors="replace")
        n = p.stem.split("_")[-1]
        hdr = re.search(r"(\d{3,4} [AP]M [A-Z]{3} \w{3} \w{3} \d+ \d{4})", t)
        paras = [x.strip() for x in re.split(r"\n\s*\n", t)]
        keep = [x for x in paras if re.search(r"shear|intensif|sea.surface|SST|ocean heat|inner.core|RI\b|rapid", x, re.I) and "Key Messages" not in x and len(x) > 120]
        out.append((n, hdr.group(1) if hdr else "", keep[:3]))
    return out


# ── main ─────────────────────────────────────────────────────────────────────────
def main(sid):
    root = DATA / "storms" / sid.upper()
    bdeck = next(iter((root / "atcf").glob("b*.dat")), None)
    if not bdeck:
        print("no best track archived yet"); return
    fixes = parse_bdeck(bdeck)
    name = sid
    try:
        name = json.loads(sorted((root / "currentstorms").glob("*.json"))[-1].read_text())["name"]
    except Exception:
        pass
    coef = json.loads(COEF.read_text()) if COEF.exists() else None
    ships = {}
    for p in sorted((root / "ships").glob("*_ships.txt")):
        s = parse_ships(p)
        if s:
            ships[s["ships_time"]] = s
    snaps = hycom_snapshots()
    argo = json.loads((DATA / "argo" / "argo_gulf.geojson").read_text()) if (DATA / "argo" / "argo_gulf.geojson").exists() else {"features": []}
    gliders = json.loads((DATA / "gliders" / "gliders_gulf.geojson").read_text()) if (DATA / "gliders" / "gliders_gulf.geojson").exists() else {"features": []}

    prior_rows = {}
    if (root / "ri_timeline.csv").exists():
        with open(root / "ri_timeline.csv", newline="", encoding="utf-8") as fh:
            prior_rows = {r["time_utc"]: r for r in csv.DictReader(fh)}

    # 24-h change, RI flags, onset
    by_t = {f["time"]: f for f in fixes}
    rows = []
    for f in fixes:
        later = by_t.get(f["time"] + datetime.timedelta(hours=RI_H))
        earlier = by_t.get(f["time"] - datetime.timedelta(hours=RI_H))
        f["dv_next24"] = (later["vmax"] - f["vmax"]) if later else None
        f["dv_prev24"] = (f["vmax"] - earlier["vmax"]) if earlier else None
        f["ri_window_start"] = f["dv_next24"] is not None and f["dv_next24"] >= RI_KT
        f["ri_met_here"] = f["dv_prev24"] is not None and f["dv_prev24"] >= RI_KT
    onset = next((f for f in fixes if f["ri_window_start"]), None)
    met = next((f for f in fixes if f["ri_met_here"]), None)
    hurricane = next((f for f in fixes if f["vmax"] >= 64), None)

    for f in fixes:
        s = ships.get(f["time"])
        r = {"time_utc": f["time"].strftime("%Y-%m-%d %HZ"), "lat": f["lat"], "lon": f["lon"], "vmax_kt": f["vmax"], "mslp_mb": f["mslp"], "type": f["type"],
             "dv_prev24_kt": f["dv_prev24"], "dv_next24_kt": f["dv_next24"], "ri_window_start": f["ri_window_start"], "ri_met_here": f["ri_met_here"]}
        if s:
            r.update({k: v for k, v in s.items() if k not in ("ships_time", "vmax")})
            r["our_rii_30kt24h_pct"] = our_rii(coef, s)
            r["our_rii_25kt24h_pct"] = our_rii(coef, s, "25")
        r.update(hycom_for(f["time"], f["lat"], f["lon"], snaps, prior_rows.get(r["time_utc"])))
        na = nearest_point(argo["features"], f["lat"], f["lon"], want_profile=True)
        ng = nearest_point(gliders["features"], f["lat"], f["lon"], kind="now")
        r.update({"argo_id": na[1]["platform"] if na else "", "argo_km": round(na[0]) if na else "", "argo_date": na[1]["time"][:10] if na else "",
                  "argo_d26_m": na[1].get("d26") if na else "", "argo_surf_c": (na[1].get("surface") or {}).get("temperature") if na else "",
                  "glider_id": ng[1]["id"] if ng else "", "glider_km": round(ng[0]) if ng else ""})
        rows.append(r)
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(root / "ri_timeline.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); [w.writerow(r) for r in rows]

    vort = [parse_vortex(p) for p in sorted((root / "recon").glob("REPNT2-*.txt")) + sorted((root / "recon").glob("URNT12-*.txt"))]
    vort = [v for v in vort if v["lat"] is not None]
    vort.sort(key=lambda v: v["fix_time_utc"])
    if vort:
        with open(root / "vortex_fixes.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(vort[0].keys())); w.writeheader(); [w.writerow(v) for v in vort]

    # ── markdown record ──
    fmt = lambda v, u="", d=1: "–" if v in (None, "") else (f"{v:.{d}f}{u}" if isinstance(v, float) else f"{v}{u}")
    L = [f"# {name} ({sid.upper()}) — rapid-intensification record", "",
         f"Generated {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%MZ} from the archive in this folder by ri_event_record.py. "
         f"Definition used: NHC rapid intensification = maximum sustained wind increase of at least {RI_KT} kt in {RI_H} h (best track, 6-hourly). "
         "All numbers are read from archived sources; nothing is estimated.", ""]
    L += ["## 1. The event by the definition", ""]
    if onset:
        L.append(f"- **RI window opens:** {onset['time']:%Y-%m-%d %HZ} at {onset['lat']:.1f}N {abs(onset['lon']):.1f}W, {onset['vmax']} kt {onset['mslp'] or '–'} mb ({onset['type']}); +{onset['dv_next24']} kt over the following 24 h.")
    else:
        L.append(f"- RI window: no 24-h gain of {RI_KT} kt or more in the best track yet.")
    if met:
        L.append(f"- **Definition met:** {met['time']:%Y-%m-%d %HZ} at {met['lat']:.1f}N {abs(met['lon']):.1f}W, {met['vmax']} kt {met['mslp'] or '–'} mb ({met['type']}); +{met['dv_prev24']} kt over the previous 24 h.")
    if hurricane:
        L.append(f"- **First hurricane fix (≥64 kt):** {hurricane['time']:%Y-%m-%d %HZ} at {hurricane['lat']:.1f}N {abs(hurricane['lon']):.1f}W, {hurricane['vmax']} kt {hurricane['mslp'] or '–'} mb.")
    # the advisory that first called it a hurricane, and the aircraft fix NHC had in hand at that moment
    upgrade = None
    for p in sorted((root / "currentstorms").glob("*.json")):
        try:
            cs = json.loads(p.read_text())
            if str(cs.get("classification", "")).upper() == "HU":
                upgrade = cs; break
        except Exception:
            pass
    if upgrade:
        L.append(f"- **NHC upgrade to hurricane:** advisory {upgrade.get('publicAdvisory', {}).get('advNum', '?')} at {upgrade.get('lastUpdate', '?')[:16].replace('T', ' ')}Z, "
                 f"{upgrade.get('intensity')} kt {upgrade.get('pressure')} mb at {float(upgrade.get('latitudeNumeric')):.1f}N {abs(float(upgrade.get('longitudeNumeric'))):.1f}W.")
    if vort:
        L.append(f"- **Aircraft fixes archived:** {len(vort)} (first {vort[0]['fix_time_utc']}, latest {vort[-1]['fix_time_utc']}).")
        if upgrade:
            ut = upgrade.get("lastUpdate", "")[:16].replace("T", " ") + "Z"
            basis = [v for v in vort if v["fix_time_utc"] <= ut]
            if basis:
                b = basis[-1]
                L.append(f"- **Aircraft fix in hand at the upgrade:** {b['fix_time_utc']} at {b['lat']:.2f}N {abs(b['lon']):.2f}W, {b['min_slp_mb']} mb, "
                         f"max 700 mb flight-level wind {b['max_fl_wind_kt']} kt at {b['max_fl_wind_where']} ({b['mission']}).")
    L += ["", "## 2. Measurements at the key moments", "",
          "| Moment | Time | Vmax | MSLP | SST (SHIPS) | OHC kJ/cm² | HYCOM SST | HYCOM D26 | Shear kt / dir | 700–500 RH | POT kt | D200 | NHC SHIPS-RII 30/24 | DTOPS 30/24 | Our RII 30/24 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    def moment(label, f):
        if not f:
            return
        r = next(x for x in rows if x["time_utc"] == f["time"].strftime("%Y-%m-%d %HZ"))
        L.append(f"| {label} | {r['time_utc']} | {r['vmax_kt']} kt | {fmt(r['mslp_mb'],' mb',0)} | {fmt(r.get('sst_c'),' °C')} | {fmt(r.get('ohc_kjcm2'),'',0)} | {fmt(r.get('hycom_sst_c'),' °C',2)} | {fmt(r.get('hycom_d26_m'),' m',0)} | "
                 f"{fmt(r.get('shear_kt'),'',0)} / {fmt(r.get('shear_dir'),'°',0)} | {fmt(r.get('rh_700_500'),'%',0)} | {fmt(r.get('pot_kt'),'',0)} | {fmt(r.get('d200'),'',0)} | {fmt(r.get('nhc_ships-rii_30kt24h_pct'),'%')} | {fmt(r.get('nhc_dtops_30kt24h_pct'),'%')} | {fmt(r.get('our_rii_30kt24h_pct'),'%')} |")
    moment("RI window opens", onset); moment("Definition met", met); moment("First hurricane fix", hurricane)
    L += ["", "SST, OHC, shear, RH, POT (MPI minus Vmax) and D200 (200 mb divergence, 1e-7 s⁻¹) are the 0-h values in NHC's operational SHIPS file for that cycle. "
          "HYCOM values are this site's 1/12° model snapshot nearest the fix time, sampled at the fix. Our RII is the gulf-ri-model rebuild of SHIPS-RII (logistic, six predictors) applied to the same 0-h values.", ""]
    L += ["## 3. Factor table across the event (every best-track fix)", "",
          "| Time | Vmax | Δ24 prev | SST | OHC | HYCOM D26 | Shear | RH | POT | D200 | Speed kt | IR cold % | NHC RII 30/24 | DTOPS | Our RII |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['time_utc']} | {r['vmax_kt']} | {fmt(r['dv_prev24_kt'],'',0)} | {fmt(r.get('sst_c'),'')} | {fmt(r.get('ohc_kjcm2'),'',0)} | {fmt(r.get('hycom_d26_m'),'',0)} | {fmt(r.get('shear_kt'),'',0)} | {fmt(r.get('rh_700_500'),'',0)} | "
                 f"{fmt(r.get('pot_kt'),'',0)} | {fmt(r.get('d200'),'',0)} | {fmt(r.get('storm_speed_kt'),'',0)} | {fmt(r.get('ir_pct_cold'),'',0)} | {fmt(r.get('nhc_ships-rii_30kt24h_pct'),'%')} | {fmt(r.get('nhc_dtops_30kt24h_pct'),'%')} | {fmt(r.get('our_rii_30kt24h_pct'),'%')} |")
    if vort:
        L += ["", "## 4. Aircraft center fixes", "", "| Fix time | Position | Min SLP | Eye | Max 700 mb wind | Mission |", "|---|---|---|---|---|---|"]
        for v in vort:
            L.append(f"| {v['fix_time_utc']} | {v['lat']:.2f}N {abs(v['lon']):.2f}W | {fmt(v['min_slp_mb'],' mb',0)} | {v['eye'] or '–'} | {fmt(v['max_fl_wind_kt'],' kt',0)} {v['max_fl_wind_where']} | {v['mission']} |")
    exc = discussion_intensity_excerpts(root / "advisories")
    if exc:
        L += ["", "## 5. NHC's own intensity reasoning, by discussion (verbatim excerpts)", ""]
        for n, hdr, paras in exc:
            L.append(f"**Discussion {n}** ({hdr})")
            for x in paras:
                L.append("> " + " ".join(x.split()))
            L.append("")
    L += ["## 6. Sources in this folder", "", "- `atcf/` working best track (b-deck) and model guidance (a-deck) from ftp.nhc.noaa.gov",
          "- `ships/` operational SHIPS diagnostic files (predictors, SHIPS-RII, DTOPS)", "- `advisories/` every public/forecast advisory, discussion and wind-probability product",
          "- `gis/` cone, track, points and watches per advisory", "- `recon/` HDOB high-density observations and vortex data messages", "- `environment.csv` HYCOM/Argo/glider readings under the center at each archive run", ""]
    (root / "RI_EVENT_RECORD.md").write_text("\n".join(L), encoding="utf-8")
    print(f"record: {len(rows)} fixes, {len(ships)} SHIPS cycles, {len(vort)} aircraft fixes; onset {onset['time'] if onset else None}; met {met['time'] if met else None}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "AL092026")
