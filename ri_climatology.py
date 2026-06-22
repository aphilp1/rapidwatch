"""
ri_climatology.py — RapidWatch observed rapid-intensification (RI) climatology
═════════════════════════════════════════════════════════════════════════════
Question: WHERE (and when) do Gulf hurricanes preferentially undergo rapid
intensification, based on 175 years of NOAA best-track history?

Method (all from data/hurdat2-atlantic.txt, reusing build_gulf_hurricanes):
  1. Restrict to storms that reached hurricane status AND entered the Gulf.
  2. RI ONSET detection at every best-track fix: an onset is a fix whose wind
     rises >= 30 kt over the next ~24 h (NOAA's operational RI threshold).
     The onset is geolocated at the START fix — the place you would want eyes
     on the ocean BEFORE the storm blows up.
  3. Grid the Gulf + approaches (0.25 deg). Per cell:
        n_fix  total hurricane fixes passing through  (exposure / traffic)
        n_ri   RI onsets that started in the cell
        rate   n_ri / n_fix  (conditional RI propensity — corrects for traffic)
  4. Gaussian KDE of onset points -> a smooth, normalized RI-likelihood surface.
  5. Locate the hotspot centroid + a "RI Watch Box" (cells >= 60% of peak KDE).
  6. Seasonality (month of onset) and onset-intensity distribution.
  7. Overlap with the Loop Current / warm-eddy deep-warm-water corridor.

Outputs:
  data/ri_climatology.json   grid + watch box + centroid + season + stats
  console RESULTS block (the numbers cited in the NOAA report)

Honesty / limits: this is a CLIMATOLOGY (a historical prior), not a dynamical
forecast. Best-track winds carry real uncertainty, larger in the pre-aircraft
era (<1944); observing density also grew over time. RI here = >=30 kt/24 h.
"""

import json, math, pathlib
from collections import Counter, defaultdict
import build_gulf_hurricanes as g

DIR    = pathlib.Path(__file__).parent
OUT    = DIR / 'data' / 'ri_climatology.json'

# analysis domain: Gulf proper + SE approaches (Yucatan Channel & Florida Straits)
LON0, LON1 =  -98.0, -80.0
LAT0, LAT1 =   18.0,  31.0
DEG        =   0.25            # grid spacing
KDE_BW     =   0.75            # KDE bandwidth (degrees)
MIN_FIX    =   30              # min exposure for a trustworthy per-cell conditional rate

# deep-warm-water corridor (Loop Current + shed warm-core eddies) from RapidWatch
CORRIDOR = {'lat0': 23.0, 'lat1': 27.0, 'lon0': -91.0, 'lon1': -85.0}

def in_box(lat, lon):
    return LAT0 <= lat <= LAT1 and LON0 <= lon <= LON1

def near_24h(track, i):
    """Return index j>i whose time is closest to i+24h within [21,27]h, else None."""
    ti = g.fix_dt(track[i])
    best, bestd = None, 99
    for j in range(i + 1, len(track)):
        dh = (g.fix_dt(track[j]) - ti).total_seconds() / 3600.0
        if dh > 27:
            break
        if dh >= 21 and abs(dh - 24) < bestd:
            best, bestd = j, abs(dh - 24)
    return best

