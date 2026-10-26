#!/usr/bin/env bash
set -euo pipefail

BASE="$HOME/ameriflux_batch05_stage38"
mkdir -p "$BASE"

# GitHub source commit and Git blob SHA are immutable science provenance.
PY_COMMIT="60cbc5520441e90105f94c7c0843cdb477186ba5"
PY_BLOB="d6884f53b3a7f3eae46860862a2c3ea023a585bf"
REMOTE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT"
RELPATH="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage38/38_fast_small_site_closeout_and_Vcp_full_episode_method_trials_readonly.py"
SCRIPT="$BASE/stage38.py"

curl -fLsS --retry 3 "$REMOTE/$RELPATH" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$PY_BLOB"
echo "STAGE38 SOURCE VERIFIED"

python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test

D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
D37="$HOME/ameriflux_batch05_stage37/boundary_before_after_20261026T170105Z_1109806"
D35="$HOME/ameriflux_batch05_stage35/science_VPD_trial_20261026T132821Z_715715"
ROOT="/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"

for d in "$D27" "$D24" "$D37" "$D35" "$ROOT"; do
  if [[ ! -d "$d" ]]; then
    printf 'SOURCE_DIRECTORY_MISSING %s\n' "$d" >&2
    exit 1
  fi
done

OUT="$BASE/fast_closeout_$(date -u +%Y%m%dT%H%M%SZ)_$$"
echo "STAGE38_PLAN source original unchanged; new report $OUT"

python3 -B "$SCRIPT" \
  --stage27-dir "$D27" \
  --stage24-dir "$D24" \
  --stage37-dir "$D37" \
  --stage35-dir "$D35" \
  --sites-root "$ROOT" \
  --out "$OUT" \
  2>&1 | tee "$BASE/stage38.log"

echo "STAGE38_REPORTS=$OUT"
cat "$OUT/STAGE38_SMALL_SITE_AND_FULL_VCP_EVENT_CLOSURE.md"
echo "STAGE38_COMPLETE_NO_ORIGINAL_WRITES"
