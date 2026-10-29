# US-NR3 | Claude scientific handoff | Stage01–Stage05 (2026-10-29)

**Scope:** AmeriFlux Batch03 **US-NR3** (Niwot Ridge Alpine, **T-Van West**), not US-NR1, US-MtB or US-Me6. This is a self-contained transfer of completed audits, source receipts, scientific decisions and next research questions. **No further code or model execution is requested by the user at handoff.**

**Current disposition:** original **238 Stage12G NOLEAP missing halfhours stay HOLD**; **0 scientifically approved replacements**. Separate **1,484 source QC2 anomalous humidity records** are *not* 1,484 current missing rows. No approved forcing, DATM, AD400 or Slurm run. The only repository changes made here are **new read-only audit scripts and documentary evidence**. The baseline raw BASE, original FLUXMET, companion ERA5, research shadows, Stage12G selected file and historical scripts have not been overwritten.

## Essential evidence links and pinned identities

1. [Initial project scientific handoff](US_NR3_ADVANCED_MODEL_SCIENTIFIC_HANDOFF_20261029.md) — site and older Stage10–Stage12 provenance.
2. [Stage01–02 inventory/science script](../scripts/us_nr3_science/nr3_01_source_inventory_READONLY.py) — 238/1,484 reconciliation; grid candidates A/B/C; ERA5-Land physics and QC0 tests.
3. [Stage03–04 SHA-pinned BASE source bridge](../scripts/us_nr3_science/nr3_03_04_BASE_bridge_READONLY.py) — operator-verified combined audit version **nr3-03-04-v1.1-20261029**, pinned run commit **f79b2ac5a29c2457ef1af9e403a6380af57e456b**.
4. [Stage03 exact BASE evidence/sonic yearly validation](US_NR3_STAGE03_BASE_VERIFIED_STAGE04_PENDING_20261029.md). The historical filename contains "PENDING" because it preceded the successful Stage04 run; see next item for final Stage04 status.
5. [Stage04 completed source overlap/pressure provenance](US_NR3_STAGE04_VERIFIED_2017_OBSERVATION_COCOVERAGE_20261029.md).
6. [Stage05 SHA-pinned H2O + 44-event script](../scripts/us_nr3_science/nr3_05_H2O_44_event_science_READONLY.py) — operator-verified **nr3-stage05-v1-20261029**, pinned run commit **6cd03b2d47c421136881f44183f9001eb5a2c2d9**.
7. [Stage05 completed H2O and manual HOLD report](US_NR3_STAGE05_VERIFIED_H2O_AND_44_EVENT_MANUAL_HOLD_20261029.md).
8. [Exact 44 missing HH with all original observational fields and diagnostic values](US_NR3_STAGE05_44_RAW_TRIPLET_EVENT_LEDGER_20261029.csv). Rows in this CSV were transcribed directly from the operator-returned Stage05 log; **it is an evidence transcription, not a newly measured source or approved forcing**.
9. [Stage06 draft-only read-only script](../scripts/us_nr3_science/nr3_06_original_HOLD_reason_and_cold_QC0_READONLY.py) — source/ancestor reason and cold QC0 audit **committed but not run on IRIDIS6** before user handed work to Claude. Its existence does **not** constitute a scientific result or request that Claude execute it without review.
10. [US-NR3 dedicated audit README](../scripts/us_nr3_science/README.md).

Original SHA256 source identity (operator-verified):

