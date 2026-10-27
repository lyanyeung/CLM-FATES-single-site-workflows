#!/usr/bin/env bash
# Source-only US-Me6 six remaining original QC1 run comparison:
# nearest measured tower QC0 RH vs native ERA RH, original 2017 QC2 edges.
# No new RH source approval, 8C/4hPa relaxation or model outputs.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
B="$HOME/ameriflux_batch03_stage13x"
mkdir -p "$B"
R="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/eab06436fa29b1ffd74a6515be8a8d1058133a29/examples/AmeriFlux_MultiSite_10_Batch03"
S="$B/13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py"
P="$B/13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py"
curl -fLsS --retry 3 "$R/scripts/stage13/$(basename "$S")" -o "$S"
curl -fLsS --retry 3 "$R/scripts/stage13/$(basename "$P")" -o "$P"
test "$(git hash-object "$S")" = "734a9d988f45c9628131e77b669913d9b0f4e8ae"
test "$(git hash-object "$P")" = "5a8dc69f5fb65015a9b7c9096153935684f466a8"
echo "STAGE13X SIGNED SOURCE SCIENCE SCRIPT SHA PASS"
python3 -B -m py_compile "$S" "$P"
python3 -B "$S" --self-test
python3 -B "$S" --check 2>&1 | tee "$B/stage13x_Me6_check.log"
grep -qF "STAGE13X READONLY CHECK PASS" "$B/stage13x_Me6_check.log"
python3 -B "$S" --run 2>&1 | tee "$B/stage13x_Me6_run.log"
grep -qF "STAGE13X QC0 MEASURED RH VS ERA SOURCE SKILL AND 2017 QC2 EDGES REPORT COMPLETE" "$B/stage13x_Me6_run.log"
echo "STAGE13X ORIGINAL QC0 RH REFERENCE AND QC2 EDGES COMPLETE; NO FORCING/DATM/SLURM"
