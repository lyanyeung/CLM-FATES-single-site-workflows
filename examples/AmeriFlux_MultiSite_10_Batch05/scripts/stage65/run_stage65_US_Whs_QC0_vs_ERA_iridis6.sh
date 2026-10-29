#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage65_Whs"
mkdir -p "$BASE"
COMMIT="9aaca947101905f9062f9a8a3c82c1859ec2b0d5"
BLOB="3c53fb7a8028c13a51449b61192c0f3f3170e5cf"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage65/65_US_Whs_20120526_QC0_TA_vs_source_ERA_before_after_READONLY.py"
PY="$BASE/stage65.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$PY"
test "$(git hash-object "$PY")" = "$BLOB"
echo "STAGE65 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test
D64="$HOME/ameriflux_batch05_stage64_Whs/Whs_one_original_HH_manual_20261029T025926Z_1934005"
test -d "$D64"
OUT="$BASE/Whs_20120526_original_QC0_TA_vs_ERA_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" --stage64-dir "$D64" --out "$OUT" 2>&1 | tee "$BASE/stage65.log"
echo "STAGE65_REPORTS=$OUT"
echo "STAGE65 SOURCE ORIGINAL /204/DATM/SLURM NOT MODIFIED"
