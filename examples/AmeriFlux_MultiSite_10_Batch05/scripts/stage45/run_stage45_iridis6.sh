#!/usr/bin/env bash
set -euo pipefail

BASE="$HOME/ameriflux_batch05_stage45"
mkdir -p "$BASE"
PY_COMMIT="8b1a5c9aa886517153b05e955ba97c092fa680ed"
PY_BLOB="ace88da48f088c709487cac1d949ad80d54f454f"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage45/45_actual_483_event_full_native_era_boundaries_and_connected_runs.py"
PY="$BASE/stage45.py"

curl -fLsS --retry 3 \
 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT/$REL" \
 -o "$PY"
test "$(git hash-object "$PY")" = "$PY_BLOB"
echo "STAGE45 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test

D44="$HOME/ameriflux_batch05_stage44/whole_batch_physics_20261026T192416Z_3084937"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
ROOT="/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"
for x in "$D44" "$D27" "$D24" "$ROOT"; do
  test -d "$x" || { echo "MISSING_REQUIRED_SOURCE_DIRECTORY $x" >&2; exit 1; }
done

OUT="$BASE/all_native_event_edges_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" \
 --stage44-dir "$D44" \
 --stage27-dir "$D27" \
 --stage24-dir "$D24" \
 --sites-root "$ROOT" \
 --out "$OUT" 2>&1 | tee "$BASE/stage45.log"

echo "STAGE45_REPORTS=$OUT"
cat "$OUT/STAGE45_ALL483_EVENT_NATIVE_ERA_BOUNDARY_REPORT.md"
echo "STAGE45 NO SOURCE/DATM/CIME/SLURM WRITES"
