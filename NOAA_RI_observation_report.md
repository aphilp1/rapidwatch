# Where Gulf Hurricanes Rapidly Intensify — and Where We Must Watch

### A climatological targeting recommendation for rapid-intensification (RI) observations in the Gulf of Mexico

**Prepared by:** RapidWatch (independent analysis)
**Date:** 21 June 2026
**For consideration by:** NOAA National Hurricane Center (NHC); AOML Hurricane Research Division (HRD); NOAA Office of Marine & Aviation Operations / Aircraft Operations Center (OMAO/AOC); NESDIS; U.S. IOOS glider program. *cc: Joint Hurricane Testbed.*
**Data:** NOAA HURDAT2 Atlantic best-track database, 1851–2025 (02-27-2026 release).

---

## 1. Executive summary

Rapid intensification (RI) — a wind increase of **≥30 kt in 24 h** — remains the single hardest hurricane-forecast problem, and the Gulf of Mexico is where it most often turns a routine system into a coastal catastrophe with little warning (Camille 1969, Katrina/Rita 2005, Michael 2018, Ida 2021, Milton 2024).

We are confident about **why** RI happens — warm sea-surface temperature (the fuel), deep warm water / high ocean heat content as measured by the depth of the 26 °C isotherm, "D26" (the amplifier), and low vertical wind shear (the on/off switch). This memo addresses the operational question of **where and when** to put scarce observing assets to catch it.

Using 175 years of NOAA best-track data, we built an **observed RI climatology** for the Gulf. The findings are sharp and actionable:

- **A storm is 3.1× more likely to be undergoing RI onset inside a small "core box" in the southern Gulf (≈20.9–22.9 °N, 91.6–93.9 °W — the Bay of Campeche / southwestern flank of the Loop Current) than the Gulf average** (23.1% vs 7.5% of fixes).
- **RI begins while storms are still weak:** the median intensity at RI onset is **50 kt**, and **66% of RI onsets occur at tropical-storm strength or below.** The storms that blow up are not the ones that already look dangerous.
- **Timing is tightly seasonal:** **September is the peak month and 84% of all RI onsets occur August–October.**
- The hotspot is **co-located with the Gulf's two deepest warm-water features** — the Loop Current intrusion through the Yucatan Channel and the Bay of Campeche warm pool — exactly as the physical mechanism predicts.

**Recommendation:** When a system forms in, or is forecast to enter, the Gulf (including the NW Caribbean approach through the Yucatan Channel), pre-position **ocean-heat-content and inner-core observations over the southern-Gulf RI core box *ahead of the storm*, 12–36 h before projected onset, even when the system is only a tropical storm.** A second, high-stakes watch applies to the **Loop Current corridor and north-central shelf**, where RI *continues* to U.S. landfall. Section 6 specifies the protocol; Section 7 specifies the platforms.

---

## 2. The problem and why it matters

Track forecasts have improved dramatically over three decades; **intensity** forecasts, and RI in particular, have lagged. The limiting factors are well established in the literature and in NOAA's own forecast-improvement plans:

1. **Ocean initialization.** Coupled models (HAFS with its HYCOM/MOM6 ocean component) are highly sensitive to the pre-storm ocean heat field. Where D26 is deep, the storm's own cold wake is suppressed and intensification continues unchecked; where it is shallow, mixing shuts the storm down. Yet the subsurface ocean is sparsely observed precisely where it matters most.
2. **Inner-core observations of *developing* systems.** Reconnaissance is, understandably, tasked toward storms that already threaten land and already look strong. RI, however, **begins in weak systems** (Section 5.3). The pre-RI inner core is therefore systematically under-sampled.

The Gulf concentrates both problems: it is small, semi-enclosed, ringed by dense population, and threaded by the deepest warm water in the basin. A targeting strategy here offers an unusually high return on a fixed observing budget.

---

## 3. Data and method

