#!/usr/bin/env bash
# Eleven-site PROVISIONAL CLM-FATES startup spin-up, adapted from proven 8-site CIME workflow.
# GitHub references: FLUXNET_MultiSite_8/scripts/09_eight_site_spinup500.sh
#                    FLUXNET_MultiSite_8/docs/srun_pmix_resume_2026-10-14.md
# Usage: --preflight | --prepare | --submit SITE | --status
# --prepare configures the cases, but never submits. --submit submits ONE named site.
set -Eeuo pipefail
trap 'rc=$?; echo "STOP at line ${LINENO}, exit=${rc}. No automatic retry; inspect output." >&2' ERR

MODE="${1:---preflight}"
if [[ "$MODE" != --preflight && "$MODE" != --prepare && "$MODE" != --submit && "$MODE" != --status ]]; then
    echo "Usage: bash $0 --preflight|--prepare|--submit SITE|--status" >&2; exit 2
fi

USER_ID="${IRIDIS_USER:-$(id -un)}"
[[ "$USER_ID" == ly3n24 ]] || { echo 'STOP: expected IRIDIS user ly3n24' >&2; exit 2; }
ROOT="/iridisfs/scratch/${USER_ID}/CLM_FATES"
SITES_ROOT="$ROOT/sites/MY_EC_SITE"
CASES="$ROOT/cases"
CTSM="$ROOT/CTSM"
INPUTDATA="$ROOT/inputdata"
OUTROOT="/scratch/${USER_ID}/CTSM_FATES_OUTPUTS"
SOURCE_CASE="$CASES/GF-Guy_FATES_SURF2000_CO2405_1PT"
DATM_FOLDER='datm_11_provisional_dynamic_zbot_v1'
POLICY="$HOME/FLUXNET_MultiSite_11/stage15_provisional_DATM/height_policy_v1.json"
VERIFY="$HOME/FLUXNET_MultiSite_11_stage15/03_verify_11_datm_readonly.py"
MPI_CMD='srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores'
TOTAL_YEARS=500
CHUNK_YEARS=5
RESUBMITS=99
# NOAA GML global annual mean CO2 in first forcing year, frozen from 2026 data
# https://gml.noaa.gov/ccgg/trends/gl_data.html
SITES=(BE-Bra FR-Fon GL-ZaH IT-Noe AT-Neu FI-Sod CH-Aws CH-Cha CH-Fru CH-Lae CZ-Stn)
declare -A FIRST=( [BE-Bra]=1996 [FR-Fon]=2005 [GL-ZaH]=2000 [IT-Noe]=2004 [AT-Neu]=2002 [FI-Sod]=2001 [CH-Aws]=2006 [CH-Cha]=2005 [CH-Fru]=2005 [CH-Lae]=2004 [CZ-Stn]=2010 )
declare -A LAST=( [BE-Bra]=2025 [FR-Fon]=2025 [GL-ZaH]=2025 [IT-Noe]=2025 [AT-Neu]=2020 [FI-Sod]=2025 [CH-Aws]=2024 [CH-Cha]=2024 [CH-Fru]=2024 [CH-Lae]=2024 [CZ-Stn]=2024 )
declare -A CO2=( [BE-Bra]=361.93 [FR-Fon]=378.98 [GL-ZaH]=368.96 [IT-Noe]=376.95 [AT-Neu]=372.58 [FI-Sod]=370.56 [CH-Aws]=381.15 [CH-Cha]=378.98 [CH-Fru]=378.98 [CH-Lae]=376.95 [CZ-Stn]=388.75 )
fail(){ echo "STOP: $*" >&2; exit 1; }
case_name(){ printf '%s_FATES_SPINUP500_11P' "$1"; }
case_path(){ printf '%s/%s' "$CASES" "$(case_name "$1")"; }
xmlval(){ (cd "$1" && ./xmlquery "$2" --value) | tr -d '[:space:]'; }
xmlraw(){ (cd "$1" && ./xmlquery "$2" --value) | sed -e 's/^ *//' -e 's/ *$//' ; }
site_exists(){ local s; for s in "${SITES[@]}"; do [[ "$s" != "$1" ]] || return 0; done; return 1; }
lock_setup(){ command -v flock >/dev/null || fail 'flock unavailable'; exec 9>"$CASES/.eleven_provisional_500_setup.lock"; flock -n 9 || fail 'another 11-site setup is active'; }

