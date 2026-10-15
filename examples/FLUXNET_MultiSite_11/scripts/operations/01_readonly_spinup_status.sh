#!/usr/bin/env bash
# Safe, READ-ONLY snapshot of the submitted 11-site spin-up campaigns.
# Does not alter case XML, forcing, job dependencies, resubmission counts,
# model binaries, or scheduler state. Run on IRIDIS6.
set -Eeuo pipefail
CASES="/iridisfs/scratch/ly3n24/CLM_FATES/cases"
OUT="/scratch/ly3n24/CTSM_FATES_OUTPUTS"
sites=(BE-Bra FR-Fon GL-ZaH IT-Noe AT-Neu FI-Sod CH-Aws CH-Cha CH-Fru CH-Lae CZ-Stn)
echo "=== QUEUE ==="
squeue -u "$(id -un)" -o '%.12i %.48j %.12T %.8C %R' || true
echo
echo "=== SITE CASE STATUS ==="
printf '%-9s %-42s %-7s %-9s %-10s %-12s %-12s\n' "SITE" "CASE" "STOP_N" "RESUBMIT" "CONTINUE" "H0A_COUNT" "LATEST_STATUS"
for s in "${sites[@]}"; do
  case_name="${s}_FATES_SPINUP500_11P"
  c="$CASES/$case_name"
  if [[ ! -x "$c/xmlquery" ]]; then
    printf '%-9s MISSING_CASE\n' "$s"
    continue
  fi
  v() { (cd "$c" && ./xmlquery "$1" --value 2>/dev/null) | tr -d '[:space:]'; }
  sn="$(v STOP_N || true)"
  re="$(v RESUBMIT || true)"
  cr="$(v CONTINUE_RUN || true)"
  n=0
  if [[ -d "$OUT/archive/$case_name" ]]; then
    n="$(find "$OUT/archive/$case_name" -name '*.clm2.h0a.*.nc' -type f | wc -l)"
  fi
  status="$(tail -1 "$c/CaseStatus" 2>/dev/null | tr '\t' ' ' | cut -c1-42)"
  printf '%-9s %-42s %-7s %-9s %-10s %-12s %s\n' "$s" "$case_name" "$sn" "$re" "$cr" "$n" "$status"
done
echo
echo "=== CH-AWS TRIAL CASES (NOT SUCCESSFUL AS OF 2026-10-15) ==="
for n in CH-Aws_FATES_SPINUP1000_RH21A CH-Aws_FATES_SPINUP1000_RH25A; do
  c="$CASES/$n"
  [[ -d "$c" ]] || continue
  echo "$n"
  tail -6 "$c/CaseStatus" 2>/dev/null || true
done
echo
echo "=== RECORDED CH-AWS SLURM JOBS ==="
sacct -j 4286717,4286891,4286954 --format=JobID,JobName%42,State,ExitCode,Elapsed || true
echo
echo "READ-ONLY SNAPSHOT FINISHED. Running/PENDING does NOT mean model-year 1000 or convergence."
