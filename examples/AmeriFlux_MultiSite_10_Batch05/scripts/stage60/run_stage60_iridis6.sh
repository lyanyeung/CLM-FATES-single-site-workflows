#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage60"
mkdir -p "$BASE"
COMMIT="e3a8032b9e21d6ade1475e7caa2b3d93b81ecf6d"
BLOB="3a7cf4365b7168620c758992e7c33e0faee0a1b2"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage60/60_Wjs2018_original_VPD_MDS_QC_49HH_READONLY.py"
PY="$BASE/stage60.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$PY"
test "$(git hash-object "$PY")" = "$BLOB"
echo "STAGE60 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test
D59="$HOME/ameriflux_batch05_stage59/wjs2018_original_49HH_weather_source_20261028T233732Z_861557"
D58="$HOME/ameriflux_batch05_stage58/wjs2018_compare_four_methods_20261028T224753Z_551429"
D56="$HOME/ameriflux_batch05_stage56/eight_user_approved_interpolations_20261028T193428Z_4078597"
for D in "$D59" "$D58" "$D56"; do test -d "$D"; done
OUT="$BASE/wjs2018_exact_original_MDS_QC_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" --stage59-dir "$D59" --stage58-dir "$D58" --stage56-dir "$D56" --out "$OUT" 2>&1 | tee "$BASE/stage60.log"
echo "STAGE60_REPORTS=$OUT"
echo "STAGE60 ORIGINAL/174/2018_HOLD/DATM/SLURM UNCHANGED"
