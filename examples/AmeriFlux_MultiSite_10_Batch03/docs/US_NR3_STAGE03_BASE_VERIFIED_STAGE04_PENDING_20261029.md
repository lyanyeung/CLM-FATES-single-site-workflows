# US-NR3 — Stage03 BASE evidence and Stage04 pending rerun (2026-10-29)

**Scope**: AmeriFlux Batch03 US-NR3 (Niwot Ridge Alpine / T-Van West) only. Original raw/ERA/shadows, Git history, DATM and model jobs are unchanged. This record transcribes **operator-returned terminal output**; it is not a claim that the GitHub runner accessed IRIDIS6. No replacement is approved.

## Reproducibility

- BASE source: AMF_US-NR3_BASE_HH_6-5.csv, SHA256 **85db3e85463aaf300f326c0766f24c8a228b174f679968265e97b69bd619a35b**; local path \`/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-NR3/forcing/raw/AMF_US-NR3_BASE_HH_6-5.csv\`.
- Original FLUXNET-1F v1.3_r1 primary: AMF_US-NR3_FLUXNET_FLUXMET_HH_2007-2024_v1.3_r1.csv, SHA256 **dbc365368a492285ea73193b1ff1dbb0336673f9448c18d734e82fb7717087a2**, resolved via Stage07 exact_input_manifest.json; no guessed source path.
- The operator's 2026-10-29 Stage03 returned **315,600 BASE rows**, **315,600 FLUXNET rows**, **315,600 exact native-time matches** and **0 unmatched**. Both full-file digests passed.
- Existing source-to-selected reconciliation (Stage01/02): **238 Stage12G NOLEAP missing in 53 episodes** = **172 original protected physics HOLD + 66 other gaps** (41 site–grid |ΔT|>5°C, 19 ice-saturation screen failures, 6 no external-year grid evidence). **172** overlap the **1,484** source-VPD QC2 physics events. These are different populations; do not add their totals.
- Existing QC0-evaluated gridded VPD methods (10 equal-weight source years): A transfer absolute e: MAE **0.811 hPa**, 8/238 numerical screen passes; B grid RH: **1.234 hPa**, 4/238; C grid q: **0.736 hPa**, 20/238. Numerically passing is **not** independent source-supported repair; approved count remains **zero**.

## Full 2007–2024 original BASE coverage (operator-returned Stage03)

All values below are numeric counts, not independent sensor QC designations. \`dual_QC0\` is the same-release original FLUXNET TA_F/VPD_F simultaneous QC0 count; \`PA_QC2_with_BASE\` is the count of BASE pressure observations for which the processed PA_F flag was 2.

| Year | BASE TA | BASE RH | BASE VPD_PI | BASE PA | BASE T_SONIC | FLUXNET dual_QC0 | PA_QC2_with_BASE |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2007 | 8,899 | 8,890 | 8,899 | 8,900 | 9,222 | 8,890 | 8,900 |
| 2008 | 17,513 | 17,265 | 17,483 | 17,513 | 17,252 | 17,265 | 17,513 |
| 2009 | 17,453 | 17,384 | 17,401 | 17,453 | 17,312 | 17,384 | 17,453 |
| 2010 | 17,144 | 16,261 | 16,271 | 17,144 | 16,987 | 16,261 | 17,144 |
| 2011 | 11,263 | 10,861 | 11,134 | 12,177 | 12,068 | 10,861 | 12,177 |
| 2012 | 3,609 | 3,609 | 3,609 | 14,512 | 14,377 | 3,609 | 14,512 |
| 2013 | 17,381 | 17,135 | 17,380 | 17,385 | 17,216 | 17,135 | 17,385 |
| 2014 | 14,776 | 14,752 | 14,753 | 14,787 | 14,509 | 14,752 | 14,787 |
| 2015 | 11,651 | 11,638 | 11,647 | 11,651 | 11,553 | 11,638 | 11,651 |
| 2016 | 2,813 | 8,029 | 2,813 | 8,029 | 7,954 | 2,813 | 8,029 |
| 2017 | 0 | 6,329 | 0 | 6,340 | 6,170 | 0 | 6,340 |
| 2018 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2019 | 5,878 | 6,483 | 5,875 | 8,943 | 8,865 | 5,857 | 8,943 |
| 2020 | 9,147 | 9,107 | 9,146 | 6,554 | 7,849 | 9,107 | 6,554 |
| 2021 | 14,728 | 14,632 | 14,727 | 14,730 | 14,383 | 14,632 | 14,730 |
| 2022 | 3,794 | 3,789 | 3,793 | 3,794 | 3,763 | 3,789 | 3,794 |
| 2023 | 0 | 0 | 0 | 3,623 | 3,515 | 0 | 3,623 |
| 2024 | 14,584 | 14,566 | 14,584 | 14,940 | 15,815 | 14,566 | 14,940 |

**Source rule:** presence of BASE_PA while processed PA_F_QC is 2 does *not* establish the exact PA_F numerical lineage or the original raw PA QA. Distinguish \`FLUX_PA\`, \`PA_F\`, \`BASE_PA\` in the unrun Stage04 check.

## Missing-source years: exact operator-returned coverage

| Year | BASE TA | BASE RH | BASE VPD_PI | BASE PA | BASE T_SONIC | original simultaneous dual QC0 TA/VPD |
|---|---:|---:|---:|---:|---:|---:|
| 2017 | 0 | 6,329 | 0 | 6,340 | 6,170 | 0 |
| 2018 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2023 | 0 | 0 | 0 | 3,623 | 3,515 | 0 |

All 17,520 original FLUXMET halfhours per listed year had \`TA_F_QC=2\` and \`VPD_F_QC=2\`. This indicates ERA-based/downscaled provenance under the product conventions, **not** proof instruments were physically broken. BASE presence is not an independently vetted QC0 designation. 2017 counts are marginal availability and do **not** show how many RH+T_SONIC+PA are simultaneous. Stage04 is designed to answer that question.

## Stage03 year-by-year uncalibrated sonic comparison

Reference: original \`TA_F_QC=0\` and \`VPD_F_QC=0\` with water-physical truth checks, compared against fixed \`Ts_K = T_K (1 + 0.51 q)\` inversion using BASE T_SONIC, RH and PA, no learned annual or monthly offset.

| Year | n | MAE °C | bias °C | P95(abs error) °C |
|---|---:|---:|---:|---:|
| 2007 | 8,856 | 0.8821 | -0.8516 | 1.4490 |
| 2008 | 17,094 | 0.5411 | -0.4941 | 1.1046 |
| 2009 | 17,257 | 0.3246 | +0.0066 | 0.7416 |
| 2010 | 16,225 | 0.3839 | +0.2435 | 0.8116 |
| 2011 | 10,797 | 0.5756 | +0.4527 | 0.9987 |
| 2012 | 3,550 | 0.4488 | +0.4213 | 0.7957 |
| 2013 | 17,058 | 0.7260 | +0.6759 | 1.3530 |
| 2014 | 14,477 | 0.8973 | +0.8641 | 1.5543 |
| 2015 | 11,541 | 0.8884 | +0.8067 | 1.5813 |
| 2016 | 2,744 | 0.6724 | +0.6147 | 1.0883 |
| 2019 | 5,192 | 1.2667 | +1.2186 | 1.9137 |
| 2020 | 5,791 | 1.1605 | +1.1261 | 1.8416 |
| 2021 | 14,315 | 1.1587 | +1.0769 | 1.8736 |
| 2022 | 3,762 | 1.0495 | +1.0103 | 1.8316 |
| 2024 | 13,291 | 1.0173 | +0.9547 | 1.6808 |

2007–2024 BASE_TA vs original FLUXNET QC0 TA MAE was approximately 0.0002–0.0003 °C in each measured year (release/source consistency, **not independent validation**). Sonic-based residual sign and magnitude vary by year, precluding any scientifically justified extrapolation of an offset into 2017 or 2023. For 2011, equal-date MAE 0.8926 °C versus HH MAE 0.5756 °C illustrates aggregation sensitivity; preserve dates and QC rather than combining unweighted rows alone.

## Exact physical exceptions

- Native 2011-11-29 14:00: BASE TA **-34.87352 °C**, RH missing, PA **66.81376 kPa**, T_SONIC **-1.818732 °C**, BASE VPD_PI **0.0 hPa**; FLUXNET TA_F **-34.873 °C / QC0**, VPD_F **2.451 hPa / QC1**, TA_ERA **-0.519 °C**, VPD_ERA **3.339 hPa**, PA_F **66.812 kPa / QC2**. At TA_F, es_water approx **0.319 hPa**; \`es_water(TA_F)-VPD_F\` negative approx **-2.132 hPa**. **Do not label VPD as QC0** or assert either TA or sonic absolute value is independently true; this episode remains HOLD pending source QA.
- Native 2018-02-21 09:30: BASE TA/RH/PA/sonic all absent, FLUXNET TA_F=TA_ERA=-21.064 °C, VPD_F=VPD_ERA=1.572 hPa (both QC2).
- Native 2018-02-21 10:00: BASE absent; FLUXNET TA_F=TA_ERA=-19.050 °C, VPD_F=VPD_ERA=1.623 hPa (both QC2). Compare same-source pair thermodynamics before any cross-source VPD reattachment.

For **every year with BASE PA**, the operator's availability table showed \`BASE_PA_FLUX_QC2\` equal to \`BASE_PA\` count. This does not establish whether \`PA_F\` equals BASE PA; Stage04 compares BASE with the raw FLUXMET PA column and PA_F separately (kPa). Be explicit about QC2 provenance.

## Corrected Stage04 reproducibility / status

The first operator Stage04 invocation **stopped before loading or changing any science data**, with \`NR3_STOP: SHA mismatch .../AMF_US-NR3_BASE_HH_6-5.csv\`. Cause: the preceding assistant's inline expected BASE_SHA accidentally omitted the final **b**. This was a coding typo, **not evidence of source corruption**. The fixed expected SHA above is used in \`nr3_03_04_BASE_bridge_READONLY.py\`. The consolidated Stage04 script is newly committed but its full cluster run is **PENDING**, not a PASS.

Use \`python -B .../nr3_03_04_BASE_bridge_READONLY.py --self-test\` then \`--stage04\` on IRIDIS6. It verifies SHA and exact 238 Stage12G missing timestamps, counts simultaneous 2017 BASE RH+PA+sonic availability and contiguous windows, tests BASE-vs-FLUXNET pressure and RH provenance, and prints year-specific overlap. No files or model jobs are produced.

## Manual decision (as of 2026-10-29)

- **SOURCE_MEASURED_SUPPORTED**: 0 approved repairs; BASE temperature with source QC0 is the same primary measurement lineage, so concordance alone is not external truth.
- **EXTERNAL_ERA_CANDIDATE_UNCERTAIN**: A/B/C numerically feasible subsets require independent truth and local/topographic/phase validation; cannot back-fill the protected 172 by arithmetic screen alone.
- **PHYSICS_CONFLICT_HOLD**: retain source cold VPD contradictions, 2011 severe TA/sonic discrepancy and protected 172.
- **EVIDENCE_INSUFFICIENT_HOLD**: retain absent years/unsupported sensor observations and the other 66 Stage12G gaps until per-event evidence exists.
- **APPROVED_FOR_NEW_VERSION=false** for all 238. No raw FLUXMET/BASE/ERA overwrite, no existing shadow overwrite, no DATM, AD400, or Slurm.

Next unapproved steps requiring scientific review: sensor-specific BADM start/end, instrument/height and QA (especially 2017); FLUXNET v1.3_r1 processing cause of \`VPD_ERA>es_water(TA_ERA)\`; ERA5-Land grid topography and pressure representativeness; installed active CDEPS datamode versus public reference. Do not infer true instrument failure or repair success from QC labels alone.


## Stage04 post-commit operator failure and correction

The operator tested the first GitHub consolidated script from commit
`aa816af6661206b46c74b2b147aefe0deb7c3df8`. The
`--self-test` passed, followed by both exact SHA checks. But the
`--stage04` audit stopped during `load_sources` with
`AttributeError: 'DataFrame' object has no attribute 'BASE_SONIC'. Did you
mean: 'BASE_T_SONIC'?`.

Root cause: raw BASE `T_SONIC` had been renamed automatically as
`BASE_T_SONIC`, while Stage03/Stage04 referred to `BASE_SONIC`.
In commit `f79b2ac5a29c2457ef1af9e403a6380af57e456b`, a
single `base_column_map()` now maps `T_SONIC` consistently to
`BASE_SONIC`, with schema regression checks in self-test and before
analysis. No other science or source modification was authorised.
**Corrected Stage04 has not yet been operator-run; no Stage04 results
are claimed.** The previous Stage03 operator results remain the evidence
baseline, not independently recalculated by this commit.
