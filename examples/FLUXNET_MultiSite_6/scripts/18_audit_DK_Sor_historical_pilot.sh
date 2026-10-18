#!/usr/bin/env bash
# READ-ONLY DK-Sor historical hybrid pilot audit, IRIDIS6.
# Does not change XML, restart/pointer files, build status or Slurm jobs.
# 0 = all basic preflight checks passed. Nonzero = NOT READY or incomplete.
# Scientific compatibility, e.g. mapping old DATM restart state onto 1996,
# still needs a checked first-year run before extending to 1996–2024.
set -Eeuo pipefail
ROOT=/iridisfs/scratch/ly3n24/CLM_FATES
OUT=/scratch/ly3n24/CTSM_FATES_OUTPUTS
SRCNAME=DK-Sor_FATES_SPINUP500
NAME=DK-Sor_FATES_HIST1996_2024_TEST
CASE="$ROOT/cases/$NAME"
SRC="$ROOT/cases/$SRCNAME"
STAMP=2996-01-01-00000
REST="$OUT/archive/$SRCNAME/rest/$STAMP"
RUN="$OUT/$NAME/run"
ARCH="$OUT/archive/$NAME"
fail() { echo "NOT READY: $*" >&2; exit 1; }
val() { (cd "$CASE" && ./xmlquery "$1" --value | tr -d '[:space:]'); }
srcval() { (cd "$SRC" && ./xmlquery "$1" --value | tr -d '[:space:]'); }
expect() { local key="$1" value="$2" actual; actual=$(val "$key"); [ "$actual" = "$value" ] || fail "$key=$actual, expected $value"; }
[ -x "$CASE/xmlquery" ] || fail "pilot case missing: $CASE"
[ -x "$SRC/xmlquery" ] || fail "source spin-up case missing: $SRC"
[ -d "$REST" ] || fail "archived 1000-year restart directory missing"
[ -d "$RUN" ] || fail "pilot run directory missing"

echo "=== CIME identity and timing ==="
expect CASE "$NAME"
expect RUN_TYPE hybrid
expect CONTINUE_RUN FALSE
expect RUN_REFCASE "$SRCNAME"
expect RUN_REFDATE 2996-01-01
expect RUN_REFTOD 00000
expect RUN_STARTDATE 1996-01-01
expect GET_REFCASE FALSE
expect STOP_OPTION nyears
expect STOP_N 1
expect RESUBMIT 0
expect CALENDAR NO_LEAP
expect ATM_NCPL 48
expect CLM_CO2_TYPE constant
expect RUNDIR "$RUN"
expect DOUT_S_ROOT "$ARCH"
echo "PASS: basic case/timing configuration"

echo "=== Shared build ==="
src_exe=$(srcval EXEROOT)
new_exe=$(val EXEROOT)
[ "$src_exe" = "$new_exe" ] || fail "EXEROOT mismatch"
[ -x "$new_exe/cesm.exe" ] || fail "Shared executable missing/not executable"
[ "$(srcval BUILD_COMPLETE)" = TRUE ] || fail "Original spin-up case BUILD_COMPLETE not TRUE"
if [ "$(val BUILD_COMPLETE)" != TRUE ]; then
    fail "Pilot BUILD_COMPLETE is FALSE. Check shared build provenance first; do not submit."
fi
echo "PASS: shared executable and build status"

echo "=== Required archived restart files ==="
for comp in clm2 datm cpl; do
    [ -s "$REST/$SRCNAME.$comp.r.$STAMP.nc" ] || fail "Missing archived $comp restart"
    [ -s "$RUN/$SRCNAME.$comp.r.$STAMP.nc" ] || fail "Missing staged $comp restart"
done
for comp in atm lnd cpl; do
    [ -s "$RUN/rpointer.$comp" ] || fail "Missing active rpointer.$comp"
    [ -s "$RUN/rpointer.$comp.$STAMP" ] || fail "Missing dated rpointer.$comp"
done
echo "PASS: staged restart set present"

echo "=== Land initialization and met forcing ==="
LND="$CASE/CaseDocs/lnd_in"
[ -s "$LND" ] || fail "Missing CaseDocs/lnd_in"
grep -Fq "$SRCNAME.clm2.r.$STAMP.nc" "$LND" || fail "Wrong finidat"
grep -Fq 'surfdata_DK-Sor_hist_' "$LND" || fail "Wrong site surface"
STREAM="$CASE/user_nl_datm_streams"
[ -s "$STREAM" ] || fail "Missing DATM stream"
for pair in "year_first 1996" "year_last 2024" "year_align 1996" "taxmode cycle"; do
    read -r key value <<< "$pair"
    grep -Eq "^CLM_USRDAT[.]UNSET:$key[[:space:]]*=[[:space:]]*$value[[:space:]]*$" "$STREAM" || fail "Wrong DATM $key"
done
echo "PASS: land initialization/forcing metadata"

echo "=== Slurm and MPI ==="
grep -Eq '^#SBATCH[[:space:]]+--nodes=1([[:space:]]|$)' "$CASE/.case.run" || fail "Wrong node count"
grep -Fq 'srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores' "$CASE/.case.run" || fail "MPI launcher absent from .case.run"
echo "PASS: Slurm/MPI configuration"
echo
echo "BASIC PREFLIGHT PASSED — STILL NOT EVIDENCE OF RUN SUCCESS."
echo "Before any case.submit: examine hybrid DATM/coupler restart semantics,"
echo "run preview_run, and confirm correct 1996 model/forcing time alignment."
