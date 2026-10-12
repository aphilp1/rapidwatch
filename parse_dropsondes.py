"""
parse_dropsondes.py - one table from the archived Hurricane Hunter dropsonde messages.

Reads data/storms/<ID>/recon/REPNT3-*.txt (WMO FM-37 TEMP DROP, UZNT13 headers as NHC/WPC
relayed them) and writes data/storms/<ID>/sensors/dropsondes.csv, one row per sonde:

  release_utc, lat, lon            from the 62626 remarks: REL <lat><lon> <HHMMSS>
  splash_utc, splash_lat, splash_lon                       SPG <lat><lon> <HHMMSS>
  surface_p_mb, surface_t_c, surface_wdir_deg, surface_wspd_kt   XXAA surface group 99PPP TTTDD dddff
  wl150_wdir_deg, wl150_wspd_kt    the 150 m layer mean wind (WL150 ddfff)
  mbl_wdir_deg, mbl_wspd_kt        mean boundary-layer wind (MBL WND ddfff)
  dlm_wdir_deg, dlm_wspd_kt        deep-layer mean wind (DLM WND ddfff)
  aircraft, mission, ob, center    from the 61616 line; "center" = 1 when the remarks say CENTER
  source_files                     every archived file carrying this sonde (KNHC and KWBC relays)

Only what the message states is written; a group that is missing or slashed stays blank.
Duplicates (the same sonde relayed by KNHC and KWBC, or re-issued) collapse on
mission + ob + release time.

Run:  python parse_dropsondes.py AL092026
"""
import csv, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def wind(g):
    """ddfff -> (direction deg, speed kt); None if slashed. Speeds >= 100 kt add 500 to dd."""
    if not g or not re.fullmatch(r"\d{5}", g):
        return None, None
    dd, ff = int(g[:3]), int(g[3:])
    if dd >= 500:
        dd -= 500; ff += 100
    return dd, ff


def temp(g):
    """TTTDD -> temperature C (tenths; odd tenths digit = negative)."""
    if not g or not re.fullmatch(r"\d{5}", g):
        return None
    t = int(g[:3]) / 10.0
    return -t if int(g[2]) % 2 else t


def latlon(s):
    m = re.fullmatch(r"(\d{2})(\d{2})([NS])(\d{3})(\d{2})([EW])", s)
    if not m:
        return None, None
    la = int(m.group(1)) + int(m.group(2)) / 100.0
    lo = int(m.group(4)) + int(m.group(5)) / 100.0
    return (la if m.group(3) == "N" else -la), (lo if m.group(6) == "E" else -lo)


def parse_message(body, file_day):
    """body = text from XXAA up to the next XXAA/XXBB. Returns a dict or None."""
    toks = re.sub(r"\s+", " ", body).split(" ")
    try:
        i = toks.index("XXAA")
    except ValueError:
        return None
    r = {}
    # XXAA YYGGI 99LaLaLa QcLoLoLoLo MMMULaULo 99PPP TTTDD dddff ...
    try:
        yygg = toks[i + 1]
        day = int(yygg[:2]); day = day - 50 if day > 50 else day
        r["obs_day"] = day; r["obs_hour"] = int(yygg[2:4])
        if toks[i + 5].startswith("99"):
            ppp = int(toks[i + 5][2:]); r["surface_p_mb"] = ppp + 1000 if ppp < 100 else ppp
            r["surface_t_c"] = temp(toks[i + 6])
            r["surface_wdir_deg"], r["surface_wspd_kt"] = wind(toks[i + 7])
    except (ValueError, IndexError):
        pass
    txt = " ".join(toks)
    m = re.search(r"61616 (\S+) (\S+) (\S+)\s+OB (\d+)", txt)
    if m:
        r["aircraft"], r["mission"], r["storm"], r["ob"] = m.group(1), m.group(2), m.group(3), int(m.group(4))
    r["center"] = 1 if re.search(r"62626 CENTER", txt) else 0
    m = re.search(r"MBL WND (\d{5})", txt)
    if m: r["mbl_wdir_deg"], r["mbl_wspd_kt"] = wind(m.group(1))
    m = re.search(r"DLM WND (\d{5})", txt)
    if m: r["dlm_wdir_deg"], r["dlm_wspd_kt"] = wind(m.group(1))
    m = re.search(r"WL150 (\d{5})", txt)
    if m: r["wl150_wdir_deg"], r["wl150_wspd_kt"] = wind(m.group(1))
    m = re.search(r"REL (\d{4}[NS]\d{5}[EW]) (\d{6})", txt)
    if m:
        r["lat"], r["lon"] = latlon(m.group(1)); r["release_hhmmss"] = m.group(2)
    m = re.search(r"SPG (\d{4}[NS]\d{5}[EW]) (\d{6})", txt)
    if m:
        r["splash_lat"], r["splash_lon"] = latlon(m.group(1)); r["splash_hhmmss"] = m.group(2)
    return r if "release_hhmmss" in r else None


