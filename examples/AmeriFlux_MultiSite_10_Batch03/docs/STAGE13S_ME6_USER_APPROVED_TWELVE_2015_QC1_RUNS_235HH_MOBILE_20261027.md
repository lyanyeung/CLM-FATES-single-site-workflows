# Stage13s US-Me6 — 12 source-original full 2015 QC1 humidity episodes operator-approved, pending IRIDIS6

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
