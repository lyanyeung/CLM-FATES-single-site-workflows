#!/usr/bin/env bash
# GF-Guy Stage 3: run convergence and final-cycle EC validation.
# READ ONLY for CIME case, model restart and archived NetCDF input.
# Generates analysis files below the site spinup300_diagnostics/ directory.
set -Eeuo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/00_config.sh"

CASE_NAME_SPINUP="GF-Guy_FATES_SPINUP300_CO2405"
HIST="/scratch/${IRIDIS_USER}/CTSM_FATES_OUTPUTS/archive/${CASE_NAME_SPINUP}/lnd/hist"
OBS="${SITE_ROOT}/forcing/raw/ICOSETC_GF-Guy_ARCHIVE_L2/ICOSETC_GF-Guy_FLUXNET_HH_L2.csv"
OUT="${SITE_ROOT}/spinup300_diagnostics"

if [[ ! -d "$HIST" ]]; then
    echo "ERROR: model history folder not found: $HIST" >&2
    exit 1
fi
if [[ ! -f "$OBS" ]]; then
    echo "ERROR: half-hourly EC CSV not found: $OBS" >&2
    exit 1
fi

# Do NOT call case.setup, case.build, xmlchange or case.submit here.
echo "===== STEP 1: 300-year carbon-pool convergence ====="
python "$HERE/13_plot_spinup300_convergence.py" \
    --archive "$HIST" --output "$OUT"

echo "===== STEP 2: final 5-year cycle vs EC ====="
python "$HERE/14_compare_final_cycle_ec.py" \
    --user "$IRIDIS_USER" --hist "$HIST" --obs "$OBS" \
    --out "$OUT/EC_final_cycle"

echo
 echo "===== ANALYSIS COMPLETED ====="
 echo "Results: $OUT"
find "$OUT" -maxdepth 2 -type f \( -name '*.png' -o -name '*.csv' \) -print | sort
