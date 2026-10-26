# Olana (CP032026) — rapid-intensification record

Generated 2026-10-26 13:26Z from the archive in this folder by ri_event_record.py. Definition used: NHC rapid intensification = maximum sustained wind increase of at least 30 kt in 24 h (best track, 6-hourly). All numbers are read from archived sources; nothing is estimated.

## 1. The event by the definition

- RI window: no 24-h gain of 30 kt or more in the best track yet.

## 2. Measurements at the key moments

| Moment | Time | Vmax | MSLP | SST (SHIPS) | OHC kJ/cm² | HYCOM SST | HYCOM D26 | Shear kt / dir | 700–500 RH | POT kt | D200 | NHC SHIPS-RII 30/24 | DTOPS 30/24 | Our RII 30/24 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

SST, OHC, shear, RH, POT (MPI minus Vmax) and D200 (200 mb divergence, 1e-7 s⁻¹) are the 0-h values in NHC's operational SHIPS file for that cycle. HYCOM values are this site's 1/12° model snapshot nearest the fix time, sampled at the fix. Our RII is the gulf-ri-model rebuild of SHIPS-RII (logistic, six predictors) applied to the same 0-h values.

## 3. Factor table across the event (every best-track fix)

| Time | Vmax | Δ24 prev | SST | OHC | HYCOM D26 | Shear | RH | POT | D200 | Speed kt | IR cold % | NHC RII 30/24 | DTOPS | Our RII |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-10 18Z | 15 | – | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-08-11 00Z | 15 | – | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-08-11 06Z | 15 | – | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-08-11 12Z | 25 | – | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-08-11 18Z | 30 | 15 | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-08-12 00Z | 30 | 15 | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-08-12 06Z | 35 | 20 | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-08-12 12Z | 40 | 15 | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-08-12 18Z | 40 | 10 | 25.2 | 0 | 40 | 19 | 56 | 69 | -2 | 16 | 15 | 0.0% | 0.0% | 1.9% |
| 2026-08-13 00Z | 35 | 5 | 24.7 | 0 | 40 | 24 | 60 | 69 | -16 | 13 | 9 | 0.0% | 0.0% | 0.6% |
| 2026-08-13 06Z | 30 | -5 | 23.7 | 0 | 40 | 26 | 60 | 67 | -27 | 13 | 0 | 0.0% | 0.0% | 0.3% |
| 2026-08-13 12Z | 25 | -15 | 23.8 | 0 | 40 | 21 | 59 | 73 | -14 | 14 | 0 | 0.0% | 0.0% | 0.5% |
## 6. Sources in this folder

- `atcf/` working best track (b-deck) and model guidance (a-deck) from ftp.nhc.noaa.gov
- `ships/` operational SHIPS diagnostic files (predictors, SHIPS-RII, DTOPS)
- `advisories/` every public/forecast advisory, discussion and wind-probability product
- `gis/` cone, track, points and watches per advisory
- `recon/` HDOB high-density observations and vortex data messages
- `environment.csv` HYCOM/Argo/glider readings under the center at each archive run
