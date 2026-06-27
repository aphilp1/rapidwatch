# RAPIDWATCH — Gulf Rapid Intensification Observatory

A working reference for the sensors, platforms, and science used to observe and
forecast **hurricane rapid intensification (RI)** — a maximum-wind increase of
**30 kt (35 mph) in 24 hours** (NHC threshold) — across the Gulf of Mexico
(Gulf of America). Sibling project to Stormwatch; same build philosophy
(hindcast known events to learn where each model layer fails).

**Live site:** https://aphilp1.github.io/rapidwatch/
&nbsp;·&nbsp; **App:** https://aphilp1.github.io/rapidwatch/rapidwatch-gulf-ri.html
&nbsp;·&nbsp; **Repo:** https://github.com/aphilp1/rapidwatch

The site auto-deploys from `master` via GitHub Pages, and a scheduled GitHub
Action refreshes the live buoy/storm data every 30 minutes.

## The thesis

Track forecasting has improved for decades; intensity — and the *timing* of RI —
remains the hard problem, and the Gulf concentrates every ingredient that drives it.
The Gulf-specific signal is **deep ocean heat**: the Loop Current and the warm-core
eddies it sheds carry a warm layer 80–150 m deep, so a storm's self-induced cold
wake doesn't cut off its fuel. Knowing that heat reservoir *before* a storm forms is
the highest-leverage, most Gulf-specific observation — which is why the observing
priorities and the modeling priorities point at the same place: the upper-ocean
heat field and the air–sea interface.

The project's analysis (see the **Analysis** tab / report) quantifies *where* and
*when* RI begins in the Gulf from 175 years of best-track data, and tests the
ocean-heat link directly against reconstructed ocean fields.

## The app — three tabs

The published page (`rapidwatch-gulf-ri.html`) is a single app with three tabs:

- **RI Observatory** — the observing-systems reference. An interactive vertical
  "stack" from geostationary orbit (35,786 km) down to a 2,000 m float, with every
  platform tappable; the air–sea interface is highlighted as the flux bottleneck.
  Includes the Gulf RI problem, the four-tier platform catalog, a ranked
  "what's essential" deployment argument, and where RI happens.
- **Gulf Map** — a coordinate-accurate, fully self-contained Leaflet canvas
  (Leaflet + coastline inlined, renders offline) with toggleable layers (see below).
- **Analysis** — the full research memo, *Understanding Hurricane Rapid
  Intensification Dynamics*, embedded as a styled report with seven figures.

### Gulf Map layers

- **Real hurricane best tracks** — Katrina/Rita (2005), Helene/Milton (2024),
  colored by Saffir–Simpson category with the RI stretch ringed in amber.
- **Live GOES RI animations** — georeferenced Band-13 IR video overlays of each
  storm's rapid-intensification window (2005 via GridSat-GOES, 2024 via GOES-16).
- **Real ocean heat (D26)** — measured depth of the 26 °C isotherm beneath each of
  the four storms (HYCOM GOFS 3.1 for 2005, Copernicus GLORYS for 2024).
- **Gulf RI Watch — Zone A / Zone B** — the two operational watch zones from the
  report: Zone A (onset core, primary target) and Zone B (Loop Current corridor &
  north-central shelf, secondary target).
- **RI climatology hotspot** — observed RI-onset density (1851–2025), exposure-
  normalized, with the 3.1× core box.
- **Historical Gulf hurricanes** — 326 Gulf hurricanes from HURDAT2 (1851–2025),
  plus their run-up-to-peak intensification segments.
- **Ocean context** — Loop Current & OHC corridor, warm-core eddies (with rotation),
  animated surface currents, peak-season SST and wind-shear climatology.
- **Live observing assets** — NDBC buoys (live SST/wind/pressure) and the active
  NHC storm cone, refreshed server-side; plus Argo floats, glider/saildrone zones,
  and Hurricane Hunter bases. Click any Gulf water point for a D26 depth sounding.

## How it's built

The published page is **assembled** — do not edit it directly:

```
rapidwatch-gulf-ri-source.html  ┐
rapidwatch-gulf-map.html        ┙─ python assemble_rapidwatch.py ─►  rapidwatch-gulf-ri.html
                                                                     rapidwatch.html
```

Edit a source file, run `python assemble_rapidwatch.py`, then hard-refresh.
The **Analysis** tab is an iframe of `NOAA_RI_observation_report.html`, which is
rendered from the Markdown report by `make_report_html.py` (figures from
`make_figures.py`).

