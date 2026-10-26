# Batch03 2026-10-26 Stage12ak verified; Stage12al next (research-only)

## Actual operator IRIDIS6 Stage12ak output — PASS

At 2026-10-26 03:17 UTC operator's pinned Stage12ak source SHA/syntax, synthetic `--self-test`, source-validated `--check` and SHA-sealed `--trial` all PASSED. Original Stage12ai nine-site complete-source successor statuses preserved; original Stage12ah and Stage12af remain immutable. New two-site isolated **NOT OPERATOR-APPROVED** successors:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage12ak_7_nonhumidity_source_interpolation_PROPOSALS_ONLY_20261026T031747Z_61471fd7`

Original source QC2 extrema and neighbors (PA_F source in kPa) yielded EXACT six original-30min PSRF research candidate values: US-Kon `200412032330=96535.500`, `200412040000=96527.000`, `200412040030=96518.500` Pa; US-NR1 `200412032230=69935.750`, `200412032300=69929.500`, `200412032330=69923.250` Pa. Two source QC2 longwave radiations at NR1 `200412032200=191.566` and `200412032230=191.503` W/m2. These 8 variable repairs affect 7 distinct native timestamps. Stage12ak science *trial* has **zero other nonhumidity missing data rows** in Kon and NR1. Existing Kon VPD/QBOT 389 and NR1 VPD/QBOT 240 remain missing, all other source fields and time unchanged. No production approval or model launch.

## Stage12al next: six original-native source companion ERA-RH humidity repairs in separate NR1 research trial

On 2022-09-10 at native HH `0600,0630,0700,0730,0800,0830`, original site `TA_F_QC=1` anomalous warm values at 06:30/07:30/08:00 were **already user-approved and applied in original immutable Stage12af** via interpolation from QC0 temperature anchors; their six VPD/QBOT remain HOLD pending humidity science. Original source FLUXNET companion `TA_ERA/VPD_ERA` at exact native times implies continuously varying RH ~72%; independent prior Stage12af source calculations yielded prospective VPD hPa **1.811838, 1.873343, 1.936537, 1.912989, 1.890739, 1.853710**, with expected negligible jumps versus Stage12af existing 05:30 ~1.791 hPa and 09:00 ~1.869 hPa.

New [Stage12al original-native six-record independent source ERA-RH trial](../scripts/stage12/12al_NR1_six_native_ERA_RH_on_12ak_nonhumidity_science_trial.py) SHA-verifies BOTH preceding Stage12af and new Stage12ak original source selections/receipts and original signed Stage07 site tower/paired ERA. It recomputes all six exact ERA RH/VPD/QBOT values at the approved site temperature and source P **from original full-precision data**, matches original Stage12af source proposal table to 1e-9, checks all seven affected neighboring native 30min VPD jumps ≤4hPa, zero off-target forcing changes, retains 7 HH/8 field Stage12ak corrections and source clock. `--check` no writes; `--trial` only one new SHA-sealed **INCOMPLETE/NOT USER-APPROVED** NR1 full-source model-time research candidate, six source receipts and seven edge ledger. This script was committed to GitHub (commit `3178d616c3fcf0cf64866ae8505330c1677b9e50`, Git blob `664953766caec968eeac223c102592296c06e76e`) but **is not yet verified on operator IRIDIS6**.

If all source checks pass, **NR1 numeric VPD/QBOT missing 240→234**, nine signed site trial combined VPD missing subtotal **3788→3782**, and NR1 source other-variable missing stays zero in science trial. Kon research trial remains 389 held humidity records. **Neither Stage12ak 8 fields nor Stage12al 6 humidity values are individually operator-approved for formal science acceptance or use in Post-v5/DATM/spinup.** The user's instruction to continue means continue scientific processing; do not imply final science sign-off. Original US-MtB 2,840, US-Kon 389, US-NR3 238, US-Me6 65, US-MMS 16, and US-Me2 four clock holds still block completion of Batch03.

## Scientific sequencing

- US-NR1 after Stage12al: request operator's scoped final decision on **paired ERA RH** for six native rows plus 8 earlier QC2 nonhumidity interpolations before model promotion. Other 234 NR1 native gaps remain.
- US-Kon: event-coherent 34 VPD held centers + 23 corrected-temperature QC1 VPD/HOLD neighbors need grouped same-source physics reconciliation, NOT naive single-center fill; preserve 10 other QC1 T holds.
- US-Me6 33 previous operator-approved RH-source method cases should be repaired using original native paired ERA source, not unapproved gridded ERA5-Land offsets.
- US-MtB Stage12j all 4 gridded correction methods failed measured-QC0 multiyear screen and 4 ice supersaturation cases remain conditional on exact model path.
- Other US-NR3, US-MMS, US-Me2 and three earlier numerically complete Stage11 shadows need separate audit and strict Post-v5 release.

All original inputs, Stage12a–ak snapshots, human-approved temperature fixes, original source quality codes, PFT and CIME unmodified.
