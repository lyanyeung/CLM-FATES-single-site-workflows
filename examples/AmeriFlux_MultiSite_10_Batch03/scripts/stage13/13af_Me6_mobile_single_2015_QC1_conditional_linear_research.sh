#!/usr/bin/env bash
# US-Me6 Stage13AF -- exactly Run14 source 2015-11-12 13:30 QC1
# self-test + SHA scientific read-only check before separate research shadow.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
B="$HOME/ameriflux_batch03_stage13af"
mkdir -p "$B"
P="$B/13af_Me6_Run14_one_source_QC1_spike_conditional_LINEAR_SHADOW.py"
curl -fLsS --retry 3 \
  "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/32f66b4c7fee5efc72cd8c78a3fb904bea5cb203/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13/13af_Me6_Run14_one_source_QC1_spike_conditional_LINEAR_SHADOW.py" \
  -o "$P"
test "$(git hash-object "$P")" = "ad245c8bcf2b332f1e3b1ec60561656a3c37c6ca"
echo "STAGE13AF ORIGINAL PINNED PYTHON SHA VERIFIED"
python3 -B - "$P" <<'PY'
import sys
from pathlib import Path
f=Path(sys.argv[1])
compile(f.read_text(),str(f),"exec")
print("STAGE13AF PYTHON SYNTAX PASS | NO WRITES",flush=True)
PY
python3 -B "$P" --self-test
python3 -B "$P" --check 2>&1 | tee "$B/stage13af_check.log"
grep -qF "STAGE13AF READONLY PRECHECK PASS" "$B/stage13af_check.log"
python3 -B "$P" --apply 2>&1 | tee "$B/stage13af_apply.log"
grep -qF "STAGE13AF ONE EXACT Run14 QC1 RESEARCH SHADOW COMPLETE" "$B/stage13af_apply.log"
echo "STAGE13AF SCIENTIFIC ONE-HH SHADOW READY | NO POSTV5/DATM/AD400/SLURM"
