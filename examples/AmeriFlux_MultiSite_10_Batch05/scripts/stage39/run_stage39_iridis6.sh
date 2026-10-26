#!/usr/bin/env bash
set -euo pipefail

BASE="$HOME/ameriflux_batch05_stage39"
mkdir -p "$BASE"
COMMIT="b3e311dcdd9e8efd1d40e6e8ac44315794eb7308"
BLOB="72e9e146799dd550788f8ca8055395a5081dd116"
REMOTE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage39/39_fast_16_event_shortlist_safe_trial_and_US_UMB_source_inventory.py"
PY="$BASE/stage39.py"
curl -fLsS --retry 3 "$REMOTE" -o "$PY"
test "$(git hash-object "$PY")" = "$BLOB"
echo "STAGE39 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test

D38="$HOME/ameriflux_batch05_stage38/fast_closeout_20261026T173610Z_1368437"
D37="$HOME/ameriflux_batch05_stage37/boundary_before_after_20261026T170105Z_1109806"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
ROOT="/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"
for d in "$D38" "$D37" "$D27" "$D24" "$ROOT"; do
  test -d "$d" || { echo "MISSING_REQUIRED_SOURCE_DIRECTORY $d" >&2; exit 1; }
done

OUT="$BASE/actual_shortlist_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" \
  --stage38-dir "$D38" \
  --stage37-dir "$D37" \
  --stage27-dir "$D27" \
  --stage24-dir "$D24" \
  --sites-root "$ROOT" \
  --out "$OUT" \
  2>&1 | tee "$BASE/stage39.log"

echo "STAGE39_REPORTS=$OUT"
cat "$OUT/STAGE39_SHORTLIST_MANUAL_DECISIONS_AND_NEXT_ACTIONS.md"
echo "STAGE39 RESEARCH_ONLY; NO ORIGINAL OR DATM MODIFICATIONS"
