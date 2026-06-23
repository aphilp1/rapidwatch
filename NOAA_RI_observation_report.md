# Where Gulf Hurricanes Rapidly Intensify — and Where We Must Watch

### A climatological targeting recommendation for rapid-intensification (RI) observations in the Gulf of Mexico

**Prepared by:** Alex Philp, Ph.D. · RapidWatch (independent analysis)
**Date:** 21 June 2026
**For consideration by:** NOAA National Hurricane Center (NHC); AOML Hurricane Research Division (HRD); NOAA Office of Marine & Aviation Operations / Aircraft Operations Center (OMAO/AOC); NESDIS; U.S. IOOS glider program. *cc: Joint Hurricane Testbed.*
**Primary data:** NOAA HURDAT2 Atlantic best-track database, 1851–2025 (02-27-2026 release) [10]. **Ocean data:** HYCOM GOFS 3.1 reanalysis [11][12] and Copernicus Marine GLORYS reanalysis/analysis (depth of the 26 °C isotherm, D26).

---

## Abstract

Rapid intensification — a large, fast increase in a hurricane's wind speed over a single day — is the most difficult part of hurricane forecasting and among the most dangerous situations for coastal communities, because it can turn a modest storm into a major one with little warning. The Gulf of Mexico is where this occurs most frequently in the United States.

Using the complete NOAA best-track record of Atlantic hurricanes from 1851 to 2025, this analysis maps where and when rapid intensification occurs in the Gulf. Three results stand out. First, it is geographically concentrated: a storm is roughly three times more likely to begin rapidly intensifying in a specific zone of the southern Gulf — the Bay of Campeche and the Loop Current region — than in the Gulf on average. Second, it is strongly seasonal, with most cases in September and the large majority between August and October. Third, it typically begins while a storm is still weak, before it appears threatening.

The analysis also used reconstructed ocean-temperature data to test directly whether the depth of warm water beneath a storm predicts rapid intensification. In individual major storms, intensification did occur over unusually deep warm water, consistent with established physics. Across 76 storms, however, the depth of warm water added little predictive information beyond a storm's location and the time of year — because location and season already indicate where the deep warm water lies.

Together these results support a specific operational conclusion. Observations intended to improve rapid-intensification forecasts should be concentrated in the southern Gulf during late summer, positioned ahead of approaching or developing storms — including weak ones. The principal value of real-time ocean-heat measurements is in initializing the coupled computer models that forecast an individual storm, rather than in serving as a stand-alone climatological warning signal.

---

## 1. Executive summary

Rapid intensification (RI) — conventionally defined as a maximum-sustained-wind increase of **≥30 kt in 24 h**, the ~95th percentile of 24-h over-water intensity change [1] — remains the single hardest hurricane-forecast problem [3], and the Gulf of Mexico is where it most often turns a routine system into a coastal catastrophe with little warning (Camille 1969; Katrina/Rita 2005 [5][6]; Michael 2018 [18]; Ida 2021; Milton 2024 [17]).

We are confident about **why** RI happens — warm sea-surface temperature as the fuel (TCs require SST of roughly ≥26 °C [8][9]), deep warm water / high upper-ocean heat content as the amplifier (it suppresses the storm-induced cold wake that would otherwise cap intensification [4][6]), and low vertical wind shear as the on/off switch [7]. This memo addresses the operational question of **where and when** to put scarce observing assets to catch it.

Using 175 years of NOAA best-track data [10], we built an **observed RI climatology** for the Gulf. The findings are sharp, actionable, and consistent with the peer-reviewed literature [19][20]:

