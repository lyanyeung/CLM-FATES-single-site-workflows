#!/usr/bin/env bash
# US-Me6 Batch03 Stage13AG read-only daily science review for Run14-18.
# Exact actual AF source and historical independent QC0 CV, source sha sealed.
# No DATM, no production forcing, no Slurm.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch03_stage13ag"
mkdir -p "$BASE"
PIN="d84f1303aa00840564caa80162db6a4955725356"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13"
while read -r HASH NAME; do
  curl -fLsS --retry 3 "$RAW/$NAME" -o "$BASE/$NAME"
  test "$(git hash-object "$BASE/$NAME")" = "$HASH"
done <<'SCIENCE_PINS'
2d3b08b31c0b16ffa417e53c58bf10d67fca2dc4 13ag_Me6_five_held_long_runs_daily_QC0_ERA_group_review_READONLY.py
de62b7f6d1001fafa923163e565b2945bb2a8816 13_validation_Me6_six_run_repair_candidates.py
734a9d988f45c9628131e77b669913d9b0f4e8ae 13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py
5a8dc69f5fb65015a9b7c9096153935684f466a8 13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py
SCIENCE_PINS
echo "STAGE13AG FOUR PINNED PYTHON SOURCES VERIFIED"
python3 -B - "$BASE" <<'PY'
import sys
from pathlib import Path
for p in Path(sys.argv[1]).glob("*.py"):
    compile(p.read_text(),str(p),"exec")
print("STAGE13AG SYNTAX PASS | NO WRITES",flush=True)
PY
P="$BASE/13ag_Me6_five_held_long_runs_daily_QC0_ERA_group_review_READONLY.py"
python3 -B "$P" --self-test
python3 -B "$P" --run 2>&1 | tee "$BASE/stage13ag_original_daily_review.log"
grep -qF "STAGE13AG FIVE HELD RUN DAILY SCIENCE GROUP REPORT COMPLETE" "$BASE/stage13ag_original_daily_review.log"
echo "STAGE13AG COMPLETE; ONLY READONLY SCIENCE REPORT CREATED, NO DATM/SLURM"
