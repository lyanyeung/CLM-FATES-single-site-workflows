#!/usr/bin/env bash
# US-Me6: full ORIGINAL QC1 source episodes around Stage13q 33 held centers.
# READ ONLY. Source SHA + scientific QC0/RH/QBOT/VPD diagnostics.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
B="$HOME/ameriflux_batch03_stage13r"
mkdir -p "$B"
R="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/9b2bbdd7316f4327198fa73f088336c8105b21b3/examples/AmeriFlux_MultiSite_10_Batch03"
S="$B/13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py"
curl -fLsS --retry 3 "$R/scripts/stage13/$(basename "$S")" -o "$S"
test "$(git hash-object "$S")" = "5a8dc69f5fb65015a9b7c9096153935684f466a8"
echo "STAGE13R PINNED SOURCE VERIFIED"
python3 -B -m py_compile "$S"
python3 -B "$S" --self-test
python3 -B "$S" --check 2>&1 | tee "$B/stage13r_Me6_check.log"
grep -qF "STAGE13R READONLY CHECK PASS" "$B/stage13r_Me6_check.log"
python3 -B "$S" --run 2>&1 | tee "$B/stage13r_Me6_run.log"
grep -qF "STAGE13R ORIGINAL QC1 FULL RUN SCIENCE EVIDENCE COMPLETE" "$B/stage13r_Me6_run.log"
echo "STAGE13R ME6 ORIGINAL QC1 SOURCE EPISODES GROUPED; NO SOURCE/FORCING/MODEL CHANGES"
