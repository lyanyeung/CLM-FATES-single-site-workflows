# US-NR3 Stage07 (Claude): per-event scientific decisions for the 238 missing half-hours (2026-10-29)

**Scope.** This report covers US-NR3 Niwot Ridge Alpine (T-Van West) only.

**Approval state.** Nothing is approved.
- `APPROVED_FOR_NEW_VERSION = False` for all 238 rows.
- No original BASE/FLUXMET/ERA file or research shadow was changed.
- No DATM, AD400 or Slurm work was done.
- Every option below needs an explicit user decision.

## Evidence base

**Script.** [`nr3_07_claude_ERA_mechanism_QC0_validation_event_decisions_READONLY.py`](../scripts/us_nr3_science/nr3_07_claude_ERA_mechanism_QC0_validation_event_decisions_READONLY.py)
- Commit `07b8581`, sha256 `958637ea…b165`.
- Run by the operator on IRIDIS6 with `--run` on 2026-10-29.
- It imports the operator-verified Stage01 inventory from its pinned blob (`83e3643e`). That import re-verified the full Stage07/10/12G SHA lineage and the reconciliation 238 = 172 + 66.

**Inputs (SHA-pinned).**
- BASE v6-5 `85db3e85…a35b`
- FLUXMET v1.3_r1 `dbc36536…87a2`
- Stage12G `b16f81d1…c48f`
- Stage10D `701f5e7b…e06e`
- Joins: 315,600/315,600.

**Report on IRIDIS.** `reports/nr3_07_claude_event_science_20261029T061908Z_505d290d/`. It holds the per-event file `US_NR3_238_missing_event_decisions.csv`, the full 1,484 matrix `US_NR3_1484_source_ERA_pair_matrix.csv`, the validation tables, and `nr3_07_receipt.json`.

**ERA5-Land years available.** 13 years: 2007, 2009, 2012, 2014, 2016–2024. No grid exists for 2008, 2010, 2011, 2013 or 2015.

## 1. Sensor metadata (what is and is not established)

**FLUXNET BIFVARINFO (release metadata), all effective 2007-05-17.**