def main():
    storms = g.parse_hurdat(g.SRC)

    # qualifying set: ever-hurricane AND entered Gulf polygon
    qual = [s for s in storms
            if any(p['status'] == 'HU' for p in s['track'])
            and any(g.in_gulf(p['lon'], p['lat']) for p in s['track'])]

    onsets   = []          # dicts: lat, lon, month, w0, w1, delta, storm, year
    ri_storm = set()
    fix_pts  = []          # all in-box hurricane-eligible fixes (exposure)

    for s in qual:
        tr = s['track']
        for p in tr:
            if in_box(p['lat'], p['lon']) and p['wind'] is not None:
                fix_pts.append((p['lat'], p['lon']))
        for i, p in enumerate(tr):
            if p['wind'] is None or not in_box(p['lat'], p['lon']):
                continue
            j = near_24h(tr, i)
            if j is None or tr[j]['wind'] is None:
                continue
            dW = tr[j]['wind'] - p['wind']
            if dW >= 30:
                onsets.append({'lat': p['lat'], 'lon': p['lon'],
                               'month': int(p['date'][4:6]),
                               'w0': p['wind'], 'w1': tr[j]['wind'], 'delta': dW,
                               'storm': s['name'], 'year': s['year']})
                ri_storm.add(s['id'])

    # ── grid ───────────────────────────────────────────────────────────────────
    nx = int(round((LON1 - LON0) / DEG))
    ny = int(round((LAT1 - LAT0) / DEG))
    nfix = defaultdict(int)
    nri  = defaultdict(int)
    def cell(lat, lon):
        cx = min(nx - 1, int((lon - LON0) / DEG))
        cy = min(ny - 1, int((lat - LAT0) / DEG))
        return cx, cy
    for lat, lon in fix_pts:
        nfix[cell(lat, lon)] += 1
    for o in onsets:
        nri[cell(o['lat'], o['lon'])] += 1

    cells = []
    inv2 = 1.0 / (2 * KDE_BW * KDE_BW)
    for cy in range(ny):
        for cx in range(nx):
            clat = LAT0 + (cy + 0.5) * DEG
            clon = LON0 + (cx + 0.5) * DEG
            nf = nfix[(cx, cy)]
            nr = nri[(cx, cy)]
            # KDE from all onsets
            k = 0.0
            for o in onsets:
                dy = clat - o['lat']; dx = clon - o['lon']
                k += math.exp(-(dx * dx + dy * dy) * inv2)
            rate = (nr / nf) if nf >= MIN_FIX else None
            cells.append({'lat': round(clat, 3), 'lon': round(clon, 3),
                          'n_fix': nf, 'n_ri': nr,
                          'rate': round(rate, 4) if rate is not None else None,
                          'kde': k})

    kmax = max(c['kde'] for c in cells) or 1.0
    for c in cells:
        c['kde'] = round(c['kde'] / kmax, 4)         # normalize 0..1

    # hotspot centroid = KDE-weighted mean of onset points
    sw = sum(1 for _ in onsets)
    cen_lat = sum(o['lat'] for o in onsets) / sw
    cen_lon = sum(o['lon'] for o in onsets) / sw

    # peak KDE cell
    peak = max(cells, key=lambda c: c['kde'])

    # RI Watch boxes: tiered by KDE intensity. core = operational target.
    def box_of(thresh):
        h = [c for c in cells if c['kde'] >= thresh]
        return {'lat0': round(min(c['lat'] for c in h), 2),
                'lat1': round(max(c['lat'] for c in h), 2),
                'lon0': round(min(c['lon'] for c in h), 2),
                'lon1': round(max(c['lon'] for c in h), 2),
                'cells': len(h)}
    core    = box_of(0.80)        # tight operational target
    watch   = box_of(0.60)        # broader elevated zone

    # ── "lift": P(RI onset | a hurricane fix here) vs domain average ─────────────
    def box_counts(b):
        nf = sum(1 for lat, lon in fix_pts
                 if b['lat0'] <= lat <= b['lat1'] and b['lon0'] <= lon <= b['lon1'])
        nr = sum(1 for o in onsets
                 if b['lat0'] <= o['lat'] <= b['lat1'] and b['lon0'] <= o['lon'] <= b['lon1'])
        return nf, nr
    dom_rate = len(onsets) / len(fix_pts)
    cf, cr = box_counts(core)
    wf, wr = box_counts(watch)
    core_rate = cr / cf if cf else 0
    watch_rate = wr / wf if wf else 0
    lift = {'domain_rate': round(dom_rate, 4),
            'core_rate': round(core_rate, 4), 'core_lift': round(core_rate / dom_rate, 2),
            'core_fix': cf, 'core_ri': cr,
            'watch_rate': round(watch_rate, 4), 'watch_lift': round(watch_rate / dom_rate, 2),
            'watch_fix': wf, 'watch_ri': wr}

    # highest conditional-rate cell (well-sampled)
    rated = [c for c in cells if c['rate'] is not None]
    toprate = sorted(rated, key=lambda c: -c['rate'])[:5]

    # seasonality
    mon = Counter(o['month'] for o in onsets)
    tot = sum(mon.values())
    aso = sum(mon[m] for m in (8, 9, 10))
    peak_month = mon.most_common(1)[0][0]

    # onset intensity (how strong storms are WHEN RI begins)
    w0 = sorted(o['w0'] for o in onsets)
    med_w0 = w0[len(w0) // 2]
    pct_ts = 100 * sum(1 for w in w0 if w <= 63) / len(w0)   # begins at <= TS
    pct_c1 = 100 * sum(1 for w in w0 if w <= 83) / len(w0)   # begins at <= Cat 1

    # corridor overlap
    in_corr = sum(1 for o in onsets
                  if CORRIDOR['lat0'] <= o['lat'] <= CORRIDOR['lat1']
                  and CORRIDOR['lon0'] <= o['lon'] <= CORRIDOR['lon1'])
    pct_corr = 100 * in_corr / len(onsets)

    # strongest jumps
    big = sorted(onsets, key=lambda o: -o['delta'])[:8]

    stats = {
        'qualifying_storms': len(qual),
        'ri_storms': len(ri_storm),
        'ri_onsets': len(onsets),
        'centroid': {'lat': round(cen_lat, 2), 'lon': round(cen_lon, 2)},
        'peak_cell': {'lat': peak['lat'], 'lon': peak['lon'], 'kde': peak['kde']},
        'core_box': core,
        'watch_box': watch,
        'lift': lift,
        'top_rate_cells': [{'lat': c['lat'], 'lon': c['lon'],
                            'rate': c['rate'], 'n_fix': c['n_fix'], 'n_ri': c['n_ri']}
                           for c in toprate],
        'season': {'by_month': dict(sorted(mon.items())),
                   'peak_month': peak_month,
                   'pct_aug_oct': round(100 * aso / tot, 1)},
        'onset_intensity': {'median_kt': med_w0,
                            'pct_begin_at_or_below_TS': round(pct_ts, 1),
                            'pct_begin_at_or_below_Cat1': round(pct_c1, 1)},
        'corridor': {'box': CORRIDOR, 'pct_onsets_in_corridor': round(pct_corr, 1)},
        'strongest_jumps': [{'storm': o['storm'], 'year': o['year'],
                             'delta_kt': o['delta'], 'w0': o['w0'], 'w1': o['w1'],
                             'lat': round(o['lat'], 1), 'lon': round(o['lon'], 1)}
                            for o in big],
    }

    OUT.write_text(json.dumps(
        {'meta': {'source': 'NOAA HURDAT2 1851-2025 (02272026 release)',
                  'method': 'RI onset (>=30kt/24h) climatology; KDE bw=%.2fdeg; grid=%.2fdeg' % (KDE_BW, DEG),
                  'domain': {'lat': [LAT0, LAT1], 'lon': [LON0, LON1]}},
         'stats': stats,
         'cells': cells}, indent=1))

    # ── RESULTS ─────────────────────────────────────────────────────────────────
    P = print
    P("\n================ RI CLIMATOLOGY — RESULTS ================")
    P(f"Qualifying Gulf hurricanes (1851-2025): {len(qual)}")
    P(f"  ...that underwent >=1 RI onset in-domain: {len(ri_storm)} "
      f"({100*len(ri_storm)/len(qual):.0f}%)")
    P(f"Total RI onset intervals detected: {len(onsets)}")
    P(f"\nHOTSPOT centroid: {cen_lat:.2f}N {abs(cen_lon):.2f}W")
    P(f"Peak-density cell: {peak['lat']:.2f}N {abs(peak['lon']):.2f}W")
    P(f"CORE box (KDE>=80%): {core['lat0']}-{core['lat1']}N, "
      f"{abs(core['lon1'])}-{abs(core['lon0'])}W")
    P(f"WATCH box (KDE>=60%): {watch['lat0']}-{watch['lat1']}N, "
      f"{abs(watch['lon1'])}-{abs(watch['lon0'])}W")
    P(f"\nLIFT (P[RI onset | fix]): domain={lift['domain_rate']*100:.1f}%  "
      f"core={lift['core_rate']*100:.1f}% ({lift['core_lift']}x)  "
      f"watch={lift['watch_rate']*100:.1f}% ({lift['watch_lift']}x)")
    P(f"\nHighest conditional RI rate cells (RI onsets / fixes, n_fix>={MIN_FIX}):")
    for c in toprate:
        P(f"   {c['lat']:.2f}N {abs(c['lon']):.2f}W  rate={c['rate']*100:.0f}%  "
          f"({c['n_ri']} RI / {c['n_fix']} fixes)")
    P(f"\nSeasonality: peak month = {peak_month:02d}; "
      f"Aug-Oct share = {stats['season']['pct_aug_oct']}%")
    P(f"Onset intensity: median {med_w0} kt; "
      f"{pct_ts:.0f}% of RI begins at <=TS, {pct_c1:.0f}% at <=Cat 1")
    P(f"Corridor overlap: {pct_corr:.0f}% of RI onsets inside the "
      f"Loop Current / warm-eddy box {CORRIDOR['lat0']}-{CORRIDOR['lat1']}N "
      f"{abs(CORRIDOR['lon0'])}-{abs(CORRIDOR['lon1'])}W")
    P("\nStrongest 24-h jumps on record (in-domain):")
    for o in big:
        P(f"   {o['year']} {o['storm']:14s} +{o['delta']} kt "
          f"({o['w0']}->{o['w1']}) @ {o['lat']:.1f}N {abs(o['lon']):.1f}W")
    P(f"\nWrote {OUT.name}  ({OUT.stat().st_size//1024} KB)")
    P("=========================================================")

if __name__ == '__main__':
    main()
