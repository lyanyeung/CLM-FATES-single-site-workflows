#!/usr/bin/env bash
# Recreate the GF-Guy first-year FATES case from generated user_mods.
# This file intentionally refuses to replace the existing successful case.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"
USER_MODS="${SITE_ROOT}/subset_data/user_mods"

[[ -d "${USER_MODS}" ]] || { echo "ERROR: Run 06_make_surface.sh first" >&2; exit 1; }
[[ -f "${USER_MODS}/user_nl_clm" ]] || { echo "ERROR: Missing user_nl_clm" >&2; exit 1; }
[[ ! -e "${CASE}" ]] || {
    echo "ERROR: Case already exists: ${CASE}" >&2
    echo "Existing successful case will not be overwritten." >&2
    exit 1
}

# Enforce original working forcing filename convention and validate inputs.
for year in $(seq "${START_YEAR}" "${END_YEAR}"); do
    f="${DATM_DIR}/${SITE}_DATM_${year}.nc"
    [[ -f "$f" ]] || { echo "ERROR: DATM forcing file missing: $f" >&2; exit 1; }
done

# subset_data can generate mpi-serial; this successful setup uses OpenMPI.
if [[ -f "${USER_MODS}/shell_commands" ]]; then
    sed -i '/MPILIB.*mpi-serial/d' "${USER_MODS}/shell_commands"
fi

# Build the DATM stream explicitly (never transform another site's file list).
{
cat <<EOF
CLM_USRDAT.UNSET:taxmode = cycle
CLM_USRDAT.UNSET:tintalgo = linear
CLM_USRDAT.UNSET:mapalgo = none
CLM_USRDAT.UNSET:meshfile = none

CLM_USRDAT.UNSET:year_first = ${START_YEAR}
CLM_USRDAT.UNSET:year_last = ${END_YEAR}
CLM_USRDAT.UNSET:year_align = ${START_YEAR}

CLM_USRDAT.UNSET:datafiles = \\
EOF
for year in $(seq "${START_YEAR}" "${END_YEAR}"); do
    if (( year < END_YEAR )); then
        printf '%s, \\\n' "${DATM_DIR}/${SITE}_DATM_${year}.nc"
    else
        printf '%s\n' "${DATM_DIR}/${SITE}_DATM_${year}.nc"
    fi
done
cat <<'EOF'

CLM_USRDAT.UNSET:datavars = \
PRECTmms Faxa_precn, \
FSDS Faxa_swdn, \
ZBOT Sa_z, \
TBOT Sa_tbot, \
WIND Sa_wind, \
QBOT Sa_shum, \
PSRF Sa_pbot, \
FLDS Faxa_lwdn
EOF
} > "${USER_MODS}/user_nl_datm_streams"

# Proven working workaround for GF-Guy initialisation (successful 1-year case).
sed -i \
  -e '/^[[:space:]]*hist_nhtfrq[[:space:]]*=/d' \
  -e '/^[[:space:]]*hist_mfilt[[:space:]]*=/d' \
  -e '/^[[:space:]]*use_excess_ice[[:space:]]*=/d' \
  -e '/^[[:space:]]*use_excess_ice_streams[[:space:]]*=/d' \
  "${USER_MODS}/user_nl_clm"
cat >> "${USER_MODS}/user_nl_clm" <<'EOF'

! Daily history; disable excess-ice streams for this one-point setup
hist_nhtfrq = -24
hist_mfilt = 365
use_excess_ice = .false.
use_excess_ice_streams = .false.
EOF

# Confirm generated list uses exactly the configured number of years.
EXPECTED=$(( END_YEAR - START_YEAR + 1 ))
ACTUAL=$(grep -Ec "${SITE}_DATM_[0-9]{4}\\.nc" "${USER_MODS}/user_nl_datm_streams")
[[ "$ACTUAL" -eq "$EXPECTED" ]] || { echo "ERROR: Incorrect DATM list count" >&2; exit 1; }

cd "${CTSM}/cime/scripts"
./create_newcase \
  --case "${CASE}" \
  --compset I1PtClm60FatesRsGs \
  --res CLM_USRDAT \
  --machine iridis6 \
  --compiler intel \
  --mpilib openmpi \
  --user-mods-dir "${USER_MODS}" \
  --run-unsupported
cd "${CASE}"

# Same model/calendar settings as ES-LJu, but only 1 year of simulation.
touch user_nl_datm
./xmlchange DIN_LOC_ROOT="${INPUTDATA}"
./xmlchange ATM_NCPL=48
./xmlchange CALENDAR=NO_LEAP
./xmlchange RUN_TYPE=startup
./xmlchange RUN_STARTDATE="${START_YEAR}-01-01"
./xmlchange CONTINUE_RUN=FALSE
./xmlchange STOP_OPTION=nyears
./xmlchange STOP_N=1
./xmlchange REST_OPTION=nyears
./xmlchange REST_N=1
./xmlchange RESUBMIT=0
./xmlchange DOUT_S=TRUE
./xmlchange DOUT_S_ROOT="${ARCHIVE_ROOT}"

# DIFFERENCE FROM ES-LJu: site-start-year CO2 value is fixed explicitly.
# 405 ppm is the intended GF-Guy value, not a globally universal default.
./xmlchange CLM_CO2_TYPE=constant
./xmlchange CCSM_CO2_PPMV="${CO2_PPM}"

printf '\n===== GF-Guy one-year case configuration =====\n'
./xmlquery RUN_STARTDATE,STOP_N,RESUBMIT,CLM_CO2_TYPE,CCSM_CO2_PPMV,MPILIB,DIN_LOC_ROOT
