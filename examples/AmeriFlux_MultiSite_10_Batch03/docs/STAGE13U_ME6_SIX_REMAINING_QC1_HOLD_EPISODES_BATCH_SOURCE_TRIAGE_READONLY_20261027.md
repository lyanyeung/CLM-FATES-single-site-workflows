# Batch03 US-Me6 Stage13u — batch-first scientific review of six remaining full original QC1 runs

## ACTUAL IRIDIS6 Stage13u read-only source review PASS — 2026-10-27 07:47 UTC

The operator ran the fixed SHA-pinned Stage13u mobile runner on `login6001`. `--self-test`, `--check`, `--run` **PASS**. Original tower, paired ERA, Stage13r, successful Stage13s 280,320-row source and Stage13t original signed receipts verified and preserved; no forcing or model modified. New signed **read-only source triage report**:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13u_Me6_six_held_source_QC1_runs_BATCH_SCIENCE_ONLY_20261027T074748Z_9e23952f`

| Original Stage13r held full-run ID | Original QC1 native HH | Original measured tower QC0 TA preserved | Original paired ERA RH/QBOT + T source physics PASS | Direct original measured VPD QC0 boundaries | ERA candidate max adjacent VPD jump (hPa) |
|---|---:|---:|---:|---|---:|
| 12 (2015 Sep26) | 4 | 4 | 4 | YES on both sides | 4.800355; 2 failing edges |
| 14 (2015 Nov) | 469 | 469 | **464, five HOLD** | YES on both sides | 2.512215 (screen only; five interior source holds) |
| 15 (2017 Jun) | 95 | 95 | **87, eight HOLD** | NO (both direct QC2) | 5.741840; 2 failing edges |
| 16 (2017 Jun–Jul) | 30 | 30 | 30 | NO (both direct QC2) | 4.489297; 2 failing edges |
| 17 (2017 Jul) | 137 | 137 | **136, one HOLD** | NO (both direct QC2) | 4.190815; 1 failing edge; five original approved Stage12ac July04 records stay protected |
| 18 (2017 Jul) | 47 | 47 | 47 | NO (both direct QC2) | 6.552221; 4 failing edges |
| **Total** | **782** | **782** | **768; 14 HOLD** | **2/6 groups** | Not a licence to relax the original 4 hPa boundary rule |

Other exact audit status: 16 earlier method-reviewed original QC1 centers and 5 separately user-approved 2017 Stage12ac rows are preserved; **761 other QC1 neighbors are NOT authorized**. Source SHA checks passed for original FLUXMET `721d87464c70ea38c7ab6206deee6953647709072cde33827a825408970971e0`, native companion ERA `af2be6dce8b9d1310540f29b3a87d57fbac4da7d2f8192434e93217e5079f98f`, successful Stage13s candidate `02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565` and Stage13t receipt `66022e2df1f317c7de94b21ed56a564424292336a30e3f94d9f3486c1fdc3631`.

**Scientific conclusion:** 2015 Nov469 QC1 source run has five physic/QBOT exceptions within an otherwise plausible paired original ERA-RH background. Max adjacent VPD of 2.512215 hPa is insufficient to approve the whole run, since five points failed physics; no ten-day blanket interpolation. Four original 2017 source run boundaries are **QC2**, and distant original measured QC0 references (17/233; 113/202; 151/57; 296/2 HH for nearest external QC0) do NOT amount to two immediate observed anchors. All 6 remain HOLD. Do not overwrite 2017 Stage12ac prior five. Next should isolate the **fourteen individual source physics failures and valid contiguous QC1 sub-episodes in a single batch source-science diagnostic**, not request 782 individual votes. Operator explicitly prefers batch repairs and permits later grouped requests for scientific decisions.

**2026-10-27 Stage13u initial IRIDIS6 FAIL-CLOSED SCRIPT BUG, now FIXED IN GITHUB, re-run PENDING:** Operator ran pinned old Stage13u initial mobile SHA checks and `--self-test` PASS on `login6001`, but before any full source audit it stopped with `AttributeError: 'Series' object has no attribute 'month'` in `forcing()` at old source line 121. Root cause: `pd.to_datetime(Series)` returns a **Series**, whose month and day accessors require `.dt`; corrected version explicitly constructs `pd.DatetimeIndex` before `.month` / `.day` and chronological/unique/NOLEAP gates. Added source-free regression selftests for timestamps, leap day and duplicate native time. Main fixed Git blob `aeaa3ce78e32d17ace2f356a660447e3c51e1b77`; fixed phone launcher Git blob `156388dc2f8d2a2e97ee1a11c1d2a3f52173fe16` pinned to commit `dd60db82dfa91f578632f810aca946558225efd7`. **Original 6 source HOLD groups and all original Stage13s successful forcing untouched; old failure was a Python indexing defect, NOT a scientific failure, and no Stage13u read-only result exists until corrected IRIDIS6 execution.** No DATM/Slurm submitted.

## Actual Stage13s and Stage13t state (verified on IRIDIS6)

- Stage13s (2026-10-27 06:50 UTC) actual signed `--check` + `--apply` **PASS** on previously user-approved **12 full original 2015 QC1 runs = 235 native HH**. Final new independent **280320-row** Me6 site research-only candidate `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage13s_Me6_12x2015_235HH_ERA_RH_operator_approved_20261027T065056Z_6890a105`; **214 VPD_USE + 214 QBOT actual source numeric changes**, with **18 previously blank native humidity values newly filled**, 2017 July04 5 earlier operator-approved records immutable, other source runs held; no model jobs.
- Stage13t (2026-10-27 07:12 UTC) actual signed `--check` + `--run` **PASS but original 2015-Sep26 4HH run stays HOLD**, untouched. Measured original tower VPD QC0 at 04:30 **5.413hPa** and 07:00 **6.468hPa**. Paired original companion ERA RH-at-retained-tower-T inside 05:00/05:30/06:00/06:30 gives VPD **1.410641/1.476824/1.567620/1.667645hPa**, creating two abrupt measured-QC0 transitions **4.002359** and **4.800355 hPa** >4hPa. Small QC0-to-QC0 **linear diagnostic** has per-step 0.211hPa but is **NOT independent evidence of actual tower humidity, NOT scientifically approved**.
- Signed actual Stage13t evidence directory `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13t_Me6_20150926_four_QC1_original_QC0_ERA_RH_READONLY_20261027T071247Z_a30c3a4e`.

## User strategy: prefer BATCH repairs and ask for HUMAN grouped science signoff

The user stated, **“后面如果需要人工审核的可以问我，优先批量修复”**. Therefore **do NOT seek single-event operator permission for just the four Sep26 timestamps** now. The remaining complete Stage13r original site source VPD QC1 full runs are **6** and total **782 native HH**:

| Original Stage13r source run | Source original QC1 dates | Native source QC1 HH | Old method-reviewed centers | Existing July2017 Stage12ac protected | OTHER QC1 native neighbors unapproved |
| --- | --- | ---: | ---: | ---: | ---: |
| 12 | 2015-09-26 05:00–06:30 | 4 | 1 | 0 | 3 |
| 14 | 2015-11-04 13:00–2015-11-14 07:00 | 469 | 2 | 0 | 467 |
| 15 | 2017-06-28 17:00–2017-06-30 16:00 | 95 | 3 | 0 | 92 |
| 16 | 2017-06-30 17:00–2017-07-01 07:30 | 30 | 1 | 0 | 29 |
| 17 | 2017-07-01 12:00–2017-07-04 08:00 | 137 | 6 | **5** | 126 |
| 18 | 2017-07-04 12:30–2017-07-05 11:30 | 47 | 3 | 0 | 44 |
| **TOTAL** |  | **782** | **16** | **5** | **761** |

The original 12 passed 2015 source runs are **not reopened**. The 469HH November 2015 run cannot be interpolated blindly across ~10 days; four 2017 QC1 episodes lack measured source QC0 anchors at both immediate boundaries, and 2017 run17 overlaps five **already approved Stage12ac** source native slots. No broad overwrite permission for the 761 extra QC1 neighboring records. The protected five Stage12ac records remain numerically identical.

## Stage13u scientific BATCH triage implementation

[Stage13u read-only six-run source audit](../scripts/stage13/13u_Me6_remaining_six_full_original_QC1_runs_BATCH_TRIAGE_READONLY.py) and [one-copy phone launcher](../scripts/stage13/13u_Me6_mobile_batch_one_click_READONLY.sh).

The batch script SHA-locks:
1. Historical original Stage13r full run source module Git blob `5a8dc69f5fb65015a9b7c9096153935684f466a8`, and existing signed Stage13q/Stage12ac original tower/ERA site input manifest.
2. Actual Stage13r SHA-receipted original 18-run QC1 report, keeping all 12 PASS runs untouched and **exact 6 held runs / 782 QC1 native rows**.
3. Actual successful Stage13s complete original 280320-row **research-only** CSV and signed SHA receipt, and ensures old five Stage12ac 2017 native rows remain unchanged.
4. Actual Stage13t SHA-sealed original 2015 Sep26 source QC0 edge diagnosis and no scientific repair approval.

It then reads **all original source-native 2015+2017 tower and paired FLUXNET ERA records** and evaluates each of the remaining **782 QC1 timestamps**: original VPD QC1, measured TA QC0 vs retained site T, original ERA RH/QBOT at retained T and PSRF, original Stage13s model humidity held vs finite, seven/whole source VPD edge continuity including existing 2017 corrections. For each full held run, gives immediate left/right original VPD QC (QC0/QC2), nearest actually measured original VPD QC0 on either side within a 14-day search window (nearest far QC0 **is not a valid immediate bracket**), ERA-derived whole run transition screen and counts of physically valid source intervals. The original Sep26 tiny four-source-HH event additionally reports optional **NOT APPROVED** QC0-to-QC0 linear VPD interpolation feasibility and water QBOT checks, with measured QC0 boundaries fixed.

Outputs: **six-row batch grouped scientific criteria** + **782-row per-native source ledger** + signed hashes, to one NEW `reports/stage13u_Me6_six_held_source_QC1_runs_BATCH_SCIENCE_ONLY_*` directory. Every output is a read-only scientific research *report*, never a source forcing or DATM file.

**No Stage13u HPC execution yet:** GitHub script and phone launcher are committed but cannot be presumed to have actually checked source records until user runs them. After actual Stage13u scientific evidence returns, propose the **few scientifically defensible subsets and methods** for **one grouped operator decision**, not 782 independent votes and not blanket approval of a large QC1 segment. For any missing true QC0 anchors, extra source temperature provenance failures, 4hPa continuity failures, or weak interpolation at long durations, retain scientific HOLD unless a stronger external reference and explicit human science method approval is obtained.

Original tower/ERA, Stage12ac original, successfully patched Stage13s, US-Kon, US-NR1, site surface/PFT/ZBOT, CIME/DATM, AD400/Normal400 and Slurm remain unchanged.
