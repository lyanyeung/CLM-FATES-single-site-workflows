#!/usr/bin/env bash
# Guarded Git object packing for nine completed 1000-year cases (2026-10-20).
# Usage: bash pack_11site_nine_1000yr.sh audit|run
# Excludes IT-Noe and CH-Aws. Never deletes .git, outputs, or stale locks.
set -Eeuo pipefail
MODE="$1"
case "$MODE" in audit|run) ;; *) echo "Usage: bash $0 audit|run" >&2; exit 2;; esac

ROOT="/iridisfs/scratch/ly3n24/CLM_FATES/cases"
OUT="/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive"
SITES="BE-Bra FR-Fon GL-ZaH AT-Neu FI-Sod CH-Cha CH-Fru CH-Lae CZ-Stn"
SELF_JOB="$(printenv SLURM_JOB_ID 2>/dev/null || true)"
die() { echo "STOP: $*" >&2; exit 1; }

exec 9>"$HOME/.11site_nine_git_pack.lock"
flock -n 9 || die "Another copy of this maintenance script is running"

check_queue() {
    local jobs jid job state site
    jobs="$(squeue -h -u "$USER" -o '%i|%j|%t')" || die "squeue failed"
    while IFS='|' read -r jid job state; do
        [[ -n "$jid" ]] || continue
        [[ -n "$SELF_JOB" && "$jid" == "$SELF_JOB" ]] && continue
        for site in $SITES; do
            if [[ "$job" == *"${site}_FATES_SPINUP500_11P"* ]]; then
                die "Slurm job targets selected case: $jid $job $state"
            fi
        done
    done <<< "$jobs"
}

xml() {
    (cd "$1" && ./xmlquery "$2" --value) | tr -d '[:space:]'
}

verify_archive() {
    python3 - "$1" "$2" "$3" <<'PY'
from pathlib import Path
import re, sys
root, name, first = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
hist = root / "lnd" / "hist"
rest = root / "rest"
if not hist.is_dir():
    sys.exit(f"STOP: missing archived history directory: {hist}")
pat = re.compile(re.escape(name) + r"\.clm2\.h0a\.(\d{4})-\d{2}-\d{2}(?:-\d+)?\.nc$")
years = []
for item in hist.iterdir():
    if item.is_file():
        m = pat.fullmatch(item.name)
        if m:
            if item.stat().st_size <= 0:
                sys.exit(f"STOP: zero-byte history file: {item}")
            years.append(int(m.group(1)))
expected = list(range(first, first + 1000))
if len(years) != 1000 or sorted(years) != expected:
    missing = sorted(set(expected) - set(years))
    sys.exit(f"STOP: {name}: {len(years)} annual files; missing years {missing[:8]}")
end = first + 1000
if not rest.is_dir():
    sys.exit(f"STOP: missing restart directory: {rest}")
last = [p for p in rest.iterdir()
        if p.is_dir() and p.name.startswith(f"{end:04d}-01-01-")]
if not last or not any(any(p.iterdir()) for p in last):
    sys.exit(f"STOP: missing/empty final archived restart at {end}-01-01")
print(f"HISTORY_OK {name}: {first}-{end-1}, 1000 annual files, restart {end}-01-01")
PY
}

git_info() {
    du --inodes -s "$1/.git"
    git -C "$1" count-objects -vH | grep -E '^(count|in-pack|packs|size-pack):'
}

check_site() {
    local site="$1" name c a root resub stop start first
    name="$site"_FATES_SPINUP500_11P
    c="$ROOT/$name"
    a="$OUT/$name"
    [[ -x "$c/xmlquery" && -s "$c/CaseStatus" && -d "$c/.git" ]] ||
        die "$site: missing case, CaseStatus or Git directory"
    root="$(git -C "$c" rev-parse --show-toplevel)" || die "$site: Git lookup failed"
    [[ "$(realpath "$root")" == "$(realpath "$c")" ]] || die "$site: Git root mismatch"
    [[ ! -e "$c/.git/gc.pid" ]] || die "$site: gc.pid exists; investigate recorded PID/host"
    if find "$c/.git" -name '*.lock' -print -quit | grep -q .; then
        die "$site: Git lock exists; do not delete automatically"
    fi
    resub="$(xml "$c" RESUBMIT)"
    stop="$(xml "$c" STOP_N)"
    start="$(xml "$c" RUN_STARTDATE)"
    [[ "$resub" == 0 && "$stop" == 5 ]] ||
        die "$site: expected RESUBMIT=0 STOP_N=5, got $resub $stop"
    [[ "$start" =~ ^[0-9]{4}-01-01$ ]] || die "$site: unexpected RUN_STARTDATE=$start"
    grep -q 'st_archive success' "$c/CaseStatus" || die "$site: no archive success in CaseStatus"
    first="$(printf '%s' "$start" | cut -c1-4)"
    verify_archive "$a" "$name" "$first"
    git -C "$c" fsck --connectivity-only --no-dangling >/dev/null ||
        die "$site: git fsck failed"
    echo "READY $site (RESUBMIT=$resub)"
    git_info "$c"
}

echo "NINE COMPLETED SITES ONLY; EXCLUDED: IT-Noe CH-Aws; MODE=$MODE"
check_queue
for site in $SITES; do
    check_site "$site"
done
if [[ "$MODE" == audit ]]; then
    echo "AUDIT PASSED: no changes made"
    exit 0
fi

for site in $SITES; do
    check_queue
    check_site "$site"
    c="$ROOT/$site"_FATES_SPINUP500_11P
    loose="$(git -C "$c" count-objects -v | awk '/^count:/ {print $2}')"
    if [[ "$loose" == 0 ]]; then
        echo "SKIP $site: already packed"
    else
        echo "PACK $site: $loose loose objects"
        nice -n 10 git -C "$c" gc --no-prune
    fi
    git -C "$c" fsck --connectivity-only --no-dangling
    echo "AFTER $site"
    git_info "$c"
done
echo "DONE. Verify Scratch quota with myfiles; no model files removed."
