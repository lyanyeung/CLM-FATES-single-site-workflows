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

Stage10h v1 [original script](../scripts/stage10/10h_original_qc_source_provenance.py) passed its pure self-test but **failed IRIDIS6 read-only input check** before producing a report: `Native source/ERA times differ, duplicate or truncated`. That failure came from v1's unsupported *position-by-position* equality assumption between two independently validated, exact-release source files. Stage09h had verified each file's own timestamp chronology and SHA but not required identical start/end range. **Do not infer that raw files were corrupted from this error**; which site's overlap differs and why remains to be established by the replacement run.

The non-destructive v2 [timestamp-keyed source provenance script](../scripts/stage10/10h_v2_timestamp_keyed_qc_provenance.py) has now **passed IRIDIS6 self-test, read-only check and full audit** on 2026-10-24. It SHA-verifies both source files, checks native cadence independently, joins only exactly matching `TIMESTAMP_START` keys, reports primary-only and ERA-only timestamps, carries unmatched companion ERA evidence as missing (never a row-number substitution or inferred clock shift), and tests these cases with synthetic clock regressions. It will count original TA/VPD QC0/1/2 for all 1,924 source-timestamp-matched blockers over all 32 affected site-years, compare original VPD_F to exact-release companion VPD_ERA at QC2 timestamps, and explicitly show US-NR3 2017/2018/2023 source classes. The script will not repair meteorology or approve DATM/spinup.

**All source/QC reports remain science evidence only. Approval status: 0 replacements, 0 verified clock approvals, Post-v5 not accepted, no CLM-FATES model jobs authorized.**

## Stage10h-v2 verified result (2026-10-24)

A raw-data audit across 7 stations and 32 site-years matched all `1,924/1,924` Stage10d blocker identities to exactly matching primary FLUXMET/FULLSET and companion ERA5 `TIMESTAMP_START` values. **100% of every primary source's native timestamps** occur in the larger companion ERA5 temporal coverage. The original Stage10h-v1 failure reflected its unsupported demand for identical whole-file row counts and spans, **not** corrupted source chronology.

**Original `VPD_F_QC` provenance at the 1,924 events:**

| Site | Events | QC0 measured | QC1 gap-filled | QC2 downscaled ERA |
| --- | ---: | ---: | ---: | ---: |
| US-Kon | 229 | 0 | 25 | 204 |
| US-MMS | 18 | 0 | 0 | 18 |
| US-Me2 | 4 | 0 | 4 | 0 |
| US-Me6 | 1 | 0 | 0 | 1 |
| US-MtB | 15 | 0 | 4 | 11 |
| US-NR1 | 173 | 0 | 25 | 148 |
| US-NR3 | 1,484 | 0 | 0 | 1,484 |
| **Total** | **1,924** | **0** | **58** | **1,866** |

Each of the 1,866 original QC2 VPD values matched the exact-time companion `VPD_ERA` to within 0.01 hPa. No QC0 VPD was found among the selected residual humidity events. The 58 QC1 records are gap-filled, **not** native VPD measurement confirmations.

US-NR3 in **2017, 2018 and 2023**: for each year, all 17,520 native half-hours of `TA_F` and `VPD_F` were source-labeled QC2 (ERA-downscaled); zero were QC0 or QC1. This does not establish the root algorithmic cause or prove independent atmospheric observations were entirely unavailable.