def stamp(file_ts, hhmmss, obs_day):
    """ISO time: the message's own day (YYGG) + the REL/SPG clock, year-month from the file name."""
    y, mo = file_ts[:4], file_ts[4:6]
    return f"{y}-{mo}-{obs_day:02d}T{hhmmss[:2]}:{hhmmss[2:4]}:{hhmmss[4:]}Z"


def main(sid):
    rec = DATA / "storms" / sid / "recon"
    out = DATA / "storms" / sid / "sensors" / "dropsondes.csv"
    sondes = {}
    files = sorted(rec.glob("REPNT3-*.txt"))
    for f in files:
        txt = f.read_text(encoding="utf-8", errors="replace")
        file_ts = re.search(r"\.(\d{12})", f.name).group(1)
        # a file can carry several messages; split on each XXAA part A (part B XXBB repeats the remarks)
        parts = re.split(r"(?=XXAA )", txt)
        for part in parts:
            if not part.startswith("XXAA"):
                continue
            part = part.split("XXBB")[0]
            r = parse_message(part, file_ts)
            if not r:
                continue
            r["release_utc"] = stamp(file_ts, r["release_hhmmss"], r["obs_day"])
            if "splash_hhmmss" in r:
                r["splash_utc"] = stamp(file_ts, r["splash_hhmmss"], r["obs_day"])
            key = (r.get("mission"), r.get("ob"), r["release_utc"])
            if key in sondes:
                sondes[key]["source_files"].add(f.name)
                # prefer a row that carries more fields (a re-issue can add the surface group)
                for k, v in r.items():
                    if v is not None and sondes[key].get(k) in (None, ""):
                        sondes[key][k] = v
            else:
                r["source_files"] = {f.name}
                sondes[key] = r
    fields = ["release_utc", "lat", "lon", "splash_utc", "splash_lat", "splash_lon", "surface_p_mb", "surface_t_c",
              "surface_wdir_deg", "surface_wspd_kt", "wl150_wdir_deg", "wl150_wspd_kt", "mbl_wdir_deg", "mbl_wspd_kt",
              "dlm_wdir_deg", "dlm_wspd_kt", "aircraft", "mission", "ob", "center", "source_files"]
    rows = sorted(sondes.values(), key=lambda r: r["release_utc"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            r["source_files"] = ";".join(sorted(r["source_files"]))
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})
    print(f"{len(files)} files -> {len(rows)} sondes -> {out}")
    sp = [r for r in rows if r.get("surface_p_mb")]
    if sp:
        lo = min(sp, key=lambda r: r["surface_p_mb"]); print("lowest surface pressure:", lo["surface_p_mb"], "mb at", lo["release_utc"], lo.get("lat"), lo.get("lon"), "center" if lo["center"] else "")
    wl = [r for r in rows if r.get("wl150_wspd_kt") is not None]
    if wl:
        hi = max(wl, key=lambda r: r["wl150_wspd_kt"]); print("highest WL150 wind:", hi["wl150_wdir_deg"], "deg", hi["wl150_wspd_kt"], "kt at", hi["release_utc"], hi.get("lat"), hi.get("lon"))
    return rows


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "AL092026")
