#!/usr/bin/env bash
# Audit or compact Git objects in *idle* CIME case repositories.
# Usage: bash cime_git_maintenance.sh audit|run [EXACT_CASE_BASENAME ...]
set -Eeuo pipefail
MODE="${1:-audit}"
[[ "$MODE" == "audit" || "$MODE" == "run" ]] || { echo "Usage: $0 audit|run [case basename ...]" >&2; exit 2; }
shift || true
ROOT="${CIME_CASE_ROOT:-/iridisfs/scratch/ly3n24/CLM_FATES/cases}"
if (( $# > 0 )); then
  CASES=("$@")
else
  CASES=(RU-Fyo_FATES_SPINUP500 DE-Tha_FATES_SPINUP500 DK-Sor_FATES_SPINUP500 NL-Loo_FATES_SPINUP500 IL-Yat_FATES_SPINUP500)
fi
[[ -d "$ROOT" ]] || { echo "Missing case root: $ROOT" >&2; exit 1; }
# Prevent simultaneous invocation of this script even across multiple login nodes.
exec 9>"$HOME/.cime_git_maintenance.lock"
flock -n 9 || { echo "STOP: another maintenance invocation has the lock"; exit 1; }
# Conservative: any user's Slurm job may modify a target case, including opaque job names.
check_slurm() {
  command -v squeue >/dev/null || { echo "STOP: squeue unavailable"; return 1; }
  local jobs
  jobs="$(squeue -h -u "$USER" -o '%i %j %t')" || return 1
  if [[ -n "$jobs" ]]; then printf 'STOP: Slurm jobs exist:\n%s\n' "$jobs"; return 1; fi
}
check_case() {
  local name="$1" casepath="$ROOT/$1" actual
  [[ "$name" =~ ^[a-zA-Z0-9_.-]+$ && "$name" != "." && "$name" != ".." ]] || { echo "STOP: invalid case basename: $name"; return 1; }
  [[ -d "$casepath/.git" && -f "$casepath/CaseStatus" ]] || { echo "STOP: missing CIME case: $casepath"; return 1; }
  actual="$(git -C "$casepath" rev-parse --show-toplevel)"
  [[ "$(realpath "$actual")" == "$(realpath "$casepath")" ]] || { echo "STOP: Git root mismatch: $name"; return 1; }
  if [[ -e "$casepath/.git/gc.pid" ]]; then echo "STOP: gc.pid exists: $name"; return 1; fi
  if find "$casepath/.git" -name '*.lock' -print -quit | grep -q .; then echo "STOP: Git lock exists: $name"; return 1; fi
  git -C "$casepath" fsck --connectivity-only --no-dangling >/dev/null || { echo "STOP: Git fsck failed: $name"; return 1; }
}
stats() {
  local name="$1" c="$ROOT/$name"
  printf '%-42s ' "$name"
  du --inodes -s "$c/.git" | awk '{printf "inodes=%-7s ", $1}'
  git -C "$c" count-objects -v | awk '/^count:/ {a=$2} /^in-pack:/ {b=$2} /^packs:/ {p=$2} END {printf "loose=%-7s packed=%-7s packs=%s\n",a,b,p}'
}
check_slurm
echo "Mode: $MODE | Case root: $ROOT"
# Preflight ALL before writing anything. A stale lock stops the batch.
for name in "${CASES[@]}"; do check_case "$name"; stats "$name"; done
if [[ "$MODE" == "audit" ]]; then echo "AUDIT ONLY: no case files changed"; exit 0; fi
for name in "${CASES[@]}"; do
  check_slurm
  check_case "$name"
  c="$ROOT/$name"
  loose="$(git -C "$c" count-objects -v | awk '/^count:/ {print $2}')"
  if [[ "$loose" == 0 ]]; then
    echo "SKIP already packed: $name"
  else
    echo "PACK $name ($loose loose objects)"
    nice -n 10 git -C "$c" gc --no-prune
  fi
  git -C "$c" fsck --connectivity-only --no-dangling >/dev/null
  stats "$name"
done
if command -v myfiles >/dev/null; then myfiles; fi
echo "COMPLETE"