- **A storm is 3.1× more likely to be undergoing RI onset inside a small "core box" in the southern Gulf (≈20.9–22.9 °N, 91.6–93.9 °W — the Bay of Campeche / southwestern flank of the Loop Current) than the Gulf average** (23.1% vs 7.5% of fixes). This aligns with published findings that the Gulf and Caribbean exhibit the basin's highest mean intensification rates [20].
- **RI begins while storms are still weak:** the median intensity at RI onset is **50 kt**, and **66% of RI onsets occur at tropical-storm strength or below.** The storms that blow up are not the ones that already look dangerous — consistent with the climatological RI predictors used operationally [1][2].
- **Timing is tightly seasonal:** **September is the peak month and 84% of all RI onsets occur August–October.**
- The hotspot is **co-located with the Gulf's two deepest warm-water features** — the Loop Current intrusion through the Yucatan Channel and the Bay of Campeche warm pool — exactly as the ocean-heat-content mechanism predicts [4][5][6].
- **A direct test with measured ocean heat (Section 5.7) confirms the mechanism case-by-case but shows that D26 adds no *climatological* skill beyond location and season** — because geography and season already encode it. This validates pre-positioning by location/season and locates the value of real-time ocean observations in dynamical-model initialization, not in standalone climatological prediction.

**Recommendation:** When a system forms in, or is forecast to enter, the Gulf (including the NW Caribbean approach through the Yucatan Channel), pre-position **upper-ocean-heat-content and inner-core observations over the southern-Gulf RI core box *ahead of the storm*, 12–36 h before projected onset, even when the system is only a tropical storm.** A second, high-stakes watch applies to the **Loop Current corridor and north-central shelf**, where RI *continues* to U.S. landfall. Section 6 specifies the protocol; Section 7 specifies the platforms.

---

## 2. The problem and why it matters

Track forecasts have improved dramatically over three decades; **intensity** forecasts, and RI in particular, have lagged, although guidance is now slowly improving [3]. NHC has run a statistical–dynamical Rapid Intensification Index operationally since 2008 [2], but skill remains limited by two well-established factors:

1. **Ocean initialization.** Coupled models — including NOAA's operational Hurricane Analysis and Forecast System (HAFS) and its HYCOM ocean component — are sensitive to the pre-storm upper-ocean heat field, and adding a dynamic ocean measurably changes intensity forecasts [11][12]. Where the 26 °C isotherm (D26) is deep, the storm's own cold wake is suppressed and intensification continues unchecked [4][6]; where it is shallow, mixing shuts the storm down. Yet the subsurface ocean is sparsely observed precisely where it matters most [13].
2. **Inner-core observations of *developing* systems.** Reconnaissance and field campaigns have repeatedly shown the value of inner-core and targeted observations for intensity analysis and forecasting [16]. Tasking, however, is understandably weighted toward storms that already threaten land and already look strong. RI, by contrast, **begins in weak systems** (Section 5.3). The pre-RI inner core is therefore systematically under-sampled.

The Gulf concentrates both problems: it is small, semi-enclosed, ringed by dense population, and threaded by the deepest warm water in the basin [4][5]. A targeting strategy here offers an unusually high return on a fixed observing budget.

---

## 3. Data and method

- **Source:** HURDAT2 (1851–2025), 2,004 Atlantic systems, 6-hourly best-track fixes [10].
- **Population:** the **326 hurricanes** that both reached hurricane status and entered a Gulf-of-Mexico polygon (Caribbean/Atlantic-only systems excluded by a hand-drawn coastline mask).
- **RI onset detection:** at every fix, we look ~24 h ahead (21–27 h window, nearest fix) and flag an **onset** where wind rises ≥30 kt — the standard RI threshold [1]. The onset is geolocated at the **start** fix — the place and time at which you would want eyes on the ocean *before* the explosion.
- **Exposure normalization:** the Gulf domain (18–31 °N, 80–98 °W) is gridded at 0.25°. For each cell we count both RI onsets and **all** hurricane fixes passing through, so we measure **propensity** (onsets ÷ traffic), not merely where storms happen to travel.
- **Likelihood surface:** a Gaussian kernel-density estimate (bandwidth 0.75°) of onset points, normalized 0–1, yields a smooth RI-likelihood field and the tiered "watch" / "core" boxes.
- **Lift:** the conditional probability *P(RI onset | a hurricane fix is here)* inside each box versus the domain average.

