# AmeriFlux Batch03 — Stage12T original full-year VPD_F_QC vs TA_F_QC physics audit (operator-reported PASS)

**Date:** 2026-10-25. **Scope:** read-only three original year-sources, **52,560 source half-hours**: US-Me6 2015, US-Me6 2017, US-NR1 2022. Operator log includes two repeated original full-year reports and self-tests. **This is a Batch03 diagnostic, independent of Batch04 manual-three-temperature trial.**

```text
STAGE12T SELF-TEST PASS: original VPD vs water saturation, strict native QC and full-year episode counts; NO WRITES
STAGE12T SUMMARY: full_native_source_halfhours=52560 site_years=3 original_QC1_held_neighbor_sides=32 original_86_held_events_preserved=TRUE original_233_phys_holds_preserved=TRUE new_repairs=0 Postv5_approved=0 DATM_ready=0 spinup=0
STAGE12T CHECK ONLY: NO SOURCE, REPORT OR MODEL WRITES.
STAGE12T ORIGINAL YEAR-SOURCE REPORT DIR: /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12t_original_VPD_QC1_full_year_physics_episodes_20261025T181302Z_7b987cae
```

## Verified original native-year VPD physics grouped by VPD QC

The physical screen tests original `VPD_F` against saturation water vapour pressure at original `TA_F`, with distinction between native `VPD_F_QC` and original tower `TA_F_QC`. The physical inconsistency is not, by itself, proof that the tower TA is invalid.

| Site | Year | QC0 invalid / QC0 valid | QC1 invalid / QC1 valid | QC2 invalid / QC2 valid |
| --- | --- | --- | --- | --- |
| US-Me6 | 2015 | 0 / 12,612 | **115 / 3,228** | **18 / 1,680** |
| US-Me6 | 2017 | 0 / 15,872 | **114 / 1,608** | 0 / 40 |
| US-NR1 | 2022 | 0 / 16,904 | **126 / 614** | 0 / 2 |

All source native `TA_F_QC=0` for the invalid rows counted in the log; **none of the original VPD QC0 records violates the temperature/VPD saturation screen** across these three site-years. The invalidities appear only in **VPD QC1/QC2**. These counts are **whole-year screens**, not new approved correction targets; do not sum them or replace the pre-existing **233 physically held events** as if they were the same set.

## 32 signed focal source sides

| Site-year | Value origin | Signed sides | Median episode HH | Longest episode HH | QC0 valid anchor ≤24 h before | ≤24 h after |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| US-Me6 2015 | BOTH_FINITE_DIFFER | 9 | 2.0 | 6 | 8 | 8 |
| US-Me6 2015 | RAW_ONLY_FINITE | 3 | 2.0 | 3 | 3 | 3 |
| US-Me6 2017 | BOTH_FINITE_DIFFER | 13 | 12.0 | 23 | 1 | 2 |
| US-Me6 2017 | RAW_ONLY_FINITE | 5 | 6.0 | 17 | 0 | 2 |
| US-NR1 2022 | BOTH_FINITE_DIFFER | 2 | 37.5 | 45 | 1 | 2 |

**Long episodes requiring caution:**

- **US-NR1 2022:** 2022-09-09 08:00 → 2022-09-10 06:00 **45 HH (22.5 h)**, maximum VPD above saturation **3.996382 hPa**; 2022-09-10 08:30 → 23:00 **30 HH (15 h)**, max excess **5.167442 hPa**.
- **US-Me6 2017:** 2017-06-29 02:30 → 13:30 **23 HH (11.5 h)**, max excess **10.713476 hPa**; 2017-07-02 02:30 → 10:30 **17 HH (8.5 h)**, max excess **9.439266 hPa**.
- US-Me6 2015's longest listed run: 2015-11-30 08:00 → 13:00, **11 HH (5.5 h)**.

**Interpretation:** QC1 invalid spans sometimes persist for **many consecutive half-hours**, and no valid QC0 anchor within 24 hours precedes all episodes. Do not automatically interpolate long physical-inconsistency episodes from a single nearby source-side QC0 anchor. Consider using independent, clock-matched RH/d2m/T/p evidence for humidity-only candidates while keeping original tower TA when independently supportable. Source-side traceability and the exact **32** focal sides must remain intact.

**No source or model files were modified.** Original **86 held events** and **233 physical holds** remain; no Post-v5, DATM or spinup authorisation. This result does **not** imply the independent Batch04 trial is production-ready.
