#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage59"
mkdir -p "$BASE"
COMMIT="0ed28039bc79f9a7dfd02dc75e946d98908af14c"
BLOB="786ca0cde9ab6245634e7c49a39ac7f21f001902"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage59/59_Wjs2018_original_humidity_and_weather_field_provenance_READONLY.py"
PY="$BASE/stage59.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$PY"
test "$(git hash-object "$PY")" = "$BLOB"
echo "STAGE59 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test
D53="$HOME/ameriflux_batch05_stage53/actual_tower_and_source_ERA_three_events_20261028T171202Z_2496835"
D56="$HOME/ameriflux_batch05_stage56/eight_user_approved_interpolations_20261028T193428Z_4078597"
D57="$HOME/ameriflux_batch05_stage57/wjs2018_actual_ERA5Land_20261028T195055Z_4119241"
D58="$HOME/ameriflux_batch05_stage58/wjs2018_compare_four_methods_20261028T224753Z_551429"
for D in "$D53" "$D56" "$D57" "$D58"; do test -d "$D"; done
OUT="$BASE/wjs2018_original_49HH_weather_source_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" --stage53-dir "$D53" --stage56-dir "$D56" --stage57-dir "$D57" --stage58-dir "$D58" --out "$OUT" 2>&1 | tee "$BASE/stage59.log"
echo "STAGE59_REPORTS=$OUT"
echo "STAGE59 NO SCIENCE APPROVAL OR ORIGINAL/174/HOLD/DATM/SLURM MODIFICATION"
