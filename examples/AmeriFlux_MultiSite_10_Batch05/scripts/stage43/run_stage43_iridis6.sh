#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage43"
mkdir -p "$BASE"
COMMIT="952a2ea64c99c7468c782d37a7b0aa0e4c4f04c5"
BLOB="9f55b4094ffafec88f6aed47db448d6173f1bbd5"
REMOTE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage43/43_shortlist_10_numeric_trials_23_science_holds.py"
PY="$BASE/stage43.py"
curl -fLsS --retry 3 "$REMOTE" -o "$PY"
test "$(git hash-object "$PY")" = "$BLOB"
echo "STAGE43 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test

D42="$HOME/ameriflux_batch05_stage42/postv5_research_20261026T190608Z_2870133"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
for d in "$D42" "$D27" "$D24"; do
  test -d "$d" || { echo "MISSING_REQUIRED_SOURCE $d" >&2; exit 1; }
done
OUT="$BASE/numeric_15_source_trial_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" \
  --stage42-dir "$D42" \
  --stage27-dir "$D27" \
  --stage24-dir "$D24" \
  --out "$OUT" 2>&1 | tee "$BASE/stage43.log"

echo "STAGE43_REPORTS=$OUT"
echo "STAGE43 10 EVENT OPTIONS:"
cat "$OUT/stage43_TEN_NUMERIC_EVENTS.csv"
echo "STAGE43 OTHER 23 METHODS:"
cat "$OUT/stage43_23_BLOCKED_METHODS.csv"
echo "STAGE43 REPORT-ONLY; NO SOURCE/DATM/SLURM CHANGE"
