#!/usr/bin/env bash
# US-Me6 Stage13AO original QA source 19HH and two QC2 border e/RH/QBOT
# NO original source change, no approved science, no DATM/AD400/Slurm.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch03_stage13ao"
mkdir -p "$BASE"
PIN="50f86a341c87583d402e0da173a868f93f2b9a6d"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13"
while read -r HASH NAME; do
  curl -fLsS --retry 3 "$RAW/$NAME" -o "$BASE/$NAME"
  test "$(git hash-object "$BASE/$NAME")" = "$HASH"
done <<'TEN_EXACT_SOURCE_PINS'
897f37b91c76b0200df2e120656b924700fea500 13ao_Me6_19HH_QC2_temperature_vapour_e_QBOT_edge_decomposition_READONLY.py
ade4f4fce3dc9e1e64a09b0e32baf80240a60481 13an_Me6_19HH_2015_QC2_edges_nearest_QC0_bias_stability_READONLY.py
df561eb8904b0147fc4a5aa0f977a5ec66545477 13am_Me6_19HH_joint_QC0_bias_corrected_ERA_RH_event_PREVIEW_READONLY.py
440e02cd7fd54d2a3fc9661a977d55125c513dde 13al_Me6_19HH_joint_cold_and_ERA_Tbias_QC0_leave_year_out_READONLY.py
5e82bd31484a3949a43829264f3ceb4d6c0f7832 13ak_Me6_19HH_multi_year_QC0_winter_temperature_donor_READONLY.py
62fb8b5225157f989d58c7a31d6a0a61237d4646 13aj_Me6_19HH_winter_2015_source_ERA_water_ice_QC0_validation_READONLY.py
c0b7f0429d352c82a10becf8d59d8a5d62987edf 13ah_Me6_46_remaining_native_missing_source_ERA_context_READONLY.py
de62b7f6d1001fafa923163e565b2945bb2a8816 13_validation_Me6_six_run_repair_candidates.py
734a9d988f45c9628131e77b669913d9b0f4e8ae 13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py
5a8dc69f5fb65015a9b7c9096153935684f466a8 13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py
TEN_EXACT_SOURCE_PINS
echo "STAGE13AO TEN ORIGINAL SCIENCE SOURCES GIT SHA VERIFIED"
python3 -B - "$BASE" <<'PY'
from pathlib import Path
import sys
for f in Path(sys.argv[1]).glob("*.py"):
    compile(f.read_text(),str(f),"exec")
print("STAGE13AO ALL ORIGINAL PYTHON SOURCES SYNTAX PASS | NO FORCING WRITES",flush=True)
PY
SCRIPT="$BASE/13ao_Me6_19HH_QC2_temperature_vapour_e_QBOT_edge_decomposition_READONLY.py"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --run 2>&1 | tee "$BASE/stage13ao_19HH_QC2_water_vapour_edges.log"
grep -qF "STAGE13AO 19HH QC2 VAPOUR PRESSURE AND QBOT EDGE DECOMPOSITION COMPLETE" \
  "$BASE/stage13ao_19HH_QC2_water_vapour_edges.log"
echo "STAGE13AO ORIGINAL QC2 VAPOUR BOUNDARY REPORT COMPLETE | 45 HH MISSING UNCHANGED, NO SLURM"
