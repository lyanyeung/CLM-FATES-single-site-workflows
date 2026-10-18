#!/usr/bin/env bash
# IRIDIS6 one-click continuation: RU-Fyo, DE-Tha, DK-Sor, NL-Loo, IL-Yat.
# Continue ORIGINAL CIME cases from 1000 -> 3000 cumulative model years.
# Reuses the pinned, tested 500->1000 continuation logic; never rebuilds cesm.exe.
# CIME original case name remains <SITE>_FATES_SPINUP500 by design.
# Usage: bash SCRIPT all | audit | prepare | status | submit SESSION_DIR
set -Eeuo pipefail
trap 'rc=$?; echo "STOP: wrapper failed at line $LINENO (exit $rc). No blind retry; inspect logs." >&2' ERR

MODE="${1:-all}"
[[ "$MODE" =~ ^(all|audit|prepare|submit|status)$ ]] || { echo "Usage: $0 all|audit|prepare|submit SESSION_DIR|status" >&2; exit 2; }
[[ "${USER:-}" == ly3n24 ]] || { echo 'STOP: designed for IRIDIS account ly3n24.' >&2; exit 2; }
REPO="$HOME/CLM-FATES-single-site-workflows"
REL='examples/FLUXNET_MultiSite_6/scripts/13_extend_six_site_spinup500_to1000.sh'
PIN='273ccb976856e1b71c67788a1b9e6b76eb6cca84'
GENERATED="$HOME/20_five_site_spinup1000_to3000_generated.sh"
ROOT='/scratch/ly3n24/CTSM_FATES_OUTPUTS/recovery_backups/five_site_1000to3000'
mkdir -p "$ROOT"
command -v git >/dev/null || { echo 'STOP: git missing' >&2; exit 2; }
command -v python3 >/dev/null || { echo 'STOP: python3 missing' >&2; exit 2; }
command -v squeue >/dev/null || { echo 'STOP: not on a Slurm login node' >&2; exit 2; }
[[ -d "$REPO/.git" ]] || { echo "STOP: Git repo missing at $REPO" >&2; exit 2; }
GOT=$(git -C "$REPO" rev-parse "main:$REL" 2>/dev/null) || {
    echo "STOP: script template unavailable. Use git pull --ff-only in $REPO" >&2; exit 2;
}
[[ "$GOT" == "$PIN" ]] || {
    echo "STOP: upstream template version differs: $GOT vs $PIN" >&2
    echo "Check current version: $REPO/$REL" >&2
    echo 'Do not silently patch an unreviewed template.' >&2
    exit 2
}
TMP="$(mktemp "$ROOT/source_13.XXXXXX")"
trap 'rm -f -- "$TMP"' EXIT
git -C "$REPO" show "main:$REL" > "$TMP"
python3 - "$TMP" "$GENERATED" <<'PY'
import sys
from pathlib import Path
source, dest = map(Path, sys.argv[1:])
s = source.read_text()

def sub(old, new, n=1):
    global s
    found = s.count(old)
    if found != n:
        raise SystemExit(f'STOP: source template changed! Expected {n} occurrences, got {found}: {old[:110]!r}')
    s = s.replace(old, new)

sub('SITES=( DE-Hai RU-Fyo DE-Tha DK-Sor NL-Loo IL-Yat )',
    'SITES=( RU-Fyo DE-Tha DK-Sor NL-Loo IL-Yat )')
sub('SESSION_ROOT="$OUT/recovery_backups"',
    'SESSION_ROOT="$OUT/recovery_backups/five_site_1000to3000"')
sub('    (( done >= 500 && done <= 1000 && done % 5 == 0 )) || fail "$site archived years=$done; expected 500 to 1000 in 5-year steps"\n'
    '    [[ "$done" -lt 1000 ]] || fail "$site already reached 1000; do not resubmit"\n'
    '    remaining=$(((1000 - done) / 5))',
    '    (( done == 1000 )) || fail "$site archived years=$done; require EXACTLY 1000 completed model years"\n'
    '    [[ "$stamp" == "$(printf "%04d-01-01-00000" "$(( FIRST[$site] + 1000 ))")" ]] || fail "$site unexpected 1000-year restart stamp"\n'
    '    remaining=400')
sub('(( nhist >= 500 )) || fail "$site only $nhist archived annual h0a files; do not assume 500 years completed"',
    '(( nhist >= 1000 )) || fail "$site only $nhist archived annual h0a files; require at least 1000"')
sub('(( nr >= 100 && na >= 100 ))', '(( nr >= 200 && na >= 200 ))')
sub("archive=%s completed=%4d/1000 extra_left=%3d segments RESUBMIT=%d\\n",
    "archive=%s completed=%4d/3000 extra_left=%3d segments RESUBMIT=%d\\n")
sub('"$HOME/.six_site_500to1000_prepare.lock"', '"$HOME/.five_site_1000to3000_prepare.lock"')
sub('"$SESSION_ROOT/six_site_500to1000_$(date +%Y%m%d_%H%M%S)_XXXXXX"',
    '"$SESSION_ROOT/five_site_1000to3000_$(date +%Y%m%d_%H%M%S)_XXXXXX"')
