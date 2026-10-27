#!/usr/bin/env bash
# Stage13u US-Me6 six held full ORIGINAL QC1 episode batch science triage
# Check SHA original source, 2017 Stage12ac, 2015 Stage13s success and Sep26
# Stage13t. Only new REPORT files; no original forcing/DATM/CIME/SLURM writes.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
B="$HOME/ameriflux_batch03_stage13u"
mkdir -p "$B"
ROOT="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/dd60db82dfa91f578632f810aca946558225efd7/examples/AmeriFlux_MultiSite_10_Batch03"
MAIN="$B/13u_Me6_remaining_six_full_original_QC1_runs_BATCH_TRIAGE_READONLY.py"
PREV="$B/13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py"
curl -fLsS --retry 3 "$ROOT/scripts/stage13/$(basename "$MAIN")" -o "$MAIN"
curl -fLsS --retry 3 "$ROOT/scripts/stage13/$(basename "$PREV")" -o "$PREV"
test "$(git hash-object "$MAIN")" = "aeaa3ce78e32d17ace2f356a660447e3c51e1b77"
test "$(git hash-object "$PREV")" = "5a8dc69f5fb65015a9b7c9096153935684f466a8"
echo "STAGE13U TWO SOURCE GIT HASHES VERIFIED"
python3 -B -m py_compile "$MAIN" "$PREV"
python3 -B "$MAIN" --self-test
python3 -B "$MAIN" --check 2>&1 | tee "$B/stage13u_Me6_check.log"
grep -qF "STAGE13U READONLY CHECK PASS" "$B/stage13u_Me6_check.log"
python3 -B "$MAIN" --run 2>&1 | tee "$B/stage13u_Me6_run.log"
grep -qF "STAGE13U ALL SIX HELD SOURCE RUNS BATCH SCIENCE REPORT COMPLETE" "$B/stage13u_Me6_run.log"
echo "STAGE13U ALL SIX ORIGINAL QC1 HOLD RUNS BATCH REVIEW COMPLETE; NO FORCING OR SLURM"
