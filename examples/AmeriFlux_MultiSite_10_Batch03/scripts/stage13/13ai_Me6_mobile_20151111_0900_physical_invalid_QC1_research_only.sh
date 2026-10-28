#!/usr/bin/env bash
# Batch03 US-Me6 one physically invalid source 2015-11-11 09:00 QC1
# Single center VPD/QBOT to independent research-only shadow.
# No production science, no DATM/AD400/Slurm.
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env
B="$HOME/ameriflux_batch03_stage13ai"
mkdir -p "$B"
P="$B/13ai_Me6_20151111_0900_physically_invalid_QC1_single_linear_SHADOW.py"
curl -fLsS --retry 3 \
 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/b18be10227dcaa8379cb67752f20bfd08f82a06e/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage13/13ai_Me6_20151111_0900_physically_invalid_QC1_single_linear_SHADOW.py" \
 -o "$P"
test "$(git hash-object "$P")" = "72f258ae469866ec85309f8bbeb948ef0d981cb5"
echo "STAGE13AI EXACT SCIENCE PYTHON GIT SOURCE VERIFIED"
python3 -B - "$P" <<'PY'
from pathlib import Path
import sys
path=Path(sys.argv[1])
compile(path.read_text(),str(path),"exec")
print("STAGE13AI SOURCE AST SYNTAX PASS | NO WRITES",flush=True)
PY
python3 -B "$P" --self-test
python3 -B "$P" --check 2>&1 | tee "$B/stage13ai_check.log"
grep -qF "STAGE13AI EXACT 46->45 MISSING READONLY SCIENCE CHECK PASS" "$B/stage13ai_check.log"
python3 -B "$P" --apply 2>&1 | tee "$B/stage13ai_trial.log"
grep -qF "STAGE13AI EXACT PHYSICS-INVALID SINGLE QC1 RESEARCH SHADOW COMPLETE" "$B/stage13ai_trial.log"
echo "STAGE13AI ONE RESEARCH SHADOW SUCCESSFULLY GENERATED | NO POSTV5/DATM/AD400/SLURM"
