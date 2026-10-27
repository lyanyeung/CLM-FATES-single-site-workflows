#!/usr/bin/env bash
# Strict signed Stage13u/v original scientific source reports;
# 14 original source RH/T/QBOT failures + four 2017 QC2 boundary issues.
# READONLY: self-test/check/run produce only reports, no forcing or Slurm.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
B="$HOME/ameriflux_batch03_stage13w"
mkdir -p "$B"
R="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/2fced0720744b40fc4ad985f0a5a88dd745b5647/examples/AmeriFlux_MultiSite_10_Batch03"
S="$B/13w_Me6_exact_14_failed_ERA_RH_T_QBOT_and_2017_QC2_BATCH_READONLY.py"
curl -fLsS --retry 3 "$R/scripts/stage13/$(basename "$S")" -o "$S"
test "$(git hash-object "$S")" = "b7f3b589fc466ad3e47615488f9658ed166f133d"
echo "STAGE13W REPRODUCIBLE SOURCE HASH VERIFIED"
python3 -B -m py_compile "$S"
python3 -B "$S" --self-test
python3 -B "$S" --check 2>&1 | tee "$B/stage13w_Me6_check.log"
grep -qF "STAGE13W READONLY CHECK PASS" "$B/stage13w_Me6_check.log"
python3 -B "$S" --run 2>&1 | tee "$B/stage13w_Me6_run.log"
grep -qF "STAGE13W ME6 14 SOURCE PHYSICS CAUSES AND 4 QC2 EDGE GROUPS VERIFIED" "$B/stage13w_Me6_run.log"
echo "STAGE13W BATCH ORIGINAL SOURCE 14-FAILURE REASONS COMPLETE; NO FORCING/DATM/SLURM"
