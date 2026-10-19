#!/usr/bin/env bash
# Read-only inspection. NEVER automatically remove a remote-host gc.pid.
set -Eeuo pipefail
[[ $# -eq 1 && "$1" =~ ^[a-zA-Z0-9_.-]+$ && "$1" != "." && "$1" != ".." ]] || { echo "Usage: $0 EXACT_CASE_BASENAME" >&2; exit 2; }
ROOT="${CIME_CASE_ROOT:-/iridisfs/scratch/ly3n24/CLM_FATES/cases}"
CASE="$ROOT/$1"
LOCK="$CASE/.git/gc.pid"
[[ -d "$CASE/.git" ]] || { echo "Missing case Git: $CASE"; exit 1; }
echo "=== Case ==="; echo "$CASE"
echo "=== Current login node ==="; hostname
echo "=== Lock ==="
if [[ -e "$LOCK" ]]; then
  cat "$LOCK"; echo; stat "$LOCK"
  echo "IMPORTANT: this could refer to a process on a DIFFERENT HOST."
else
  echo "No gc.pid"
fi
echo "=== Other Git lock files ==="
find "$CASE/.git" -name '*.lock' -print
echo "=== Slurm ==="
squeue -u "$USER" || true
echo "=== Current-host Git processes (NOT a cluster-wide check) ==="
ps -u "$USER" -o pid,ppid,stat,etime,args | grep -E 'git gc|git repack|pack-objects|prune-packed' | grep -v grep || true
echo "=== Objects ==="
git -C "$CASE" count-objects -vH
echo "=== Policy ==="
echo "Do NOT remove a lock based only on its age or a local ps check."
