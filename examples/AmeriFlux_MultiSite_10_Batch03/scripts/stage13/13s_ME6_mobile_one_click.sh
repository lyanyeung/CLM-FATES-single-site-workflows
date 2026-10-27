#!/usr/bin/env bash
# US-Me6 Stage13s exact 12 full 2015 QC1 runs; 235 source-native halfhours.
# User/operator-approved 17 centers plus 218 previously unapproved QC1 neighbors.
# Strict source signed SHA, measured QC0 anchor, physics + 4hPa per-edge gate.
# Check before applying; new INDEPENDENT RESEARCH SHADOW ONLY. NO SLURM.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
B="$HOME/ameriflux_batch03_stage13s"
mkdir -p "$B"
R="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/b410d15374e515c50cddafa0b80d92930deef2ca/examples/AmeriFlux_MultiSite_10_Batch03"
S="$B/13s_ME6_12x2015_QC1_235HH_operator_APPROVED_ERA_RH_shadow.py"
P="$B/13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py"
A="$B/stage13s_Me6_user_approval.json"
curl -fLsS --retry 3 "$R/scripts/stage13/$(basename "$S")" -o "$S"
curl -fLsS --retry 3 "$R/scripts/stage13/$(basename "$P")" -o "$P"
curl -fLsS --retry 3 "$R/decisions/STAGE13S_OPERATOR_APPROVED_ME6_TWELVE_2015_FULL_QC1_RUNS_235HH_20261027.json" -o "$A"
test "$(git hash-object "$S")" = "3dfa1b3382fd32101d0d1e563d86142e0271bb07"
test "$(git hash-object "$P")" = "5a8dc69f5fb65015a9b7c9096153935684f466a8"
test "$(git hash-object "$A")" = "e855e0e078bf43f2a84c319955fe9527bd1a993f"
echo "STAGE13S PINNED OPERATOR SCIENCE SOURCES AND AUTHORIZATION HASH PASS"
python3 -B -m py_compile "$S" "$P"
python3 -B "$S" --self-test
python3 -B "$S" --check --approval "$A" 2>&1 | tee "$B/stage13s_Me6_check.log"
grep -qF "STAGE13S READONLY CHECK PASS" "$B/stage13s_Me6_check.log"
echo "STAGE13S ALL TWELVE Me6 SCIENCE RUNS CHECK PASS; START ISOLATED RESEARCH SHADOW"
python3 -B "$S" --apply --approval "$A" 2>&1 | tee "$B/stage13s_Me6_apply.log"
grep -qF "STAGE13S ALL 12 SOURCE RUNS PASS; 235 ORIGINAL QC1 HH OPERATOR APPROVED RESEARCH SHADOW SUCCESS" "$B/stage13s_Me6_apply.log"
echo "STAGE13S ME6 DONE; 12x2015 ORIGINAL QC1 RUNS APPROVED; NO SLURM/DATM/AD400"
