# US-NR3 — Stage05 verified BASE H2O and 44-event scientific decision (2026-10-29)

**Status:** operator-returned successful Stage05 from pinned commit `6cd03b2d47c421136881f44183f9001eb5a2c2d9`. All calculations in this memo originate from the operator's output; this is **not** a remote rerun by the GitHub editor. Original data/shadow/ERA/model files not modified. **238 Stage12G missing HOLD, 0 scientifically approved repairs**.

## Exact source and workflow

- `AMF_US-NR3_BASE_HH_6-5.csv` SHA256 `85db3e85463aaf300f326c0766f24c8a228b174f679968265e97b69bd619a35b`.
- `AMF_US-NR3_FLUXNET_FLUXMET_HH_2007-2024_v1.3_r1.csv` SHA256 `dbc365368a492285ea73193b1ff1dbb0336673f9448c18d734e82fb7717087a2`.
- `US-NR3_STAGE12G_INCOMPLETE_NOLEAP.csv` SHA256 `b16f81d125944c47cf6d1886d51461053091cd819cb3d5048cea49247bccc48f`.
- `all_1924_manual_review.csv` SHA256 `701f5e7bb42e97448607f6cc63265d80889ce94347e5f6109b89ec282dfac06e`.
- Exact BASE/FLUXNET joined native HH records: **315,600** each, zero unmatched.
- `NR3_STAGE05_READONLY_COMPLETE` and shell `STAGE05 FINISHED` returned.
- Script: [Stage05](../scripts/us_nr3_science/nr3_05_H2O_44_event_science_READONLY.py). Exact **44 native-time rows** transcribed from the log in [the Stage05 44-row evidence CSV](US_NR3_STAGE05_44_RAW_TRIPLET_EVENT_LEDGER_20261029.csv), including original `TA_USE`, `PSRF`, RH, T_SONIC, PA, H2O, source QC2, subfreezing diagnostics, case-event flags and candidate VPD (not approved).

## H2O question settled for current 238

