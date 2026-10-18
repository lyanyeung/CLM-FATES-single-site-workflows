#!/bin/bash
#SBATCH --job-name=seven500_figs
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=03:00:00
#SBATCH --output=seven_site_spinup500_%j.log
#SBATCH --error=seven_site_spinup500_%j.err

set -euo pipefail

# Limit Python numerical libraries to one CPU
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export BLIS_NUM_THREADS=1

REPO="$HOME/CLM-FATES-single-site-workflows"
SCRIPT="$REPO/examples/FLUXNET_MultiSite_8/scripts/18_plot_seven_site_spinup500.py"

cd "$REPO"

echo "Started: $(date -Is)"
echo "Node: $(hostname)"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Allocated CPUs: ${SLURM_CPUS_PER_TASK}"
echo "Python: $(command -v python)"

python -c 'import netCDF4, numpy, pandas, matplotlib; print("Dependencies OK")'

# Explicit CPU binding; serial processing of seven sites
srun --mpi=none \
     --ntasks=1 \
     --cpus-per-task=1 \
     --cpu-bind=cores \
     python "$SCRIPT" \
       --repo "$REPO" \
       --output-root "$HOME/seven_site_spinup500_final"

echo "Finished: $(date -Is)"
