# RapidWatch — Geospatial Data Source & Metadata Document

**Project:** RapidWatch — Gulf of Mexico rapid-intensification observatory
**Live site:** https://aphilp1.github.io/rapidwatch/
**This document:** complete provenance for every geospatial layer, dataset, and live
feed in the project — what it is, who produced it, where it comes from, how it is
fetched, its resolution / extent / coverage, the local file it lands in, the script
that builds it, and its license. Maintained by hand; update when a source changes.

**Coordinate reference system (everything):** WGS84 geographic, lon/lat decimal degrees
(`urn:ogc:def:crs:OGC:1.3:CRS84` / EPSG:4326). No projected CRS is used; the web map
applies a simple equirectangular canvas projection for rendering.

**Standard analysis box (Gulf of Mexico):** lat 15.0 → 32.0 °N, lon −100.0 → −74.0 °E
(used for all ocean-heat subsets). Hurricane selection uses a hand-drawn Gulf polygon
(see `build_gulf_hurricanes.py › GULF_POLY`) that includes the Bay of Campeche.

**"Measured" vs "illustrative":** Layers are explicitly tagged below. Best tracks, D26,
GOES IR, live buoys, and the NHC cone are **real observational/reanalysis data**. The
Loop Current path, eddy/glider/saildrone scaffolding, and analytical SST/shear/current
climatology are **schematic** (labeled as such in-app) and are NOT in this provenance
table because they are illustrative, not sourced.

---

## 1. Master quick-reference table

| # | Layer / product | Provider | Type | Local file(s) | Built by | Refresh |
|---|-----------------|----------|------|---------------|----------|---------|
| 1 | RI best tracks (4 storms) | NOAA HURDAT2 + NHC TCRs | Measured | `data/storms.geojson` | hand-assembled | static |
| 2 | Historical Gulf hurricanes (326) | NOAA HURDAT2 | Measured | `data/gulf_hurricanes.geojson` · `.json` | `build_gulf_hurricanes.py` | static (annual HURDAT2 release) |
| 3 | Intensification run-ups (311) | NOAA HURDAT2 (derived) | Derived | `data/gulf_intensification.geojson` | `build_gulf_hurricanes.py` | static |
| 4 | RI climatology hotspot grid | NOAA HURDAT2 (derived) | Derived | `data/ri_climatology.json` | `ri_climatology.py` | static |
| 5 | Ocean heat D26 — 2005 storms | NOAA/NRL HYCOM GOFS 3.1 | Measured (reanalysis) | `data/ohc/katrina_d26.json` · `rita_d26.json` | `build_ohc_hycom.py` | static |
| 6 | Ocean heat D26 — 2024 storms | Copernicus Marine (GLORYS/analysis) | Measured (analysis) | `data/ohc/helene_d26.json` · `milton_d26.json` | `build_ohc_copernicus.py` | static |
| 7 | Scaled D26-vs-RI study | Copernicus Marine | Derived | `data/ohc/ri_d26_samples.csv` · `ri_d26_ahead_1p0.csv` | `scaled_d26_ri.py` · `scaled_d26_ri_ahead.py` | static |
| 8 | GOES IR animation — 2024 | NOAA GOES-16 (ABI) via AWS | Measured | `data/overlays/{helene,milton}_ir.{mp4,webm}` | `make_storm_ri_animation.py` | static |
| 9 | GOES IR animation — 2005 | NOAA GridSat-GOES (GOES-12) via NCEI | Measured | `data/overlays/{katrina,rita}_ir.{mp4,webm}` | `make_storm_ri_animation.py` | static |
| 10 | Live buoy observations | NOAA NDBC | Measured (live) | `data/ndbc/*.txt` | `build_live_data.py` | every 30 min |
| 11 | Live NHC active storms + cone | NOAA NHC | Measured (live) | `data/nhc_currentstorms.json` · `data/nhc/*.geojson` | `build_live_data.py` | every 30 min |
| 12 | Coastline / admin basemap | Natural Earth | Reference | `data/geo/ne_50m_*.geojson` | static download | static |

---

## 2. Detailed source entries

### 1 — Rapid-intensification best tracks (the 4 headline storms)
- **What:** Synoptic best-track fixes (position, max wind, MSLP, category, RI flag,
  landfall flag) for Katrina (2005), Rita (2005), Helene (2024), Milton (2024).
  123 point/line features.
