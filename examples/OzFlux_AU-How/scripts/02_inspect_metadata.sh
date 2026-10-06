#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

F="${REMOTE_RAW}"

echo "===== Source file ====="
ls -lh "${F}"

echo
echo "===== Required forcing / EC variables ====="
ncdump -h "${F}" | \
grep -E 'double (Ta|SH|ps|Fsd|Fld|Ws|Precip|GPP_LT|NEE_LT)\(' || true

echo
echo "===== Important variable metadata ====="
ncdump -h "${F}" | \
grep -E '(Ta|SH|ps|Fsd|Fld|Ws|Precip):(units|height|valid_range|coverage_L6)' || true

echo
echo "===== Site/time global metadata ====="
ncdump -h "${F}" | \
grep -E ':(fluxnet_id|site_name|latitude|longitude|altitude|tower_height|time_step|time_zone|time_coverage_start|time_coverage_end|vegetation|license_name) ='

echo
echo "Expected values used by this workflow:"
echo "  site       = AU-How"
echo "  lat        = ${SITE_LAT}"
echo "  lon        = ${SITE_LON}"
echo "  elevation  = ${SITE_ELEV} m"
echo "  ZBOT       = ${ZBOT} m"
echo "  timestep   = 30 min"
