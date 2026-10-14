#!/usr/bin/env bash
# IRIDIS6 / CTSM-FATES: safely extend the six EXISTING, fully archived
# 500-model-year spin-ups to 1000 years (500 additional model years).
# Six cases only; the eight active FLUXNET_MultiSite_8 cases are out of scope.
# Usage: [EXCLUDE_NODES=red6129] bash SCRIPT audit|prepare|submit SESSION|status
# audit/status are read-only. prepare changes six idle cases but submits NO jobs.
# submit requires the complete, unchanged prepared session, and runs ONCE.
set -Eeuo pipefail
trap 'rc=$?; echo "ERROR line $LINENO (exit $rc). STOP; inspect CaseStatus and backups before retrying." >&2' ERR

MODE="${1:-audit}"
[[ "$MODE" =~ ^(audit|prepare|submit|status)$ ]] || { echo "Usage: $0 audit|prepare|submit SESSION_DIR|status" >&2; exit 2; }
[[ "${USER:-}" == ly3n24 ]] || { echo 'STOP: this script is specific to IRIDIS user ly3n24' >&2; exit 2; }

CASE_ROOT=/iridisfs/scratch/ly3n24/CLM_FATES/cases
OUT=/scratch/ly3n24/CTSM_FATES_OUTPUTS
SESSION_ROOT="$OUT/recovery_backups"
SITES=( DE-Hai RU-Fyo DE-Tha DK-Sor NL-Loo IL-Yat )
declare -A FIRST=( [DE-Hai]=2000 [RU-Fyo]=1998 [DE-Tha]=1996 [DK-Sor]=1996 [NL-Loo]=1997 [IL-Yat]=2000 )
declare -A LAST=( [DE-Hai]=2025 [RU-Fyo]=2025 [DE-Tha]=2025 [DK-Sor]=2024 [NL-Loo]=2025 [IL-Yat]=2024 )
declare -A CO2=( [DE-Hai]=368.96 [RU-Fyo]=365.70 [DE-Tha]=361.93 [DK-Sor]=361.93 [NL-Loo]=363.04 [IL-Yat]=368.96 )
declare -A STAMP DONE LEFT RESUB
MPI_CMD='srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores'
EXCLUDE_NODES="${EXCLUDE_NODES:-}"
[[ -z "$EXCLUDE_NODES" || "$EXCLUDE_NODES" =~ ^[A-Za-z0-9,-]+$ ]] || { echo 'Invalid EXCLUDE_NODES; example: red6129' >&2; exit 2; }
SESSION=""

fail() { echo "STOP: $*" >&2; exit 1; }
casepath() { printf '%s/%s_FATES_SPINUP500' "$CASE_ROOT" "$1"; }
val() { (cd "$1" && ./xmlquery "$2" --value) | tr -d '[:space:]'; }
rawval() { (cd "$1" && ./xmlquery "$2" --value) | tr -d '\r\n'; }
latest() {
    [[ -d "$1" ]] || fail "Missing archived rest directory: $1"
    find "$1" -mindepth 1 -maxdepth 1 -type d -name '????-01-01-00000' -printf '%f\n' | LC_ALL=C sort | tail -1
}
sha() { sha256sum "$1" | awk '{print $1}'; }

no_six_jobs() {
    local queue site
    queue=$(squeue -h -u "$USER" -o '%i|%j|%t') || fail 'Unable to check Slurm queue'
    for site in "${SITES[@]}"; do
        if printf '%s\n' "$queue" | grep -Fq "${site}_FATES_SPINUP500"; then
            printf '%s\n' "$queue" >&2
            fail "$site has queued/running jobs: do not touch its CIME case"
        fi
    done
}

