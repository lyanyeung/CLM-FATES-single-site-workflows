#!/usr/bin/env bash
# US-MMS: one SHA-pinned, once-only 16 hourly gaps + original 18 ERA anomaly
# manual science read-only review. NO forcing/shadow/DATM/Slurm modification.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
D="$HOME/ameriflux_batch03_US_MMS_onepass"
mkdir -p "$D"
F="$D/14b_US_MMS_16hour_manual_onepass_READONLY.py"
curl -fLsS --retry 3 \
  "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/1b6b463c47f42707e45a070d74e73f020c577460/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14b_US_MMS_16hour_manual_onepass_READONLY.py" \
  -o "$F"
test "$(git hash-object "$F")" = "d6bd10b5d125f4d8daeb01071af7bfa26f82f4f5"
echo "US-MMS ONEPASS SOURCE GIT BLOB VERIFIED"
python3 -B - "$F" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1])
compile(s.read_text(),str(s),"exec")
print("US-MMS PYTHON SYNTAX PASS",flush=True)
PY
python3 -B "$F" --self-test
# Full signed original source integrity and source/manual audit executes once.
python3 -B "$F" --run 2>&1 | tee "$D/US_MMS_16H_18ERA_MANUAL_ONEPASS.log"
grep -qF "US-MMS 16-HOUR MANUAL ONEPASS SUCCESS" "$D/US_MMS_16H_18ERA_MANUAL_ONEPASS.log"
echo "US-MMS ONEPASS FINISHED; candidate decisions only; original forcing unchanged"
