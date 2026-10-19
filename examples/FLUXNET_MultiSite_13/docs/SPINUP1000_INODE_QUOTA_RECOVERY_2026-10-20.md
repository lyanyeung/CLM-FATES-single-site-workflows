# Stage 37 — recover thirteen existing 1000-year spin-ups after IRIDIS6 inode quota exhaustion

**Recorded 20 October 2026. Recovery implementation committed; runtime recovery has NOT been confirmed.**

## Cause and scope

On 18–19 October, IRIDIS6 Scratch had reached its **per-user file-count quota of 614,400 files**, despite usable byte capacity. CESM ParallelIO logged `Disk quota exceeded`, and some CIME Git writes failed with index-lock errors. The associated Slurm archive jobs appeared as `DependencyNeverSatisfied` because their prerequisite model jobs did not succeed. These archive-dependency errors do not show how many prior five-year model segments succeeded. The same storage incident affected other campaigns; **per-site failure causality must still be verified from `cesm.log`, `CaseStatus` and `sacct`**.

This recovery is restricted to 13 existing CIME cases with suffix `_FATES_SPINUP1000_S30SHARED`: DE-Lnf, DE-Obe, ES-Agu, ES-LJu, IT-Col, DE-Gri, DE-RuR, FI-Hyy, FI-Let, FR-Pue, GF-Guy, IT-MBo, IT-Tor. Do not confuse these with the earlier `_S30EXCL` family or rerun Stage31–36 fresh-start scripts. The experiment retains 5-year segments, `NO_LEAP`, half-hourly DATM forcing, fixed site-specific CO2, the original surface and GF-Guy-linked executable. The overall target is **1000 elapsed model years**, not calendar year 1000. Full scientific convergence still needs independent evaluation.

## Stage37 source

[37_recover_13site_spinup1000_after_inode_quota.py](../scripts/stage37/37_recover_13site_spinup1000_after_inode_quota.py)

The code has three explicit modes:

- `inspect`: read-only scan of all 13 cases; shows elapsed model years from the latest archived `rest/YYYY-01-01-00000` checkpoint, remaining years, job state and blockers.
- `prepare SITE`: one-site guarded operation, permitted only if all invariants pass. Snapshots CIME inputs and run pointers, moves potentially incomplete later history/restart files into a separate backup session, stages last archived coordinated CPL/ATM/LND checkpoint, checks SHA-256. Does **not** change XML, reset RESUBMIT, remove data, submit work or cancel jobs.
- `submit SESSION_DIRECTORY`: one attempt at `./case.submit` for that prepared case, after checking no active Slurm jobs, case state and checkpoint hashes. A durable `SUBMIT_ATTEMPTED` marker prevents casual retry if Slurm submission is ambiguous.

**Conservative blocks** include: missing archived restarts, unknown case directories or Slurm jobs, later successful model than archive, newer coordinated restarts that might be preserved instead of rolling back, mismatched RESUBMIT/CONTINUE_RUN, unexpected model-clock date, missing or wrong component restart pointers, and CIME configurations different from the validated shared-node PMIx configuration.

A few original runs may have failed during their first 5-year segment. Stage37 **does not automatically restart a zero-year case**, because restart semantics differ from continuation. First inspect that case manually.

## Runbook on IRIDIS6

```bash
cd ~/CLM-FATES-single-site-workflows
git pull --ff-only origin main
myfiles
squeue -u ly3n24 -o '%.12i %.60j %.10T %R'
python3 -m py_compile examples/FLUXNET_MultiSite_13/scripts/stage37/37_recover_13site_spinup1000_after_inode_quota.py
python3 examples/FLUXNET_MultiSite_13/scripts/stage37/37_recover_13site_spinup1000_after_inode_quota.py inspect
```

Read all blocker messages and inspect component logs/checkpoints. In particular, **do not treat a pending `st_archive` dependency error as permission to drop a newer successful checkpoint**.

Once a specific site has been independently verified safe, prepare **one site**:

```bash
python3 examples/FLUXNET_MultiSite_13/scripts/stage37/37_recover_13site_spinup1000_after_inode_quota.py prepare DE-Lnf
```

This prints a unique `SESSION=/scratch/...` path. Examine the new manifest, isolated files, case snapshots, and run pointers before submitting:

```bash
python3 examples/FLUXNET_MultiSite_13/scripts/stage37/37_recover_13site_spinup1000_after_inode_quota.py submit /scratch/.../DE-Lnf_SESSION_PATH
```

The placeholder above must be replaced with the exact printed session path. **Do not run the submit command until the inspection and the prepared snapshot are validated.** After a successful Slurm submission, validate the next model run, archive, and actual new restart date before repeating on other sites.

## Slurm cleanup

Archive jobs pending with `DependencyNeverSatisfied` should be identified by **full** job name (not truncated `squeue` output) and linked case. Stale jobs can be individually cancelled after evidence preservation, but **never use `scancel -u ly3n24`** or cancel tasks belonging to other 6/8/11-site experiments. Stage37 never calls `scancel`. Clear stale case-specific jobs separately and re-run `inspect` before preparing.

## Audit trail and result integrity

Record per-site selected checkpoint, the sha256s of all three archived component restarts, the original and restored pointers, original `RESUBMIT`, Slurm job IDs and status, `CaseStatus` model/archive success messages, subsequent archived checkpoint and numerical convergence diagnostics. Keep source model NetCDF, licensed tower data and internal logs off GitHub. Only the reusable source, workflow explanation and non-sensitive summaries should be published.

**Status:** Stage37 source and plan are documented here; neither actual restoration nor 1000-year completion has been established by the information available at publication.
