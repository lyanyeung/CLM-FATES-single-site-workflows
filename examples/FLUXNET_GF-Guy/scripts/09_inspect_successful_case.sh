#!/usr/bin/env bash
# Read-only provenance check of the existing successful GF-Guy one-year case.
# Safe even if an independent 300-year spin-up is running.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

[[ -d "${CASE}" ]] || { echo "ERROR: Successful case not found: ${CASE}" >&2; exit 1; }
cd "${CASE}"

echo '======== EXISTING CASE ========' 
printf '%s\n' "${CASE}"
./xmlquery CASE,RUN_STARTDATE,STOP_OPTION,STOP_N,RESUBMIT,ATM_NCPL,CALENDAR

echo '======== CO2 SETTINGS ========' 
./xmlquery CLM_CO2_TYPE,CCSM_CO2_PPMV

echo '======== BUILD AND OUTPUT ========' 
./xmlquery BUILD_COMPLETE,EXEROOT,RUNDIR,DOUT_S_ROOT

echo '======== SITE SURFACE (resolved) ========' 
if [[ -f CaseDocs/lnd_in ]]; then
    grep -Ei 'fsurdat|use_excess_ice|hist_nhtfrq|hist_mfilt' CaseDocs/lnd_in || true
else
    echo 'CaseDocs/lnd_in absent'
fi

echo '======== DATM STREAM ========' 
if [[ -f user_nl_datm_streams ]]; then
    grep -E 'taxmode|year_first|year_last|year_align|GF-Guy_DATM_' user_nl_datm_streams || true
else
    echo 'user_nl_datm_streams absent'
fi

echo '======== CASE STATUS ========' 
tail -n 20 CaseStatus || true
