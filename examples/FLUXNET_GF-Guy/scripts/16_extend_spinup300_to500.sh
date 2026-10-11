#!/usr/bin/env bash

# ============================================================
# GF-Guy CLM-FATES: Extend Spin-up from 300 to 500 years
#
# Existing: 2017-01-01 -> 2317-01-01 (300 years)
# Extend:   2317-01-01 -> 2517-01-01 (200 years)
#
# CO2: constant 405 ppm
# DATM: 2017-2021 cycling
# 40 jobs x 5 years = 200 additional years
#
# Reuses the existing Case and executable.
# No case.setup or case.build.
# ============================================================

set -Eeuo pipefail

trap 'echo "ERROR near line $LINENO. Check the log." >&2' ERR

ROOT=/iridisfs/scratch/ly3n24/CLM_FATES

NAME=GF-Guy_FATES_SPINUP300_CO2405
CASE="$ROOT/cases/$NAME"

ARCHIVE="/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive/$NAME"

STAMP=2317-01-01-00000
REST="$ARCHIVE/rest/$STAMP"

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

section() {
    printf '\n========== %s ==========\n' "$*"
}


# ============================================================
# 1. VERIFY COMPLETED 300-YEAR RUN
# ============================================================

section "1. Checking completed 300-year Spin-up"

[[ -d "$CASE" && -f "$CASE/CaseStatus" ]] || \
    fail "Case not found"

cd "$CASE"

# Previous simulation must contain 60 successful runs.
N_SUCCESS=$(grep -c 'model execution success' CaseStatus || true)

[[ "$N_SUCCESS" == 60 ]] || \
    fail "Expected 60 successful runs, found $N_SUCCESS"

[[ "$(./xmlquery RESUBMIT --value | tr -d '[:space:]')" == 0 ]] || \
    fail "Previous RESUBMIT is not zero"

[[ "$(./xmlquery CONTINUE_RUN --value | tr -d '[:space:]' | tr '[:lower:]' '[:upper:]')" == TRUE ]] || \
    fail "CONTINUE_RUN is not TRUE"

# Prevent submitting the extension twice.
LAST_SUBMIT=$(grep -n 'case.submit success' CaseStatus | tail -1 | cut -d: -f1)
LAST_ARCHIVE=$(grep -n 'st_archive success' CaseStatus | tail -1 | cut -d: -f1)

[[ -n "$LAST_SUBMIT" && -n "$LAST_ARCHIVE" ]] || \
    fail "Submission/archive record missing"

(( LAST_ARCHIVE > LAST_SUBMIT )) || \
    fail "A newer job has already been submitted"

ACTIVE=$(squeue -u ly3n24 -h -o '%j' | grep -F "$NAME" || true)

[[ -z "$ACTIVE" ]] || \
    fail "GF-Guy job is already running or queued"

[[ -d "$REST" ]] || \
    fail "Final 2317 restart directory missing"

LATEST=$(find "$ARCHIVE/rest" \
    -mindepth 1 -maxdepth 1 -type d \
    -printf '%f\n' | sort | tail -1)

[[ "$LATEST" == "$STAMP" ]] || \
    fail "Unexpected latest restart: $LATEST"

# Check all 300 history years.
N_HIST=$(find "$ARCHIVE/lnd/hist" \
    -maxdepth 1 -type f \
    -name "$NAME.clm2.h0a.*.nc" | wc -l)

[[ "$N_HIST" == 300 ]] || \
    fail "Expected 300 history files, found $N_HIST"

# Check essential archived restart datasets.
for prefix in clm2.r datm.r cpl.r; do
    [[ -s "$REST/$NAME.$prefix.$STAMP.nc" ]] || \
        fail "Missing $prefix restart at 2317"
done

echo "Previous 300-year run verified."


# ============================================================
# 2. VERIFY CO2, DATM AND EXECUTABLE
# ============================================================

section "2. Checking model configuration"

CO2=$(./xmlquery CCSM_CO2_PPMV --value | tr -d '[:space:]')
CO2_TYPE=$(./xmlquery CLM_CO2_TYPE --value | tr -d '[:space:]')
BUILD=$(./xmlquery BUILD_COMPLETE --value | tr -d '[:space:]')
STOP_OPTION=$(./xmlquery STOP_OPTION --value | tr -d '[:space:]')
STOP_N=$(./xmlquery STOP_N --value | tr -d '[:space:]')

[[ "$CO2" == 405.0 ]] || fail "Unexpected CO2: $CO2"
[[ "$CO2_TYPE" == constant ]] || fail "CO2 is not constant"
[[ "${BUILD^^}" == TRUE ]] || fail "BUILD_COMPLETE is not TRUE"
[[ "$STOP_OPTION" == nyears && "$STOP_N" == 5 ]] || \
    fail "Unexpected STOP configuration"

