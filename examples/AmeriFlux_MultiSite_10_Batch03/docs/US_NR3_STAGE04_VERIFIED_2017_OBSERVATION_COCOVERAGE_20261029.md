# US-NR3 Stage04 — verified BASE observational overlap and scientific HOLD (2026-10-29)

**Evidence**: operator-returned `--stage04` terminal output from [`nr3_03_04_BASE_bridge_READONLY.py`](../scripts/us_nr3_science/nr3_03_04_BASE_bridge_READONLY.py), version `nr3-03-04-v1.1-20261029`; operator invoked pinned code at Git commit `f79b2ac5a29c2457ef1af9e403a6380af57e456b`. This is not a GitHub CI, remote filesystem read, sensor QA approval or rerun by this report's author.

All self-tests passed. Source SHA256 checked:

- BASE `AMF_US-NR3_BASE_HH_6-5.csv`: `85db3e85463aaf300f326c0766f24c8a228b174f679968265e97b69bd619a35b`
- FLUXMET `AMF_US-NR3_FLUXNET_FLUXMET_HH_2007-2024_v1.3_r1.csv`: `dbc365368a492285ea73193b1ff1dbb0336673f9448c18d734e82fb7717087a2`
- Stage12G selected `US-NR3_STAGE12G_INCOMPLETE_NOLEAP.csv`: `b16f81d125944c47cf6d1886d51461053091cd819cb3d5048cea49247bccc48f`

Exact native join 315,600 BASE/315,600 FLUXMET, 315,600 matched, 0 unmatched.

## 2017 simultaneous RH/sonic/pressure coverage

A valid marginal count is not a verified sensor measurement, and valid co-occurrence is not an approved repair. Script's diagnostic co-occurrence applies BASE RH in [0,100]%, T_SONIC in [-70,60] °C and PA in [40,110] kPa; these numerical checks are **not** model admissibility thresholds or QA approval.

| Month 2017 | BASE RH | T_SONIC | PA | simultaneous diagnostic triplet |
|---|---:|---:|---:|---:|
| Jan | 1,449 | 1,415 | 1,449 | 1,415 |
| Feb | 1,265 | 1,263 | 1,265 | 1,263 |
| Mar | 1,365 | 1,331 | 1,365 | 1,331 |
| Apr | 1,440 | 1,401 | 1,440 | 1,401 |
| May | 810 | 760 | 821 | 750 |
| Jun–Dec | 0 | 0 | 0 | 0 |
| **Total** | **6,329** | **6,170** | **6,340** | **6,160** |

The 6,160 triplets occur in **53** contiguous 30-minute windows. Longest: native `201704011300` to `201704281730`, **1,306 HH**. Other windows include `201701270130`–`201702100430` (679), `201703010800`–`201703131400` (589) and `201702111700`–`201702232200` (587). **Do not confuse these 53 source co-occurrence windows with the 53 Stage12G missing episodes**; they are different definitions.

The 2017 BASE RH and FLUXMET RH series have **6,329 exact matched numeric values**, MAE **0** and maximum absolute difference **0**. Therefore they represent a common variable lineage and do **not** form independent humidity truth.

## Stage12G missing-source overlap

| Source year | 238 missing HH | BASE TA | BASE RH | BASE PA | BASE sonic | RH+sonic+PA triplets | TA/VPD original dual QC2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2007 | 45 | 0 | 0 | 0 | 0 | 0 | 45 |
| 2009 | 16 | 0 | 0 | 0 | 0 | 0 | 16 |
| 2011 | 6 | 3 | 0 | 6 | 6 | 0 | 2 |
| 2012 | 13 | 0 | 0 | 6 | 6 | 0 | 13 |
| 2016 | 12 | 0 | 11 | 11 | 11 | **11** | 12 |
| 2017 | 38 | 0 | 33 | 33 | 33 | **33** | 38 |
| 2018 | 27 | 0 | 0 | 0 | 0 | 0 | 27 |
| 2019 | 7 | 0 | 0 | 0 | 0 | 0 | 7 |
| 2021 | 8 | 0 | 0 | 0 | 0 | 0 | 8 |
| 2022 | 35 | 0 | 0 | 0 | 0 | 0 | 35 |
| 2023 | 9 | 0 | 0 | 8 | 7 | 0 | 9 |
| 2024 | 22 | 0 | 0 | 22 | 21 | 0 | 22 |
| **Total** | **238** | **3** | **44** | **86** | **84** | **44** | **234** |

