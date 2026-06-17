# Rapid Intensification — Forecasting Literature (verified)

Curated reading list for Gulf hurricane RI forecasting. Citations were checked
against the record; see the note on a common mis-attribution below.

## Correction worth knowing

A frequent error in AI-generated and secondhand lists is crediting the operational
**SHIPS Rapid Intensification Index (SHIPS-RII)** to Kaplan & DeMaria (2003). That
2003 paper established the *large-scale environmental characteristics* of RI storms
(and a first, simple index); the **operational Revised RII is Kaplan, DeMaria &
Knaff (2010)**. The standard way the lineage is cited is "RII; Kaplan and DeMaria
2003; Kaplan et al. 2010; DeMaria et al. 2021" — three papers, not one. Cite 2010
as the index.

## Statistical / probabilistic (operational backbone)

- **DeMaria & Kaplan (1994)** — the original SHIPS (Statistical Hurricane Intensity
  Prediction Scheme). Root of the operational lineage.
- **Kaplan & DeMaria (2003)**, *Wea. Forecasting* 18(6), 1093-1108 — large-scale RI
  characteristics: warm SST, high low-level humidity, weak vertical shear.
- **Kaplan, DeMaria & Knaff (2010)**, *Wea. Forecasting* 25(1), 220-241 — the
  operational **Revised RII**. This is "SHIPS-RII."
- **Kaplan et al. (2015)**, *Wea. Forecasting* (WAF-D-15-0032.1) — "Evaluating
  Environmental Impacts on TC RI Predictability Utilizing Statistical Models." The
  standard multi-predictor, multi-basin environmental reference.
- **DeMaria, Franklin, Onderlinde & Kaplan (2021)**, *Atmosphere* 12(6), 683 —
  operational RI guidance at NHC; introduces DTOPS and reviews skill/evolution.

## Dynamical / numerical

- **HWRF scientific documentation (Biswas et al.)** — the legacy coupled
  hurricane model.
- **HAFS model-description papers (Hazelton et al.; Dong et al.)** — NOAA's current
  FV3 flagship: storm-following moving nest, ocean coupling, multi-scale DA. *Pull
  exact citations from AOML directly — these are recent and easy to mis-date.*

## Machine learning / AI

- **Yang, Lee & Tippett (2020)** — LSTM for global RI; the recurrent-network baseline.
- **Griffin, Wimmers & Velden (2022)**, *Wea. Forecasting* — satellite-IR + SHIPS
  predictors for RI in the Atlantic/East Pacific. **Your-basin relevant.**
- **IOPscience (2025)** — sea-surface-salinity + calibrated ML for RI; relevant to the
  Gulf's river-plume / low-salinity RI mechanism.
- **Wang & Yang et al. (2025)**, *PNAS* — "Advancing forecasting capabilities: A
  contrastive learning model for forecasting TC rapid intensification." *Caveat:
  tested in the Northwest Pacific (not Atlantic/Gulf) with a 13 m/s (~25 kt)
  threshold — its POD/FARate numbers don't transfer directly to your basin.*

## Climate trend / attribution

- **Bhatia et al. (2019)**, *Nat. Commun.* 10, 635 — original detection of rising TC
  intensification rates.
- **Bhatia et al. (2022)**, *Nat. Commun.* 13, 6626 — "A potential explanation for the
  global increase in TC rapid intensification." Detection/attribution; thermodynamic
  environments have become more favorable, with a human-caused contribution.

## Ocean / Gulf-specific — the through-line for this project

*Absent from most generic RI lists, and central here: OHC and the Loop Current are
where the Gulf-specific RI signal lives.*

- **Shay, Goni & Black (2000)**, *Mon. Wea. Rev.* — Hurricane Opal over a Loop
  Current warm eddy. The foundational ocean-heat-content / RI paper — and a Gulf case.
- **Lin et al. (2005)** — Supertyphoon Maemi over a warm eddy; the eddy-RI mechanism
  generalized.
- **Mainelli et al. (2008)** — operational use of satellite-derived OHC in intensity
  forecasting.

---
*Verified June 2026. Where a citation is flagged "pull exact cite," confirm
author/volume/DOI from the primary source before publishing.*
