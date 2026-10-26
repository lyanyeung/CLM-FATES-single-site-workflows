# Stage13L — US-MOz 40 half-hours, operator-approved reanalysis-backed repair

## 2026-10-26 19:39 UTC — STAGE13L v2 APPLIED AND VERIFIED on IRIDIS6

Operator-supplied `login6003` original full terminal transcript verifies Stage13l v2 pinned source hash, Python AST / `--self-test` PASS, `--check` PASS, and **`--apply` SUCCESS**. The exact new SHA-sealed **research-only** 315,360 native halfhour forcing was written and reparsed with all source-data differential and 40-source science checks:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage13l_US_MOz_40HH_user_approved_CDSEra5Land_20261026T193902Z_95631db8`

Final operator program output:

`STAGE13L 40/40 OPERATOR APPROVED SCIENCE SHADOW SUCCESS`

`SOURCE NOLEAP ROWS 315360 ACTUAL NEW MODEL FIELD EDIT COUNTS {'TBOT': 40, 'QBOT': 40, 'TA_USE': 40, 'VPD_USE': 40}`

Previous signed Stage13g SHA256 `f6b740491fd3b7d9b66fe9bc33c20586db6124442b93df72273410d761bd6b27`; CDS SHA256 `5879ed81aca701d53b8b9674183556df7369861ce4a8cdca1ffd54126fb712ef`; signed Stage13k receipt SHA `05531f8ce7d85229b85335912c5855ce8f99e296d593039644d66c26091a7e2d`. BIF official UTC−6 and original measured tower QC0 29 analogue records were verified; replacement **waived local ±6h QC0 for the 40 slots only** by documented operator decision. Both source-native boundary T/VPD steps and all paired ERA/RH/pressure numerical checks **PASS**.

Original FLUXMET, prior Stage07, Stage13g, PFT, ZBOT, CIME and Slurm unchanged. **First 27 Jan05/06 QC1 source records remain HOLD**, as do the Jan09 negative discrepancy and any other unapproved source event. **Post-v5/DATM/AD400/spinup remain FALSE**. This supersedes the older 'no IRIDIS6 execution received yet' language below.

## Decision and scientific provenance — 26 October 2026

The operator explicitly authorised the **second** Stage13k original QC1 episode only, source-native `2005-01-06 14:00:00` through `2005-01-07 09:30:00`, 40 x 30-minute records. This permits **one new isolated science shadow**, replacing `TA_USE` and `VPD_USE` with paired signed CDS ERA5-Land T2m and dewpoint-derived VPD and regenerating `TBOT` and `QBOT` using unchanged `PSRF`. Original FLUXMET, companion source ERA, existing Stage07 and successful Stage13g (315,360 source-native half-hours) stay immutable.

This decision explicitly waives for these 40 records only the unavailable ±6-hour locally **measured QC0** temperature/VPD anchors and the Stage13j ≥1°C superiority margin for official BIF UTC−6. It **does not pretend** CDS ERA5-Land is independent measured tower truth; the downloaded ERA5-Land product is ERA5-dependent. The operator instead accepted the actual Stage13k source evidence, BIF official UTC−6, the 29 nearby available independent original measured QC0 analogue samples (not adjacent to event), and the external source numerical plus retained forcing boundary checks.

**The first source QC1 event** 2005-01-05 20:00 to 2005-01-06 09:00 (27 half-hours) remains **HOLD**, as does the unapproved Jan09 negative source temperature discrepancy and all other unapproved native times. The previously operator-approved Jan06 10:00 temperature/VPD fix is retained; no second pass of that record.

## Actual prior Stage13k results (verified on IRIDIS6 19:24 UTC)

Stage13k original evidence report: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13k_MOz_Jan2005_QC0_extended_and_CDS_comparison_20261026T192412Z_5fb1be73`.