- **Source:** HURDAT2 (1851–2025), 2,004 Atlantic systems, 6-hourly best-track fixes.
- **Population:** the **326 hurricanes** that both reached hurricane status and entered a Gulf-of-Mexico polygon (Caribbean/Atlantic-only systems excluded by a hand-drawn coastline mask).
- **RI onset detection:** at every fix, we look ~24 h ahead (21–27 h window, nearest fix) and flag an **onset** where wind rises ≥30 kt. The onset is geolocated at the **start** fix — the place and time at which you would want eyes on the ocean *before* the explosion.
- **Exposure normalization:** the Gulf domain (18–31 °N, 80–98 °W) is gridded at 0.25°. For each cell we count both RI onsets and **all** hurricane fixes passing through, so we measure **propensity** (onsets ÷ traffic), not merely where storms happen to travel.
- **Likelihood surface:** a Gaussian kernel-density estimate (bandwidth 0.75°) of onset points, normalized 0–1, yields a smooth RI-likelihood field and the tiered "watch" / "core" boxes.
- **Lift:** the conditional probability *P(RI onset | a hurricane fix is here)* inside each box versus the domain average.

**Limitations (stated plainly).** This is a **climatology — a historical prior, not a dynamical forecast.** Best-track winds carry uncertainty that is larger before the aircraft-reconnaissance era (pre-1944) and before satellites (pre-1966); observing density has grown over time, which can inflate apparent activity in recent decades and along historical shipping lanes. The ≥30 kt/24 h threshold is one common RI definition; results are qualitatively stable under ±5 kt. The onset-location signal also reflects an **intensity-ceiling effect** — weak systems entering from the south have the most "room" to gain 30 kt — which is itself operationally useful (it tells us to watch the southern entry). None of these caveats move the hotspot off the deep-warm-water features.

---

## 4. Headline numbers

| Quantity | Value |
|---|---|
| Gulf hurricanes analyzed (1851–2025) | **326** |
| …that underwent ≥1 RI onset inside the Gulf | **152 (47%)** |
| Total RI-onset intervals detected | **411** |
| Domain-average P(RI onset \| fix) | **7.5%** |
| **Core box** P(RI onset \| fix) — 20.9–22.9 °N, 91.6–93.9 °W | **23.1% → 3.1× lift** |
| **Watch box** P(RI onset \| fix) — 20.1–23.4 °N, 84.4–95.1 °W | **14.6% → 1.95× lift** |
| Peak-density cell | **21.6 °N, 92.9 °W** |
| Onset-weighted centroid | **22.7 °N, 88.6 °W** |
| Peak month / Aug–Oct share | **September / 84%** |
| Median intensity at RI onset | **50 kt** |
| RI onsets beginning at ≤ tropical-storm strength | **66%** |
| RI onsets beginning at ≤ Cat 1 | **87%** |

---

## 5. Findings

### 5.1 Where RI begins — the southern-Gulf core
The RI-onset density peaks over the **southern Gulf**, with the tightest core over the **Bay of Campeche and the southwestern flank of the Loop Current (≈20.9–22.9 °N, 91.6–93.9 °W)** and a broader elevated zone fanning east toward the **Yucatan Channel / Loop Current intrusion (centroid 22.7 °N, 88.6 °W).** Inside the core box, **nearly one in four** hurricane fixes is an RI onset — **3.1× the basin average.** This is a genuine preference, not a traffic artifact: it survives normalization by total storm fixes.

### 5.2 When — September, and the warm-ocean season
RI onset is strongly seasonal: **September is the modal month, and August–October account for 84%** of all onsets. This is when SST is at its annual peak, the Loop Current and its shed warm-core eddies carry the deepest D26, and basin-wide shear is climatologically lowest — the three RI ingredients in simultaneous alignment.

