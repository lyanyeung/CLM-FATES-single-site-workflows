# IRIDIS6 maintenance tools

Utilities for checking and maintaining existing CLM-FATES experiments. **Monitoring is read-only; it does not submit, cancel, restart, or clean any jobs.**

## Four-batch spin-up status checker

[`check_four_spinups.py`](check_four_spinups.py) reproduces the detailed four-batch operator table covering:

- `FLUXNET_MultiSite_6` — 6 sites (five continuation cases to 3000 years; DE-Hai is a separate 1000-year target).
- `FLUXNET_MultiSite_8` — 8 sites (seven 1000-year targets, FR-Hes 500).
- `FLUXNET_MultiSite_11` — 11 sites (1000-year targets).
- `FLUXNET_MultiSite_13` — 13 sites (1000-year targets).

### Run on IRIDIS6 (recommended: works even if the local clone is missing files)

The Python checker **exists in GitHub's `main` branch**, but it is **not guaranteed to be installed in `~/CLM-FATES-single-site-workflows` on IRIDIS6**. GitHub and the IRIDIS6 working copy are separate. In particular, an unresolved local Git merge prevents `git pull`, and running `python3 maintenance/check_four_spinups.py` will fail with `No such file or directory` until that file is present locally.

**Recommended: download a fresh, read-only checker to a separate Home folder; no `git pull` required. Run this from any IRIDIS6 directory:**

```bash
mkdir -p "$HOME/CLM_FATES_maintenance"
curl --fail --location --show-error --silent --retry 3 \
  "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/maintenance/check_four_spinups.py" \
  --output "$HOME/CLM_FATES_maintenance/check_four_spinups.py" &&
python3 "$HOME/CLM_FATES_maintenance/check_four_spinups.py"
```

To retain a timestamped log **after downloading**:

```bash
python3 "$HOME/CLM_FATES_maintenance/check_four_spinups.py" \
  | tee "$HOME/four_spinups_status_$(date +%Y%m%d_%H%M%S).log"
```

The optional in-repository command below only works after confirming the file exists in that *particular IRIDIS6 working tree*. The GitHub web page alone does not establish local availability:

```bash
test -f "$HOME/CLM-FATES-single-site-workflows/maintenance/check_four_spinups.py" &&
python3 "$HOME/CLM-FATES-single-site-workflows/maintenance/check_four_spinups.py"
```

For a single batch:

```bash
python3 "$HOME/CLM_FATES_maintenance/check_four_spinups.py" --batch FLUXNET_MultiSite_8
```

### Interpretation

Output: `SITE`, `DONE/TARGET`, `LEFT`, `CHECKPOINT`, `RESUB`, `SLURM` and `JOB IDs / NOTE`. The `DONE` figure comes from the latest dated archived checkpoint that has a nonempty CPL, DATM, CLM NetCDF restart file **and** a matching dated `rpointer` for each of the three components, not from a running job's progress. Unlike a full NetCDF scan, this is a fast structural check; file integrity and history continuity must be verified separately before moving/deleting any files or declaring scientific convergence.

- `RUNNING` or `PENDING`: active Slurm job(s); dependent archive tasks may be pending normally.
- `IDLE`: no matching current Slurm job; inspect the case before assuming completion.
- `REVIEW`: missing/incomplete latest checkpoint or last model success newer than the last archive success.
- `COMPLETE`: expected cumulative target has an archived three-component checkpoint and no matching queued job. This is **not** scientific convergence.

The script deliberately avoids `myfiles`, `ncdump`, recursive full-archive reads, and `git` commands so it is lightweight enough for operator checks. The older simple history audit remains at [`scripts/research_filestore/audit_four_batches_live.py`](../scripts/research_filestore/audit_four_batches_live.py), with its optional JSON output and 1000-year history-continuity checks.

### Unified main table: one monitored current case per site

The **default** `check_four_spinups.py` output now uses **one selected current CIME case per station** in the same four-batch table, including the two nonstandard 11-site experiments:

| Batch/site | Current monitored CIME case | Case label |
| --- | --- | --- |
| 11 / IT-Noe | `IT-Noe_ERA5_ABW_BRANCH2009` | `ERA5-BR` |
| 11 / CH-Aws | `CH-Aws_FATES_SPINUP1000_RH42A_V8_CONT2016` | `RH42A-V8` |
| All remaining sites | The established four-batch case names | `-` |

Each main-table row gives `SITE`, `CASE` label, `DONE/TARGET`, `LEFT`, the current case's three-component archived `CHECKPOINT`, `RESUB`, execution `PHASE`, and separate `MODEL` and `ARCHIVE` Slurm job IDs/states. `RUNNING`, `PENDING`, `ARCH_WAIT`, `ARCHIVING`, and `BLOCKED` are phase labels. A successful model run waiting for short-term archive remains `ARCH_WAIT`, not a new checkpoint.

