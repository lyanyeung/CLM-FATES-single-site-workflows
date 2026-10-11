#!/usr/bin/env bash
# Six independent CTSM/CLM-FATES 500-year startup spin-ups on Southampton IRIDIS6.
# Proven GF-Guy software/build and 5-year segment configuration; DIFFERENCES:
#   - each site's own surface, full-record DATM cycle, and first-year fixed CO2.
# Before ANY submission: preflight all inputs; prepare & validate all six cases.
# No one-year run, no case.build, no modification of GF-Guy or existing cases.
set -Eeuo pipefail
trap 'rc=$?; echo "ERROR at line $LINENO (exit ${rc}); consult the log. No automatic retry." >&2' ERR

USER_ID="${IRIDIS_USER:-${USER}}"
CLM_ROOT="/iridisfs/scratch/${USER_ID}/CLM_FATES"
CTSM="${CLM_ROOT}/CTSM"
INPUTDATA="${CLM_ROOT}/inputdata"
SITES_ROOT="${CLM_ROOT}/sites/MY_EC_SITE"
CASES_DIR="${CLM_ROOT}/cases"
OUT_ROOT="/scratch/${USER_ID}/CTSM_FATES_OUTPUTS"
SOURCE_NAME="GF-Guy_FATES_SURF2000_CO2405_1PT"
SOURCE_CASE="${CASES_DIR}/${SOURCE_NAME}"
FORCING_SUBDIR="datm_v5_candidate_timevarying_zbot"
# Historical years and CO2 are intentional research settings, not local CO2 measurements.
# Global annual mean CO2: NOAA GML co2_annmean_gl.csv, May 2026 (ppm).
SITES=( DE-Hai RU-Fyo DE-Tha DK-Sor NL-Loo IL-Yat )
declare -A FIRST=( [DE-Hai]=2000 [RU-Fyo]=1998 [DE-Tha]=1996 [DK-Sor]=1996 [NL-Loo]=1997 [IL-Yat]=2000 )
declare -A LAST=( [DE-Hai]=2025 [RU-Fyo]=2025 [DE-Tha]=2025 [DK-Sor]=2024 [NL-Loo]=2025 [IL-Yat]=2024 )
declare -A CO2=( [DE-Hai]=368.96 [RU-Fyo]=365.70 [DE-Tha]=361.93 [DK-Sor]=361.93 [NL-Loo]=363.04 [IL-Yat]=368.96 )
declare -A LAT=( [DE-Hai]=51.079213 [RU-Fyo]=56.4615278 [DE-Tha]=50.962597 [DK-Sor]=55.4858694 [NL-Loo]=52.16644722 [IL-Yat]=31.345044585655 )
declare -A LON=( [DE-Hai]=10.452168 [RU-Fyo]=32.9220833 [DE-Tha]=13.565333 [DK-Sor]=11.6446444 [NL-Loo]=5.74355 [IL-Yat]=35.0519885122776 )

TOTAL_YEARS=500
YEARS_PER_JOB=5
RESUBMITS=$((TOTAL_YEARS/YEARS_PER_JOB-1))
REPORT="${HOME}/six_site_spinup500_submission_manifest.tsv"

fail() { echo "STOP: $*" >&2; exit 1; }
announce() { printf '\n========== %s ==========\n' "$*"; }
xmlval() { ./xmlquery "$1" --value | tr -d '[:space:]'; }

[[ "$USER_ID" == "ly3n24" ]] || fail "Wrong IRIDIS username (${USER_ID}); review fixed paths before running."
[[ "$TOTAL_YEARS" == 500 && "$YEARS_PER_JOB" == 5 && "$RESUBMITS" == 99 ]] || fail 'Unexpected spin-up duration.'
[[ -d "$CTSM/cime/scripts" && -d "$INPUTDATA" && -d "$CASES_DIR" ]] || fail 'CTSM/inputdata/cases directory missing.'
[[ -x "$CTSM/cime/scripts/create_clone" ]] || fail 'CIME create_clone missing.'
[[ -d "$SOURCE_CASE" && -x "$SOURCE_CASE/xmlquery" ]] || fail 'GF-Guy source case missing.'
[[ -f "$SOURCE_CASE/user_nl_clm" && -f "$SOURCE_CASE/CaseStatus" ]] || fail 'GF-Guy source case incomplete.'
if ! grep -Eq 'model execution success|case.run success' "$SOURCE_CASE/CaseStatus"; then
  fail 'No successful GF-Guy model execution found: cannot trust keepexe source.'
