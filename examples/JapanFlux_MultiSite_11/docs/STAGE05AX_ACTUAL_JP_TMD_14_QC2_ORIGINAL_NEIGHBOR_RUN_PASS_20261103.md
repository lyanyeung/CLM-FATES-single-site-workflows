# JapanFlux Stage05AX — ACTUAL JP-Tmd original QC0/QC1 native neighbor audit PASS (2026-11-03)

## Exact operator-executed read-only evidence

The user ran [Stage05AX](../scripts/stage05/05ax_45_original_JPF_QC0_QC1_neighbor_and_QC2_run_READONLY.py), pinned Git blob `7cc202ff9a15fd4f78bba84d33cf65faeb4b3e07` (numeric str/float and original Stage05K README SHA validation corrected), using actual Stage05AW 45-field original QC2 ledger and actual Stage05K original source README metadata. Syntax and self-test PASS. JP-Tmd original source nested JPF release scanned completely (333,072 original FLUXMET_HH records), exact original README SHA `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5` matches Stage05K, **14 original selected F=embedded ERA QC2 variable fields at 10 distinct native half-hours** matched. No original source/forcing changes, CDS requests, or Slurm jobs.

```text
STAGE05AX SELF-TEST PASS | source 45 QC2 fields, nearest genuine QC0 vs QC1 gapfill, full original QC2 run, 24h each side; NO NETWORK/WRITES
STAGE05AX ORIGINAL_SOURCE_QC0_QC1_NEIGHBOR_REVIEW_PASS JP-Tmd FIELDS 14 NATIVE_TIMES 10
SOURCE_HH_ROWS_SCANNED 333072 README_SHA256 17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5
FULL_SOURCE_QC2_RUN_MAX_HH 333072
TEMPORAL_BRACKET_SCREEN_ONLY {'LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED': 14}
EVENT 200508120200 LW_IN QC2_RUN_HH 11749 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
EVENT 200508120230 LW_IN QC2_RUN_HH 11749 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
EVENT 200508120230 PA QC2_RUN_HH 333072 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
EVENT 200508120230 TA QC2_RUN_HH 10754 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
EVENT 200508120300 PA QC2_RUN_HH 333072 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
EVENT 200508120300 TA QC2_RUN_HH 10754 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
EVENT 200508120330 PA QC2_RUN_HH 333072 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
EVENT 200508120330 TA QC2_RUN_HH 10754 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
EVENT 201112170630 PA QC2_RUN_HH 333072 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
EVENT 201112170700 PA QC2_RUN_HH 333072 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
EVENT 201112170730 PA QC2_RUN_HH 333072 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
EVENT 202204090230 PA QC2_RUN_HH 333072 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
EVENT 202204090300 PA QC2_RUN_HH 333072 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
EVENT 202204090330 PA QC2_RUN_HH 333072 LEFT_QC0 NONE RIGHT_QC0 NONE SCREEN LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED
SOURCE_NEIGHBOR_EVENT_TABLE /home/ly3n24/japanflux_stage05ax/site_results/JP-Tmd/stage05ax_JP_Tmd_original_45scope_source_QC2_run_neighbor_readonly.tsv
SOURCE_24H_CONTEXT_TABLE /home/ly3n24/japanflux_stage05ax/site_results/JP-Tmd/stage05ax_JP_Tmd_original_source_24h_each_side_QC0_QC1_F_MDS_ERA.tsv
ORIGINAL_SCIENCE_HOLD_REPORT /home/ly3n24/japanflux_stage05ax/site_results/JP-Tmd/stage05ax_JP_Tmd_source_neighbor_science_HOLD.json
NO_REPAIR_VALUES/NO_CDS/NO_ORIGINAL_SOURCE_OR_FORCING_WRITES/NO_SLURM_ALL_45_HOLD
```

## Science interpretation — product selected-field QC2 run is **NOT** a physical-anomaly episode

- **JP-Tmd PA_F_QC=2 across every one of the 333,072 original source halfhours.** This indicates *the selected PA_F variable throughout this original FLUXNET release relies on source ERA downscaling* (product QC class 2); it **does not** mean that PA was physically impossible across the entire record. The exact previously flagged six? original PA source physical outliers remain the isolated 2005, 2011, and 2022 events. (For JP-Tmd 2005 3 +2011 3+2022 3 = **9 flagged original PA fields**, not six.)
- For the flagged August 2005 selected-source TA_F records, the original surrounding QC2 run spans **10,754 halfhours** (all three same run); for selected LW_IN_F it spans **11,749 halfhours** (two same run). **These are durations of QC2 source *provenance class*** and not proof that the numerical source anomaly persists throughout those intervals.
- All **14/14 original flagged QC2 variable fields** lack a measured QC0 same-variable temporal anchor on either side **within ±24 hours**; all are in `LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED`. Thus **native tower-measured QC0-to-QC0 short-gap linear interpolation is unsupported on the examined ±24h scope**. No statement is made about whether QC0 observations exist *elsewhere*, or whether raw flux tower sensor measurements not represented as selected F_QC=0 are available outside this product.
- Optional original `*_F_MDS` and `*_F_MDS_QC` field presence and actual nearest QC1 details are in the operator-created source neighbor TSV and event TSV, not inferable from this printed run log alone. QC1 means source-product gapfill, not independently measured tower data.
- The original JP-Tmd README explicitly says local solar time, while user selected JST UTC+9 for **diagnostic** external ERA5-Land comparisons. Original native timestamps are untouched; no definitive source timebase proof from this result.
- Original Stage05AW scientific state unchanged: **45/45** original selected F=downscaled ERA QC2 physical outliers already independently contextualized with ERA5-Land hourly data (22 prior strong-context, 23 context-only), **all 45 source fields SCIENCE HOLD, 0 approved replacements**.

## Next Stage05AX

Run the same corrected SHA-pinned Stage05AX for the other **four** source sites: JP-Fjy6, JP-Khw11, JP-Yms10, JP-Tef4, each with `--stage05k-dir "$HOME/japanflux_stage05k"`, `--manifest .../sites.tsv`, and identical actual Stage05AW field TSV / summary. Each one-site output must live under `$HOME/japanflux_stage05ax/site_results/JP-<site>`; no auto-overwrite/re-download. Then invoke `--aggregate --site-results-root $HOME/japanflux_stage05ax/site_results --out-dir <new directory>`, which will reconcile exactly **45/45** native source QC2 neighbor reports over **35** distinct station×native HH, with per-variable and per-site class checks.

Only after actual five-site aggregate PASS should a subsequent Stage05AY evaluate possible shadow repair methods. For JP-Tmd, the absence of nearby QC0 bracketing means ordinary local QC0 linear interpolation is **not** a defensible automatic method. Any external/hourly ERA5-Land based alternative must remain an explicitly source-constrained hypothetical model and obey local-solar vs JST provenance uncertainty and adjacent-variable physical consistency.
