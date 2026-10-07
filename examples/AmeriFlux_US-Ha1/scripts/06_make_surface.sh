#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

mkdir -p "${SITE_ROOT}/subset_data"

CFG="${SITE_ROOT}/US-Ha1_data.cfg"

cd "${CTSM}"

cp tools/site_and_regional/default_data_2000.cfg "${CFG}"

# Reproduce the surface-data source used in the working cases.
sed -i \
  's|dir = lnd/clm2/surfdata_esmf/ctsm5.4.0|dir = lnd/clm2/surfdata_esmf/ctsm5.3.0|g' \
  "${CFG}"

sed -i \
  's|surfdat_16pft = .*|surfdat_16pft = surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc|' \
  "${CFG}"

sed -i \
  's|mesh_surf = .*|mesh_surf = fv0.9x1.25_141008_ESMFmesh.nc|' \
  "${CFG}"

tools/site_and_regional/subset_data point \
  --lat "${SITE_LAT}" \
  --lon "${SITE_LON}" \
  --lon-type 180 \
  --site "${SITE}" \
  --surf-year 2000 \
  --create-surface \
  --create-user-mods \
  --inputdata-dir "${INPUTDATA}" \
  --cfg-file "${CFG}" \
  --outdir "${SITE_ROOT}/subset_data" \
  --overwrite

echo
find "${SITE_ROOT}/subset_data" -maxdepth 2 -type f -print | sort
