# IRIDIS6 CLM-FATES: eight-site MPI affinity repair and checkpoint-safe continuation

**Date:** 2026-10-14 (Europe/London)  
**Scope:** eight unfinished 500-year FLUXNET CIME cases on IRIDIS6. This is a case-specific research incident record, not an IRIDIS6-wide diagnosis.  
**Primary script:** [`../scripts/12_resume_eight_site_srun_pmix500.sh`](../scripts/12_resume_eight_site_srun_pmix500.sh).  
**Generic tests and interpretation:** [root IRIDIS6 MPI guide](../../../IRIDIS6_MPI_CPU_AFFINITY.md).

## Executive summary

An earlier resource repair removed two `--exclusive` Slurm directives. The eight one-rank model jobs were allocated **1 CPU and 8 GiB each** rather than 192 allocated CPUs per job. However, their CIME launch remained `mpirun -n 1 --bind-to core --map-by socket cesm.exe`. Eight model jobs scheduled together on node `red6082` ran for a full hour and timed out; two inspected model logs showed continued scientific simulation through spring 2048, rather than a hung model. Subsequent affinity tests demonstrated that two independent Slurm jobs received distinct CPUs, while the legacy OpenMPI launcher reset their child affinity to CPU 0 in both trials. Switching to `srun --mpi=pmix --cpu-bind=cores` preserved separate Slurm CPU allocations in a test with real `MPI_Init`. A five-year IT-Ren CLM-FATES continuation completed and archived successfully with that corrected CIME launcher.

**A passed single-site IT-Ren test does not certify all eight 500-year runs, all eight concurrent run times, spin-up convergence, or scientific forcing correctness.**

## Reconstructed failure timeline

| Event | Evidence |
|---|---|
| Excessive resource reservation | Original eight runs had 192 AllocCPUS because of two inherited `--exclusive` directives, despite 1 MPI task and 1 thread |
| Single-core, nonexclusive test | IT-Ren job `4143672` COMPLETED in 00:08:21; archive `4143673` COMPLETED; one core, 8 GiB |
| Eight independent concurrent models | `4147672`, `4147674`, `4147676`, `4147678`, `4147680`, `4147682`, `4147684`, `4147686` all on `red6082` |
| Failure | All eight `TIMEOUT`, each `Elapsed=01:00:19`, `Timelimit=01:00:00`; dependent archives `4147673`–`4147687` (odd IDs) reported `DependencyNeverSatisfied` |
| Proof of ongoing simulation | IT-Ren `atm.log` reached 2048-05-20, CZ-BK1 2048-04-06 in the restarted 2044–2049 segments |
| Legacy launcher test | Two different jobs on `red6129`: Slurm allowed CPUs 63 and 16, while legacy `mpirun` children both showed `Cpus_allowed_list: 0` |
| Corrected launcher test | Two different jobs on `red6087`: Slurm allowed CPUs 71 and 110, and `srun --mpi=pmix` MPI ranks used 71 and 110, respectively |
| Real CLM-FATES validation | IT-Ren `4232435`: `model execution success` at 01:28:31 after starting 01:20:19; `4232436`: `st_archive success` at 01:29:31 |
| New verified checkpoint | IT-Ren `2049-01-01-00000`, 50/500 model years completed |

`TotalCPU` around 1.5 seconds in the timed-out batch accounting is **not** proof that `cesm.exe` only ran for 1.5 seconds. The advancing atmosphere and land logs demonstrate work continued. Similarly, `--bind-to core` is not generally wrong in every OpenMPI/Slurm installation; this report concerns the actual combination observed on IRIDIS6.

## Root cause and corrected architecture

Two independent problems must not be confused:

1. **Allocation:** inherited `--exclusive` consumed a whole 192-core node per single-rank job. The historical [shared-node document](shared_node_resume_2026-10-13.md) describes removal and CIME batch-script regeneration. Each job subsequently correctly requested `--nodes=1`, `--ntasks-per-node=1`, `--cpus-per-task=1`, `--mem=8G`, with no `--exclusive`.
2. **Binding:** the historical CIME launch `mpirun -n 1 --bind-to core --map-by socket` could bind the launched process to a CPU **outside** its parent Slurm `Cpus_allowed_list` (observed CPU 0). This is direct evidence of an affinity mismatch under the tested configuration; the eight-run performance collapse is strongly consistent with core contention, but identical per-rank affinity for all eight historical model processes was not separately recorded.

CIME supports a case-local override, preserving the compiled executable:

```bash
cd /iridisfs/scratch/ly3n24/CLM_FATES/cases/IT-Ren_FATES_SPINUP500

# In a stopped/idle case only:
./xmlchange 'MPI_RUN_COMMAND=srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores'
./preview_run
```

`preview_run` should display an `MPIRUN (job=case.run)` line beginning with the new `srun` command. There is **no need** to directly overwrite `env_mach_specific.xml`, rebuild `cesm.exe`, recreate case directories, or change scientific inputs merely to override the launcher.

