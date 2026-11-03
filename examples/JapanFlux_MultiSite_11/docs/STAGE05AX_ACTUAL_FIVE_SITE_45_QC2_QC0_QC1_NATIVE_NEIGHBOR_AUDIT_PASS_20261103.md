# JapanFlux Stage05AX — ACTUAL five-site native-source QC0/QC1 neighbor audit PASS (2026-11-03)

## Source and provenance

This record reflects **actual operator-supplied successful IRIDIS6 stdout**, not a simulated run, from the pinned [Stage05AX original JPF source reader](../scripts/stage05/05ax_45_original_JPF_QC0_QC1_neighbor_and_QC2_run_READONLY.py) Git blob SHA `7cc202ff9a15fd4f78bba84d33cf65faeb4b3e07`. Source evidence comes from exact original JPF nested `FLUXMET_HH` CSVs, original README SHA reverified against saved Stage05K source metadata, and the actual [Stage05AW all-45 source ledger](STAGE05AW_ACTUAL_45_OF_45_UNIFIED_EVIDENCE_PASS_NEXT_STAGE05AX_20261103.md). The five source site-level runs and final aggregate all **PASS**.

```text
STAGE05AX FIVE_SITES_45_ORIGINAL_SOURCE_QC2_QC0_QC1_NEIGHBOR_MERGE_PASS | NO_REPAIRS
SOURCE_EVENTS 45 NATIVE_SITE_HALFHOURS 35 ORIGINAL_VARS {'PA': 27, 'TA': 6, 'LW_IN': 12}
QC0/QC1_TEMPORAL_FEASIBILITY_SCREENS {'LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED': 45}
FIVE_SOURCE_SITES_REVIEWED 5 ORIGINAL_README_TIME_CONFLICT_TEF_TMD_RETAINED
UNIFIED_NEIGHBOR_FEASIBILITY_TSV /home/ly3n24/japanflux_stage05ax/aggregate_20261103T065006Z/stage05ax_45_original_QC2_native_source_quality_anchor_feasibility_NO_REPAIR.tsv
SCIENCE_HOLD_SOURCE_SUMMARY /home/ly3n24/japanflux_stage05ax/aggregate_20261103T065006Z/stage05ax_45_original_QC2_five_site_QC0_QC1_neighbor_HOLD_summary.json
ALL_45_SCIENCE_HOLD; NO_REPLACEMENTS/CDS/FORCING/SLURM
```

## Actual five-site results

| Site | Flagged source QC2 variable fields | Distinct native halfhours | Original HH rows scanned | Max contiguous original F_QC=2 source-provenance run, HH | ±24h measured QC0 bracketing eligibility |
|---|---:|---:|---:|---:|---|
| JP-Fjy | 6 | 6 | 368,160 | 262,944 (PA) | 0 / 6 |
| JP-Khw | 11 | 7 | 385,728 | 385,728 (PA entire product) | 0 / 11 |
| JP-Yms | 10 | 8 | 420,768 | 325,824 (PA) | 0 / 10 |
| JP-Tef | 4 | 4 | 403,200 | 315,223 (LW_IN) | 0 / 4 |
| JP-Tmd | 14 | 10 | 333,072 | 333,072 (PA entire product) | 0 / 14 |
| **Total** | **45** | **35** | **1,911,928** | Not additive | **0 / 45** |

The **45/45** original selected-source QC2 flagged variable-fields were all assigned `LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED`. Specifically, none had a **same-variable measured QC0 anchor on both sides** in its native ±24 h window. The stdout for every one of the 45 target fields printed `LEFT_QC0 NONE RIGHT_QC0 NONE`. This is a *limited temporal-window statement*, not a claim that all raw tower sensor measurements in the original site are absent or that no useful gridded/other station references exist. QC1 represents selected-source gapfill, **not independent measured tower QC0**.

The contiguous QC2 run lengths refer to the *source of selected F* (ERA-downscaled) and **do NOT** indicate that every QC2 record is physically anomalous. Examples:

