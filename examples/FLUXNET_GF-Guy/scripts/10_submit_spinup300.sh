#!/usr/bin/env bash
# GF-Guy Stage 2: create (or repair an UNSUBMITTED clone) and submit 300 years.
# The source 1-year case and existing 300-year results are NEVER modified.
# IMPORTANT: Existing submitted case => print status and EXIT WITHOUT CHANGES.
set -Eeuo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${HERE}/00_config.sh"
source "${HERE}/10_spinup_config.sh"

say() { printf '\n========== %s ==========\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# Never exit the interactive SSH shell: execute via bash this_script.sh.
trap 'rc=$?; echo "ERROR: step failed near line $LINENO; exit $rc" >&2' ERR

say 'GF-Guy 300-year spin-up (CO2=405 ppm; DATM 2017-2021)'

[[ "$SITE" == 'GF-Guy' ]] || die 'Wrong site ID'
[[ "$START_YEAR" == '2017' ]] || die 'Stage 1 source start year has changed; review setup'
[[ "$CO2_PPM" == '405.0' ]] || die 'Expected fixed CO2=405.0'
[[ "$SPINUP_FORCING_FIRST" == '2017' && "$SPINUP_FORCING_LAST" == '2021' ]] || die 'Unexpected forcing years'
[[ "$SPINUP_TOTAL_YEARS" =~ ^[0-9]+$ ]] || die 'TOTAL_YEARS must be integer'
[[ "$SPINUP_YEARS_PER_JOB" =~ ^[0-9]+$ ]] || die 'YEARS_PER_JOB must be integer'
(( SPINUP_YEARS_PER_JOB > 0 && SPINUP_TOTAL_YEARS % SPINUP_YEARS_PER_JOB == 0 )) || die 'Total years must divide into whole job segments'
(( SPINUP_TOTAL_YEARS == 300 && SPINUP_YEARS_PER_JOB == 5 )) || die 'Expected 300 years, 5 years per job'
RESUBMITS=$(( SPINUP_TOTAL_YEARS / SPINUP_YEARS_PER_JOB - 1 ))

[[ -d "$CASE" && -f "$CASE/CaseStatus" && -x "$CASE/xmlquery" ]] || die "Successful source case missing: $CASE"
[[ -f "$CASE/user_nl_clm" && -f "$CASE/user_nl_datm_streams" ]] || die 'Source case namelist/stream missing'
[[ -x "$CTSM/cime/scripts/create_clone" ]] || die 'CIME create_clone command missing'
[[ -d "$DATM_DIR" ]] || die "Forcing directory missing: $DATM_DIR"

# Stop two copies of this setup script running concurrently on the same login.
command -v flock >/dev/null || die 'flock is required'
exec 9>"${CLM_ROOT}/cases/.${SPINUP_CASE_NAME}.setup.lock"
flock -n 9 || die 'Another spin-up setup script is active'

# A submitted case is a scientific result: DO NOT redo setup or change XML.
if [[ -e "$SPINUP_CASE" ]]; then
    [[ -f "$SPINUP_CASE/CaseStatus" && -x "$SPINUP_CASE/xmlquery" ]] || die "Target path is not a valid CIME case: $SPINUP_CASE"
    if grep -Eiq 'case\.submit success|model execution starting|case\.run (starting|success)' "$SPINUP_CASE/CaseStatus"; then
        say 'ALREADY SUBMITTED — READ-ONLY EXIT'
        printf 'Case: %s\n' "$SPINUP_CASE"
        (cd "$SPINUP_CASE" && ./xmlquery CONTINUE_RUN,RESUBMIT,STOP_N)
        tail -15 "$SPINUP_CASE/CaseStatus"
        echo 'No setup changes, no resubmission. Run scripts/11_monitor_spinup300.sh instead.'
        exit 0
    fi
    echo 'Reusing an existing, not-yet-submitted clone.'
else
    say 'Cloning the successful one-year FATES executable'
    (cd "$CTSM/cime/scripts" && ./create_clone --case "$SPINUP_CASE" --clone "$CASE" --keepexe)
fi

cd "$SPINUP_CASE"
[[ "$(./xmlquery CASE --value | tr -d '[:space:]')" == "$SPINUP_CASE_NAME" ]] || die 'Incorrect CIME case identity'
[[ -f env_workflow.xml ]] || die 'CIME env_workflow.xml is missing'
grep -q 'case.run' env_workflow.xml || die 'CIME workflow does not define case.run'

# Ensure no previous model output exists. Never destroy/overwrite simulation data.
for directory in "$SPINUP_RUNDIR" "$SPINUP_ARCHIVE"; do
    if [[ -d "$directory" ]]; then
        if find "$directory" -type f \( -name '*.nc' -o -name 'rpointer.*' -o -name '*.log.*' \) -print -quit | grep -q .; then
            die "Previous model output exists: $directory. Refusing to reuse this run."
        fi
    fi
done

say 'Creating / repairing CIME batch scripts'
# A fresh clone may not have .case.run; case.setup generates it. The correct
# archive filename is case.st_archive (NO leading dot).
if [[ ! -f .case.run || ! -f case.st_archive ]]; then
    if grep -q 'case.setup success' CaseStatus; then
        ./case.setup --reset
    else
        ./case.setup
    fi
fi
[[ -f .case.run ]] || die 'CIME batch script .case.run missing after setup'
[[ -f case.st_archive ]] || die 'CIME batch script case.st_archive missing after setup'

say 'Writing 300-year CIME configuration'
./xmlchange RUN_TYPE=startup
./xmlchange CONTINUE_RUN=FALSE
./xmlchange RUN_STARTDATE="${START_YEAR}-01-01"
./xmlchange CALENDAR=NO_LEAP
./xmlchange ATM_NCPL=48
./xmlchange CLM_CO2_TYPE=constant
./xmlchange CCSM_CO2_PPMV="$CO2_PPM"
./xmlchange STOP_OPTION=nyears
./xmlchange STOP_N="$SPINUP_YEARS_PER_JOB"
./xmlchange REST_OPTION=nyears
./xmlchange REST_N="$SPINUP_YEARS_PER_JOB"
./xmlchange RESUBMIT="$RESUBMITS"
./xmlchange DOUT_S=TRUE
./xmlchange DOUT_S_ROOT="$SPINUP_ARCHIVE"
./xmlchange DIN_LOC_ROOT="$INPUTDATA"
./xmlchange RUNDIR="$SPINUP_RUNDIR"

say 'Checking cloned executable (no recompilation)'
SOURCE_EXEROOT="$(cd "$CASE" && ./xmlquery EXEROOT --value | tr -d '[:space:]')"
CLONE_EXEROOT="$(./xmlquery EXEROOT --value | tr -d '[:space:]')"
SOURCE_RUN="$(cd "$CASE" && ./xmlquery RUNDIR --value | tr -d '[:space:]')"
[[ -n "$SOURCE_EXEROOT" && "$SOURCE_EXEROOT" == "$CLONE_EXEROOT" ]] || die 'Source and clone EXEROOT mismatch: keepexe unsafe'
[[ -x "$CLONE_EXEROOT/cesm.exe" ]] || die "Compiled executable missing: $CLONE_EXEROOT/cesm.exe"
[[ "$SPINUP_RUNDIR" != "$SOURCE_RUN" ]] || die 'Source and spin-up RUNDIR must differ'
[[ "$SPINUP_ARCHIVE" != "$ARCHIVE_ROOT" ]] || die 'Source and spin-up archive must differ'

say 'Generating strict DATM 2017-2021 cycle'
python "${HERE}/prepare_datm_cycle.py" \
    --source "$CASE/user_nl_datm_streams" \
    --output "$SPINUP_CASE/user_nl_datm_streams" \
    --site "$SITE" \
    --first "$SPINUP_FORCING_FIRST" \
    --last "$SPINUP_FORCING_LAST" \
    --forcing-dir "$DATM_DIR"

say 'Applying successful GF-Guy Excess Ice fix and daily history'
cp -p "$CASE/user_nl_clm" user_nl_clm
sed -i -E '/^[[:space:]]*(use_excess_ice|use_excess_ice_streams|hist_nhtfrq|hist_mfilt)[[:space:]]*=/d' user_nl_clm
cat >> user_nl_clm <<'NML'

! GF-Guy 300-year spin-up; same setup as successful 1-year case.
use_excess_ice = .false.
use_excess_ice_streams = .false.
hist_nhtfrq = -24
hist_mfilt = 365
NML

say 'Validating generated namelists and forcing inputs'
./preview_namelists
[[ -f CaseDocs/lnd_in ]] || die 'CaseDocs/lnd_in not generated'
if grep -Eiq '^[[:space:]]*use_excess_ice(_streams)?[[:space:]]*=[[:space:]]*\.true\.' CaseDocs/lnd_in; then
    die 'Excess Ice remains enabled'
fi
./check_input_data

# CIME `case.setup --reset` can leave BUILD_COMPLETE=FALSE even for a clone
# that shares the SUCCESSFULLY COMPILED source cesm.exe. Only restore after
# matching EXEROOT and confirming actual executable is present and executable.
if [[ "$(./xmlquery BUILD_COMPLETE --value | tr -d '[:space:]')" != 'TRUE' ]]; then
    echo 'Restoring BUILD_COMPLETE=TRUE for verified --keepexe clone.'
    ./xmlchange BUILD_COMPLETE=TRUE
fi

say 'Final review'
./xmlquery RUN_STARTDATE,CALENDAR,STOP_N,REST_N,RESUBMIT,CONTINUE_RUN,CLM_CO2_TYPE,CCSM_CO2_PPMV,BUILD_COMPLETE,RUNDIR,DOUT_S_ROOT
printf '\nDATM configuration:\n'
grep -E 'taxmode|year_first|year_last|year_align|GF-Guy_DATM_' user_nl_datm_streams
printf '\nExcess Ice:\n'
grep -E 'use_excess_ice|hist_nhtfrq|hist_mfilt' CaseDocs/lnd_in || true
[[ -f .case.run && -f case.st_archive ]] || die 'CIME batch scripts missing'

# Recheck after preparation to avoid duplicate submissions.
if grep -Eiq 'case\.submit success|model execution starting|case\.run (starting|success)' CaseStatus; then
    die 'Submission detected while preparing; refusing another submit'
fi

say 'SUBMIT: first of 60 five-year segments'
./case.submit
say 'Job submitted (NOT evidence 300 years have completed)'
echo 'Read-only monitoring: bash scripts/11_monitor_spinup300.sh'