verify_slurm(){
    local c="$1" f key
    for f in "$c/.case.run" "$c/case.st_archive"; do
        [[ -s "$f" ]] || fail "Missing batch file $f"
        ! grep -q -- '--exclusive' "$f" || fail "--exclusive still present: $f"
        for key in '--nodes=1' '--ntasks-per-node=1' '--cpus-per-task=1' '--mem=8G'; do
            grep -Eq "^#SBATCH[[:space:]]+${key}[[:space:]]*$" "$f" || fail "Missing ${key} in $f"
        done
    done
}

# Patches only a FRESHLY CREATED, IDLE clone; mirrors 8-site shared-node recovery.
patch_batch_xml(){
    python3 - "$1/env_batch.xml" <<'PY'
from pathlib import Path
import re, sys, xml.etree.ElementTree as ET
p=Path(sys.argv[1]); s=p.read_text()
s,n=re.subn(r'(?m)^[ \t]*<directive>[ \t]*--exclusive[ \t]*</directive>[ \t]*\r?\n','',s)
if n not in (0,1,2): raise SystemExit(f'STOP: unexpected --exclusive count {n}')
if '--exclusive' in s: raise SystemExit('STOP: other exclusive directive remains')
needle='<directive>--cpus-per-task={{ thread_count }}</directive>'
if s.count(needle)!=1: raise SystemExit('STOP: expected exactly one cpus-per-task directive')
mem='<directive>--mem=8G</directive>'
allmem=re.findall(r'<directive>\s*--mem(?:=|\s).*?</directive>',s)
if not allmem: s=s.replace(needle,needle+'\n        '+mem,1)
elif len(allmem)!=1 or allmem[0]!=mem: raise SystemExit(f'STOP: unexpected existing memory directive {allmem}')
ET.fromstring(s)
if p.read_text()!=s:
    p.write_text(s)
    print('env_batch.xml: removed exclusive and set --mem=8G')
else: print('env_batch.xml: resources already corrected')
PY
}

