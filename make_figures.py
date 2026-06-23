"""
make_figures.py — generate the figures embedded in NOAA_RI_observation_report
═══════════════════════════════════════════════════════════════════════════════
Clean, scientific charts built from the analysis outputs:
  fig1_hotspot_map.png   RI-onset likelihood surface + core/watch boxes (climatology)
  fig2_seasonality.png   RI onsets by month
  fig3_onset_intensity.png  storm intensity when RI begins
  fig4_scaled_d26.png    population test: D26 vs RI (distribution + tercile rates)
  fig5_storm_d26.png     four-storm co-location: D26 at RI vs Gulf background
"""
import json, csv, pathlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import build_gulf_hurricanes as g

DIR = pathlib.Path(__file__).parent
FIG = DIR / 'figures'; FIG.mkdir(exist_ok=True)
CLIM = json.loads((DIR / 'data' / 'ri_climatology.json').read_text())
ROWS = [r for r in csv.DictReader((DIR / 'data' / 'ohc' / 'ri_d26_samples.csv').open())]

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 10,
    'axes.titlesize': 12, 'axes.titleweight': 'bold',
    'axes.edgecolor': '#444', 'axes.linewidth': 0.8,
    'figure.dpi': 150, 'savefig.dpi': 150, 'savefig.bbox': 'tight',
    'axes.grid': True, 'grid.color': '#e6e6e6', 'grid.linewidth': 0.7,
})
INK, AMBER, RED, TEAL = '#16222e', '#c9700f', '#c0392b', '#0d6b73'

# ── Fig 1: hotspot map ────────────────────────────────────────────────────────
def fig1():
    cells = CLIM['cells']; st = CLIM['stats']
    lats = sorted(set(c['lat'] for c in cells)); lons = sorted(set(c['lon'] for c in cells))
    ny, nx = len(lats), len(lons)
    li = {v: i for i, v in enumerate(lats)}; lj = {v: i for i, v in enumerate(lons)}
    kde = np.full((ny, nx), np.nan)
    for c in cells:
        if c['kde'] >= 0.08:
            kde[li[c['lat']], lj[c['lon']]] = c['kde']
    fig, ax = plt.subplots(figsize=(8.2, 5.8))
    LON0, LON1, LAT0, LAT1 = -98, -80, 18, 31
    pm = ax.pcolormesh(np.array(lons), np.array(lats), kde, cmap='YlOrRd',
                       shading='nearest', vmin=0, vmax=1)
    # Gulf coastline (polygon)
    poly = np.array(g.GULF_POLY + [g.GULF_POLY[0]])
    ax.plot(poly[:, 0], poly[:, 1], color='#33444f', lw=1.3, alpha=.8)
    # boxes
    cb, wb = st['core_box'], st['watch_box']
    ax.add_patch(Rectangle((wb['lon0'], wb['lat0']), wb['lon1']-wb['lon0'], wb['lat1']-wb['lat0'],
                 fill=False, ec=AMBER, lw=1.6, ls='--', label='Watch box (1.95×)'))
    ax.add_patch(Rectangle((cb['lon0'], cb['lat0']), cb['lon1']-cb['lon0'], cb['lat1']-cb['lat0'],
                 fill=False, ec=RED, lw=2.2, label='Core box (3.1×)'))
    ce = st['centroid']; ax.plot(ce['lon'], ce['lat'], '*', ms=15, mfc='#fff', mec=RED, mew=1.5)
    ax.annotate('Bay of\nCampeche', (-94.2, 20.3), fontsize=8.5, color=INK, ha='center')
    ax.annotate('Loop Current /\nYucatan Channel', (-85.6, 23.6), fontsize=8.5, color=INK, ha='center')
    ax.set_xlim(LON0, LON1); ax.set_ylim(LAT0, LAT1)
    ax.set_xlabel('Longitude (°W)'); ax.set_ylabel('Latitude (°N)')
    xt = list(range(-96, -79, 4)); ax.set_xticks(xt)
    ax.set_xticklabels([str(abs(x)) for x in xt])
    ax.set_title('Where Gulf hurricanes begin to rapidly intensify (1851–2025)')
    ax.legend(loc='upper right', fontsize=8.5, framealpha=.95)
    cbar = fig.colorbar(pm, ax=ax, shrink=.85, pad=.02)
    cbar.set_label('Relative RI-onset likelihood (normalized)')
    ax.set_aspect(1.15)
    fig.savefig(FIG / 'fig1_hotspot_map.png'); plt.close(fig)