**Limitations (stated plainly).** This is a **climatology — a historical prior, not a dynamical forecast.** Best-track winds carry uncertainty that is larger before the aircraft-reconnaissance era (pre-1944) and before satellites (pre-1966) [10]; observing density has grown over time, which can inflate apparent activity in recent decades and along historical shipping lanes. The ≥30 kt/24 h threshold is one common RI definition [1]; results are qualitatively stable under ±5 kt. The onset-location signal also reflects an **intensity-ceiling effect** — weak systems entering from the south have the most "room" to gain 30 kt — which is itself operationally useful (it tells us to watch the southern entry). None of these caveats move the hotspot off the deep-warm-water features.

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
RI onset is strongly seasonal: **September is the modal month, and August–October account for 84%** of all onsets. This is when SST is at its annual peak, the Loop Current and its shed warm-core eddies carry the deepest D26 [4][5], and basin-wide shear is climatologically lowest [7] — the three RI ingredients in simultaneous alignment.

### 5.3 At what intensity — weak systems, not strong ones
The operational sting: **RI begins early.** Median intensity at onset is **50 kt** (a moderate tropical storm); **66% of onsets occur at ≤ tropical-storm strength** and **87% at ≤ Cat 1.** By the time a storm "looks" dangerous, the RI window we most needed to observe has often already opened. Targeting must therefore include **developing** systems — a point reinforced by the operational RI-index literature, which identifies current intensity and persistence among the leading climatological predictors [1][2].

### 5.4 Why — the hotspot sits on the deep warm water
The geography is not a coincidence. The core and elevated zones overlie the Gulf's two deepest-warm-water features:
- the **Loop Current**, which transports deep, hot Caribbean water through the **Yucatan Channel** and sheds **warm-core eddies** westward [4][6]; and
- the **Bay of Campeche** warm pool over the Campeche Bank.

These are precisely the regions of high upper-ocean heat content — the "amplifier." Warm-core features suppress the storm-induced sea-surface cooling that would otherwise limit intensification, a mechanism documented for Hurricane Opal (1995) [4] and for Hurricanes Katrina and Rita (2005), whose intensification tracked the Loop Current's dynamic topography rather than SST alone [5][6]. In the warm season the "fuel" (SST [8][9]) and the "switch" (low shear [7]) are also satisfied, so all three ingredients co-occur over the core box. The record bears this out: the strongest 24-h jumps in the database — **Milton 2024 (+80 kt over the Bay of Campeche) [17]**, the 1932 Cuba/Texas hurricane, Anita 1977, and the Katrina/Rita 2005 pair over the Loop Current corridor [5] — all occurred over these features.

### 5.5 Two distinct operational zones
RI onset and RI *impact* are not in the same place:
- **Zone A — Southern-Gulf onset zone (core box, Section 5.1).** Where RI most often *begins*, in weak systems entering from the Caribbean or forming in the Bay of Campeche. **Best place to catch RI early.**
- **Zone B — Loop Current corridor & north-central shelf (≈24–29 °N, 86–94 °W).** Where RI most often *continues to U.S. landfall* — Katrina, Rita [5][6], Michael (reanalyzed to Category 5 at the Florida Panhandle coast) [18], Ida. **Highest-stakes for warning.** A storm that RI'd in Zone A and tracks north re-intensifies over the warm corridor and shelf.

A complete strategy samples **both**: the ocean ahead in Zone A to catch onset, and the warm corridor ahead of a northbound storm in Zone B to forecast landfall intensity.

