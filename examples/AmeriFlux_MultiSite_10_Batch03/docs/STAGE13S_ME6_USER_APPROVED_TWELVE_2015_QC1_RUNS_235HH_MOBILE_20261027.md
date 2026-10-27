# Stage13s US-Me6 — 12 source-original full 2015 QC1 humidity episodes operator-approved, pending IRIDIS6

## ACTUAL IRIDIS6 STAGE13S APPLIED SUCCESS (operator log, 2026-10-27)

The user executed the Git-pinned mobile Stage13s launcher from `login6001` and provided the full original `--self-test`, `--check`, `--apply` terminal output. **All passed**. Exact final markers:

```text
STAGE13S READONLY CHECK PASS | all twelve whole QC1 runs, 235 native HH, 24 original QC0 bookends, 2017 protected; NO WRITES
STAGE13S ALL 12 SOURCE RUNS PASS; 235 ORIGINAL QC1 HH OPERATOR APPROVED RESEARCH SHADOW SUCCESS /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage13s_Me6_12x2015_235HH_ERA_RH_operator_approved_20261027T065056Z_6890a105
STAGE13S 2015 exact 235 native records; SOURCE-VPD/QBOT actual field delta {'VPD_USE': 214, 'QBOT': 214} old H0 fills {'VPD_USE': 18, 'QBOT': 18}
STAGE13S ORIGINAL Stage12ac 2017 5 VALUES & 6 SOURCE HELD RUNS PRESERVED; NO Slurm/DATM/AD400
STAGE13S ME6 DONE
```

Actual source/receipt evidence in execution log:
- Stage13s user-approved operator JSON SHA256 `a686189a775f51e8e015627bc1152a66ad883415c5a10d953b8fb4cf08b5036e`.
- Stage13r signed original evidence SHA256 `498a0de192bf982c5751fa0b9dab2fbb7d1b2fa702a50b61b7de51445af1dbcb`; Stage13q receipt `8b52f7c258034f0061cd46116d50feab3957d1f6a4aa1f43afe003643ff1f254`.
- Last previously approved Stage12ac selected input SHA256 `54bccdadde9ff72c8c60a17bd17c28e5695aad0431fdee6dfca18faff4e2f085`.
- Original tower FLUXMET `721d87464c70ea38c7ab6206deee6953647709072cde33827a825408970971e0`, native companion ERA `af2be6dce8b9d1310540f29b3a87d57fbac4da7d2f8192434e93217e5079f98f`.
- Original Me6 selected input: **280,320 full native NOLEAP records** (16 × 17,520). **235 original source QC1 timestamps validated**, but only **214 VPD_USE and 214 QBOT numeric field values actually changed**, with **18 previously absent VPD_USE + 18 QBOT records filled**; these are separate concepts and MUST NOT be conflated. All 24 original VPD QC0 edges retain source tower values, and all original July2017 Stage12ac five corrected halfhours remain identical.
- Source science maximum full episode 30-minute VPD step among the twelve groups **2.9996543882588456 hPa** (<4hPa); no new original 2017 / other 6 hold runs modified.
- **This is a new isolated RESEARCH-ONLY candidate, not approved Post-v5/DATM/AD400/Slurm**. Other original humidity science HOLDs remain. These same 235 site-native observations need no repeated operator review.

The pending execution note below is historical and superseded by this logged actual result. Next recommended scientific decision is the **small original Sep26 2015 source VPD QC1 full episode run ID 12**, which previously failed a 4hPa boundary check at 4.800355hPa. Inspect full source/ERA and measured QC0 boundaries read-only first; never silently relax 4hPa or copy unrelated original 2017 values.

## Operator approval and exact protected scope

The operator explicitly approved **only Stage13r actual science PASS original QC1 full run IDs 1–11 and 13**, total **12** source runs across **235 original 30-minute 2015 humidity timestamps**, including 17 previously method-reviewed centers and **218 additional original source QC1 neighboring native timestamps**. Original sources are site-native FLUXNET tower, original same-native companion FLUXNET ERA, signed Stage12ac operator-approved site selected TA_USE and PSRF. ERA RH is a reanalysis-derived estimate, *not measured tower RH*.

