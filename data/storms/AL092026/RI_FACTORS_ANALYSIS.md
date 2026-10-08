# Hurricane Isaias (AL092026): what drove the rapid intensification

Written 2026-10-08 04:40 UTC, while the storm was a 65 kt hurricane in the southern Gulf. Every number
below is read from the archived sources in this folder (NHC operational SHIPS files, best track,
aircraft messages, NHC discussions, this site's HYCOM snapshots and Argo profiles). This is an
analysis of the record, not a forecast. It will be revised after the storm when the final best track
and the NHC tropical cyclone report are available. The auto-generated tables are in
`RI_EVENT_RECORD.md` and `ri_timeline.csv`; this document interprets them.

## 1. What happened, by the numbers

| Time (UTC) | Wind | Pressure | Position | Note |
|---|---|---|---|---|
| Oct 6 18Z | 30 kt | 1007 mb | 21.9 N 95.7 W | Tropical depression forms, Bay of Campeche |
| Oct 7 00Z | 30 kt | 1006 mb | 21.7 N 95.3 W | **RI window opens** (30 kt gain over the next 24 h) |
| Oct 7 06Z | 35 kt | 1004 mb | 21.9 N 94.6 W | Tropical Storm Isaias |
| Oct 7 12Z | 40 kt | 1002 mb | 22.2 N 93.9 W | Enters the Zone A onset core box |
| Oct 7 18Z | 50 kt | 995 mb | 22.5 N 93.3 W | |
| Oct 8 00Z | 60 kt | 988 mb | 22.7 N 92.3 W | **RI definition met** (+30 kt / 24 h) |
| Oct 8 02:48Z | aircraft fix | 982 mb | 22.9 N 91.9 W | AF301: 57 kt at 700 mb, 7 nm from center |
| Oct 8 03:28Z | 65 kt | 982 mb | 22.9 N 91.9 W | **Hurricane**, by Tropical Cyclone Update, from dropsonde data |

Pressure fell 18 mb in the 24 h to 00Z and a further 6 mb in the next 3 h. The 24 h gain was exactly
the 30 kt threshold on the best track, with the hurricane upgrade following 3.5 h later.

**Where it began, relative to the site's watch boxes.** The RI window opened at 21.7 N 95.3 W. That
is 0.2° west of the expanded Zone A box (84.4 to 95.1 W) and 1.4° west of the onset core box
(91.6 to 93.9 W). The storm entered the expanded box by 06Z and the core box by 12Z, and the entire
second half of the RI window, including the hurricane upgrade, took place inside the core box. So the
event supports the Field Observation Report's core-box finding for where RI runs, while the onset
itself sat just outside the box's western edge, in the Bay of Campeche's southwest corner.

## 2. The factors, in order of how much the evidence supports them

### 2.1 Thermodynamic ceiling: near-record SST and a very high potential intensity

The SHIPS sea-surface temperature at the center was 30.8 to 30.9 °C through the whole window, easing
to 30.6 °C at the end. NHC's discussion 4 called these "near-record SSTs for this time of the year."
The resulting maximum potential intensity was 168 to 171 kt, so at the window opening the storm was
139 kt below its thermodynamic ceiling. In SHIPS-RII terms this is the strongest single predictor the
storm had, and it stayed strong throughout. A 30 kt system over 31 °C water in October with a 170 kt
ceiling has, by construction, the fuel for a fast climb. The 200 mb temperature of about minus 51 °C
(a cold upper troposphere) is part of why the ceiling was so high.

### 2.2 Shear: moderate, southwesterly, and steady enough

Deep-layer shear was 13 to 14 kt from the south-southwest (206° to 243°) for every cycle through 18Z
on Oct 7, rising to 19 kt from 226° at 00Z Oct 8. This is "moderate" in SHIPS terms, not the low-shear
switch the site's Observatory tab once described; the RI happened under 13 to 19 kt of shear, which
matches what the same page now says after the 2026-10-05 correction. NHC's P-3 tail Doppler radar on
Oct 7 showed the mid-level center displaced 5 to 10 nautical miles northeast of the low-level center,
a tilt consistent with that southwesterly shear, and the discussions note outflow "somewhat restricted
to the southwest." The shear was tolerated rather than absent. Two things helped: it was steady, and
the vortex re-formed and aligned (section 2.5), which is the known route by which a tilted storm
survives moderate shear.

### 2.3 Ocean heat: warm, but not deep

This is the point where Isaias departs from the Katrina and Rita template and resembles Milton (2024).

| Source | Value under the center |
|---|---|
| SHIPS ocean heat content | 54 to 56 kJ/cm² at the window opening, 34 to 42 kJ/cm² during the climb |
| HYCOM D26 (this site, nearest 6 h snapshot) | 42 to 49 m along the track |
| Argo float 2904010, 10 km from the center at 12Z Oct 7 (profile of Sep 27) | D26 69 m, mixed layer 50 m, surface 31.0 °C |

The Field Observation Report's full-record Gulf median D26 is about 44 m, so Isaias intensified over a
warm layer near or slightly above the median, with ocean heat content below the 80 kJ/cm² level the
literature links most strongly to RI. There was no Loop Current ring under it. The nearest float
measured a deeper 26 °C isotherm (69 m) than the model's 43 to 49 m, which is consistent with the
site-wide pattern seen on 2026-10-06 (floats run about 20 m deeper than HYCOM D26). Either way the
warm layer was adequate, not exceptional. What mattered more was the extreme surface temperature and,
most likely, the slow-to-moderate forward speed over a bay where the whole upper layer was warm.

### 2.4 Moisture: a very humid column

Mid-level relative humidity (700 to 500 mb) was 74 to 76% at the window opening and 69 to 70% during
the climb. NHC's discussions describe "plenty of deep-layer moisture" and "a very humid environment."
The SHIPS upshear dry-air metric at 06Z Oct 7 showed 0.6% of the area with precipitable water under
45 mm, essentially no dry air upshear. Dry-air intrusion, the usual RI killer in the western Gulf, was
absent.

### 2.5 Structure: center re-formation, then a small core that organized fast

NHC's discussion 4 (Oct 7, 15Z) reports a center re-formation that brought "the low- and mid-level
centers ... into better alignment" and says this "could facilitate rapid intensification." Discussion 3
had already noted bursting convection with cloud tops below minus 85 °C tightening a previously broad
circulation (an ASCAT pass at 03Z had found only 31 kt). Discussion 5A calls the storm small with a
"formative inner core," and by the 01:13Z fix on Oct 8 the aircraft reported an eyewall open to the
southwest, closed enough by 02:48Z for a dropsonde in the eye. GOES infrared statistics from the SHIPS
files agree: the fraction of pixels colder than minus 20 °C within 200 km went 94% (18Z Oct 6), 62% at
06Z Oct 7 (the broad, disorganized phase), then 97%, 90% and 86% as the convection consolidated.

Small storms respond faster to a favorable environment because the inner core spins up with less
mass to accelerate. This is the mechanism NHC leaned on when it raised the forecast to a 95 kt peak.

### 2.6 Upper-level support: divergence rising sharply as the climb accelerated

The 200 mb divergence from SHIPS went 48, 49, 36, 46, 53 and then 78 (units of 10⁻⁷ s⁻¹) across the six
cycles, with the jump coming between 18Z Oct 7 and 00Z Oct 8, the period of the 50 to 60 kt gain and
the fastest pressure falls. Outflow was observed in all quadrants by 03Z Oct 8. The 850 mb environmental
vorticity rose in step, from 5 to 14 early to 26 to 28 late. The steering was a mid-level trough along
the northern Gulf coast and an Atlantic subtropical ridge; the trough's upper-level flow is the likely
source of the improving outflow channel, and NHC expects the same trough to raise shear sharply before
landfall.

### 2.7 Motion: slow, east-northeast, over the warm pool

Forward speed was 2 to 8 kt, east-northeast. Slow motion over a thin warm layer normally risks a
self-induced cold wake. Isaias did not show one in the data in hand: HYCOM surface temperature under
the center went 29.3, 29.7, 30.2, 29.9, 29.6, 30.4 °C across the snapshots, with no step down. The
Bay of Campeche warm pool is broad, so an 8 kt storm keeps finding fresh 30 °C water ahead of it. The
ocean response will be clearer when the post-storm HYCOM and satellite SST fields are archived.

### 2.8 Climatology: the right place in the right month, starting weak

October is inside the August to October window that holds 84% of Gulf RI onsets. The storm began
intensifying at 30 kt, below the 50 kt median onset intensity in the 1851 to 2025 record, which is the
"begins in weak systems" finding of the Field report. The onset was in the Bay of Campeche, the
densest RI-onset region in the record, within 0.2° of the expanded watch box.

## 3. How the guidance saw it

| Cycle | Best track 24 h later | SHIPS deterministic 24 h forecast | NHC SHIPS-RII (30 kt/24 h) | DTOPS | Our rebuilt RII |
|---|---|---|---|---|---|
| Oct 6 18Z (30 kt) | 50 kt | 44 kt | 12.7% | 2% | 19.6% |
| Oct 7 00Z (30 kt) | 60 kt | 54 kt | 13.0% | 3% | 19.6% |
| Oct 7 06Z (35 kt) | 65 kt (03:28Z) | 58 kt | 13.1% | 28% | 14.7% |
| Oct 7 12Z (40 kt) | pending | 57 kt | 18.6% | 17% | 15.8% |
| Oct 7 18Z (50 kt) | pending | 76 kt | 29.2% | 15% | 24.4% |
| Oct 8 00Z (60 kt) | pending | 85 kt | 36.2% | 32% | 23.9% |

Three observations:

1. **Every probabilistic tool put RI at a minority probability when the window opened** (13% official,
   20% ours, 2 to 3% DTOPS), and the event happened. That is the expected behavior of a well-calibrated
   index for a 6.5% base-rate event: a 2 to 3 times climatological signal is a flag, not a prediction.
   NHC's human forecast at advisory 3 (+30 kt in 24 h) was stronger than any of the statistical tools.
2. **The SHIPS deterministic forecast under-forecast the first 24 h by 6 to 10 kt** and then caught up
   once persistence and the shrinking storm size fed in.
3. **Our rebuilt index tracked the official one closely** (within 2 to 7 points) until the last cycle,
   where it stayed at 24% against the official 36%. The difference is the shear term: our model uses
   the 0 h shear (19 kt), the official index uses a 24 h forecast average that includes the 12 to 16 kt
   values of the following cycles, and it also carries satellite and dry-air predictors our six-term
   rebuild does not.

## 4. Summary judgment

Isaias rapidly intensified because a small, newly aligned vortex sat under a 170 kt thermodynamic
ceiling in a saturated column with steady, moderate shear and an improving outflow channel, moving
slowly across a broad 31 °C warm pool. The ocean's role was as fuel at the surface rather than as a
deep reservoir: the warm layer was near the Gulf median, nothing like a Loop Current ring. In the
site's own framing this is the Milton pattern, not the Katrina pattern, and it is the second time in
two seasons that the Bay of Campeche has produced it.

## 5. What to add when the storm is over

1. Final best track (reanalysis may move the RI window or the hurricane time).
2. NHC tropical cyclone report, for the official intensity reasoning and recon summary.
3. Post-storm HYCOM and satellite SST fields, to measure the cold wake along the track.
4. Peak intensity and whether the forecast 95 kt and the pre-landfall shear increase verified.
5. The full dropsonde set (66 archived so far), especially the eye sondes of 02:30 to 03:10Z Oct 8.