pointer_ref() {
    # Normalize trailing Fortran padding and './' prefix; never silently
    # accept an unexpected component, site or checkpoint filename.
    local file="$1" name="$2" kind="$3" stamp="$4" ref
    [[ -s "$file" ]] || fail "Missing pointer $file"
    ref=$(head -n 1 "$file" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    ref="${ref#./}"
    [[ "$ref" == "$name.$kind.$stamp.nc" ]] || fail "Bad $file -> <$ref>"
    printf '%s' "$ref"
}

check_site() {
    local site="$1" name="${1}_FATES_SPINUP500" case run arch stamp year done remaining
    local exe co2val kind comp ref ptr nhist nr na last_sub last_arc
    case=$(casepath "$site"); run="$OUT/$name/run"; arch="$OUT/archive/$name"
    [[ -x "$case/xmlquery" && -x "$case/case.submit" && -x "$case/case.setup" ]] || fail "$site missing CIME case"
    [[ -s "$case/CaseStatus" && -s "$case/user_nl_clm" && -s "$case/user_nl_datm_streams" ]] || fail "$site missing case inputs"
    [[ "$(val "$case" CASE)" == "$name" && "$(val "$case" RUN_STARTDATE)" == "${FIRST[$site]}-01-01" ]] || fail "$site case identity/start differs"
    [[ "$(val "$case" RUN_TYPE)" == startup && "$(val "$case" CONTINUE_RUN)" == TRUE ]] || fail "$site is not a continuation of original startup spin-up"
    [[ "$(val "$case" CALENDAR)" == NO_LEAP && "$(val "$case" ATM_NCPL)" == 48 ]] || fail "$site calendar or atmosphere coupling differs"
    [[ "$(val "$case" CLM_CO2_TYPE)" == constant ]] || fail "$site CO2 is not constant"
    co2val=$(val "$case" CCSM_CO2_PPMV)
    python3 - "$site" "$co2val" "${CO2[$site]}" <<'PY'
import sys
site, got, expected=sys.argv[1],float(sys.argv[2]),float(sys.argv[3])
if abs(got-expected)>0.011: raise SystemExit(f"STOP {site}: CO2 differs ({got} vs {expected})")
PY
    [[ "$(val "$case" STOP_OPTION)" == nyears && "$(val "$case" STOP_N)" == 5 ]] || fail "$site STOP must be nyears/5"
    [[ "$(val "$case" REST_OPTION)" == nyears && "$(val "$case" REST_N)" == 5 ]] || fail "$site REST must be nyears/5"
    [[ "$(val "$case" DOUT_S)" == TRUE && "$(val "$case" MPILIB)" == openmpi ]] || fail "$site archive/MPI settings differ"
    [[ "$(val "$case" BUILD_COMPLETE)" == TRUE ]] || fail "$site BUILD_COMPLETE not TRUE"
    [[ "$(val "$case" RESUBMIT)" == 0 ]] || fail "$site RESUBMIT is not zero; investigate past run/submission first"
    [[ "$(val "$case" RUNDIR)" == "$run" && "$(val "$case" DOUT_S_ROOT)" == "$arch" ]] || fail "$site output paths differ"
    [[ -d "$run" ]] || fail "$site run directory missing"
    exe=$(val "$case" EXEROOT)
    [[ "$exe" == "$OUT/GF-Guy_FATES_SURF2000_CO2405_1PT/bld" && -x "$exe/cesm.exe" ]] || fail "$site compiled executable differs/missing"
    for comp in ATM LND CPL; do
        [[ "$(val "$case" NTASKS_${comp})" == 1 && "$(val "$case" NTHRDS_${comp})" == 1 ]] || fail "$site MPI/threads mismatch for $comp"
    done
    for comp in first last align; do
        local exp
        case "$comp" in first|align) exp="${FIRST[$site]}";; last) exp="${LAST[$site]}";; esac
        grep -Eq "^CLM_USRDAT\.UNSET:year_${comp}[[:space:]]*=[[:space:]]*${exp}[[:space:]]*$" "$case/user_nl_datm_streams" || fail "$site DATM year_${comp} mismatch"
    done
    grep -Eq '^CLM_USRDAT\.UNSET:taxmode[[:space:]]*=[[:space:]]*cycle[[:space:]]*$' "$case/user_nl_datm_streams" || fail "$site DATM not cycle"
    grep -Fq "${site}_DATM_${FIRST[$site]}.nc" "$case/user_nl_datm_streams" || fail "$site first forcing file absent"
    grep -Fq "${site}_DATM_${LAST[$site]}.nc" "$case/user_nl_datm_streams" || fail "$site last forcing file absent"

    stamp=$(latest "$arch/rest")
    [[ "$stamp" =~ ^([0-9]{4})-01-01-00000$ ]] || fail "$site cannot locate full archived restart"
    year="${BASH_REMATCH[1]}"; done=$((10#$year - FIRST[$site]))
    (( done >= 500 && done <= 1000 && done % 5 == 0 )) || fail "$site archived years=$done; expected 500 to 1000 in 5-year steps"
    [[ "$done" -lt 1000 ]] || fail "$site already reached 1000; do not resubmit"
    remaining=$(((1000 - done) / 5))
    for comp in cpl atm lnd; do
        case "$comp" in cpl) kind=cpl.r;; atm) kind=datm.r;; lnd) kind=clm2.r;; esac
        ptr="$arch/rest/$stamp/rpointer.$comp.$stamp"
        ref=$(pointer_ref "$ptr" "$name" "$kind" "$stamp")
        [[ -s "$arch/rest/$stamp/$ref" ]] || fail "$site missing archived $ref"
    done
    [[ -d "$arch/lnd/hist" ]] || fail "$site archive history directory missing"
    nhist=$(find "$arch/lnd/hist" -maxdepth 1 -type f -name "$name.clm2.h0a.*.nc" | wc -l)
    (( nhist >= 500 )) || fail "$site only $nhist archived annual h0a files; do not assume 500 years completed"
    nr=$(grep -c 'model execution success' "$case/CaseStatus" || true)
    na=$(grep -c 'st_archive success' "$case/CaseStatus" || true)
    (( nr >= 100 && na >= 100 )) || fail "$site too few successful model/archive events (run=$nr archive=$na)"
    # Refuse to trample results from a newer submission that has not been archived.
    last_sub=$(grep -n 'case.submit success' "$case/CaseStatus" | tail -1 | cut -d: -f1 || true)
    last_arc=$(grep -n 'st_archive success' "$case/CaseStatus" | tail -1 | cut -d: -f1 || true)
    [[ -n "$last_sub" && -n "$last_arc" && "$last_arc" -gt "$last_sub" ]] || fail "$site has unarchived/newer submission; inspect manually"
    STAMP[$site]="$stamp"; DONE[$site]="$done"; LEFT[$site]="$remaining"; RESUB[$site]="$((remaining - 1))"
    printf '%-7s archive=%s completed=%4d/1000 extra_left=%3d segments RESUBMIT=%d\n' "$site" "$stamp" "$done" "$remaining" "${RESUB[$site]}"
}

