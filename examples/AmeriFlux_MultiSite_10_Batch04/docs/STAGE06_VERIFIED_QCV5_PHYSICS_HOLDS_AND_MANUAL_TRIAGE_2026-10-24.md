# AmeriFlux Batch04 — Stage06 operator VERIFIED; manual science QC triage

**Date:** 2026-10-24. Evidence: operator Stage06 full terminal log (self-test/check/run). All three priority source FLUXMET releases and Stage05 patches passed SHA and targeted original value, humidity reconstruction and candidate-effect checks. No original/Stage05 forcing modifications.

## Executed command results

- Stage06 self-test PASS; `--check` PASS; `--run` PASS.
- All original HH rows re-read in source provenance checks: US-SP1 **368,208**, US-Syv **438,288**, US-Ton **438,288**.
- Candidate variable-level patch rows **5,336**; Stage05 unresolved HOLD rows **754**; high-impact adjacent VPD review edges **210**. Review edges are flagged when **new VPD jump >4 hPa OR the change in jump >2 hPa**; **not all 210 are necessarily newly introduced**.
- Isolated Stage06 report directory:
  `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/reports/stage06_qcv5_candidate_effects_20261024T105030Z_8cc1f59c`
- Stage05 candidate source remains:
  `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage05_candidates/candidate_20261024T103113Z`

| Site | Original HH rows | Patch variable rows | Unique patched half-hours | RH+VPD reconstructed half-hours | Local TA/PA/joint-zero candidate rows | HOLD rows | ERA reconstructed at T<0°C | VPD change >5 hPa | Native VPD QC0 changed | VPD jump review edges |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| US-SP1 | 368,208 | 87 | 45 | 39 | 9 | 147 | 4 | 32 | 0 | 19 |
| US-Syv | 438,288 | 534 | 268 | 265 | 4 | 606 | 231 | 1 | 42 | 12 |
| US-Ton | 438,288 | 4,715 | 2,359 | 2,356 | 3 | 1 | 1 | 552 | 2,259 | 179 |
| **Total** | **1,244,784** | **5,336** | **2,672** | **2,660** | **16** | **754** | **236** | **585** | **2,301** | **210** |

## HOLD breakdown — NOT automatic fallback

| Reason | Site | Count |
| --- | --- | ---: |
| SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID | US-SP1 | 147 |
| SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID | US-Syv | 183 |
| ERA_PAIR_HUMIDITY_INVALID | US-Syv | 419 |
| ERA_RH_OUTSIDE_QCV5_USABLE_RANGE | US-Syv | 4 |
| SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID | US-Ton | 1 |
| **TOTAL** | | **754** |

There are **331** temperature discrepancy/invalid-tower-TA holds, **419** broken ERA pairs and **4** ERA RH domain holds. A >8°C tower–ERA difference is a *screening condition*, not direct proof that the measured tower temperature is wrong. Do not force source ERA substitution on invalid pairs; use independent ERA5-Land/reference evidence as appropriate, checking clock, source pair consistency and saturated-over-ice convention in winter.

## Important: candidate risk is greater than merely 754 HOLDs

**2,301 native VPD_F_QC=0 half-hours would be altered** by the current overlay (US-Ton **2,259**, US-Syv **42**). The latter changes must receive their own source/QC audit before acceptance; a QC0 datum cannot be overwritten merely because raw `RH` is outside an arbitrary range. US-Ton original `RH≈102%` can coexist with `VPD_F=0` and internally saturated derived humidity (100%) without requiring nonzero ERA VPD. In that case consider leaving scientifically valid native TA/VPD untouched while flagging/capping only the separate raw RH representation if scientifically justified. Apparent extreme dry RH also needs raw sensor/QC provenance and comparisons; positive RH<5% is not automatically a false measurement.

**585** humidity VPD reconstruction candidates differ by >5 hPa, overlapping with QC0 and edge groups. **236** humidity reconstructions occurred below zero °C (231 US-Syv, 4 US-SP1, 1 US-Ton); source RH over liquid water and ice/temperature definitions require review.

**210** flagged adjacent VPD edges: US-Ton 179, US-SP1 19, US-Syv 12. These **include pre-existing** high jumps; do not equate every flag with a new effect or smooth solely by threshold.

Top operator-verified changes:

| Station | Boundary | Original abs ΔVPD hPa | Candidate abs ΔVPD hPa | Added hPa |
| --- | --- | ---: | ---: | ---: |
| US-Ton | 2001-05-18 05:30→06:00 | 0.986 | **16.404455** | **15.418455** |
| US-Ton | 2001-05-18 11:30→12:00 | 3.107 | **11.991424** | **8.884424** |
| US-SP1 | 2008-03-23 07:00→07:30 | 0.619 | **9.211947** | **8.592947** |
| US-Ton | 2003-02-27 09:00→09:30 | 0.068 | **8.418701** | **8.350701** |
| US-Ton | 2023-10-10 18:30→19:00 | 0.093 | **7.954041** | **7.861041** |
| US-Ton | 2023-10-10 18:00→18:30 | 0.097 | **7.950041** | **7.853041** |
| US-Syv | 2007-05-12 19:00→19:30 | 0.686 | **5.542211** | **4.856211** |

## Next decision gates, in order

1. **Hold** automatic acceptance of all humidity-overwrite entries with original VPD QC0 until source QC/provenance adjudication. Prioritize US-Ton (2,259) and US-Syv (42); group contiguous episodes and evidence rather than require a line-by-line manual edit of 2,301 points.
2. Triage US-Ton original `RH>100`, native `VPD_F=0`, and genuine low RH as **separate** conditions. Decide whether to preserve native VPD, adjust raw RH output representation only, or approve ERA-RH replacement with independent evidence.
3. Group and adjudicate **754** HOLDs by primary reason. 419 US-Syv invalid ERA pairs should receive an independent ERA5/ERA5-Land dewpoint or other supported source, not a forced reuse of corrupted `*_ERA`. Check 331 TA difference/T invalid cases against native TA QC and independent temperature context; evaluate 4 ERA RH bounds separately.
4. Examine top **210** flagged VPD transitions with original and proposed RH/VPD, original QC and provenance, whether jump is added, cold/saturation calculations, and any disjoint repair windows; never automatically smooth all.
5. Verify and retain the **16** highly constrained short-run TA/PA interpolations only where local conditions are physically plausible. Candidates themselves have not yet been accepted as production forcing.
6. Once three-site science gates pass, separately extend scientific meteorological QC to the other **seven Batch04 sites**. No site Post-v5/DATM/CLM-FATES spinup approval has been recorded.

**Current scientific status:** Stage05 candidate-building VERIFIED, Stage06 full technical audit VERIFIED, science review required; there are **0 Post-v5 approvals, 0 DATM approvals, 0 spinup approvals** for this Batch04 pipeline.
