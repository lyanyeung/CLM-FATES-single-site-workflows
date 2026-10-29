#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage102_evidence"
mkdir -p "$BASE"
RUN="$(mktemp -d "$BASE/run_$(date -u +%Y%m%dT%H%M%SZ)_XXXXXXXX")"
ROOT="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
B05="examples/AmeriFlux_MultiSite_10_Batch05/scripts"
curl -fLsS --retry 3 "$ROOT/ff9bfd30597d3f50d46a58af0f23728426290875/$B05/AD400_direct_preflight/run_stage101_batch05_DATM_source_selection_NO_SUBMIT_iridis6.sh" -o "$RUN/stage101.sh"
test "$(git hash-object "$RUN/stage101.sh")" = d9d74ba57c13376aeb0e1d5d310c6196e2cdff0f
curl -fLsS --retry 3 "$ROOT/2c4ef552d123082fb3ad6c76f419a859880981f7/$B05/stage102/batch05_risk_evidence.py" -o "$RUN/stage102.py"
test "$(git hash-object "$RUN/stage102.py")" = 2cd9bc9647768f49778f62e6b365842d9d0e4567
echo "STAGE102: both downloaded scripts verified; running Stage101 then source evidence"
python3 -B -m py_compile "$RUN/stage102.py"
bash "$RUN/stage101.sh" 2>&1 | tee "$RUN/stage101.log"
S101="$(sed -n 's/^STAGE101_REPORTS=//p' "$RUN/stage101.log" | tail -n 1)"
test -n "$S101" && test -d "$S101"
D84="$HOME/ameriflux_batch05_stage84_Vcp/Vcp_direct582_20261029T062857Z_2211876"
D97="$HOME/ameriflux_batch05_stage97/original_56_holds_five_science_groups_20261029T075507Z_3517881"
python3 -B "$RUN/stage102.py" --stage101 "$S101" --stage84 "$D84" --stage97 "$D97" --out "$RUN/results" 2>&1 | tee "$RUN/stage102.log"
echo "COPY BACK: all STAGE102 output above, or the whole $RUN/stage102.log"
echo "STAGE102 RUN DIRECTORY=$RUN"
