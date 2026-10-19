# Five-site 1000–3000-year spin-up: Scratch inode-quota interruption and recovery (19 October 2026)

## Scope and evidence
Five existing cases: RU-Fyo, DE-Tha, DK-Sor, NL-Loo, IL-Yat; DE-Hai is excluded. Original CIME names remain `<SITE>_FATES_SPINUP500`, even while running to 3000 model years. The October 18 failure was **Scratch file-count quota exhaustion**, not evidence of a science-model instability: `myfiles` showed **614,400 / 614,400 Scratch files** although disk usage was approximately 629 / 2,000 GB. CESM/ParallelIO reported `Disk quota exceeded`, and CIME also encountered Git `.git/index.lock` creation problems. Slurm `st_archive` jobs showed `DependencyNeverSatisfied` following failed upstream runs. This does not mean all earlier restart checkpoints failed.

The operator reports that the file-count issue was addressed and model histories backed up using the Research Filestore procedure. **Transfer verification, exact live quotas, restart repair, successful resumed Slurm submissions, and eventual 3000-year completion are not established by these messages.** GitHub stores code, documents, and small figures, not the NetCDF model restarts.

## Read-only recovery preflight observed on IRIDIS6

Output from `python3 ~/resume_five_site_3000_safely.py check` (19 October 2026):

| Site | Latest archived checkpoint (elapsed model years) | Remaining to 3000 | Reported pre-repair condition |
|---|---:|---:|---|
| RU-Fyo | 1070 | 1930 | All three run pointers differ; 4 unarchived h* NetCDFs |
| DE-Tha | 1065 | 1935 | All three run pointers differ; 8 unarchived h* NetCDFs |
| DK-Sor | 1070 | 1930 | All three run pointers differ; 6 unarchived h* NetCDFs |
| NL-Loo | 1065 | 1935 | All three run pointers differ; 6 unarchived h* NetCDFs |
| IL-Yat | 1105 | 1895 | All three run pointers differ; 4 unarchived h* NetCDFs |

All five showed `BLOCKED`: model-run pointers `rpointer.cpl`, `rpointer.atm`, and `rpointer.lnd` differed from the most recent archived checkpoint; partial history NetCDF files remained in the active `run/` directories. These are recoverable *candidates*, not evidence that the pointers or later states are corrupted. Check for newer valid coordinated restarts before any rollback.

## Recovery strategy and files

- Prior continuation: [20 one-click initialization](../scripts/20_five_site_spinup1000_plus2000_oneclick.sh) and [21 generated CIME continuation](../scripts/21_five_site_spinup1000_to3000_generated.sh). **Do not rerun the one-click `all` operation** on submitted cases.
- Recovery helper: `recover_five_site_spinup3000_after_quota.py` (first distributed to IRIDIS Home). This is an **operator-review recovery script**, not proof of execution.
- `inspect` is read-only. `repair` is designed to snapshot CIME configuration, save failed-segment output to `recovery_backups/five_site_1000to3000/post_inode_recovery/`, and restore coordinated ATM/LND/CPL restarts/pointers from the latest valid archive. `submit SESSION` separately attempts existing `case.submit` once for each repaired case. The original CO2, forcing, surface, model executable, case name, and CIME RESUBMIT state must be preserved.
- Before `repair`, manually verify the most recent **complete** coordinated restart and Slurm/CaseStatus; do not roll back if a newer valid restorable restart exists. Verify source and staged hashes. Do not delete history NetCDFs or restart pointers.
- Verify inode headroom with `myfiles`, no live jobs with `squeue -u ly3n24`, and latest `CaseStatus` with `tail -n 30`.
- A successful `case.submit` only queues a job: confirm `sacct`, `CaseStatus`, and the next archived checkpoint before claiming restoration success.
- To achieve 3000 total years, retain five-year model segments and case original start dates. The required remaining segments from the observed checkpoints are 386, 387, 386, 387, and 379 respectively. CIME resubmission counts must be reconciled with whether the next submission is counted; **never reset to 399**.

## Safe operator commands

```bash
myfiles
squeue -u ly3n24 -o '%.12i %.55j %.10T %R'
python3 ~/resume_five_site_3000_safely.py check
python3 ~/recover_five_site_spinup3000_after_quota.py inspect
# Only after human review of the five cases and most recent coordinated restarts:
# python3 ~/recover_five_site_spinup3000_after_quota.py repair
# python3 ~/recover_five_site_spinup3000_after_quota.py submit SESSION_PATH
```

**Important implementation caution:** the initial recovery helper should be treated as an archived candidate and independently audited before execution. In particular, verify it recognizes all component restart filenames and does not submit twice or overwrite unsaved work.

## Evidence still needed

Store an anonymized per-site recovery record with selected checkpoint stamp, sha256 manifests, before/after pointer targets, `RESUBMIT`, Slurm run/archive IDs, CaseStatus model/archive successes, and the next completed checkpoint. Record success only after these checks. See [Research Filestore retention guide](../../../docs/research_filestore/FLUXNET_MultiSite_6.md).
