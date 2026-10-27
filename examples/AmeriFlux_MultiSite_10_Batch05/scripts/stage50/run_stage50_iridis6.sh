#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage50"
mkdir -p "$BASE"
PY_COMMIT="0104fbb6ce68a15d7c45da6ccc45c620044dca1a"
PY_BLOB="3a354cdcc4c577a69110303aaaaa8ddce4139527"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage50/50_trackA_eventwide_RH_offset_hypotheses_and_70_reference_queue.py"
PY="$BASE/stage50.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT/$REL" -o "$PY"
test "$(git hash-object "$PY")" = "$PY_BLOB"
echo "STAGE50 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test
D49="$HOME/ameriflux_batch05_stage49/assistant_70_reference_52_jump_20261027T142654Z_3801977"
D48="$HOME/ameriflux_batch05_stage48/assistant_122_full_event_trial_20261027T141646Z_3720216"
D45="$HOME/ameriflux_batch05_stage45/all_native_event_edges_20261026T193713Z_3134330"
D44="$HOME/ameriflux_batch05_stage44/whole_batch_physics_20261026T192416Z_3084937"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
for d in "$D49" "$D48" "$D45" "$D44" "$D27"; do
  test -d "$d" || { echo "STAGE50 MISSING ORIGINAL SOURCE REPORT $d" >&2; exit 1; }
done
OUT="$BASE/full_native_boundary_sensitivity_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" --stage49-dir "$D49" --stage48-dir "$D48" \
  --stage45-dir "$D45" --stage44-dir "$D44" --stage27-dir "$D27" \
  --out "$OUT" 2>&1 | tee "$BASE/stage50.log"
echo "STAGE50_REPORTS=$OUT"
cat "$OUT/STAGE50_ASSISTANT_REFERENCE_SCIENCE_AND_EVENTWIDE_OFFSET_LIMITS.md"
echo "STAGE50 REPORT ONLY. NO SOURCE/DATM/Slurm WRITES; CLAUDE108 UNTOUCHED"