[Full precise operator-approved source scope](../decisions/STAGE13S_OPERATOR_APPROVED_ME6_TWELVE_2015_FULL_QC1_RUNS_235HH_20261027.json). Older [Stage13s proposal-only file](../decisions/STAGE13S_PROPOSED_US_ME6_TWELVE_2015_FULL_QC1_RUNS_235HH_20261027.json) remains historical, NOT authorization by itself.

## Implementation

[Stage13s strict source-gated script](../scripts/stage13/13s_ME6_12x2015_QC1_235HH_operator_APPROVED_ERA_RH_shadow.py):

- Original pinned helper Stage13r Git blob `5a8dc69f5fb65015a9b7c9096153935684f466a8`. SHA-verifies the **actual original Stage13r signed full-run receipts and outputs**, predecessor Stage13q 33 original-source science cases and 31 HOLD groups, signed Stage12ac immutable July2017 previously approved five native halfhours. Re-runs original Stage13r science audit.
- Exact source-native 2015 12 full QC1 runs and 235 time positions. For each original source candidate native HH independently verifies `VPD_F_QC=1`, original `TA_F_QC=0`, original measured tower TA matches retained Stage12ac TA_USE, paired companion `TA_ERA,VPD_ERA`, retained PSRF, 0<RH<100%, 0<VPD<es(T), 0<QBOT<0.08, |T_tower-T_ERA|<=8°C. Rechecks SHA-signed Stage13r candidate values.
- All 24 original **true VPD_F_QC=0 source bookends** are numerically identical to selected original Stage12ac values; each complete run's 30-minute adjacent VPD jumps, including before+after, must be <=4 hPa.
- Checks all 12 group identities and the exact 17/218 split; never touches held source runs ID 12/14/15/16/17/18 (761 other QC1 neighbors remain unauthorized) or previous original 2017 July04 five approved values. No source values beyond year 2015 altered, no other site model fields, clocks, source files or PFT/ZBOT touched.
- If **any full run** fails a source/QC/physics/neighbor test, the **entire run stays HOLD** and the conservative program stops **without producing any new forcing at all**. If all pass, only VPD_USE/QBOT at up to 235 source native 2015 times in the **new isolated research-only Me6 full NOLEAP shadow** may differ from the previously approved Stage12ac. Counts of actual cells edited may differ from 235 if some source values had already matched the ERA candidate. Reports exact before/after and old gaps filled, never fabricates full completion.
- Re-read full source new output and compare complete native-time and field schema, full signed source receipts with SHA, record/model delta receipt. **Post-v5/DATM/AD400/Normal400/Slurm remain denied**, even on success.

## Mobile / cluster workflow

[Stage13s mobile one-click](../scripts/stage13/13s_ME6_mobile_one_click.sh) is designed to use a single mobile shell command. It checks pinned Git blob of approved JSON, main script and original Stage13r module, performs Python AST compile, synthetic self-test, immutable-source `--check`, requires exact read-only PASS marker, then reruns all science audits inside `--apply`. Expected successful apply marker:

`STAGE13S ALL 12 SOURCE RUNS PASS; 235 ORIGINAL QC1 HH OPERATOR APPROVED RESEARCH SHADOW SUCCESS`

Result will appear only after the operator actually executes it on IRIDIS6. GitHub commit/code presence is **not** an executed source-science PASS or model forcing promotion. Cluster log paths: `$HOME/ameriflux_batch03_stage13s/stage13s_Me6_check.log`, `$HOME/ameriflux_batch03_stage13s/stage13s_Me6_apply.log`. Source full-run signed report `reports/stage13r_Me6_original_full_QC1_run_and_original_QC0_ERA_RH_READONLY_20261027T004033Z_5eefea7b`.

**Status:** Stage13s operator approval and code committed; **IRIDIS6 Stage13s check/apply unverified pending user operator run**. No Slurm submissions.
