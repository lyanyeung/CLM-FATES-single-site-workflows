# NEXT operator review: US-Mpj 5 historical VPD review events — 2026-10-26

**User priority:** human science decisions first; observed-PFT composition already updated in user GitHub, do not reopen the PFT literature exercise. Source site `US-Mpj`, Batch03 AmeriFlux.

**Status:** proposal / OPERATOR DECISION REQUIRED; no new authorisation, forcing writes, Post-v5 release, DATM or Slurm. The original six Stage13d TA QC0 interpolation science approvals include **one US-Mpj 2020-02-11 06:30 temperature spike at 1.1795°C**, and are separate from the 2014/2018 VPD decisions here.

**Original primary source and full manual context:** [Stage13c 24 original review cases](STAGE13C_24_MANUAL_DECISIONS_TOWER_ERA_CONTEXT_20261026.md), original IRIDIS6 exact-timestamp/±2h audit report at `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13c_24_manual_original_tower_ERA_TA_context_20261026T171801Z_bed5a936`. Source Stage07 selected historical candidate is `qcv5_native_trial_20261022T024559Z_36c46e58`. The exact original file and source receipts must be reverified if a new science shadow is generated.

## Five source-native halfhour operator decision table

| Native local time | Original TA_F / paired TA_ERA (°C) | Original VPD_F -> existing Stage07 VPD_USE (hPa) | Original science finding | Suggested scoped decision |
|---|---|---|---|---|
| 2014-10-11 02:30 | 1.065 / 6.654 | 8.245 -> **1.032** | Original VPD exceeds saturation at tower T, numeric candidate plausible | **CONDITIONALLY APPROVE** the existing Stage07 VPD (not a new ERA-only value), after original QC/native time, RH/QBOT and both neighboring VPD check |
| 2014-10-11 04:30 | 3.883 / 6.233 | 8.170 -> **1.163** | Original VPD near/exceeds saturation at tower T, candidate plausible | **CONDITIONALLY APPROVE** existing Stage07 candidate with same tests |
| 2014-10-21 08:30 | 8.530 / 8.473 | 11.018 -> **2.103** | Original near-zero RH; candidate RH-repair plausible but requires adjacent tower-source continuity | **CONDITIONALLY APPROVE** existing Stage07 candidate only when source/native QC and both-side VPD and RH pass |
| 2018-02-02 17:30 | 8.822 / 12.225 | **11.261 -> 11.261 (unchanged)** | Very low but positive RH; no source change | **PRESERVE ORIGINAL**, no VPD replacement authorized |
| 2018-02-02 19:00 | 5.798 / 9.390 | **9.178 -> 9.178 (unchanged)** | Very low but positive RH; no source change | **PRESERVE ORIGINAL**, no VPD replacement authorized |

These are actual source-observation times and selected Stage07 candidate values, not a newly produced file. Do not assert that the 2014 three events have been fully independently validated at adjacent source observations. Stage13c reports plausible candidates; the missing source-side information must be checked before applying the operator's conditional rule.

## Proposed one-time scientific authorization to ask operator

Approve only the exact three existing `US-Mpj` October 2014 Stage07 VPD candidate values **conditional upon** successful verification of: SHA-pinned original FLUXMET tower and paired source ERA, source timestamps and QC flags, unchanged signed Stage07 target values, 0 < RH < 100%, reconstructed QBOT at preserved model PSRF, both immediate adjacent source VPD values and physical transitions, no modifications outside the three approved native times; preserve the two original Feb 2018 low-positive-RH VPD times unchanged. **If any condition fails, hold only that event and do not silently repair.** No replacement of original source files or changes to 2020-02-11 approved temperature interpolation. This does not authorize Post-v5, DATM or model jobs.

If approved by operator: first create one combined signed original-source/neighborhood audit for all three 2014 candidates, then write a NEW independent candidate shadow only for entries that pass all signed science tests. Avoid repeating the manual approval prompt per timestamp.

**Next manual site after US-Mpj:** US-NR1 already prepared six exact original-native 2022-09-10 paired-ERA RH candidates `1.811838,1.873343,1.936537,1.912989,1.890739,1.853710` hPa and Stage12ak 8 two-site nonhumidity variable interpolations; need one separate bounded operator decision based on the original Stage12al receipt. Then review US-NC2 13 VPD cases. US-MMS 16 hourly gaps are an automatic source-evidence task rather than the top immediate operator-approval task.
