# Eight-site CLM-FATES spin-up: recovery using shared Slurm nodes

> **Historical configuration (2026-10-13); superseded for future concurrent restarts.** This document explains removal of Slurm `--exclusive`, but the original `mpirun --bind-to core --map-by socket` still allowed competing CPU affinity. The eight-run batch described below **timed out after one hour** and its archive dependencies could not run. Use [the corrected `srun --mpi=pmix` recovery](srun_pmix_resume_2026-10-14.md) and [current script `12_resume_eight_site_srun_pmix500.sh`](../scripts/12_resume_eight_site_srun_pmix500.sh) instead. Keep this document as incident history, not current operational instructions.

**Project:** `CLM-FATES-single-site-workflows`  
**Date:** 2026-10-13 (Europe/London)  
**Scope:** ONLY the eight unfinished `<SITE>_FATES_SPINUP500` cases in `examples/FLUXNET_MultiSite_8`. Do not rerun the original Stage 07 creation/submission script. The other six sites in `FLUXNET_MultiSite_6` finished their spin-ups and are **out of scope**.

## Background and evidence

The eight runs were cloned from `GF-Guy_FATES_SURF2000_CO2405_1PT` via CIME `create_clone --keepexe`. They use their own surface/forcing/CO2, `RUN_TYPE=startup` (original case type), `CONTINUE_RUN=TRUE` after initial segment, `NO_LEAP`, `ATM_NCPL=48`, and 100 × 5-year segments for 500 total model years. Each site's meteorological cycling window is distinct from its 5-year CIME job segment. These model/forcing settings must remain unchanged.

The inherited IRIDIS6 batch configuration had **two** `--exclusive` entries, resulting in allocation of 192 CPU cores per run job while the case's MPI and OpenMP layout remained `NTASKS=1`, `NTHRDS=1`. Across eight completed 5-year jobs, Slurm `TotalCPU/Elapsed` was ~0.98–0.99 CPU cores and `.batch` MaxRSS was ~1.7 GiB. A separate nonexclusive Slurm allocation test, job `4140300`, completed with `AllocCPUS=1` and `ReqMem=4G`.

One representative 5-year continuation of **IT-Ren** was submitted after repairing CIME's locked `env_batch.xml` via `./case.setup --reset`: model job **4143672** and archive job **4143673**, configured for one core and 8 GiB of RAM, without `--exclusive`. Slurm reported `4143672` as `RUNNING` with **1 allocated core**. **This record does not claim job completion:** before batch recovery, verify both jobs and the new IT-Ren `2044-01-01-00000` restart succeeded.

## Site baselines and unchanged scientific inputs

| Site | Initial model year | Forcing cycle | CO2 (ppm) | Paused checkpoint | Completed years at pause |
|---|---:|---|---:|---|---:|
| CZ-BK1 | 2004 | 2004–2025 | 376.95 | 2044-01-01 | 40 |
| IT-Ren | 1999 | 1999–2025 | 367.80 | 2039-01-01 | 40 |
| FR-Hes | 1997 | 1997–2025 | 363.04 | 2032-01-01 | 35 |
| FR-FBn | 2008 | 2008–2024 | 385.02 | 2043-01-01 | 35 |
| DE-Hzd | 2010 | 2010–2025 | 388.75 | 2045-01-01 | 35 |
| CH-Dav | 1997 | 1997–2025 | 363.04 | 2032-01-01 | 35 |
| BE-Vie | 1996 | 1996–2025 | 361.93 | 2031-01-01 | 35 |
| IT-Lav | 2003 | 2003–2020 | 375.14 | 2038-01-01 | 35 |

After successful IT-Ren test, it should be at model year `2044-01-01`, with 45/500 completed. The resume script derives the **current** checkpoint and calculates the remaining 5-year segments dynamically; it does not assume all sites remain at the dates in the table.

## Actual changes required