fi
SOURCE_EXEROOT="$(cd "$SOURCE_CASE" && ./xmlquery EXEROOT --value | tr -d '[:space:]')"
[[ -x "$SOURCE_EXEROOT/cesm.exe" ]] || fail "Missing compiled GF-Guy cesm.exe in ${SOURCE_EXEROOT}"
[[ "$(cd "$SOURCE_CASE" && ./xmlquery BUILD_COMPLETE --value | tr -d '[:space:]')" == TRUE ]] || fail 'Source GF-Guy BUILD_COMPLETE not TRUE.'
command -v flock >/dev/null || fail 'flock is required.'
exec 9>"${CASES_DIR}/.six_site_spinup500_setup.lock"
flock -n 9 || fail 'Another six-site setup script is active.'

announce 'PREFLIGHT: ALL SIX SITE INPUTS (no submissions yet)'
for SITE in "${SITES[@]}"; do
  FIRST_Y="${FIRST[$SITE]}"; LAST_Y="${LAST[$SITE]}"; CO2_PPM="${CO2[$SITE]}"
  SITE_ROOT="${SITES_ROOT}/${SITE}"
  MODS="${SITE_ROOT}/subset_data/user_mods"
  DATM="${SITE_ROOT}/forcing/${FORCING_SUBDIR}"
  NAME="${SITE}_FATES_SPINUP500"
  CASE="${CASES_DIR}/${NAME}"
  RUN="${OUT_ROOT}/${NAME}/run"
  ARCHIVE="${OUT_ROOT}/archive/${NAME}"
  if [[ -e "$CASE" ]]; then
    [[ -d "$CASE" && -x "$CASE/xmlquery" && -f "$CASE/CaseStatus" ]] || fail "Existing case invalid: $CASE"
    [[ "$(cd "$CASE" && ./xmlquery CASE --value | tr -d '[:space:]')" == "$NAME" ]] || fail "Wrong existing case: $CASE"
    if grep -Eiq 'case\.submit success|model execution starting|case\.run (starting|success)' "$CASE/CaseStatus"; then
      fail "Case already submitted: $CASE"
    fi
    echo "Reusing unsubmitted case: $NAME"
  fi
  for d in "$RUN" "$ARCHIVE"; do
    if [[ -e "$d" ]]; then
      [[ -e "$CASE" && -d "$d" ]] || fail "Unexpected run/archive path: $d"
      [[ -z "$(find "$d" -type f \( -name '*.nc' -o -name 'rpointer.*' -o -name '*.log.*' \) -print -quit)" ]] || fail "Existing model output: $d"
    fi
  done
  [[ -s "${MODS}/user_nl_clm" ]] || fail "Site user_nl_clm missing: ${MODS}"
  # Verify an existing site-specific surface is really specified in generated user mods.
  shopt -s nullglob
  SURF_FILES=( "${SITE_ROOT}/subset_data/surfdata_${SITE}_hist_2000_16pfts_"*.nc )
  shopt -u nullglob
  [[ "${#SURF_FILES[@]}" -eq 1 && -s "${SURF_FILES[0]}" ]] || fail "Expected one nonempty surface for ${SITE}; found ${#SURF_FILES[@]}"
  grep -Fq "$(basename "${SURF_FILES[0]}")" "${MODS}/user_nl_clm" || fail "Site user_nl_clm does not reference ${SURF_FILES[0]}"
  n=0
  for ((year=FIRST_Y; year<=LAST_Y; year++)); do
    [[ -s "${DATM}/${SITE}_DATM_${year}.nc" ]] || fail "Missing ${SITE} DATM year ${year}"
    ((n+=1))
  done
  printf '%-8s DATM=%d years (%d-%d) CO2=%s ppm  Surface=%s\n' "$SITE" "$n" "$FIRST_Y" "$LAST_Y" "$CO2_PPM" "$(basename "${SURF_FILES[0]}")"
done

