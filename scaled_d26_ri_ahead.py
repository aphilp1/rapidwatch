"""
scaled_d26_ri_ahead.py — §5.7 refinement: sample D26 AHEAD OF TRACK, not at the centre.
═══════════════════════════════════════════════════════════════════════════════
The original scaled_d26_ri.py sampled D26 at each storm's own centre, where the
storm's cold wake and best-track position error bias the ocean-heat association
LOW (report footnote [^1]). This refinement re-samples the SAME cached ocean
fields (data/ohc/raw/*.nc — no re-download) at a point a fixed lead-distance
AHEAD of the storm along its heading: the ocean it is about to enter, ahead of
the wake. We then re-run the identical statistics and compare.

  python scaled_d26_ri_ahead.py                 # default lead 1.0° (~111 km)
  python scaled_d26_ri_ahead.py --lead 1.5      # tune the lead distance
  python scaled_d26_ri_ahead.py --sweep         # compare several leads + centre
  python scaled_d26_ri_ahead.py --statsonly     # stats on existing ahead CSV
"""
import sys, argparse, csv, math, pathlib
import numpy as np
import build_gulf_hurricanes as g
import scaled_d26_ri as base

DIR = pathlib.Path(__file__).parent
OHC = DIR / 'data' / 'ohc'
RAW = OHC / 'raw'

def ahead_point(tr, i, lead_deg):
    """Point lead_deg great-circle degrees ahead of fix i along the storm heading."""
    if i + 1 < len(tr):   a, b = tr[i], tr[i + 1]
    elif i > 0:           a, b = tr[i - 1], tr[i]
    else:                 return tr[i]['lat'], tr[i]['lon']
    clat = math.cos(math.radians(tr[i]['lat'])) or 1e-6
    dlat = b['lat'] - a['lat']
    dlon = (b['lon'] - a['lon']) * clat
    n = math.hypot(dlat, dlon)
    if n < 1e-6:          return tr[i]['lat'], tr[i]['lon']
    alat = tr[i]['lat'] + lead_deg * dlat / n
    alon = tr[i]['lon'] + lead_deg * (dlon / n) / clat
    return alat, alon

def csv_for(lead):
    return OHC / f"ri_d26_ahead_{str(lead).replace('.','p')}.csv"

def build(storms, lead):
    gulf = base.gulf_hurricanes(storms)
    out_csv = csv_for(lead)
    f = out_csv.open('w', newline=''); w = csv.writer(f)
    w.writerow(['id','name','year','month','lat','lon','alat','alon','wind','dW24','is_ri','d26'])
    nfield = nrows = 0
    for s in gulf:
        path = RAW / f"{s['id']}_thetao.nc"
        if not path.exists():                       # cached-only; never re-download
            continue
        try:    fld = base.open_field(path)
        except Exception: continue
        nfield += 1
        tr = s['track']
        for i, p in enumerate(tr):
            if p['wind'] is None or not g.in_gulf(p['lon'], p['lat']):
                continue
            j = base.near_24h(tr, i)
            if j is None: continue
            is_ri = int(tr[j]['wind'] - p['wind'] >= 30); dW = tr[j]['wind'] - p['wind']
            alat, alon = ahead_point(tr, i, lead)
            d26 = base.sample_d26(fld, alat, alon)
            w.writerow([s['id'], s['name'], s['year'], int(p['date'][4:6]),
                        round(p['lat'],2), round(p['lon'],2), round(alat,2), round(alon,2),
                        p['wind'], dW, is_ri, '' if np.isnan(d26) else round(d26,1)])
            nrows += 1
    f.close()
    print(f"  lead {lead}°: {nfield} cached fields, {nrows} fixes -> {out_csv.name}")
    return out_csv

def summarize(csv_path, label):
    from scipy.stats import mannwhitneyu
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    from sklearn.metrics import roc_auc_score
    rows = [r for r in csv.DictReader(csv_path.open()) if r['d26'] != '']
    y   = np.array([int(r['is_ri']) for r in rows])
    d26 = np.array([float(r['d26']) for r in rows])
    lat = np.array([float(r['lat']) for r in rows]); lon = np.array([float(r['lon']) for r in rows])
    mon = np.array([int(r['month']) for r in rows]); wind= np.array([float(r['wind']) for r in rows])
    n, npos = len(y), int(y.sum())
    md_ri, md_non = np.median(d26[y==1]), np.median(d26[y==0])
    _, pmw = mannwhitneyu(d26[y==1], d26[y==0], alternative='greater')
    auc_d26 = roc_auc_score(y, d26)
    sinm, cosm = np.sin(2*np.pi*mon/12), np.cos(2*np.pi*mon/12)
    std = lambda M: (M - M.mean(0)) / (M.std(0) + 1e-9)
    Xb = std(np.column_stack([lat, lon, sinm, cosm, wind]))
    Xd = std(np.column_stack([lat, lon, sinm, cosm, wind, d26]))
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    lr = LogisticRegression(max_iter=2000, class_weight='balanced')
    ab = cross_val_score(lr, Xb, y, cv=cv, scoring='roc_auc').mean()
    af = cross_val_score(lr, Xd, y, cv=cv, scoring='roc_auc').mean()
    return dict(label=label, n=n, npos=npos, md_ri=md_ri, md_non=md_non, p=pmw,
                auc=auc_d26, base=ab, full=af, add=af-ab)

def print_row(r):
    print(f"  {r['label']:18s}  n={r['n']:3d}/{r['npos']:<3d}  "
          f"med {r['md_ri']:4.0f} vs {r['md_non']:4.0f} m  p={r['p']:.2g}  "
          f"AUC(D26)={r['auc']:.3f}  CV {r['base']:.3f}->{r['full']:.3f} ({r['add']:+.3f})")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lead', type=float, default=1.0)
    ap.add_argument('--sweep', action='store_true')
    ap.add_argument('--statsonly', action='store_true')
    args = ap.parse_args()
    storms = g.parse_hurdat(g.SRC)
    leads = [0.5, 1.0, 1.5, 2.0] if args.sweep else [args.lead]

    print("="*92)
    print("D26 vs RI — CENTRE (original) vs AHEAD-OF-TRACK  [med = median D26 RI vs non-RI]")
    print("="*92)
    # centre baseline from the original CSV
    if base.CSV.exists():
        print_row(summarize(base.CSV, 'centre (original)'))
    for lead in leads:
        cp = csv_for(lead)
        if not args.statsonly:
            cp = build(storms, lead)
        if cp.exists():
            print_row(summarize(cp, f'ahead {lead}°'))

if __name__ == '__main__':
    main()
