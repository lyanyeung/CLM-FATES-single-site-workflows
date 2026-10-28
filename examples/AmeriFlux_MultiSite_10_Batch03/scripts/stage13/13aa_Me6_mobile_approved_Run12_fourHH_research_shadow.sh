#!/usr/bin/env bash
# Stage13AA: USER APPROVED exact 4 HH US-Me6 Run12 source research shadow only.
# Never updates original forcing or submits jobs; approval and science SHA sealed.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
B="$HOME/ameriflux_batch03_stage13aa"
mkdir -p "$B"
SRC="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/e3351cacb1ac67d6652ba09042650d3cbb26e746/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13/13aa_Me6_Run12_fourHH_operator_approved_QC0_linear_SHADOW.py"
APR="https://raw.githubusercontent.com/lyanyeung/Non-Competition-CLM-experiment/ff3e2a9e085dee022d6f129c40e00232b50f3c76/examples/AmeriFlux_Batch03_10/decisions/US-Me6_Run12_20150926_QC0_linear_user_approval.json"
SCRIPT="$B/13aa_Me6_Run12_fourHH_operator_approved_QC0_linear_SHADOW.py"
APPROVAL="$B/US-Me6_Run12_20150926_QC0_linear_user_approval.json"
curl -fLsS --retry 3 "$SRC" -o "$SCRIPT"
curl -fLsS --retry 3 "$APR" -o "$APPROVAL"
test "$(git hash-object "$SCRIPT")" = "e0c945f54de2a2533d203172c36c075ff2cd89ac"
test "$(git hash-object "$APPROVAL")" = "a9d7275590eb4c7f4294d324583c2455b52abec0"
echo "STAGE13AA PYTHON AND USER APPROVAL SOURCE HASH VERIFIED"
python3 -B - "$SCRIPT" <<'PY'
import sys
from pathlib import Path
p=Path(sys.argv[1])
compile(p.read_text(),str(p),"exec")
print("STAGE13AA SOURCE SYNTAX PASS | NO WRITES")
PY
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --check --approval "$APPROVAL" 2>&1 | tee "$B/stage13aa_check.log"
grep -qF "STAGE13AA READONLY CHECK PASS" "$B/stage13aa_check.log"
python3 -B "$SCRIPT" --apply --approval "$APPROVAL" 2>&1 | tee "$B/stage13aa_apply.log"
grep -qF "STAGE13AA APPROVED FOUR-HH RESEARCH SHADOW COMPLETE" "$B/stage13aa_apply.log"
echo "STAGE13AA RESEARCH SHADOW VERIFIED; NO POSTV5/DATM/AD400/SLURM"
