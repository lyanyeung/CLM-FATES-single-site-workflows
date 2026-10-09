#!/usr/bin/env bash
# DE-Hai ICOS / FLUXNET single-site configuration (release 2026).

export SITE="DE-Hai"
export NETWORK="ICOS"
export START_YEAR=2000
export END_YEAR=2025
export SITE_LAT=51.079212
export SITE_LON=10.452168
export SITE_ELEV=438.7
export ATM_NCPL=48

export IRIDIS_USER="${IRIDIS_USER:-ly3n24}"
export CLM_ROOT="${CLM_ROOT:-/iridisfs/scratch/${IRIDIS_USER}/CLM_FATES}"
export CTSM="${CLM_ROOT}/CTSM"
export INPUTDATA="${CLM_ROOT}/inputdata"
export SITE_ROOT="${CLM_ROOT}/sites/MY_EC_SITE/${SITE}"
export RAW_ROOT="${SITE_ROOT}/forcing/raw"
export RAW_PACKAGE_NAME="ICOS_DE-Hai_FLUXNET_2000-2025_v1.3_r1"
export RAW_ZIP="${RAW_ROOT}/${RAW_PACKAGE_NAME}.zip"
export RAW_EXTRACTED="${RAW_ROOT}/${RAW_PACKAGE_NAME}"
export ICOS_PID="VsQ1NTQTcEO5zRyfZjrBtkQa"
export ICOS_SHA256="56c4353534137043b9cd1c9f663ac1b6441a3b533fbab163c1f3ab4a272abb50"
export CASE="${CLM_ROOT}/cases/${SITE}_FATES_1PT"
export ARCHIVE_ROOT="/scratch/${IRIDIS_USER}/CTSM_FATES_OUTPUTS/archive/${SITE}_FATES_1PT"
