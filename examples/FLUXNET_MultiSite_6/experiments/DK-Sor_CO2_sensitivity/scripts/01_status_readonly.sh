#!/usr/bin/env bash
# READ-ONLY monitoring: DK-Sor historical fixed-CO2 vs NOAA-CO2 experiments.
# IRIDIS6, user ly3n24. Never calls case.submit, xmlchange, scancel or case.build.
set -Eeuo pipefail
ROOT=/iridisfs/scratch/ly3n24/CLM_FATES/cases
ARCH=/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive
CASES=( DK-Sor_FATES_HIST1996_2024_TEST DK-Sor_FATES_HIST1996_2024_NOAA_CO2 )
echo "=== DK-Sor historical CO2 sensitivity: read-only status ==="
if command -v squeue >/dev/null 2>&1; then
  echo "-- Slurm jobs (full names; truncated display names can be ambiguous)"
  squeue -h -u ly3n24 -o '%i|%j|%t|%M|%R' |
    grep -F 'DK-Sor_FATES_HIST1996_2024_' || true
fi
for name in "${CASES[@]}"; do
  echo
  echo "=== $name ==="
  case_dir="$ROOT/$name"
  hist_dir="$ARCH/$name/lnd/hist"
  restart_dir="$ARCH/$name/rest"
  if [[ -s "$case_dir/CaseStatus" ]]; then
    tail -n 18 "$case_dir/CaseStatus"
  else
    echo "No CaseStatus yet: $case_dir"
  fi
  if [[ -d "$hist_dir" ]]; then
    mapfile -t history < <(find "$hist_dir" -maxdepth 1 -type f -name "$name.clm2.h0a.*.nc" -printf '%f\n' | sort)
    echo "Archived annual h0a count: ${#history[@]}"
    if (("${#history[@]}" > 0)); then
      echo "First: ${history[0]}"
      echo "Last:  ${history[${#history[@]}-1]}"
    fi
  else
    echo "No archived lnd/hist directory yet"
  fi
  if [[ -d "$restart_dir" ]]; then
    echo "Latest archived restart directories:"
    find "$restart_dir" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort | tail -n 3
  else
    echo "No archived restart directory yet"
  fi
done
echo
echo "Read-only complete. A Slurm COMPLETED state alone does not verify CO2 is changing in FATES."
