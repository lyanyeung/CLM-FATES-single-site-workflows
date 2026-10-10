#!/usr/bin/env bash
# Read-only GF-Guy 300-year spin-up monitoring; safe during live computation.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"
source "${HERE}/10_spinup_config.sh"

[[ -d "$SPINUP_CASE" ]] || { echo "Case missing: $SPINUP_CASE" >&2; exit 1; }
cd "$SPINUP_CASE"

echo '========== CURRENT SLURM JOBS =========='
squeue -u "$IRIDIS_USER" || true

echo
echo '========== CIME CONTINUATION =========='
./xmlquery CONTINUE_RUN,RESUBMIT,STOP_N,CCSM_CO2_PPMV

echo
echo '========== RECENT CASE STATUS =========='
tail -25 CaseStatus

echo
echo '========== COMPLETED SEGMENTS =========='
# Only successful CIME case.run entries count towards model years here.
segments=$(grep -Ec 'case\.run success[[:space:]]+[0-9]+' CaseStatus || true)
completed=$(( segments * SPINUP_YEARS_PER_JOB ))
echo "Confirmed successful segments: $segments"
echo "Estimated completed model years: $completed / $SPINUP_TOTAL_YEARS"
# Note: archiving may lag the run; this is a progress indicator, not a
# numerical convergence test or a guarantee the next resubmission succeeds.

echo
echo '========== ARCHIVED HISTORY =========='
histdir="$SPINUP_ARCHIVE/lnd/hist"
if [[ -d "$histdir" ]]; then
    find "$histdir" -maxdepth 1 -type f -name '*.clm2.h0a.*.nc' | sort | tail -8
else
    echo 'No archived history directory yet.'
fi

echo
echo '========== ARCHIVED RESTART DATES =========='
restdir="$SPINUP_ARCHIVE/rest"
if [[ -d "$restdir" ]]; then
    find "$restdir" -mindepth 1 -maxdepth 1 -type d | sort | tail -5
else
    echo 'No archived restart directory yet.'
fi

echo
echo 'For refresh: watch -n 30 "bash scripts/11_monitor_spinup300.sh"'
