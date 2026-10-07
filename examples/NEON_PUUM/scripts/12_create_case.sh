#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"

USER_MODS="${SITE_ROOT}/subset_data/user_mods"

if [[ ! -d "${USER_MODS}" ]]; then
    echo "Missing ${USER_MODS}; run 06_make_surface.sh first."
    exit 1
fi

# subset_data may force mpi-serial; keep OpenMPI.
sed -i '/MPILIB.*mpi-serial/d' \
    "${USER_MODS}/shell_commands"

# Build the exact 1991-2025 DATM stream.
{
cat <<EOF
CLM_USRDAT.UNSET:taxmode=cycle
CLM_USRDAT.UNSET:tintalgo=linear
CLM_USRDAT.UNSET:readmode=single
CLM_USRDAT.UNSET:mapalgo=none
CLM_USRDAT.UNSET:dtlimit=1.5
CLM_USRDAT.UNSET:year_first=${START_YEAR}
CLM_USRDAT.UNSET:year_last=${END_YEAR}
CLM_USRDAT.UNSET:year_align=${START_YEAR}
CLM_USRDAT.UNSET:meshfile=none
CLM_USRDAT.UNSET:datafiles=\
EOF

for y in $(seq "${START_YEAR}" "${END_YEAR}"); do
    if [[ "${y}" -lt "${END_YEAR}" ]]; then
        echo "${DATM_DIR}/${SITE}_forcing_${y}.nc, \\"
    else
        echo "${DATM_DIR}/${SITE}_forcing_${y}.nc"
    fi
done

cat <<'EOF'
CLM_USRDAT.UNSET:datavars=PRECTmms Faxa_precn,FSDS Faxa_swdn,ZBOT Sa_z,TBOT Sa_tbot,WIND Sa_wind,QBOT Sa_shum,PSRF Sa_pbot,FLDS Faxa_lwdn
EOF

} > "${USER_MODS}/user_nl_datm_streams"

# Daily history and custom-site excess-ice settings.
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

EXPECTED_FILES=$((END_YEAR - START_YEAR + 1))

nfiles=$(grep -o "${SITE}_forcing_[0-9]\{4\}\.nc" \
    "${USER_MODS}/user_nl_datm_streams" | wc -l)

if [[ "${nfiles}" -ne "${EXPECTED_FILES}" ]]; then
    echo "Expected ${EXPECTED_FILES} DATM files, found ${nfiles}"
    exit 1
fi

if [[ -e "${CASE}" ]]; then
    echo "Case already exists: ${CASE}"
    echo "Remove or rename it explicitly before recreating."
    exit 1
fi

cd "${CTSM}"

./cime/scripts/create_newcase \
  --case "${CASE}" \
  --compset I1PtClm60FatesRsGs \
  --res CLM_USRDAT \
  --machine iridis6 \
  --compiler intel \
  --mpilib openmpi \
  --user-mods-dir "${USER_MODS}" \
  --run-unsupported

cd "${CASE}"

# Required by this CDEPS/DATM configuration even when empty.
touch user_nl_datm

./xmlchange DIN_LOC_ROOT="${INPUTDATA}"

./xmlchange DOUT_S=TRUE
./xmlchange DOUT_S_ROOT="${ARCHIVE_ROOT}"

./xmlchange ATM_NCPL="${ATM_NCPL}"
./xmlchange CALENDAR=NO_LEAP

./xmlchange RUN_TYPE=startup
./xmlchange RUN_STARTDATE=${START_YEAR}-01-01
./xmlchange CONTINUE_RUN=FALSE

./xmlchange STOP_OPTION=nyears
./xmlchange STOP_N=1

./xmlchange REST_OPTION=nyears
./xmlchange REST_N=1

./xmlchange RESUBMIT=$((END_YEAR - START_YEAR))

echo
echo "===== key XML settings ====="
./xmlquery \
DIN_LOC_ROOT,DOUT_S,DOUT_S_ROOT,ATM_NCPL,CALENDAR,RUN_TYPE,RUN_STARTDATE,CONTINUE_RUN,STOP_OPTION,STOP_N,REST_OPTION,REST_N,RESUBMIT,MPILIB
