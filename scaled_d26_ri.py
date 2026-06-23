"""
scaled_d26_ri.py — does D26 separate RI from non-RI across many Gulf hurricanes?
═══════════════════════════════════════════════════════════════════════════════
For every Gulf hurricane in the ocean-reanalysis era (1994-2025) we download one
ocean-temperature field (Copernicus GLORYS reanalysis for <=2021, analysis for
>=2022) dated at the storm's strongest 24-h intensification window, compute D26
at every in-Gulf best-track fix, and label each fix RI-onset (next ~24h >=+30kt)
or not. Then we test whether D26 separates the two — and whether it adds skill
BEYOND location and season.

  python scaled_d26_ri.py --dryrun       # just enumerate
  python scaled_d26_ri.py                # download + sample + stats (resumable)
  python scaled_d26_ri.py --statsonly    # stats on the existing CSV
"""
import sys, argparse, csv, pathlib
import numpy as np
import netCDF4 as nc
import build_gulf_hurricanes as g
from build_ohc_hycom import d26_profile

DIR = pathlib.Path(__file__).parent
OHC = DIR / 'data' / 'ohc'
RAW = OHC / 'raw'; RAW.mkdir(parents=True, exist_ok=True)
CSV = OHC / 'ri_d26_samples.csv'
YEAR_MIN = 1994
LAT_MIN, LAT_MAX = 15.0, 32.0
LON_MIN, LON_MAX = -100.0, -74.0

MY   = 'cmems_mod_glo_phy_my_0.083deg_P1D-m'              # reanalysis <=2021
ANFC = 'cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m'     # analysis  >=2022

def dataset_chain(year):
    return [MY, ANFC] if year <= 2021 else [ANFC, MY]

def near_24h(track, i):
    ti = g.fix_dt(track[i]); best, bestd = None, 99
    for k in range(i + 1, len(track)):
        dh = (g.fix_dt(track[k]) - ti).total_seconds() / 3600
        if dh > 27: break
        if dh >= 21 and abs(dh - 24) < bestd and track[k]['wind'] is not None:
            best, bestd = k, abs(dh - 24)
    return best

def gulf_hurricanes(storms):
    return [s for s in storms if s['year'] >= YEAR_MIN
            and any(p['status'] == 'HU' for p in s['track'])
            and any(g.in_gulf(p['lon'], p['lat']) for p in s['track'])]

def labelled_fixes(s):
    tr = s['track']; out = []
    for i, p in enumerate(tr):
        if p['wind'] is None or not g.in_gulf(p['lon'], p['lat']):
            continue
        j = near_24h(tr, i)
        if j is None: continue
        out.append((p, int(tr[j]['wind'] - p['wind'] >= 30), tr[j]['wind'] - p['wind']))
    return out

def field_date(s):
    """date (YYYY-MM-DD) of the storm's strongest 24-h intensification window start."""
    tr = s['track']; best = (None, -999)
    for i, p in enumerate(tr):
        if p['wind'] is None: continue
        j = near_24h(tr, i)
        if j is None: continue
        dW = tr[j]['wind'] - p['wind']
        if dW > best[1]: best = (p, dW)
    p = best[0] or next(q for q in tr if g.in_gulf(q['lon'], q['lat']))
    return f"{p['date'][:4]}-{p['date'][4:6]}-{p['date'][6:8]}"

def pull_field(s):
    import copernicusmarine as cm
    day = field_date(s)
    for ds_id in dataset_chain(s['year']):
        out = RAW / f"{s['id']}_thetao.nc"
        try:
            cm.subset(dataset_id=ds_id, variables=['thetao'],
                minimum_longitude=LON_MIN, maximum_longitude=LON_MAX,
                minimum_latitude=LAT_MIN, maximum_latitude=LAT_MAX,
                minimum_depth=0, maximum_depth=300,
                start_datetime=f"{day}T00:00:00", end_datetime=f"{day}T00:00:00",
                output_filename=out.name, output_directory=str(RAW),
                overwrite=True, disable_progress_bar=True)
            if out.exists():
                return out, ds_id, day
        except Exception:
            continue
    return None, None, day

def sample_d26(ds, lat, lon):
    lats = ds['lats']; lons = ds['lons']; depth = ds['depth']; th = ds['th']
    i = int(np.argmin(np.abs(lats - lat))); j = int(np.argmin(np.abs(lons - lon)))
    for rad in range(0, 4):
        i0, i1 = max(0, i-rad), min(len(lats), i+rad+1)
        j0, j1 = max(0, j-rad), min(len(lons), j+rad+1)
        best = np.nan
        for ii in range(i0, i1):
            for jj in range(j0, j1):
                d = d26_profile(th[:, ii, jj], depth)
                if not np.isnan(d): return d
    return np.nan

def open_field(path):
    d = nc.Dataset(path)
    th = np.asarray(d.variables['thetao'][0])
    th = np.where(np.isfinite(th), th, np.nan)
    th = np.where((th < -5) | (th > 45), np.nan, th)
    out = {'lats': np.asarray(d.variables['latitude'][:], float),
           'lons': np.asarray(d.variables['longitude'][:], float),
           'depth': np.asarray(d.variables['depth'][:], float), 'th': th}
    d.close(); return out

