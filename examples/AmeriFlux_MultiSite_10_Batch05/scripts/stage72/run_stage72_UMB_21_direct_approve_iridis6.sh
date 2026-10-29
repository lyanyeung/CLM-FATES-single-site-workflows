#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage72_UMB"
mkdir -p "$BASE"
COMMIT="2db26af772756d41002e7eee1bf620ac24ca4afa"
BLOB="2e3f2b9eba5827c6541999b16fc1f6239bc27006"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage72/72_US_UMB_negative_RH_21HH_direct_approved_240.py"
PY="$BASE/stage72.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$PY"
test "$(git hash-object "$PY")" = "$BLOB"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test
D63="$HOME/ameriflux_batch05_stage63/exact10_site_204_crosswalk_20261029T025331Z_1904396"
D69="$HOME/ameriflux_batch05_stage69_70/UMd_219_directly_approved_20261029T040340Z_2262688"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
OUT="$BASE/UMB_240_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" --stage63-dir "$D63" --stage69-dir "$D69" --stage27-dir "$D27" --out "$OUT"
echo "STAGE72_REPORTS=$OUT"
