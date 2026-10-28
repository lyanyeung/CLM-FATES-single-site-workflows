#!/usr/bin/env bash
# AmeriFlux Batch03 US-Me6 5 held source runs; SHA-pinned standalone read-only.
# Scan source BEFORE/AFTER 2 native HH, do not rewrite Stage13AD or other data.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch03_stage13ae"
mkdir -p "$BASE"
PIN="aced432514f861e20e7960e61843f9660dbbcb0e"
ROOT="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13"
while read -r DIGEST NAME; do
  curl -fLsS --retry 3 "$ROOT/$NAME" -o "$BASE/$NAME"
  test "$(git hash-object "$BASE/$NAME")" = "$DIGEST"
done <<'SOURCES'
04a88cb3bfd559552f09cc520aa6daa08a486583 13ae_Me6_all_five_held_runs_isolated_original_spike_screen_READONLY.py
de62b7f6d1001fafa923163e565b2945bb2a8816 13_validation_Me6_six_run_repair_candidates.py
734a9d988f45c9628131e77b669913d9b0f4e8ae 13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py
5a8dc69f5fb65015a9b7c9096153935684f466a8 13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py
SOURCES
echo "STAGE13AE FOUR PINNED PYTHON SOURCES VERIFIED"
python3 -B - "$BASE" <<'PY'
import sys
from pathlib import Path
for p in Path(sys.argv[1]).glob("*.py"):compile(p.read_text(),str(p),"exec")
print("STAGE13AE PYTHON SYNTAX PASS | NO WRITES",flush=True)
PY
SCRIPT="$BASE/13ae_Me6_all_five_held_runs_isolated_original_spike_screen_READONLY.py"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --run 2>&1 | tee "$BASE/stage13ae_original_source_spikes.log"
grep -qF "STAGE13AE SOURCE ORIGINAL FIVE-RUN ISOLATED REVIEW COMPLETE" "$BASE/stage13ae_original_source_spikes.log"
echo "STAGE13AE REPORT DONE | ORIGINAL TOWER/ERA/RESEARCH SHADOW IMMUTABLE"
