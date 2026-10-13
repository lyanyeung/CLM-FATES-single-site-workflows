#!/usr/bin/env bash
# IRIDIS6: resume ONLY the eight unfinished FLUXNET 500-year CLM-FATES cases.
# 1 Slurm CPU, 8G RAM per run AND archive; no --exclusive.
# Keep existing compiled binary, scientific settings, data, and last archived restart.
# Commands: audit | prepare | submit SESSION_DIR | resume
# 2026-10-13, recovery after CIME locked env_batch.xml adjustment.
set -Eeuo pipefail
trap 'rc=$?; echo "ERROR at line $LINENO (exit $rc). Check this session log; do not rerun submit blindly." >&2' ERR

MODE="${1:-audit}"
[[ "$MODE" == audit || "$MODE" == prepare || "$MODE" == submit || "$MODE" == resume ]] || {
  echo "Usage: bash $0 audit|prepare|submit SESSION_DIR|resume" >&2; exit 2;
}
ROOT=/iridisfs/scratch/ly3n24/CLM_FATES
CASE_ROOT="$ROOT/cases"
OUT_ROOT=/scratch/ly3n24/CTSM_FATES_OUTPUTS
SITES=(CZ-BK1 IT-Ren FR-Hes FR-FBn DE-Hzd CH-Dav BE-Vie IT-Lav)
declare -A START=( [CZ-BK1]=2004 [IT-Ren]=1999 [FR-Hes]=1997 [FR-FBn]=2008 [DE-Hzd]=2010 [CH-Dav]=1997 [BE-Vie]=1996 [IT-Lav]=2003 )
declare -A MIN_CHECKPOINT=( [CZ-BK1]=2044 [IT-Ren]=2039 [FR-Hes]=2032 [FR-FBn]=2043 [DE-Hzd]=2045 [CH-Dav]=2032 [BE-Vie]=2031 [IT-Lav]=2038 )
declare -A EXPECT_CO2=( [CZ-BK1]=376.95 [IT-Ren]=367.80 [FR-Hes]=363.04 [FR-FBn]=385.02 [DE-Hzd]=388.75 [CH-Dav]=363.04 [BE-Vie]=361.93 [IT-Lav]=375.14 )
declare -A STAMP DONE LEFT RESUB
SESSION=""

fail() { printf 'STOP: %s\n' "$*" >&2; exit 1; }
val() { (cd "$1" && ./xmlquery "$2" --value) | tr -d '[:space:]'; }
latest() {
  local parent="$1"
  [[ -d "$parent" ]] || fail "Restart archive directory not found: $parent"
  find "$parent" -mindepth 1 -maxdepth 1 -type d -name '????-01-01-00000' -printf '%f\n' | LC_ALL=C sort | tail -1
}
sha() { sha256sum "$1" | awk '{print $1}'; }
casepath() { printf '%s/%s_FATES_SPINUP500' "$CASE_ROOT" "$1"; }

check_no_active_target_jobs() {
  local active name
  active=$(squeue -h -u "$USER" -o '%i|%j|%t') || fail 'Cannot query Slurm queue'
  for name in "${SITES[@]}"; do
    if printf '%s\n' "$active" | grep -Fq "${name}_FATES_SPINUP500"; then
      printf '%s\n' "$active" >&2
      fail "An eight-site spin-up Slurm job is running/queued (${name}). Do NOT change its case or submit again."
    fi
  done
}

