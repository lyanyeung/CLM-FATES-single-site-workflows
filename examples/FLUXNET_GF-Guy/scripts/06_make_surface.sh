#!/usr/bin/env bash
# Reproduce the ES-LJu surface generation method for GF-Guy.
# This is a documented reconstruction; do not rerun over completed site data.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

CFG="${SITE_ROOT}/${SITE}_data.cfg"
OUTDIR="${SITE_ROOT}/subset_data"
[[ -f "${CTSM}/tools/site_and_regional/default_data_2000.cfg" ]] || {
    echo "ERROR: Cannot find CTSM default_data_2000.cfg" >&2; exit 1;
}
[[ -d "${INPUTDATA}" ]] || { echo "ERROR: INPUTDATA missing" >&2; exit 1; }

# Avoid accidental overwrite of the successfully prepared surface/user_mods.
if [[ -e "${OUTDIR}/user_mods" ]] || compgen -G "${OUTDIR}/surfdata_${SITE}*" >/dev/null; then
    if [[ "${ALLOW_SURFACE_OVERWRITE:-0}" != "1" ]]; then
        echo "ERROR: Existing GF-Guy surface/user_mods detected in: ${OUTDIR}" >&2
        echo "This is intentional protection. To regenerate in a safe new" >&2
        echo "directory, first change SITE_ROOT in 00_config.sh." >&2
        exit 1
    fi
fi
mkdir -p "${OUTDIR}"
cd "${CTSM}"
cp tools/site_and_regional/default_data_2000.cfg "${CFG}"

# Same pinned source as examples/ICOS_ES-LJu/scripts/06_make_surface.sh.
sed -i \
  's|dir = lnd/clm2/surfdata_esmf/ctsm5.4.0|dir = lnd/clm2/surfdata_esmf/ctsm5.3.0|g' \
  "${CFG}"
sed -i \
  's|surfdat_16pft = .*|surfdat_16pft = surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc|' \
  "${CFG}"
sed -i \
  's|mesh_surf = .*|mesh_surf = fv0.9x1.25_141008_ESMFmesh.nc|' \
  "${CFG}"

echo "===== pinned surface configuration ====="
grep -A8 '^\[surfdat\]' "${CFG}"

# Consistent with ES-LJu: point extraction + surface + user_mods.
# --overwrite is allowed ONLY when explicitly requested above.
ARGS=(
  point --lat "${SITE_LAT}" --lon "${SITE_LON}" --lon-type 180
  --site "${SITE}" --surf-year "${SURFACE_YEAR}"
  --create-surface --create-user-mods
  --inputdata-dir "${INPUTDATA}" --cfg-file "${CFG}"
  --outdir "${OUTDIR}"
)
if [[ "${ALLOW_SURFACE_OVERWRITE:-0}" == "1" ]]; then
    ARGS+=(--overwrite)
fi

tools/site_and_regional/subset_data "${ARGS[@]}"

echo "===== generated files ====="
find "${OUTDIR}" -maxdepth 2 -type f -print | sort