audit_all() {
    no_six_jobs
    echo '===== SIX STATIONS: VALIDATE EXISTING 500+ YEAR ARCHIVES ====='
    local site
    for site in "${SITES[@]}"; do check_site "$site"; done
    echo 'Read-only preflight PASSED. No case/output files modified.'
}

batch_ok() {
    local case="$1" f k
    for f in .case.run case.st_archive; do
        [[ -s "$case/$f" ]] || return 1
        ! grep -q -- '--exclusive' "$case/$f" || return 1
        for k in '--nodes=1' '--ntasks-per-node=1' '--cpus-per-task=1' '--mem=8G'; do
            grep -Eq "^#SBATCH[[:space:]]+${k}[[:space:]]*$" "$case/$f" || return 1
        done
        if [[ -n "$EXCLUDE_NODES" ]]; then
            grep -Eq "^#SBATCH[[:space:]]+--exclude=${EXCLUDE_NODES}[[:space:]]*$" "$case/$f" || return 1
        fi
    done
    return 0
}

patch_batch_xml() {
    local xml="$1"
    python3 - "$xml" "$EXCLUDE_NODES" <<'PY'
import sys,re,xml.etree.ElementTree as ET
from pathlib import Path
p=Path(sys.argv[1]); exclude=sys.argv[2]
s=p.read_text(); orig=s
exclusive=re.compile(r'(?m)^[ \t]*<directive>[ \t]*--exclusive[ \t]*</directive>[ \t]*\r?\n')
s,n=exclusive.subn('',s)
if n not in (0,2) or '--exclusive' in s:
    raise SystemExit(f'STOP: unknown --exclusive XML entries; removed={n}')
needle='<directive>--cpus-per-task={{ thread_count }}</directive>'
if s.count(needle)!=1: raise SystemExit('STOP: unknown CIME cpus-per-task XML template')
for flag,wanted in [('--mem','<directive>--mem=8G</directive>')]:
    found=re.findall(r'<directive>\s*--mem(?:=|\s).*?</directive>',s)
    if found and (len(found)!=1 or found[0]!=wanted):
        raise SystemExit(f'STOP: conflicting memory directives: {found}')
    if not found: s=s.replace(needle,needle+'\n        '+wanted,1)
if exclude:
    wanted=f'<directive>--exclude={exclude}</directive>'
    found=re.findall(r'<directive>\s*--exclude(?:=|\s).*?</directive>',s)
    if found and (len(found)!=1 or found[0]!=wanted):
        raise SystemExit(f'STOP: conflicting node exclusions: {found}')
    if not found: s=s.replace(needle,needle+'\n        '+wanted,1)
ET.fromstring(s)
if s!=orig: p.write_text(s)
print('CIME Slurm batch XML:', 'updated' if s!=orig else 'already compatible')
PY
}

