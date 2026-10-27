# US-Me6 Stage13r: actual IRIDIS6 full original QC1 source-run scientific review — 2026-10-27 00:40 UTC

**Original operator terminal output verifies Stage13r `--check` and `--run` PASS**, SHA-verified original Stage13q receipts and Stage12ac forcing source. New SHA-sealed **READ-ONLY source report**:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13r_Me6_original_full_QC1_run_and_original_QC0_ERA_RH_READONLY_20261027T004033Z_5eefea7b`

The original 33 manually reviewed VPD QC1 Me6 center records are included across 18 **maximal consecutive original-source VPD_F_QC1** sequences. Correct figures: **12/18** complete original QC1 runs passed all *Stage13r preview* source gates (original source VPD QC0 both bookends, measured tower TA, paired original ERA RH/QBOT physics and <=4hPa all 30min VPD transitions); **6/18** runs remain source HOLD. *No forcing was generated in Stage13r, and no new QC1 neighbor has operator authority.* Stage13q earlier established the 33 *individual* positions had correct source physics but none of 31 isolated subgroups had valid old neighbor transitions.

## Twelve candidate complete runs — **proposal only: requires operator scope expansion**

| Stage13r run | Full original source QC1 native range | QC1 halfhours | Previously method-approved source centers | **New QC1 neighbors needing approval** | Max full-run VPD step hPa |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 | 2015-06-03 01:30 – 05:30 | 9 | 1 | 8 | 1.357435 |
| 2 | 2015-07-27 02:30 – 05:30 | 7 | 1 | 6 | 2.434734 |
| 3 | 2015-08-29 17:00 – 2015-08-30 10:00 | 35 | 3 | 32 | 2.999654 |
| 4 | 2015-08-30 16:30 – 2015-08-31 06:00 | 28 | 1 | 27 | 1.069926 |
| 5 | 2015-09-02 05:00 – 06:30 | 4 | 1 | 3 | 1.621207 |
| 6 | 2015-09-02 21:30 – 2015-09-03 06:00 | 18 | 1 | 17 | 0.410787 |
| 7 | 2015-09-04 20:00 – 2015-09-05 06:00 | 21 | 1 | 20 | 1.583328 |
| 8 | 2015-09-14 23:00 – 2015-09-15 06:00 | 15 | 1 | 14 | 0.841656 |
| 9 | 2015-09-15 15:30 – 2015-09-16 06:00 | 30 | 1 | 29 | 0.790999 |
| 10 | 2015-09-16 16:30 – 2015-09-17 07:30 | 31 | 2 | 29 | 1.935307 |
| 11 | 2015-09-17 16:00 – 2015-09-18 06:00 | 29 | 2 | 27 | 1.521027 |
| 13 | 2015-10-03 08:30 – 12:00 | 8 | 2 | 6 | 0.258650 |
| **TOTAL** | **12 source QC1 runs, all 2015** | **235** | **17** | **218** | **max 2.999654** |

These 235 native times do not receive automatic authorization from earlier 33-center method approval. **The new additional 218 original VPD_F_QC1 times require one explicit grouped user decision.** Candidate method: original FLUXNET companion ERA RH at preserved Stage12ac/observed tower TA, reconstruct VPD_USE and QBOT with unchanged PSRF; verify source SHA QC and native time, 24 source QC0 bookends and signed old source values, original 2017 Stage12ac 5 halfhours, and 4hPa strict every-step limits. No raw data, Post-v5, DATM or Slurm changes.

## Six whole original source runs are **HOLD / not proposed**

| Run | Original source QC1 range | Original QC1 halfhours | Source issue |
| --- | --- | ---: | --- |
| 12 | 2015-09-26 05:00–06:30 | 4 | Max native VPD step 4.800355 hPa >4 |
| 14 | 2015-11-04 13:00–2015-11-14 07:00 | 469 | >300 HH; at least some T/source ERA humidity physics HOLD (not independently full-run checked) |
| 15 | 2017-06-28 17:00–2017-06-30 16:00 | 95 | Both actual QC0 bookends absent; physics and continuity HOLD |
| 16 | 2017-06-30 17:00–2017-07-01 07:30 | 30 | Both QC0 bookends absent; >4hPa |
| 17 | 2017-07-01 12:00–2017-07-04 08:00 | 137 | Both QC0 bookends absent; contains five earlier operator-approved Stage12ac July4 HH; physics and 4hPa gate HOLD |
| 18 | 2017-07-04 12:30–2017-07-05 11:30 | 47 | Both QC0 bookends absent; >4hPa |

These 6 runs include 782 source QC1 halfhours, of which **761 newly implicated original QC1 neighbors** remain unapproved, 16 original reviewed centers, and 5 previously approved Stage12ac protected rows. Do not interpret `979` extra original QC1 neighbor total as 979 repairs: only the **218** located in the twelve fully verified 2015 runs are proposed at this point. The 2015 November 469HH case requires an independent large-event source science strategy; the 2017 sequences cannot be cleared without stronger QC and external evidence, and the earlier 2017 five approved values must remain untouched.

## Operator science decision next, NOT a model job

[Stage13s exact proposal-only source scope JSON](../decisions/STAGE13S_PROPOSED_US_ME6_TWELVE_2015_FULL_QC1_RUNS_235HH_20261027.json), with `status=PROPOSAL_ONLY_OPERATOR_APPROVAL_REQUIRED_DO_NOT_APPLY`. It **does not** authorize editing any source or forcing. Once user approves **exact 12 2015 runs**, implement bounded Stage13s `--self-test/--check/--apply` and give a phone-safe **one-line** pinned launcher; `--check` verifies original report sources and complete 235 source/native RH/QBOT/VPD continuous group with actual protected QC0 edges and a full NOLEAP differential, and `--apply` writes a **new independent research-only** Me6 forcing with the original Stage12ac five 2017 modifications and all other original source unchanged. Any run not passing on re-check is held with no forced patch. **No new Slurm/DATM/AD400, PFT or ZBOT modifications.**

Actual Stage13r done; Stage13s is **only a proposal**, not code applied to IRIDIS6 and not a successful result.
