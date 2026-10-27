#!/usr/bin/env bash
# US-Me6 after successful Stage13s. SCIENTIFIC READ-ONLY short original
# 2015-09-26 4HH QC1 HOLD, original 2 measured QC0 bookends.
# Reanalysis vs QC0-anchored interpolation strictly *diagnostic* only.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
B="$HOME/ameriflux_batch03_stage13t"
mkdir -p "$B"
R="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/3ee9ca91dcff841d80755d954d052ecaba374c43/examples/AmeriFlux_MultiSite_10_Batch03"
S="$B/13t_Me6_20150926_four_QC1_measured_QC0_ERA_RH_READONLY.py"
P="$B/13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py"
curl -fLsS --retry 3 "$R/scripts/stage13/$(basename "$S")" -o "$S"
curl -fLsS --retry 3 "$R/scripts/stage13/$(basename "$P")" -o "$P"
test "$(git hash-object "$S")" = "74b333f3f21b54c083df85b76f620113c6370c3e"
test "$(git hash-object "$P")" = "5a8dc69f5fb65015a9b7c9096153935684f466a8"
echo "STAGE13T PINNED ORIGINAL SOURCE DIAGNOSTIC HASH PASS"
python3 -B -m py_compile "$S" "$P"
python3 -B "$S" --self-test
python3 -B "$S" --check 2>&1 | tee "$B/stage13t_Me6_check.log"
grep -qF "STAGE13T READONLY CHECK PASS" "$B/stage13t_Me6_check.log"
python3 -B "$S" --run 2>&1 | tee "$B/stage13t_Me6_run.log"
grep -qF "STAGE13T ME6 20150926 SOURCE QC0 AND ERA-RH FIVE EDGES DIAGNOSTIC COMPLETE" "$B/stage13t_Me6_run.log"
echo "STAGE13T COMPLETE READONLY; ORIGINAL 4HH SOURCE HOLD; NO FORCING/DATM/SLURM"
