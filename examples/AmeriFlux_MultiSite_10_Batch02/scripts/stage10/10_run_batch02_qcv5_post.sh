#!/usr/bin/env bash
# Stage08 candidates -> Stage09 numeric/ledger and science/source Post-v5 gates.
# Files must come from one pinned bundle; existing Stage07 files stay untouched.
set -Eeuo pipefail

MODE="${1:-build-and-audit}"
PYTHON="${PYTHON:-python3}"
BATCH="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILDER="$BATCH/scripts/stage08/08_resolve_blockers_with_raw_rh.py"
POST="$BATCH/scripts/stage09/09_post_qcv5_batch02.py"
STAGE07_ROOT="${STAGE07_ROOT:-/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/qcv5_native_trial_20261022T010124Z_dfae01c2}"
EXPERIMENT_ROOT="${EXPERIMENT_ROOT:-/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02}"
REPORT_ROOT="${REPORT_ROOT:-$EXPERIMENT_ROOT/reports}"

if [[ "$MODE" != build-and-audit && "$MODE" != audit && "$MODE" != check ]]; then
  echo 'Usage: bash 10_run_batch02_qcv5_post.sh build-and-audit | audit SELECTION_ROOT | check SELECTION_ROOT' >&2
  exit 2
fi
[[ -f "$BUILDER" && -f "$POST" ]] || { echo 'ERROR: Stage08/09 bundle files missing' >&2; exit 2; }
"$PYTHON" -c 'import sys,numpy,pandas; print("PYTHON:",sys.executable,"| numpy:",numpy.__version__,"| pandas:",pandas.__version__)'

if [[ "$MODE" == build-and-audit ]]; then
  [[ $# -le 1 ]] || { echo 'ERROR: build-and-audit takes no selection argument' >&2; exit 2; }
  RUN_ID="$("$PYTHON" -c 'from datetime import datetime,timezone; from uuid import uuid4; print(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])')"
  SELECTION_ROOT="$EXPERIMENT_ROOT/raw_RH_sensitivity_$RUN_ID"
  echo '========== STAGE08: FIVE BLOCKED SITES; PRESERVE FIVE SUCCESSFUL CANDIDATES =========='
  "$PYTHON" -B "$BUILDER" --run --stage07-root "$STAGE07_ROOT" --output-root "$SELECTION_ROOT"
  echo '========== POST-V5: INDEPENDENT NUMERIC/LEDGER THEN EXTREMES/SOURCES =========='
  "$PYTHON" -B "$POST" --audit --selection-root "$SELECTION_ROOT" --report-root "$REPORT_ROOT"
else
  [[ $# -eq 2 && -d "$2" ]] || { echo 'ERROR: supply the exact completed Stage08 selection directory' >&2; exit 2; }
  SELECTION_ROOT="$2"
  if [[ "$MODE" == check ]]; then
    "$PYTHON" -B "$POST" --check --selection-root "$SELECTION_ROOT"
  else
    "$PYTHON" -B "$POST" --audit --selection-root "$SELECTION_ROOT" --report-root "$REPORT_ROOT"
  fi
fi
echo "BATCH02 PIPELINE COMPLETED: $MODE"
echo "EXACT SELECTION ROOT: $SELECTION_ROOT"
echo 'Candidates and Post-v5 reports still require scientific review before DATM/model setup.'
