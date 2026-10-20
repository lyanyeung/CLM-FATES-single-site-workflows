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

## 20 October follow-up: observed 13-site checkpoint inventory and missing runtime pointers

Read-only Stage37 inspection on IRIDIS6 found **all 13 archived checkpoints**, but all cases were initially blocked because active `run/rpointer.cpl`, `run/rpointer.atm`, and `run/rpointer.lnd` were missing. These runtime pointers are not required to persist in `run/` after successful short-term archival; they may be reconstructed **only from verified coordinated archived component restarts and dated archived pointers**.

| Site | Archived elapsed model years | Remaining | Unarchived h* files |
|---|---:|---:|---:|
| DE-Lnf | 50 | 950 | 6 |
| DE-Obe | 40 | 960 | 6 |
| ES-Agu | 40 | 960 | 10 |
| ES-LJu | 40 | 960 | 2 |
| IT-Col | 40 | 960 | 2 |
| DE-Gri | 40 | 960 | 6 |
| DE-RuR | 40 | 960 | 4 |
| FI-Hyy | 40 | 960 | 6 |
| FI-Let | 40 | 960 | 0 |
| FR-Pue | 55 | 945 | 8 |
| GF-Guy | 40 | 960 | 2 |
| IT-MBo | 35 | 965 | 2 |
| IT-Tor | 50 | 950 | 8 |

**DE-Lnf also has a separately observed incorrect/unvalidated `MPI_RUN_COMMAND`.** Stage37 was amended so missing active pointers are an expected, recoverable condition; `prepare SITE` records missing original pointers and creates them from the verified archived restarts. A guarded **`fix-mpi DE-Lnf`** command is provided to back up CIME files and correct only the launcher, without resubmitting.

**Required sequence**:

```bash
cd ~/CLM-FATES-single-site-workflows
git fetch origin main
# Retrieve the script as an exact remote blob without merging unrelated work:
SCRIPT=examples/FLUXNET_MultiSite_13/scripts/stage37/37_recover_13site_spinup1000_after_inode_quota.py
git show "origin/main:$SCRIPT" > "$SCRIPT"
python3 -m py_compile "$SCRIPT"
python3 "$SCRIPT" inspect
```

Only after the full `inspect` output confirms archived restart components, `RESUBMIT` and Slurm status, correct DE-Lnf launcher separately with `python3 "$SCRIPT" fix-mpi DE-Lnf`, then re-inspect. Use one-site `prepare SITE` and `submit SESSION` with checks between the two stages. **Do not batch-submit all 13 sites from this snapshot**; neither SHA256 verification nor actual restart execution has yet been established. This historical status snapshot is not proof of resumed simulation.

## 20 October: eleven sites prepared; DE-Lnf memory allocation unresolved

The operator reported eleven additional successful Stage37 `prepare` sessions: DE-Obe, ES-Agu, ES-LJu, IT-Col, DE-Gri, DE-RuR, FI-Hyy, FR-Pue, GF-Guy, IT-MBo and IT-Tor. FI-Let had already been prepared separately at 40 elapsed model years. These **PREPARED** states mean that restart staging and backup completed; they are **not** evidence of Slurm re-submission or a newly completed five-year segment.

A separate batch audit reported all listed sites PASS except **DE-Lnf**, where both `.case.run` and `case.st_archive` lacked the required `#SBATCH --mem=8G`. DE-Lnf's `MPI_RUN_COMMAND` was already corrected to the PMIx `srun` command, and `CONTINUE_RUN=TRUE`, `RESUBMIT=189`, `BUILD_COMPLETE=TRUE` were observed.

[Stage38 DE-Lnf memory repair](../scripts/stage38/38_fix_DE_Lnf_batch_memory_after_quota.py) addresses this as a distinct, guarded operation. `audit` is read-only; `repair` backs up the CIME batch/environment files, updates authoritative `env_batch.xml`, regenerates batch scripts via `case.setup --reset`, validates both model/archive 1CPU/8G/nonexclusive settings, and checks existing scientific configuration, executables and launcher. It does not submit jobs or modify RESUBMIT. If CIME regeneration or executable provenance fails, stop and inspect backups rather than editing generated batch files ad hoc.

```bash
cd ~/CLM-FATES-single-site-workflows
git fetch origin main
SCRIPT38=examples/FLUXNET_MultiSite_13/scripts/stage38/38_fix_DE_Lnf_batch_memory_after_quota.py
mkdir -p "$(dirname "$SCRIPT38")"
git show "origin/main:$SCRIPT38" > "$SCRIPT38"
python3 -m py_compile "$SCRIPT38"
python3 "$SCRIPT38" audit
# After reading audit and verifying no active DE-Lnf Slurm jobs:
# python3 "$SCRIPT38" repair
# python3 examples/FLUXNET_MultiSite_13/scripts/stage37/37_recover_13site_spinup1000_after_inode_quota.py inspect
```

**Operator policy:** verify FI-Let's next five-year model execution and archive first, then submit the other individually prepared sessions exactly once and only after re-checking their Slurm status. No 1000-year completion or successful post-repair submission has been demonstrated by the reported output.

## 20 October: all thirteen recovery sessions prepared; runtime result pending

Follow-up operator log confirms **DE-Lnf** also completed Stage37 `prepare`, from the **50 elapsed model-year** archived checkpoint:

```text
SESSION=/scratch/ly3n24/CTSM_FATES_OUTPUTS/recovery_backups/FLUXNET_MultiSite_13/post_inode_quota/DE-Lnf_epyk79yt
PREPARED DE-Lnf: archived checkpoint at 50 years
```

This is in addition to FI-Let and the eleven other Stage37-prepared cases. Therefore **13/13 sites have a reported PREPARED restart recovery session**. The complete source scripts are in GitHub, while CIME cases and restart files remain on IRIDIS6/Scratch or dedicated backup storage; committing code does not store the restart datasets.

**Do not infer job success from PREPARED.** At this checkpoint there is no supplied proof that all 13 `case.submit` calls succeeded, reached `RUNNING` or completed their next 5-year/archive cycles, and no verified 1000-year outcomes. Check `SUBMIT_ATTEMPTED` and `submit.log` in each session, `squeue`, `sacct`, `CaseStatus`, latest coordinated archived restart, and `myfiles` inode usage. Do not rerun an attempted submit solely because it disappeared from `squeue`. Resubmission after a model segment requires a matching successful archive and valid updated CIME state.

DE-Lnf pre-preparation configuration evidence: `CONTINUE_RUN=TRUE`, `RESUBMIT=189`, `BUILD_COMPLETE=TRUE`, corrected PMIx launcher. Its run/archive batch files were initially missing `--mem=8G`. Successful Stage37 prepare with the latest batch-directive validation indicates this blocker was cleared before preparation; the exact Stage38 repair log has not been independently provided.