# CTSM generates site-specific shell_commands and namelists in user_mods.
# Use a TEMPORARY SANITIZED COPY with create_clone --user-mods-dir to bring
# across site latitude/longitude and any required single-point configuration.
# In particular, strip the known MPILIB=mpi-serial override: keepexe must
# retain the successfully built GF-Guy Intel/OpenMPI executable and layout.
# CIME refuses build-affecting changes when user-mods-dir and keepexe are combined.

announce 'PREPARE: SIX FATES CASES (no submissions yet)'
for SITE in "${SITES[@]}"; do
  FIRST_Y="${FIRST[$SITE]}"; LAST_Y="${LAST[$SITE]}"; CO2_PPM="${CO2[$SITE]}"
  SITE_ROOT="${SITES_ROOT}/${SITE}"
  MODS="${SITE_ROOT}/subset_data/user_mods"
  DATM="${SITE_ROOT}/forcing/${FORCING_SUBDIR}"
  NAME="${SITE}_FATES_SPINUP500"
  CASE="${CASES_DIR}/${NAME}"
  RUN="${OUT_ROOT}/${NAME}/run"
  ARCHIVE="${OUT_ROOT}/archive/${NAME}"

  if [[ -d "$CASE" ]]; then
    announce "RESUME UNSUBMITTED CLONE: ${SITE}"
  else
    announce "CREATE CLONE: ${SITE}"
    STAGED_MODS="$(mktemp -d "${HOME}/.six_site_${SITE}_mods.XXXXXX")"
    cp -a "${MODS}/." "${STAGED_MODS}/"
    if [[ -f "${STAGED_MODS}/shell_commands" ]]; then
      sed -i -E '/MPILIB[[:space:]]*=[[:space:]]*mpi-serial/d' "${STAGED_MODS}/shell_commands"
    fi
    (cd "${CTSM}/cime/scripts" && ./create_clone --case "$CASE" --clone "$SOURCE_CASE" --user-mods-dir "$STAGED_MODS" --keepexe)
  fi
  [[ -x "${CASE}/xmlquery" ]] || fail "Clone creation failed: ${SITE}"
  cd "$CASE"

  # Apply single-point generated surface configuration (no GF-Guy fsurdat).
  cp -p "${MODS}/user_nl_clm" user_nl_clm
  sed -i -E '/^[[:space:]]*(use_excess_ice|use_excess_ice_streams|hist_nhtfrq|hist_mfilt)[[:space:]]*=/d' user_nl_clm
  cat >> user_nl_clm <<'NML'

