# Extend the six completed FLUXNET CLM-FATES spin-ups from 500 to 1000 years

**Scope:** DE-Hai, RU-Fyo, DE-Tha, DK-Sor, NL-Loo, IL-Yat (the existing six CIME cases named `<SITE>_FATES_SPINUP500`). This script does not create new cases and does not modify the separately running eight-site experiment.

**Primary script:** `13_extend_six_site_spinup500_to1000.sh` (IRIDIS6 login node). Run the original `09_submit_six_site_spinup500.sh` **never** against these cases: it is the initial setup, not an extension procedure.

## Evidence from the source experiment

The repository's `examples/FLUXNET_MultiSite_6/README.md` states that all six completed the first 500 model years. It reports continued slow carbon-pool drift and says 500-year completion does not certify convergence. The old CIME script configured `STOP_N=REST_N=5`, `RUN_TYPE=startup` (retain as case metadata), `NO_LEAP`, `ATM_NCPL=48`, site-specific full-record DATM cycling, first-year constant CO2, and a shared tested GF-Guy executable. The new script preserves those science settings and stages the latest **fully archived** restart to resume the already-running simulation chronology.

| Site | Original model year | Expected 500-year checkpoint | Target 1000-year checkpoint | Fixed CO2 (ppm) |
|---|---:|---:|---:|---:|
| DE-Hai | 2000 | 2500-01-01 | 3000-01-01 | 368.96 |
| RU-Fyo | 1998 | 2498-01-01 | 2998-01-01 | 365.70 |
| DE-Tha | 1996 | 2496-01-01 | 2996-01-01 | 361.93 |
| DK-Sor | 1996 | 2496-01-01 | 2996-01-01 | 361.93 |
| NL-Loo | 1997 | 2497-01-01 | 2997-01-01 | 363.04 |
| IL-Yat | 2000 | 2500-01-01 | 3000-01-01 | 368.96 |

The target years are model-clock years, **not** the year of atmospheric forcing: DATM continues cycling the original EC years. The script reads actual archived restart dates and derives remaining 5-year segments to reach **1000 total**, not 1000 *additional* years.

## CPU allocation, node choice and MPI affinity (CPU-only cases)

- 1 Slurm CPU per model job, 8 GiB RAM per model job (and archive); remove Slurm `--exclusive` from the existing CIME `env_batch.xml`. The script runs `./case.setup --reset` only if the batch XML or generated scripts require regeneration; it never recompiles `cesm.exe`.
- Fix MPI binding using `./xmlchange "MPI_RUN_COMMAND=srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores"`. This launcher was validated with an MPI_Init test and one five-year IT-Ren case. Distinct Slurm CPU allocations alone are **not** definitive evidence of rank affinity.
- **Default:** no node is forced; Slurm schedules these six separate single-core jobs where capacity exists, possibly alongside the eight others with non-overlapping CPUs.
- **Optional exclusion:** set `EXCLUDE_NODES=red6129` during **both** prepare and submit. CIME then writes `#SBATCH --exclude=red6129`, so these six jobs will not run on red6129. This can lengthen queue times and **does not guarantee** isolation from the eight jobs if they later migrate to other nodes. Do not use `--exclusive` to obtain isolation; that wastes 192-core allocations for a one-core model.
- `--time` is left unchanged: inspect `grep '^#SBATCH' .case.run` and `squeue -o '%.12i %.12M %.12l %R'` and adjust only after assessing real job duration. One Slurm job runs **five model years**, not all 500 additional years.

## Operational sequence on IRIDIS6

Upload the script from local WSL to `/home/ly3n24/` with `scp`; do not execute it in WSL.

```bash
conda activate clm_fates_env
SCRIPT="$HOME/13_extend_six_site_spinup500_to1000.sh"
chmod +x "$SCRIPT"
bash -n "$SCRIPT"

# 1. Read-only verification — required, must pass for all six sites
bash "$SCRIPT" audit

# 2. Backup old case files, safely stage full restart, change Slurm/MPI;
#    DOES NOT SUBMIT any model jobs.
set -o pipefail
EXCLUDE_NODES=red6129 bash "$SCRIPT" prepare \
    2>&1 | tee "$HOME/six_site_500_to_1000_prepare.log"

# 3. Confirm complete preparation and inspect the manifest
SESSION=$(grep '^SESSION=' "$HOME/six_site_500_to_1000_prepare.log" \
    | tail -1 | cut -d= -f2-)
test -f "$SESSION/PREPARED" || { echo 'Incomplete preparation; STOP'; exit 1; }
cat "$SESSION/manifest.tsv"

# 4. ONLY when ready and willing to start six 500-year extension chains;
#    DO NOT resubmit this session again.
EXCLUDE_NODES=red6129 bash "$SCRIPT" submit "$SESSION"

# 5. Monitoring (read-only)
bash "$SCRIPT" status
squeue -u ly3n24 -o '%.12i %.36j %.10T %.8C %R'
```