# ── Fig 2: seasonality ────────────────────────────────────────────────────────
def fig2():
    bm = CLIM['stats']['season']['by_month']
    months = list(range(5, 12))
    names = {5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov'}
    vals = [bm.get(str(m), 0) for m in months]
    cols = [RED if m in (8,9,10) else '#c9b79c' for m in months]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar([names[m] for m in months], vals, color=cols, edgecolor='#7a5a2a', lw=.5)
    ax.set_ylabel('Number of RI onsets'); ax.set_title('When RI happens: onsets by month')
    tot = sum(vals); aso = sum(bm.get(str(m),0) for m in (8,9,10))
    ax.annotate(f'Aug–Oct = {100*aso/tot:.0f}% of all onsets', (0.97, 0.93),
                xycoords='axes fraction', ha='right', fontsize=9.5, color=RED, fontweight='bold')
    ax.set_axisbelow(True); ax.grid(axis='x', alpha=0)
    fig.savefig(FIG / 'fig2_seasonality.png'); plt.close(fig)

# ── Fig 3: onset intensity ────────────────────────────────────────────────────
def fig3():
    w = np.array([float(r['wind']) for r in ROWS if r['is_ri'] == '1'])
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.hist(w, bins=np.arange(20, 130, 10), color=TEAL, edgecolor='#093d42', alpha=.85)
    ax.axvline(64, color=RED, lw=1.4, ls='--'); ax.annotate('hurricane\nstrength (64 kt)',
               (64, ax.get_ylim()[1]*.82), xytext=(78, ax.get_ylim()[1]*.82), fontsize=8.5, color=RED)
    med = np.median(w); ax.axvline(med, color=INK, lw=1.2)
    ax.annotate(f'median {med:.0f} kt', (med, ax.get_ylim()[1]*.96), fontsize=8.5, color=INK, ha='center')
    pct_ts = 100*np.mean(w <= 63)
    ax.set_xlabel('Storm intensity when RI begins (kt)'); ax.set_ylabel('Number of RI onsets')
    ax.set_title('RI begins while storms are still weak')
    ax.annotate(f'{pct_ts:.0f}% begin at tropical-storm strength (≤63 kt)',
                (0.97, 0.62), xycoords='axes fraction', ha='right', fontsize=9, color=INK)
    ax.set_axisbelow(True); ax.grid(axis='x', alpha=0)
    fig.savefig(FIG / 'fig3_onset_intensity.png'); plt.close(fig)

# ── Fig 4: scaled D26 test ────────────────────────────────────────────────────
def fig4():
    d = np.array([float(r['d26']) for r in ROWS if r['d26'] != ''])
    y = np.array([int(r['is_ri']) for r in ROWS if r['d26'] != ''])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.5, 4.2))
    bp = a1.boxplot([d[y==0], d[y==1]], tick_labels=['non-RI\nfixes', 'RI-onset\nfixes'],
                    patch_artist=True, widths=.55, showfliers=False)
    for patch, c in zip(bp['boxes'], ['#9fb3c0', RED]):
        patch.set_facecolor(c); patch.set_alpha(.65)
    for med in bp['medians']: med.set_color(INK); med.set_linewidth(1.6)
    a1.set_ylabel('D26 — depth of 26 °C isotherm (m)')
    a1.set_title('A. Ocean heat barely differs', fontsize=11)
    a1.annotate('medians 46 vs 44 m\nAUC = 0.55', (0.05, 0.9), xycoords='axes fraction',
                fontsize=8.5, va='top', color=INK)
    # terciles
    q1, q2 = np.percentile(d, [33, 67])
    masks = [d < q1, (d >= q1) & (d < q2), d >= q2]
    rates = [100*y[m].mean() for m in masks]
    a2.bar(['shallow', 'mid', 'deep'], rates, color=['#cfe0e6', '#6fa8b0', TEAL], edgecolor='#093d42', lw=.5)
    a2.set_ylabel('RI-onset rate (%)'); a2.set_title('B. …and adds little skill', fontsize=11)
    for i, v in enumerate(rates): a2.annotate(f'{v:.1f}%', (i, v+.3), ha='center', fontsize=9)
    a2.annotate('beyond location + season:\n+0.00 AUC', (0.5, 0.9), xycoords='axes fraction',
                ha='center', va='top', fontsize=8.5, color=INK)
    a2.set_axisbelow(True); a2.grid(axis='x', alpha=0); a1.grid(axis='x', alpha=0)
    fig.suptitle('Does measured ocean heat predict RI across 76 Gulf hurricanes?',
                 fontsize=12, fontweight='bold', y=1.02)
    fig.savefig(FIG / 'fig4_scaled_d26.png'); plt.close(fig)

