# Josephine (AL102026) — rapid-intensification record

Generated 2026-10-22 06:16Z from the archive in this folder by ri_event_record.py. Definition used: NHC rapid intensification = maximum sustained wind increase of at least 30 kt in 24 h (best track, 6-hourly). All numbers are read from archived sources; nothing is estimated.

## 1. The event by the definition

- RI window: no 24-h gain of 30 kt or more in the best track yet.

## 2. Measurements at the key moments

| Moment | Time | Vmax | MSLP | SST (SHIPS) | OHC kJ/cm² | HYCOM SST | HYCOM D26 | Shear kt / dir | 700–500 RH | POT kt | D200 | NHC SHIPS-RII 30/24 | DTOPS 30/24 | Our RII 30/24 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

SST, OHC, shear, RH, POT (MPI minus Vmax) and D200 (200 mb divergence, 1e-7 s⁻¹) are the 0-h values in NHC's operational SHIPS file for that cycle. HYCOM values are this site's 1/12° model snapshot nearest the fix time, sampled at the fix. Our RII is the gulf-ri-model rebuild of SHIPS-RII (logistic, six predictors) applied to the same 0-h values.

## 3. Factor table across the event (every best-track fix)

| Time | Vmax | Δ24 prev | SST | OHC | HYCOM D26 | Shear | RH | POT | D200 | Speed kt | IR cold % | NHC RII 30/24 | DTOPS | Our RII |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-18 18Z | 40 | – | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-10-19 00Z | 40 | – | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-10-19 06Z | 45 | – | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-10-19 12Z | 45 | – | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-10-19 18Z | 45 | 5 | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-10-20 00Z | 45 | 5 | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-10-20 06Z | 45 | 0 | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-10-20 12Z | 45 | 0 | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-10-20 18Z | 45 | 0 | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-10-21 00Z | 45 | 0 | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-10-21 06Z | 45 | 0 | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-10-21 12Z | 50 | 5 | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-10-21 18Z | 55 | 10 | – | – | 40 | – | – | – | – | – | – | – | – | – |
| 2026-10-22 00Z | 55 | 10 | 25.1 | 0 | 40 | 31 | 34 | 49 | 66 | 6 | 30 | 0.0% | 2.0% | 0.5% |

## 5. NHC's own intensity reasoning, by discussion (verbatim excerpts)

**Discussion 001** (500 PM AST Wed Oct 21 2026)
> The subtropical storm will likely intensify during the next day or so through a favorable trough interaction while it remains near the north wall of the Gulf Stream. Global models are in good agreement on a band of hurricane-force winds developing tomorrow on the back side of the low as it undergoes extratropical transition. A slow weakening is anticipated by late Friday with the loss of forcing from the trough while the system moves over cold water. The NHC intensity forecast is similar to a blend of the GFS/ECMWF global model solutions. The cyclone should become absorbed in about 4 days within a much larger low over the North Atlantic.

**Discussion 002** (1100 PM AST Wed Oct 21 2026)
> Josephine is unlikely to remain subtropical for long since the storm will encounter much cooler waters and stronger shear over the next 12-24 hours. However, the global models favor some near-term strengthening driven mostly by baroclinic processes and positive interaction with the approaching trough. This forecast shows Josephine becoming a hurricane-force, extratropical cyclone in 24 h, though it could lose subtropical characteristics even sooner. Gradual weakening is predicted beginning on Friday, and the updated forecast shows Josephine becoming absorbed by 96 h within a larger, extratropical low over the North Atlantic. Given the subtropical nature of this storm, the NHC intensity forecast continues to favor a blend of the GFS and ECMWF models.

## 6. Sources in this folder

- `atcf/` working best track (b-deck) and model guidance (a-deck) from ftp.nhc.noaa.gov
- `ships/` operational SHIPS diagnostic files (predictors, SHIPS-RII, DTOPS)
- `advisories/` every public/forecast advisory, discussion and wind-probability product
- `gis/` cone, track, points and watches per advisory
- `recon/` HDOB high-density observations and vortex data messages
- `environment.csv` HYCOM/Argo/glider readings under the center at each archive run