! Preserve GF-Guy successful numerical setup (no extra physics changes)
use_excess_ice = .false.
use_excess_ice_streams = .false.
hist_nhtfrq = -24
hist_mfilt = 365
NML
  [[ -s user_nl_clm ]] || fail "Failed writing ${SITE} land namelist"
  grep -Fq "surfdata_${SITE}_hist_2000_16pfts_" user_nl_clm || fail "Wrong surface in ${SITE} user_nl_clm"

  # Keep site point coordinates distinct from GF-Guy. On CLM_USRDAT these
  # XML controls may be defined by the generated user_mods shell_commands.
  # If available, ensure they match each site's verified BIF coordinates.
  if ./xmlquery PTS_LAT --value >/dev/null 2>&1; then
    ./xmlchange PTS_LAT="${LAT[$SITE]}"
  fi
  if ./xmlquery PTS_LON --value >/dev/null 2>&1; then
    ./xmlchange PTS_LON="${LON[$SITE]}"
  fi

  # Generate the exact stream syntax used by the successful GF-Guy case.
  {
    printf 'CLM_USRDAT.UNSET:taxmode = cycle\n'
    printf 'CLM_USRDAT.UNSET:tintalgo = linear\n'
    printf 'CLM_USRDAT.UNSET:mapalgo = none\n'
    printf 'CLM_USRDAT.UNSET:meshfile = none\n\n'
    printf 'CLM_USRDAT.UNSET:year_first = %s\n' "$FIRST_Y"
    printf 'CLM_USRDAT.UNSET:year_last = %s\n' "$LAST_Y"
    printf 'CLM_USRDAT.UNSET:year_align = %s\n\n' "$FIRST_Y"
    printf 'CLM_USRDAT.UNSET:datafiles = \\\n'
    for ((year=FIRST_Y; year<=LAST_Y; year++)); do
      if ((year < LAST_Y)); then
        printf '%s, \\\n' "${DATM}/${SITE}_DATM_${year}.nc"
      else
        printf '%s\n' "${DATM}/${SITE}_DATM_${year}.nc"
      fi
    done
    cat <<'DATM_VARS'

CLM_USRDAT.UNSET:datavars = \
PRECTmms Faxa_precn, \
FSDS Faxa_swdn, \
ZBOT Sa_z, \
TBOT Sa_tbot, \
WIND Sa_wind, \
QBOT Sa_shum, \
PSRF Sa_pbot, \
FLDS Faxa_lwdn
DATM_VARS
  } > user_nl_datm_streams
  touch user_nl_datm

  ./xmlchange DIN_LOC_ROOT="$INPUTDATA"
  ./xmlchange RUN_TYPE=startup
  ./xmlchange CONTINUE_RUN=FALSE
  ./xmlchange RUN_STARTDATE="${FIRST_Y}-01-01"
  ./xmlchange CALENDAR=NO_LEAP
  ./xmlchange ATM_NCPL=48
  ./xmlchange CLM_CO2_TYPE=constant
  ./xmlchange CCSM_CO2_PPMV="$CO2_PPM"
  ./xmlchange STOP_OPTION=nyears
  ./xmlchange STOP_N="$YEARS_PER_JOB"
  ./xmlchange REST_OPTION=nyears
  ./xmlchange REST_N="$YEARS_PER_JOB"
  ./xmlchange RESUBMIT="$RESUBMITS"
  ./xmlchange DOUT_S=TRUE
  ./xmlchange DOUT_S_ROOT="$ARCHIVE"
  ./xmlchange RUNDIR="$RUN"

  if [[ ! -f .case.run || ! -f case.st_archive ]]; then
    if grep -q 'case.setup success' CaseStatus; then ./case.setup --reset; else ./case.setup; fi
  fi
  [[ -f .case.run && -f case.st_archive ]] || fail "CIME batch scripts missing: ${SITE}"

  # A keepexe clone shares the already compiled GF-Guy binary.
  EXEROOT="$(xmlval EXEROOT)"
  [[ "$EXEROOT" == "$SOURCE_EXEROOT" && -x "${EXEROOT}/cesm.exe" ]] || fail "Unsafe/incorrect EXEROOT for ${SITE}"
  [[ "$(xmlval RUNDIR)" == "$RUN" ]] || fail "Wrong RUNDIR for ${SITE}"
  [[ "$(xmlval RESUBMIT)" == "$RESUBMITS" ]] || fail "Wrong RESUBMIT for ${SITE}"
  [[ "$(xmlval STOP_N)" == "$YEARS_PER_JOB" ]] || fail "Wrong STOP_N for ${SITE}"
  [[ "$(LC_ALL=C printf "%.2f" "$(xmlval CCSM_CO2_PPMV)")" == "$CO2_PPM" ]] || fail "Wrong fixed CO2 for ${SITE}: CIME may normalize trailing zeros"

  # CIME requires an up-to-date generated land namelist before job submit.
  ./preview_namelists
  [[ -s CaseDocs/lnd_in ]] || fail "Missing generated CaseDocs/lnd_in for ${SITE}"
  grep -Fq "surfdata_${SITE}_hist_2000_16pfts_" CaseDocs/lnd_in || fail "Wrong surface (GF-Guy?) in ${SITE} CaseDocs/lnd_in"
  grep -Eiq 'use_excess_ice[[:space:]]*=[[:space:]]*\.false\.' CaseDocs/lnd_in || fail "Excess-ice workaround absent for ${SITE}"
  if grep -Eiq '^[[:space:]]*use_excess_ice(_streams)?[[:space:]]*=[[:space:]]*\.true\.' CaseDocs/lnd_in; then
    fail "Excess ice still enabled for ${SITE}"
  fi
  ! grep -Fq 'GF-Guy_DATM_' user_nl_datm_streams || fail "Found GF-Guy forcing in ${SITE}"
  grep -Fq "${SITE}_DATM_${FIRST_Y}.nc" user_nl_datm_streams || fail "Missing first DATM year: ${SITE}"
  grep -Fq "${SITE}_DATM_${LAST_Y}.nc" user_nl_datm_streams || fail "Missing last DATM year: ${SITE}"
  ./check_input_data
  if [[ "$(xmlval BUILD_COMPLETE)" != TRUE ]]; then
    echo "Correcting clone BUILD_COMPLETE based on verified shared GF-Guy EXEROOT"
    ./xmlchange BUILD_COMPLETE=TRUE
  fi
  printf 'READY: %-8s forcing=%s-%s CO2=%s ppm total=%d (5-year jobs x 100)\n' "$SITE" "$FIRST_Y" "$LAST_Y" "$CO2_PPM" "$TOTAL_YEARS"