# ── Fig 5: four-storm co-location ─────────────────────────────────────────────
def fig5():
    storms = ['Katrina\n2005', 'Rita\n2005', 'Helene\n2024', 'Milton\n2024']
    seg = [82, 67, 104, 52]; med = [51, 55, 62, 63]
    x = np.arange(4); w = 0.38
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.bar(x - w/2, seg, w, label='D26 along RI run-up', color=RED, alpha=.85, edgecolor='#7a1f17', lw=.5)
    ax.bar(x + w/2, med, w, label='Gulf-median D26 that day', color='#9fb3c0', edgecolor='#5a6b78', lw=.5)
    ax.set_xticks(x); ax.set_xticklabels(storms)
    ax.set_ylabel('D26 (m)'); ax.set_title('Did the storm rapidly intensify over deep warm water?')
    ax.legend(fontsize=8.5, loc='upper left')
    ax.annotate('Milton: RI over\nbelow-median D26', (3, 56), xytext=(2.25, 92), fontsize=8.5,
                color=RED, ha='center', arrowprops=dict(arrowstyle='->', color=RED, lw=1))
    ax.set_axisbelow(True); ax.grid(axis='x', alpha=0)
    fig.savefig(FIG / 'fig5_storm_d26.png'); plt.close(fig)

# ── Fig 6: measured D26 beneath each storm, with track ────────────────────────
def _load_d26(fn):
    d = json.loads((DIR / 'data' / 'ohc' / f'{fn}_d26.json').read_text())
    lats = np.array(d['lats']); lons = np.array(d['lons'])
    grid = np.array([[np.nan if v is None else v for v in row] for row in d['d26']])
    return lats, lons, grid, d.get('time_utc', '')

