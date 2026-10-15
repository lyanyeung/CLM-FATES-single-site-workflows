#!/usr/bin/env bash
# CH-Aws ONLY: clone separate case using Stage26 v3 DATM, same GF-Guy binary,
# Slurm/PMIx core affinity, FAST human index. Submit ALL 1000 years directly.
# 5-year automatic CIME segments x 200, with first RESUBMIT=199. No smoke test.
set -Eeuo pipefail
trap 'rc=$?; echo "FAILED line $LINENO rc=$rc; inspect logs. No automatic rerun." >&2' ERR
MODE="${1:---audit}"
case "$MODE" in --audit|--prepare|--submit1000|--status) ;; *) echo 'Usage: --audit | --prepare | --submit1000 | --status'; exit 2;; esac
[[ "$(id -un)" == ly3n24 ]] || { echo 'Wrong IRIDIS user';exit 2; }
SITE='CH-Aws'
CASES='/iridisfs/scratch/ly3n24/CLM_FATES/cases'
CTSM='/iridisfs/scratch/ly3n24/CLM_FATES/CTSM'
DATM='/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing/datm_11_landrh25a_dynamic_zbot_v3'
OLD="$CASES/CH-Aws_FATES_SPINUP500_11P"
NAME='CH-Aws_FATES_SPINUP1000_RH25A'
NEW="$CASES/$NAME"
OUT='/scratch/ly3n24/CTSM_FATES_OUTPUTS'
RUNDIR="$OUT/$NAME/run"
ARCH="$OUT/archive/$NAME"
EXREF="$CASES/GF-Guy_FATES_SURF2000_CO2405_1PT"
MPI='srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores'
BUILDER="$HOME/26_CH_Aws_build_DATM_v3.py"
LOCK="$HOME/.CH_Aws_RH25A_setup.lock"
fail(){ echo "STOP: $*" >&2; exit 1; }
xval(){ (cd "$1" && ./xmlquery "$2" --value) | tr -d '[:space:]'; }
xraw(){ (cd "$1" && ./xmlquery "$2" --value) | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'; }
lock(){ exec 9>"$LOCK"; flock -n 9 || fail 'another stage27 operation is active'; }
no_new_jobs(){
    ! squeue -h -u "$(id -un)" -o '%j' | grep -Fxq "run.$NAME" || fail 'This NEW model run already queued'
    ! squeue -h -u "$(id -un)" -o '%j' | grep -Fxq "st_archive.$NAME" || fail 'This NEW archive already queued'
}
verify_batch(){
    local f k
    for f in "$NEW/.case.run" "$NEW/case.st_archive"; do
       [[ -s "$f" ]] || fail "Batch missing: $f"
       ! grep -q -- '--exclusive' "$f" || fail "--exclusive present: $f"
       for k in '--nodes=1' '--ntasks-per-node=1' '--cpus-per-task=1' '--mem=8G'; do
          grep -Eq "^#SBATCH[[:space:]]+${k}[[:space:]]*$" "$f" || fail "Missing $k in $f"
       done
    done
}
patch_batch(){
python3 - "$NEW/env_batch.xml" <<'PY'
from pathlib import Path
import re,sys,xml.etree.ElementTree as ET
p=Path(sys.argv[1]);s=p.read_text()
s,n=re.subn(r'(?m)^[ \t]*<directive>[ \t]*--exclusive[ \t]*</directive>[ \t]*\r?\n','',s)
if n>2 or '--exclusive' in s:raise SystemExit('STOP: unusual exclusive directive; do not override')
needle='<directive>--cpus-per-task={{ thread_count }}</directive>'
if s.count(needle)!=1:raise SystemExit('STOP: unexpected CIME batch cpus template')
mem='<directive>--mem=8G</directive>'
allmem=re.findall(r'<directive>\s*--mem(?:=|\s).*?</directive>',s)
if not allmem:s=s.replace(needle,needle+'\n        '+mem,1)
elif len(allmem)!=1 or allmem[0]!=mem:raise SystemExit('STOP: unexpected --mem directive')
ET.fromstring(s)
p.write_text(s)
print('Batch XML patched: no exclusive, --mem=8G')
PY
}
verify_new(){
    [[ -x "$NEW/xmlquery" && -x "$NEW/case.submit" ]] || fail 'New CIME case not found'
    [[ "$(xval "$NEW" CASE)" == "$NAME" ]] || fail 'Unexpected CASE name'
    [[ "$(xval "$NEW" RUN_TYPE)" == startup && "$(xval "$NEW" CONTINUE_RUN)" == FALSE ]] || fail 'Not fresh startup'
    [[ "$(xval "$NEW" CALENDAR)" == NO_LEAP && "$(xval "$NEW" ATM_NCPL)" == 48 ]] || fail 'Wrong time step/calendar'
    [[ "$(xval "$NEW" RUN_STARTDATE)" == 2006-01-01 ]] || fail 'Wrong first year'
    [[ "$(xval "$NEW" STOP_N)" == 5 && "$(xval "$NEW" REST_N)" == 5 && "$(xval "$NEW" RESUBMIT)" == 199 ]] || fail 'Expected 1000yr CIME auto-resubmission'
    [[ "$(xval "$NEW" BUILD_COMPLETE)" == TRUE ]] || fail 'Shared executable not marked built'
    [[ "$(xval "$NEW" DOUT_S)" == TRUE ]] || fail 'Archive not enabled'
    [[ "$(xval "$NEW" RUNDIR)" == "$RUNDIR" && "$(xval "$NEW" DOUT_S_ROOT)" == "$ARCH" ]] || fail 'Output paths mismatched'
    [[ "$(xval "$NEW" CLM_CO2_TYPE)" == constant ]] || fail 'CO2 not constant'
    python3 - "$(xval "$NEW" CCSM_CO2_PPMV)" <<'PY'
import sys
assert abs(float(sys.argv[1])-381.15)<0.011,'unexpected CO2 for CH-Aws'
PY
    [[ "$(xraw "$NEW" MPI_RUN_COMMAND)" == "$MPI" ]] || fail 'PMIx srun binding incorrect'
    [[ "$(xval "$NEW" RUN_STARTDATE)" == 2006-01-01 ]] || fail 'Original model forcing cycle must start at 2006'
    [[ "$(xval "$NEW" MPILIB)" == "$(xval "$EXREF" MPILIB)" ]] || fail 'MPI library differs from GF-Guy'
    local exe
    exe="$(xval "$EXREF" EXEROOT)"
    [[ "$(xval "$NEW" EXEROOT)" == "$exe" && -x "$exe/cesm.exe" ]] || fail 'Shared GF-Guy binary missing'
    local comp
    for comp in ATM LND CPL;do
       [[ "$(xval "$NEW" NTASKS_$comp)" == 1 && "$(xval "$NEW" NTHRDS_$comp)" == 1 ]] || fail "$comp not single-rank/thread"
    done
    verify_batch
    [[ -s "$NEW/user_nl_clm" && -s "$NEW/user_nl_datm_streams" ]] || fail 'New site namelists missing'
    grep -Eq "^[[:space:]]*calc_human_stress_indices[[:space:]]*=[[:space:]]*'FAST'" "$NEW/CaseDocs/lnd_in" || fail 'FAST not effective in CLM namelist'
    grep -Eiq '^[[:space:]]*use_excess_ice[[:space:]]*=[[:space:]]*\.false\.' "$NEW/CaseDocs/lnd_in" || fail 'Existing tested FATES excess ice workaround missing'
    grep -Fq "$DATM/CH-Aws_DATM_2006.nc" "$NEW/user_nl_datm_streams" || fail 'DATM v3 first-year input missing'
    grep -Fq "$DATM/CH-Aws_DATM_2024.nc" "$NEW/user_nl_datm_streams" || fail 'DATM v3 last-year input missing'
    ! grep -Fq 'datm_11_provisional_dynamic_zbot_v1' "$NEW/user_nl_datm_streams" || fail 'Old DATM v1 still referenced'
    ! grep -Fq 'datm_11_landrh21a_dynamic_zbot_v2' "$NEW/user_nl_datm_streams" || fail 'Old DATM v2 still referenced'
    grep -Fq 'CLM_USRDAT.UNSET:taxmode = cycle' "$NEW/user_nl_datm_streams" || fail 'Forcing not cycling'
    local sf
    sf="$(find '/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/subset_data' -name 'surfdata*.nc' -type f -print -quit)"
    [[ -s "$sf" ]] || fail 'CH-Aws surface file unavailable'
    grep -Fq "$(basename "$sf")" "$NEW/CaseDocs/lnd_in" || fail 'Wrong CH-Aws surface in CLM namelist'
    local output
    output="$(cd "$NEW" && ./preview_run)" || fail 'CIME preview_run failed'
    grep -Fq "$MPI $exe/cesm.exe" <<<"$output" || fail 'preview_run not using PMIx+srun'
    echo 'VERIFIED NEW CH-Aws: v3 forcing, FAST, 200 x 5yr = 1000yr, 1 CPU 8G, PMIx, no --exclusive'
}
preflight(){
    [[ -x "$OLD/xmlquery" && -s "$OLD/user_nl_clm" ]] || fail 'Old CH-Aws case missing'
    [[ "$(xval "$OLD" CASE)" == CH-Aws_FATES_SPINUP500_11P ]] || fail 'Old case identity wrong'
    grep -Eq "^[[:space:]]*calc_human_stress_indices[[:space:]]*=[[:space:]]*'FAST'" "$OLD/CaseDocs/lnd_in" || fail 'Old CH-Aws must have FAST restored'
    [[ -x "$EXREF/xmlquery" && "$(xval "$EXREF" BUILD_COMPLETE)" == TRUE ]] || fail 'GF-Guy executable not verified'
    [[ "$(xval "$EXREF" MPILIB)" != mpi-serial ]] || fail 'GF-Guy uses MPI serial'
    [[ -x "$CTSM/cime/scripts/create_clone" ]] || fail 'CTSM create_clone not found'
    [[ -s "$BUILDER" ]] || fail "Stage26 audit script not found: $BUILDER"
    python "$BUILDER" --verify >/dev/null || fail 'Stage26 independent 19/19 DATM v3 validation failed'
    no_new_jobs
    echo 'AUDIT OK: Stage26 verified, old case untouched, GF-Guy exe available'
}
prepare(){
    lock
    preflight
    [[ ! -e "$NEW" && ! -e "$RUNDIR" && ! -e "$ARCH" ]] || fail 'New CIME case or output already exists; will not overwrite'
    echo "Creating independent case $NAME"
    (cd "$CTSM/cime/scripts" && ./create_clone --case "$NEW" --clone "$OLD" --keepexe)
    [[ -x "$NEW/xmlquery" ]] || fail 'create_clone did not create CIME case'
    cd "$NEW"
    cp -p "$OLD/user_nl_clm" user_nl_clm
    python - <<'PY'
from pathlib import Path
import re
p=Path('user_nl_clm');s=p.read_text()
s=re.sub(r'(?im)^[ \t]*calc_human_stress_indices[ \t]*=.*(?:\n|$)','',s)
s+='\n! Stage27: keep existing FAST diagnostics with Stage25 humidity forcing\ncalc_human_stress_indices = \'FAST\'\n'
p.write_text(s)
PY
    # Recreate exactly Stage17 verified stream syntax with V3 file list.
    {
      printf 'CLM_USRDAT.UNSET:taxmode = cycle\n'
      printf 'CLM_USRDAT.UNSET:tintalgo = linear\n'
      printf 'CLM_USRDAT.UNSET:mapalgo = none\n'
      printf 'CLM_USRDAT.UNSET:meshfile = none\n\n'
      printf 'CLM_USRDAT.UNSET:year_first = 2006\nCLM_USRDAT.UNSET:year_last = 2024\nCLM_USRDAT.UNSET:year_align = 2006\n\n'
      printf 'CLM_USRDAT.UNSET:datafiles = \\\n'
      local y
      for ((y=2006;y<=2024;y++));do
        if ((y<2024));then printf '%s, \\\n' "$DATM/CH-Aws_DATM_${y}.nc";else printf '%s\n' "$DATM/CH-Aws_DATM_${y}.nc";fi
      done
      cat <<'DATM_STREAM'

CLM_USRDAT.UNSET:datavars = \
PRECTmms Faxa_precn, \
FSDS Faxa_swdn, \
ZBOT Sa_z, \
TBOT Sa_tbot, \
WIND Sa_wind, \
QBOT Sa_shum, \
PSRF Sa_pbot, \
FLDS Faxa_lwdn
DATM_STREAM
    } > user_nl_datm_streams
    touch user_nl_datm
    ./xmlchange DIN_LOC_ROOT="/iridisfs/scratch/ly3n24/CLM_FATES/inputdata"
    ./xmlchange RUN_TYPE=startup
    ./xmlchange CONTINUE_RUN=FALSE
    ./xmlchange RUN_STARTDATE=2006-01-01
    ./xmlchange CALENDAR=NO_LEAP
    ./xmlchange ATM_NCPL=48
    ./xmlchange CLM_CO2_TYPE=constant
    ./xmlchange CCSM_CO2_PPMV=381.15
    ./xmlchange STOP_OPTION=nyears
    ./xmlchange STOP_N=5
    ./xmlchange REST_OPTION=nyears
    ./xmlchange REST_N=5
    ./xmlchange RESUBMIT=199
    ./xmlchange DOUT_S=TRUE
    ./xmlchange DOUT_S_ROOT="$ARCH"
    ./xmlchange RUNDIR="$RUNDIR"
    ./xmlchange "MPI_RUN_COMMAND=$MPI"
    patch_batch
    if [[ -s .case.run ]];then ./case.setup --reset;else ./case.setup;fi
    # Set again after CIME regeneration to ensure the intended binding survived.
    ./xmlchange "MPI_RUN_COMMAND=$MPI"
    if [[ "$(xval "$NEW" BUILD_COMPLETE)" != TRUE ]];then ./xmlchange BUILD_COMPLETE=TRUE;fi
    ./preview_namelists
    ./check_input_data
    verify_new
    printf 'READY: %s. No model submitted yet.\n' "$NAME"
}
submit1000(){
    lock
    [[ "${ACK_PROVISIONAL_SCIENCE:-}" == YES ]] || fail 'Set ACK_PROVISIONAL_SCIENCE=YES to start exploratory 1000-year simulation'
    preflight
    verify_new
    [[ ! -e "$NEW/.STAGE27_SUBMIT1000_ATTEMPTED" ]] || fail 'Submission was already attempted; never submit twice automatically'
    ! grep -Eiq 'case.submit (starting|success)|model execution starting|case.run starting' "$NEW/CaseStatus" || fail 'This new case was already submitted. Never submit twice.'
    [[ ! -e "$RUNDIR" || -z "$(find "$RUNDIR" -type f \( -name '*log.*' -o -name '*.nc' -o -name 'rpointer.*' \) -print -quit)" ]] || fail 'Run directory has prior output'
    [[ ! -e "$ARCH" || -z "$(find "$ARCH" -type f \( -name '*.nc' -o -name '*log.*' \) -print -quit)" ]] || fail 'Archive has prior output'
    echo "SUBMIT 1000 model years: initial 2006-2010 plus 199 automatic CIME 5-year resubmissions"
    printf "%s\n" "$(date -Is)" > "$NEW/.STAGE27_SUBMIT1000_ATTEMPTED"
    (cd "$NEW" && ./case.submit)
    echo "INITIAL SEGMENT SUBMITTED: 200 x 5 years = 1000 model years; watch Slurm and CaseStatus"
    squeue -u ly3n24 -o '%.12i %.45j %.10T %.8C %R'
}
status(){
    if [[ -f "$NEW/CaseStatus" ]];then
        echo '=== NEW CH-Aws CaseStatus ==='
        tail -n 35 "$NEW/CaseStatus"
        echo '=== CIME config ==='
        (cd "$NEW" && ./xmlquery CASE,CONTINUE_RUN,STOP_N,REST_N,RESUBMIT,RUNDIR,DOUT_S_ROOT,MPI_RUN_COMMAND)
    else echo 'New Stage27 case not prepared';fi
    echo '=== NEW CH-Aws Slurm ==='
    squeue -h -u ly3n24 -o '%.12i %.45j %.10T %.8C %R' | grep "$NAME" || :
}
case "$MODE" in
 --audit)lock;preflight;;
 --prepare)prepare;;
 --submit1000)submit1000;;
 --status)status;;
esac
