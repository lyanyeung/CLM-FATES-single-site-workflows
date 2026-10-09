#!/usr/bin/env bash
# Optional: FIRST-YEAR case build/submit, only when creating a new case.
# Do NOT run when successful GF-Guy case or 300-year spin-up is underway.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

[[ -d "${CASE}" ]] || { echo "ERROR: Case does not exist" >&2; exit 1; }
cd "${CASE}"

# Guard against duplicate submission or overwriting the successful run.
if grep -Eiq 'case.submit success|model execution starting' CaseStatus 2>/dev/null; then
    echo "ERROR: This case was already submitted. Refusing duplicate." >&2
    exit 1
fi

# case.setup generates CIME .case.run and case.st_archive batch scripts.
./case.setup
./preview_namelists

echo '===== resolved surface ====='
grep -Ei 'fsurdat|surfdata_GF-Guy' CaseDocs/lnd_in || true

echo '===== GF-Guy CO2 ====='
./xmlquery CLM_CO2_TYPE,CCSM_CO2_PPMV

echo '===== forcing ====='
grep -R 'GF-Guy_DATM_' CaseDocs | head -20 || true

./check_input_data
./case.build
./xmlquery BUILD_COMPLETE
./preview_run

# Truly submits a 1-year experiment; does NOT submit the 300-year spin-up.
./case.submit
