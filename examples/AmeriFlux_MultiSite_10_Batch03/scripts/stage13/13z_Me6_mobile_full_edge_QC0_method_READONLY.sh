#!/usr/bin/env bash
# Stage13Z pin: original four 2015 halfhours, five full 30min boundaries.
# Source reports only. No shadow forcing modification, DATM or Slurm.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch03_stage13z"
mkdir -p "$BASE"
PIN="49dc297db6f8c54911fb1a3019966e7c525ab71b"
NAME="13z_Me6_fourHH_complete_QC0_boundary_method_screen_READONLY.py"
SCRIPT="$BASE/$NAME"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PIN/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13/$NAME"
curl -fLsS --retry 3 "$RAW" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "b857b880a4791f23cce88ad7e615fd11026ddbb2"
echo "STAGE13Z SOURCE SHA VERIFIED"
python3 -B - "$SCRIPT" <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1])
compile(p.read_text(), str(p), "exec")
print("STAGE13Z SYNTAX PASS | NO WRITES")
PY
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --check 2>&1 | tee "$BASE/stage13z_check.log"
grep -qF "STAGE13Z READONLY CHECK PASS" "$BASE/stage13z_check.log"
python3 -B "$SCRIPT" --run 2>&1 | tee "$BASE/stage13z_run.log"
grep -qF "STAGE13Z REPORT COMPLETE" "$BASE/stage13z_run.log"
echo "STAGE13Z COMPLETE | SOURCE SCIENCE ONLY; NO FORCING/DATM/SLURM"