### 5.3 At what intensity — weak systems, not strong ones
The operational sting: **RI begins early.** Median intensity at onset is **50 kt** (a moderate tropical storm); **66% of onsets occur at ≤ tropical-storm strength** and **87% at ≤ Cat 1.** By the time a storm "looks" dangerous, the RI window we most needed to observe has often already opened. Targeting must therefore include **developing** systems, contrary to threat-prioritized tasking.

### 5.4 Why — the hotspot sits on the deep warm water
The geography is not a coincidence. The core and elevated zones overlie the Gulf's two deepest-warm-water features:
- the **Loop Current**, which transports deep, hot Caribbean water through the **Yucatan Channel** and sheds **warm-core eddies** westward; and
- the **Bay of Campeche** warm pool over the Campeche Bank.

These are precisely the regions of high D26 / ocean heat content — the "amplifier." In the warm season the "fuel" (SST) and the "switch" (low shear) are also satisfied, so all three ingredients co-occur over the core box. The record bears this out: the strongest 24-h jumps in the database — **Milton 2024 (+80 kt over the Bay of Campeche), the 1932 Cuba/Texas hurricane, Anita 1977, and the Katrina/Rita 2005 pair over the Loop Current corridor** — all occurred over these features.

### 5.5 Two distinct operational zones
RI onset and RI *impact* are not in the same place:
- **Zone A — Southern-Gulf onset zone (core box, Section 5.1).** Where RI most often *begins*, in weak systems entering from the Caribbean or forming in the Bay of Campeche. **Best place to catch RI early.**
- **Zone B — Loop Current corridor & north-central shelf (≈24–29 °N, 86–94 °W).** Where RI most often *continues to U.S. landfall* (Katrina, Rita, Michael, Ida). **Highest-stakes for warning.** A storm that RI'd in Zone A and tracks north re-intensifies over the warm corridor and shelf.

A complete strategy samples **both**: the ocean ahead in Zone A to catch onset, and the warm corridor ahead of a northbound storm in Zone B to forecast landfall intensity.

---

## 6. Recommendation: the Gulf RI Watch protocol

**Trigger.** Activate when any of the following holds:
- a tropical cyclone (any intensity, including invests with high genesis odds) forms in the Gulf or Bay of Campeche; or
- a system in the NW Caribbean is forecast to transit the Yucatan Channel into the Gulf within 72 h; or
- a Gulf system is forecast to track over the Loop Current corridor / toward the north-central shelf.

**Where.**
- **Primary (Zone A):** the core box **20.9–22.9 °N, 91.6–93.9 °W**, expanded to the elevated watch box **20.1–23.4 °N, 84.4–95.1 °W** to include the Yucatan Channel intrusion.
- **Secondary (Zone B):** the Loop Current corridor and north-central shelf along the storm's forecast track.

**When / lead time.** Concentrate observations **12–36 h ahead of projected RI onset** and **ahead of the storm's track** — i.e., sample the ocean and environment the storm is *about to enter*, not the wake it leaves behind. In the warm season (Aug–Oct), treat any qualifying system as RI-capable by default.

**What to prioritize first** if assets are limited: (1) **pre-storm/ahead-of-storm ocean heat content (D26)** over the core box; (2) **inner-core structure of the developing system** even at TS strength; (3) **environmental shear** sampling around the system.

---

## 7. Observations needed — by platform and gap

The recommendation is deliberately mapped to existing and emerging NOAA/partner assets. The two persistent gaps are **subsurface ocean heat ahead of the storm** and **inner-core sampling of weak systems**; the platforms below are ordered to close them.

