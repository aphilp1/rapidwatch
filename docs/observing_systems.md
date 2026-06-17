# Gulf RI Observing Systems — Catalog & Optimal Deployment

Reference for the sensors and platforms used to observe hurricane rapid
intensification, organized into four tiers (space / airborne / surface /
subsurface), followed by a ranked argument for what is actually essential.

---

## The four tiers

### SPACE — spaceborne remote sensing (persistent, basin-wide)
- **GOES-19 ABI** — geostationary visible/IR rapid scan (30-60 s mesoscale): eye
  formation, cloud-top cooling, convective bursts.
- **GOES-19 GLM** — total lightning; inner-core bursts often precede wind changes.
- **Microwave imagers/sounders (SSMIS, ATMS, AMSR2, WSF-M, commercial)** — the
  "X-ray" of internal structure through cloud; the **earliest structural RI signal**.
  *Systemic risk: the aging DMSP/SSMIS sensors (~half of all microwave scans) were
  nearly cut off mid-2025 (extended ~Sep 2026) — the biggest single gap in the system.*
- **Scatterometer (ASCAT et al.)** — ocean surface vector winds; storm size & field.
- **Altimetry (Sentinel-6, SWOT, legacy Jason)** — sea-surface height -> maps the Loop
  Current and eddies -> the basis of satellite **OHC**. Essential for the Gulf signal.

### AIRBORNE — crewed reconnaissance
- **NOAA WP-3D Orion (x2)** — the core workhorse: Tail Doppler Radar (3-D wind),
  SFMR (surface wind + rain), AXBT/dropsonde/UAS deployment.
- **NOAA Gulfstream IV** — high-altitude synoptic surveillance; dropsondes for steering
  flow and environmental shear.
- **USAF 53rd WRS WC-130J** — operational center fixes and wind measurements to NHC.

### AIRBORNE — aircraft-deployed expendables & drones
- **GPS dropsondes** — P/T/RH/wind profiles; the DA backbone.
- **Streamsondes** — lightweight swarm sondes for dense wind sampling.
- **Altius-600 UAS** — flies the low, hazardous boundary layer crewed aircraft avoid.
- **AXBT** — air-deployed ocean temperature profiles under the storm.

### SURFACE — air-sea interface (the flux layer)
- **Saildrone Explorer USV** — sails into the eye; measures the heat & momentum fluxes
  that set intensification rate. Exposed shallow-shelf wave physics models barely capture.
- **SOFAR Spotter** — drifting wave buoys; pre-deployed/air-dropped; waves, SST, pressure.
- **Global Drifter Program** — SST, SLP, mixed-layer current; reveals the cold wake.
- **NDBC moored buoys** — fixed continuous reference; calibration anchor.

### SUBSURFACE — the ocean reservoir
- **Underwater gliders** — autonomous T/S profiles to 1,000 m; pre-positioned along the
  Loop Current corridor to measure OHC *before* a storm. Highest-leverage Gulf obs.
- **Argo floats** — global T/S to 2,000 m; background state & pre/post-storm context.
- **ALAMO floats** — air-launched, Argo-class; high-cadence under-storm profiles for >1 yr.

---

## What's actually essential (ranked by leverage per dollar)

RI predictability is limited less by model resolution than by knowing the **initial
state of the upper ocean and the air-sea interface**. An optimal Gulf design:

1. **Persistent subsurface pre-positioning** *(ESSENTIAL)* — gliders + Argo + ALAMO +
   altimetry along the Loop Current / eddy corridor. The Gulf's defining ingredient is
   deep heat, knowable before any storm. Cheap, continuous, most Gulf-specific. Start here.
2. **Continuous spaceborne microwave** *(ESSENTIAL)* — earliest structural warning;
   protect SSMIS continuity and backfill with WSF-M + commercial constellations. The
   2025 near-loss is the most urgent systemic gap.
3. **Air-sea interface flux sampling at the storm** *(ESSENTIAL)* — saildrones +
   air-deployed Spotters/drifters in the forecast path. The least-observed, highest-
   uncertainty term in intensity; the shallow Gulf shelf raises its value further.
4. **Targeted aircraft core + environment sampling** *(HIGH VALUE)* — P-3 TDR/SFMR +
   dropsondes + low-level UAS for inner-core structure and DA; G-IV/WC-130J for steering.
   Deploy by forecast risk, not routine.
5. **Coordination is the force multiplier** *(HIGH VALUE)* — co-located air/surface/
   subsurface sampling of the *same* water column (CHAOS-style) closes the flux budgets.

**One line:** watch the heat reservoir continuously from below (gliders + altimetry),
the structure continuously from above (microwave), and the interface directly when a
storm is in the path (saildrones + drifters) — then coordinate all three on the same
water column. Aircraft sharpen the inner core on top of that foundation.

*Caveat: this ranking is a defensible synthesis of the literature, not a published OSSE
result. The honest next step is data-denial / observing-system-impact evidence to
quantify each tier's leverage on RI skill.*

---
*Sources: NOAA AOML/PMEL/OMAO, Saildrone, SOFAR Ocean, NHC/AOML modeling, and
peer-reviewed literature, June 2026.*
