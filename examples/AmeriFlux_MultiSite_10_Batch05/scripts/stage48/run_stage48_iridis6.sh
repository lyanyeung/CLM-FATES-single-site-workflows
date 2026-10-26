#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage48"
mkdir -p "$BASE"
PY_COMMIT="921d7f7c54d6f7847e6f7165c9d74afb0c9c9844"
PY_BLOB="ebb31061a00efe5de4b33e374f535f65ff2b4fdd"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage48/48_trackA_full_event_122_unapproved_ERA_pilots_and_253_source_holds.py"
PY="$BASE/stage48.py"

curl -fLsS --retry 3 \
  "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT/$REL" \
  -o "$PY"
test "$(git hash-object "$PY")" = "$PY_BLOB"
echo "STAGE48 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test

D47="$HOME/ameriflux_batch05_stage47/assistant_trackA_20261026T195942Z_3223947"
D45="$HOME/ameriflux_batch05_stage45/all_native_event_edges_20261026T193713Z_3134330"
D44="$HOME/ameriflux_batch05_stage44/whole_batch_physics_20261026T192416Z_3084937"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
D43="$HOME/ameriflux_batch05_stage43/numeric_15_source_trial_20261026T191656Z_2924371"

for d in "$D47" "$D45" "$D44" "$D27" "$D24" "$D43"; do
  test -d "$d" || { echo "SOURCE_REPORT_MISSING $d" >&2; exit 1; }
done

OUT="$BASE/assistant_122_full_event_trial_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" \
  --stage47-dir "$D47" \
  --stage45-dir "$D45" \
  --stage44-dir "$D44" \
  --stage27-dir "$D27" \
  --stage24-dir "$D24" \
  --stage43-dir "$D43" \
  --out "$OUT" 2>&1 | tee "$BASE/stage48.log"

echo "STAGE48_REPORTS=$OUT"
cat "$OUT/STAGE48_ASSISTANT_122_TRIAL_EVENTS_253_SOURCE_HOLDS.md"
echo "STAGE48 RESEARCH-ONLY. Stage24 APPROVED166 / P1HOLD46 / 10 RH PLATFORM / 1574 P2P3 / DATM UNCHANGED"