sub('"$(wc -l < "$SESSION/manifest.tsv")" == 7', '"$(wc -l < "$SESSION/manifest.tsv")" == 6')
sub('"$(wc -l < "$session/manifest.tsv")" == 7', '"$(wc -l < "$session/manifest.tsv")" == 6')
sub('Manifest must contain exactly six cases', 'Manifest must contain exactly five cases')
sub('"$n" == 6', '"$n" == 5')
sub('Expected 6 manifest rows', 'Expected 5 manifest rows')
sub('cumulative_years=$((10#$yr - FIRST[$site]))/1000',
    'cumulative_years=$((10#$yr - FIRST[$site]))/3000')
sub('===== SIX STATIONS: VALIDATE EXISTING 500+ YEAR ARCHIVES =====',
    '===== FIVE STATIONS: VALIDATE COMPLETE 1000-YEAR ARCHIVES =====')
sub('===== SIX CASES PREPARED; NO MODEL JOBS SUBMITTED =====',
    '===== FIVE CASES PREPARED; NO MODEL JOBS SUBMITTED =====')
sub('===== SUBMIT SIX EXISTING 500->1000 CONTINUATIONS =====',
    '===== SUBMIT FIVE EXISTING 1000->3000 CONTINUATIONS =====')
sub('===== CURRENT SIX-SITE COMPLETE RESTARTS =====',
    '===== CURRENT FIVE-SITE COMPLETE RESTARTS =====')
# Preserve a completely separate, checksummed copy of each 1000-year restart.
sub('    rsync -a "$rest/" "$run/"',
    '    mkdir -p "$b/initial_1000yr_restart"\n'
    '    rsync -a "$rest/" "$b/initial_1000yr_restart/"\n'
    '    ( cd "$rest" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum ) > "$b/initial_restart.sha256"\n'
    '    ( cd "$b/initial_1000yr_restart" && sha256sum -c "$b/initial_restart.sha256" ) >/dev/null || fail "$site initial restart backup failed checksum"\n'
    '    rsync -a "$rest/" "$run/"')
sub('no_six_jobs', 'no_five_jobs', 3)
sub('# Six cases only;', '# Five cases only;')
sub('500-model-year spin-ups to 1000 years (500 additional model years).',
    '1000-model-year spin-ups to 3000 years (2000 additional model years).')
# Reject a mismatch rather than writing a plausible-looking but unsafe generated script.
assert 'SITES=( RU-Fyo DE-Tha DK-Sor NL-Loo IL-Yat )' in s
assert 'remaining=400' in s and 'RESUB[$site]="$((remaining - 1))"' in s
assert 'MPI_CMD=\'srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores\'' in s
assert '"$(val "$case" RESUBMIT)" == 0' in s  # no leftover queued extension
assert 'batch_ok "$case"' in s and 'sha256sum -c' in s
assert '[[ "$n" == 5 ]]' in s and '"$SESSION/manifest.tsv")" == 6' in s
assert '[[ "$done" -lt 1000 ]]' not in s
assert '(( done >= 500' not in s
assert 'remaining=$(((1000 - done) / 5))' not in s
dest.write_text(s)
dest.chmod(0o700)
print(f'Generated vetted continuation script: {dest}')
print('5 sites; +2000 model years = 400 x 5-year segments; RESUBMIT=399.')
PY
bash -n "$GENERATED"

if [[ "$MODE" == all ]]; then
    # Prevent two simultaneous interactive one-click launches.
    exec 8>"$HOME/.five_site_1000to3000_all.lock"
    flock -n 8 || { echo 'STOP: another one-click launch is active.' >&2; exit 2; }
    LOG="$ROOT/oneclick_$(date +%Y%m%d_%H%M%S).log"
    echo "LOG=$LOG"
    echo '========== AUDIT (read-only) ==========' | tee -a "$LOG"
    bash "$GENERATED" audit 2>&1 | tee -a "$LOG"
    echo '========== PREPARE (backup/checkpoint/stage; no submissions) ==========' | tee -a "$LOG"
    bash "$GENERATED" prepare 2>&1 | tee -a "$LOG"
    SESSION=$(grep '^SESSION=' "$LOG" | tail -1 | cut -d= -f2-)
    [[ -n "$SESSION" && -s "$SESSION/manifest.tsv" && -f "$SESSION/PREPARED" ]] || {
        echo 'STOP: prepare incomplete. No model job submitted.' >&2; exit 1;
    }
    echo '========== FINAL PLAN ==========' | tee -a "$LOG"
    cat "$SESSION/manifest.tsv" | tee -a "$LOG"
    echo '========== SUBMIT FIVE CASES ONCE ==========' | tee -a "$LOG"
    bash "$GENERATED" submit "$SESSION" 2>&1 | tee -a "$LOG"
    echo "SESSION=$SESSION"
    echo "LOG=$LOG"
    echo "Monitor: bash $GENERATED status"
else
    if [[ "$MODE" == submit ]]; then
        [[ $# == 2 ]] || { echo "Usage: $0 submit SESSION_DIR" >&2; exit 2; }
        bash "$GENERATED" submit "$2"
    else
        [[ $# == 1 ]] || { echo "Usage: $0 $MODE" >&2; exit 2; }
        bash "$GENERATED" "$MODE"
    fi
fi