### 5.6 Consistency with published climatology
These results are not an outlier of one method. Yaukey (2014) found that the **highest mean tropical-cyclone intensification rates in the North Atlantic occur in the Gulf of Mexico and Caribbean Sea** [20], and Benedetto & Mercer (2020) produced a spatiotemporal climatology of North Atlantic RI from the same HURDAT record and likewise identified the Gulf/western-Caribbean as a preferred RI region [19]. Our contribution is to (a) restrict to Gulf-entering hurricanes, (b) normalize by storm traffic to isolate *propensity*, and (c) translate the result into an explicit, coordinate-bounded observing-target box with a quantified lift.

---

### 5.7 A direct test with measured ocean heat (D26)
Sections 5.1–5.4 infer the ocean-heat link from geography. With the RapidWatch ocean pipeline we now test it directly, reconstructing the measured depth of the 26 °C isotherm (D26) — from HYCOM GOFS 3.1 reanalysis (≤2015) and Copernicus Marine GLORYS (2016–2025) — and co-locating it with the best track.

**Case studies (four marquee storms).** Sampling real D26 at each storm's RI onset, three of four rapidly intensified over distinctly deep warm water: **Katrina 82 m, Rita 67 m, Helene 104 m — 1.2–1.7× the contemporaneous Gulf-median D26.** The exception is instructive: **Milton (2024)**, the most explosive case (+80 kt/24 h), began its RI over the Bay of Campeche where D26 was only ~52 m (below the Gulf median) — its fuel was record SST and near-zero shear, not the deepest ocean heat. Deep warm water *amplifies* RI but is not its sole trigger.

**Population test (76 Gulf hurricanes, 1994–2025; 698 fixes, 89 RI onsets).** Across the full ocean-reanalysis-era sample, D26 only weakly separates RI-onset fixes from non-RI fixes (**median 46 vs 44 m; Mann–Whitney p ≈ 0.07; AUC of D26 alone = 0.55**). RI rate rises monotonically but modestly across D26 terciles (10.0% → 13.6% → 14.7%). Critically, in a cross-validated logistic model **D26 adds essentially no skill beyond latitude, longitude, season, and current intensity** (AUC 0.693 → 0.689).

**Interpretation.** This is *not* evidence that ocean heat is unimportant — it is evidence that, over the Gulf in the warm season, **location and season already encode the ocean-heat climatology**: knowing a storm is in the deep-warm southern Gulf in September conveys nearly the same information a D26 field would. Two consequences follow, both of which *reinforce* this memo's recommendation:
1. **Climatological targeting by geography and season (Sections 5.1–5.2) is the correct basis for pre-positioning** — it already captures the ocean-heat signal without requiring a real-time D26 analysis.
2. **The operational value of real-time ocean-heat observations lies in the dynamical forecast model, not in standalone climatological prediction.** Coupled models (HAFS [11][12]) need accurate D26 to represent the cold-wake feedback and the case-specific conjunction of deep heat with low shear — e.g., Katrina's warm-ring crossing [4] — precisely the anomalies a climatology cannot supply.

**Caveat.** This test uses one ocean snapshot per storm sampled at the storm centre, so the storm's own cold wake and best-track position error add noise that biases the measured association low. A time-matched, **pre-storm (ahead-of-track) D26 sample** is the natural refinement — and is enabled by the same pipeline.

## 6. Recommendation: the Gulf RI Watch protocol

**Trigger.** Activate when any of the following holds:
- a tropical cyclone (any intensity, including invests with high genesis odds) forms in the Gulf or Bay of Campeche; or
- a system in the NW Caribbean is forecast to transit the Yucatan Channel into the Gulf within 72 h; or
- a Gulf system is forecast to track over the Loop Current corridor / toward the north-central shelf.

**Where.**
- **Primary (Zone A):** the core box **20.9–22.9 °N, 91.6–93.9 °W**, expanded to the elevated watch box **20.1–23.4 °N, 84.4–95.1 °W** to include the Yucatan Channel intrusion.
- **Secondary (Zone B):** the Loop Current corridor and north-central shelf along the storm's forecast track.

