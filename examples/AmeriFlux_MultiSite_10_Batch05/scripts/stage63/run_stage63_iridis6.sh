#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage63"
mkdir -p "$BASE"
COMMIT="08b0c12231d03ac56aaabc70ec934e10df65b880"
BLOB="a362989caba34c2d7bb6daf56ce4777d71abc789"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage63/63_exact_204_overlay_vs_original_1750_ten_site_remaining_READONLY.py"
SCRIPT="$BASE/stage63.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$BLOB"
echo "STAGE63 SOURCE VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
D25="$HOME/ameriflux_batch05_stage25/crosswalk_20261026T034622Z_1628022"
D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
D62="$HOME/ameriflux_batch05_stage62/wjs2018_30HH_approved_versioned_204_20261029T001706Z_431668"
for D in "$D25" "$D24" "$D62"; do test -d "$D"; done
OUT="$BASE/exact10_site_204_crosswalk_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" --stage25-dir "$D25" --stage24-dir "$D24" --stage62-dir "$D62" --out "$OUT" 2>&1 | tee "$BASE/stage63.log"
cat "$OUT/STAGE63_TEN_SITE_REMAINING_APPROVAL_AND_HOLD_REPORT.md"
echo "STAGE63_REPORTS=$OUT"
echo "STAGE63 NO ORIGINAL/204/DATM/CIME/SLURM MODIFICATIONS"