prepare_one() {
    local site="$1" name="${1}_FATES_SPINUP500" case run arch stamp rest b f comp kind ref exe newexclude
    case=$(casepath "$site"); run="$OUT/$name/run"; arch="$OUT/archive/$name"
    stamp="${STAMP[$site]}"; rest="$arch/rest/$stamp"
    b="$SESSION/cases/$site"
    mkdir -p "$b" "$b/partial_history"
    echo "===== PREPARE $site: last full checkpoint $stamp ====="
    cd "$case"
    for f in env_run.xml env_batch.xml env_mach_specific.xml env_case.xml env_build.xml env_archive.xml env_mach_pes.xml env_workflow.xml .case.run case.st_archive CaseStatus user_nl_clm user_nl_datm_streams; do
        [[ ! -f "$f" ]] || cp -p "$f" "$b/$f"
    done
    [[ ! -d LockedFiles ]] || cp -a LockedFiles "$b/LockedFiles"
    for comp in cpl atm lnd; do
        [[ ! -f "$run/rpointer.$comp" ]] || cp -p "$run/rpointer.$comp" "$b/original_rpointer.$comp"
    done
    sha256sum user_nl_clm user_nl_datm_streams > "$b/science.sha256"
    # Preserve unarchived history dated on or after last complete checkpoint.
    local count=0 histyear base
    shopt -s nullglob
    for f in "$run/$name".clm2.h*.nc; do
        base="${f##*/}"
        if [[ "$base" =~ \.h[^.]*\.([0-9]{4})- ]]; then
            histyear="${BASH_REMATCH[1]}"
            if (( 10#$histyear >= 10#${stamp:0:4} )); then
                mv -- "$f" "$b/partial_history/$base"
                ((count+=1))
            fi
        fi
    done
    shopt -u nullglob
    echo "$site backed up $count partial history files; existing full archive unchanged."
    rsync -a "$rest/" "$run/"
    for comp in cpl atm lnd; do
        case "$comp" in cpl) kind=cpl.r;; atm) kind=datm.r;; lnd) kind=clm2.r;; esac
        ref=$(pointer_ref "$run/rpointer.$comp.$stamp" "$name" "$kind" "$stamp")
        [[ -s "$run/$ref" ]] || fail "$site restart copy incomplete for $ref"
        cp --remove-destination -p "$run/rpointer.$comp.$stamp" "$run/rpointer.$comp"
    done
    local before_batch after_batch
    before_batch=$(sha "$case/env_batch.xml")
    patch_batch_xml "$case/env_batch.xml"
    after_batch=$(sha "$case/env_batch.xml")
    # LockedFiles must be regenerated whenever env_batch.xml itself changes,
    # EVEN IF the old generated .case.run happens to appear compatible.
    if [[ "$before_batch" != "$after_batch" ]] || ! batch_ok "$case"; then
        echo "$site: reset CIME scripts to apply nonexclusive 1-CPU/8G setup"
        ./case.setup --reset > "$b/case_setup_reset.log" 2>&1 || { tail -70 "$b/case_setup_reset.log" >&2; fail "$site CIME reset failed"; }
    fi
    exe=$(val "$case" EXEROOT)
    [[ "$exe" == "$OUT/GF-Guy_FATES_SURF2000_CO2405_1PT/bld" && -x "$exe/cesm.exe" ]] || fail "$site executable changed/missing after setup"
    [[ "$(val "$case" MPILIB)" == openmpi && "$(val "$case" CONTINUE_RUN)" == TRUE ]] || fail "$site MPI/continuation changed after setup"
    [[ "$(val "$case" RUN_TYPE)" == startup && "$(val "$case" RUN_STARTDATE)" == "${FIRST[$site]}-01-01" ]] || fail "$site origin setup changed"
    [[ "$(val "$case" CALENDAR)" == NO_LEAP && "$(val "$case" ATM_NCPL)" == 48 ]] || fail "$site timing config changed"
    for comp in ATM LND CPL; do
        [[ "$(val "$case" NTASKS_${comp})" == 1 && "$(val "$case" NTHRDS_${comp})" == 1 ]] || fail "$site task layout changed during CIME setup"
    done
    if [[ "$(val "$case" BUILD_COMPLETE)" != TRUE ]]; then
        ./xmlchange BUILD_COMPLETE=TRUE
    fi
    # CIME MPI_RUN_COMMAND overrides the old non-Slurm-aware mpirun launcher.
    ./xmlchange "MPI_RUN_COMMAND=$MPI_CMD"
    ./xmlchange "RESUBMIT=${RESUB[$site]}"
    [[ "$(rawval "$case" MPI_RUN_COMMAND)" == "$MPI_CMD" ]] || fail "$site bad MPI override"
    [[ "$(val "$case" RESUBMIT)" == "${RESUB[$site]}" ]] || fail "$site bad RESUBMIT"
    [[ "$(val "$case" STOP_N)" == 5 && "$(val "$case" REST_N)" == 5 ]] || fail "$site five-year segments changed"
    (cd "$case" && sha256sum -c "$b/science.sha256") >/dev/null || fail "$site science inputs changed"
    batch_ok "$case" || fail "$site invalid generated Slurm directives"
    ./preview_run > "$b/preview_run.log" 2>&1 || fail "$site preview_run failed"
    grep -Fq "$MPI_CMD $exe/cesm.exe" "$b/preview_run.log" || fail "$site preview_run did not use correct srun cesm.exe"
    sha256sum env_batch.xml env_run.xml user_nl_clm user_nl_datm_streams > "$b/prepared.sha256"
    echo "$site PREPARED; no job submitted."
}

