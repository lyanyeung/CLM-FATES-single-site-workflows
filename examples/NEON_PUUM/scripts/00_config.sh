#!/usr/bin/env bash
# Shared NEON PUUM configuration.

export SITE="PUUM"
export NETWORK="NEON"

export START_YEAR=2020
export END_YEAR=2025

export SITE_LAT=19.55309
export SITE_LON=-155.31731
export ATM_NCPL=48

export IRIDIS_USER="${IRIDIS_USER:-ly3n24}"
export IRIDIS_HOST="${IRIDIS_HOST:-iridis6.soton.ac.uk}"

export CLM_ROOT="/iridisfs/scratch/${IRIDIS_USER}/CLM_FATES"
export CTSM="${CLM_ROOT}/CTSM"
export INPUTDATA="${CLM_ROOT}/inputdata"

export SITE_ROOT="${CLM_ROOT}/sites/MY_EC_SITE/${SITE}"
export DATM_DIR="${SITE_ROOT}/datm"

export PUUM_ROOT="/iridisfs/scratch/${IRIDIS_USER}/NEON/PUUM"

export CASE="${CLM_ROOT}/cases/${SITE}_FATES_1PT"

export ARCHIVE_ROOT="/scratch/${IRIDIS_USER}/CTSM_FATES_OUTPUTS/archive/${SITE}_FATES_1PT"