# ── download + sample ─────────────────────────────────────────────────────────
def build(storms):
    gulf = gulf_hurricanes(storms)
    done = set()
    if CSV.exists():
        done = {r['id'] for r in csv.DictReader(CSV.open())}
    write_header = not CSV.exists()
    f = CSV.open('a', newline='')
    w = csv.writer(f)
    if write_header:
        w.writerow(['id','name','year','month','lat','lon','wind','dW24','is_ri','d26','dataset'])
    for n, s in enumerate(gulf, 1):
        if s['id'] in done:
            continue
        path, ds_id, day = pull_field(s)
        if path is None:
            print(f"  [{n}/{len(gulf)}] {s['id']} {s['name']}: FIELD FAILED ({day})"); continue
        fld = open_field(path)
        rows = 0
        for p, is_ri, dW in labelled_fixes(s):
            d26 = sample_d26(fld, p['lat'], p['lon'])
            w.writerow([s['id'], s['name'], s['year'], int(p['date'][4:6]),
                        round(p['lat'],2), round(p['lon'],2), p['wind'], dW, is_ri,
                        '' if np.isnan(d26) else round(d26,1), ds_id.split('_')[3]])
            rows += 1
        f.flush()
        print(f"  [{n}/{len(gulf)}] {s['id']} {s['name']:12s} {day} {ds_id.split('_')[3]:4s} "
              f"{rows} fixes")
    f.close()

# ── statistics ────────────────────────────────────────────────────────────────
def stats():
    import numpy as np
    from scipy.stats import mannwhitneyu
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    from sklearn.metrics import roc_auc_score

    rows = [r for r in csv.DictReader(CSV.open()) if r['d26'] != '']
    y   = np.array([int(r['is_ri']) for r in rows])
    d26 = np.array([float(r['d26']) for r in rows])
    lat = np.array([float(r['lat']) for r in rows])
    lon = np.array([float(r['lon']) for r in rows])
    mon = np.array([int(r['month']) for r in rows])
    wind= np.array([float(r['wind']) for r in rows])
    n = len(y); npos = int(y.sum())
    print(f"\n================ SCALED D26 vs RI — {n} fixes, {npos} RI-onset "
          f"({100*npos/n:.1f}%) ================")

    # 1) D26 distribution
    md_ri, md_non = np.median(d26[y==1]), np.median(d26[y==0])
    U, p = mannwhitneyu(d26[y==1], d26[y==0], alternative='greater')
    auc_d26 = roc_auc_score(y, d26)
    print(f"Median D26  RI-onset = {md_ri:.0f} m   vs   non-RI = {md_non:.0f} m")
    print(f"Mann-Whitney (RI>non): p = {p:.2e}")
    print(f"AUC of D26 alone predicting RI onset: {auc_d26:.3f}")

    # 2) does D26 add skill beyond location + season + current intensity?
    sinm, cosm = np.sin(2*np.pi*mon/12), np.cos(2*np.pi*mon/12)
    def standardize(M):
        return (M - M.mean(0)) / (M.std(0) + 1e-9)
    X_base = standardize(np.column_stack([lat, lon, sinm, cosm, wind]))
    X_d26  = standardize(np.column_stack([lat, lon, sinm, cosm, wind, d26]))
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    lr = LogisticRegression(max_iter=2000, class_weight='balanced')
    auc_base = cross_val_score(lr, X_base, y, cv=cv, scoring='roc_auc').mean()
    auc_full = cross_val_score(lr, X_d26,  y, cv=cv, scoring='roc_auc').mean()
    print(f"\n5-fold CV AUC  [lat,lon,season,intensity]      = {auc_base:.3f}")
    print(f"5-fold CV AUC  [ ...               + D26 ]      = {auc_full:.3f}")
    print(f"Skill added by D26: {auc_full-auc_base:+.3f} AUC")

    # 3) terciles of D26 -> RI rate
    q1, q2 = np.percentile(d26, [33, 67])
    for lab, mask in [('shallow (<%.0fm)'%q1, d26<q1),
                      ('mid',      (d26>=q1)&(d26<q2)),
                      ('deep (>%.0fm)'%q2,    d26>=q2)]:
        print(f"  D26 {lab:16s}: RI rate {100*y[mask].mean():.1f}%  (n={mask.sum()})")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dryrun', action='store_true')
    ap.add_argument('--statsonly', action='store_true')
    args = ap.parse_args()
    storms = g.parse_hurdat(g.SRC)
    if args.dryrun:
        gulf = gulf_hurricanes(storms)
        fx = sum(len(labelled_fixes(s)) for s in gulf)
        ri = sum(sum(r[1] for r in labelled_fixes(s)) for s in gulf)
        print(f"{len(gulf)} storms, {fx} fixes, {ri} RI-onset"); return
    if not args.statsonly:
        build(storms)
    stats()

if __name__ == '__main__':
    main()
