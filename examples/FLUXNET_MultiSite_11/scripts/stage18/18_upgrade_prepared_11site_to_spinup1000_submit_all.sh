#!/usr/bin/env bash
# Upgrade the EXISTING eleven PREPARED but NEVER SUBMITTED 500-year 11P cases
# to 1000 model years and submit all eleven first segments with Slurm-safe PMIx.
# Reference: FLUXNET_MultiSite_8/docs/srun_pmix_resume_2026-10-14.md
# Modes: --audit | --prepare | --submit-all | --status
# NOT a scientific certification of provisional Stage15 forcing or surface/PFT.
set -Eeuo pipefail
trap 'rc=$?; printf "ERROR line %s exit=%s. Inspect output; never blindly resubmit.\n" "$LINENO" "$rc" >&2' ERR
MODE="${1:---audit}"
case "$MODE" in --audit|--prepare|--submit-all|--status) ;; *) echo "Usage: bash $0 --audit|--prepare|--submit-all|--status" >&2; exit 2;; esac
USER_ID="$(id -un)"
[[ "$USER_ID" == ly3n24 ]] || { echo "Wrong user: $USER_ID" >&2; exit 2; }
ROOT="/iridisfs/scratch/$USER_ID/CLM_FATES"
CASES="$ROOT/cases"; SITES_ROOT="$ROOT/sites/MY_EC_SITE"
OUTROOT="/scratch/$USER_ID/CTSM_FATES_OUTPUTS"
SOURCE="$CASES/GF-Guy_FATES_SURF2000_CO2405_1PT"
DATM_SUBDIR='datm_11_provisional_dynamic_zbot_v1'
POLICY="$HOME/FLUXNET_MultiSite_11/stage15_provisional_DATM/height_policy_v1.json"
POLICY_SHA='4eff9273d6aa73bc71f4b6104470b9189fb3d5491ea2393698564720f6764068'
VERIFY="$HOME/FLUXNET_MultiSite_11_stage15/03_verify_11_datm_readonly.py"
MPI_CMD='srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores'
TOTAL_YEARS=1000; SEGMENT_YEARS=5; TOTAL_SEGMENTS=200; RESUB=199
# Case names deliberately preserve previously prepared paths: renaming a CIME case is unsafe.
# Case name says 500, but the verified CIME RESUBMIT=199 means 1000 actual model years.
SITES=(BE-Bra FR-Fon GL-ZaH IT-Noe AT-Neu FI-Sod CH-Aws CH-Cha CH-Fru CH-Lae CZ-Stn)
declare -A FIRST=( [BE-Bra]=1996 [FR-Fon]=2005 [GL-ZaH]=2000 [IT-Noe]=2004 [AT-Neu]=2002 [FI-Sod]=2001 [CH-Aws]=2006 [CH-Cha]=2005 [CH-Fru]=2005 [CH-Lae]=2004 [CZ-Stn]=2010 )
declare -A LAST=( [BE-Bra]=2025 [FR-Fon]=2025 [GL-ZaH]=2025 [IT-Noe]=2025 [AT-Neu]=2020 [FI-Sod]=2025 [CH-Aws]=2024 [CH-Cha]=2024 [CH-Fru]=2024 [CH-Lae]=2024 [CZ-Stn]=2024 )
declare -A CO2=( [BE-Bra]=361.93 [FR-Fon]=378.98 [GL-ZaH]=368.96 [IT-Noe]=376.95 [AT-Neu]=372.58 [FI-Sod]=370.56 [CH-Aws]=381.15 [CH-Cha]=378.98 [CH-Fru]=378.98 [CH-Lae]=376.95 [CZ-Stn]=388.75 )
STATE="$HOME/FLUXNET_MultiSite_11/stage18_spinup1000_srun_pmix"
READY="$STATE/PREPARED_ALL_11_1000YR"
LOCK="$HOME/.fates11_spinup1000_modify_and_submit.lock"
fail(){ echo "STOP: $*" >&2; exit 1; }
case_name(){ printf '%s_FATES_SPINUP500_11P' "$1"; }
case_dir(){ printf '%s/%s' "$CASES" "$(case_name "$1")"; }
xval(){ (cd "$1" && ./xmlquery "$2" --value) | tr -d '[:space:]'; }
xraw(){ (cd "$1" && ./xmlquery "$2" --value) | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'; }
lock(){ command -v flock >/dev/null || fail 'flock missing'; exec 9>"$LOCK"; flock -n 9 || fail 'Another 11-site operation holds the lock'; }
no_submissions(){
    local site="$1" c name j run arch
    c="$(case_dir "$site")"; name="$(case_name "$site")"
    [[ -s "$c/CaseStatus" ]] || fail "$site CaseStatus missing"
    if grep -Eiq 'case\.submit success|model execution starting|case\.run (starting|success)|st_archive success' "$c/CaseStatus"; then
        fail "$site: CaseStatus shows a prior submission/run; cannot treat this as a fresh 1000-year start"
    fi
    [[ -z "$(squeue -h -u "$USER_ID" -o '%j' | grep -Fx "run.$name" || :)" ]] || fail "$site: run job already queued"
    [[ -z "$(squeue -h -u "$USER_ID" -o '%j' | grep -Fx "st_archive.$name" || :)" ]] || fail "$site: archive job already queued"
    run="$OUTROOT/$name/run"; arch="$OUTROOT/archive/$name"
    for j in "$run" "$arch"; do
        if [[ -d "$j" ]] && [[ -n "$(find "$j" -type f \( -name 'rpointer.*' -o -name '*.nc' -o -name '*log.*' \) -print -quit)" ]]; then
            fail "$site: run/archive output already exists in $j"
        fi
    done
}
slurm_verify(){
    local c="$1" f k
    for f in "$c/.case.run" "$c/case.st_archive"; do
        [[ -s "$f" ]] || fail "Missing Slurm batch script $f"
        ! grep -q -- '--exclusive' "$f" || fail "Slurm --exclusive would waste node: $f"
        for k in '--nodes=1' '--ntasks-per-node=1' '--cpus-per-task=1' '--mem=8G'; do
            grep -Eq "^#SBATCH[[:space:]]+${k}[[:space:]]*$" "$f" || fail "$f lacks #SBATCH $k"
        done
    done
}
check_one(){
    local s="$1" desired="$2" c name v srcmpi ex sf datm y n ph comp
    c="$(case_dir "$s")"; name="$(case_name "$s")"
    [[ -x "$c/xmlquery" && -x "$c/case.submit" && -x "$c/preview_run" ]] || fail "$s: not a prepared CIME case"
    [[ "$(xval "$c" CASE)" == "$name" ]] || fail "$s: wrong case ID"
    [[ "$(xval "$c" RUN_TYPE)" == startup && "$(xval "$c" CONTINUE_RUN)" == FALSE ]] || fail "$s: existing continuation/run detected"
    no_submissions "$s"
    [[ "$(xval "$c" CALENDAR)" == NO_LEAP && "$(xval "$c" ATM_NCPL)" == 48 ]] || fail "$s: model time convention changed"
    [[ "$(xval "$c" RUN_STARTDATE)" == "${FIRST[$s]}-01-01" ]] || fail "$s: unexpected initial year"
    [[ "$(xval "$c" STOP_OPTION)" == nyears && "$(xval "$c" STOP_N)" == 5 && "$(xval "$c" REST_N)" == 5 ]] || fail "$s: expected 5-year segments and restarts"
    v="$(xval "$c" RESUBMIT)"
    if [[ "$desired" == either ]]; then [[ "$v" == 99 || "$v" == 199 ]] || fail "$s: unexpected RESUBMIT=$v"
    else [[ "$v" == "$desired" ]] || fail "$s: RESUBMIT=$v expected $desired"; fi
    [[ "$(xval "$c" BUILD_COMPLETE)" == TRUE ]] || fail "$s: BUILD_COMPLETE not TRUE"
    [[ "$(xval "$c" CLM_CO2_TYPE)" == constant ]] || fail "$s: CO2 must be constant"
    ph="$(xval "$c" CCSM_CO2_PPMV)"
    python3 - "$ph" "${CO2[$s]}" <<'PY'
import sys
assert abs(float(sys.argv[1])-float(sys.argv[2]))<0.011, 'CO2 setting mismatch'
PY
    [[ "$(xval "$c" DOUT_S)" == TRUE ]] || fail "$s: short-term archive disabled"
    [[ "$(xval "$c" RUNDIR)" == "$OUTROOT/$name/run" ]] || fail "$s: RUNDIR wrong"
    [[ "$(xval "$c" DOUT_S_ROOT)" == "$OUTROOT/archive/$name" ]] || fail "$s: archive path wrong"
    [[ "$(xraw "$c" MPI_RUN_COMMAND)" == "$MPI_CMD" ]] || fail "$s: MPI override missing or incorrect"
    [[ "$(xval "$c" MPILIB)" == "$(xval "$SOURCE" MPILIB)" ]] || fail "$s: MPILIB differs from validated GF-Guy"
    ex="$(xval "$SOURCE" EXEROOT)"
    [[ "$(xval "$c" EXEROOT)" == "$ex" && -x "$ex/cesm.exe" ]] || fail "$s: not using GF-Guy tested executable"
    for comp in ATM LND CPL; do
       [[ "$(xval "$c" NTASKS_$comp)" == 1 && "$(xval "$c" NTHRDS_$comp)" == 1 ]] || fail "$s: $comp is not 1 rank / 1 thread"
    done
    slurm_verify "$c"
    [[ -s "$c/CaseDocs/lnd_in" && -s "$c/user_nl_clm" && -s "$c/user_nl_datm_streams" ]] || fail "$s: missing case namelists"
    mapfile -t sf < <(find "$SITES_ROOT/$s/subset_data" -type f -name 'surfdata*.nc' | sort)
    [[ "${#sf[@]}" == 1 && -s "${sf[0]}" ]] || fail "$s: missing/ambiguous site surface"
    grep -Fq "$(basename "${sf[0]}")" "$c/user_nl_clm" || fail "$s: incorrect land surface in user_nl_clm"
    grep -Fq "$(basename "${sf[0]}")" "$c/CaseDocs/lnd_in" || fail "$s: incorrect land surface in compiled land namelist"
    grep -Eiq 'use_excess_ice[[:space:]]*=[[:space:]]*\.false\.' "$c/CaseDocs/lnd_in" || fail "$s: excess ice workaround missing"
    grep -Fq "${s}_DATM_${FIRST[$s]}.nc" "$c/user_nl_datm_streams" || fail "$s: first DATM file not in stream"
    grep -Fq "${s}_DATM_${LAST[$s]}.nc" "$c/user_nl_datm_streams" || fail "$s: last DATM file not in stream"
    grep -Fq 'CLM_USRDAT.UNSET:taxmode = cycle' "$c/user_nl_datm_streams" || fail "$s: forcing not cycling"
    [[ -d "$SITES_ROOT/$s/forcing/$DATM_SUBDIR" ]] || fail "$s: DATM path missing"
    n=0
    for ((y=FIRST[$s]; y<=LAST[$s]; y++)); do
        datm="$SITES_ROOT/$s/forcing/$DATM_SUBDIR/${s}_DATM_${y}.nc"
        [[ -s "$datm" ]] || fail "$s: missing forcing file $datm"
        ((n+=1))
    done
    # Both MPI launch and batch Slurm directives must be validated; no old mpirun fallback.
    local preview
    preview="$(cd "$c" && ./preview_run)" || fail "$s: preview_run failed"
    grep -Fq "$MPI_CMD $ex/cesm.exe" <<<"$preview" || fail "$s: preview_run did not resolve tested srun/PMIx command"
    printf 'READY %-7s RESUBMIT=%-3s segments=%-3s years=%-4s DATM=%-2s 1CPU/8G PMIx srun\n' "$s" "$v" "$((v+1))" "$(((v+1)*5))" "$n"
}
check_global(){
    [[ -x "$SOURCE/xmlquery" && -s "$SOURCE/CaseStatus" ]] || fail 'GF-Guy reference case missing'
    [[ "$(xval "$SOURCE" BUILD_COMPLETE)" == TRUE ]] || fail 'GF-Guy BUILD_COMPLETE not true'
    [[ -x "$(xval "$SOURCE" EXEROOT)/cesm.exe" ]] || fail 'GF-Guy binary missing'
    [[ "$(xval "$SOURCE" MPILIB)" != mpi-serial ]] || fail 'GF-Guy MPI was serial'
    [[ -s "$POLICY" && -s "$VERIFY" ]] || fail 'Original frozen Stage15 inputs unavailable'
    [[ "$(sha256sum "$POLICY" | awk '{print $1}')" == "$POLICY_SHA" ]] || fail 'Height policy changed'
    command -v squeue >/dev/null || fail 'Slurm squeue missing'
    command -v python >/dev/null || fail 'Python/conda environment missing'
    for s in "${SITES[@]}"; do check_one "$s" "${1:-either}"; done
    echo "ALL 11 SITE CONFIGS OK (technical checks only, not scientific certification)."
}
case "$MODE" in
  --audit)
     lock
     check_global either
     echo 'AUDIT ONLY: No case settings changed. No jobs submitted.'
     ;;
  --prepare)
     lock
     [[ ! -e "$STATE/SUBMIT_STARTED" ]] || fail 'Submission already started; do not reconfigure ongoing cases'
     check_global either
     mkdir -p "$STATE"
     [[ ! -e "$READY" ]] || { check_global 199; echo 'Already prepared for 1000 years; no changes'; exit 0; }
     # Backup all affected XMLs before changing a single setting.
     SNAPSHOT="$STATE/backup_$(date -u +%Y%m%dT%H%M%SZ)_$$"
     mkdir -p "$SNAPSHOT"
     for s in "${SITES[@]}"; do
         c="$(case_dir "$s")"; mkdir -p "$SNAPSHOT/$s"
         cp -p "$c/env_run.xml" "$c/CaseStatus" "$SNAPSHOT/$s/"
         [[ ! -f "$c/env_batch.xml" ]] || cp -p "$c/env_batch.xml" "$SNAPSHOT/$s/"
     done
     printf 'Backup (CIME env_run / CaseStatus): %s\n' "$SNAPSHOT"
     for s in "${SITES[@]}"; do
         c="$(case_dir "$s")"
         if [[ "$(xval "$c" RESUBMIT)" == 99 ]]; then
             (cd "$c" && ./xmlchange RESUBMIT=199)
             printf 'UPGRADED %s: RESUBMIT 99 -> 199 (1000 model years)\n' "$s"
         else
             echo "UNCHANGED $s: RESUBMIT already 199"
         fi
     done
     check_global 199
     printf 'site\tcase\tmodel_years\tsegments\tresubmit\tforcing_first\tforcing_last\tco2_ppm\n' > "$STATE/prepared_manifest.tsv"
     for s in "${SITES[@]}"; do
         printf '%s\t%s\t1000\t200\t199\t%s\t%s\t%s\n' "$s" "$(case_name "$s")" "${FIRST[$s]}" "${LAST[$s]}" "${CO2[$s]}" >> "$STATE/prepared_manifest.tsv"
     done
     printf '%s\n' "$(date -Is)" > "$READY"
     echo "PREPARED 11/11 FOR 1000 YEARS. BACKUP=$SNAPSHOT. NO JOBS SUBMITTED."
     ;;
  --submit-all)
     lock
     [[ "${ACK_PROVISIONAL_SCIENCE:-}" == YES ]] || fail 'Explicit acknowledgement required: ACK_PROVISIONAL_SCIENCE=YES'
     [[ -s "$READY" && -s "$STATE/prepared_manifest.tsv" ]] || fail 'First run --prepare; all 11 must be marked prepared'
     [[ ! -e "$STATE/SUBMIT_STARTED" ]] || fail "Prior submit-all attempt detected at $STATE/SUBMIT_STARTED; inspect manifest; never blindly resubmit"
     check_global 199
     echo '=== Independent Stage15 forcing audit (read-only) ==='
     python "$VERIFY" || fail '238/238 forcing audit failed; no jobs submitted'
     # Preserve an exact submission manifest before any possible partial submission.
     mkdir -p "$STATE"
     printf 'site\tcase\tresult\ttimestamp\n' > "$STATE/submission_manifest.tsv"
     printf '%s\n' "$(date -Is)" > "$STATE/SUBMIT_STARTED"
     echo '=== SUBMITTING ALL 11 FRESH CASES: 200 x 5 years = 1000 model years each ==='
     for s in "${SITES[@]}"; do
         c="$(case_dir "$s")"
         echo "SUBMIT $s: first of 200 five-year jobs (CIME RESUBMIT=199)"
         if (cd "$c" && ./case.submit); then
             printf '%s\t%s\tSUBMITTED\t%s\n' "$s" "$(case_name "$s")" "$(date -Is)" >> "$STATE/submission_manifest.tsv"
         else
             printf '%s\t%s\tFAILED\t%s\n' "$s" "$(case_name "$s")" "$(date -Is)" >> "$STATE/submission_manifest.tsv"
             fail "Submission failure at $s. Prior jobs may have been queued. Inspect $STATE/submission_manifest.tsv; do not rerun --submit-all"
         fi
     done
     printf '%s\n' "$(date -Is)" > "$STATE/SUBMITTED_ALL_11"
     echo 'SUBMITTED 11/11 first segments. This is not proof of successful execution or of 1000-year completion.'
     cat "$STATE/submission_manifest.tsv"
     squeue -u "$USER_ID" -o '%.12i %.40j %.10T %.8C %R'
     ;;
  --status)
     if [[ -s "$STATE/submission_manifest.tsv" ]]; then cat "$STATE/submission_manifest.tsv"; fi
     for s in "${SITES[@]}"; do
        c="$(case_dir "$s")"
        if [[ -f "$c/CaseStatus" ]]; then
          echo "=== $s RESUBMIT=$(xval "$c" RESUBMIT) (name remains *SPINUP500_11P for provenance) ==="
          tail -n 4 "$c/CaseStatus"
        else echo "=== $s CASE MISSING ==="; fi
     done
     squeue -u "$USER_ID" -o '%.12i %.40j %.10T %.8C %R'
     ;;
esac
