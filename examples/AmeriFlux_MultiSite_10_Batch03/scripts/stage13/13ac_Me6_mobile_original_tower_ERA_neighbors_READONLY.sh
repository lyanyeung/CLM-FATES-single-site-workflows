#!/usr/bin/env bash
# Source-only US-Me6 Batch03: original tower+paired ERA, before/after,
# 14 T>8C events, nine unique >4hPa candidate edges, ±2h native context.
# No forcing, no DATM, no Slurm.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch03_stage13ac"
mkdir -p "$BASE"
PIN="2f9b984d603fc9c4d548c3757b9c42e0368870af"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13"
while read -r EXPECTED NAME; do
  curl -fLsS --retry 3 "$RAW/$NAME" -o "$BASE/$NAME"
  test "$(git hash-object "$BASE/$NAME")" = "$EXPECTED"
done <<'PYTHON_SOURCES'
f9d07579b0aace8a4e4e3eb8585e2f74b813f530 13ac_Me6_tower_ERA_original_vs_candidate_neighbor_review_READONLY.py
de62b7f6d1001fafa923163e565b2945bb2a8816 13_validation_Me6_six_run_repair_candidates.py
734a9d988f45c9628131e77b669913d9b0f4e8ae 13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py
5a8dc69f5fb65015a9b7c9096153935684f466a8 13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py
PYTHON_SOURCES
echo "STAGE13AC FOUR PYTHON SOURCE SHA VERIFIED"
python3 -B - "$BASE" <<'PY'
import sys
from pathlib import Path
for p in Path(sys.argv[1]).glob("*.py"):
    compile(p.read_text(),str(p),"exec")
print("STAGE13AC SYNTAX PASS | NO WRITES",flush=True)
PY
SCRIPT="$BASE/13ac_Me6_tower_ERA_original_vs_candidate_neighbor_review_READONLY.py"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --run 2>&1 | tee "$BASE/stage13ac_original_tower_ERA_full_review.log"
grep -qF "STAGE13AC TOWER ERA ORIGINAL/HYPOTHETICAL COMPARISON COMPLETE" "$BASE/stage13ac_original_tower_ERA_full_review.log"
echo "STAGE13AC REVIEW READY; NO SOURCE/FORCING/SLURM"