The AmeriFlux BASE H2O variable is **wet-air mole fraction** in **mmol/mol**, as defined by [AmeriFlux variable definitions](https://ameriflux.lbl.gov/data/aboutdata/data-variables/); the Stage05 conversion `e_hPa = H2O_mmol/mol * PA_kPa / 100` correctly uses **wet-air** basis. H2O is not a dry-air mixing ratio.

- Source H2O is present in many **other** years (Stage05 reported 15 years with H2O and validation). **No H2O** in 2017, 2018 or 2023; 2017 still has 6,329 RH numeric, 6,170 sonic numeric and 6,340 PA numeric in the *marginal* BASE coverages.
- **Zero of 238** Stage12G missing HH has numeric BASE H2O; **zero of 44** original BASE RH+sonic+PA triplets has numeric H2O, so H2O cannot provide a direct measured vapour fraction for any current missing key. Do not use H2O values from other years as replacements.
- Across 15 original `TA_F_QC=VPD_F_QC=0` source years, the Stage05 *equal source-year of equal-day* H2O-vs-source-e MAE was **0.120018 hPa**. This is a source-comparison, **not independently proven sensor-truth**; RH/VPD/H2O may share analyser lineage.
- The 2009, 2010, 2011 water-vapour source comparison was notably poor: MAE **0.430948, 0.515725, 0.328244 hPa** respectively, with approximately equally large positive bias; absolute >1 hPa error proportions **6.73%, 10.51%, 5.06%**. Contrast 2016 MAE **0.014981 hPa** and 2008 **0.040377 hPa**. Treat the 2009–2011 offset as **unresolved source consistency / instrument or variable-processing question**, not proof that one source is truth or a permitted calibration.

## Exact Stage12G + Stage10D overlap

Stage05 verified original 1,484 Stage10D source anomalies, 238 Stage12G missing, **172 exact native-key intersection**, and **44 missing records with simultaneous BASE RH, sonic and PA** (11 during 2016, 33 during 2017). **0 of those 44** belongs to the 1,484 population. They are distinct from the 172 physics-overlap events and cannot be treated as fixes for the 1,484 ERA negative-vapour cases.

The 44 triplets form **11 contiguous missing-event runs** (five in 2016, six in 2017):

| year | native start | native end | HH |
|---|---|---|---:|
| 2016 | 201612071900 | 201612071900 | 1 |
| 2016 | 201612080230 | 201612080300 | 2 |
| 2016 | 201612170400 | 201612170600 | 5 |
| 2016 | 201612172200 | 201612172230 | 2 |
| 2016 | 201612180400 | 201612180400 | 1 |
| 2017 | 201701050230 | 201701050700 | 10 |
| 2017 | 201701052230 | 201701052300 | 2 |
| 2017 | 201701060200 | 201701060200 | 1 |
| 2017 | 201701060300 | 201701060400 | 3 |
| 2017 | 201701060530 | 201701060830 | 7 |
| 2017 | 201701070400 | 201701070830 | 10 |

**Preserve set identities**: 44 absence-of-anomaly does not imply physically validated source, nor is a 53-episode whole-source triplet inventory equal to these 11 selected-HH missing runs.

## Phase and temperature disagreements within 44

- For **7/44** the *fixed, uncalibrated* humidity-adjusted sonic T differs by >5 °C from selected `TA_USE`, which is source-ERA in these records. Native keys: `201612080230`, `201612080300`, `201701050230`, `201701050300`, `201701050330`, `201701050400`, `201701050430`.
- Ice-relative RH computed from BASE RH at retained `TA_USE` is >100% in **4/44**: `201701050230`, `201701050300`, `201701050330`, `201701050400` (highest **103.098%**). Ice-relative RH under the uncalibrated sonic-T inversion is >100% in **1/44**: `201612180400` (**100.060%**).
- These are **diagnostic flags** in two separate temperature hypotheses, not grounds to automatically clip e, silently relax a model constraint, or declare observed ice supersaturation impossible.
- Neither 2016/2017 missing 44 has original simultaneous measured `TA_F_QC=VPD_F_QC=0` at the same time; all 44 have source T/VPD QC2, BASE H2O null and unresolved RH/sonic instrument provenance.

## Two separate source-original mixed-QC physics conflicts

- **2011-11-29 14:00 (native)**: `TA_F=-34.873°C QC0`, `VPD_F=2.451 hPa QC1`, implied `e=−2.132257 hPa`; original BASE T_SONIC `−1.818732°C`, TA `−34.87352°C`, BASE RH/H2O missing. Time-adjacent BASE TA: at 14:30 `−2.699991°C`, at 15:00 `−3.103054°C`, indicating a severe isolated T disagreement that needs instrument and QC-source investigation. Do not relabel VPD QC1 as QC0 or overwrite the observed QC0 TA without explicit source evidence.
- **2021-05-31 09:30 (native)**: `TA_F=1.034°C QC0`, `VPD_F=6.645 hPa QC1`, implied `e=−0.058838 hPa`, BASE RH/H2O missing, sonic `0.8115006°C`. Neighboring 10:00 has original `TA_F=0.198°C QC0`, `VPD_F=0.063 hPa QC0`, `BASE RH=98.9802%`. The 09:30 record remains unresolved and is not in the same original QC2/ERA category.

## Scientific disposition and next admission gate

| Evidence class | Next research use | Current decision |
|---|---|---|
| 2016/2017 original RH+sonic+PA (44) | Investigate instrument height/model/sampling QC, original `Stage12B` vs `Stage12E` HOLD provenance, matched-date/year cold QC0 validation, water/ice saturation and model-specific constraints | **HOLD 44** |
| Remaining 194 Stage12G missing | Trace respective inherited physics vs source/ERA data-gap reasons and independently measured anchors | **HOLD 194** |
| Stage10D 1,484 QC2 negative-e source pairs | Investigate downscaling/source processing, physical consistency and external alternatives, not automatically replace | **NO REPAIR APPROVED** |
| 2009–2011 H2O high positive bias | Verify sensor/measurement model/height and possible shared lineage before any correction | **DIAGNOSTIC ONLY** |
| 2011/2021 original QC0 TA + QC1 VPD mismatches | Source-specific manual QA and spatial/timing checks; retain original values | **HOLD / REVIEW** |

**Next step**: original BADM BIF, [AmeriFlux Measurement Height](https://ameriflux.lbl.gov/data/measurement-height/), and exact 44 ancestor-ledger reasons, then *no-fit* year/day blocked QC0 checks in cold regimes. Do **not** equate FLUXNET `QC=2` to sensor failure: the documented FLUXNET convention is ERA-downscaled provenance for `TA_F/VPD_F/PA_F` (see [FLUXNET FULLSET](https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/)). Do not infer measurement-height history from a 3 m tower height. User approval required before any output-file write, new shadow, forcing, DATM or model job.
