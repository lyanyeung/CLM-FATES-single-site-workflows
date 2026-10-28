#!/usr/bin/env bash
# US-Me6 Batch03 source-only manual-review table; NO forcing or Slurm.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch03_stage13ab"
mkdir -p "$BASE"
PIN="b80a86c3d43e31d71a6ac584e67dbbd75ebc9f45"
NAME="13ab_Me6_14_exception_and_QC2_edge_review_READONLY.py"
S="$BASE/$NAME"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13/$NAME"
curl -fLsS --retry 3 "$RAW" -o "$S"
test "$(git hash-object "$S")" = "ce794182e8b39da85d7b35075bd2ae072e45e576"
echo "STAGE13AB SOURCE SHA VERIFIED"
python3 -B - "$S" <<'PY'
import sys
from pathlib import Path
p=Path(sys.argv[1])
compile(p.read_text(),str(p),"exec")
print("STAGE13AB SYNTAX PASS | NO WRITES")
PY
python3 -B "$S" --self-test
python3 -B "$S" --run 2>&1 | tee "$BASE/stage13ab_review.log"
grep -qF "STAGE13AB MANUAL REVIEW REPORT COMPLETE" "$BASE/stage13ab_review.log"
echo "STAGE13AB REVIEW DATA COMPLETE; NO SOURCE/FORCING/DATM/SLURM"