| Input | SHA256 |
|---|---|
| BASE v6-5 \`AMF_US-NR3_BASE_HH_6-5.csv\` | \`85db3e85463aaf300f326c0766f24c8a228b174f679968265e97b69bd619a35b\` |
| FLUXMET HH v1.3_r1 \`AMF_US-NR3_FLUXNET_FLUXMET_HH_2007-2024_v1.3_r1.csv\` | \`dbc365368a492285ea73193b1ff1dbb0336673f9448c18d734e82fb7717087a2\` |
| Current selected Stage12G NOLEAP \`US-NR3_STAGE12G_INCOMPLETE_NOLEAP.csv\` | \`b16f81d125944c47cf6d1886d51461053091cd819cb3d5048cea49247bccc48f\` |
| Stage10D ledger \`all_1924_manual_review.csv\` | \`701f5e7bb42e97448607f6cc63265d80889ce94347e5f6109b89ec282dfac06e\` |

IRIDIS6 original BASE path: \`/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-NR3/forcing/raw/AMF_US-NR3_BASE_HH_6-5.csv\`. Experiment root: \`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03\`. Exact original FLUXMET location is established via \`qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json\`, **not guessed**. Original BASE and FLUXNET files have **315,600 native halfhours each, 315,600 exact keyed matches, 0 unmatched**. The Stage12G model-domain NOLEAP file has **315,360 rows**; do not confuse raw all-days with selected NOLEAP.

## Scientific reconciliation from Stage01–Stage02 — already completed

The current 238 incomplete NOLEAP HH form **53 selected missing episodes**: **172 protected original physics HOLD**, plus **66 other gaps** (41 site–grid temperature difference >5 °C, 19 inherited ice-saturation screen fails, 6 external-year source-unavailable records). Six source-year issue rows are nested in the 66, not additional to 238. There are **1,484 original QC2 VPD physics anomaly events**, of which **172 intersect these 238 missing HH**. The other 1,312 of the original 1,484 are outside current missing, and may still require numeric/source physics review.

Across all 1,484 original same-release \`TA_ERA\` and \`VPD_ERA\` paired records,
\`e_a = es_water(TA_ERA) - VPD_ERA < 0\`, which is physically impossible for actual vapour pressure. This demonstrates an inconsistent *pair of source product variables*, not physically negative atmospheric moisture, nor proof of any particular downscaling regression, elevation, or clock bug. No manual clipping of negative \`e\`, replacement of QC2 without review, or mixing gridded VPD from a different temperature with retained tower T.

Stage02 evaluated fixed uncalibrated ERA5-Land candidate transfers on true simultaneous source QC0 T/VPD in available years: **A absolute water vapour e: equal-year VPD MAE 0.811 hPa, 8/238 numerical physical screens; B water-relative RH: 1.234 hPa, 4/238; C specific humidity q: 0.736 hPa, 20/238**. These are *numerical passes only*, not scientifically admissible repairs. Original tower pressure for the missing years/rows has QC2 processing provenance. No independent tower measurements for 2017, 2018, 2023 T/VPD can be inferred.

## Stage03 BASE v6-5 bridge — operator verified

2017 original BASE availability: **0 TA**, **6,329 RH**, **0 VPD_PI**, **6,340 PA**, **6,170 T_SONIC**; 2018: **all five channels absent**; 2023: **0 TA/RH/VPD_PI, 3,623 PA and 3,515 T_SONIC**. All 17,520 records in each of 2017/2018/2023 have \`TA_F_QC=VPD_F_QC=2\` in examined FLUXMET (processed ERA/downscaled source, **not proof of field sensor failure**).

BASE TA vs FLUXNET QC0 TA is close to exact (yearly MAE ~0.0002–0.0003 °C), demonstrating **source-lineage agreement, not independent external validation**. Fixed *unfitted* CSAT-style approximate sonic humidity inversion \`Ts_K=T_K*(1+0.51q)\`, evaluated against source original dual-QC0 T/VPD, produces year-varying biases from **−0.8516 °C (2007)** to **+1.2186 °C (2019)**, and MAE often near 0.3–1.3 °C. Thus **T_SONIC is not calibrated absolute air temperature** and a year-derived correction must not be transported to unobserved 2017 or 2023 by fiat.

## Stage04 — completed successfully on IRIDIS6

**2017 source-only triplet** (numerical RH between 0 and 100%, T_SONIC between −70 and +60 °C, BASE PA 40–110 kPa) yielded **6,160 simultaneous RH+T_SONIC+PA halfhours in 53 source observation windows**, all Jan–May. The 53 observation windows are **not** the same population as 53 selected missing Stage12G episodes. From June–December 2017, none of the three channels was available in BASE.

**2017 BASE RH and FLUXMET RH are exactly the same at all 6,329 matched native records (MAE=0, maximum absolute difference=0)**. They are not two independent sensors.

The Stage12G missing 238 divide by year as follows:

| Year | Missing HH | BASE RH+sonic+PA numerical co-occurrence |
|---|---:|---:|
| 2007 | 45 | 0 |
| 2009 | 16 | 0 |
| 2011 | 6 | 0 |
| 2012 | 13 | 0 |
| 2016 | 12 | **11** |
| 2017 | 38 | **33** |
| 2018 | 27 | 0 |
| 2019 | 7 | 0 |
| 2021 | 8 | 0 |
| 2022 | 35 | 0 |
| 2023 | 9 | 0 |
| 2024 | 22 | 0 |
| **Total** | **238** | **44** |

**44/238** of current missing records have marginally plausible BASE RH+sonic+PA, **none of them has directly QC0 TA/VPD or a verified absolute temperature**. The remaining **194/238** do not have these three numerical channels concurrently. BASE PA has many numbers, but raw FLUXMET \`PA\` is absent for the inspected years and processed \`PA_F_QC=2\`; BASE-vs-PA_F errors are ~0.13–0.21 kPa MAE depending on year; no validation of pressure source/height/instrument is implied.

Stage04 identified an additional **two** original mixed-QC negative-vapour T/VPD pairs in 2011 and 2021 (QC0 TA with QC1 VPD); these do **not** belong automatically to the separate 1,484 source QC2 category.

## Stage05 — completed successfully on IRIDIS6

All four SHA256 checks passed. Original BASE/FLUXMET joined 315,600/315,600.

AmeriFlux BASE \`H2O\` is **wet-air vapour mole fraction**, mmol H2O/mol wet air (not dry-air water mixing ratio); \`e_hPa = H2O_(mmol/mol) * BASE_PA_(kPa) / 100\`.

**Key rejection of hoped-for H2O fix:** 2017, 2018 and 2023 have **zero H2O** and, in fact, **zero of all 238 missing HH has numerical BASE H2O**. All **44** RH+sonic+PA event rows have **H2O=null**. The H2O channel therefore gives **no direct observation of the present missing moisture**. It remains useful to understand historical sensor agreement, but is not a data source to fill these gaps.

H2O-inferred vapour pressure vs original simultaneous source dual-QC0 T/VPD: equal-year-of-equal-day MAE **0.120018 hPa** across 15 available years, but with notable source disagreements: 2009 MAE **0.430948 hPa** / bias +0.430905, 2010 MAE **0.515725** / bias +0.515725, 2011 MAE **0.328244** / bias +0.328115; compare 2016 MAE **0.014981 hPa**. Shared sensor/instrument/derived-variable provenance remains possible; not independently validated.

**Stage05 exact key cross-join:** **1,484** original Stage10D anomalous source events, **238** selected Stage12G missing; **172** overlap. The **44** missing halfhours with RH+sonic+PA triplets have **zero intersection with those 1,484**. These are outside the selected source-ERA negative-e anomaly ledger; they are **not validated/safe** merely by being absent from the 1,484 flagged set.

The **44** comprise **11 contiguous selected-missing runs**: five in 2016 (11 HH), six in 2017 (33 HH). For **7/44**, uncalibrated humidity-adjusted sonic T differs by >5 °C from Stage12G \`TA_USE\`; for **4/44** calculated ice-relative RH at retained \`TA_USE\` exceeds 100%; for **1/44** calculated ice-relative RH at inferred sonic T exceeds 100% (very slightly, ~100.06%). These numbers are **diagnostics**, not authorization to clip/relax saturation thresholds or overwrite T.

**Seven >5 °C discrepancy native timestamps:**
\`201612080230\`, \`201612080300\`, \`201701050230\`, \`201701050300\`, \`201701050330\`, \`201701050400\`, \`201701050430\`.

**Four ice RH(TA_USE)>100% timestamps:** \`201701050230\`, \`201701050300\`, \`201701050330\`, \`201701050400\`. **One ice RH(sonic)>100% timestamp:** \`201612180400\`. These are conditional temperature hypotheses rather than proven supersaturation measurements.

## Original mixed-QC episodes demanding manual provenance review

- **2011-11-29 14:00 native:** original \`TA_F=-34.873°C QC0\`, \`VPD_F=2.451 hPa QC1\` implying \`e≈−2.132257 hPa\`; BASE \`TA=-34.87352°C\`, \`T_SONIC=-1.818732°C\`, RH and H2O missing, BASE PA=66.81376 kPa. Neighbor BASE TA rapidly reverts to near −3 °C at 14:30/15:00. QC0 flag does not establish validity of that *mixed-variable pair*, nor justify replacing measured TA without field provenance.
- **2021-05-31 09:30 native:** original \`TA_F=1.034°C QC0\`, \`VPD_F=6.645 hPa QC1\` implying \`e≈−0.058838 hPa\`; BASE sonic 0.8115006 °C, BASE RH and H2O missing. At 10:00, \`TA_F=0.198°C QC0\`, \`VPD_F=0.063 hPa QC0\`, BASE RH ~98.98%. Needs QC1/source-processing mechanism review; not automatically one of the 1,484 source-ERA QC2 events.

## Scientific decision table — no approved replacements

| Population | Current evidence | Decision |
|---|---|---|
| 44 BASE RH+sonic+PA co-observed selected missing HH | Original instrument *values* present; 11 runs, zero H2O, no same-time QC0 T/VPD, 7 temperature disagreements, 4/1 ice cautions | **HOLD; AUXILIARY SOURCE CANDIDATE ONLY** |
| 194 remaining Stage12G missing HH | No simultaneous 3-channel BASE measurements; Stage12B/E source/physics inherited reasons remain | **HOLD** |
| Selected source abnormal QC2 ERA pairs (1,484) | Original same-release impossible negative e; 172 among present missing HH | **SOURCE PHYSICS REVIEW, no automatic replacement** |
| Mixed-QC 2011/2021 special cases | Same-record T/VPD algebra invalid, source observations conflict | **MANUAL SOURCE REVIEW / HOLD** |
| Stage02 ERA candidates A/B/C | QC0 cross-year numerical MAEs and preliminary physical screens available; no actual source truth for absent-year timestamps | **UNCERTAIN RESEARCH/SENSITIVITY ONLY; 0 approved** |

This audit did **not** establish BADM/sensor serial numbers, measurement heights, date-specific QA, an independent temperature truth in missing 2017/2018/2023, the causal FLUXNET ERA processing defect, ERA5-Land representativeness over 3,504 m alpine topography, active CTSM/CDEPS datamode or genuine model admission.

## Research questions for Claude — in priority order

1. Read original [hand-off](US_NR3_ADVANCED_MODEL_SCIENTIFIC_HANDOFF_20261029.md), [Stage04](US_NR3_STAGE04_VERIFIED_2017_OBSERVATION_COCOVERAGE_20261029.md), [Stage05](US_NR3_STAGE05_VERIFIED_H2O_AND_44_EVENT_MANUAL_HOLD_20261029.md) and [44-row event CSV](US_NR3_STAGE05_44_RAW_TRIPLET_EVENT_LEDGER_20261029.csv). **Do not rerun confirmed source inventories without a material new question.**
2. Reconcile **Stage12B original protected** vs **Stage12E other-gap HOLD** for each of the 44, with exact ancestor reason, source QC and missing field. An **unexecuted Stage06 draft** exists, but its output is *not evidence* and no script execution is requested by the user in this handoff.
3. Trace sensor-level BASE/BADM and Niwot Ridge T-Van West measurement history, **instrument type/height/period/QA**, focusing on 2016 Dec and 2017 Jan RH/sonic/PA, 2017 mid-May loss of fields, 2018 no BASE channels, 2023 sonic/PA with RH absent; never assume nearby US-NR4 / US-xNW or US-NR1 share tower measurements.
4. Evaluate any proposed method with **actual source simultaneous T/VPD QC0**, matching winter/temperature regime, whole-day and source-year blocks; compare e and VPD error, bias and tail error, pressure and ice/water saturation; **no fitted year offset applied to unseen 2017** and no arbitrary relaxed thresholds.
5. Independently verify the reason 1,484 same-release \`TA_ERA,VPD_ERA\` pairs lead to negative e. Cross-check FLUXNET processing, source time semantics, elevation/grid representativeness, water/ice saturation and raw ECMWF t2m/d2m/sp aligned on native interval midpoint/UTC offset, without assuming a root cause.
6. Verify **actual installed** CTSM/CDEPS streams/CLMNCEP path, site surface and PFT, sensor pressure/height and what (if anything) clamps QBOT. The referenced public CDEPS branch has case-dependent saturation and humidity pathways but may not match this live model case.
7. Present a **manual event-level decision memorandum** separating \`SOURCE_MEASURED_SUPPORTED\`, \`EXTERNAL_ERA_CANDIDATE_UNCERTAIN\`, \`PHYSICS_CONFLICT_HOLD\`, and \`EVIDENCE_INSUFFICIENT_HOLD\`, with exact approved count **0 until explicit user acceptance**. In particular, numerical physical pass ≠ independently measured truth ≠ scientifically approved repair.

## Strict scope and no-actions

Do **not** overwrite the original AmeriFlux BASE/FLUXMET, companion ERA, prior research shadows, approved or historical Git objects, or existing Stage12G selected rows. No auto-fill of QC2; no threshold relaxation, negative-e clipping, blind date interpolation, hidden empirical temperature calibration, forcing generation, DATM case edit, AD400, spinup, job submission, or Slurm. Any **future actual writes** to project/science data require distinct user authorization. GitHub documents are an evidence archive, not proof of scientific approval.

The user has now asked for **packaging for Claude, and explicitly does not want more code**. This handoff is the artifact to deliver; do not reply with a new runnable command.
