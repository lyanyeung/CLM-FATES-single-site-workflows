#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage62"
mkdir -p "$BASE"
COMMIT="fef79c2e8e2386550871ca9700686875f13dbe3e"
BLOB="cd6bf50688faaa6300b0386ebccded2a95b3a902"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage62/62_merge_explicitly_approved_Wjs2018_30HH_into_versioned_204.py"
SCRIPT="$BASE/stage62.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$BLOB"
echo "STAGE62 SOURCE VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
D53="$HOME/ameriflux_batch05_stage53/actual_tower_and_source_ERA_three_events_20261028T171202Z_2496835"
D56="$HOME/ameriflux_batch05_stage56/eight_user_approved_interpolations_20261028T193428Z_4078597"
D59="$HOME/ameriflux_batch05_stage59/wjs2018_original_49HH_weather_source_20261028T233732Z_861557"
D60="$HOME/ameriflux_batch05_stage60/wjs2018_exact_original_MDS_QC_20261028T234456Z_908965"
D61="$HOME/ameriflux_batch05_stage61/wjs2018_30HH_protected_linear_RH_shadow_20261028T235434Z_968717"
for D in "$D53" "$D56" "$D59" "$D60" "$D61"; do test -d "$D"; done
OUT="$BASE/wjs2018_30HH_approved_versioned_204_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" \
 --stage53-dir "$D53" --stage56-dir "$D56" \
 --stage59-dir "$D59" --stage60-dir "$D60" --stage61-dir "$D61" \
 --out "$OUT" 2>&1 | tee "$BASE/stage62.log"
echo "STAGE62_REPORTS=$OUT"
echo "STAGE62 NO SOURCE/PRIOR_174/DATM/CIME/SLURM MODIFICATIONS"
