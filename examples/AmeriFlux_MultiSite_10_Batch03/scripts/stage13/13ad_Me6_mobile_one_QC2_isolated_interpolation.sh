#!/usr/bin/env bash
# Strictly one original QC2 anomalous center, 2017-07-04 12:00, US-Me6.
# Two tower source QC1 anchors require original 5-HH physical/continuity
# verification; exact user conditional policy pinned. No production/model.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch03_stage13ad"
mkdir -p "$BASE"
PY="$BASE/13ad_Me6_isolated_QC2_single_spike_user_conditional_shadow.py"
POL="$BASE/US-Me6_conditional_isolated_spike_interpolation_20261028.json"
curl -fLsS --retry 3 \
 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/eda999a4254c6eeb29fb78d29c835cdef3c6f4b5/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13/13ad_Me6_isolated_QC2_single_spike_user_conditional_shadow.py" \
 -o "$PY"
curl -fLsS --retry 3 \
 "https://raw.githubusercontent.com/lyanyeung/Non-Competition-CLM-experiment/04a563e6ef463c935ddd207f4f4ffa974e256008/examples/AmeriFlux_Batch03_10/decisions/US-Me6_conditional_isolated_spike_interpolation_20261028.json" \
 -o "$POL"
test "$(git hash-object "$PY")" = "00d2844d5e2be75ac5ff4c998c3378d09f38bce2"
test "$(git hash-object "$POL")" = "a8b70432719798b15898039d4a4e6600dc18f533"
echo "STAGE13AD SCIENCE PYTHON AND USER POLICY SOURCE HASH VERIFIED"
python3 -B - "$PY" <<'PYTHON'
import sys
from pathlib import Path
p=Path(sys.argv[1])
compile(p.read_text(),str(p),"exec")
print("STAGE13AD SYNTAX PASS | NO WRITES",flush=True)
PYTHON
python3 -B "$PY" --self-test
python3 -B "$PY" --check --policy "$POL" 2>&1 | tee "$BASE/stage13ad_check.log"
grep -qF "STAGE13AD READONLY EXACT SINGLE-POINT PRECHECK PASS" "$BASE/stage13ad_check.log"
python3 -B "$PY" --apply --policy "$POL" 2>&1 | tee "$BASE/stage13ad_apply.log"
grep -qF "STAGE13AD ISOLATED ONE-HH CONDITIONAL RESEARCH SHADOW COMPLETE" "$BASE/stage13ad_apply.log"
echo "STAGE13AD RESEARCH TRIAL READY; NO SOURCE/PERIOD/DATM/SLURM CHANGES"
