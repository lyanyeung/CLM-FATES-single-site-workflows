#!/usr/bin/env bash
# Shared US-Ha1 AmeriFlux configuration.

export SITE="US-Ha1"
export NETWORK="AmeriFlux"

export START_YEAR=1991
export END_YEAR=2025

export SITE_LAT=42.5378
export SITE_LON=-72.1715
export SITE_ELEV=340
export ZBOT=27.9
export ATM_NCPL=24

export IRIDIS_USER="${IRIDIS_USER:-ly3n24}"
export IRIDIS_HOST="${IRIDIS_HOST:-iridis6.soton.ac.uk}"
export LOCAL_WINDOWS_USER="${LOCAL_WINDOWS_USER:-ly3n24}"

export CLM_ROOT="/iridisfs/scratch/${IRIDIS_USER}/CLM_FATES"
export CTSM="${CLM_ROOT}/CTSM"
export INPUTDATA="${CLM_ROOT}/inputdata"

export SITE_ROOT="${CLM_ROOT}/sites/MY_EC_SITE/${SITE}"
export RAW_ROOT="${SITE_ROOT}/forcing/raw"
export DATM_DIR="${SITE_ROOT}/datm"

export RAW_ZIP_NAME="AMF_US-Ha1_FLUXNET_1991-2025_v1.3_r1.zip"
export LOCAL_ZIP="/mnt/c/Users/${LOCAL_WINDOWS_USER}/Downloads/${RAW_ZIP_NAME}"

export CASE="${CLM_ROOT}/cases/${SITE}_FATES_1PT"
export ARCHIVE_ROOT="/scratch/${IRIDIS_USER}/CTSM_FATES_OUTPUTS/archive/${SITE}_FATES_1PT"
