#!/usr/bin/env bash
#SBATCH --job-name=probe_srun_pmix
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:03:00
#SBATCH --output=/home/ly3n24/probe_srun_%j.out
#SBATCH --error=/home/ly3n24/probe_srun_%j.err

set -euo pipefail
source /etc/profile.d/modules.sh
module load intel/2022.2.0.classic.custom
module load openmpi/5.0.7_classic.custom
test -x "$HOME/mpi_affinity_test"
echo "JOB=$SLURM_JOB_ID NODE=$(hostname)"
echo "===== SLURM PROCESS CPU AFFINITY ====="
grep Cpus_allowed_list /proc/self/status
echo "===== SRUN PMIX RANK AFFINITY (MPI_Init) ====="
srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=verbose,cores "$HOME/mpi_affinity_test"
echo "===== COMPLETED ====="