prepare_all() {
    audit_all
    command -v rsync >/dev/null || fail 'rsync missing'
    command -v flock >/dev/null || fail 'flock missing'
    exec 9>"$HOME/.six_site_500to1000_prepare.lock"
    flock -n 9 || fail 'A six-site preparation is already active'
    mkdir -p "$SESSION_ROOT"
    SESSION=$(mktemp -d "$SESSION_ROOT/six_site_500to1000_$(date +%Y%m%d_%H%M%S)_XXXXXX")
    echo "SESSION=$SESSION"
    mkdir -p "$SESSION/cases"
    printf 'site\tstamp\tdone_years\tleft_segments\tresubmit\tcasestatus_sha256\n' > "$SESSION/manifest.tsv"
    local site
    for site in "${SITES[@]}"; do
        mkdir -p "$SESSION/cases/$site"
        prepare_one "$site" 2>&1 | tee "$SESSION/cases/$site/prepare.log"
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$site" "${STAMP[$site]}" "${DONE[$site]}" "${LEFT[$site]}" "${RESUB[$site]}" "$(sha "$(casepath "$site")/CaseStatus")" >> "$SESSION/manifest.tsv"
    done
    [[ "$(wc -l < "$SESSION/manifest.tsv")" == 7 ]] || fail 'Incomplete manifest'
    printf '%s\n' "$EXCLUDE_NODES" > "$SESSION/exclude_nodes.txt"
    touch "$SESSION/PREPARED"
    echo '===== SIX CASES PREPARED; NO MODEL JOBS SUBMITTED ====='
    echo "SESSION=$SESSION"
    echo "Manifest: $SESSION/manifest.tsv"
}