| Variable | Sensor | Height |
| --- | --- | --- |
| TA | `TEMP-ElectResis` (resistance thermometer) | 3 m |
| RH | `RH-Capac` (capacitive) | 3 m |
| VPD | `[TA] TEMP-ElectResis. [RH] RH-Capac` | 3 m |
| PA | `GA_OP-LI-COR LI-7500` (the open-path analyser's pressure sensor) | 3 m |

Other release metadata:
- Tower type: tripod.
- Elevation 3504 m; UTC offset −7.
- ONEFlux `1.3.5-rc`, processed 2026-04-01 at AMP.

**Literature.** Blanken et al. (2009, *Biogeochemistry*) describe the T-Van systems from June 2007:
- CSAT3 sonic, LI-7500 and a shielded Vaisala HMP45C, all at 3 m;
- 10 Hz flux sampling;
- CR3000 datalogger.

This is consistent with the BIFVARINFO sensor classes. T_SONIC and H2O have no FLUXNET varinfo entry.

**Not established.**
- No BASE-BADM, AUXMETEO or instrument-history file exists next to the IRIDIS sources (the directory search returned an empty list).
- Year-specific instrument changes, serial numbers and QA notes, including why TA/RH/PA stop in May 2017, why 2018 has no BASE channels and why 2023 has PA/sonic without RH, therefore remain **unverified**.
- They require the AmeriFlux BADM workbook (BASE-BADM download) or the PI. The AmeriFlux site page lists PI John Knowles and flux contact Peter Blanken, and gives no measurement heights, instruments or gap notes.

**VPD lineage (proven).** `RH × esw(TA_F)` reproduces the QC0 vapour pressure with MAE 0.0035 hPa (N = 168,559). So the measured QC0 VPD at this site **is computed from the same HMP RH and TA**.
- Validation against QC0 therefore tests the temperature paired with the measured RH. It does not independently test the RH sensor.
- The HMP45C RH accuracy below −20 °C is not independently verified here. H2O is absent at all 238 gaps; in other years H2O-derived e agrees within 0.12 hPa (Stage05).

## 2. Mechanism of the negative ERA vapour pressure

| Quantity | Value |
| --- | --- |
| FLUXMET-clock TA_ERA/VPD_ERA pairs with e = esw(TA_ERA) − VPD_ERA < 0 | **5,466** (2007–2024) |
| of which the Stage10D selected set | 1,484 (all 1,484 confirmed negative) |
| negative but outside the 1,484 | **3,982** |
| among the 238 current missing HH | 234 |
| VPD_ERA minimum, **every year 2007–2024** | **1.448–1.449 hPa** |
| HH within 0.01 hPa of that floor | 2,790 |
| temperature where esw = floor | **−18.35 °C** |
| OLS VPD_ERA ~ ERA5-Land VPD (all grid years) | slope 0.543, **intercept 1.562 hPa**, R² 0.880 (yearly intercepts 1.506–1.612) |
| OLS TA_ERA ~ ERA5-Land T2M | slope 0.785, intercept −0.37 °C, R² 0.951 |
| negative pairs where esw(TA_ERA) < fitted VPD intercept | 4,688 of 5,466 |
| ERA5-Land d2m > t2m + 0.1 K | 0 of 227,952 |

Share of negative pairs by TA_ERA bin:

| TA_ERA bin (°C) | ≤ −25 | −25:−20 | −20:−15 | −15:−10 | > −10 |
| --- | --- | --- | --- | --- | --- |
| Negative share | 100 % | 100 % | 38.7 % | 0.1 % | 0 |

**Interpretation.**
- FLUXNET downscaling corrects TA and VPD **independently**, each by a linear regression with its own slope and intercept (Vuichard & Papale 2015, ESSD, Eq. 4). No joint saturation constraint is applied.
- At US-NR3 the VPD regression has a positive intercept, so downscaled VPD can never fall below about 1.45 hPa.
- Below about −18.3 °C, saturation vapour pressure is below that floor, so e < 0 is **arithmetically unavoidable**. Between −18 and −10 °C the floor forces e far too low.
- The raw grid is self-consistent (no dewpoint above temperature). The inconsistency is created by the downscaling step, not by the reanalysis physics.
- The BIF `GRP_ERA_DOWN` entries (slope 1.0, intercept 0.0) describe the fit of site data on the *already downscaled* series, which is 1 and 0 by construction. They do not contradict this.
- The same floor behaviour was seen at US-NR1 (VPD_ERA ≈ 2.15 hPa at −13 to −18 °C; CL01).

**Consequence beyond the 238.**
- Every ERA-filled (QC2) cold half-hour at US-NR3 is biased dry. On real QC0 cold data (Dec/Jan, TA_F ≤ −10 °C) the companion e has bias −0.73 hPa and median relative error 45 %.
- Finite Stage12G rows adjacent to the 2016-12-17 and 2017-01-05 gaps carry e = 0.05 and 0.01 hPa (ice RH of a few percent) at −18 °C. These are physically admissible numbers but **implausible**.
- This affects all of 2017, 2018 and 2023 (100 % QC2) in winter. It is a model-forcing risk far larger than the 238 gaps, and is flagged here for a separate decision.

## 3. Validation on genuine tower QC0

**Truth.** Simultaneous TA_F_QC = VPD_F_QC = 0, with e > 0.

**Metric.** Error in e (hPa). QBOT depends on e, and at a fixed temperature the e error equals the VPD error.

**Methods are fixed.** The only statistical method is the climatology, which leaves out the predicted row's whole year.

COLD44 is Dec/Jan with TA_F ≤ −10 °C, the regime of the 44 BASE events.

| Method | Pooled MAE / bias | COLD44 N | COLD44 MAE | COLD44 bias | COLD44 median rel. |
| --- | --- | --- | --- | --- | --- |
| **RH_SONIC**: BASE RH × esw(T\*), T\* = humidity-corrected sonic T | 0.218 / +0.148 | 13,714 | **0.067** | **+0.019** | **3.4 %** |
| RH_ERA_T: BASE RH × esw(TA_ERA) | 0.750 / +0.059 | 13,714 | 0.591 | +0.492 | 36.7 % |
| COMP_E: esw(TA_ERA) − VPD_ERA | 0.913 / −0.207 | 12,111 formable | 0.742 | −0.725 | 45.3 % |
| GRID_A: esw(ERA5-Land d2m) | 0.861 / +0.557 | 7,885 | 0.234 | −0.006 | 11.7 % |
| EMP_LOYO: QC0 RH climatology (month, 3-h, TA_ERA bin) × esw(TA_ERA), year left out | 1.170 / +0.024 | 14,174 | 0.410 | +0.262 | 23.4 % |

**RH_SONIC in COLD44 by year.**
- MAE ranges from 0.027 to 0.144 hPa.
- Bias is within ±0.07 hPa in 11 of 13 years. The exceptions are 2007 (−0.099) and **2011 (+0.122)**.
- The sonic T\* minus TA_F bias over the same years is −0.82 °C (2007) to **+1.44 °C (2011)**. It is diagnostic only and never applied.

**Predeclared criterion.** In COLD44, pooled **and** every year with N ≥ 50 must meet all of:
- MAE ≤ 0.15 hPa;
- |bias| ≤ 0.10 hPa;
- median relative error ≤ 10 %;
- MAE below every ERA-family method.

Result:
- Pooled: pass.
- Beats the ERA family: yes.
- Every year: **fail**. 12 of 13 years pass; 2011 fails on bias alone, at 0.122 hPa.
- **`RH_SONIC_SUPPORTED = False`.** The rule is not changed after seeing the result.

**DATM (installed source).** `components/cdeps/datm/datm_datamode_clmncep_mod.F90`, sha256 `e85fc972…87da`.
- With a specific-humidity stream: `qsat` is computed from `datm_esat(tbot,tbot)` (Flatau polynomial, **over ice below 0 °C**) and QBOT is clamped to it, silently.
- With an RH stream: RH is multiplied by the same `datm_esat`, so below 0 °C RH would be read relative to ice. AmeriFlux/HMP RH is relative to water, so this would bias humidity dry by 9–29 % between −10 and −35 °C.
- The active case datamode and build are not verified.

## 4. Per-event decisions (predeclared rules, operator run)

| Class | HH | Composition |
| --- | --- | --- |
| SOURCE_MEASURED_SUPPORTED | **0** | — |
| EXTERNAL_ERA_CANDIDATE_UNCERTAIN | **163** | All via EMP_LOYO, a site QC0 climatology at ERA temperature; no ERA humidity used |
| PHYSICS_CONFLICT_HOLD | **75** | 44 BASE rows (27 + 17 below) + 31 non-BASE |
| EVIDENCE_INSUFFICIENT_HOLD | **0** | — |
| **Approved** | **0** | |

### 4a. The 44 BASE RH+sonic+PA rows (0 in the 1,484)

**27 rows fail only the 2011 year criterion.** They are physical at the forcing temperature (ice RH at TA_USE ≤ 96 %), with e from 0.18 to 1.01 hPa and a sonic-bias envelope half-width ≤ 0.10 hPa.
- 2016-12-07 19:00
- 2016-12-17 22:00 and 22:30
- 2016-12-18 04:00
- 2017-01-05 22:30 and 23:00
- 2017-01-06 02:00, 03:00, 03:30, 04:00, 05:30–08:30 (11)
- 2017-01-07 04:00–08:30 (10)

2017-01-06 is a very dry event (RH 17–27 %, e ≈ 0.2 hPa), against ERA-based neighbours of 0.6–0.9 hPa.

**17 rows are a genuine temperature/phase conflict.** ERA TA_USE is 1.9–6.3 °C colder than T\*, so the measured e is above ice saturation at TA_USE. DATM would clamp these rows.

| Run | HH | T\* − TA_USE (°C) | Ice RH at TA_USE |
| --- | --- | --- | --- |
| 2016-12-08 02:30–03:00 | 2 | +6.3, +5.6 | 86 % and 108 % |
| 2016-12-17 04:00–06:00 | 5 | +4.6 to +5.0 | 136–143 % |
| 2017-01-05 02:30–07:00 | 10 | +1.9 to +5.8 | 113–165 % |

For the 2017-01-05 run, the e envelope half-width is 0.13–0.19 hPa and there is no 2017 QC0. The humidity is not what is in doubt here; the forcing **temperature** is.

### 4b. The 194 non-BASE rows

**163 rows: EXTERNAL_ERA_CANDIDATE_UNCERTAIN.**
- TA_USE ranges from −24.9 to −16.4 °C. 161 of the 163 also have GRID_A; 2 are in years without an ERA5-Land grid.
- EMP_LOYO is physical at TA_USE and passes the Stage12j gates in its (month, TA_ERA bin) stratum.
- In those strata EMP_LOYO has MAE 0.24–0.53 hPa, bias −0.07 to +0.21 hPa and median relative error **20–38 %**.
- GRID_A has *lower* error in every one of these strata (MAE 0.18–0.37, median relative error 16–25 %). It never passed the gate only because the grid exists for 13 of 18 years (valid fraction < 0.6), which is a coverage artefact of the gate rather than a skill result.
- The forcing temperature of these rows is itself ERA (QC2).

**31 rows: PHYSICS_CONFLICT_HOLD.**
- **2009-12-03 01:00–07:30 (14 HH), TA_USE −25.7 to −28.1 °C.** No validated stratum exists, because QC0 data at TA_ERA ≤ −25 °C in December are too few.
- **2018-10-15 01:00 and 2023-10-29 23:30 → 2023-10-30 03:00 (8 HH).** Both candidates are above ice saturation at TA_USE: EMP 100.7–104.2 %, GRID_A 103–132 %.
- **2019-01-01 03:00, 2019-11-27 04:00–05:00 (3) and 2022-03-11 05:00 (5 HH).** EMP is physical (ice RH 90–100 %), but its (month, TA_ERA ≤ −20 °C) stratum has no validation (N < 100 or gate fail).
- **2011-10-25 14:30 and 15:00.** No ERA5-Land year; the warm (−3.5 °C) October stratum is not gated.
- **2011-11-29 13:30 and 14:00.**
  - **Diagnosis: an isolated temperature spike at a sensor restart.**
  - BASE TA and RH are missing from 11:00. At 13:30 TA_F is a QC1 MDS value of −18.8 °C. At 14:00 TA_F is **QC0 −34.873 °C** (BASE −34.874).
  - The sonic reads −1.4 to −1.8 °C throughout, ERA −0.5 °C. At 14:30 TA is back to −2.70 °C, with RH 50 %.
  - The MDS TA values at 11:00–13:30 (−24 to −19 °C) are contaminated by the spike.
  - The 14:00 QC0 value is almost certainly not air temperature. Overriding a QC0 source value is the user's decision.

**2021-05-31 09:30 (TA QC0 1.03 °C, VPD QC1 6.645 hPa, e = −0.06) is not in the 238.**
- RH is missing from 06:30 to 09:30. MDS filled VPD at 4.4–6.6 hPa (RH ≈ 10–25 % at about 0 °C), yet RH is 99 % from 10:00.
- The Stage12G value at that half-hour, and the whole 06:30–09:30 MDS run, deserve a check. This is not part of the current gap set.

## 5. Options for the user (no default is applied)

| # | Population | Options | Claude's assessment |
| --- | --- | --- | --- |
| 1 | 27 BASE rows | (a) keep HOLD under the predeclared rule; (b) accept RH_SONIC as SOURCE_MEASURED_SUPPORTED (research), recording that 12/13 cold years pass and 2011 fails on bias 0.122 hPa | (b) is scientifically defensible: COLD44 MAE 0.067 hPa, an order of magnitude better than any ERA method; in-year 2016 QC0 bias +0.057; 2017 envelope ≤ 0.08 hPa. It is a deliberate exception to a predeclared criterion, so it is the user's call. |
| 2 | 17 BASE T-conflict rows | (a) HOLD; (b) research T sensitivity: TA = T\* (uncalibrated physics, cold-season sonic bias −0.8…+1.4 °C) with measured e; (c) keep ERA T with measured e capped to ice saturation, which is what DATM would do anyway | (a) now. (b) is a temperature repair and needs its own approval. (c) hides a real 2–6 °C temperature conflict. |
| 3 | 163 EMP rows | (a) HOLD; (b) EMP_LOYO sensitivity-only; (c) GRID_A sensitivity-only where the grid exists (161 of 163) | Sensitivity only, never "measured". GRID_A has the lower validated error; EMP has full coverage. |
| 4 | 31 non-BASE conflicts | HOLD. For 2011-11-29 14:00, decide whether to flag the QC0 TA spike as invalid source data. | HOLD; the spike flag is recommended for review. |
| 5 | All ERA-filled cold rows (outside the 238) | Separate decision: the 1.45 hPa VPD floor makes QC2 winter humidity systematically too dry, which affects 2017/2018/2023 entirely | Recommend a dedicated research shadow comparing companion vs GRID_A vs EMP for QC2 cold rows before any NR3 model admission. |

US-NR3 cannot be admitted to a model run while any of the 238 rows is NaN. Whichever options are chosen, the result is a new research shadow. The original Stage12G is not edited.

## 6. Stage08 (2026-10-29 06:33): alternatives for the HOLD rows and gap locations

**Run.** Script [`nr3_08_claude_HOLD_alternatives_and_gap_locations_READONLY.py`](../scripts/us_nr3_science/nr3_08_claude_HOLD_alternatives_and_gap_locations_READONLY.py), commit `11068aa`. It is read-only and wrote one report: `reports/nr3_08_claude_HOLD_alternatives_20261029T063329Z_40b2fe2d`.

**User decisions recorded on 2026-10-29.** The recommendations in §5 were accepted:
- the 27 BASE rows are accepted as a research exception;
- the 17 and 31 rows stay HOLD pending alternatives;
- the 163 rows are sensitivity-only;
- the spike flag goes for review;
- the dry-bias question gets a separate study.

Nothing has been written to any forcing or shadow yet.

**Where the gaps are.**
- All 238 lack **only humidity** (`QBOT|VPD_USE`).
- They fall in 53 episodes. All but 2 are cold nights or early mornings, December to March, with TA_USE between −16 and −35 °C, inside QC2 (ERA-filled) periods.
- The full episode table is `P0_missing_episodes.csv`.

**T\* (humidity-corrected sonic) versus ERA as air temperature, on QC0 TA_F.**

| Stratum | T\* MAE / bias (°C) | TA_ERA MAE / bias (°C) |
| --- | --- | --- |
| Pooled (N 161,950) | 0.75 / +0.46 | 3.36 / +0.02 |
| COLD44 (N 13,714) | **0.58 / +0.20** | **4.17 / +3.10** |
| \|TA_F − TA_ERA\| > 5 | 0.73 / +0.41 | 6.73 / −0.92 |
| COLD44 by year | 0.21–0.82 (2011: 1.61) | 2.96–4.79 |

- T\* is better than ERA in all 13 years, so the predeclared criterion `T_STAR_BETTER = True`.
- The complete measured pair (VPD at T\*, from measured RH) has COLD44 MAE **0.027 hPa**.

**Time interpolation.** It validates very well on NR3 QC0: 3-HH pseudo-gaps give MAE 0.02–0.24 hPa and every regime passes. It is formable for **none** of the gaps, because none has a QC0 anchor within 4 HH.

**Alternatives for the 48 HOLD rows (none approved).**

| Group | Alternative | HH |
| --- | --- | --- |
| 17 BASE temperature conflict | `MEASURED_PAIR_CANDIDATE_T_REPAIR`: TA = T\*, e = RH × esw(T\*); ice RH at T\* 46–97 % | 17 |
| 31 non-BASE | EMP_LOYO validated at season + bin level: 2009-12-03 01:00–07:30 (14 HH), 2019-01-01 03:00 | 15 |
| | GRID_A validated at bin level: 2019-11-27 04:00–05:00, 2022-03-11 05:00 | 4 |
| | GRID_A capped to ice saturation, excess ≤ 3.3 %: 2018-10-15 01:00, 2023-10-29 23:30 | 2 |
| | **HOLD**: 2011-10-25 14:30–15:00 (no validated stratum); 2011-11-29 13:30–14:00 (QC0 TA spike −34.87 °C); 2023-10-30 00:00–03:00 (6 HH, GRID_A 11–32 % above ice saturation; EMP would need only a 2.3–4.2 % cap, but the predeclared lower-MAE rule chose GRID_A) | 10 |

**Scope beyond the 238.** There are **11,981** QC2-temperature half-hours that do have a tower RH+sonic+PA triplet: 2016-09 to 2017-05, and 2019-01.
- The current shadow TA_USE differs from T\* by an MAE of about 3.3 °C.
- The shadow e is biased −0.4 to −0.8 hPa.

**Dry artefact.** Compare the shadow's QC2 cold rows (TA_USE < −10 °C, N = 16,670) with QC0 truth (N = 30,867):

| Population | Median ice RH | Share with ice RH < 30 % |
| --- | --- | --- |
| Shadow QC2 cold rows | **31 %** | 47 % |
| QC0 truth | **94 %** | 1.1 % |

This is the largest humidity problem at US-NR3, and it lies outside the 238.
