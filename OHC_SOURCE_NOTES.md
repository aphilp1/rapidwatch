# OHC / D26 Data Source Notes — 2026-07-05

Findings from the source hunt that revived `build_ohc.py` after the old
NESDIS SOHCS ERDDAP dataset disappeared.

## What died

- Old config: `https://coastwatch.noaa.gov/erddap` / dataset `nesdisVHsohcsDaily`,
  variables `OHC`, `D26`.
- Status 2026-07-05: server UP (`/erddap/index.html` → 200) but the dataset id
  → **HTTP 404**, and full-text searches for `SOHCS` / `ocean heat content` on
  that server return nothing OHC-related. The dataset was removed, not renamed
  in place.

## What is live now (verified by actually pulling data)

**NOAA PolarWatch ERDDAP** hosts the SOHCS North Atlantic grids:

| Dataset ID | Coverage | Grid | Variables |
|---|---|---|---|
| `noaacwOHC14na` | 2024-01-15 → present (rolling) | 0.25°, NA (0–60 N, 100 W–0) | `ohc` (kJ cm⁻²), `iso26C` (m), plus `sst`, `ssha`, `iso20C`, `omld` |
| `noaacwOHCna`   | 2020-04-30 → 2024-01-18        | same | same |

- Base: `https://polarwatch.noaa.gov/erddap`
- Variable renames vs the old dataset: `OHC` → `ohc`, `D26` → `iso26C`.
- Tested request (HTTP 200, 68 KB NetCDF):
  `https://polarwatch.noaa.gov/erddap/griddap/noaacwOHC14na.nc?ohc[(2024-09-25T12:00:00Z):1:(2024-09-25T12:00:00Z)][(15.0):1:(32.0)][(-100.0):1:(-74.0)],iso26C[...]`
- Sanity (Gulf box, 2024-09-25, Helene RI): `ohc` 0–230 kJ cm⁻², mean 106;
  `iso26C` 20–158 m, mean 84 — physically sane for the record-warm 2024 Loop
  Current. Fill value in raw files is −999 (properly masked in netCDF4).
- Cross-check: SOHCS `iso26C` mean 83 m for Milton vs 69 m from the existing
  Copernicus-derived `data/ohc/milton_d26.json` — same ballpark (different
  method, grid, and day within the RI window).

Note: NP/SP basins exist too (`noaacwOHC14np`, `noaacwOHC14sp`, ...) if
RapidWatch ever leaves the Atlantic.

## The 2005 problem — no SOHCS archive reaches Katrina/Rita

The old header claim "SOHCS covers 1993–present" was **wrong**. Checked:

- PolarWatch: earliest 2020-04-30 (`noaacwOHCna`).
- AOML ERDDAP (`https://erddap.aoml.noaa.gov/hdb/erddap`): `UOHC_2012` …
  `UOHC_2026` per-year datasets (variables `Ocean_Heat_Content`, `D26`, `D20`,
  global 0.25°) — earliest **2012**; `UOHC_2005` → 404.
- Upwell ERDDAP: `noaa_aoml_6b09_4e6f_46dd` (OHC/D26/D20 0.25°) — **2016**-present.
- AOML legacy TCHP directory (`aoml.noaa.gov/phod/cyclone/data/`) → 401.
- CoastWatch main + PFEG ERDDAPs: nothing OHC-gridded at all.

**2005 recipe (already validated in this repo):** `build_ohc_hycom.py` —
HYCOM GOFS 3.1 reanalysis `GLBv0.08/expt_53.X` via OPeNDAP (1994–2015),
`water_temp` → D26. Endpoint re-verified alive 2026-07-05
(`.../dodsC/GLBv0.08/expt_53.X/data/2005.dds` → 200). Copernicus GLORYS
(`GLOBAL_MULTIYEAR_PHY_001_030`, 1993→near-present, login required) is the
backup if HYCOM ever dies — same D26 integration as `build_ohc_copernicus.py`.

## Resulting pipeline design

- `build_ohc.py` (raw OHC+D26 NetCDF → `data/ohc_raw/`): PolarWatch SOHCS,
  auto-selects `noaacwOHC14na` / `noaacwOHCna` by RI window; storms before
  2020-04-30 are reported as out-of-coverage (not failures) with a pointer to
  the HYCOM path. `--dataset <id>` still overrides.
- `build_ohc_hycom.py`: 2005 storms (D26 JSON → `data/ohc/`). Unchanged.
- `build_ohc_copernicus.py`: 2024 D26 via CMEMS (login). Unchanged; SOHCS now
  provides a no-login alternative that also carries **OHC**, which the
  model-derived paths never had.

Run 2026-07-05: `helene_ohc.nc` (123 KB) and `milton_ohc.nc` (179 KB) pulled
into `data/ohc_raw/` with sane values; manifest written.
