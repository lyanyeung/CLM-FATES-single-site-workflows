#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage51"
mkdir -p "$BASE"
PY_COMMIT="5778c165f100fe0d11b684c3d8cc5e1685ace479"
PY_BLOB="734d94e6b3d29232aa606d16c9d09c4cf40eb05c"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage51/51_trackA_three_numeric_hypotheses_and_49_failed_offset_mechanisms_readonly.py"
PY="$BASE/stage51.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT/$REL" -o "$PY"
test "$(git hash-object "$PY")" = "$PY_BLOB"
echo "STAGE51 PATCHED SOURCE VERIFIED | invalid numeric-prefixed output keyword fixed"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test

D50="$HOME/ameriflux_batch05_stage50/full_native_boundary_sensitivity_20261027T174050Z_733866"
D49="$HOME/ameriflux_batch05_stage49/assistant_70_reference_52_jump_20261027T142654Z_3801977"
D45="$HOME/ameriflux_batch05_stage45/all_native_event_edges_20261026T193713Z_3134330"
D44="$HOME/ameriflux_batch05_stage44/whole_batch_physics_20261026T192416Z_3084937"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
for d in "$D50" "$D49" "$D45" "$D44" "$D27"; do
  test -d "$d" || { echo "STAGE51 MISSING ORIGINAL REPORT $d" >&2; exit 1; }
done
OUT="$BASE/three_hypotheses_49_offset_holds_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" --stage50-dir "$D50" --stage49-dir "$D49" \
 --stage45-dir "$D45" --stage44-dir "$D44" --stage27-dir "$D27" \
 --out "$OUT" 2>&1 | tee "$BASE/stage51.log"
echo "STAGE51_REPORTS=$OUT"
cat "$OUT/STAGE51_ASSISTANT_THREE_HYPOTHESES_FORTYNINE_HOLDS_NO_APPROVAL.md"
echo "STAGE51 SCIENCE-ONLY; ORIGINAL/APPROVED166/P1HOLD46/RH10/P2P3_1574/DATM/SLURM/CLAUDE108 UNCHANGED"
