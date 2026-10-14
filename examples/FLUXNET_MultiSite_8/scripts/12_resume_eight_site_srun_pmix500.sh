#!/usr/bin/env bash
# IRIDIS6 / CLM-FATES: checkpoint-safe 8-site continuation using Slurm srun PMIx.
# 2026-10-14. Runs on IRIDIS6, NOT on WSL.
# Modes: audit (read-only); prepare (backup/configure only); submit SESSION (once); status (read-only).
# Nothing is submitted by 'audit' or 'prepare'. The IT-Ren single-segment 2044->2049
# test must be COMPLETED AND ARCHIVED before 'prepare'.
set -Eeuo pipefail
trap 'rc=$?; echo "ERROR line $LINENO (exit $rc). No automatic retry; inspect logs and backups." >&2' ERR

MODE="${1:-audit}"
[[ "$MODE" =~ ^(audit|prepare|submit|status)$ ]] || {
  echo "Usage: bash $0 audit|prepare|submit SESSION_DIR|status" >&2; exit 2;
}

CASE_ROOT=/iridisfs/scratch/ly3n24/CLM_FATES/cases
OUT_ROOT=/scratch/ly3n24/CTSM_FATES_OUTPUTS
SITES=(CZ-BK1 IT-Ren FR-Hes FR-FBn DE-Hzd CH-Dav BE-Vie IT-Lav)
declare -A START=( [CZ-BK1]=2004 [IT-Ren]=1999 [FR-Hes]=1997 [FR-FBn]=2008 [DE-Hzd]=2010 [CH-Dav]=1997 [BE-Vie]=1996 [IT-Lav]=2003 )
declare -A MIN_RESTART=( [CZ-BK1]=2044 [IT-Ren]=2049 [FR-Hes]=2032 [FR-FBn]=2043 [DE-Hzd]=2045 [CH-Dav]=2032 [BE-Vie]=2031 [IT-Lav]=2038 )
declare -A CO2=( [CZ-BK1]=376.95 [IT-Ren]=367.80 [FR-Hes]=363.04 [FR-FBn]=385.02 [DE-Hzd]=388.75 [CH-Dav]=363.04 [BE-Vie]=361.93 [IT-Lav]=375.14 )
declare -A STAMP=() DONE=() LEFT=() RESUB=()
MPI_CMD='srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores'
SESSION=''