def fig6():
    cells = [('Katrina', 'AL122005', 'katrina'), ('Rita', 'AL182005', 'rita'),
             ('Helene', 'AL092024', 'helene'), ('Milton', 'AL142024', 'milton')]
    storms = {s['id']: s for s in g.parse_hurdat(g.SRC)}
    fig, axs = plt.subplots(2, 2, figsize=(11, 9.2))
    pm = None
    for ax, (nm, sid, fn) in zip(axs.flat, cells):
        lats, lons, grid, tval = _load_d26(fn)
        pm = ax.pcolormesh(lons, lats, grid, cmap='YlOrRd', shading='nearest', vmin=0, vmax=180)
        poly = np.array(g.GULF_POLY + [g.GULF_POLY[0]])
        ax.plot(poly[:, 0], poly[:, 1], color='#33444f', lw=1, alpha=.6)
        tr = storms[sid]['track']
        ax.plot([p['lon'] for p in tr], [p['lat'] for p in tr], color='#16222e', lw=1.2, alpha=.85)
        ramp = g.intensification_to_peak(tr)
        if ramp:
            rc = np.array(ramp['coords'])
            ax.plot(rc[:, 0], rc[:, 1], color='#103a6e', lw=3.2, solid_capstyle='round')
            ax.plot(ramp['peak_lon'], ramp['peak_lat'], '*', ms=13, mfc='#fff', mec='#103a6e', mew=1.3)
        ax.set_xlim(-98, -80); ax.set_ylim(18, 31); ax.set_aspect(1.15)
        ax.set_title(f"{nm} — {tval[:10]}", fontsize=11)
        ax.set_xticks(range(-96, -79, 4)); ax.set_xticklabels([str(abs(x)) for x in range(-96, -79, 4)])
        ax.tick_params(labelsize=8); ax.grid(alpha=.15)
    fig.suptitle('Measured ocean heat (D26) beneath each storm, with its rapid-intensification run-up (blue) and peak (★)',
                 fontsize=12.5, fontweight='bold', y=.995)
    cb = fig.colorbar(pm, ax=axs, shrink=.62, pad=.02)
    cb.set_label('D26 — depth of the 26 °C isotherm (m);  deeper = more ocean heat')
    fig.savefig(FIG / 'fig6_storm_d26_maps.png'); plt.close(fig)

# ── Fig 7: two operational watch zones ────────────────────────────────────────
def fig7():
    st = CLIM['stats']; cb, wb = st['core_box'], st['watch_box']
    fig, ax = plt.subplots(figsize=(8.4, 5.9))
    poly = np.array(g.GULF_POLY + [g.GULF_POLY[0]])
    ax.fill(poly[:, 0], poly[:, 1], color='#eef3f6', zorder=0)
    ax.plot(poly[:, 0], poly[:, 1], color='#33444f', lw=1.2)
    # Zone B — Loop Current corridor / landfall continuation
    ax.add_patch(Rectangle((-94, 24), 8, 5, fc=AMBER, ec=AMBER, alpha=.16, lw=1.6))
    ax.add_patch(Rectangle((-94, 24), 8, 5, fill=False, ec=AMBER, lw=1.6))
    # Zone A — onset core + watch
    ax.add_patch(Rectangle((wb['lon0'], wb['lat0']), wb['lon1']-wb['lon0'], wb['lat1']-wb['lat0'],
                 fill=False, ec=RED, ls='--', lw=1.5))
    ax.add_patch(Rectangle((cb['lon0'], cb['lat0']), cb['lon1']-cb['lon0'], cb['lat1']-cb['lat0'],
                 fc=RED, ec=RED, alpha=.22, lw=2.2))
    ax.annotate('ZONE A — onset\nsouthern Gulf core\n(sample ocean ahead,\neven of weak storms)',
                (-92.7, 21.7), fontsize=9, color='#7a1f17', ha='center', va='center', fontweight='bold')
    ax.annotate('ZONE B — continuation\nLoop Current corridor &\nN-central shelf (RI to landfall)',
                (-89.5, 26.6), fontsize=9, color='#7a5a18', ha='center', va='center', fontweight='bold')
    ax.annotate('Yucatan\nChannel', (-85.7, 21.6), fontsize=8, color='#33444f', ha='center')
    ax.set_xlim(-98, -80); ax.set_ylim(18, 31); ax.set_aspect(1.15)
    ax.set_xticks(range(-96, -79, 4)); ax.set_xticklabels([str(abs(x)) for x in range(-96, -79, 4)])
    ax.set_xlabel('Longitude (°W)'); ax.set_ylabel('Latitude (°N)')
    ax.set_title('Two operational watch zones for Gulf RI observations')
    fig.savefig(FIG / 'fig7_zones.png'); plt.close(fig)

if __name__ == '__main__':
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6(); fig7()
    print("Wrote figures:", *[p.name for p in sorted(FIG.glob('*.png'))])
