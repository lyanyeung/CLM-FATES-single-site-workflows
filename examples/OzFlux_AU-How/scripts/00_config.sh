#!/usr/bin/env bash
# Shared AU-How configuration.
# Source this file from the other shell scripts.

export SITE="AU-How"
export START_YEAR=2003
export END_YEAR=2025

# Coordinates used in the successful CLM-FATES AU-How run.
export SITE_LAT=-12.4952
export SITE_LON=131.15005
export SITE_ELEV=64
export ZBOT=23

export IRIDIS_USER="${IRIDIS_USER:-ly3n24}"
export IRIDIS_HOST="${IRIDIS_HOST:-iridis6.soton.ac.uk}"

export CLM_ROOT="/iridisfs/scratch/${IRIDIS_USER}/CLM_FATES"
export CTSM="${CLM_ROOT}/CTSM"
export INPUTDATA="${CLM_ROOT}/inputdata"
export SITE_ROOT="${CLM_ROOT}/sites/MY_EC_SITE/${SITE}"
export CASE="${CLM_ROOT}/cases/${SITE}_FATES_1PT"
export ARCHIVE_ROOT="/scratch/${IRIDIS_USER}/CTSM_FATES_OUTPUTS/archive/${SITE}_FATES_1PT"

# Local WSL source file used in the successful workflow.
export LOCAL_RAW="/mnt/d/Site_Level_Experiment/AU-How/HowardSprings_L6.nc"
export REMOTE_RAW="${SITE_ROOT}/forcing/raw/HowardSprings_L6.nc"
