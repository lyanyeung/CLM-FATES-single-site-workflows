#!/usr/bin/env bash
# Shared ES-LJu configuration.
# Source this file from the other shell scripts.

export SITE="ES-LJu"
export START_YEAR=2004
export END_YEAR=2024

export SITE_LAT=36.926594
export SITE_LON=-2.752115
export SITE_ELEV=1600
export ZBOT=2.5

export IRIDIS_USER="${IRIDIS_USER:-ly3n24}"
export IRIDIS_HOST="${IRIDIS_HOST:-iridis6.soton.ac.uk}"

export CLM_ROOT="/iridisfs/scratch/${IRIDIS_USER}/CLM_FATES"
export CTSM="${CLM_ROOT}/CTSM"
export INPUTDATA="${CLM_ROOT}/inputdata"
export SITE_ROOT="${CLM_ROOT}/sites/MY_EC_SITE/${SITE}"
export RAW_PACKAGE_NAME="EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1"
export RAW_ROOT="${SITE_ROOT}/forcing/raw/${RAW_PACKAGE_NAME}"
export CASE="${CLM_ROOT}/cases/${SITE}_FATES_1PT"

export ARCHIVE_ROOT="/scratch/${IRIDIS_USER}/CTSM_FATES_OUTPUTS/archive/${SITE}_FATES_1PT"

# Local WSL source folder used in the successful workflow.
export LOCAL_RAW="/mnt/d/Site_Level_Experiment/ES-Lju/EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1/EUF_ES-LJu_FLUXNET_2004-2024_v1.3_r1"
