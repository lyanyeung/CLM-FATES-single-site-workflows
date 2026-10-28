#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage61"
mkdir -p "$BASE"
PY_COMMIT="22d8a1fe5ce688e6b846ce1eafbff067190d5298"
PY_BLOB="40bd1448f618cda0d03fd56c07692a6a8b9194e9"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage61/61_Wjs2018_30HH_source_scoped_interpolation_candidate_READONLY.py"
PY="$BASE/stage61.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT/$REL" -o "$PY"
test "$(git hash-object "$PY")" = "$PY_BLOB"
echo "STAGE61 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test
D60="$HOME/ameriflux_batch05_stage60/wjs2018_exact_original_MDS_QC_20261028T234456Z_908965"
D58="$HOME/ameriflux_batch05_stage58/wjs2018_compare_four_methods_20261028T224753Z_551429"
D56="$HOME/ameriflux_batch05_stage56/eight_user_approved_interpolations_20261028T193428Z_4078597"
for D in "$D60" "$D58" "$D56"; do test -d "$D"; done
OUT="$BASE/wjs2018_30HH_protected_linear_RH_shadow_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" --stage60-dir "$D60" --stage58-dir "$D58" --stage56-dir "$D56" --out "$OUT" 2>&1 | tee "$BASE/stage61.log"
echo "STAGE61_REPORTS=$OUT"
echo "STAGE61 30HH candidate is NOT approved, NOT merged, NOT forcing"
