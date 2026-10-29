#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage66_Whs"
mkdir -p "$BASE"
COMMIT="a702a2f144a6bbb0e02acfab04e27200e7594e84"
BLOB="736f7be58b5ca1426ac8adae745c4dd380f1765a"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage66/66_US_Whs_full_record_TA_jump_QC_READONLY.py"
PY="$BASE/stage66.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$PY"
test "$(git hash-object "$PY")" = "$BLOB"
echo "STAGE66 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test
OUT="$BASE/all_TA_jumps_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" --out "$OUT" 2>&1 | tee "$BASE/stage66.log"
echo "STAGE66_REPORTS=$OUT"
