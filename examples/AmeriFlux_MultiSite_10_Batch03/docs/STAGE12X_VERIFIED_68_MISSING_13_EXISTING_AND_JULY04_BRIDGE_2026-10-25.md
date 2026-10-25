# Batch03 Stage12x VERIFIED — 68 Stage12g missing, 13 Stage12g first-finite differences, one isolated candidate-pass

**Operator result on IRIDIS6 2026-10-25 19:35 UTC:** pinned Stage12x v2 source Git SHA, Python syntax, `--self-test`, `--check`, and `--run` ALL PASS. Isolated SHA-receipted, source-only forensic output directory:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12x_68missing_13historic_finite_stage12w_cross_candidate_20261025T193514Z_fc1729a4/`

This is not production forcing. All 86 previously signed held source-event T/VPD records, the older separate 233 physical science holds, original QC0 tower temperature, site pressure, native source clocks and Post-v5/DATM/CIME/spinup prohibitions remain unchanged.

## Exact Stage12x source-provenance reconciliation

| Stage12w hypothetical original native companion ERA-RH class | Stage12g still missing | Stage12g already finite |
| --- | ---: | ---: |
| Paired ERA air temperature differs >5C from tower | 32 | 12 |
| Trial source candidate >4 hPa jump to available Stage12g neighbor | 35 | 1 |
| Trial passes Stage12w immediate available neighbor screen, not approved | **1** | 274 (outside Stage12x 81 flagged) |
| **Total** | **68** | **13 warning-group** |

Stage12x checked **all 81** exceptional original native source timestamps against each SHA-sealed Stage12c/d/e/g shadow and original original Stage12d, Stage12e, and Stage12g hold ledgers. All 68 missing records have signed D/E/G historical HOLD entries (68/68). All 13 historical-finite warning-group records **first became finite in Stage12g**, not in C, D or E, and have no historical G missing-year ledger row. This is a source provenance fact, **not** an approval of either the historical Stage12g grid-based product or the new Stage12w hypothetical original companion RH replacement.

For the **13 already-finite Stage12g warnings**, all are US-Me6, 12 for alternative original companion ERA T difference >5C and one for new original-companion hypothetical VPD jump >4hPa. Their new original-companion candidate differs from the untouched Stage12g gridded historical result at the same original timestamp. Stage12x printed values and signs of all 13, preserving the historical references. Automatic overwrite/deletion is prohibited.

## The single Stage12w screen-pass yet Stage12g missing

- **US-Me6, original native 2017-07-04 07:00**, `native_key=201707040700`
- Hypothetical original companion ERA-RH VPD at retained tower T = **5.154795 hPa**, QBOT = **0.008275 kg/kg**
- All actual Stage12c, D, E, G VPD at this native key are **MISSING**, not finite.
- Stage12d original historical reason = `NEW_EDGE_JUMP_GT4HPA_HOLD`
- Stage12e original historical reason = `NO_VERIFIED_ERA5LAND_SOURCE_FOR_SITE_YEAR`
- Stage12g original historical reason = `HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA`
- Nearest finite Stage12g historical prior VPD: **3.974495 hPa 30min before** (2017-07-04 06:30).
- Nearest finite Stage12g historical later VPD: **21.391 hPa 60min after** (2017-07-04 08:00).
- Historical Stage12g has **22 other finite native half-hours in the exact +/-6h window**.
- The hypothetical 07:00 value differs by only 1.180300 hPa from 06:30 but by 16.236205 hPa from the *non-adjacent* 08:00 reading. **Never count the latter as an immediate 30min jump**; instead inspect the intervening 07:30 record, its original source, uncertainty and scientific source provenance to assess whether both 30min transitions can be physically continuous under a consistent method.
- This is the reason a provisional Stage12w immediate-available-edge pass can coexist with an older historical Stage12g 4hPa HOLD. The screening method and neighbor availability differ.

The priority next step is to reconcile exact original signed Stage12g gridded repair ledger for the 13 already-finite values, inspect complete 06:30–08:00 original-native *four-point bridge* around 07:00 with original sources and Stage12w hypothetical companion ERA-RH candidates at both missing keys (07:00, 07:30 where available), without applying any patch. Require ice/water closure, matched source T, 5C T mismatch, and the original 4 hPa **half-hour** adjacent edge rule for any proposed numerical candidate sequence. Only a signed science report may be produced; source, forcing and original research shadows stay unchanged.

## Stage12y next step (source committed, not yet IRIDIS6-tested)

Pinned revision `460d724532f85a0c2eb27d033f64c52332f5bb76`, Git blob `0743c5d2bbb5e33d52da9929a7c4674d013f322d`: [Stage12y original grid provenance and 07:00/07:30 pairwise bridge science-only script](../scripts/stage12/12y_Me6_July04_two_gap_bridge_and_13_G_grid_provenance_READONLY.py). Stage12y validates the 13 existing Stage12g gridded native VPD against the signed Stage12g `new_ERA5Land_year_source_RH_repair_candidates.csv` and corresponding pressure, gridded humidity and unapproved source-clock metadata. It separately checks source-native original 2017-07-04 06:30, 07:00, 07:30, 08:00, the 07:00 and 07:30 signed science-hold reasons, and each of the **three** 30-minute hypothetical transitions. It remains scientifically **unexecuted**, and even if it passes its tests it will make no repairs or authorise an incomplete DATM/spinup forcing.