check_site() {
  local site="$1" name="${1}_FATES_SPINUP500" case run arch date yr complete remaining
  local nrun narch expected_runs co2 mpilib
  case=$(casepath "$site")
  [[ -x "$case/xmlquery" && -x "$case/case.setup" && -x "$case/case.submit" ]] || fail "$site: CIME case missing/incomplete"
  [[ -f "$case/CaseStatus" && -f "$case/user_nl_clm" && -f "$case/user_nl_datm_streams" ]] || fail "$site: key case files missing"
  [[ "$(val "$case" CASE)" == "$name" ]] || fail "$site: CIME CASE mismatch"
  [[ "$(val "$case" RUN_STARTDATE)" == "${START[$site]}-01-01" ]] || fail "$site: unexpected original RUN_STARTDATE"
  [[ "$(val "$case" CONTINUE_RUN)" == TRUE ]] || fail "$site: CONTINUE_RUN must be TRUE"
  [[ "$(val "$case" RESUBMIT)" == 0 ]] || fail "$site: expected paused RESUBMIT=0 (do not rerun on active/resumed case)"
  [[ "$(val "$case" RUN_TYPE)" == startup ]] || fail "$site: unexpected RUN_TYPE"
  [[ "$(val "$case" CALENDAR)" == NO_LEAP && "$(val "$case" ATM_NCPL)" == 48 ]] || fail "$site: calendar/coupling differs"
  [[ "$(val "$case" CLM_CO2_TYPE)" == constant ]] || fail "$site: atmospheric CO2 is not constant"
  co2=$(val "$case" CCSM_CO2_PPMV)
  python3 - "$co2" "${EXPECT_CO2[$site]}" <<'PY'
import sys
assert abs(float(sys.argv[1]) - float(sys.argv[2])) < 0.011, f'CO2 differs: actual={sys.argv[1]}, expected={sys.argv[2]}'
PY
  [[ "$(val "$case" STOP_OPTION)" == nyears && "$(val "$case" STOP_N)" == 5 ]] || fail "$site: STOP must be 5 years"
  [[ "$(val "$case" REST_OPTION)" == nyears && "$(val "$case" REST_N)" == 5 ]] || fail "$site: REST must be 5 years"
  [[ "$(val "$case" DOUT_S)" == TRUE ]] || fail "$site: short-term archiving is disabled"
  for comp in ATM LND CPL; do
    [[ "$(val "$case" NTASKS_${comp})" == 1 && "$(val "$case" NTHRDS_${comp})" == 1 ]] || fail "$site: MPI/threads layout changed for ${comp}"
  done
  [[ "$(val "$case" BUILD_COMPLETE)" == TRUE ]] || fail "$site: BUILD_COMPLETE not TRUE"
  mpilib=$(val "$case" MPILIB)
  [[ "$mpilib" == openmpi ]] || fail "$site: unexpected MPILIB=$mpilib"
  local exe_root
  exe_root=$(val "$case" EXEROOT)
  [[ -x "$exe_root/cesm.exe" ]] || fail "$site: compiled executable is absent: $exe_root/cesm.exe"
  run=$(val "$case" RUNDIR)
  arch=$(val "$case" DOUT_S_ROOT)
  [[ "$run" == "$OUT_ROOT/$name/run" && -d "$run" ]] || fail "$site: unexpected RUNDIR ($run)"
  [[ "$arch" == "$OUT_ROOT/archive/$name" ]] || fail "$site: unexpected archive ($arch)"
  date=$(latest "$arch/rest")
  [[ "$date" =~ ^([0-9]{4})-01-01-00000$ ]] || fail "$site: no valid final archived restart date"
  yr="${BASH_REMATCH[1]}"
  (( 10#$yr >= MIN_CHECKPOINT[$site] )) || fail "$site: archived restart unexpectedly old ($date)"
  complete=$((10#$yr - START[$site]))
  (( complete > 0 && complete < 500 && complete % 5 == 0 )) || fail "$site: unexpected completed years ($complete)"
  remaining=$(((500 - complete)/5))
  local rest="$arch/rest/$date" ptr ref kind
  for comp in cpl atm lnd; do
    case "$comp" in
      cpl) kind=cpl.r ;;
      atm) kind=datm.r ;;
      lnd) kind=clm2.r ;;
    esac
    ptr="$rest/rpointer.$comp.$date"
    [[ -s "$ptr" ]] || fail "$site: missing archived pointer $ptr"
    ref=$(head -n 1 "$ptr" | tr -d '\r' | sed 's/[[:space:]]*$//')
    [[ "${ref#./}" == "$name.$kind.$date.nc" ]] || fail "$site: INVALID $ptr -> $ref"
    [[ -s "$rest/$ref" ]] || fail "$site: missing archived NetCDF $rest/$ref"
  done
  # When the interrupted segment completed model execution but NOT its archive,
  # do not silently overwrite it by resuming an older checkpoint.
  nrun=$(grep -c 'model execution success' "$case/CaseStatus" || true)
  narch=$(grep -c 'st_archive success' "$case/CaseStatus" || true)
  expected_runs=$((complete / 5))
  (( nrun == expected_runs )) || fail "$site: model successes=$nrun but archived checkpoint corresponds to $expected_runs segments; investigate before resuming"
  (( narch >= expected_runs )) || fail "$site: archive successes=$narch < $expected_runs; inspect archive history"
  STAMP[$site]="$date" DONE[$site]="$complete" LEFT[$site]="$remaining" RESUB[$site]="$((remaining-1))"
  printf '%-7s checkpoint=%s done=%3d/500y segments_left=%3d RESUBMIT=%d\n' "$site" "$date" "$complete" "$remaining" "${RESUB[$site]}"
}

preflight() {
  echo '===== VERIFY ALL 8 EXISTING CASES AND ARCHIVED RESTARTS ====='
  local site
  for site in "${SITES[@]}"; do check_site "$site"; done
}

check_test_completed() {
  local c
  c=$(casepath IT-Ren)
  [[ "${STAMP[IT-Ren]}" == 2044-01-01-00000 ]] || fail 'IT-Ren shared-node test (2039 -> 2044) has not yet produced the completed archived restart; come back after it is archived'
  grep -Fq 'case.run success 4143672' "$c/CaseStatus" || fail 'IT-Ren single-CPU test run job 4143672 did not log success'
  grep -Fq 'st_archive success 4143673' "$c/CaseStatus" || fail 'IT-Ren single-CPU test archive job 4143673 did not log success'
  echo 'IT-Ren single-CPU test run and archive confirmed. All eight cases may be prepared.'
}

backup_partial_run_histories() {
  local site="$1" run="$2" stamp="$3" backup="$4" name="${1}_FATES_SPINUP500"
  local year="${stamp:0:4}" file base histyear count=0
  # The interrupted job may have produced unarchived history files. Preserve
  # those before a replay can overwrite filenames with matching model dates.
  local data_backup="$OUT_ROOT/recovery_backups/$(basename "$SESSION")/$site"
  mkdir -p "$data_backup"
  echo "$data_backup" > "$backup/partial_run_output_backup_path.txt"
  shopt -s nullglob
  for file in "$run/$name".clm2.h*.nc; do
    base="${file##*/}"
    if [[ "$base" =~ \.h[^.]*\.([0-9]{4})- ]]; then
      histyear="${BASH_REMATCH[1]}"
      if (( 10#$histyear >= 10#$year )); then
        cp --reflink=auto -p "$file" "$data_backup/$base"
        ((count+=1))
      fi
    fi
  done
  shopt -u nullglob
  echo "$site: preserved $count unarchived history NetCDF(s) (if any)."
}

patch_batch_xml() {
  local file="$1"
  python3 - "$file" <<'PY'
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
p = Path(sys.argv[1]); s = p.read_text()
exclusive = r'(?m)^[ \t]*<directive>[ \t]*--exclusive[ \t]*</directive>[ \t]*\r?\n'
s, found = re.subn(exclusive, '', s)
if found not in (0, 2):
    raise SystemExit(f'STOP: expected exactly 0 or 2 exclusive lines, found {found}')
if '--exclusive' in s:
    raise SystemExit('STOP: an unrecognized --exclusive directive remains')
needle = '<directive>--cpus-per-task={{ thread_count }}</directive>'
if s.count(needle) != 1:
    raise SystemExit('STOP: cannot find unique --cpus-per-task directive')
mem = '<directive>--mem=8G</directive>'
all_mem = re.findall(r'<directive>\s*--mem(?:=|\s).*?</directive>', s)
if not all_mem:
    s = s.replace(needle, needle + '\n        ' + mem, 1)
elif len(all_mem) != 1 or all_mem[0] != mem:
    raise SystemExit(f'STOP: unexpected Slurm memory directives: {all_mem}')
ET.fromstring(s)
if p.read_text() != s:
    p.write_text(s)
    print('Modified env_batch.xml to 1 CPU / 8G / no exclusive.')
else:
    print('env_batch.xml already has correct resources; no rewrite.')
PY
}

validate_batch() {
  local site="$1" case="$2" f name="${1}_FATES_SPINUP500" key
  for f in .case.run case.st_archive; do
    [[ -s "$case/$f" ]] || return 1
    ! grep -q -- '--exclusive' "$case/$f" || return 1
    for key in '--cpus-per-task=1' '--mem=8G' '--nodes=1' '--ntasks-per-node=1'; do
      grep -Eq "^#SBATCH[[:space:]]+${key}[[:space:]]*$" "$case/$f" || return 1
    done
  done
  grep -Fq -- "--job-name=run.$name" "$case/.case.run" || return 1
  grep -Fq -- "--job-name=st_archive.$name" "$case/case.st_archive" || return 1
  return 0
}

prepare_site() {
  local site="$1" case name run arch stamp rest backup exe_root pre_sha mpilib
  name="${site}_FATES_SPINUP500"
  case=$(casepath "$site")
  run="$OUT_ROOT/$name/run"
  arch="$OUT_ROOT/archive/$name"
  stamp="${STAMP[$site]}"
  rest="$arch/rest/$stamp"
  backup="$SESSION/cases/$site"
  mkdir -p "$backup"
  cd "$case"
  echo "===== PREPARE $site (restart $stamp, RESUBMIT=${RESUB[$site]}) ====="
  for f in env_batch.xml env_run.xml env_build.xml env_mach_pes.xml env_case.xml env_workflow.xml env_archive.xml .case.run case.st_archive CaseStatus user_nl_clm user_nl_datm_streams; do
    [[ ! -f "$f" ]] || cp -p "$f" "$backup/$f"
  done
  [[ ! -d LockedFiles ]] || cp -a LockedFiles "$backup/LockedFiles"
  for c in cpl atm lnd; do
    [[ ! -f "$run/rpointer.$c" ]] || cp -p "$run/rpointer.$c" "$backup/rpointer.$c"
  done
  sha256sum user_nl_clm user_nl_datm_streams > "$backup/scientific_inputs.sha256"
  exe_root=$(val "$case" EXEROOT)
  mpilib=$(val "$case" MPILIB)
  [[ -x "$exe_root/cesm.exe" ]] || fail "$site: executable not found prior to CIME setup"

  backup_partial_run_histories "$site" "$run" "$stamp" "$backup"
  # From proven GF-Guy extension: copy an intact archived coordinated restart
  # into RUNDIR without deleting any existing output or history.
  rsync -a "$rest/" "$run/"
  local c ref wanted
  for c in cpl atm lnd; do
    wanted="$run/rpointer.$c.$stamp"
    [[ -s "$wanted" ]] || fail "$site: dated restart pointer not staged: $wanted"
    cp --remove-destination -p "$wanted" "$run/rpointer.$c"
    ref=$(head -n 1 "$run/rpointer.$c" | tr -d '\r' | sed 's/[[:space:]]*$//')
    [[ "${ref#./}" == "$name."*".$stamp.nc" && -s "$run/$ref" ]] || fail "$site: invalid staged $c restart $ref"
  done

  patch_batch_xml "$case/env_batch.xml"
  # Locked XML is part of the CIME-generated Slurm configuration. The tested
  # repair is case.setup --reset (NOT case.build, NOT a startup model reset).
  if ! validate_batch "$site" "$case"; then
    echo "$site: rebuilding CIME batch scripts with case.setup --reset"
    ./case.setup --reset 2>&1 | tee "$backup/case_setup_reset.log"
  else
    echo "$site: batch scripts already correct; no CIME setup reset needed"
  fi
  sha256sum -c "$backup/scientific_inputs.sha256" || fail "$site: scientific user_nl files changed"
  [[ "$(val "$case" CASE)" == "$name" && "$(val "$case" RUNDIR)" == "$run" && "$(val "$case" DOUT_S_ROOT)" == "$arch" ]] || fail "$site: case identity/path changed after setup"
  [[ "$(val "$case" CONTINUE_RUN)" == TRUE && "$(val "$case" RUN_TYPE)" == startup ]] || fail "$site: model continuation changed after setup"
  [[ "$(val "$case" STOP_N)" == 5 && "$(val "$case" REST_N)" == 5 ]] || fail "$site: run length changed after setup"
  [[ "$(val "$case" RUN_STARTDATE)" == "${START[$site]}-01-01" ]] || fail "$site: original model start changed after setup"
  [[ "$(val "$case" EXEROOT)" == "$exe_root" && -x "$exe_root/cesm.exe" && "$(val "$case" MPILIB)" == "$mpilib" ]] || fail "$site: reused executable or MPI library changed after setup"
  for c in ATM LND CPL; do
    [[ "$(val "$case" NTASKS_${c})" == 1 && "$(val "$case" NTHRDS_${c})" == 1 ]] || fail "$site: MPI/threads changed after setup"
  done
  if [[ "$(val "$case" BUILD_COMPLETE)" != TRUE ]]; then
    echo "$site: verifying the existing --keepexe executable and restoring CIME BUILD_COMPLETE=TRUE"
    [[ -x "$exe_root/cesm.exe" ]] || fail "$site: cannot restore build flag without cesm.exe"
    ./xmlchange BUILD_COMPLETE=TRUE
  fi
  [[ "$(val "$case" BUILD_COMPLETE)" == TRUE ]] || fail "$site: build flag remains FALSE"
  validate_batch "$site" "$case" || fail "$site: generated run/archive batch scripts have incorrect Slurm resources"
  [[ "$(val "$case" RESUBMIT)" == 0 ]] || fail "$site: premature RESUBMIT modification during preparation"
  # CIME's setup has already been used successfully for IT-Ren. Do not call
  # case.build; only check regenerated resources and keep original science.
  grep -E '^#SBATCH' .case.run > "$backup/generated_run_sbatch.txt"
  grep -E '^#SBATCH' case.st_archive > "$backup/generated_archive_sbatch.txt"
  sha256sum env_batch.xml user_nl_clm user_nl_datm_streams > "$backup/prepared_files.sha256"
  echo "$site: ready (1 core / 8G, ${LEFT[$site]} segments)"
}

prepare_all() {
  check_no_active_target_jobs
  preflight
  check_test_completed
  for cmd in flock rsync squeue sha256sum; do command -v "$cmd" >/dev/null || fail "Missing command: $cmd"; done
  exec 9>"$HOME/.fates_eight_resume.lock"
  flock -n 9 || fail 'Another eight-site recovery process is running'
  SESSION=$(mktemp -d "$HOME/fates_eight_shared_resume_$(date +%Y%m%d_%H%M%S)_XXXXXX")
  echo "SESSION=$SESSION"
  mkdir -p "$SESSION/cases"
  printf 'site\tcheckpoint\tcompleted_years\tremaining_segments\tresubmit\tcase_status_sha256\n' > "$SESSION/prepared_manifest.tsv"
  local site
  for site in "${SITES[@]}"; do
    mkdir -p "$SESSION/cases/$site"
    prepare_site "$site" 2>&1 | tee "$SESSION/cases/$site/prepare.log"
  done
  # Set RESUBMIT only AFTER all sites have passed batch, restart and scientific
  # checks. If setup fails early, all paused cases retain RESUBMIT=0.
  echo '===== ACTIVATE FUTURE AUTO-RESUBMIT COUNTS ====='
  for site in "${SITES[@]}"; do
    (cd "$(casepath "$site")" && ./xmlchange "RESUBMIT=${RESUB[$site]}")
    [[ "$(val "$(casepath "$site")" RESUBMIT)" == "${RESUB[$site]}" ]] || fail "$site: RESUBMIT update failed"
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$site" "${STAMP[$site]}" "${DONE[$site]}" "${LEFT[$site]}" "${RESUB[$site]}" \
      "$(sha "$(casepath "$site")/CaseStatus")" >> "$SESSION/prepared_manifest.tsv"
  done
  touch "$SESSION/PREPARE_COMPLETE"
  echo "All eight cases prepared. No jobs submitted yet. SESSION=$SESSION"
  echo "Manifest: $SESSION/prepared_manifest.tsv"
}

submit_all() {
  local session_arg="$1" site stamp completed left resubmit expected_sha case current_sha
  [[ -n "$session_arg" && -d "$session_arg" && -f "$session_arg/PREPARE_COMPLETE" ]] || fail 'Supply a complete session directory printed by prepare mode'
  [[ ! -e "$session_arg/SUBMIT_STARTED" ]] || fail 'This session has already attempted submission; inspect Slurm/CaseStatus, do not repeat'
  check_no_active_target_jobs
  [[ "$(wc -l < "$session_arg/prepared_manifest.tsv")" == 9 ]] || fail 'Manifest does not contain all eight cases'
  # Validate *every* case before submitting *any* job.
  while IFS=$'\t' read -r site stamp completed left resubmit expected_sha; do
    [[ "$site" == site ]] && continue
    case=$(casepath "$site")
    [[ -d "$case" ]] || fail "$site: missing case"
    [[ "$(val "$case" RESUBMIT)" == "$resubmit" ]] || fail "$site: RESUBMIT changed since preparation"
    [[ "$(val "$case" CONTINUE_RUN)" == TRUE && "$(val "$case" BUILD_COMPLETE)" == TRUE ]] || fail "$site: CIME flags changed"
    [[ "$(latest "$OUT_ROOT/archive/${site}_FATES_SPINUP500/rest")" == "$stamp" ]] || fail "$site: archived restart has changed since preparation"
    validate_batch "$site" "$case" || fail "$site: generated resources no longer correct"
    current_sha=$(sha "$case/CaseStatus")
    [[ "$current_sha" == "$expected_sha" ]] || fail "$site: CaseStatus changed since preparation; possible submission or execution"
    ( cd "$case" && sha256sum -c "$session_arg/cases/$site/prepared_files.sha256" ) >/dev/null || fail "$site: scientific/batch XML changed since prepare"
  done < "$session_arg/prepared_manifest.tsv"
  touch "$session_arg/SUBMIT_STARTED"
  echo '===== SUBMIT EIGHT 1-CPU 8G CONTINUATIONS ====='
  while IFS=$'\t' read -r site stamp completed left resubmit expected_sha; do
    [[ "$site" == site ]] && continue
    echo "SUBMIT $site from $stamp (remaining segments=$left, RESUBMIT=$resubmit)"
    ( cd "$(casepath "$site")" && ./case.submit ) 2>&1 | tee "$session_arg/cases/$site/submission.log"
    printf '%s\t%s\n' "$site" "$(date -Is)" >> "$session_arg/submitted_sites.tsv"
  done < "$session_arg/prepared_manifest.tsv"
  echo '===== SLURM QUEUE ====='
  squeue -u "$USER" -o '%.12i %.36j %.10T %.8C %R'
  echo "BACKUP + MANIFEST: $session_arg"
}

case "$MODE" in
  audit)
    preflight
    echo 'Audit done; no files changed and no jobs submitted.'
    ;;
  prepare)
    prepare_all
    ;;
  submit)
    [[ $# == 2 ]] || fail 'Usage: script submit /home/ly3n24/fates_eight_shared_resume_...'
    submit_all "$2"
    ;;
  resume)
    prepare_all
    submit_all "$SESSION"
    ;;
esac
