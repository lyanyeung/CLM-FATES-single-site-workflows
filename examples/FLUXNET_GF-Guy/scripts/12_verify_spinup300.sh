#!/usr/bin/env bash
# Read-only audit of the active or completed 300-year GF-Guy spin-up.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"
source "${HERE}/10_spinup_config.sh"

fail=0
check() {
    local label="$1"; shift
    if "$@"; then
        printf 'PASS: %s\n' "$label"
    else
        printf 'FAIL: %s\n' "$label" >&2
        fail=1
    fi
}

[[ -d "$SPINUP_CASE" && -x "$SPINUP_CASE/xmlquery" ]] || {
    echo "ERROR: Missing case $SPINUP_CASE" >&2; exit 1;
}
cd "$SPINUP_CASE"

xml_value() { ./xmlquery "$1" --value | tr -d '[:space:]'; }
equals() { [[ "$1" == "$2" ]]; }
file_exists() { [[ -f "$1" ]]; }

check 'Correct CIME case name' equals "$(xml_value CASE)" "$SPINUP_CASE_NAME"
check '2017 start date' equals "$(xml_value RUN_STARTDATE)" '2017-01-01'
check 'Five model years per submission' equals "$(xml_value STOP_N)" '5'
check 'Five-year restart intervals' equals "$(xml_value REST_N)" '5'
check 'Fixed atmospheric CO2 mode' equals "$(xml_value CLM_CO2_TYPE)" 'constant'
check 'Atmospheric CO2 = 405 ppm' equals "$(xml_value CCSM_CO2_PPMV)" '405.0'
check 'Correct independent run directory' equals "$(xml_value RUNDIR)" "$SPINUP_RUNDIR"
check 'Correct independent archive directory' equals "$(xml_value DOUT_S_ROOT)" "$SPINUP_ARCHIVE"
check 'CIME run script exists' file_exists '.case.run'
check 'CIME archive script exists (no leading dot)' file_exists 'case.st_archive'

source_exe="$(cd "$CASE" && ./xmlquery EXEROOT --value | tr -d '[:space:]')"
spinup_exe="$(xml_value EXEROOT)"
check 'Cloned executable location matches source' equals "$spinup_exe" "$source_exe"
check 'Compiled cesm.exe exists' test -x "$spinup_exe/cesm.exe"

stream='user_nl_datm_streams'
if [[ -f "$stream" ]]; then
    check 'DATM taxmode=cycle' grep -Eq '^CLM_USRDAT\.UNSET:taxmode[[:space:]]*=[[:space:]]*cycle' "$stream"
    check 'DATM year_first=2017' grep -Eq '^CLM_USRDAT\.UNSET:year_first[[:space:]]*=[[:space:]]*2017' "$stream"
    check 'DATM year_last=2021' grep -Eq '^CLM_USRDAT\.UNSET:year_last[[:space:]]*=[[:space:]]*2021' "$stream"
    check 'DATM year_align=2017' grep -Eq '^CLM_USRDAT\.UNSET:year_align[[:space:]]*=[[:space:]]*2017' "$stream"
    count="$(grep -Ec 'GF-Guy_DATM_[0-9]{4}\.nc' "$stream" || true)"
    check 'Exactly five annual DATM files' equals "$count" '5'
    for y in 2017 2018 2019 2020 2021; do
        check "DATM file year $y referenced" grep -q "GF-Guy_DATM_${y}.nc" "$stream"
    done
else
    echo 'FAIL: Missing user_nl_datm_streams' >&2
    fail=1
fi

if [[ -f CaseDocs/lnd_in ]]; then
    for setting in use_excess_ice use_excess_ice_streams; do
        check "$setting disabled" grep -Eq "^[[:space:]]*${setting}[[:space:]]*=[[:space:]]*\\.false\\." CaseDocs/lnd_in
    done
else
    echo 'FAIL: Missing CaseDocs/lnd_in' >&2
    fail=1
fi

printf '\n========== CURRENT RUN PROGRESS ==========\n'
./xmlquery CONTINUE_RUN,RESUBMIT,STOP_N
printf '\n========== LATEST STATUS ==========\n'
tail -12 CaseStatus

if (( fail )); then
    echo 'AUDIT RESULT: FAIL (read-only; no files changed)' >&2
    exit 1
fi
echo 'AUDIT RESULT: PASS (configuration checks only; not a 300-year convergence claim)'