submit_all() {
    local session="$1" site stamp done left resubmit expectedsha c n=0
    [[ -d "$session" && -f "$session/PREPARED" ]] || fail 'Supply path to successfully prepared SESSION'
    [[ ! -e "$session/SUBMIT_STARTED" ]] || fail 'This session has already attempted a submission'
    no_six_jobs
    [[ "$(wc -l < "$session/manifest.tsv")" == 7 ]] || fail 'Manifest must contain exactly six cases'
    [[ -f "$session/exclude_nodes.txt" && "$(cat "$session/exclude_nodes.txt")" == "$EXCLUDE_NODES" ]] || fail 'EXCLUDE_NODES differs from prepare; use same environment value'
    while IFS=$'\t' read -r site stamp done left resubmit expectedsha; do
        [[ "$site" == site ]] && continue
        ((n+=1)); [[ " ${SITES[*]} " == *" $site "* ]] || fail "Unrecognized manifest site $site"
        c=$(casepath "$site")
        [[ "$(latest "$OUT/archive/${site}_FATES_SPINUP500/rest")" == "$stamp" ]] || fail "$site checkpoint changed after prepare"
        [[ "$(val "$c" RESUBMIT)" == "$resubmit" && "$(rawval "$c" MPI_RUN_COMMAND)" == "$MPI_CMD" ]] || fail "$site CIME configuration changed"
        [[ "$(sha "$c/CaseStatus")" == "$expectedsha" ]] || fail "$site CaseStatus changed since prepare; possible prior submit"
        (cd "$c" && sha256sum -c "$session/cases/$site/prepared.sha256") >/dev/null || fail "$site prepared config changed"
        batch_ok "$c" || fail "$site Slurm resource configuration changed"
    done < "$session/manifest.tsv"
    [[ "$n" == 6 ]] || fail "Expected 6 manifest rows, found $n"
    touch "$session/SUBMIT_STARTED"   # one-shot, even if a later site fails
    echo '===== SUBMIT SIX EXISTING 500->1000 CONTINUATIONS ====='
    while IFS=$'\t' read -r site stamp done left resubmit expectedsha; do
        [[ "$site" == site ]] && continue
        echo "Submit $site from $stamp, $left five-year segments remaining"
        (cd "$(casepath "$site")" && ./case.submit) 2>&1 | tee "$session/cases/$site/submit.log"
        echo "$site" >> "$session/submitted_sites.txt"
    done < "$session/manifest.tsv"
    squeue -u "$USER" -o '%.12i %.36j %.10T %.8C %R'
}

status_all() {
    squeue -u "$USER" -o '%.12i %.36j %.10T %.8C %R' || true
    echo '===== CURRENT SIX-SITE COMPLETE RESTARTS ====='
    local site c d yr
    for site in "${SITES[@]}"; do
        c=$(casepath "$site")
        d=$(latest "$OUT/archive/${site}_FATES_SPINUP500/rest")
        yr="${d:0:4}"
        echo "$site archived=$d cumulative_years=$((10#$yr - FIRST[$site]))/1000 resubmit=$(val "$c" RESUBMIT) MPI=$(rawval "$c" MPI_RUN_COMMAND)"
    done
}

case "$MODE" in
    audit) audit_all ;;
    prepare) prepare_all ;;
    submit) [[ $# == 2 ]] || fail 'Usage: script submit SESSION_DIRECTORY'; submit_all "$2" ;;
    status) status_all ;;
esac
