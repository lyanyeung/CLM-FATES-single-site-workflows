#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage42"
mkdir -p "$BASE"

PY_COMMIT="6233a57b3e82d1b2ca9ad42523aedef70fab0368"
PY_BLOB="5f68fdbe658470841da30a449f7143deb2bd8421"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT"
RELPATH="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage42/42_postv5_isolated_15_ERA_events_and_UMB23_fullset_source_trials.py"
PY="$BASE/stage42.py"
curl -fLsS --retry 3 "$RAW/$RELPATH" -o "$PY"
test "$(git hash-object "$PY")" = "$PY_BLOB"
echo "STAGE42 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test

D41="$HOME/ameriflux_batch05_stage41/ERA_original_RH_policy_20261026T182003Z_1665949"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
ROOT="/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"
for d in "$D41" "$D27" "$D24" "$ROOT"; do
  test -d "$d" || { echo "SOURCE_DIRECTORY_MISSING $d" >&2; exit 1; }
done

OUT="$BASE/postv5_research_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" \
  --stage41-dir "$D41" \
  --stage27-dir "$D27" \
  --stage24-dir "$D24" \
  --sites-root "$ROOT" \
  --out "$OUT" 2>&1 | tee "$BASE/stage42.log"

echo "STAGE42_REPORTS=$OUT"
cat "$OUT/STAGE42_POSTV5_BOUNDARIES_AND_UMB_SOURCE_CLOSURE.md"
echo "STAGE42 RESEARCH-ONLY; NO FORCING/ORIGINAL WRITES"
