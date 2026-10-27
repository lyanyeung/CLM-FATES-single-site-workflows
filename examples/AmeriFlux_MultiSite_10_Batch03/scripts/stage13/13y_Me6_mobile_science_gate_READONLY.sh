#!/usr/bin/env bash
# Batch03 / US-Me6 Stage13Y: scientific gate only (no forcing, DATM, AD400, Slurm).
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch03_stage13y"
mkdir -p "$BASE"
PIN="f12472a2cb174d0fb9f19a9d73e39f8c6c3dc9f3"
NAME="13y_Me6_eleven_subepisodes_operator_gate_READONLY.py"
SCRIPT="$BASE/$NAME"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13/$NAME"
curl -fLsS --retry 3 "$RAW" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "6e79833e9dc54b64c2bd11a45ad134be396737f7"
echo "STAGE13Y PINNED PYTHON SCRIPT SOURCE SHA VERIFIED"
python3 -B - "$SCRIPT" <<'PY'
import sys
from pathlib import Path
p=Path(sys.argv[1])
compile(p.read_text(),str(p),"exec")
print("STAGE13Y SYNTAX PASS | NO WRITES",flush=True)
PY
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --check 2>&1 | tee "$BASE/stage13y_check.log"
grep -qF "STAGE13Y READONLY CHECK PASS" "$BASE/stage13y_check.log"
python3 -B "$SCRIPT" --run 2>&1 | tee "$BASE/stage13y_run.log"
grep -qF "STAGE13Y REPORT COMPLETE" "$BASE/stage13y_run.log"
echo "STAGE13Y COMPLETE | SOURCE SCIENCE REPORT ONLY; NO FORCING/DATM/SLURM"