### 7.1 Ocean heat content / D26 (close the biggest gap)
- **Airborne ocean profilers from the recon aircraft:** **AXBT** (temperature) and **AXCTD** (temperature + salinity) expendables dropped from the NOAA WP-3D and USAF C-130 on the *outbound* legs, seeded **across the core box ahead of the storm.** This is the most direct way to initialize the coupled model's ocean over the hotspot.
- **Air-deployed profiling floats — ALAMO/APEX** launched from the P-3 to give repeat T/S profiles through the RI window.
- **Underwater gliders (U.S. IOOS "hurricane glider" network):** pre-position a southern-Gulf / Loop Current picket line (Yucatan Channel to the Campeche Bank) for the full Aug–Oct season; gliders uniquely measure the *evolving* subsurface during the event.
- **Satellite altimetry for OHC/D26 fields:** sustain and densify **Sentinel-6 Michael Freilich, Jason-continuity, and SWOT** wide-swath altimetry; OHC derived from sea-surface-height anomaly is the operational backbone for mapping the Loop Current and warm-core eddies. Constellation gaps directly degrade RI guidance.
- **Argo / regional floats:** enhanced seasonal deployment in the Gulf to anchor the altimetry-to-D26 conversion.

### 7.2 Inner core of developing systems (sample weak storms early)
- **NOAA WP-3D Orion** with **Tail Doppler Radar** (3-D wind/structure) and **GPS dropwindsondes** — task **earlier in the life cycle**, at TS strength, for systems over the core box, not only for land-threatening hurricanes.
- **Small uncrewed aircraft launched in-storm** (Altius-600, Coyote) to sample the boundary-layer inflow that fuels RI — the layer crewed aircraft cannot safely reach.
- **Saildrone uncrewed surface vehicles** stationed in the southern-Gulf / Loop Current region for air–sea flux at the surface during the warm season (building on NOAA's 2021–present hurricane Saildrone missions).

### 7.3 Environment and continuity
- **NOAA G-IV synoptic-surveillance** dropsondes around the system to constrain **shear** and steering.
- **Microwave sounders/imagers** (ATMS, AMSR2, GMI, SSMIS) for inner-core structure through cloud — protect against the looming microwave-constellation gap, which is acute for RI detection between fixes.
- **GOES-R rapid-scan / mesoscale sectors** (and future GeoXO) parked on the core box in season.
- **Scatterometer (ASCAT) and SAR (Sentinel-1 / RADARSAT)** for high-resolution surface wind in and around the developing core.
- **Moored buoys:** maintain/return key southern- and central-Gulf NDBC stations for ground-truth SST, wind, and pressure.

---

## 8. Expected benefit
Targeting these observations on the data-identified hotspot, at the right season and lead time, should:
- **improve the ocean initialization** of HAFS and other coupled models exactly where their RI errors are largest;
- **extend RI lead time** by catching onset in weak systems that current tasking tends to miss;
- **raise the value per flight hour and per glider-day** by concentrating finite assets on the 3.1×-lift core rather than spreading them uniformly; and
- provide a **seasonal pre-positioning calendar** (Aug–Oct, peaking September) and a **geographic priority map** that can be built directly into AOC flight planning and IOOS glider deployment.

---

## 9. Caveats
The findings are a historical **prior**, to be combined with — not substituted for — real-time SST/D26 analysis, shear diagnosis, and model guidance. Best-track and observing-density biases (Section 3) argue for treating the *shape* of the hotspot as robust and its exact decade-to-decade magnitude as approximate. The onset-location signal partly reflects where weak storms first meet deep warm water; the highest-impact RI to landfall occurs downstream in Zone B, which the protocol explicitly covers.

---

## 10. One-line summary
**When a storm forms in or heads into the Gulf in August–October, put ocean-heat and inner-core observations over the southern-Gulf core box (≈21–23 °N, 92–94 °W) and the Loop Current corridor *ahead of the storm* — that is where, when, and why hurricanes rapidly intensify, and where better data will most improve the forecast.**

---

*Analysis and figures reproducible from `ri_climatology.py` and `build_gulf_hurricanes.py` (NOAA HURDAT2 1851–2025). Companion interactive map: RapidWatch Gulf Geospatial Canvas — layers "Historical Gulf hurricanes," "Intensification to peak," and "RI climatology hotspot."*