Rows with original dual-QC2 are provenance counts, not a declaration that each row has numerical VPD or is itself one of the selected 1,484 source physics anomalies. Prior Stage01 verified **172 of the 238** overlapping that selected 1,484 population, a different definition.

**Disposition:** 11 2016 + 33 2017 missing HH have concurrent numerically present original BASE RH, sonic temperature and pressure. This is *potential auxiliary evidence*, not independently proven correct temperature or approved humidity repair. **194** selected missing HH have no valid three-channel triplet. The 2017 source has no TA and no original dual-QC0 T/VPD; 2018 has no BASE TA/RH/PA/sonic; 2023 has PA and sonic but lacks RH.

## Pressure/source lineage

The FLUXMET raw `PA` variable was numerically absent (`raw_FLUXNET_PA=0`) for the queried years, while all `PA_F_QC` records were `2`. BASE pressure is often present and differs from processed PA_F; all MAEs are in **kPa**:

| Year | BASE PA HH | BASE vs PA_F n | MAE kPa | Bias kPa | P95 abs kPa |
|---|---:|---:|---:|---:|---:|
| 2011 | 12,177 | 12,177 | 0.208813 | -0.062037 | 0.455538 |
| 2016 | 8,029 | 8,029 | 0.209784 | +0.172095 | 0.527738 |
| 2017 | 6,340 | 6,340 | 0.182081 | +0.117052 | 0.486279 |
| 2018 | 0 | 0 | — | — | — |
| 2019 | 8,943 | 8,943 | 0.177938 | +0.125282 | 0.459622 |
| 2023 | 3,623 | 3,623 | 0.200223 | +0.166747 | 0.428831 |
| 2024 | 14,940 | 14,940 | 0.131662 | +0.041157 | 0.346080 |

The differences establish that BASE pressure and processed FLUXNET PA_F are not identical. They do **not** establish which instrument or pressure is more accurate, or whether PA_F was generated from BASE.

## Additional pair-physics exceptions

`es_water(TA_F)-VPD_F<0` with `TA_F_QC=0`, `VPD_F_QC=1`: **one record in 2011, one in 2021**. The 2011 example is native `201111291400`: BASE TA=-34.87352°C, T_SONIC=-1.818732°C, BASE RH missing, original TA_F=-34.873°C QC0, VPD_F=2.451 hPa QC1. These must receive individual source measurement/processing reviews. Do not include these two automatically in the distinct 1,484 source ERA QC2 population.

## New lead: independent water-vapour observable

The original BASE header includes `H2O`. AmeriFlux defines BASE H2O as water-vapour mole fraction of **wet air in mmol H2O mol−1** (not H2O_MIXING_RATIO, which uses dry air). It could be a valuable additional vapour constraint **if actually present, independently measured, timestamp-matched, within physical range and validated against original measured QC0 T/VPD**. Stage04 did not report H2O coverage; **no assumption of its availability is made**.

Reference: https://ameriflux.lbl.gov/data/aboutdata/data-variables/ and https://ameriflux.lbl.gov/sites/siteinfo/US-NR3. Measurement-height and sensor provenance must be verified before treating it as independent.

## Manual gate

`APPROVED_FOR_NEW_VERSION=false`; all **238 HOLD** remain, including the **44** triplets. No source/ERA/raw/shadow/forcing changes, no downloads, no Slurm/AD400. Next audit: exact 44 HH, H2O and CO2 numeric availability by year, conditional BASE RH-vs-H2O molecular thermodynamics, stage12g selected TA and PSRF, native clock, instrument/BADM provenance, original QC0 date- and year-blocked validation, and whether Stage10 source-ERA anomaly flags overlap these rows. No automatic QC2 filling or inferred repair entitlement.
