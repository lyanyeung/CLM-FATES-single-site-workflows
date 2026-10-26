#!/usr/bin/env bash
set -euo pipefail

BASE="$HOME/ameriflux_batch05_stage41"
mkdir -p "$BASE"

COMMIT="6583ccdfd8b6195b1a5b291fb4c8199a4c3a990b"
BLOB="2eeaf59d2aa53ed410af13620e6cbcb286dad3e6"
REMOTE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage41/41_policy_negative_RH_ERA_overlay_trial_and_US_UMB_FULLSET_source.py"
SCRIPT="$BASE/stage41.py"

curl -fLsS --retry 3 "$REMOTE" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$BLOB"
echo "STAGE41 SOURCE VERIFIED"

python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test

D40="$HOME/ameriflux_batch05_stage40/source_humidity_physics_20261026T180721Z_1601029"
D39="$HOME/ameriflux_batch05_stage39/actual_shortlist_20261026T175318Z_1490492"
D38="$HOME/ameriflux_batch05_stage38/fast_closeout_20261026T173610Z_1368437"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
ROOT="/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"
for d in "$D40" "$D39" "$D38" "$D27" "$D24" "$ROOT"; do
  test -d "$d" || { echo "REQUIRED_SOURCE_DIRECTORY_MISSING $d" >&2; exit 1; }
done

OUT="$BASE/ERA_original_RH_policy_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" \
  --stage40-dir "$D40" \
  --stage39-dir "$D39" \
  --stage38-dir "$D38" \
  --stage27-dir "$D27" \
  --stage24-dir "$D24" \
  --sites-root "$ROOT" \
  --out "$OUT" \
  2>&1 | tee "$BASE/stage41.log"

echo "STAGE41_REPORTS=$OUT"
cat "$OUT/STAGE41_SOURCE_POLICY_AND_UMB_FULLSET_REPORT.md"
echo "STAGE41 SCIENCE-CANDIDATE ONLY; NO ORIGINAL/DATM/SLURM CHANGES"