To allow Slurm to use any eligible shared node, simply omit `EXCLUDE_NODES=red6129` in **both** prepare and submit commands. `audit` ignores the exclusion setting; `submit` requires that the same exclusion setting is used as during `prepare`.

**Before triggering prepare,** verify all six are idle, and that none of the six has a newer unarchived submission. The script checks this automatically and refuses inconsistent states. It also verifies the old simulation has reached at least 500 years, plus ≥500 archived annual land history files and ≥100 successful run/archive events. If any check fails, examine the reported difference rather than bypassing it.

## Safeguards

- `audit` and `status`: do not modify files; `audit` checks archive integrity, CIME consistency and no active six-site jobs.
- `prepare`: first backs up CIME XML/CaseStatus/namelist/pointers under `/scratch/ly3n24/CTSM_FATES_OUTPUTS/recovery_backups/six_site_500to1000_*`. Preserves unarchived history files separately, re-stages coordinated cpl/datm/clm2 restart and normalizes Fortran-padded `rpointer` entries. Modifies the six already-idle cases to `srun` and calculates remaining `RESUBMIT` values. It does **not** call `case.submit`.
- `submit SESSION`: checks the preparation manifest, checkpoints, resource directives and file SHA256 checksums before submitting. Marks `SUBMIT_STARTED` **before** any submission so a partial failure cannot lead to blind duplicate submissions. A failed prepare or submit is **not** automatically retried.
- `status`: shows Slurm queue and current completed years from archives; does not claim all six reached 1000 merely because a queue is empty.
- The script does **not** remove existing archived NetCDFs or rebuild the original shared executable; it does not touch `FLUXNET_MultiSite_8`. It does not copy entire archives out of scratch to protected storage; arrange independent backup separately.

## After adding 500 years

1. Verify `model execution success` / `case.run success` / `st_archive success` for each five-year segment, especially the first six under the corrected launcher.
2. Verify the complete coordinated restart at each site's expected 1000-year checkpoint.
3. Re-run **carbon-pool convergence** diagnostics at 500 vs 1000 model years using seasonal/cycle-matched comparisons, including `TOTECOSYSC` and slow vegetation/soil carbon pools where present. A further 500 years does **not** guarantee a steady state, and poor EC GPP/NEE fit cannot automatically be solved by longer spin-up.
4. Do not commit raw tower flux packages, NetCDF model outputs/restarts, or raw cluster logs to the public repository. Only commit reviewed scripts and documentation.

References: `examples/FLUXNET_MultiSite_6/README.md`, `examples/FLUXNET_MultiSite_6/scripts/09_submit_six_site_spinup500.sh`, `examples/FLUXNET_GF-Guy/scripts/16_extend_spinup300_to500.sh`, and repository root `IRIDIS6_MPI_CPU_AFFINITY.md`.

## First continuation jobs reported on 2026-10-14

The six-site extension was already submitted by the researcher. The first continuation model job IDs were: DE-Hai 4237364, RU-Fyo 4237366, DE-Tha 4237368, DK-Sor 4237370, NL-Loo 4237372, and IL-Yat 4237374. At the latest reported status, these were either RUNNING or PENDING; no 1000-year completion was established. Never repeat the `prepare` or `submit` commands while those six cases are active.

To monitor an active extension without changing any model files:

```bash
bash ~/13_extend_six_site_spinup500_to1000.sh status
squeue -u ly3n24 -o '%.12i %.36j %.10T %.12M %.12l %R'
sacct -j 4237364,4237366,4237368,4237370,4237372,4237374 -X --format=JobID,JobName%36,State,Elapsed,AllocCPUS,NodeList
```

For MPI-core diagnosis, compare `scontrol show job -dd JOBID` (`CPU_IDs`) with the actual `cesm.exe` process's `/proc/PID/status` (`Cpus_allowed_list`) on its node. One CPU allocated to each Slurm job is necessary but not sufficient evidence that the launched MPI rank stayed within its allocation. See [the root IRIDIS6 MPI troubleshooting guide](../../../IRIDIS6_MPI_CPU_AFFINITY.md).