- JP-Fjy: flagged PA source run **262,944 HH**.
- JP-Khw: PA source run **385,728 HH**, the full original source product, plus TA run **52,606 HH** and LW_IN run **157,536 HH** for 2005 source anomaly fields.
- JP-Yms: PA source run **325,824 HH**, LW_IN run **232,706 HH**.
- JP-Tef: LW_IN run **315,223 HH**, original README solar/JST uncertainty unchanged.
- JP-Tmd: PA source run **333,072 HH**, the full original source product, plus TA run **10,754 HH** and LW_IN run **11,749 HH** at 2005 source anomalies.

Source SHA256 attestation: JP-Fjy, JP-Khw, JP-Yms original README SHA `fe96facec6fafc57b126e850140152a540a16d97c3bfde8adfa090a3747598f9`; JP-Tef, JP-Tmd original README SHA `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5`. The latter original README states **local solar time**, while operator selected JST UTC+9 as a **diagnostic timestamp hypothesis** only for independent ERA5-Land hour references; no original source clock convention was authoritatively resolved.

## Original operator-generated file locations, on IRIDIS6

Original source field-wise final aggregated read-only artifacts:

```text
/home/ly3n24/japanflux_stage05ax/aggregate_20261103T065006Z/stage05ax_45_original_QC2_native_source_quality_anchor_feasibility_NO_REPAIR.tsv
/home/ly3n24/japanflux_stage05ax/aggregate_20261103T065006Z/stage05ax_45_original_QC2_five_site_QC0_QC1_neighbor_HOLD_summary.json
```

Site-specific supporting files, one `site_results/JP-<site>/` subdirectory each:

```text
/home/ly3n24/japanflux_stage05ax/site_results/JP-Fjy/
/home/ly3n24/japanflux_stage05ax/site_results/JP-Khw/
/home/ly3n24/japanflux_stage05ax/site_results/JP-Yms/
/home/ly3n24/japanflux_stage05ax/site_results/JP-Tef/
/home/ly3n24/japanflux_stage05ax/site_results/JP-Tmd/
```

Each subdirectory contains a `stage05ax_JP_<site>_original_45scope_source_QC2_run_neighbor_readonly.tsv`, a `stage05ax_JP_<site>_original_source_24h_each_side_QC0_QC1_F_MDS_ERA.tsv`, and a `stage05ax_JP_<site>_source_neighbor_science_HOLD.json`. These reports and private source data are stored on IRIDIS6 and **have NOT been copied to GitHub**: GitHub contains reproducible scripts and this operator-confirmed numerical summary.

## Exact science state and next action

- Prior Stages05AL/AT/AU/AV/AW: **45/45** source selected `F=ERA`, `F_QC=2` variable values (35 site-native HH) independently compared with nearby ERA5-Land hourly meteorological context and outside conservative ranges; **22 previously STRONG_CONTEXT**, **23 CONTEXT_ONLY**. These labels are evidence tiers, **not repair approval**.
- Stage05AX: **45/45** original nested FLUXMET_HH neighbor/QC2 source-provenance episode scans successfully completed, all **45** no QC0 bracketing ±24h. Source `F_QC=2` provenance run length is NOT duration of numerical anomalies.
- **0/45** source variable-field replacement values estimated or scientifically approved. All **45** retain original science `HOLD` and there were **no source ZIP, production forcing, model, PFT, Slurm/AD400 modifications**, or new CDS calls during Stage05AX.
- **Stage05AY/next advanced research task:** perform a deeper source-grounded, **READ-ONLY** feasibility audit: examine whether non-QC0 **physically plausible neighboring `F_QC=2` selected F** and independently downloaded ERA5-Land hourly `t2m/sp/strd` can bracket the *short isolated numerical spike*, distinguish shared cross-site downscaling-data corruption versus site-specific effects, validate original-source timebase conflicts, and propose shadow-only candidate repair methods with exact scientific rationale, cross-variable checks, and no automatic forcing edits. Original `QC1`/MDS are gapfilled and cannot be promoted as measured QC0; a long F_QC2 provenance episode must not be naively treated as a long anomalous meteorological interval.

The next model must **not** claim actual 30-minute repairs exist just because 45/45 numerical flags have independent hourly gridded context.
