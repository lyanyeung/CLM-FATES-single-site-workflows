#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

cd "${CASE}"

# Required by DATM buildnml on this CTSM/CDEPS configuration.
touch user_nl_datm

./preview_namelists
./case.setup
./preview_namelists

echo "===== DATM annual-file count ====="
n=$(grep -c "${SITE}_forcing_" CaseDocs/datm.streams.xml)
echo "${n}"

if [[ "${n}" -ne 35 ]]; then
    echo "Expected 35 US-Ha1 annual DATM files."
    exit 1
fi

echo "===== Input-data check ====="
./check_input_data

echo "===== Build ====="
./case.build
./xmlquery BUILD_COMPLETE

echo "===== Preview run ====="
./preview_run

echo "===== Submit ====="
./case.submit
