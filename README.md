# RAPIDWATCH — Gulf Rapid Intensification Observatory

A working reference for the sensors, platforms, and science used to observe and
forecast **hurricane rapid intensification (RI)** — a maximum-wind increase of
**30 kt (35 mph) in 24 hours** (NHC threshold) — across the Gulf of Mexico
(Gulf of America). Sibling project to Stormwatch; same build philosophy
(hindcast known events to learn where each model layer fails).

## The thesis

Track forecasting has improved for decades; intensity — and the *timing* of RI —
remains the hard problem, and the Gulf concentrates every ingredient that drives it.
The Gulf-specific signal is **deep ocean heat**: the Loop Current and the warm-core
eddies it sheds carry a warm layer 80–150 m deep, so a storm's self-induced cold
wake doesn't cut off its fuel. Knowing that heat reservoir *before* a storm forms is
the highest-leverage, most Gulf-specific observation — which is why the observing
priorities and the modeling priorities point at the same place: the upper-ocean
heat field and the air–sea interface.

## Directory layout

```
RapidWatch/
├── README.md                     this file
├── serve.bat                     double-click: serves the folder at http://localhost:8000
├── rapidwatch-gulf-ri.html       observing-stack reference (4 tiers, "what's essential")
├── rapidwatch-gulf-map.html      geospatial canvas — Gulf basemap + real best tracks
├── docs/
│   ├── observing_systems.md      four-tier sensor catalog + ranked optimal deployment
│   └── RI_literature.md          curated, verified reading list (corrected citations)
└── data/
    ├── storms.geojson            real best tracks: Katrina/Rita 2005, Helene/Milton 2024
    └── gulf_land.geojson         Natural Earth 50 m land, clipped to the Gulf window
```

## The two interfaces

**rapidwatch-gulf-ri.html** — the observing-systems reference. An interactive vertical
"stack" from geostationary orbit (35,786 km) down to a 2,000 m float, with every
platform tappable. The air–sea interface is highlighted as the flux bottleneck — the
least-sampled, highest-uncertainty term in RI. Sections: the Gulf RI problem; the
four-tier platform catalog (space / airborne / surface / subsurface); a ranked
"what's essential" deployment argument; forecasting methods & models; sources.

**rapidwatch-gulf-map.html** — the geospatial canvas. A coordinate-accurate Leaflet
map of the Gulf with toggleable layers: the Loop Current & OHC corridor, a
representative warm-core eddy, NDBC buoys, a glider line, a saildrone zone,
Hurricane Hunter bases, a graticule, and **real hurricane best tracks** colored by
Saffir–Simpson category with the rapid-intensification stretch ringed in amber.
Built fully self-contained (Leaflet + coastline inlined) so it renders offline.

## Local server

Double-click `serve.bat`, or from a terminal in this folder:

```
python -m http.server 8000
```

Then open http://localhost:8000/rapidwatch-gulf-map.html . Serving over localhost
(rather than file://) is what lets the map fetch the data/ GeoJSON files at runtime.

## Data provenance & honesty notes

- **Hurricane tracks are real best-track data.** The 2005 Katrina/Rita pair is from
  NOAA **HURDAT2**; the 2024 Helene/Milton pair is from the official **NHC Tropical
  Cyclone Reports** (2025-released best tracks). RI is detected from the wind data
  itself (>=30 kt / 24 h on synoptic fixes), not hand-placed.
- **Still schematic** (clearly labeled in-app): the Loop Current path, the eddy, and
  the glider line are illustrative scaffolding. NDBC buoy positions are
  representative, to be replaced with live station metadata.
- **Coastline**: Natural Earth 50 m, clipped to the Gulf and simplified.

## Next increments

- More real tracks from their NHC TCRs: **Ida (2021), Michael (2018), Laura (2020),
  Beryl (2024)**.
- Replace the schematic Loop Current / OHC corridor with a **real OHC / sea-surface-
  height field** (altimetry-derived).
- Pull **live NDBC station positions** to replace the representative buoy set.
- An observing-system-impact pass (OSSE / data-denial evidence) to replace the
  ranked "what's essential" argument with quantified leverage per tier.

---
*Assembled June 2026 from NOAA AOML/PMEL/OMAO, Saildrone, SOFAR Ocean, NHC, and
peer-reviewed literature. RI = +30 kt / 24 h (NHC).*