# All modes other than --status validate the source environment.
preflight(){
    [[ -d "$SITES_ROOT" && -d "$CASES" && -d "$INPUTDATA" ]] || fail 'CTSM/inputdata/cases missing'
    [[ -x "$CTSM/cime/scripts/create_clone" ]] || fail 'CIME create_clone missing'
    [[ -x "$SOURCE_CASE/xmlquery" && -s "$SOURCE_CASE/CaseStatus" ]] || fail 'GF-Guy source case missing'
    grep -Eq 'model execution success|case.run success' "$SOURCE_CASE/CaseStatus" || fail 'GF-Guy CaseStatus does not show successful run'
    local exe srcmpi
    exe="$(xmlval "$SOURCE_CASE" EXEROOT)"
    srcmpi="$(xmlval "$SOURCE_CASE" MPILIB)"
    [[ -x "$exe/cesm.exe" ]] || fail "Missing source cesm.exe: $exe"
    [[ "$(xmlval "$SOURCE_CASE" BUILD_COMPLETE)" == TRUE ]] || fail 'GF-Guy BUILD_COMPLETE != TRUE'
    [[ -n "$srcmpi" && "$srcmpi" != mpi-serial ]] || fail "Unsafe source MPILIB=$srcmpi"
    [[ -s "$POLICY" && -s "$VERIFY" ]] || fail 'Frozen Stage15 policy or validator missing'
    [[ "$(sha256sum "$POLICY" | awk '{print $1}')" == 4eff9273d6aa73bc71f4b6104470b9189fb3d5491ea2393698564720f6764068 ]] || fail 'Stage15 frozen height-policy SHA256 changed'
    echo "SOURCE MPI=$srcmpi EXEROOT=$exe"
    echo 'RUNNING VERIFIED STAGE15 INDEPENDENT DATM AUDIT (read only)'
    python "$VERIFY" || fail '238 DATM audit failed'
    local n=0 s c site_root mods datm y surf
    for s in "${SITES[@]}"; do
        site_root="$SITES_ROOT/$s"; mods="$site_root/subset_data/user_mods"; datm="$site_root/forcing/$DATM_FOLDER"
        [[ -s "$mods/user_nl_clm" ]] || fail "$s: user_nl_clm missing"
        [[ -d "$datm" ]] || fail "$s: DATM folder missing"
        mapfile -t SURF < <(find "$site_root/subset_data" -name 'surfdata*.nc' -type f | sort)
        [[ ${#SURF[@]} -eq 1 && -s "${SURF[0]}" ]] || fail "$s: expected one nonempty surface, got ${#SURF[@]}"
        grep -Fq "$(basename "${SURF[0]}")" "$mods/user_nl_clm" || fail "$s: user_nl_clm does not select site surface"
        for ((y=FIRST[$s];y<=LAST[$s];y++)); do
            [[ -s "$datm/${s}_DATM_${y}.nc" ]] || fail "$s: missing year $y DATM"
            ((n+=1))
        done
        c="$(case_path "$s")"
        if [[ -e "$c" ]]; then
            [[ -x "$c/xmlquery" ]] || fail "$s: an unexpected existing case path exists: $c"
            echo "NOTE $s case already exists; --prepare must not run blindly; use --status"
        fi
        echo "$s ${FIRST[$s]}-${LAST[$s]} CO2=${CO2[$s]} ppm Surface=$(basename "${SURF[0]}")"
    done
    [[ "$n" -eq 238 ]] || fail "Unexpected DATM count $n"
    echo "PREFLIGHT OK: $n annual forcing files; no CIME case created or job submitted"
}

prepare(){
    preflight
    lock_setup
    local s c name mods stage run arch exe srcmpi sf lat lon tmp
    exe="$(xmlval "$SOURCE_CASE" EXEROOT)"; srcmpi="$(xmlval "$SOURCE_CASE" MPILIB)"
    for s in "${SITES[@]}"; do
        c="$(case_path "$s")"
        [[ ! -e "$c" ]] || fail "$s: case already exists ($c). Do not overwrite or re-clone"
        name="$(case_name "$s")"; mods="$SITES_ROOT/$s/subset_data/user_mods"
        run="$OUTROOT/$name/run"; arch="$OUTROOT/archive/$name"
        for tmp in "$run" "$arch"; do [[ ! -e "$tmp" ]] || fail "$s: unexpected output path exists $tmp"; done
    done
    echo '=== PREPARE ALL 11: clones only, no submissions ==='
    for s in "${SITES[@]}"; do
        c="$(case_path "$s")"; name="$(case_name "$s")"; mods="$SITES_ROOT/$s/subset_data/user_mods"
        run="$OUTROOT/$name/run"; arch="$OUTROOT/archive/$name"
        echo "======== PREPARE $s ========"
        stage="$(mktemp -d "$HOME/.11site_${s}_mods.XXXXXX")"
        cp -a "$mods/." "$stage/"
        if [[ -f "$stage/shell_commands" ]]; then
            # Preserve original user_mods; only sanitize temporary clone input
            sed -i -E '/MPILIB[[:space:]]*=[[:space:]]*mpi-serial/d' "$stage/shell_commands"
            ! grep -Eq 'MPILIB[[:space:]]*=[[:space:]]*mpi-serial' "$stage/shell_commands" || fail "$s: mpi-serial remains"
        fi
        (cd "$CTSM/cime/scripts" && ./create_clone --case "$c" --clone "$SOURCE_CASE" --user-mods-dir "$stage" --keepexe)
        [[ -x "$c/xmlquery" ]] || fail "$s: clone missing xmlquery"
        cd "$c"
        cp -p "$mods/user_nl_clm" user_nl_clm
        sed -i -E '/^[[:space:]]*(use_excess_ice|use_excess_ice_streams|hist_nhtfrq|hist_mfilt)[[:space:]]*=/d' user_nl_clm
        cat >> user_nl_clm <<'NML'

! Proven GF-Guy workaround, with daily history for 500-year diagnostics
use_excess_ice = .false.
use_excess_ice_streams = .false.
hist_nhtfrq = -24
hist_mfilt = 365
NML
        sf="$(find "$SITES_ROOT/$s/subset_data" -type f -name 'surfdata*.nc' -print -quit)"
        grep -Fq "$(basename "$sf")" user_nl_clm || fail "$s: wrong surface after copying user_nl_clm"
        # Site coordinates derive from the validated Stage15 Surface, never from GF-Guy.
        read -r lat lon < <(python - "$sf" <<'PY'
from netCDF4 import Dataset
import numpy as np,sys
with Dataset(sys.argv[1]) as nc:
    def val(keys):
        for k in keys:
            if k in nc.variables:
                a=np.ma.filled(nc[k][:],np.nan).ravel()
                if len(a)==1 and np.isfinite(a[0]): return float(a[0])
        raise SystemExit(f'Missing scalar coordinates: {keys}')
    lat=val(['LATIXY','lat','latitude']);lon=val(['LONGXY','lon','longitude'])
    if lon>180:lon-=360
    if not -90<=lat<=90 or not -180<=lon<=180:raise SystemExit('Invalid site geo')
    print(lat,lon)
PY
)
        [[ -n "${lat:-}" && -n "${lon:-}" ]] || fail "$s: missing coordinates"
        # Exactly the DATM stream grammar from proven GF-Guy / eight-site case
        {
            printf 'CLM_USRDAT.UNSET:taxmode = cycle\n'
            printf 'CLM_USRDAT.UNSET:tintalgo = linear\n'
            printf 'CLM_USRDAT.UNSET:mapalgo = none\n'
            printf 'CLM_USRDAT.UNSET:meshfile = none\n\n'
            printf 'CLM_USRDAT.UNSET:year_first = %s\n' "${FIRST[$s]}"
            printf 'CLM_USRDAT.UNSET:year_last = %s\n' "${LAST[$s]}"
            printf 'CLM_USRDAT.UNSET:year_align = %s\n\n' "${FIRST[$s]}"
            printf 'CLM_USRDAT.UNSET:datafiles = \\\n'
            for ((y=FIRST[$s];y<=LAST[$s];y++)); do
                if ((y<LAST[$s]));then printf '%s, \\\n' "$SITES_ROOT/$s/forcing/$DATM_FOLDER/${s}_DATM_${y}.nc"
                else printf '%s\n' "$SITES_ROOT/$s/forcing/$DATM_FOLDER/${s}_DATM_${y}.nc"; fi
            done
            cat <<'DATM'

CLM_USRDAT.UNSET:datavars = \
PRECTmms Faxa_precn, \
FSDS Faxa_swdn, \
ZBOT Sa_z, \
TBOT Sa_tbot, \
WIND Sa_wind, \
QBOT Sa_shum, \
PSRF Sa_pbot, \
FLDS Faxa_lwdn
DATM
        } > user_nl_datm_streams
        touch user_nl_datm
        ./xmlchange DIN_LOC_ROOT="$INPUTDATA"
        ./xmlchange RUN_TYPE=startup
        ./xmlchange CONTINUE_RUN=FALSE
        ./xmlchange RUN_STARTDATE="${FIRST[$s]}-01-01"
        ./xmlchange CALENDAR=NO_LEAP
        ./xmlchange ATM_NCPL=48
        ./xmlchange CLM_CO2_TYPE=constant
        ./xmlchange CCSM_CO2_PPMV="${CO2[$s]}"
        ./xmlchange STOP_OPTION=nyears
        ./xmlchange STOP_N=5
        ./xmlchange REST_OPTION=nyears
        ./xmlchange REST_N=5
        ./xmlchange RESUBMIT=99
        ./xmlchange DOUT_S=TRUE
        ./xmlchange DOUT_S_ROOT="$arch"
        ./xmlchange RUNDIR="$run"
        # Crucial tested fix: CIME launch MUST honor Slurm CPU affinity.
        ./xmlchange "MPI_RUN_COMMAND=$MPI_CMD"
        if ./xmlquery PTS_LAT --value >/dev/null 2>&1; then ./xmlchange PTS_LAT="$lat"; fi
        if ./xmlquery PTS_LON --value >/dev/null 2>&1; then ./xmlchange PTS_LON="$lon"; fi
        [[ "$(xmlval "$c" MPILIB)" == "$srcmpi" ]] || fail "$s: MPILIB changed from source"
        [[ "$(xmlval "$c" EXEROOT)" == "$exe" ]] || fail "$s: executable not shared with GF-Guy"
        patch_batch_xml "$c"
        # Regenerate unlocked batch scripts from corrected env_batch.xml. Never rebuild.
        if grep -Eq 'case.setup success' CaseStatus || [[ -f .case.run ]]; then
            ./case.setup --reset
        else
            ./case.setup
        fi
        [[ "$(xmlval "$c" EXEROOT)" == "$exe" && -x "$exe/cesm.exe" ]] || fail "$s: executable invalid after case.setup"
        [[ "$(xmlval "$c" MPILIB)" == "$srcmpi" ]] || fail "$s: MPI library changed after case.setup"
        # CIME --keepexe clone has the successful executable; setup --reset may unset flag.
        if [[ "$(xmlval "$c" BUILD_COMPLETE)" != TRUE ]]; then ./xmlchange BUILD_COMPLETE=TRUE; fi
        ./preview_namelists
        [[ -s CaseDocs/lnd_in ]] || fail "$s: missing CaseDocs/lnd_in"
        grep -Fq "$(basename "$sf")" CaseDocs/lnd_in || fail "$s: generated namelist lacks own surface"
        grep -Eiq 'use_excess_ice[[:space:]]*=[[:space:]]*\.false\.' CaseDocs/lnd_in || fail "$s: excess ice workaround absent"
        ./check_input_data
        ./preview_run > "$HOME/${name}_preview_run.txt" 2>&1 || fail "$s: preview_run failed"
        grep -Fq "$MPI_CMD" "$HOME/${name}_preview_run.txt" || fail "$s: MPI launch not present in preview_run"
        verify_slurm "$c"
        [[ "$(xmlval "$c" RESUBMIT)" == 99 && "$(xmlval "$c" STOP_N)" == 5 ]] || fail "$s: bad segment count"
        [[ "$(xmlval "$c" RUN_STARTDATE)" == "${FIRST[$s]}-01-01" ]] || fail "$s: bad start date"
        [[ "$(xmlval "$c" BUILD_COMPLETE)" == TRUE ]] || fail "$s: build marked incomplete"
        for comp in ATM LND CPL; do
            [[ "$(xmlval "$c" NTASKS_${comp})" == 1 && "$(xmlval "$c" NTHRDS_${comp})" == 1 ]] || fail "$s: MPI task/thread mismatch on $comp"
        done
        echo "READY $s: 1 CPU, 8G, no --exclusive, PMIx srun, 5years x100, CO2=${CO2[$s]} ppm"
    done
    echo 'ALL 11 PREPARED. NO JOB SUBMITTED. To submit an exploratory site use --submit SITE with ACK_PROVISIONAL_SCIENCE=YES.'
}

submit_one(){
    local site="${2:-}" c name srcmpi source_exe
    [[ -n "$site" ]] && site_exists "$site" || fail 'Usage: --submit SITE (site must be in eleven-site list)'
    [[ "${ACK_PROVISIONAL_SCIENCE:-}" == YES ]] || fail 'Explicit acknowledgement required: ACK_PROVISIONAL_SCIENCE=YES (science QC/PFT and CH-Aws still provisional)'
    lock_setup
    name="$(case_name "$site")"; c="$(case_path "$site")"
    [[ -x "$c/case.submit" && -s "$c/CaseDocs/lnd_in" ]] || fail "$site: case not prepared"
    [[ "$(xmlval "$c" CASE)" == "$name" ]] || fail "$site: wrong CASE identity"
    [[ "$(xmlval "$c" RUN_STARTDATE)" == "${FIRST[$site]}-01-01" ]] || fail "$site: wrong first year"
    [[ "$(xmlval "$c" RUN_TYPE)" == startup && "$(xmlval "$c" CONTINUE_RUN)" == FALSE ]] || fail "$site: case already continued or not startup"
    [[ "$(xmlval "$c" STOP_N)" == 5 && "$(xmlval "$c" REST_N)" == 5 && "$(xmlval "$c" RESUBMIT)" == 99 ]] || fail "$site: 500yr segments not configured"
    [[ "$(xmlval "$c" CALENDAR)" == NO_LEAP && "$(xmlval "$c" ATM_NCPL)" == 48 ]] || fail "$site: calendar or ATM_NCPL wrong"
    [[ "$(xmlval "$c" BUILD_COMPLETE)" == TRUE ]] || fail "$site: BUILD_COMPLETE not true"
    [[ "$(xmlval "$c" CCSM_CO2_PPMV)" == "${CO2[$site]}" ]] || fail "$site: incorrect fixed CO2"
    [[ "$(xmlval "$c" RUNDIR)" == "$OUTROOT/$name/run" ]] || fail "$site: wrong run directory"
    [[ "$(xmlval "$c" DOUT_S_ROOT)" == "$OUTROOT/archive/$name" ]] || fail "$site: wrong archive directory"
    [[ "$(xmlraw "$c" MPI_RUN_COMMAND)" == "$MPI_CMD" ]] || fail "$site: wrong CIME MPI launcher"
    [[ "$(xmlval "$c" MPILIB)" == "$(xmlval "$SOURCE_CASE" MPILIB)" ]] || fail "$site: wrong MPILIB"
    source_exe="$(xmlval "$SOURCE_CASE" EXEROOT)"
    [[ "$(xmlval "$c" EXEROOT)" == "$source_exe" && -x "$source_exe/cesm.exe" ]] || fail "$site: wrong source executable"
    verify_slurm "$c"
    grep -Fq "${site}_DATM_${FIRST[$site]}.nc" "$c/user_nl_datm_streams" || fail "$site: wrong DATM first file"
    grep -Fq "${site}_DATM_${LAST[$site]}.nc" "$c/user_nl_datm_streams" || fail "$site: wrong DATM last file"
    grep -Fq 'CLM_USRDAT.UNSET:taxmode = cycle' "$c/user_nl_datm_streams" || fail "$site: forcing not cycling"
    if grep -Eiq 'case.submit success|model execution starting|case.run starting|case.run success' "$c/CaseStatus"; then
        fail "$site: already submitted/started. Never submit twice."
    fi
    if squeue -h -u "$USER_ID" -o '%j' | grep -Fxq "run.$name"; then fail "$site: active run job already in queue"; fi
    if squeue -h -u "$USER_ID" -o '%j' | grep -Fxq "st_archive.$name"; then fail "$site: active archive job already in queue"; fi
    # Fresh independent numeric audit just before first submission; doesn't alter data.
    python "$VERIFY" --sites "$site" || fail "$site: DATM audit failed before submit"
    echo "SUBMIT PROVISIONAL ${site}: 500-model-year experiment, 100 sequential 5-year segments"
    (cd "$c" && ./case.submit)
    squeue -u "$USER_ID" -o '%.12i %.36j %.10T %.8C %R'
    echo "SUBMITTED $site (first job only). Future resubmits depend on successful model/archive workflows."
}

status(){
    for s in "${SITES[@]}"; do
        c="$(case_path "$s")"
        if [[ -f "$c/CaseStatus" ]]; then
            echo "=== $s: $(xmlval "$c" RESUBMIT) resubmits remaining ==="
            tail -n 4 "$c/CaseStatus"
        else echo "=== $s: NOT PREPARED ==="; fi
    done
    squeue -u "$USER_ID" -o '%.12i %.36j %.10T %.8C %R'
}

case "$MODE" in
    --preflight) preflight ;;
    --prepare) prepare ;;
    --submit) submit_one "$@" ;;
    --status) status ;;
esac
