#!/usr/bin/env bash
# Batch03 US-NR1 Stage13p exactly two operator-approved groups.
# Downloads pinned source/decision and 12ak/12al scientific helpers;
# verifies all source blob hashes, runs self-test/check/apply in order.
# No Slurm jobs, DATM, post-v5, PFT/ZBOT or original input modification.
set -euo pipefail

if command -v conda >/dev/null 2>&1; then
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda activate clm_fates_env
fi

BASE="$HOME/ameriflux_batch03_stage13p"
mkdir -p "$BASE"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/9c700edfd2fe347880f15b6899a6952a5073deda/examples/AmeriFlux_MultiSite_10_Batch03"
SCRIPT="$BASE/13p_NR1_operator_approved_two_group_ERA_RH_PSRF_FLDS_shadow.py"
AK="$BASE/12ak_Kon_NR1_seven_nonhumidity_pressure_longwave_SCOPED_TRIAL.py"
AL="$BASE/12al_NR1_six_native_ERA_RH_on_12ak_nonhumidity_science_trial.py"
APPROVAL="$BASE/stage13p_NR1_approval.json"

curl -fLsS --retry 3 "$RAW/scripts/stage13/$(basename "$SCRIPT")" -o "$SCRIPT"
curl -fLsS --retry 3 "$RAW/scripts/stage12/$(basename "$AK")" -o "$AK"
curl -fLsS --retry 3 "$RAW/scripts/stage12/$(basename "$AL")" -o "$AL"
curl -fLsS --retry 3 "$RAW/decisions/STAGE13P_OPERATOR_APPROVED_NR1_6_2022_VPD_QBOT_AND_5_2004_PSRF_FLDS_20261026.json" -o "$APPROVAL"

test "$(git hash-object "$SCRIPT")" = "da99dc21022f86fc908d13ec44126ac1511493c9"
test "$(git hash-object "$AK")" = "6c91b342009b3308fabbb42ed75504f3162540db"
test "$(git hash-object "$AL")" = "664953766caec968eeac223c102592296c06e76e"
test "$(git hash-object "$APPROVAL")" = "066aebb9563bb56688cbb1e334012bfa2a91c410"
echo "STAGE13P MOBILE PINNED SOURCES AND OPERATOR APPROVAL HASH PASS"

python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --check --approval "$APPROVAL" 2>&1 | tee "$BASE/stage13p_NR1_check.log"
grep -qF "STAGE13P READONLY CHECK PASS" "$BASE/stage13p_NR1_check.log"
echo "STAGE13P SAFE TO APPLY: BOTH NR1 SOURCE GROUPS CHECK PASS"
python3 -B "$SCRIPT" --apply --approval "$APPROVAL" 2>&1 | tee "$BASE/stage13p_NR1_apply.log"
grep -qF "STAGE13P TWO SOURCE GROUPS PASS; NR1 6 HUMIDITY + 5 NONHUMIDITY FIELDS SUCCESS" "$BASE/stage13p_NR1_apply.log"
echo "STAGE13P MOBILE OPERATION COMPLETE; RESEARCH SHADOW ONLY; NO SLURM/DATM/AD400"