The tested 5-year continuation also used `RESUBMIT=0` so the trial could not automatically chain hundreds of years; the batch recovery program restores per-site `RESUBMIT` counts only after every site passes preparation.

## Oct 14 snapshot and remaining work

| Site | Original start | Latest full archive after IT-Ren trial | Completed model years | Remaining 5-year jobs | RESUBMIT |
|---|---:|---|---:|---:|---:|
| CZ-BK1 | 2004 | 2044-01-01 | 40 | 92 | 91 |
| IT-Ren | 1999 | 2049-01-01 | 50 | 90 | 89 |
| FR-Hes | 1997 | 2032-01-01 | 35 | 93 | 92 |
| FR-FBn | 2008 | 2043-01-01 | 35 | 93 | 92 |
| DE-Hzd | 2010 | 2045-01-01 | 35 | 93 | 92 |
| CH-Dav | 1997 | 2032-01-01 | 35 | 93 | 92 |
| BE-Vie | 1996 | 2031-01-01 | 35 | 93 | 92 |
| IT-Lav | 2003 | 2038-01-01 | 35 | 93 | 92 |

The script discovers current checkpoints on every audit rather than hardcoding these as final values. The model's original `RUN_STARTDATE` differs from its **current continuation** date; CIME obtains the latter from coordinated restart files and pointers.

The recovery program is intentionally site-specific: it asserts site identity, start date, forcing/cycle setup indirectly through unchanged case config and scientific file hashes, site constant CO₂, `NO_LEAP`, `ATM_NCPL=48`, one MPI task/thread, five-year STOP/REST, and an existing shared `EXEROOT/cesm.exe`. Its archived pointers may include Fortran-style trailing padding or `./`; `pointer_ref()` normalizes these safely and ensures every corresponding `cpl/datm/clm2` NetCDF exists.

### Execute on IRIDIS6

```bash
# The script should already be copied from this repo to your IRIDIS6 home.
SCRIPT=~/12_resume_eight_site_srun_pmix500.sh
bash -n "$SCRIPT"
bash "$SCRIPT" audit

set -o pipefail
bash "$SCRIPT" prepare 2>&1 | tee ~/fates_eight_srun_prepare.log

SESSION=$(grep '^SESSION=' ~/fates_eight_srun_prepare.log | tail -1 | cut -d= -f2-)
test -f "$SESSION/PREPARED" || { echo "NOT PREPARED"; exit 1; }
cat "$SESSION/manifest.tsv"

# Submit only once and only after inspecting manifest and verifying no active duplicate jobs.
bash "$SCRIPT" submit "$SESSION"

# Safe to run while jobs are active:
bash "$SCRIPT" status
```

### Preparation failure that was caught and fixed

The first `prepare` attempt (session `fates_eight_srun_20261014_014027_413623`) failed at the Bash pipeline:

```text
tee: .../cases/CZ-BK1/prepare.log: No such file or directory
```

Because `tee` started before `prepare_site` created its directory, the wrapper failed even though CZ-BK1 had already backed up **10** partial history files, staged its archived 2044 restart and set `MPI_RUN_COMMAND`. No job was submitted. The corrected script explicitly runs `mkdir -p "$SESSION/cases/$site"` **before** the pipeline. The original backup should be preserved; a fresh `audit` and a new `prepare` session avoid replaying a partially written session.

### Safety and verification

- **Never** submit on active/running or queued target cases; **never** rerun `09_eight_site_spinup500.sh` against these existing case folders.
- `audit`: read-only checks; `prepare`: backs up and modifies case configuration/restaging, but submits zero jobs; `submit SESSION`: validates the manifest, then submits once; `status`: read-only progress.
- `PREPARED` is not `COMPLETED`. The marker only proves that the preparation phase finished. Success of an individual 5-year segment requires `model execution success`, `case.run success`, `st_archive success`, and a coherent archived restart date and component files.
- `--time=01:00:00` limits **each** 5-year job, **not** the entire 500 model years. Monitor first concurrent `srun` jobs for any renewed oversubscription/timeouts.
- Keep all backup directories and restart archives until full validation; the script does not back up all NetCDF files off-site. No institutional backup is implied.
- Check carbon-pool trends and steady-state criteria separately after enough model years; 500-year target is **not** proof of convergence.

## Related documentation

- [Standalone IRIDIS6 MPI/Slurm affinity diagnosis](../../../IRIDIS6_MPI_CPU_AFFINITY.md)
- [Legacy shared-node fix, historical record](shared_node_resume_2026-10-13.md)
- [Original eight-site experiment build/submission](spinup500_submission.md)
- [Original eight-site stage-07 code](../scripts/09_eight_site_spinup500.sh)
- [Current recovered eight-site program](../scripts/12_resume_eight_site_srun_pmix500.sh)
