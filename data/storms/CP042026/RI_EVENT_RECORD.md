# Pena (CP042026) — rapid-intensification record

Generated 2026-11-06 21:39Z from the archive in this folder by ri_event_record.py. Definition used: NHC rapid intensification = maximum sustained wind increase of at least 30 kt in 24 h (best track, 6-hourly). All numbers are read from archived sources; nothing is estimated.

## 1. The event by the definition

- RI window: no 24-h gain of 30 kt or more in the best track yet.

## 2. Measurements at the key moments

| Moment | Time | Vmax | MSLP | SST (SHIPS) | OHC kJ/cm² | HYCOM SST | HYCOM D26 | Shear kt / dir | 700–500 RH | POT kt | D200 | NHC SHIPS-RII 30/24 | DTOPS 30/24 | Our RII 30/24 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

SST, OHC, shear, RH, POT (MPI minus Vmax) and D200 (200 mb divergence, 1e-7 s⁻¹) are the 0-h values in NHC's operational SHIPS file for that cycle. HYCOM values are this site's 1/12° model snapshot nearest the fix time, sampled at the fix. Our RII is the gulf-ri-model rebuild of SHIPS-RII (logistic, six predictors) applied to the same 0-h values.

## 3. Factor table across the event (every best-track fix)

| Time | Vmax | Δ24 prev | SST | OHC | HYCOM D26 | Shear | RH | POT | D200 | Speed kt | IR cold % | NHC RII 30/24 | DTOPS | Our RII |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-02 12Z | 20 | – | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-02 18Z | 20 | – | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-03 00Z | 20 | – | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-03 06Z | 25 | – | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-03 12Z | 25 | 5 | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-03 18Z | 30 | 10 | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-04 00Z | 30 | 10 | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-04 06Z | 30 | 5 | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-04 12Z | 25 | 0 | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-04 18Z | 25 | -5 | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-05 00Z | 25 | -5 | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-05 06Z | 30 | 0 | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-05 12Z | 30 | 5 | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-05 18Z | 30 | 5 | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-06 00Z | 30 | 5 | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-06 06Z | 30 | 0 | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-06 12Z | 30 | 0 | – | – | – | – | – | – | – | – | – | – | – | – |
| 2026-11-06 18Z | 40 | 10 | – | – | – | – | – | – | – | – | – | – | – | – |

## 5. NHC's own intensity reasoning, by discussion (verbatim excerpts)

**Discussion 001** (1100 AM HST Fri Nov 06 2026)
> Tropical Storm Pena Discussion Number 1 NWS Central Pacific Hurricane Center Honolulu HI CP042026 Issued by NWS National Hurricane Center Miami FL 1100 AM HST Fri Nov 06 2026
> The intensity forecast is tricky because the overall environment generally seems conducive to strengthening for at least the next day or so. While there is an increase in shear in much of the models this weekend, this shear could abate early next week, with no obvious dry air or instability issues seen in the large-scale guidance. It is a little puzzling why many of the models show little change or even a weakening so quickly in seemingly conducive conditions, though perhaps it is linked to the unrealistically weak initial vortex representation of Pena. The first forecast is on the higher side of the guidance and reflects a blend of some aids that get close to hurricane-strength, while others weaken to a depression. It probably goes without saying that this too is an uncertain prediction, similar to the track forecast.

## 6. Sources in this folder

- `atcf/` working best track (b-deck) and model guidance (a-deck) from ftp.nhc.noaa.gov
- `ships/` operational SHIPS diagnostic files (predictors, SHIPS-RII, DTOPS)
- `advisories/` every public/forecast advisory, discussion and wind-probability product
- `gis/` cone, track, points and watches per advisory
- `recon/` HDOB high-density observations and vortex data messages
- `environment.csv` HYCOM/Argo/glider readings under the center at each archive run
