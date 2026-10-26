#!/usr/bin/env bash
# One-line phone-friendly launch of US-Me6 33 source-policy episode science
# report. READONLY original forcing and NO model submission.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
B="$HOME/ameriflux_batch03_stage13q"
mkdir -p "$B"
P="$B/13q_Me6_33_operator_source_policy_grouped_ERA_RH_readonly.py"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/8ae133d3b91b389bc457178a1a8f2292171ea4df/examples/AmeriFlux_MultiSite_10_Batch03"
curl -fLsS --retry 3 "$RAW/scripts/stage13/$(basename "$P")" -o "$P"
test "$(git hash-object "$P")" = "7348a5cb5e6c0ca1e0be6f69b07c81e48782d33b"
echo "STAGE13Q ME6 SCIENCE SCRIPT HASH PASS"
python3 -B -m py_compile "$P"
python3 -B "$P" --self-test
python3 -B "$P" --check 2>&1 | tee "$B/stage13q_Me6_check.log"
grep -qF "STAGE13Q READONLY CHECK PASS" "$B/stage13q_Me6_check.log"
python3 -B "$P" --run 2>&1 | tee "$B/stage13q_Me6_run.log"
grep -qF "STAGE13Q READONLY REPORT COMPLETE" "$B/stage13q_Me6_run.log"
echo "STAGE13Q ME6 33 SOURCE-NATIVE GROUP PASS/HOLD EVIDENCE COMPLETE; NO FORCING/MODEL WRITES"