**When / lead time.** Concentrate observations **12–36 h ahead of projected RI onset** and **ahead of the storm's track** — i.e., sample the ocean and environment the storm is *about to enter*, not the wake it leaves behind. In the warm season (Aug–Oct), treat any qualifying system as RI-capable by default.

**What to prioritize first** if assets are limited: (1) **pre-storm/ahead-of-storm upper-ocean heat content (D26)** over the core box; (2) **inner-core structure of the developing system** even at TS strength; (3) **environmental shear** sampling around the system.

---

## 7. Observations needed — by platform and gap

The recommendation is deliberately mapped to existing and emerging NOAA/partner assets. The two persistent gaps are **subsurface ocean heat ahead of the storm** and **inner-core sampling of weak systems**; the platforms below are ordered to close them.

### 7.1 Ocean heat content / D26 (close the biggest gap)
- **Airborne ocean profilers from the recon aircraft:** **AXBT** (temperature) and **AXCTD** (temperature + salinity) expendables dropped from the NOAA WP-3D and USAF C-130 on the *outbound* legs, seeded **across the core box ahead of the storm.** Real-time airborne ocean-temperature profiling during operational reconnaissance has been demonstrated to characterize the upper-ocean heat available to a storm [15], and is the most direct way to initialize the coupled model's ocean over the hotspot [11][12].
- **Air-deployed profiling floats — ALAMO/APEX** launched from the P-3 for repeat T/S profiles through the RI window.
- **Underwater gliders (U.S. IOOS "hurricane glider" network):** pre-position a southern-Gulf / Loop Current picket line (Yucatan Channel to the Campeche Bank) for the full Aug–Oct season; gliders uniquely measure the *evolving* subsurface during the event [13].
- **Satellite altimetry for OHC/D26 fields:** sustain and densify **Sentinel-6 Michael Freilich, Jason-continuity, and SWOT** wide-swath altimetry; OHC derived from sea-surface-height anomaly is the operational backbone for mapping the Loop Current and warm-core eddies [4][5]. Constellation gaps directly degrade RI guidance.
- **Argo / regional floats:** enhanced seasonal deployment in the Gulf to anchor the altimetry-to-D26 conversion.

### 7.2 Inner core of developing systems (sample weak storms early)
- **NOAA WP-3D Orion** with **Tail Doppler Radar** (3-D wind/structure) and **GPS dropwindsondes** — task **earlier in the life cycle**, at TS strength, for systems over the core box, not only for land-threatening hurricanes; inner-core observation programs have a demonstrated record of improving intensity science and forecasts [16].
- **Small uncrewed aircraft launched in-storm** (e.g., Altius-600, Coyote) to sample the boundary-layer inflow that fuels RI — the layer crewed aircraft cannot safely reach.
- **Saildrone uncrewed surface vehicles** stationed in the southern-Gulf / Loop Current region for air–sea flux at the surface during the warm season, building on NOAA/Saildrone missions that have sampled inside major hurricanes (e.g., SD-1045 in Hurricane Sam, 2021) [14].

### 7.3 Environment and continuity
- **NOAA G-IV synoptic-surveillance** dropsondes around the system to constrain **shear** and steering [7].
- **Passive-microwave sounders/imagers** (ATMS, AMSR2, GMI, SSMIS) for inner-core structure through cloud. *Note: a single canonical peer-reviewed citation for the looming microwave-constellation coverage gap was not available at the time of writing; this is, however, a widely recognized operational concern within NOAA/NESDIS and the TC-analysis community and should be documented with current agency sources before formal submission.*
- **GOES-R rapid-scan / mesoscale sectors** (and future GeoXO) parked on the core box in season.
- **Scatterometer (ASCAT) and SAR (Sentinel-1 / RADARSAT)** for high-resolution surface wind in and around the developing core.
- **Moored buoys:** maintain/return key southern- and central-Gulf NDBC stations for ground-truth SST, wind, and pressure.

