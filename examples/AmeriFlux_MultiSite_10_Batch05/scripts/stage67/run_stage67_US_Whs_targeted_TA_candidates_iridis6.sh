#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage67_Whs"
mkdir -p "$BASE"
SCRIPT="$BASE/stage67_Whs.py"
SOURCE_COMMIT="f76c0a8ef07124a8b69b9b94fc34aa8c2aadf81f"
SOURCE_BLOB="fa209d5e2483f48769d8e24e0725bb23a6cf621a"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage67/67_US_Whs_QC1_to_QC2_QC0_to_QC1_TA_repair_candidates.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$SOURCE_COMMIT/$REL" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$SOURCE_BLOB"
echo "STAGE67 SOURCE VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
D66="$HOME/ameriflux_batch05_stage66_Whs/all_TA_jumps_20261029T033601Z_2119759"
test -d "$D66"
OUT="$BASE/Whs_selected_TA_reconstruction_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" --stage66-dir "$D66" --out "$OUT" 2>&1 | tee "$BASE/stage67.log"
echo "STAGE67_REPORTS=$OUT"
echo "STAGE67 ORIGINAL_SOURCE/204/VPD/QC/DATM/CIME/SLURM UNCHANGED"
