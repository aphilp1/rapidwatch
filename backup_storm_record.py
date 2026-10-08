"""
backup_storm_record.py — daily off-site copy of the storm record and RI tooling
================================================================================
Zips data/storms (every archived storm), data/ri_model, reviews/, the tracking and
record scripts, the gulf-ri-model results/docs/src, and the RapidWatch memory notes,
then writes the zip to Documents, Desktop and OneDrive (OneDrive = off-machine copy).
Also refreshes a git bundle of the RapidWatch repo (full history) in the same places
once a day. Run by the Windows scheduled task "RapidWatch storm record backup".

Run:  python backup_storm_record.py
"""
import datetime, pathlib, shutil, subprocess, zipfile

HOME = pathlib.Path.home()
DOCS = HOME / "Documents"
RW = DOCS / "RapidWatch"
GRM = DOCS / "gulf-ri-model"
MEM = HOME / ".claude" / "projects" / "C--Users-aphil" / "memory"
TARGETS = [DOCS, HOME / "Desktop", HOME / "OneDrive"]
STAMP = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
LOG = RW / "backup_runs.log"


def log(msg):
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    zpath = DOCS / f"RapidWatch-StormRecord-{STAMP}.zip"
    n = 0
    seen = set()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        def add(p, arc):
            nonlocal n
            if arc in seen or not p.is_file():
                return
            z.write(p, arc); seen.add(arc); n += 1
        for root in (RW / "data" / "storms", RW / "data" / "ri_model", RW / "reviews", GRM / "results", GRM / "docs", GRM / "src"):
            if root.exists():
                for p in root.rglob("*"):
                    add(p, str(p.relative_to(DOCS)))
        for f in ("track_storm.py", "ri_event_record.py", "build_argo.py", "build_gliders.py", "build_live_data.py",
                  "build_ocean_state.py", "rapidwatch-sensors.html", "trigger_runs.log", "backup_storm_record.py"):
            add(RW / f, f"RapidWatch/{f}")
        for p in MEM.glob("*.md"):
            if "rapidwatch" in p.name.lower() or "gulf_ri" in p.name.lower() or p.name == "MEMORY.md":
                add(p, f"memory/{p.name}")
    with zipfile.ZipFile(zpath) as z:
        bad = z.testzip()
    if bad:
        log(f"ZIP TEST FAILED on {bad}"); return
    log(f"zip {zpath.name}: {n} files, {zpath.stat().st_size/1e6:.1f} MB")
    for t in TARGETS[1:]:
        if t.exists():
            shutil.copy2(zpath, t / zpath.name)
    # full-history bundle of the RapidWatch repo (~390 MB): refresh weekly, verified before copying.
    # Bundles are never deleted automatically.
    newest = sorted(DOCS.glob("RapidWatch-backup-*.bundle"), key=lambda p: p.stat().st_mtime)
    age_days = (datetime.datetime.now().timestamp() - newest[-1].stat().st_mtime) / 86400 if newest else 999
    if age_days >= 7:
        bpath = DOCS / f"RapidWatch-backup-{STAMP}.bundle"
        subprocess.run(["git", "bundle", "create", str(bpath), "--all"], cwd=RW, capture_output=True, text=True)
        v = subprocess.run(["git", "bundle", "verify", str(bpath)], cwd=RW, capture_output=True, text=True)
        if "okay" in (v.stdout + v.stderr):
            for t in TARGETS[1:]:
                if t.exists():
                    shutil.copy2(bpath, t / bpath.name)
            log(f"bundle {bpath.name}: {bpath.stat().st_size/1e6:.0f} MB, verified, copied to Desktop + OneDrive")
        else:
            log(f"bundle verify FAILED: {(v.stdout + v.stderr).strip()[:200]}")
    else:
        log(f"bundle skipped: newest is {age_days:.1f} days old ({newest[-1].name})")
    # keep the 14 newest daily zips in every target (only files this script makes; bundles are kept)
    for t in TARGETS:
        olds = sorted(t.glob("RapidWatch-StormRecord-*.zip"), key=lambda p: p.stat().st_mtime)[:-14]
        for o in olds:
            try:
                o.unlink(); log(f"pruned {o}")
            except Exception:
                pass


if __name__ == "__main__":
    main()