---

## 8. Expected benefit
Targeting these observations on the data-identified hotspot, at the right season and lead time, should:
- **improve the ocean initialization** of HAFS and other coupled models exactly where their RI errors are largest [11][12];
- **extend RI lead time** by catching onset in weak systems that current tasking tends to miss [1][2];
- **raise the value per flight hour and per glider-day** by concentrating finite assets on the 3.1×-lift core rather than spreading them uniformly; and
- provide a **seasonal pre-positioning calendar** (Aug–Oct, peaking September) and a **geographic priority map** that can be built directly into AOC flight planning and IOOS glider deployment.

---

## 9. Caveats
The findings are a historical **prior**, to be combined with — not substituted for — real-time SST/D26 analysis, shear diagnosis, and model guidance. Best-track and observing-density biases (Section 3) [10] argue for treating the *shape* of the hotspot as robust and its exact decade-to-decade magnitude as approximate. The onset-location signal partly reflects where weak storms first meet deep warm water; the highest-impact RI to landfall occurs downstream in Zone B, which the protocol explicitly covers.

---

## 10. One-line summary
**When a storm forms in or heads into the Gulf in August–October, put ocean-heat and inner-core observations over the southern-Gulf core box (≈21–23 °N, 92–94 °W) and the Loop Current corridor *ahead of the storm* — that is where, when, and why hurricanes rapidly intensify, and where better data will most improve the forecast.**

---

## References

All references below were verified against publisher pages, DOIs, or official NOAA/NHC sources.

