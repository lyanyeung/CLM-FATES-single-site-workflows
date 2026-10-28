#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage54"
mkdir -p "$BASE"
PY_COMMIT="e2c3e0999b77d52097eda3d8af907b25d48c204c"
PY_BLOB="81e8c9647af550aba7e00c0e911999cd073359b3"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage54/54_three_event_true_qc0_brackets_readonly.py"
SCRIPT="$BASE/stage54.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT/$REL" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$PY_BLOB"
echo "STAGE54 SOURCE VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
D53="$HOME/ameriflux_batch05_stage53/actual_tower_and_source_ERA_three_events_20261028T171202Z_2496835"
D52="$HOME/ameriflux_batch05_stage52/original_three_event_humidity_provenance_20261028T162951Z_2137755"
test -d "$D53" && test -d "$D52"
python3 -B "$SCRIPT" --stage53-dir "$D53" --stage52-dir "$D52" 2>&1 | tee "$BASE/stage54.log"
echo "STAGE54_LOG=$BASE/stage54.log"
echo "STAGE54 READONLY | NO APPROVAL NO FORCING CHANGES NO SLURM"
