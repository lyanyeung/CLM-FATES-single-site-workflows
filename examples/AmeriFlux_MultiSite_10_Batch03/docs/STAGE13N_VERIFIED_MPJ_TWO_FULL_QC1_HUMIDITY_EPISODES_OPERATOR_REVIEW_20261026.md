# Stage13n IRIDIS6 PASS — US-Mpj two 2014 continuous QC1 humidity episodes, grouped Stage13o operator decision

## Actual source results

On `login6003`, Stage13n pinned `a474f5b1124199096eed82f6b1abb689e67800bd`, `--self-test`, `--check`, `--run` all **PASS**. Confirmed exact full source-native original 5h QC1 runs, **not** isolated 3 spikes:

| Event | Original QC1 native halfhours | Adjacent true QC0 original site VPD | Source/ERA paired RH transfer basic physical preview | Stage13n 30min transition results |
|---|---:|---|---|---|
| Oct11 `2014-10-11T01:30:00` through `2014-10-11T06:00:00` | 10 | before `2014-10-11T01:00:00`; after `2014-10-11T06:30:00` | 10/10 source QC1 and ERA-RH-at-site-TA physics PASS | 02:30 center bounded minimal 6-point `01:30–04:00` max **1.344928 hPa**; 04:30 center bounded minimal 7-point `03:00–06:00` max **1.414406 hPa**; both candidate windows overlap and cover the full 10-point run |
| Oct21 `2014-10-21T04:00:00` through `2014-10-21T08:30:00` | 10 | before `2014-10-21T03:30:00`; after `2014-10-21T09:00:00` | 10/10 source QC1 and ERA-RH-at-site-TA physics PASS | Entire QC1 run possible bounded candidate max **1.443102 hPa**, and no measured QC0 overwritten |

Original VPD source science: Oct11 source `VPD_F` within QC1 8.282→8.089 hPa while preceding original measured QC0 01:00 is 0.100 hPa and following measured QC0 06:30 is 0.235 hPa. Original RH from tower T/VPD on Oct11 at 02:30 was **−24.9078%**, at 04:30 **−1.2944%**, both nonphysical. Source companion ERA RH remains 83–86% during the 5h QC1 event. Oct21 source original QC1 up to 11.018 hPa while the subsequent original measured QC0 VPD at 09:00 is 1.462 hPa. This is evidence of a likely QC1 segment-wide humidity-provenance artifact, **not proof that ERA RH equals tower truth**.

Stage13m source and companion SHA unchanged:
- Stage07 US-Mpj 315,360-row selected source `c227f65b800baca3160efe40442fee91ee83c5f04308a0453e0c22bd05d0f592`
- Original FLUXMET `11f4383dd6deebec8d8ec4f8d82ea00b94e2d4100144811f335f395925451e75`
- Original companion ERA `fb9dc6954b585c125669fab10af1f6d1ca22f2ee84ef18b59f55c9d2449b7f2e`

Newest immutable SHA-sealed source evidence report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13n_Mpj_original_QC1_ERA_RH_episode_READONLY_20261026T201029Z_3b42b67d`.
Another earlier Stage13n report in the same terminal log is 20:09:14 UTC; the latest is 20:10:29 UTC.

## One proposed grouped user-science decision (NOT yet granted)

**Recommend approval** for the **two FULL 10-halfhour original source VPD QC1 runs** above, 20 native timestamps total. Original Stage13m operator had conditionally approved 3 individual exact 2014 VPD values but the original source neighbor continuity failed, with `passed_science_adoptions=0` and no successor written. Extending to both entire source QC1 runs adds **17 previously unapproved original QC1 VPD halfhours**, all of which need explicit operator authorisation; do **not** treat three prior center approvals as blanket approval.

Method after *separate* operator approval: use original SHA-locked site-downscaled companion ERA RH at *retained original Stage07 TA_USE*, recompute VPD and QBOT using unchanged Stage07 PSRF, **only for 20 original VPD_F_QC=1 halfhours**; retain the three existing operator-specified Stage07 center values where numerically equivalent, and require no additional edits at them; verify across both full joined episodes all original source/QC/ERA clock, 20/20 source physical checks, both QC0 source boundaries intact, every adjacent VPD step ≤4hPa, no other native-time/variable differences. **Fail the whole event**, not a partially repaired QC1 run, if any original source, physics, clock or two-sided transition gate fails.

Never alter the two protected 2018 Feb02 `17:30 VPD=11.261`, `19:00 VPD=9.178` (both original QC2, preserve), already-approved 2020 Feb11 06:30 TA=1.1795, raw FLUXMET, Stage07, Stage11h, PFT, ZBOT, DATM, AD400, Normal400 or Slurm. Write only a new research-only shadow after operator approval and repeat source gate/whole-source differential and SHA receipts.

[**Stage13o proposal-only operator JSON**](../decisions/STAGE13O_PROPOSED_US_MPJ_TWO_ORIGINAL_QC1_2014_SEGMENTS_20HH_20261026.json) has status `PROPOSAL_REQUIRES_EXPLICIT_OPERATOR_APPROVAL`, `not_a_permission_to_apply=true`. It is **not** an approved instruction to repair; none of these 17 extra native records has been changed. No Post-v5 or model job permission.

## Next action

User can approve **the two 10HH source-native QC1 runs in one grouped decision**. Then write a strictly scoped Stage13o source-gated `--self-test/--check/--apply` and separately SHA-sealed successor. If not approved, all original 2014 Stage13m center source decisions stay HOLD and proceed with independent US-NR1 six-RH science.