1. Kaplan, J., and M. DeMaria, 2003: Large-scale characteristics of rapidly intensifying tropical cyclones in the North Atlantic basin. *Weather and Forecasting*, **18**(6), 1093–1108. doi:10.1175/1520-0434(2003)018<1093:LCORIT>2.0.CO;2
2. Kaplan, J., M. DeMaria, and J. A. Knaff, 2010: A revised tropical cyclone Rapid Intensification Index for the Atlantic and eastern North Pacific basins. *Weather and Forecasting*, **25**(1), 220–241. doi:10.1175/2009WAF2222280.1
3. DeMaria, M., C. R. Sampson, J. A. Knaff, and K. D. Musgrave, 2014: Is tropical cyclone intensity guidance improving? *Bulletin of the American Meteorological Society*, **95**(3), 387–398. doi:10.1175/BAMS-D-12-00240.1
4. Shay, L. K., G. J. Goni, and P. G. Black, 2000: Effects of a warm oceanic feature on Hurricane Opal. *Monthly Weather Review*, **128**(5), 1366–1383. doi:10.1175/1520-0493(2000)128<1366:EOAWOF>2.0.CO;2
5. Scharroo, R., W. H. F. Smith, and J. L. Lillibridge, 2005: Satellite altimetry and the intensification of Hurricane Katrina. *Eos, Transactions American Geophysical Union*, **86**(40), 366–367. doi:10.1029/2005EO400004
6. Jaimes, B., and L. K. Shay, 2009: Mixed layer cooling in mesoscale oceanic eddies during Hurricanes Katrina and Rita. *Monthly Weather Review*, **137**(12), 4188–4207. doi:10.1175/2009MWR2849.1
7. DeMaria, M., 1996: The effect of vertical shear on tropical cyclone intensity change. *Journal of the Atmospheric Sciences*, **53**(14), 2076–2088. doi:10.1175/1520-0469(1996)053<2076:TEOVSO>2.0.CO;2
8. Palmén, E., 1948: On the formation and structure of tropical hurricanes. *Geophysica*, **3**, 26–38.
9. Gray, W. M., 1968: Global view of the origin of tropical disturbances and storms. *Monthly Weather Review*, **96**(10), 669–700. doi:10.1175/1520-0493(1968)096<0669:GVOTOO>2.0.CO;2
10. Landsea, C. W., and J. L. Franklin, 2013: Atlantic hurricane database uncertainty and presentation of a new database format. *Monthly Weather Review*, **141**(10), 3576–3592. doi:10.1175/MWR-D-12-00254.1
11. Gramer, L. J., J. Steffen, M. Aristizabal Vargas, and H.-S. Kim, 2024: The impact of coupling a dynamic ocean in the Hurricane Analysis and Forecast System. *Frontiers in Earth Science*, **12**, 1418016. doi:10.3389/feart.2024.1418016
12. Kim, H.-S., and Coauthors, 2024: Ocean component of the first operational version of Hurricane Analysis and Forecast System: Evaluation of HYbrid Coordinate Ocean Model and hurricane feedback forecasts. *Frontiers in Earth Science*, **12**, 1399409. doi:10.3389/feart.2024.1399409
13. Domingues, R., and Coauthors, 2019: Ocean observations in support of studies and forecasts of tropical and extratropical cyclones. *Frontiers in Marine Science*, **6**, 446. doi:10.3389/fmars.2019.00446
14. Zhang, D., and Coauthors, 2023: Observing extreme ocean and weather events using innovative Saildrone uncrewed surface vehicles. *Oceanography*, **36**(2–3), 70–77. doi:10.5670/oceanog.2023.214
15. Sanabia, E. R., B. S. Barrett, P. G. Black, S. Chen, and J. A. Cummings, 2013: Real-time upper-ocean temperature observations from aircraft during operational hurricane reconnaissance missions: AXBT Demonstration Project year one results. *Weather and Forecasting*, **28**(6), 1404–1422. doi:10.1175/WAF-D-12-00107.1
16. Rogers, R., and Coauthors, 2006: The Intensity Forecasting Experiment: A NOAA multiyear field program for improving tropical cyclone intensity forecasts. *Bulletin of the American Meteorological Society*, **87**(11), 1523–1537. doi:10.1175/BAMS-87-11-1523
17. National Hurricane Center (A. B. Hagen, R. Berg, and R. J. Pasch), 2025: *Hurricane Milton (AL142024) Tropical Cyclone Report*. NOAA/National Hurricane Center, Miami, FL. https://www.nhc.noaa.gov/data/tcr/AL142024_Milton.pdf
18. Beven, J. L., II, R. Berg, and A. Hagen, 2019: *Hurricane Michael (AL142018) Tropical Cyclone Report*. NOAA/National Hurricane Center, Miami, FL. https://www.nhc.noaa.gov/data/tcr/AL142018_Michael.pdf
19. Benedetto, K. M., and A. E. Mercer, 2020: Climatology and spatiotemporal analysis of North Atlantic rapidly intensifying hurricanes (1851–2017). *Atmosphere*, **11**(3), 291. doi:10.3390/atmos11030291
20. Yaukey, P. H., 2014: Intensification and rapid intensification of North Atlantic tropical cyclones: the role of geography, time of year, age since genesis, and storm characteristics. *International Journal of Climatology*, **34**(4), 1038–1049. doi:10.1002/joc.3744

*Citations verified June 2026. The microwave-coverage-gap point (Section 7.3) is flagged as lacking a verified peer-reviewed source and should be supported with current NOAA/NESDIS documentation prior to any formal submission.*

---

*Analysis and figures reproducible from `build_gulf_hurricanes.py`, `ri_climatology.py`, and the ocean-heat pipeline (`build_ohc_hycom.py`, `build_ohc_copernicus.py`, `analyze_d26_ri.py`, `scaled_d26_ri.py`) — NOAA HURDAT2 1851–2025 [10], HYCOM GOFS 3.1, and Copernicus Marine GLORYS. Companion interactive map: RapidWatch Gulf Geospatial Canvas — layers "Historical Gulf hurricanes," "Intensification to peak," "RI climatology hotspot," and four measured "Real D26" fields.*
