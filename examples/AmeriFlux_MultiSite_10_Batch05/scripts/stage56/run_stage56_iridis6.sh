#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage56"
mkdir -p "$BASE"
PY_COMMIT="b9c440cc82636b7fbab9a4f7c3c8ad3ff3436a47"
PY_BLOB="ebcf495a3dfcf19bbf43f3362f53b6b8e204d56e"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage56/56_eight_user_approved_RH_interpolations_and_174_versioned_overlay.py"
SCRIPT="$BASE/stage56.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT/$REL" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$PY_BLOB"
echo "STAGE56 SOURCE VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
D52="$HOME/ameriflux_batch05_stage52/original_three_event_humidity_provenance_20261028T162951Z_2137755"
D53="$HOME/ameriflux_batch05_stage53/actual_tower_and_source_ERA_three_events_20261028T171202Z_2496835"
D55="$HOME/ameriflux_batch05_stage55/umb_user_approved_2HH_wjs_earlier_20261028T191350Z_4028511"
test -d "$D52" && test -d "$D53" && test -d "$D55"
ARGS=(--stage52-dir "$D52" --stage53-dir "$D53" --stage55-dir "$D55")
D24=""
for M in "$HOME"/ameriflux_batch05_stage24/*/stage24_manifest.json; do
  if test -f "$M" && test -f "$(dirname "$M")/stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv"; then
    D24="$(dirname "$M")"
  fi
done
if test -n "$D24"; then
  echo "STAGE56 STAGE24_CANDIDATE_TO_VERIFY=$D24"
  ARGS+=(--stage24-dir "$D24")
else
  echo "STAGE56 STAGE24_166_NOT_FOUND | only standalone 8HH overlay will be written; no 174 merge"
fi
OUT="$BASE/eight_user_approved_interpolations_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" "${ARGS[@]}" --out "$OUT" 2>&1 | tee "$BASE/stage56.log"
echo "STAGE56_REPORTS=$OUT"
echo "STAGE56 SOURCE/PRIOR_166/2018_HOLD/DATM/SLURM UNCHANGED"
