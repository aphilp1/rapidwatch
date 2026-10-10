"""
backfill_sensors.py — one-time close-out of a storm's NDBC sensor record
=========================================================================
The hourly sweep (sweep_sensors.py) only fetches stations inside the moving corridor, so a
station that drops out of the corridor stops being fetched and its file ends early. This
script re-fetches the NDBC 45-day real-time files for EVERY station that already has a file
in data/storms/<ID>/sensors/ndbc/ (plus one retry of the stations NDBC 404'd), union-merges
all rows since storm start, and appends one entry to SENSOR_LOG.md. Nothing is deleted.

Run:  python backfill_sensors.py AL092026
"""
import csv, json, pathlib, sys, urllib.error
import sweep_sensors as sw

def main(sid):
    sid = sid.upper()
    root = pathlib.Path("data/storms") / sid
    out = root / "sensors"
    run_ts = sw.utcnow().strftime("%Y%m%dT%H%M")
    past = sw.bdeck_points(root, sid)
    d = past[0][2]
    since = f"{d[:4]}-{d[4:6]}-{d[6:8]}T00:00Z"
    tags = sorted({p.name[:-4] for p in (out / "ndbc").glob("*.csv")})          # e.g. 42001.txt
    missing_p = out / "_ndbc_missing.json"
    missing = sw.load_json(missing_p) or {}
    retry = sorted(k for k in missing if k.endswith(".txt"))
    print(f"{sid}: backfilling {len(tags)} files since {since}; retrying {len(retry)} 404'd met files")
    report, total, extended, still_missing = [], 0, 0, []
    for tag in tags + retry:
        try:
            txt = sw.get(f"{sw.NDBC_RT}{tag}", timeout=30).decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404 and tag in retry:
                still_missing.append(tag); missing[tag] = run_ts
            report.append((tag, "HTTP %s" % e.code, 0)); continue
        except Exception as e:
            report.append((tag, f"error {type(e).__name__}", 0)); continue
        fields, rows = sw.parse_ndbc(txt)
        if not fields:
            report.append((tag, "unparseable", 0)); continue
        p = out / "ndbc" / f"{tag}.csv"
        n = sw.merge_csv(p, fields, rows, since=since)
        with open(p, newline="", encoding="utf-8") as f:
            last = max((r["time_utc"] for r in csv.DictReader(f)), default="")
        total += n; extended += (n > 0)
        report.append((tag, last, n))
        if tag in retry:
            missing.pop(tag, None)
    missing_p.write_text(json.dumps(missing, sort_keys=True), encoding="utf-8")
    for tag, last, n in report:
        print(f"  {tag:14s} last {last}  +{n}")
    print(f"TOTAL new rows {total} across {extended} files; still 404: {len(still_missing)}")
    with open(out / "SENSOR_LOG.md", "a", encoding="utf-8") as f:
        f.write(f"\n## {run_ts} UTC · CLOSE-OUT BACKFILL (backfill_sensors.py)\n"
                f"- Re-fetched the NDBC 45-day files for all {len(tags)} station files on disk regardless of corridor, "
                f"merged every row since {since}: {total} new rows in {extended} files. "
                f"Retried {len(retry)} stations NDBC had 404'd: {len(retry)-len(still_missing)} now have a file, {len(still_missing)} still absent.\n")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "AL092026")
