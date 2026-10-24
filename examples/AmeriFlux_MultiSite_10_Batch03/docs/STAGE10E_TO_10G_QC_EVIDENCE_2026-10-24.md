# AmeriFlux Batch03 — Stage10e to Stage10g raw QC evidence (2026-10-24)

**Status:** Operator-run, checksum-backed science diagnostics; no forcing repair approved.  
**Scope:** The 89 P0/P1 records from the Stage10d 1,924-event review, grouped into 19 of the 183 native-contiguous clusters.  
**Important:** Results below were transcribed from user-supplied IRIDIS6 logs; full original CSVs, source files and per-event receipts remain on IRIDIS6, not in this GitHub document.

## Stage10e — original meteorology in the +/- 6 hour window

Script: [10e_priority_event_flanking_context.py](../scripts/stage10/10e_priority_event_flanking_context.py)

Stage10e matched all 89 P0/P1 events in 19 source-time clusters (4 stations), SHA-verified original native primary CSVs, and extracted 773 rows of original meteorology across the +/-6h windows.

| Site | P0 | P1 | Clusters | Stage10e both 6h flanks with VPD-only QC0 |
| --- | ---: | ---: | ---: | ---: |
| US-MMS | 0 | 1 | 1 | 0 |
| US-Me2 | 4 | 0 | 1 | 0 |
| US-MtB | 1 | 0 | 1 | 0 |
| US-NR3 | 26 | 57 | 16 | 0 |
| **Total** | **31** | **58** | **19** | **0** |

**Correction:** The original Stage10e `raw_valid_QC0_pair` checks the VPD source QC=0 plus numeric TA/VPD plausibility, **not** TA and VPD QC=0 jointly. This imprecise label was identified and corrected conceptually by Stage10f; Stage10e historical results are preserved unchanged.

Stage10e report:  
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage10e_priority_flank_context_20261024T043136Z_557ade35`

## Stage10f — actual dual TA_F_QC=0 and VPD_F_QC=0

Script: [10f_dual_qc0_24h_context.py](../scripts/stage10/10f_dual_qc0_24h_context.py)

| Site | Clusters | Both-side dual QC0 within 6h | Both-side within 24h | At least one side within 24h |
| --- | ---: | ---: | ---: | ---: |
| US-MMS | 1 | 0 | 0 | 0 |
| US-Me2 | 1 | 0 | 1 | 1 |
| US-MtB | 1 | 0 | 0 | 1 |
| US-NR3 | 16 | 0 | 0 | 0 |
| **Total** | **19** | **0** | **1** | **2** |

Stage10f read-only and report runs passed `89/89` event identities, `19/19` cluster checks, 0 repair approvals.

Stage10f report:  
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage10f_dual_qc0_24h_20261024T043720Z_8df51a8c`

## Stage10g-v2.1 — affected year source QC0 and 24h/72h/7d flanks

Successful version: [10g_v2_source_qc0_gap_audit.py](../scripts/stage10/10g_v2_source_qc0_gap_audit.py). Legacy Stage10g and the initial self-test versions had software errors; v2.1 passed SHA verification, self-test, full `--check` and `--run`. Do not treat the failed attempts as science checks.

| Site | Clusters | Both 24h | Both 72h | Both 7 days | Any side 7 days |
| --- | ---: | ---: | ---: | ---: | ---: |
| US-MMS | 1 | 0 | 0 | 0 | 0 |
| US-Me2 | 1 | 1 | 1 | 1 | 1 |
| US-MtB | 1 | 0 | 0 | 1 | 1 |
| US-NR3 | 16 | 0 | 0 | 0 | 0 |
| **Total** | **19** | **1** | **1** | **2** | **2** |

### US-NR3 full-year source quality in affected years

All years below have 17,520 native half-hour records. The `physically_valid_and_dual_QC0` count requires TA and VPD source QC0 simultaneously **and** basic water-based physical plausibility.

| Year | TA_F_QC0 | VPD_F_QC0 | Physically valid TA/VPD | Physically valid and dual-QC0 | Dual QC0 fraction |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2007 | 8,899 | 8,890 | 17,341 | 8,890 | 50.742% |
| 2017 | **0** | **0** | 17,366 | **0** | **0%** |
| 2018 | **0** | **0** | 17,237 | **0** | **0%** |
| 2019 | 5,878 | 5,857 | 17,231 | 5,857 | 33.430% |
| 2022 | 3,794 | 3,789 | 17,181 | 3,789 | 21.626% |
| 2023 | **0** | **0** | 17,355 | **0** | **0%** |

The complete Stage10g run reported `events=89/89 clusters=19/19 both_24h=1/19 both_72h=1/19 both_7d=2/19 any_7d=2/19 scientific_repair_approvals=0`.

Stage10g report:  
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage10g_source_qc0_7day_20261024T045334Z_691519c6`

### Correct scientific interpretation

The official FLUXNET FULLSET product specifications state that for native HH/HR `TA_F_QC` and `VPD_F_QC`, class **0** is measured, class **1** is good-quality gapfill, and class **2** is downscaled from ERA. For `*_F_MDS_QC`, classes 0/1/2/3 mean measured/good/medium/poor, respectively. [FLUXNET official FULLSET variables](https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/); [variables quick guide](https://fluxnet.org/data/fluxnet2015-dataset/variables-quick-start-guide/).

The absent QC0 at US-NR3 for the whole of 2017, 2018 and 2023 means there are **no TA_F or VPD_F values labeled measured in those released products for those years**. It does not mean missing numeric values or automatically demonstrate a continuous instrument failure. **The next essential step is to count QC1 versus QC2 and inspect the product's recorded source**, rather than seek more distant interpolation anchors. ERA5-Land and FLUXNET ERA-derived fields are not wholly independent; physically plausible humidity does not by itself establish accuracy. The 7-day flanking diagnostic does not authorize 7-day interpolation.

The other affected years and sites can have high annual QC0 coverage yet no QC0 near specific winter episodes. Annual coverage must not be substituted for local event provenance or QC.

## Stage10h — source provenance next step, not yet run

Script committed: [10h_original_qc_source_provenance.py](../scripts/stage10/10h_original_qc_source_provenance.py). It is **awaiting operator's IRIDIS6 verification**. It will count original TA/VPD QC0/1/2 for all 1,924 source-timestamp-matched blockers over all 32 affected site-years, compare original VPD_F to exact-release companion VPD_ERA at QC2 timestamps, and explicitly show US-NR3 2017/2018/2023 source classes. The script will not repair meteorology or approve DATM/spinup.

**All source/QC reports remain science evidence only. Approval status: 0 replacements, 0 verified clock approvals, Post-v5 not accepted, no CLM-FATES model jobs authorized.**