1. **Keep model inputs and scientific configuration unchanged:** site-specific forcing cycle, surface, FATES namelists, atmospheric CO2, calendar, build executable, and `STOP_N=REST_N=5`.
2. **Modify each affected case's `env_batch.xml`** to remove both `<directive>--exclusive</directive>` entries and insert exactly one `<directive>--mem=8G</directive>` while preserving `--cpus-per-task={{ thread_count }}`.
3. For cases whose Slurm scripts are still exclusive, execute `./case.setup --reset` on an **idle** case so that the locked CIME batch settings and regenerated `.case.run`/`case.st_archive` agree. `case.setup --reset` may clear `BUILD_COMPLETE`; restore it to `TRUE` **only after verifying the original `EXEROOT/cesm.exe` still exists and the EXEROOT and MPI library have not changed**. No `case.build` or new CIME clone is required.
4. Stage the newest **successfully archived** coordinated restart (three components: `cpl`, `datm`, `clm2`) from `<ARCHIVE>/rest/<STAMP>` into the site-specific RUNDIR, including its dated and generic `rpointer.cpl`, `rpointer.atm`, and `rpointer.lnd`. Never mix station restart files. Preserve preexisting generic pointers in the session backup. Copy (do not delete) archived restart payloads.
5. Set `CONTINUE_RUN=TRUE`; set `RESUBMIT = (500 - completed_years)/5 - 1`, because `case.submit` starts the first remaining 5-year segment and `RESUBMIT` describes **additional** segments.
6. Verify model and archive batch files each request `--nodes=1`, `--ntasks-per-node=1`, `--cpus-per-task=1`, `--mem=8G` and contain no `--exclusive`, then submit each original case **once**.

## Recovery script and operation

Use `scripts/10_resume_shared_node_spinup500.sh`. It checks all eight station identities, scientific parameters, compiled executables, `CaseStatus`, archived pointers and NetCDFs, and the successful IT-Ren test. It saves a timestamped local session backup under `/home/ly3n24/fates_eight_shared_resume_*` with copied case XML, LockedFiles, CaseStatus, restart pointers, batch directives, per-site preparation logs, the checkpoint manifest, and submission logs. **It does not back up multi-year raw forcing or every history/restart NetCDF into home**; these remain on scratch and in the existing output archive. It separately preserves any detected unarchived history files that could be overwritten during replay.

On IRIDIS6:

```bash
conda activate clm_fates_env
bash -n ~/10_resume_shared_node_spinup500.sh

# Read-only review, after IT-Ren test is archived:
bash ~/10_resume_shared_node_spinup500.sh audit

# Recommended two-stage operation:
bash ~/10_resume_shared_node_spinup500.sh prepare \
  2>&1 | tee ~/eight_shared_prepare.log

# Set SESSION to the exact path printed at the end of 'prepare':
SESSION=/home/ly3n24/fates_eight_shared_resume_YYYYMMDD_HHMMSS_XXXXXX
bash ~/10_resume_shared_node_spinup500.sh submit "$SESSION" \
  2>&1 | tee ~/eight_shared_submit.log

# Alternative: a single guarded command, without calling prepare first:
# bash ~/10_resume_shared_node_spinup500.sh resume \
#   2>&1 | tee ~/eight_shared_resume.log
```

Do **not** run `resume` after a successful `prepare`/`submit` or after an initial submission. The script prevents reusing the same session and checks active Slurm jobs; if it halts with `STOP`, inspect its logs instead of bypassing checks.

## Expected counts after the IT-Ren test

| Site | Completed years | Remaining segment count | RESUBMIT |
|---|---:|---:|---:|
| CZ-BK1 | 40 | 92 | 91 |
| IT-Ren | 45 | 91 | 90 |
| FR-Hes | 35 | 93 | 92 |
| FR-FBn | 35 | 93 | 92 |
| DE-Hzd | 35 | 93 | 92 |
| CH-Dav | 35 | 93 | 92 |
| BE-Vie | 35 | 93 | 92 |
| IT-Lav | 35 | 93 | 92 |

