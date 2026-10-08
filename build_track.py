"""
build_track.py — the storm's ENTIRE path from the moment NHC first tracked it
================================================================================
Written 2026-10-08 (Hurricane Isaias). Called by track_storm.py each run; also by hand:
    python build_track.py AL092026

Sources already in this archive (nothing is fetched here):
  atcf/b<id>.dat        NHC best track (ATCF b-deck) - starts when NHC first carried the system
                        (for Isaias: 2026-10-04 18Z as a disturbance "DB"), one fix every 6 h
  vortex_fixes.csv      aircraft center fixes (from ri_event_record.py)
  gis/adv<nn>_points    the latest forecast points (NHC MapServer snapshot)

Outputs (regenerated every run):
  track_full.geojson    FeatureCollection: best_track_line, best_track_point (one per fix, with
                        time, vmax, mslp, type), aircraft_fix, forecast_line, forecast_point
  TRACK.md              the same as a table, plus distance travelled and mean speed per leg
"""
import csv, json, pathlib, sys
import sweep_sensors as ss

DATA = pathlib.Path(__file__).resolve().parent / "data"
TYPE_NAME = {"DB": "disturbance", "LO": "low", "WV": "tropical wave", "TD": "tropical depression", "TS": "tropical storm",
             "HU": "hurricane", "EX": "extratropical", "SD": "subtropical depression", "SS": "subtropical storm",
             "PT": "post-tropical", "TY": "typhoon", "ST": "super typhoon"}


def dtg_iso(d):
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}T{d[8:10]}:00Z"


def hours_between(a, b):
    """Whole hours between two ATCF date-time groups (YYYYMMDDHH)."""
    import datetime
    fa = datetime.datetime(int(a[:4]), int(a[4:6]), int(a[6:8]), int(a[8:10]))
    fb = datetime.datetime(int(b[:4]), int(b[4:6]), int(b[6:8]), int(b[8:10]))
    return max(1.0, (fb - fa).total_seconds() / 3600)


def build(sid, root, name=""):
    past = ss.bdeck_points(root, sid)            # (lat, lon, dtg, vmax, mslp)
    types = {}
    bp = root / "atcf" / f"b{sid.lower()}.dat"
    if bp.exists():
        for line in bp.read_text(errors="replace").splitlines():
            f = [x.strip() for x in line.split(",")]
            if len(f) > 10 and f[4] == "BEST" and f[2] not in types:
                types[f[2]] = f[10]
    fc, fc_file = ss.forecast_points(root)
    fixes = []
    vp = root / "vortex_fixes.csv"
    if vp.exists():
        with open(vp, newline="", encoding="utf-8") as f:
            fixes = list(csv.DictReader(f))

    feats = []
    if len(past) > 1:
        feats.append({"type": "Feature", "properties": {"kind": "best_track_line", "storm": sid, "name": name,
                                                        "from": dtg_iso(past[0][2]), "to": dtg_iso(past[-1][2])},
                      "geometry": {"type": "LineString", "coordinates": [[p[1], p[0]] for p in past]}})
    rows = []
    for i, (la, lo, dtg, vmax, mslp) in enumerate(past):
        leg_km = ss.km(past[i - 1][0], past[i - 1][1], la, lo) if i else 0.0
        spd_kt = round(leg_km / 1.852 / hours_between(past[i - 1][2], dtg), 1) if i else ""
        t = types.get(dtg, "")
        try:
            pmb = int(mslp) if mslp and int(mslp) > 0 else None
        except ValueError:
            pmb = None
        p = {"kind": "best_track_point", "time_utc": dtg_iso(dtg), "lat": la, "lon": lo, "vmax_kt": int(vmax or 0),
             "mslp_mb": pmb, "type": t, "type_name": TYPE_NAME.get(t, t),
             "leg_km": round(leg_km), "speed_kt": spd_kt, "first": i == 0, "latest": i == len(past) - 1}
        feats.append({"type": "Feature", "properties": p, "geometry": {"type": "Point", "coordinates": [lo, la]}})
        rows.append(p)
    for x in fixes:
        try:
            feats.append({"type": "Feature",
                          "properties": {"kind": "aircraft_fix", "time_utc": x["fix_time_utc"], "min_slp_mb": x["min_slp_mb"],
                                         "max_fl_wind_kt": x["max_fl_wind_kt"], "eye": x["eye"], "mission": x["mission"]},
                          "geometry": {"type": "Point", "coordinates": [float(x["lon"]), float(x["lat"])]}})
        except (KeyError, ValueError):
            pass
    if fc:
        feats.append({"type": "Feature", "properties": {"kind": "forecast_line", "advisory_file": fc_file},
                      "geometry": {"type": "LineString", "coordinates": [[p[1], p[0]] for p in fc]}})
        for la, lo, tau, vt, mw in fc:
            feats.append({"type": "Feature", "properties": {"kind": "forecast_point", "tau_h": tau, "valid": vt, "maxwind_kt": mw},
                          "geometry": {"type": "Point", "coordinates": [lo, la]}})
    gj = {"type": "FeatureCollection", "name": f"{sid} full track", "features": feats}
    (root / "track_full.geojson").write_text(json.dumps(gj), encoding="utf-8")

    total = sum(r["leg_km"] for r in rows)
    md = [f"# {name or sid} ({sid}) - full track since NHC first tracked it", "",
          f"Source: NHC best track (ATCF b-deck atcf/b{sid.lower()}.dat) as archived here; regenerated every run by build_track.py. "
          f"Positions are NHC's 6-hourly best-track fixes, not interpolated. Aircraft fixes are listed in RI_EVENT_RECORD.md.", ""]
    if rows:
        md += [f"- **First tracked:** {rows[0]['time_utc']} at {rows[0]['lat']:.1f}N {abs(rows[0]['lon']):.1f}W as a {rows[0]['type_name']} ({rows[0]['vmax_kt']} kt).",
               f"- **Latest fix:** {rows[-1]['time_utc']} at {rows[-1]['lat']:.1f}N {abs(rows[-1]['lon']):.1f}W, {rows[-1]['type_name']} {rows[-1]['vmax_kt']} kt"
               + (f" {rows[-1]['mslp_mb']} mb." if rows[-1]['mslp_mb'] else "."),
               f"- **Fixes:** {len(rows)} spanning {hours_between(past[0][2], past[-1][2]):.0f} h; distance along the track {total:.0f} km ({total / 1.852:.0f} nmi).", "",
               "| Time (UTC) | Lat | Lon | Type | Vmax kt | MSLP mb | Leg km | Speed kt |", "|---|---|---|---|---|---|---|---|"]
        for r in rows:
            md.append(f"| {r['time_utc']} | {r['lat']:.1f}N | {abs(r['lon']):.1f}W | {r['type']} | {r['vmax_kt']} | {r['mslp_mb'] or '-'} | {r['leg_km'] or '-'} | {r['speed_kt'] or '-'} |")
    if fc:
        md += ["", f"Latest NHC forecast points ({fc_file}):", "", "| Lead | Valid | Lat | Lon | Max wind kt |", "|---|---|---|---|---|"]
        md += [f"| +{tau} h | {vt} | {la:.1f}N | {abs(lo):.1f}W | {mw} |" for la, lo, tau, vt, mw in fc]
    (root / "TRACK.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return f"track: {len(rows)} fixes from {rows[0]['time_utc'] if rows else '-'}, {len(fixes)} aircraft fixes, {len(fc)} forecast pts"


def main(only=None):
    for root in sorted((DATA / "storms").glob("AL*")):
        if only and root.name.upper() != only.upper():
            continue
        print(root.name, build(root.name, root))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
