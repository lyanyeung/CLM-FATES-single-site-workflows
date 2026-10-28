#!/usr/bin/env bash
# SHA-pinned Batch03 US-Me6 all 46 missing original source HH,
# 17 within held Run14-18, 29 outside, read-only scientific assessment.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch03_stage13ah"
mkdir -p "$BASE"
PIN="11c3588d3f7637c39ffa6d6445930f5c3c21ddc0"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13"
while read -r HASH NAME; do
  curl -fLsS --retry 3 "$RAW/$NAME" -o "$BASE/$NAME"
  test "$(git hash-object "$BASE/$NAME")" = "$HASH"
done <<'SCIENCE_SOURCE_PINS'
3303da0a5adce5463e270502094046d005d0dca5 13ah_Me6_46_remaining_native_missing_source_ERA_context_READONLY.py
de62b7f6d1001fafa923163e565b2945bb2a8816 13_validation_Me6_six_run_repair_candidates.py
734a9d988f45c9628131e77b669913d9b0f4e8ae 13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py
5a8dc69f5fb65015a9b7c9096153935684f466a8 13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py
SCIENCE_SOURCE_PINS
echo "STAGE13AH FOUR SCIENCE SOURCES AND SHA VERIFIED"
python3 -B - "$BASE" <<'PY'
import sys
from pathlib import Path
for p in Path(sys.argv[1]).glob("*.py"):
    compile(p.read_text(),str(p),"exec")
print("STAGE13AH SYNTAX PASS | NO WRITES",flush=True)
PY
SCRIPT="$BASE/13ah_Me6_46_remaining_native_missing_source_ERA_context_READONLY.py"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --run 2>&1 | tee "$BASE/stage13ah_46_original_tower_ERA_full.log"
grep -qF "STAGE13AH ALL 46 MISSING ORIGINAL TOWER ERA BEFORE AFTER REVIEW COMPLETE" \
    "$BASE/stage13ah_46_original_tower_ERA_full.log"
echo "STAGE13AH ORIGINAL 46 NATIVE SOURCE REVIEW COMPLETE | NO MODEL/FORCING WRITES"
