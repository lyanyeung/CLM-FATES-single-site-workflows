#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

cd "${CASE}"

./case.setup
./preview_namelists

echo "===== DATM stream check ====="
grep -R "${SITE}_DATM_" CaseDocs | head -40 || true

echo "===== Surface check ====="
grep -R "surfdata_${SITE}" CaseDocs || true

echo "===== Input-data check ====="
./check_input_data

echo "===== Build ====="
./case.build
./xmlquery BUILD_COMPLETE

echo "===== Preview run ====="
./preview_run

echo "===== Submit ====="
./case.submit