fail(){ printf 'STOP: %s\n' "$*" >&2; exit 1; }
casepath(){ printf '%s/%s_FATES_SPINUP500' "$CASE_ROOT" "$1"; }
compact(){ (cd "$1" && ./xmlquery "$2" --value) | tr -d '[:space:]'; }
rawvalue(){ (cd "$1" && ./xmlquery "$2" --value) | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'; }
latest(){
  [[ -d "$1" ]] || fail "Missing archive rest directory: $1"
  find "$1" -mindepth 1 -maxdepth 1 -type d -name '????-01-01-00000' -printf '%f\n' | LC_ALL=C sort | tail -1
}
sha(){ sha256sum "$1" | awk '{print $1}'; }
pointer_ref(){
  # Some CIME rpointer files use long space-padded fixed-length strings.
  sed -n '1{s/^[[:space:]]*//;s/[[:space:]]*$//;p;}' "$1" | sed 's@^\./@@'
}
no_active_jobs(){
  local queue site
  queue=$(squeue -h -u "$USER" -o '%i|%j|%t') || fail 'Cannot inspect Slurm queue'
  for site in "${SITES[@]}"; do
    if grep -Fq "${site}_FATES_SPINUP500" <<<"$queue"; then
      printf '%s\n' "$queue" >&2
      fail "An eight-site run/archive job still exists for $site. No changes allowed."
    fi
  done
}
check_resources(){
  local site="$1" case_dir="$2" f item name="${1}_FATES_SPINUP500"
  for f in .case.run case.st_archive; do
    [[ -s "$case_dir/$f" ]] || return 1
    if grep -q -- '--exclusive' "$case_dir/$f"; then return 1; fi
    for item in '--nodes=1' '--ntasks-per-node=1' '--cpus-per-task=1' '--mem=8G'; do
      grep -Eq "^#SBATCH[[:space:]]+${item}[[:space:]]*$" "$case_dir/$f" || return 1
    done
  done
  grep -Fq -- "--job-name=run.$name" "$case_dir/.case.run" || return 1
  grep -Fq -- "--job-name=st_archive.$name" "$case_dir/case.st_archive" || return 1
  return 0
}
check_case(){
  local site="$1" name="${1}_FATES_SPINUP500" c run archive stamp year complete left
  local comp type ptr ref nrun narch exe
  c=$(casepath "$site")
  [[ -x "$c/xmlquery" && -x "$c/case.submit" && -x "$c/preview_run" ]] || fail "$site: missing CIME executables"
  [[ -s "$c/CaseStatus" && -s "$c/user_nl_clm" && -s "$c/user_nl_datm_streams" ]] || fail "$site: missing case files"
  [[ "$(compact "$c" CASE)" == "$name" ]] || fail "$site: CASE identity mismatch"
  [[ "$(compact "$c" RUN_STARTDATE)" == "${START[$site]}-01-01" ]] || fail "$site: original RUN_STARTDATE changed"
  [[ "$(compact "$c" RUN_TYPE)" == startup && "$(compact "$c" CONTINUE_RUN)" == TRUE ]] || fail "$site: not continuing original startup run"
  [[ "$(compact "$c" STOP_OPTION)" == nyears && "$(compact "$c" STOP_N)" == 5 ]] || fail "$site: 5-year STOP changed"
  [[ "$(compact "$c" REST_OPTION)" == nyears && "$(compact "$c" REST_N)" == 5 ]] || fail "$site: 5-year restart interval changed"
  [[ "$(compact "$c" CALENDAR)" == NO_LEAP && "$(compact "$c" ATM_NCPL)" == 48 ]] || fail "$site: calendar/time-step changed"
  [[ "$(compact "$c" MPILIB)" == openmpi && "$(compact "$c" BUILD_COMPLETE)" == TRUE ]] || fail "$site: MPI/build flags changed"
  [[ "$(compact "$c" DOUT_S)" == TRUE ]] || fail "$site: short-term archiving is disabled"
  [[ "$(compact "$c" CLM_CO2_TYPE)" == constant ]] || fail "$site: CO2 setting changed"
  python3 - "$(compact "$c" CCSM_CO2_PPMV)" "${CO2[$site]}" <<'PY'
import sys
assert abs(float(sys.argv[1])-float(sys.argv[2])) < 0.011, 'CO2 concentration changed'
PY
  for comp in ATM LND CPL; do
    [[ "$(compact "$c" NTASKS_${comp})" == 1 && "$(compact "$c" NTHRDS_${comp})" == 1 ]] || fail "$site: MPI/thread layout changed: $comp"
  done
  exe=$(compact "$c" EXEROOT)
  [[ -x "$exe/cesm.exe" ]] || fail "$site: missing compiled $exe/cesm.exe"
  run="$OUT_ROOT/$name/run"
  archive="$OUT_ROOT/archive/$name"
  [[ "$(compact "$c" RUNDIR)" == "$run" && -d "$run" ]] || fail "$site: unexpected RUNDIR"
  [[ "$(compact "$c" DOUT_S_ROOT)" == "$archive" ]] || fail "$site: unexpected archive root"
  check_resources "$site" "$c" || fail "$site: Slurm resource settings differ from 1 CPU / 8G / nonexclusive"
  stamp=$(latest "$archive/rest")
  [[ "$stamp" =~ ^([0-9]{4})-01-01-00000$ ]] || fail "$site: no archived 5-year checkpoint"
  year=$((10#${BASH_REMATCH[1]}))
  (( year >= MIN_RESTART[$site] )) || fail "$site: archived checkpoint older than expected ($stamp)"
  complete=$((year - START[$site]))
  (( complete > 0 && complete < 500 && complete % 5 == 0 )) || fail "$site: invalid already-completed years: $complete"
  left=$(((500 - complete) / 5))
  for comp in cpl atm lnd; do
    case "$comp" in cpl) type=cpl.r ;; atm) type=datm.r ;; lnd) type=clm2.r ;; esac
    ptr="$archive/rest/$stamp/rpointer.$comp.$stamp"
    [[ -s "$ptr" ]] || fail "$site: missing rpointer $ptr"
    ref=$(pointer_ref "$ptr")
    [[ "$ref" == "$name.$type.$stamp.nc" ]] || fail "$site: unexpected $comp rpointer content [$ref]"
    [[ -s "$archive/rest/$stamp/$ref" ]] || fail "$site: missing referenced NetCDF $ref"
  done
  nrun=$(grep -c 'model execution success' "$c/CaseStatus" || true)
  narch=$(grep -c 'st_archive success' "$c/CaseStatus" || true)
  (( nrun == complete / 5 )) || fail "$site: model successes=$nrun but restart shows $((complete/5)) complete segments"
  (( narch >= complete / 5 )) || fail "$site: insufficient successful archives ($narch)"
  STAMP[$site]="$stamp" DONE[$site]="$complete" LEFT[$site]="$left" RESUB[$site]="$((left-1))"
  printf '%-7s archived=%s done=%3d/500y left=%3d segments RESUBMIT=%d\n' "$site" "$stamp" "$complete" "$left" "${RESUB[$site]}"
}
preflight(){
  no_active_jobs
  echo '===== ALL EIGHT STATION/SCIENCE/RESTART CHECKS ====='
  local s
  for s in "${SITES[@]}"; do check_case "$s"; done
  # IT-Ren must have completed the dedicated srun 2044->2049 trial,
  # including successful archive, before resuming the full chain.
  [[ "${STAMP[IT-Ren]}" == 2049-01-01-00000 ]] || fail 'IT-Ren 2044->2049 srun trial is not fully archived; do not batch-submit yet'
  echo 'Preflight passed. No files changed.'
}
backup_site(){
  local site="$1" c run backup file base year count=0
  c=$(casepath "$site"); run="$OUT_ROOT/${site}_FATES_SPINUP500/run"
  backup="$SESSION/cases/$site"
  mkdir -p "$backup/partial_history"
  for file in env_batch.xml env_run.xml env_build.xml env_mach_pes.xml env_mach_specific.xml env_case.xml env_workflow.xml env_archive.xml .case.run case.st_archive CaseStatus user_nl_clm user_nl_datm_streams; do
    [[ ! -f "$c/$file" ]] || cp -p "$c/$file" "$backup/$file"
  done
  [[ ! -d "$c/LockedFiles" ]] || cp -a "$c/LockedFiles" "$backup/LockedFiles"
  for file in "$run"/rpointer.cpl "$run"/rpointer.atm "$run"/rpointer.lnd; do
    [[ ! -f "$file" ]] || cp -p "$file" "$backup/"
  done
  # Preserve unarchived output from the interrupted 5-year segment.
  # Move to a distinct backup (rather than leave stale history for replay).
  shopt -s nullglob
  for file in "$run/${site}_FATES_SPINUP500".clm2.h*.nc; do
    base=${file##*/}
    if [[ "$base" =~ \.h[^.]*\.([0-9]{4})- ]]; then
      year=$((10#${BASH_REMATCH[1]}))
      if (( year >= 10#${STAMP[$site]:0:4} )); then
        [[ ! -e "$backup/partial_history/$base" ]] || fail "$site: backup name collision $base"
        mv -- "$file" "$backup/partial_history/$base"
        count=$((count + 1))
      fi
    fi
  done
  shopt -u nullglob
  echo "$site: backed up original case config and moved $count unarchived history files to $backup/partial_history"
}
prepare_site(){
  local site="$1" c run rest archive stamp comp ref exe preview
  c=$(casepath "$site")
  run="$OUT_ROOT/${site}_FATES_SPINUP500/run"
  archive="$OUT_ROOT/archive/${site}_FATES_SPINUP500"
  stamp="${STAMP[$site]}"
  rest="$archive/rest/$stamp"
  exe=$(compact "$c" EXEROOT)
  echo "===== CONFIGURE $site from $stamp ====="
  backup_site "$site"
  (cd "$c" && ./xmlchange RESUBMIT=0)
  rsync -a "$rest/" "$run/"
  for comp in cpl atm lnd; do
    [[ -s "$run/rpointer.$comp.$stamp" ]] || fail "$site: archived dated pointer not staged"
    cp --remove-destination -p "$run/rpointer.$comp.$stamp" "$run/rpointer.$comp"
    ref=$(pointer_ref "$run/rpointer.$comp")
    [[ -s "$run/$ref" ]] || fail "$site: missing staged restart $ref"
  done
  (cd "$c" && ./xmlchange "MPI_RUN_COMMAND=$MPI_CMD")
  [[ "$(rawvalue "$c" MPI_RUN_COMMAND)" == "$MPI_CMD" ]] || fail "$site: MPI_RUN_COMMAND override mismatch"
  [[ "$(compact "$c" CONTINUE_RUN)" == TRUE && "$(compact "$c" BUILD_COMPLETE)" == TRUE ]] || fail "$site: CIME settings changed unexpectedly"
  (cd "$c" && sha256sum user_nl_clm user_nl_datm_streams env_batch.xml) > "$SESSION/cases/$site/inputs.sha256"
  preview="$SESSION/cases/$site/preview_run.txt"
  (cd "$c" && ./preview_run) > "$preview" 2>&1 || fail "$site: preview_run failed (see $preview)"
  grep -Fq "$MPI_CMD $exe/cesm.exe" "$preview" || fail "$site: preview_run did not show new srun MPI launch"
  [[ "$(compact "$c" RESUBMIT)" == 0 ]] || fail "$site: premature automatic resubmit"
  echo "$site: srun PMIx configured and 5-year restart re-staged; no job submitted"
}
prepare_all(){
  for cmd in rsync squeue flock sha256sum python3; do command -v "$cmd" >/dev/null || fail "Missing executable: $cmd"; done
  exec 9>"$HOME/.fates_eight_srun_prepare.lock"
  flock -n 9 || fail 'Another batch recovery process holds the lock'
  preflight
  SESSION="$OUT_ROOT/recovery_backups/fates_eight_srun_$(date +%Y%m%d_%H%M%S)_$$"
  mkdir -p "$SESSION/cases"
  echo "SESSION=$SESSION"
  echo -e 'site\tcheckpoint\tcompleted_years\tremaining_segments\tresubmit\tcase_status_sha256' > "$SESSION/manifest.tsv"
  local site c
  for site in "${SITES[@]}"; do
    mkdir -p "$SESSION/cases/$site"
    prepare_site "$site" 2>&1 | tee "$SESSION/cases/$site/prepare.log"
  done
  # Activate automatic resubmission ONLY after all eight cases pass.
  for site in "${SITES[@]}"; do
    c=$(casepath "$site")
    (cd "$c" && ./xmlchange "RESUBMIT=${RESUB[$site]}")
    [[ "$(compact "$c" RESUBMIT)" == "${RESUB[$site]}" ]] || fail "$site: RESUBMIT did not persist"
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$site" "${STAMP[$site]}" "${DONE[$site]}" "${LEFT[$site]}" "${RESUB[$site]}" "$(sha "$c/CaseStatus")" >> "$SESSION/manifest.tsv"
  done
  touch "$SESSION/PREPARED"
  echo '===== ALL EIGHT CASES PREPARED; NOTHING SUBMITTED ====='
  echo "SESSION=$SESSION"
  echo "Next, run: bash $0 submit '$SESSION'"
}
submit_all(){
  local sess="$1" site stamp complete left resub status_hash c cur
  [[ -d "$sess" && -f "$sess/PREPARED" && -s "$sess/manifest.tsv" ]] || fail 'Invalid prepare session'
  [[ ! -e "$sess/SUBMIT_STARTED" ]] || fail 'This session already attempted submission. Do not double-submit.'
  [[ "$(wc -l < "$sess/manifest.tsv")" == 9 ]] || fail 'Expected exactly 8 prepared sites'
  exec 9>"$HOME/.fates_eight_srun_prepare.lock"
  flock -n 9 || fail 'Another batch recovery process holds the lock'
  no_active_jobs
  # Validate everything before submitting even the first job.
  while IFS=$'\t' read -r site stamp complete left resub status_hash; do
    [[ "$site" == site ]] && continue
    [[ " ${SITES[*]} " == *" $site "* ]] || fail "Unexpected site $site in manifest"
    c=$(casepath "$site")
    [[ "$(compact "$c" RESUBMIT)" == "$resub" ]] || fail "$site: RESUBMIT changed since prepare"
    [[ "$(compact "$c" CONTINUE_RUN)" == TRUE && "$(compact "$c" BUILD_COMPLETE)" == TRUE ]] || fail "$site: continuation/build flags changed"
    [[ "$(latest "$OUT_ROOT/archive/${site}_FATES_SPINUP500/rest")" == "$stamp" ]] || fail "$site: archive changed since prepare"
    [[ "$(rawvalue "$c" MPI_RUN_COMMAND)" == "$MPI_CMD" ]] || fail "$site: MPI command changed since prepare"
    check_resources "$site" "$c" || fail "$site: Slurm CPU/memory configuration changed"
    [[ "$(sha "$c/CaseStatus")" == "$status_hash" ]] || fail "$site: CaseStatus changed since prepare"
    (cd "$c" && sha256sum -c "$sess/cases/$site/inputs.sha256") >/dev/null || fail "$site: scientific input / Slurm batch settings changed"
    cur="$(compact "$c" EXEROOT)"
    [[ -x "$cur/cesm.exe" ]] || fail "$site: compiled executable now missing"
  done < "$sess/manifest.tsv"
  touch "$sess/SUBMIT_STARTED"  # irreversible submit guard, even on partial failure
  echo '===== SUBMIT EIGHT CASES (ONE 5-YEAR SEGMENT + CIME AUTO-RESUBMITS) ====='
  while IFS=$'\t' read -r site stamp complete left resub status_hash; do
    [[ "$site" == site ]] && continue
    echo "SUBMIT $site: $complete/500 completed; $left remaining 5-year segments; RESUBMIT=$resub"
    (cd "$(casepath "$site")" && ./case.submit) 2>&1 | tee "$sess/cases/$site/submit.log"
    printf '%s\t%s\n' "$site" "$(date -Is)" >> "$sess/submitted.tsv"
  done < "$sess/manifest.tsv"
  squeue -u "$USER" -o '%.12i %.36j %.10T %.8C %R'
  echo "Session/backup: $sess"
}
show_status(){
  squeue -u "$USER" -o '%.12i %.36j %.10T %.8C %R' || true
  echo '===== CURRENT ARCHIVED PROGRESS ====='
  local site c stamp y
  for site in "${SITES[@]}"; do
    c=$(casepath "$site")
    stamp=$(latest "$OUT_ROOT/archive/${site}_FATES_SPINUP500/rest")
    y=${stamp:0:4}
    printf '%-7s archived=%s completed=%3d/500y resubmit=%s MPI=%s\n' \
      "$site" "$stamp" "$((10#$y - START[$site]))" "$(compact "$c" RESUBMIT)" "$(rawvalue "$c" MPI_RUN_COMMAND)"
  done
}
case "$MODE" in
  audit) preflight ;;
  prepare) prepare_all ;;
  submit) [[ $# == 2 ]] || fail 'Usage: script submit SESSION_DIR'; submit_all "$2" ;;
  status) show_status ;;
esac