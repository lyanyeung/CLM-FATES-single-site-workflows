# NEXT HUMAN OPERATOR DECISION — US-NR1, 6 native 2022 RH / 5 native 2004 PSRF+FLDS repairs (26 October 2026)

## Previous US-Mpj now COMPLETED in research shadow, without model release

On 2026-10-26 21:07 UTC, US-Mpj Stage13o operator `--check` and `--apply` **both PASS**, creating 315,360-row new independent research-only input at `science_trials/stage13o_Mpj_20HH_operator_approved_ERA_RH_20261026T210746Z_5c3c8653`. Exactly 20/20 originally QC1 site native halfhours scientifically vetted, **17 new VPD_USE and 17 QBOT model value edits**, original 3 Stage07 2014 center candidates unchanged, original four QC0 bookends unchanged, 2018 two protected source VPD and approved 2020 original temperature retained. No additional user scientific approval needed for the two US-Mpj 2014 episodes. Production Post-v5, DATM, spinup, Slurm all remain HOLD.

## US-NR1: PRIORITIZE ONE COMBINED HUMAN DECISION — not yet approved!

**A. Six original-source-native humidity cells, 10 September 2022 (06:00,06:30,07:00,07:30,08:00,08:30):**

- Existing Stage12af user-accepted source TA at all six dates: **0.762, 1.241, 1.720, 1.556667, 1.393333, 1.230°C** (includes three temperature interpolations already approved, remaining original source tower temperature). PRESERVE TA.
- Existing Stage12al operator-executed, SHA-receipted separate science shadow/QA has paired FLUXNET companion ERA RH = **71.945909, 71.976540, 72.009137, 72.024243, 72.023933, 72.248312%**.
- Prospective original-native source VPD (hPa), derived from companion ERA RH applied to retained site TA: **1.811838, 1.873343, 1.936537, 1.912989, 1.890739, 1.853710**. Recompute corresponding QBOT using preserved site `PSRF`, water vapor pressure and CLM physics. Stage12al seven 30min jumps across source-native 05:30–09:00: **0.021051,0.061505,0.063194,0.023548,0.022250,0.037029,0.014803 hPa**, all far below 4hPa gate.
- Original source `VPD_F_QC=1` (gapfilled, not directly measured QC0), so paired source reanalysis RH is a method choice, **not independent tower humidity validation**. Original native source and paired ERA SHA receipts are already sealed in Stage12af/12ak/12al.
- Research-only candidate existing: `science_trials/stage12al_NR1_20220910_six_original_native_ERA_RH_RESEARCH_ONLY_20261026T032328Z_f8c3ff27`.
- Original baseline VPD/QBOT source gaps 240, research-only six-source overlay would reach 234. **No user adoption of six as production science input yet.**

**B. Five separate QC2 original-source corrupted nonhumidity values in US-NR1, 3 December 2004:**

| Original source-native date | Site model field | Old original source | SHA/neighbor-based Stage12ak interpolation proposal |
| --- | --- | --- | --- |
| 2004-12-03 22:00 | FLDS | Original LW_IN_F 22.869 W/m2 (QC2) | **191.566 W/m2** |
| 2004-12-03 22:30 | FLDS | Original LW_IN_F 22.869 W/m2 (QC2) | **191.503 W/m2** |
| 2004-12-03 22:30 | PSRF | Original PA_F 30.871 kPa (QC2) | **69,935.75 Pa** |
| 2004-12-03 23:00 | PSRF | Original PA_F −8.200 kPa (QC2) | **69,929.50 Pa** |
| 2004-12-03 23:30 | PSRF | Original PA_F 30.859 kPa (QC2) | **69,923.25 Pa** |

Original measured neighboring tower/site pressure anchors 2004-12-03 22:00 at 69.942 kPa and 2004-12-04 00:00 at 69.917 kPa; longwave neighbor anchors 2004-12-03 21:30 at 191.629 W/m² and 2004-12-03 23:00 at 191.440 W/m². Prior Stage12aj original source / Stage12ak `--check` and `--trial` PASS science-trial only. Stage12ak also includes **three other source PSRF fixes at US-Kon**, which are **NOT in the proposed US-NR1 approval** and must remain separately held. The five US-NR1 field edits affect four distinct original-native times, retain all original TA/VPD and all other fields.

## Proposed exact scope for next user operator decision

**Approve conditionally 6 source-native paired ERA-RH-at-approved-TA VPD+QBOT changes on 2022-09-10 06:00–08:30 and 5 QC2 PSRF/FLDS neighbor interpolation values on 2004-12-03 exactly as table, for US-NR1 only.** Every adoption must revalidate original source SHA, original QC/native time, prior Stage12af T operator approval, Stage12ak and Stage12al full signed input and exact science trial receipts, unchanged original source time/CIME/PFT/ZBOT, RH/QBOT/PSRF/longwave physics and native neighbor edges. When a group fails, HOLD group without partial/forced scientific acceptance. A new separate US-NR1 candidate must demonstrate exact field/time delta and SHA receipt, original-source data untouched. This decision does **not** authorize the other remaining 234 RH source gaps, the three US-Kon PSRF proposals, Post-v5, DATM, spinup or Slurm.

**Status: OPERATOR_APPROVAL_NEEDED for these NR1 eleven model-field edits.** Do NOT imply approval by previous user requests to proceed with manual review.

Evidence: [Stage12al verified 6 RH 7 edge source QA](STAGE12AL_VERIFIED_NR1_6_RH_AND_STAGE12AM_KON_57_EVENT_QC_20261026.md), [Stage12ak 8 original fields two sites research-only](STAGE12AK_VERIFIED_NR1_STAGE12AL_SIX_ERA_RH_CONTINUOUS_RESEARCH_20261026.md), [Stage12aj original QC2 corrupt 7 native records](STAGE12AJ_VERIFIED_SEVEN_NONHUMIDITY_STAGE12AK_SOURCE_QC_PROPOSALS_20261026.md).