**CH-Aws v8 branch continuation (updated 21 October 2026):** The main table now selects `CH-Aws_FATES_SPINUP1000_RH42A_V8_CONT2016` (Stage43) instead of failed RH34A/RH38A trials. This case uses Stage42 global 19-year QC1 RH sensitivity forcing v8. It branches from the RH34A 2016-01-01 restart after the 2006–2015 ten-year baseline, with a target of 1000 cumulative model years (990 remaining at submit; 198 five-year segments; original `RESUBMIT=197`). The special `10*/1000` display is **only the inherited, structurally verified RH34A restart baseline**, not an RH42A archived checkpoint. It requires the Stage43 provenance receipt, matching CIME branch metadata and all three archived source restarts. Once an RH42A archive exists, displayed progress comes from its own validated three-component archive. If provenance cannot be validated, progress remains unknown and notes flag the issue. Neither an active job nor a completed but unarchived segment adds years. First submitted Slurm pair was `4614961` (model) / `4614962` (archive); these are historical submission identifiers, not a claim of current status. Run the checker for live Slurm state.

**Progress caveat for IT-Noe:** A `branch` case's `DONE` is the elapsed model-clock years since its own `RUN_STARTDATE` (e.g. 2014 minus 2004 = 10); those are *not* necessarily the years independently simulated since a 2009 branch restart. The script also displays `BRANCH_YEARS` when `RUN_REFDATE` can be read, and otherwise marks that quantity unknown. It does not inherit the old `_11P` case's progress or count a queued/active model segment as archived.

Older `IT-Noe_FATES_SPINUP500_11P`, `CH-Aws_FATES_SPINUP500_11P`, and failed CH-Aws RH29A, RH34A and RH38A are optional **historical** entries rather than interfering with the current-case status. Use:

```bash
python3 ~/CLM_FATES_maintenance/check_four_spinups.py
python3 ~/CLM_FATES_maintenance/check_four_spinups.py --batch FLUXNET_MultiSite_11
python3 ~/CLM_FATES_maintenance/check_four_spinups.py --batch FLUXNET_MultiSite_11 --show-alternates
```

The monitoring case selection is explicit in `PRIMARY_CASE_OVERRIDES` in the Python script. Change it deliberately if the chosen scientific experiments change; an older pending job must not automatically replace a newer primary experiment.

### Safety and updates

The checker reads Slurm queue, `env_run.xml`, `CaseStatus`, and existing archived restart paths only; it makes **no filesystem modifications or Slurm submissions**. Batch/site targets reflect the October 2026 experimental plan; if you change targets, update the `BATCHES` mapping and commit the change. Check `sacct`, CIME `CaseStatus`, all restart components, and long-term carbon pools separately before taking corrective action.

## Other maintenance workflows

See [`cime_git_cleanup/`](cime_git_cleanup/README.md) for the **separate**, potentially mutating CIME Git/inode maintenance tools. Do not confuse a read-only progress check with Git garbage collection or Scratch cleanup.

## One-command recovery of blocked multisite spin-ups (October 2026)

[`recover_blocked_spinups.py`](recover_blocked_spinups.py) provides one-session recovery for the four batches covered by `check_four_spinups.py`: 6 + 8 + 11 + 13 sites. The October 21 incident has 29 blocked sites and nine completed sites.

On IRIDIS6 as `ly3n24`:

```bash
cd ~/CLM-FATES-single-site-workflows
git pull --ff-only origin main
python3 maintenance/recover_blocked_spinups.py inspect
python3 maintenance/recover_blocked_spinups.py run
python3 maintenance/check_four_spinups.py
```

`inspect` is read-only with respect to CIME and Slurm, and flags sites requiring review. `run` independently attempts every selected site; before modifying a case it cancels **only** that case's exact-match `PENDING (DependencyNeverSatisfied)` Slurm jobs. It verifies the archived three-component restart, retains any interrupted output and backs up case configuration, stages a coordinated restart and updates MPI/RESUBMIT settings before one `case.submit` attempt. Other queued or active jobs are not touched. It refuses to overwrite a newer complete unarchived checkpoint or a model success that has not been archived.

The operator can also limit the operation to one site, e.g. `python3 maintenance/recover_blocked_spinups.py run --site FR-Hes`, or one batch, e.g. `--batch FLUXNET_MultiSite_13`. Logs, original configurations and interrupted outputs are retained under `/scratch/ly3n24/CTSM_FATES_OUTPUTS/recovery_backups/four_batches_dependency_20261021/bulk_*/`. A site reported `REVIEW` has not been successfully resubmitted; inspect the corresponding `result.json`. A site reported `SUBMITTED` only means `case.submit` returned successfully, **not** that CESM or short-term archive finished. The local Slurm state, quota, and output validity must still be checked.

Note: FR-Hes has a 500-year monitor target; IT-Noe monitors the ERA5 branch case, and CH-Aws monitoring now uses RH42A v8; this recovery tool is a distinct, potentially mutating workflow and must not be used casually against the new RH42A case. This recovery does not change scientific forcing, branch reference state, or input namelists.
