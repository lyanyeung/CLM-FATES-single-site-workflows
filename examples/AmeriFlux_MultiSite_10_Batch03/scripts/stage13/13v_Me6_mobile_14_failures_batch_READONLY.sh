#!/usr/bin/env bash
# Me6 6 remaining original QC1 runs: 14 exact failed ERA science native HH.
# SHA-verifies original Stage13u actual IRIDIS6 report. READ ONLY + reports.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
B="$HOME/ameriflux_batch03_stage13v"
mkdir -p "$B"
R="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/1670b460c0dee42e1490beb7ae186f67ed10f729/examples/AmeriFlux_MultiSite_10_Batch03"
S="$B/13v_Me6_14_original_ERA_failure_group_review_READONLY.py"
curl -fLsS --retry 3 "$R/scripts/stage13/$(basename "$S")" -o "$S"
test "$(git hash-object "$S")" = "5562e42fdca317d68e8260ae7c4560a4df0562c7"
echo "STAGE13V PINNED SOURCE SHA VERIFIED"
python3 -B -m py_compile "$S"
python3 -B "$S" --self-test
python3 -B "$S" --check 2>&1 | tee "$B/stage13v_Me6_check.log"
grep -qF "STAGE13V READONLY CHECK PASS" "$B/stage13v_Me6_check.log"
python3 -B "$S" --run 2>&1 | tee "$B/stage13v_Me6_run.log"
grep -qF "STAGE13V FOURTEEN ORIGINAL SOURCE FAILURES AND GROUP PROPOSALS REPORT COMPLETE" "$B/stage13v_Me6_run.log"
echo "STAGE13V ME6 BATCH SOURCE SCIENCE REPORT SUCCESS; NO FORCING/DATM/AD400/SLURM"