done

announce 'FINAL PRE-SUBMISSION REVIEW: ALL SIX CASES'
for SITE in "${SITES[@]}"; do
  FIRST_Y="${FIRST[$SITE]}"; LAST_Y="${LAST[$SITE]}"; CO2_PPM="${CO2[$SITE]}"
  CASE="${CASES_DIR}/${SITE}_FATES_SPINUP500"
  cd "$CASE"
  [[ -f CaseStatus && -f CaseDocs/lnd_in && -f .case.run ]] || fail "Incomplete ${SITE} case"
  grep -Eiq 'case\.submit success|model execution starting|case\.run starting' CaseStatus && fail "Already submitted ${SITE}"
  [[ "$(xmlval CLM_CO2_TYPE)" == constant ]] || fail "CO2 is not constant: ${SITE}"
  [[ "$(xmlval RUN_STARTDATE)" == "${FIRST_Y}-01-01" ]] || fail "Wrong start: ${SITE}"
  [[ "$(xmlval RESUBMIT)" == 99 && "$(xmlval STOP_N)" == 5 ]] || fail "Wrong spin-up length: ${SITE}"
  [[ "$(xmlval BUILD_COMPLETE)" == TRUE ]] || fail "Build not complete: ${SITE}"
  grep -Fq "CLM_USRDAT.UNSET:year_first = ${FIRST_Y}" user_nl_datm_streams || fail "Bad DATM year_first: ${SITE}"
  grep -Fq "CLM_USRDAT.UNSET:year_last = ${LAST_Y}" user_nl_datm_streams || fail "Bad DATM year_last: ${SITE}"
  grep -Fq 'CLM_USRDAT.UNSET:taxmode = cycle' user_nl_datm_streams || fail "Not DATM cycle: ${SITE}"
  printf 'READY %-8s %s-%s %s ppm\n' "$SITE" "$FIRST_Y" "$LAST_Y" "$CO2_PPM"
done

# All case configurations validated. Now—and only now—submit six jobs.
announce 'SUBMIT SIX INDEPENDENT 500-YEAR SPIN-UPS'
printf 'site\tcase\tforcing_first\tforcing_last\tfixed_co2_ppm\tsegments\tstatus\n' > "$REPORT"
for SITE in "${SITES[@]}"; do
  CASE="${CASES_DIR}/${SITE}_FATES_SPINUP500"
  cd "$CASE"
  echo "Submitting ${SITE} ..."
  if ./case.submit; then
    printf '%s\t%s\t%s\t%s\t%s\t100\tSUBMITTED\n' "$SITE" "$CASE" "${FIRST[$SITE]}" "${LAST[$SITE]}" "${CO2[$SITE]}" >> "$REPORT"
  else
    printf '%s\t%s\t%s\t%s\t%s\t100\tSUBMISSION_FAILED\n' "$SITE" "$CASE" "${FIRST[$SITE]}" "${LAST[$SITE]}" "${CO2[$SITE]}" >> "$REPORT"
    fail "Submission failed for ${SITE}; earlier jobs may already be queued. Inspect $REPORT"
  fi
done

announce 'SUBMISSION SUMMARY (submitting is not completing 500 years)'
cat "$REPORT"
echo
echo 'View jobs: squeue -u ly3n24'
echo "Manifest: $REPORT"
echo "Check a case: tail -20 ${CASES_DIR}/DE-Hai_FATES_SPINUP500/CaseStatus"
