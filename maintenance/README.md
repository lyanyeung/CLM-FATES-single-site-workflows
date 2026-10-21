# IRIDIS6 maintenance tools

Utilities for checking and maintaining existing CLM-FATES experiments. **Monitoring is read-only; it does not submit, cancel, restart, or clean any jobs.**

## Four-batch spin-up status checker

[`check_four_spinups.py`](check_four_spinups.py) reproduces the detailed four-batch operator table covering:

- `FLUXNET_MultiSite_6` — 6 sites (five continuation cases to 3000 years; DE-Hai is a separate 1000-year target).
- `FLUXNET_MultiSite_8` — 8 sites (seven 1000-year targets, FR-Hes 500).
- `FLUXNET_MultiSite_11` — 11 sites (1000-year targets).
- `FLUXNET_MultiSite_13` — 13 sites (1000-year targets).

### Run on IRIDIS6

Download the script to Home if your local source repository contains unfinished Git changes or a merge conflict:

```bash
mkdir -p "$HOME/CLM_FATES_maintenance"
curl -fL --retry 3 \
  "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/maintenance/check_four_spinups.py" \
  -o "$HOME/CLM_FATES_maintenance/check_four_spinups.py"

python3 "$HOME/CLM_FATES_maintenance/check_four_spinups.py" \
  | tee "$HOME/four_spinups_status_$(date +%Y%m%d_%H%M%S).log"
```

If the local repository is clean and updated, run it in place:

```bash
python3 ~/CLM-FATES-single-site-workflows/maintenance/check_four_spinups.py
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

### Safety and updates

The checker reads Slurm queue, `env_run.xml`, `CaseStatus`, and existing archived restart paths only; it makes **no filesystem modifications or Slurm submissions**. Batch/site targets reflect the October 2026 experimental plan; if you change targets, update the `BATCHES` mapping and commit the change. Check `sacct`, CIME `CaseStatus`, all restart components, and long-term carbon pools separately before taking corrective action.

## Other maintenance workflows

See [`cime_git_cleanup/`](cime_git_cleanup/README.md) for the **separate**, potentially mutating CIME Git/inode maintenance tools. Do not confuse a read-only progress check with Git garbage collection or Scratch cleanup.
