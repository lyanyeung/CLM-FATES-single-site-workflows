#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage40"
mkdir -p "$BASE"

COMMIT="6ae6899e00586fcfbfabe6924418263f7ff8a19c"
BLOB="6aa37fee2a4d3ed9c2726b0cc855ba6f06d9c099"
REMOTE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage40/40_original_humidity_physics_and_real_manual_decision_priorities.py"
SCRIPT="$BASE/stage40.py"

curl -fLsS --retry 3 "$REMOTE" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$BLOB"
echo "STAGE40 SOURCE VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test

D39="$HOME/ameriflux_batch05_stage39/actual_shortlist_20261026T175318Z_1490492"
D38="$HOME/ameriflux_batch05_stage38/fast_closeout_20261026T173610Z_1368437"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
for d in "$D39" "$D38" "$D27"; do
  test -d "$d" || { echo "SOURCE_DIRECTORY_MISSING $d" >&2; exit 1; }
done

OUT="$BASE/source_humidity_physics_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" \
  --stage39-dir "$D39" \
  --stage38-dir "$D38" \
  --stage27-dir "$D27" \
  --out "$OUT" \
  2>&1 | tee "$BASE/stage40.log"

echo "STAGE40_REPORTS=$OUT"
cat "$OUT/STAGE40_TRUE_HUMAN_REVIEW_AND_SAFE_PILOT_QUEUE.md"
echo "STAGE40 REPORT ONLY; NO ORIGINAL OR DATM FORCING MODIFICATIONS"
