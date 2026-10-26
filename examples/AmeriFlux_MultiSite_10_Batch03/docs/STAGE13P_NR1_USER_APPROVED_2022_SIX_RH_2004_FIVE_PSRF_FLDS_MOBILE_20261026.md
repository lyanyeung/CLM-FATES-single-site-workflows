# Stage13p — user-approved US-NR1 six 2022 humidity and five 2004 nonhumidity repairs

## 2026-10-26 22:36 UTC — ACTUAL IRIDIS6 Stage13p source science and applied result

The operator executed the Git blob verified [Stage13p mobile one-click](../scripts/stage13/13p_NR1_mobile_one_click.sh) from `login6003` and provided full terminal log. Hash guard PASS; original Stage12af/ak/al receipt and source-chain read-only check PASS; original five 2004 source QC2 interpolations and six 2022 original-native paired ERA RH 7-edge VPD scientific checks PASS. Final:

`STAGE13P TWO SOURCE GROUPS PASS; NR1 6 HUMIDITY + 5 NONHUMIDITY FIELDS SUCCESS /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage13p_NR1_6ERA_RH_5_PSRF_FLDS_OPERATOR_APPROVED_20261026T223628Z_6b3f07eb`

Original 490,560 NOLEAP rows with full-source and output readback verified. Exactly `{'QBOT': 6, 'PSRF': 3, 'FLDS': 2, 'VPD_USE': 6}` field changes compared to the last operator-approved Stage12af NR1 source; 17 changed field-values over 10 native time stamps. The VPD seven 30min edges have maximum `0.06319390197164276` hPa. All other original source times/fields unchanged, previous Stage12af approved temperature retained; Stage12ak audit prints hypothetical source Kon pressure corrections as part of its verified original source audit, **but US-Kon has no file written by Stage13p**. The other 234 NR1 humidity-held timestamps remain blank, and **Post-v5/DATM/AD400/Slurm false**.

These exact 11 operator-approved US-NR1 model-field corrections need no repeated user scientific approval. The new output is still research-only, not an admitted model forcing.

## Exact approved scope and Stage12 source facts

Operator explicitly approved two bounded site-science groups, ONLY **US-NR1**.

| Group | Original-source-native records | New model field values | Original source evidence |
|---|---|---|---|
| 2022-09-10 06:00–08:30, 6 adjacent original 30min `VPD_F_QC=1` | six source-native timestamps | six `VPD_USE` and six `QBOT` | Signed Stage12af approved site TA and original FLUXNET companion ERA relative humidity; Stage12al original trial, 7 adjacent source-native edges <0.064hPa |
| 2004-12-03 22:00, 22:30, 23:00, 23:30, 4 original-source-native timestamps | exact five field edits: 2 `FLDS` + 3 `PSRF` | five | Original Stage12aj/ak QC2 longwave/pressure fields, exact original good QC2 bracketing interpolation sources |

Original pressure interpolants: 22:30 = **69935.75 Pa**, 23:00 = **69929.50 Pa**, 23:30 = **69923.25 Pa**. Original longwave interpolants: 22:00 = **191.566 W/m²**, 22:30 = **191.503 W/m²**. The previously approved Stage12af September2022 site temperature corrections are retained, not recomputed differently or overwritten. Original six companion ERA-RH-based VPD hPa: **1.811838,1.873343,1.936537,1.912989,1.890739,1.853710**.

[Signed exact new Stage13p operator decision](../decisions/STAGE13P_OPERATOR_APPROVED_NR1_6_2022_VPD_QBOT_AND_5_2004_PSRF_FLDS_20261026.json) and [strict original signed sources audit + research-only independent source candidate script](../scripts/stage13/13p_NR1_operator_approved_two_group_ERA_RH_PSRF_FLDS_shadow.py). **No other US-NR1 source HOLD and no US-Kon source repair is authorised by this decision.**

## Signed original inputs and fail-closed design

Stage13p contains original pinned science helpers, not rewritten science rules:

- Original Stage12ak Git blob `6c91b342009b3308fabbb42ed75504f3162540db`, original prior scientific version `batch03-stage12ak-v1-20261026-nonhumidity-KON-NR1-eight-variable-proposals`.
- Original Stage12al Git blob `664953766caec968eeac223c102592296c06e76e`, original version `batch03-stage12al-v1-20261026-NR1-six-ERA-RH-research-only`.
- Original signed research sources are existing directories `stage12af_NR1_20220910_user_approved_three_T_only_20261026T013349Z_34ff1cda`, `stage12ak_7_nonhumidity_source_interpolation_PROPOSALS_ONLY_20261026T031747Z_61471fd7` and `stage12al_NR1_20220910_six_original_native_ERA_RH_RESEARCH_ONLY_20261026T032328Z_f8c3ff27`.
- Stage13p hashes **all source files named in the three original SHA receipts**, verifies signed receipt linking original approved temperature and original Stage12ak/Stage12al trials, then **re-executes original source QC/timestamps/original good neighbor pressure/longwave interpolation** via Stage12ak `audit()` and **six paired original ERA-RH/approved site T thermodynamic/QBOT and seven VPD edge** checks via Stage12al `audit()`. All source checks are fail-closed.
- Checks original selected **US-NR1 Stage12af 490,560 native NOLEAP rows** against recomputed and signed Stage12al, expecting **only 17 field-value differences in exactly ten original-native times**: VPD_USE 6, QBOT 6, PSRF 3, FLDS 2. Pre-existing model source defects not explicitly approved remain unchanged, including **234 remaining NR1 VPD/QBOT gaps**.
- On any source/time/QC/physics/anchor/SHA failure, Stage13p `--check` fails and the launch script does **not** execute `--apply`. This implementation is stricter than group-isolated partial success: **both approved groups must pass** to generate the independent source candidate.
- On `--apply` PASS, Stage13p writes an **isolated, originally SHA-pinned 490,560-row NR1 research-only CSV** with provenance/QA ledgers and new signed SHA receipt, re-reads the full CSV to check all fields/time. No original FLUXMET/ERA, US-Kon, PFT, ZBOT, CTSM case, Post-v5, DATM, AD400, Normal400 or Slurm changes.

## IRIDIS6 mobile invocation

Use [Stage13p mobile one-click launcher](../scripts/stage13/13p_NR1_mobile_one_click.sh), in one shell line. The launcher downloads from pinned commit `9c700edfd2fe347880f15b6899a6952a5073deda`, verifies source file Git blobs `da99dc21022f86fc908d13ec44126ac1511493c9` (main Python), `6c91b342009b3308fabbb42ed75504f3162540db` (Stage12ak helper), `664953766caec968eeac223c102592296c06e76e` (Stage12al helper), and `066aebb9563bb56688cbb1e334012bfa2a91c410` (Stage13p user approval), runs Python AST compile and synthetic self-test, then scientific `--check`, only if `STAGE13P READONLY CHECK PASS` triggers `--apply`.

Logs: `$HOME/ameriflux_batch03_stage13p/stage13p_NR1_check.log` and `$HOME/ameriflux_batch03_stage13p/stage13p_NR1_apply.log`.

Expected `--apply` success marker:

`STAGE13P TWO SOURCE GROUPS PASS; NR1 6 HUMIDITY + 5 NONHUMIDITY FIELDS SUCCESS`

**Current status:** operator approved and new code/source pins committed to main on 2026-10-26. **Stage13p has not yet been run on IRIDIS6**, so do not infer actual NR1 independent research output or claim source data/model-ready status. The previous original Stage12al trials were research-only until the new approval; no model submitted.
