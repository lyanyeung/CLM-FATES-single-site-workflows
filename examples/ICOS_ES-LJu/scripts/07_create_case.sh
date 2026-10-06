#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

USER_MODS="${SITE_ROOT}/subset_data/user_mods"

if [[ ! -d "${USER_MODS}" ]]; then
    echo "Missing ${USER_MODS}; run 06_make_surface.sh first."
    exit 1
fi

# Keep OpenMPI. subset_data may write MPILIB=mpi-serial.
sed -i '/MPILIB.*mpi-serial/d' "${USER_MODS}/shell_commands"

# Build the DATM stream file from scratch. Do NOT clone another site's
# explicit file list using sed.
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

for y in $(seq "${START_YEAR}" "${END_YEAR}"); do
    if [[ "${y}" -lt "${END_YEAR}" ]]; then
        echo "${SITE_ROOT}/forcing/datm/${SITE}_DATM_${y}.nc, \\"
    else
        echo "${SITE_ROOT}/forcing/datm/${SITE}_DATM_${y}.nc"
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

# Ensure daily history and disable excess-ice streams for this custom site.
sed -i \
  -e '/^[[:space:]]*hist_nhtfrq[[:space:]]*=/d' \
  -e '/^[[:space:]]*hist_mfilt[[:space:]]*=/d' \
  -e '/^[[:space:]]*use_excess_ice[[:space:]]*=/d' \
  -e '/^[[:space:]]*use_excess_ice_streams[[:space:]]*=/d' \
  "${USER_MODS}/user_nl_clm"

cat >> "${USER_MODS}/user_nl_clm" <<'EOF'

hist_nhtfrq = -24
hist_mfilt = 365
use_excess_ice = .false.
use_excess_ice_streams = .false.
EOF

nfiles=$(grep -o "${SITE}_DATM_[0-9]\{4\}\.nc" \
    "${USER_MODS}/user_nl_datm_streams" | wc -l)

if [[ "${nfiles}" -ne 21 ]]; then
    echo "Expected 21 DATM files in user_nl_datm_streams, found ${nfiles}"
    exit 1
fi

if [[ -e "${CASE}" ]]; then
    echo "Case already exists: ${CASE}"
    echo "Remove or rename it explicitly before recreating."
    exit 1
fi

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

./xmlchange ATM_NCPL=48
./xmlchange CALENDAR=NO_LEAP
./xmlchange RUN_TYPE=startup
./xmlchange RUN_STARTDATE=2004-01-01
./xmlchange CONTINUE_RUN=FALSE

./xmlchange STOP_OPTION=nyears
./xmlchange STOP_N=1
./xmlchange REST_OPTION=nyears
./xmlchange REST_N=1
./xmlchange RESUBMIT=20

./xmlchange DOUT_S=TRUE
./xmlchange DOUT_S_ROOT="${ARCHIVE_ROOT}"

# Critical on this IRIDIS setup.
./xmlchange DIN_LOC_ROOT="${INPUTDATA}"

echo
echo "===== key XML settings ====="
./xmlquery ATM_NCPL
./xmlquery CALENDAR
./xmlquery RUN_STARTDATE
./xmlquery STOP_OPTION
./xmlquery STOP_N
./xmlquery RESUBMIT
./xmlquery MPILIB
./xmlquery DIN_LOC_ROOT
./xmlquery DOUT_S_ROOT
