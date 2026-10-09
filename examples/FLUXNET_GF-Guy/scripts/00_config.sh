#!/usr/bin/env bash
# GF-Guy (Guyaflux): configuration for the first-year reproducibility example.
# Source from the scripts in this directory. All derived files stay on IRIDIS.

export SITE="GF-Guy"
export START_YEAR=2017
export END_YEAR=2025     # Existing one-year case used 2017 and 2025 DATM streams;
                         # verify full availability before attempting a rebuild.
export SITE_LAT=5.2788
export SITE_LON=-52.9249
export SURFACE_YEAR=2000   # CTSM surface reference year, NOT CO2 reference year.
export CO2_PPM=405.0      # Fixed, approximately 2017 atmospheric CO2; chosen case value.
export ATM_NCPL=48        # 30-minute coupling steps.

export IRIDIS_USER="${IRIDIS_USER:-ly3n24}"
export CLM_ROOT="/iridisfs/scratch/${IRIDIS_USER}/CLM_FATES"
export CTSM="${CLM_ROOT}/CTSM"
export INPUTDATA="${CLM_ROOT}/inputdata"
export SITE_ROOT="${CLM_ROOT}/sites/MY_EC_SITE/${SITE}"
export DATM_DIR="${SITE_ROOT}/forcing/datm"

# The first-year case that succeeded on IRIDIS (job 4073259).
# Never overwrite or recreate this directory without explicitly archiving it.
export CASE_NAME="GF-Guy_FATES_SURF2000_CO2405_1PT"
export CASE="${CLM_ROOT}/cases/${CASE_NAME}"
export ARCHIVE_ROOT="/scratch/${IRIDIS_USER}/CTSM_FATES_OUTPUTS/archive/${CASE_NAME}"
