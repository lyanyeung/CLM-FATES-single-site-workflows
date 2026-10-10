#!/usr/bin/env bash
# GF-Guy 300-year spin-up (Stage 2). Source AFTER 00_config.sh.
# Distinct from the Stage 1 first-year forcing interval (2017-2025).
export SPINUP_FORCING_FIRST=2017
export SPINUP_FORCING_LAST=2021
export SPINUP_TOTAL_YEARS=300
export SPINUP_YEARS_PER_JOB=5
export SPINUP_CASE_NAME="GF-Guy_FATES_SPINUP300_CO2405"
export SPINUP_CASE="${CLM_ROOT}/cases/${SPINUP_CASE_NAME}"
export SPINUP_RUNDIR="/scratch/${IRIDIS_USER}/CTSM_FATES_OUTPUTS/${SPINUP_CASE_NAME}/run"
export SPINUP_ARCHIVE="/scratch/${IRIDIS_USER}/CTSM_FATES_OUTPUTS/archive/${SPINUP_CASE_NAME}"