for setting in \
    'taxmode = cycle' \
    'year_first = 2017' \
    'year_last = 2021' \
    'year_align = 2017'; do

    grep -Fq "$setting" user_nl_datm_streams || \
        fail "Incorrect DATM setting: $setting"
done

EXEROOT=$(./xmlquery EXEROOT --value | tr -d '[:space:]')

[[ -x "$EXEROOT/cesm.exe" ]] || fail "cesm.exe missing"

[[ -f .case.run && -f case.st_archive ]] || \
    fail "CIME batch scripts missing"

echo "CO2 = 405 ppm"
echo "DATM = 2017-2021 cycling"
echo "Executable verified."


# ============================================================
# 3. RESTORE FINAL RESTART + TIMESTAMPED RPOINTERS
# ============================================================

section "3. Restoring 2317 restart"

RUNDIR=$(./xmlquery RUNDIR --value | tr -d '[:space:]')

# Check expected run directory.
[[ "$RUNDIR" == /scratch/ly3n24/CTSM_FATES_OUTPUTS/*/run ]] || \
    fail "Unexpected RUNDIR: $RUNDIR"

mkdir -p "$RUNDIR"

# Restore archived restart datasets without changing the archive.
cp -a "$REST"/. "$RUNDIR"/

# IMPORTANT:
# Current CTSM uses date-stamped restart pointer names:
#
# rpointer.lnd.2317-01-01-00000
# rpointer.atm.2317-01-01-00000
# rpointer.cpl.2317-01-01-00000
#
# These pointers may be located in REST or already in RUNDIR.

for component in lnd atm cpl; do

    DATED="rpointer.$component.$STAMP"
    PLAIN="rpointer.$component"

    if [[ -s "$REST/$DATED" ]]; then

        cp -p "$REST/$DATED" "$RUNDIR/$DATED"

    elif [[ -s "$RUNDIR/$DATED" ]]; then

        # Correct dated pointer is already available.
        :

    elif [[ -s "$REST/$PLAIN" ]]; then

        # Backward-compatible pointer file.
        cp -p "$REST/$PLAIN" "$RUNDIR/$DATED"

    else

        fail "Cannot find final $DATED"

    fi

    [[ -s "$RUNDIR/$DATED" ]] || \
        fail "Failed to restore $DATED"

    # Confirm pointer references the intended restart date.
    grep -Fq "$STAMP" "$RUNDIR/$DATED" || \
        fail "$DATED does not reference 2317 restart"

    echo "Verified: $DATED"

done

# Ensure all component restart datasets are staged.
for prefix in clm2.r datm.r cpl.r; do

    [[ -s "$RUNDIR/$NAME.$prefix.$STAMP.nc" ]] || \
        fail "Missing staged $prefix restart"

done

# Protect against existing extended output.
if find "$ARCHIVE/lnd/hist" -maxdepth 1 \
    -name "$NAME.clm2.h0a.2317-*.nc" \
    -print -quit | grep -q .; then

    fail "Extended simulation output already exists"

fi

echo "2317 restart successfully staged."


# ============================================================
# 4. CONFIGURE ADDITIONAL 200 YEARS
# ============================================================

section "4. Configuring another 200 years"

# Back up XML configuration.
cp -p env_run.xml \
    "env_run.xml.before_extend300to500.$(date +%Y%m%d_%H%M%S)"

# Continue existing simulation.
./xmlchange CONTINUE_RUN=TRUE

# Five years per job.
./xmlchange STOP_OPTION=nyears
./xmlchange STOP_N=5

# Restart every five years.
./xmlchange REST_OPTION=nyears
./xmlchange REST_N=5

# First run + 39 resubmissions = 40 jobs = 200 years.
./xmlchange RESUBMIT=39

echo
./xmlquery CONTINUE_RUN,STOP_OPTION,STOP_N,REST_OPTION,REST_N,RESUBMIT

echo
echo "Start restart: 2317-01-01"
echo "Additional years: 200"
echo "Final restart: 2517-01-01"
echo "Total spin-up: 500 model years"


# ============================================================
# 5. SUBMIT
# ============================================================

section "5. Submitting additional 200-year Spin-up"

./case.submit

echo
echo "=============================================="
echo " GF-Guy 300 -> 500 year extension SUBMITTED"
echo "=============================================="
echo
echo "Monitor:"
echo "squeue -u ly3n24"
echo
echo "CaseStatus:"
echo "tail -25 $CASE/CaseStatus"
