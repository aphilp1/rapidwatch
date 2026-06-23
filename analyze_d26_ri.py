"""
analyze_d26_ri.py — does the real ocean-heat data explain the rapid intensification?
═══════════════════════════════════════════════════════════════════════════════════
For each of the 4 storms we now have a measured D26 field. This co-locates that
field with the storm's actual HURDAT2 best track and asks the mechanism question:
did the storm rapidly intensify OVER anomalously deep warm water?

For each storm:
  - find the 24-h window of maximum intensification (the RI core) from best track
  - sample the real D26 at the RI-onset location and along the RI segment
  - compare to the Gulf-box background (median + 90th pct) of the same field
Honest caveats printed at the end.
"""
import json, pathlib
import numpy as np
import build_gulf_hurricanes as g
fix_dt = g.fix_dt

DIR = pathlib.Path(__file__).parent
OHC = DIR / 'data' / 'ohc'

STORMS = {'katrina': 'AL122005', 'rita': 'AL182005',
          'helene': 'AL092024', 'milton': 'AL142024'}

def load_grid(name):
    d = json.loads((OHC / f'{name}_d26.json').read_text())
    lats = np.array(d['lats'], float); lons = np.array(d['lons'], float)
    grid = np.array([[np.nan if v is None else v for v in row] for row in d['d26']], float)
    return lats, lons, grid, d['source'], d['time_utc']

def sample(lats, lons, grid, lat, lon):
    """nearest-valid-cell sample of D26 at (lat,lon)."""
    i = int(np.argmin(np.abs(lats - lat))); j = int(np.argmin(np.abs(lons - lon)))
    # search outward for a non-nan cell (storm centre may sit on a masked point)
    for rad in range(0, 4):
        i0, i1 = max(0, i - rad), min(len(lats), i + rad + 1)
        j0, j1 = max(0, j - rad), min(len(lons), j + rad + 1)
        sub = grid[i0:i1, j0:j1]
        if np.isfinite(sub).any():
            return float(np.nanmean(sub))
    return np.nan

def ri_core(track):
    """Return (onset_fix, plus24_fix, dW) for the 24-h window of max intensification."""
    best = (None, None, -1)
    for i, p in enumerate(track):
        if p['wind'] is None:
            continue
        # nearest fix ~24h ahead
        ti = fix_dt(p)
        j = None; bestd = 99
        for k in range(i + 1, len(track)):
            dh = (fix_dt(track[k]) - ti).total_seconds() / 3600
            if dh > 27: break
            if dh >= 21 and abs(dh - 24) < bestd and track[k]['wind'] is not None:
                j, bestd = k, abs(dh - 24)
        if j is not None:
            dW = track[j]['wind'] - p['wind']
            if dW > best[2]:
                best = (p, track[j], dW)
    return best

def main():
    storms = {s['id']: s for s in g.parse_hurdat(g.SRC)}
    print(f"{'STORM':9s} {'RI core 24h':>11s}  {'onset loc':>16s}  "
          f"{'D26@onset':>9s} {'D26 RIseg':>9s} {'Gulf med':>8s} {'Gulf p90':>8s}  ratio")
    print('-' * 96)
    rows = []
    for name, sid in STORMS.items():
        lats, lons, grid, src, tval = load_grid(name)
        bg_med = float(np.nanmedian(grid)); bg_p90 = float(np.nanpercentile(grid, 90))
        tr = storms[sid]['track']
        onset, plus24, dW = ri_core(tr)
        seg = [p for p in tr if fix_dt(onset) <= fix_dt(p) <= fix_dt(plus24)]
        d_on = sample(lats, lons, grid, onset['lat'], onset['lon'])
        d_seg = np.nanmean([sample(lats, lons, grid, p['lat'], p['lon']) for p in seg])
        ratio = d_seg / bg_med if bg_med else np.nan
        rows.append((name, dW, d_on, d_seg, bg_med, bg_p90, ratio))
        print(f"{name:9s} {('+'+str(dW)+' kt'):>11s}  "
              f"{onset['lat']:5.1f}N {abs(onset['lon']):5.1f}W  "
              f"{d_on:8.0f}m {d_seg:8.0f}m {bg_med:7.0f}m {bg_p90:7.0f}m  {ratio:4.2f}x")
    print('-' * 96)
    seg_vals = [r[3] for r in rows]; med_vals = [r[4] for r in rows]
    print(f"\nMean across 4 storms: D26 over RI segment = {np.mean(seg_vals):.0f} m  "
          f"vs Gulf background median = {np.mean(med_vals):.0f} m  "
          f"({np.mean([r[6] for r in rows]):.2f}x)")
    above = sum(1 for r in rows if r[3] > r[4])
    print(f"Storms that rapidly intensified over ABOVE-median D26: {above}/4")
    print("\nCAVEATS: one D26 snapshot per storm (~RI-day); storm cold-wake can depress")
    print("D26 at the centre (we sample nearest-valid + segment mean to reduce this);")
    print("4 cases corroborate the mechanism but are NOT a statistical test — see note.")

if __name__ == '__main__':
    main()