- **Provider / source:** NOAA HURDAT2 for the 2005 pair; official **NHC Tropical
  Cyclone Reports** for the 2024 pair. (Recorded in the file's own `metadata.source`.)
- **RI definition:** +30 kt sustained-wind increase within 24 h on synoptic fixes
  (NHC operational threshold); detected from the wind series, not hand-placed.
- **Local file:** `data/storms.geojson` · **CRS:** WGS84 · **Cadence:** static.

### 2 — Historical Gulf hurricane track library (326 storms, 1851–2025)
- **What:** Full LineString track + lifetime-peak and in-Gulf-peak wind/category/
  pressure for every Atlantic hurricane that reached HU status **and** entered the
  Gulf-of-Mexico polygon. 12 reached Cat 5 in-Gulf.
- **Provider / source:** **NOAA HURDAT2** Atlantic best-track database, 1851–present.
  - Download (once): `https://www.nhc.noaa.gov/data/hurdat/` → file
    `hurdat2-1851-2025-02272026.txt` (the 27 Feb 2026 release, 2004 systems).
  - Stored locally as `data/hurdat2-atlantic.txt` (7.1 MB).
- **Local files:** `data/gulf_hurricanes.geojson` (tracks) · `data/gulf_hurricanes.json`
  (summary) · **Built by:** `build_gulf_hurricanes.py`.
- **License:** U.S. Government work, public domain. Cite NOAA/NHC; Landsea & Franklin (2013).

### 3 — Intensification "run-up" segments (311)
- **What:** The contiguous strengthening stretch culminating at each storm's lifetime
  max wind; flagged rapid (≥30 kt/24 h) vs gradual. 190/311 (~61%) qualified as RI.
- **Source:** derived from HURDAT2 (#2) by `build_gulf_hurricanes.py`.
- **Local file:** `data/gulf_intensification.geojson`.

### 4 — RI climatology hotspot grid
- **What:** Gridded conditional RI-onset propensity over the Gulf — Gaussian KDE of
  RI-onset start points, exposure-normalized by track traffic. 0.25° grid, 0.75° KDE
  bandwidth. Yields the core box (Bay of Campeche / SW Loop Current, ~3.1× domain avg)
  and a watch box. 3744 cells.
- **Source:** derived from HURDAT2 (#2) by `ri_climatology.py`.
- **Local file:** `data/ri_climatology.json`.
- **Caveat:** Pre-1944 / pre-satellite undercount and growing observing density bias
  early-era counts — documented in the research memo.

### 5 — Ocean heat content / D26 — 2005 storms (Katrina, Rita)
- **What:** D26 = depth of the 26 °C isotherm (m), computed at every grid point from
  3-D ocean temperature profiles over the Gulf box for the storm's RI date.
- **Provider / source:** **NOAA/NRL HYCOM GOFS 3.1 reanalysis** (1994–2015).
  - Dataset: `GLBv0.08/expt_53.X`, variable `water_temp`.
  - Access: OPeNDAP via HYCOM THREDDS —
    `https://tds.hycom.org/thredds/dodsC/GLBv0.08/expt_53.X/data/{year}`.
  - Note: GLBv0.08 longitude is 0–360 (auto-detected/converted to −180…180).
- **Extent / resolution:** Gulf box (15–32 °N, 100–74 °W), native 0.08° grid (~214×327),
  40 depth levels, time step nearest the RI-window midpoint.
- **Local files:** `data/ohc/katrina_d26.json` · `data/ohc/rita_d26.json` (+ `manifest.json`).
- **Built by:** `build_ohc_hycom.py`. **License:** public (NRL/NOAA); cite HYCOM/GOFS 3.1.

### 6 — Ocean heat content / D26 — 2024 storms (Helene, Milton)
- **What:** Same D26 product for the 2024 pair (HYCOM reanalysis does not extend past
  Sep 2024, so a 2024-capable source was required).
- **Provider / source:** **Copernicus Marine Service** —
  `GLOBAL_ANALYSISFORECAST_PHY_001_024`.
  - Dataset id: `cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m` (daily-mean potential
    temperature `thetao`), product version 202406.
  - Access: `copernicusmarine` Python API (`cm.login()` / `cm.subset()`); requires a
    free Copernicus Marine account. **Credentials live in `~/.copernicusmarine/` and are
    never committed to the repo.**
- **Extent / resolution:** Gulf box (15–32 °N, 100–74 °W), 0.083° grid, depths 0–300 m,
  storm's RI date.
- **Local files:** `data/ohc/helene_d26.json` · `data/ohc/milton_d26.json`.
- **Built by:** `build_ohc_copernicus.py`. **License:** Copernicus Marine Service terms —
  free reuse with attribution ("Generated using E.U. Copernicus Marine Service Information").

### 7 — Scaled D26-vs-RI statistical study
- **What:** D26 sampled at best-track fixes for 76 Gulf hurricanes (698 fixes, 89 RI-onset)
  to test D26 as an RI predictor; plus the **ahead-of-track** refinement that samples
  ~1° along each storm's heading (un-waked ocean) instead of at the cold-wake center.
- **Provider / source:** Copernicus Marine GLORYS reanalysis
  `cmems_mod_glo_phy_my_0.083deg_P1D-m` (fixes ≤ 2021) chained with the analysis dataset
  `cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m` (≥ 2022). Cached NetCDF in
  `data/ohc/raw/` (gitignored).
- **Local files (headline CSVs):** `data/ohc/ri_d26_samples.csv` (center sample) ·
  `data/ohc/ri_d26_ahead_1p0.csv` (1° ahead). Sweep CSVs are regenerable via
  `python scaled_d26_ri_ahead.py --sweep`.
- **Built by:** `scaled_d26_ri.py`, `scaled_d26_ri_ahead.py`, `analyze_d26_ri.py`.
- **Headline result (honest):** at center, D26 adds ~0 independent skill (AUC 0.55, p≈0.07);
  ahead-of-track, AUC rises to 0.64 (p≈1.3e-5) with +0.01–0.02 CV-AUC independent skill —
  i.e. cold-wake sampling masked the signal. Reported with its caveats in the memo §5.7.

### 8 — GOES infrared animation — 2024 storms (Helene, Milton)
- **What:** Reconstructed RI animation from satellite clean-IR brightness temperature.
- **Provider / source:** **NOAA GOES-16 (GOES-East) ABI**, Level-2 Cloud & Moisture
  Imagery, product `ABI-L2-CMIPC` (CONUS), **Band 13** (clean longwave IR, ~10.3 µm).
  - Access: **AWS Open Data** S3 bucket `noaa-goes16`, anonymous/unsigned reads (boto3
    UNSIGNED). Cached to `data/goes_cache/`.
- **Cadence (native):** ~10 min (CONUS). **Local files:** `data/overlays/{helene,milton}_ir.mp4`
  + `.webm` (+ frame dirs `data/{helene,milton}_frames/`, `*_overlay_frames/`).
- **Built by:** `make_storm_ri_animation.py <storm>`. **License:** public domain (NOAA);
  AWS NOAA Open Data Program.

### 9 — GOES infrared animation — 2005 storms (Katrina, Rita)
- **What:** Same animation for the GOES-12 era (pre-ABI), so a different archive is used.
- **Provider / source:** **NOAA NCEI GridSat-GOES** (gridded geostationary IR), satellite
  `goes12`, variable `ch4` (IR window ~10.7 µm).
  - Access: anonymous HTTPS —
    `https://www.ncei.noaa.gov/data/gridsat-goes/access/goes/{YYYY}/{MM}/GridSat-GOES.goes12.{YYYY}.{MM}.{DD}.{HH}00.v01.nc`
  - **Cadence (native):** hourly (regular lat/lon grid).
- **Local files:** `data/overlays/{katrina,rita}_ir.mp4` + `.webm`.
- **Built by:** `make_storm_ri_animation.py <storm>`. **License:** public domain (NOAA NCEI).

### 10 — Live buoy observations (NDBC)
- **What:** Real-time marine observations (wind, gust, wave height/period, pressure, air
  & sea temperature, dewpoint, etc.) from Gulf moored buoys.
- **Provider / source:** **NOAA National Data Buoy Center (NDBC)**, realtime2 feed —
  `https://www.ndbc.noaa.gov/data/realtime2/{station}.txt`.
- **Stations (Gulf of Mexico moored buoys):** `42001, 42002, 42036, 42039, 42040, 42055`
  (station coordinates & names are on each NDBC station page;
  `https://www.ndbc.noaa.gov/station_page.php?station={id}`).
- **Local files:** `data/ndbc/{id}.txt` (raw realtime2, parsed by the page as-is).
- **Built by:** `build_live_data.py`. **Refresh:** every 30 min via GitHub Action.
- **Why mirrored:** NDBC has no CORS headers, so the page cannot fetch it directly in a
  browser — the Action mirrors it to a same-origin file.

### 11 — Live NHC active storms & forecast cone
- **What:** Current active tropical cyclones and their 5-day forecast cone / track / points.
- **Provider / source:** **NOAA National Hurricane Center (NHC)** —
  - `https://www.nhc.noaa.gov/CurrentStorms.json` (active-storm index, verbatim).
  - `https://www.nhc.noaa.gov/storm_graphics/api/{stormID}_5day_{pgn,lin,pts}.geojson`
    (cone polygon / track line / points per active storm).
- **Local files:** `data/nhc_currentstorms.json` · `data/nhc/{ID}_5day_{pgn,lin,pts}.geojson`.
- **Built by:** `build_live_data.py`. **Refresh:** every 30 min. (Empty when no active storms.)

### 12 — Coastline & administrative basemap
- **What:** Gulf coastline and admin-0 boundary lines used as the vector basemap (the app
  uses no raster tile service — basemap is drawn from these vectors on canvas).
- **Provider / source:** **Natural Earth** 50 m cultural/physical vectors
  (`ne_50m_admin_0_boundary_lines_land`, `ne_50m_coastline`), clipped to the Gulf and
  simplified. Download: https://www.naturalearthdata.com/.
- **Local files:** `data/geo/ne_50m_admin0.geojson` · `data/geo/ne_50m_coastline.geojson`.
- **License:** **public domain** (Natural Earth). Attribution appreciated, not required.

---

## 3. Live-data pipeline (the only auto-updating part)

- **Driver:** `build_live_data.py` (stdlib `urllib`, User-Agent
  `RapidWatch/1.0 (+https://github.com/aphilp1/rapidwatch)`).
- **Scheduler:** GitHub Action `.github/workflows/live-data.yml`, `cron: */30 * * * *`
  (every 30 min; GitHub may delay/coalesce under load), Python 3.12.
- **Mechanism (git-scraping):** the Action fetches NDBC + NHC, writes the files above,
  and commits them (`data: refresh live buoy/NHC snapshot [skip ci]`) so the GitHub Pages
  site serves them same-origin — **no CORS proxy** (all free proxies are dead/unreliable).
- **Failure mode:** on a fetch error the previous good file is kept (never overwritten with
  a bad/empty payload).

---

## 4. Licenses & required attribution (summary)

| Source | License | Attribution string |
|--------|---------|--------------------|
| NOAA HURDAT2 / NHC TCRs / NDBC / NHC cone / GOES-16 / GridSat-GOES | U.S. Government work, public domain | "NOAA" (cite the specific product) |
| NOAA/NRL HYCOM GOFS 3.1 | Public (NRL/NOAA) | "HYCOM GOFS 3.1 reanalysis (NRL/NOAA)" |
| Copernicus Marine (GLORYS / analysis) | Free reuse w/ attribution | "Generated using E.U. Copernicus Marine Service Information" |
| Natural Earth | Public domain | "Natural Earth" |
| RapidWatch code & original content | **MIT License** (`LICENSE`) | "© Alex Philp" |

Third-party datasets remain the property of their providers and carry their own terms —
credit the original sources when reusing the data.

---

## 5. Software & libraries (provenance of the tooling)

- **Web map:** Leaflet (https://leafletjs.com) + a custom HTML5 canvas renderer for the
  layered raster/vector stack; all in a single self-contained page (no build step).
- **Python pipeline:** `numpy`, `netCDF4`, `requests`/`urllib`, `copernicusmarine` (v2.4.1),
  `boto3` (UNSIGNED S3), `scikit-learn` (D26-vs-RI study), `matplotlib` (figures),
  plus `ffmpeg` for animation encoding.
- **Build / assembly:** `assemble_rapidwatch.py` (page assembly + checks),
  `make_*` scripts (figures, animations, report/README HTML).

---

## 6. Research memo & citations

The observing-recommendation memo (`NOAA_RI_observation_report.md` / `.html`) cites 20
**verified** peer-reviewed / NOAA primary sources (DOIs confirmed) — e.g. Kaplan & DeMaria
(2003), Shay (2000), Scharroo (2005), Jaimes & Shay (2009), DeMaria (1996), Landsea &
Franklin (2013), Yaukey (2014), Benedetto & Mercer (2020), plus Milton/Michael TCRs.
**Rule of record:** citations are never invented — each is verified against the primary
source before use. The D26-vs-RI finding (including its null result on independent skill)
is reported honestly.

---

*Maintained for RapidWatch. CRS throughout: WGS84 (EPSG:4326). When a source, endpoint,
dataset id, or station list changes, update the corresponding row above and the relevant
`build_*` script — keep this document and the code in sync.*
