#!/usr/bin/env bash
# Reproducibility record: DK-Sor first-year historical hybrid pilot preparation.
# Recorded from the successful 2026-10-18 CIME setup session, NOT an
# independently verified production run. Does NOT submit a job.
#
# WARNING: the named pilot case was already created on IRIDIS6.
# Re-running this script against that case is not necessary. It deliberately
# refuses to overwrite existing CIME cases, run directories or archives.
#
# A CIME case.setup --reset can leave BUILD_COMPLETE=FALSE even with --keepexe.
# Do not submit until the shared executable/build status and restart state
# have been separately checked; see 18_audit_DK_Sor_historical_pilot.sh.
set -Eeuo pipefail
trap 'rc=$?; echo "STOP line $LINENO (exit $rc). Inspect case before retrying." >&2' ERR

ROOT=/iridisfs/scratch/ly3n24/CLM_FATES
OUT=/scratch/ly3n24/CTSM_FATES_OUTPUTS
SRCNAME=DK-Sor_FATES_SPINUP500
NEWNAME=DK-Sor_FATES_HIST1996_2024_TEST
SRC="$ROOT/cases/$SRCNAME"
DST="$ROOT/cases/$NEWNAME"
STAMP=2996-01-01-00000
REF="$OUT/archive/$SRCNAME/rest/$STAMP"
RUNDIR="$OUT/$NEWNAME/run"
ARCHIVE="$OUT/archive/$NEWNAME"

echo "=== Check original case and restart ==="
test -x "$SRC/xmlquery"
test -d "$REF"
test -x "$ROOT/CTSM/cime/scripts/create_clone"
for comp in clm2 datm cpl; do
    test -s "$REF/$SRCNAME.$comp.r.$STAMP.nc"
done
for comp in atm lnd cpl; do
    test -s "$REF/rpointer.$comp.$STAMP"
done

# Never overwrite an existing case or output.
for path in "$DST" "$RUNDIR" "$ARCHIVE"; do
    if [ -e "$path" ]; then
        echo "STOP: already exists: $path"
        exit 1
    fi
done

echo "=== Clone DK-Sor ==="
(
    cd "$ROOT/CTSM/cime/scripts"
    ./create_clone --case "$DST" --clone "$SRC" --keepexe
)
cd "$DST"

echo "=== Configure one-year hybrid pilot ==="
./xmlchange RUN_TYPE=hybrid
./xmlchange CONTINUE_RUN=FALSE
./xmlchange RUN_REFCASE="$SRCNAME"
./xmlchange RUN_REFDATE=2996-01-01
./xmlchange RUN_REFTOD=00000
./xmlchange RUN_STARTDATE=1996-01-01
./xmlchange GET_REFCASE=FALSE
./xmlchange STOP_OPTION=nyears
./xmlchange STOP_N=1
./xmlchange REST_OPTION=nyears
./xmlchange REST_N=1
./xmlchange RESUBMIT=0
./xmlchange CLM_CO2_TYPE=constant
./xmlchange CCSM_CO2_PPMV=361.93
./xmlchange RUNDIR="$RUNDIR"
./xmlchange DOUT_S=TRUE
./xmlchange DOUT_S_ROOT="$ARCHIVE"
./xmlchange "MPI_RUN_COMMAND=srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores"

echo "=== Stage reference restart ==="
mkdir -p "$RUNDIR"
rsync -a \
  --exclude '*.clm2.h0a.*' \
  --exclude '*.clm2.h0i.*' \
  "$REF/" "$RUNDIR/"
for comp in atm lnd cpl; do
    cp -p "$RUNDIR/rpointer.$comp.$STAMP" "$RUNDIR/rpointer.$comp"
done

echo "=== Regenerate and inspect CIME configuration ==="
./case.setup --reset
SRC_EXE=$(cd "$SRC" && ./xmlquery EXEROOT --value)
NEW_EXE=$(./xmlquery EXEROOT --value)
if [ "$SRC_EXE" != "$NEW_EXE" ] || [ ! -x "$NEW_EXE/cesm.exe" ]; then
    echo "STOP: shared executable mismatch"
    exit 1
fi

./preview_namelists
./check_input_data
./preview_run

echo "=== Configuration (no job submitted) ==="
./xmlquery RUN_TYPE,CONTINUE_RUN,RUN_REFCASE,RUN_REFDATE,RUN_STARTDATE
./xmlquery STOP_N,REST_N,RESUBMIT,RUNDIR,DOUT_S_ROOT
./xmlquery EXEROOT,BUILD_COMPLETE
grep '^#SBATCH' .case.run || true

echo "PREPARATION COMPLETE — NOT SUBMITTED"
echo "IMPORTANT: Check BUILD_COMPLETE and verify hybrid/restart compatibility."
echo "New case: $DST"