- Selected 40 source original `TA_F_QC=1` and `VPD_F_QC=1`, and all 40 records differ from original companion ERA TA by >5°C.
- Signed CDS response SHA256 `5879ed81aca701d53b8b9674183556df7369861ce4a8cdca1ffd54126fb712ef`, hourly UTC coverage Jan03 00:00 through Jan11 23:00 (216 hours), BIF 38.7441°N, −92.2°E, published offset UTC−6.
- **40/40** each passed CDS derived T/VPD water physics, original companion ERA temperature agreement (≤3.5°C), companion RH agreement (≤15 percentage points), external versus preserved site model pressure (≤12kPa). Grid–source ERA T MAE **0.817015°C**; RH MAE **4.335509 percentage points**.
- Boundary against unchanged Stage13g: temperature discontinuity before **0.894647°C**, after **3.070375°C**; VPD before **1.559645 hPa**, after **0.834160 hPa**, all ≤4.
- Original Stage13g source SHA256 `f6b740491fd3b7d9b66fe9bc33c20586db6124442b93df72273410d761bd6b27`.
- Measured QC0 original T+VPD is absent within 6h of both event ends, but operator specifically approved this 40-only reanalysis-backed evidence policy. **This is a scientific model input choice, not a validation against local QC0 measurements.**

## 2026-10-26 IRIDIS6 regression failure and Stage13l v2 fix

Operator ran Stage13l v1 `--check`. Its source/CDS SHA, 216-h CDS UTC and previously signed Stage13k verification passed through the NumPy physical gate, but line 207 raised:
`TypeError: ufunc 'bitwise_and' not supported for the input types...`

**Root cause:** `physical` used chained `&` logical conjunction with final unparenthesised `np.abs(cdsp-psrf)<=12000`, allowing bitwise AND to bind to floating-point arrays before pressure comparison. This was a Python precedence bug, **not evidence of bad science, bad CDS, changed original input, or an actual repaired shadow**. Original sources and Stage13g remain unchanged.

The [Stage13l v2 revised script](../scripts/stage13/13l_apply_MOz_40HH_approved_ERA5Land_reanalysis_shadow.py) extracts `physical_gate()` using `np.logical_and.reduce` of explicitly boolean masks with `(abs(pressure_difference)<=12000)`. Self-test verifies 40 valid float values, one pressure failure and one NaN-RH failure. The exact original operator-approved 40 source-native slots, all external source SHA pins and Stage13k previous science receipt checks remain unchanged. Do **not** change the first 27 held records, 2005 Jan09, other original source/case or submit model jobs.

Stage13l v2 Git commit: `f01bf3817724b97fa3ee2d76e33047efd24e3966`, file Git blob `aa56cd8fc2989bce1aee6f4ece0ef25ec67c4a3f`. Run revised `--self-test`, `--check` then only after `READONLY CHECK PASS` run `--apply`; SHA-locked original Stage13j helper and both decision JSONs unchanged. At time of this note, user has **not yet reported** IRIDIS6 Stage13l v2 successful export.

## Repository artifacts and instructions

- [Exact Stage13L operator waiver JSON](../decisions/STAGE13L_OPERATOR_APPROVED_US_MOz_2005JAN06_40HH_REANALYSIS_ALTERNATIVE_20261026.json)
- [Stage13L strict signed source and full NOLEAP differential tool](../scripts/stage13/13l_apply_MOz_40HH_approved_ERA5Land_reanalysis_shadow.py).
- Existing adjacent Stage13j v4 helper is pinned to original Git blob `9283b411b49500428e7534b5f12041c71190e93b` and the exact Stage13j 67-slot conditional decision JSON already used with Stage13k. It is loaded **read-only** for original source metadata/CDS model evaluation; Stage13j original strict QC0 approval policy is not modified.
- `--self-test`: pure isolated 40-halfhour, ice/saturation formula check, **no I/O**.
- `--check --approval <json> --previous-decision <Stage13j json>`: hashes all original inputs and Stage13k scientific reports, validates all 40 original QC1 rows, source ERA, CDS time and variables, preserved pressure/QBOT/TA physical consistency and pre/post edges; prints exact prospective changes and source QA; **no writes**.
- `--apply --approval <json> --previous-decision <Stage13j json>`: repeats all science checks, emits a new independent 315,360-row 18-year CSV, exact 40-source-value ledger and SHA audit receipt under new `science_trials/stage13l_US_MOz_40HH_...`. Only four selected model fields `TA_USE`, `VPD_USE`, `TBOT` and `QBOT` are modified, at only these 40 exact source-native times (160 proposed model-cell changes total). All non-target source fields/timestamps are verified unchanged.

**Status as of GitHub commit:** authorisation and code committed; **no actual Stage13L IRIDIS6 execution result received yet**. Do not claim the candidate was created until `--apply` prints SUCCESS and its receipt exists. Even then `Postv5_approved=false`, `DATM_ready=false`, `spinup_authorized=false`; do not submit Slurm. Later independent 2005-QC1 source review and ZBOT/PFT/case checks remain necessary.