Stage10h-v2 exact result report (not stored in GitHub):

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage10h_original_source_provenance_20261024T054425Z_faf342a8/`

Latest run: `event_join=1924/1924 affected_site_years=32/32 VPD_QC2_at_blockers=1866/1924 exact_companion_ERA_event_matches=1924/1924 missing_exact_ERA_events=0/1924 all_offsets_approved=0 repairs_approved=0`.

**Scientifically important preexisting result:** Stage08c calculated `ERA_RH_pct` from the *paired* `TA_ERA_C` and `VPD_ERA_hPa` using liquid-water saturation. All 1,924 residuals were classified as `ERA_RH_BELOW_MINUS2_PCT`, so the inconsistency is already present under the paired companion ERA-derived quantities: this is not necessarily an artefact of mixing ERA VPD with tower retained air temperature. This algebraic result does **not** identify the faulty stage of source generation or justify RH/VPD clipping.

### Stage10i — VERIFIED ERA source temperature/VPD inconsistency

[Stage10i source ERA VPD vs saturation audit](../scripts/stage10/10i_source_ERA_vpd_saturation_audit.py) subsequently **passed IRIDIS6** `--self-test`, `--check` and `--run`. It independently reproduced Stage08c's `ERA_RH_pct` for all 1,924/1,924 events, with every event satisfying `VPD_ERA > es_water(TA_ERA)`: source-pair implied water vapour pressure was negative in 1,924/1,924 events. Original `VPD_F_QC2` accounted for 1,866 events and matched original companion `VPD_ERA` within 0.01 hPa. No clock/repair approvals were given.

| Site | Events | Median ERA-derived water RH (%) | Median source VPD above es_water(T) (hPa) | Maximum overage (hPa) |
| --- | ---: | ---: | ---: | ---: |
| US-Kon | 229 | -10.599 | 0.205305 | 0.696663 |
| US-MMS | 18 | -13.049 | 0.150566 | 0.342470 |
| US-Me2 | 4 | -3.694 | 0.153912 | 0.167077 |
| US-Me6 | 1 | -3.827 | 0.033836 | 0.033836 |
| US-MtB | 15 | -8.279 | 0.256513 | 0.427115 |
| US-NR1 | 173 | -10.111 | 0.203790 | 0.678531 |
| US-NR3 | 1,484 | -13.699 | 0.186228 | 0.889337 |

**Scientific interpretation:** The negative implied vapour pressure occurs using the paired `TA_ERA` and `VPD_ERA` from the source companion, without tower retained temperature. This does NOT establish that actual atmospheric vapour pressure was negative or which source downscaling algorithm introduced the algebraic inconsistency. The official [FLUXNET FULLSET specification](https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/) identifies downscaled, linearly regressed `VPD_ERA` and the consolidated `VPD_F`; independently regressed variables can lose joint physical consistency, but that is a hypothesis, **not yet a demonstrated root cause**. The reanalysis product behind each site's exact release must not be assumed identical to the separately requested ERA5-Land evidence.

US-Me2's retained/original FLUXMET T was 9.533 C colder than source `TA_ERA` at the median of its four events, so it needs special metadata/height/clock investigation in addition to the common source-pair inconsistency.

Stage10i results retained on IRIDIS6:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage10i_era_vpd_physics_20261024T055509Z_b5a44de8/`

Next proposed diagnostic (code committed, **not yet executed on IRIDIS6**): [Stage10j source-versus-grid counterfactual](../scripts/stage10/10j_source_vs_grid_humidity_counterfactuals.py). This will contrast existing original ERA temperature/VPD with existing SHA-pinned ERA5-Land gridded T/dewpoint evidence at identical 1,924 event IDs, without any new meteorological download or repair. A single-input mathematical substitution is a diagnostic sensitivity **only**, not a valid repair recommendation.


### Stage10j — VERIFIED source vs ERA5-Land counterfactuals

Stage10j [script](../scripts/stage10/10j_source_vs_grid_humidity_counterfactuals.py) passed IRIDIS6 `--self-test`, `--check` and `--run` on 2026-10-24. All 1,924 events and 32 site-years matched the existing SHA-pinned Stage10b (ERA5-Land T/Tdew) and Stage10i (source ERA temperature/VPD) reports. The original source `e_a=es_water(TA_ERA)-VPD_ERA` was negative for all 1,924; grid-derived dewpoint vapour pressure was positive for all 1,924. This is a **cross-reanalysis algebraic sensitivity**, not an independent observation of local humidity.

Mutually exclusive source/grid single-variable counterfactual results:

| Stage10j category | Count | Description |
| --- | ---: | --- |
| GRID_VPD_ONLY_REMOVES_NEGATIVE_EA | 1,736 | Substitute only ERA5-Land dewpoint-derived grid VPD at original source T; nonnegative implied vapour pressure |
| BOTH_SINGLE_INPUT_SWAPS_REMOVE_NEGATIVE_EA | 186 | Either grid VPD alone or grid T alone eliminates negative implied vapour pressure |
| GRID_T_ONLY_REMOVES_NEGATIVE_EA | **2** | Only grid T changes the sign; both exceptions were from **US-NR3** |
| NEITHER_SINGLE_INPUT_SWAP_REMOVES_NEGATIVE_EA | 0 | Neither swap changes sign |

Overall **1,922/1,924 = 99.90%** get nonnegative implied water vapour pressure under the VPD-only numerical counterfactual; only **188/1,924 = 9.77%** under the temperature-only one. **These are not approved replacement percentages.** FLUXNET source ERA and ERA5-Land are related, and replacing a VPD estimated at one 2m temperature with a grid VPD while retaining another temperature is not a thermodynamically validated prescription.

Stage10j report (kept on IRIDIS6):

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage10j_ERA_counterfactuals_20261024T060351Z_eddc1a32/`

Next code prepared, **not yet run against IRIDIS6 data**: [Stage10k exception provenance / science-gate check](../scripts/stage10/10k_exception_provenance_science_gate.py). It verifies the Stage10j SHA receipt, explicitly lists both US-NR3 exceptional event IDs, summarizes QC2/QC1 source provenance, and makes no forcing or approval changes.

**Current approvals:** humidity repairs 0; UTC offsets 0; Post-v5 acceptance 0; CLM-FATES spinups 0.
