#!/usr/bin/env bash
#SBATCH --nodes=1
#SBATCH --job-name=fates_5site_1000_plot
#SBATCH --time=04:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=1
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
# READ-ONLY diagnostics: no CIME jobs or experiment data altered.
set -euo pipefail

# Must match actual checkout path (commands below clone here if absent).
REPO="${HOME}/CLM-FATES-single-site-workflows"
SCRIPT="${HOME}/14_plot_five_site_spinup1000.py"

if ! command -v conda >/dev/null 2>&1; then
  # Some noninteractive shells do not load conda; use the known login profile.
  source "${HOME}/.bash_profile" 2>/dev/null || true
fi
command -v conda >/dev/null 2>&1 || { echo 'ERROR: conda command not found' >&2; exit 1; }
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate clm_fates_env

[[ -f "$SCRIPT" ]] || { echo "ERROR missing $SCRIPT" >&2; exit 1; }
[[ -f "$REPO/examples/FLUXNET_MultiSite_6/scripts/10_compare_six_site_latest_complete_cycle.py" ]] || {
  echo "ERROR missing existing GitHub reference script under $REPO" >&2
  exit 1
}

python -u "$SCRIPT" \
  --repo "$REPO" \
  --output-root "${HOME}/six_site_spinup1000_final"