These are **expected**, not a claim of completed work. The script recalculates from actual on-disk archived checkpoints and aborts on mismatches.

## Monitoring and acceptance criteria

```bash
squeue -u ly3n24 -o '%.12i %.36j %.10T %.8C %R'
sacct -u ly3n24 -S 2026-10-13 -X \
  --format=JobID,JobName%36,State,AllocCPUS,ReqMem,Elapsed
```

**Accept a 5-year segment as successful only when:** `case.run success` and `st_archive success` are recorded, the expected next checkpoint's component files and pointers exist in the station archive, and Slurm confirms the new run was allocated one CPU. Periodically inspect memory (`MaxRSS`) and actual wall time; for 500 years, the 8 GiB memory request should remain under review. This resource repair does **not** prove FATES carbon-pool convergence or correct forcing/PFT science.

## Previous failure analysis

- Initial `resume_8_fates_shared.sh` / v2: a Bash simultaneous `local` assignment used the previous site identity, making IT-Ren's test pick IT-Lav. It stopped at the site-specific pointer check, before submitting a model job. Fixed by separate assignments and exact CASE/RUNDIR/archive identity checks.
- v2: direct `from CIME.case import Case` in generic conda Python failed with `ModuleNotFoundError: No module named 'CIME'`, and editing locked `env_batch.xml` without `case.setup --reset` triggered `Detected diff in locked file`. Fixed by invoking the case's own CIME setup/reset after edits, and checking the reused compiled executable/build flag.
- A fresh `startup` run, rerunning `09_eight_site_spinup500.sh`, or rebuilding is **not** a valid way to resume these already-submitted cases.

## GitHub hygiene

Commit this script and documentation, not NetCDFs, user-specific logs, original model output, large scratch files, tokens or keys. Store actual CIME XML backups and restart archives on IRIDIS6 and/or a protected institutional backup system; GitHub is a code/documentation backup, not an HPC data backup.

## Original workflow references

- [`FLUXNET_MultiSite_8/scripts/09_eight_site_spinup500.sh`](../scripts/09_eight_site_spinup500.sh)
- [`FLUXNET_MultiSite_8/docs/spinup500_submission.md`](spinup500_submission.md)
- [`FLUXNET_MultiSite_6/scripts/09_submit_six_site_spinup500.sh`](../../FLUXNET_MultiSite_6/scripts/09_submit_six_site_spinup500.sh)
- [`FLUXNET_GF-Guy/scripts/16_extend_spinup300_to500.sh`](../../FLUXNET_GF-Guy/scripts/16_extend_spinup300_to500.sh)

## Verified eight-site shared-node execution (2026-10-13)

The previous IT-Ren continuation test completed successfully:

- Run job: 4143672 — COMPLETED, AllocCPUS=1, ReqMem=8G.
- Archive job: 4143673 — COMPLETED, AllocCPUS=1, ReqMem=8G.
- Run wall time: 00:08:21.

All eight unfinished spin-ups were subsequently resumed using
their existing CIME cases and archived restart checkpoints.

| Site | Run Job ID | Archive Job ID |
|---|---:|---:|
| CZ-BK1 | 4147672 | 4147673 |
| IT-Ren | 4147674 | 4147675 |
| FR-Hes | 4147676 | 4147677 |
| FR-FBn | 4147678 | 4147679 |
| DE-Hzd | 4147680 | 4147681 |
| CH-Dav | 4147682 | 4147683 |
| BE-Vie | 4147684 | 4147685 |
| IT-Lav | 4147686 | 4147687 |

At verification, all eight model jobs were RUNNING on node red6082,
each with 1 allocated CPU. Archive jobs were pending on dependencies.

Each case requests 1 CPU and 8 GB RAM without Slurm --exclusive.

This verifies successful shared-node scheduling, not completion
of the eight 500-year simulations or carbon-pool convergence.
