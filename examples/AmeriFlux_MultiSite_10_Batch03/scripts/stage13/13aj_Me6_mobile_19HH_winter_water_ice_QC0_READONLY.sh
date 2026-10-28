#!/usr/bin/env bash
# AmeriFlux Batch03 US-Me6 Stage13AJ: exact 19 2014/15 winter source
# water/ice and ERA RH transfer QC0 evidence, all READONLY, no Slurm.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch03_stage13aj"
mkdir -p "$BASE"
PIN="e12458d60dce9ce11fd1007489cfc8e651e32d7a"
URL="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13"
while read -r SHA NAME; do
  curl -fLsS --retry 3 "$URL/$NAME" -o "$BASE/$NAME"
  test "$(git hash-object "$BASE/$NAME")" = "$SHA"
done <<'PINNED_PYTHON'
62fb8b5225157f989d58c7a31d6a0a61237d4646 13aj_Me6_19HH_winter_2015_source_ERA_water_ice_QC0_validation_READONLY.py
c0b7f0429d352c82a10becf8d59d8a5d62987edf 13ah_Me6_46_remaining_native_missing_source_ERA_context_READONLY.py
de62b7f6d1001fafa923163e565b2945bb2a8816 13_validation_Me6_six_run_repair_candidates.py
734a9d988f45c9628131e77b669913d9b0f4e8ae 13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py
5a8dc69f5fb65015a9b7c9096153935684f466a8 13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py
PINNED_PYTHON
echo "STAGE13AJ FIVE SOURCE PYTHON GIT BLOBS VERIFIED"
python3 -B - "$BASE" <<'PY'
import sys
from pathlib import Path
for p in Path(sys.argv[1]).glob("*.py"):
    compile(p.read_text(),str(p),"exec")
print("STAGE13AJ PYTHON SYNTAX PASS | NO WRITES",flush=True)
PY
SCRIPT="$BASE/13aj_Me6_19HH_winter_2015_source_ERA_water_ice_QC0_validation_READONLY.py"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --run 2>&1 | tee "$BASE/stage13aj_19HH_source_ERA_QC0.log"
grep -qF "STAGE13AJ NINETEEN COLD ORIGINAL SOURCE WATER ICE QC0 SCIENCE REPORT COMPLETE" \
 "$BASE/stage13aj_19HH_source_ERA_QC0.log"
echo "STAGE13AJ ORIGINAL 19HH COLD RESEARCH REPORT COMPLETE | NO REPAIR OR SLURM"