### Live data (no CORS proxy)

`.github/workflows/live-data.yml` runs `build_live_data.py` every 30 minutes,
fetches NDBC buoys + the NHC cone server-side, and commits trimmed same-origin
snapshots under `data/`. The page fetches those local files, so live data works
for every visitor without a third-party proxy.

## Directory layout

```
RapidWatch/
├── index.html                       public landing page (links into the app)
├── rapidwatch-gulf-ri.html          ← published app (assembled — do not edit)
├── rapidwatch.html                  identical assembled copy
├── rapidwatch-gulf-ri-source.html   SOURCE: RI Observatory tab
├── rapidwatch-gulf-map.html         SOURCE: Gulf Map tab
├── assemble_rapidwatch.py           builds the two assembled files from the sources
├── NOAA_RI_observation_report.md    the research memo (source)
├── NOAA_RI_observation_report.html  rendered report (the Analysis tab)
├── make_report_html.py / make_figures.py    report + figure pipeline
├── serve.bat                        double-click: serves the folder at :8000
├── .github/workflows/live-data.yml  30-min live buoy/cone refresh
├── docs/
│   ├── observing_systems.md         four-tier sensor catalog
│   └── RI_literature.md             curated, verified reading list
├── figures/                         report figures (PNG)
└── data/
    ├── storms.geojson               real best tracks (4 storms)
    ├── gulf_hurricanes.geojson      326 Gulf hurricanes (HURDAT2 1851–2025)
    ├── ri_climatology.json          observed RI-onset density grid
    ├── ohc/                         measured D26 fields + the D26-vs-RI study
    ├── overlays/                    georeferenced GOES RI animation videos
    ├── ndbc/  nhc_currentstorms.json  live buoy + storm snapshots (auto-refreshed)
    └── geo/                         coastline / land geometry
```

### Analysis scripts

`build_gulf_hurricanes.py` (HURDAT2 → Gulf storm library) · `ri_climatology.py`
(RI-onset climatology) · `build_ohc_hycom.py` / `build_ohc_copernicus.py` (measured
D26 fields) · `scaled_d26_ri.py` + `analyze_d26_ri.py` (population D26-vs-RI test) ·
`make_storm_ri_animation.py` (GOES RI video overlays) · `make_presentation.py`
(slide deck).

## Run locally

Double-click `serve.bat`, or from a terminal in this folder:

```
python -m http.server 8000
```

Then open http://localhost:8000/rapidwatch-gulf-ri.html . Serving over localhost
(rather than `file://`) is what lets the page fetch the `data/` files at runtime.

## Data provenance & honesty notes

- **Hurricane tracks are real best-track data.** The 2005 Katrina/Rita pair is from
  NOAA **HURDAT2**; the 2024 Helene/Milton pair is from the official **NHC Tropical
  Cyclone Reports**. RI is detected from the wind data itself (≥30 kt / 24 h on
  synoptic fixes), not hand-placed.
- **Ocean heat (D26) is measured, not schematic** for the four storms: HYCOM GOFS 3.1
  reanalysis (2005) and Copernicus Marine GLORYS (2024).
- **Live buoys & cone are real**, refreshed every 30 min via the GitHub Action.
- **Still illustrative** (labeled in-app): the schematic Loop Current path, the
  representative eddy/glider/saildrone scaffolding, and the analytical SST/shear/
  current climatology layers.
- **Coastline**: Natural Earth 50 m, clipped to the Gulf and simplified.
- The research memo's citations are verified against primary sources; the D26-vs-RI
  finding is reported honestly, including its null result on independent skill.

## Next increments

- More real best tracks (Ida 2021, Michael 2018, Laura 2020, Beryl 2024).
- Pre-storm / ahead-of-track D26 sampling for a cleaner ocean-heat test (report §5.7).
- A real-time altimetry-derived OHC field to replace the schematic Loop Current layer.
- An observing-system-impact (OSSE / data-denial) pass to quantify leverage per tier.

## License

Code and original content are released under the **MIT License** (see
[`LICENSE`](LICENSE)). Third-party datasets remain the property of their providers
(NOAA, Copernicus Marine Service, Natural Earth) and carry their own terms — please
credit the original sources when reusing the data.

---
*Assembled 2026 from NOAA AOML/PMEL/OMAO, NHC, NDBC, NOAA/NRL HYCOM, Copernicus
Marine Service, Saildrone, SOFAR Ocean, and peer-reviewed literature.
RI = +30 kt / 24 h (NHC).*
