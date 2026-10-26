# CIME case Git maintenance — IRIDIS6

This folder documents a **safe, non-destructive approach** to reducing Scratch inode usage from the per-case `.git/objects` directories created and updated by CIME during long CLM-FATES spin-ups.

**Use `git gc --no-prune`, never `rm -rf .git`.** Git object packing preserves reachable history, case configuration, NetCDF outputs and restart files. It does not demonstrate that a spin-up has converged.

## Why this is needed

On 19 October 2026, Scratch was limited to 614,400 files/inodes. Usage exceeded 593,000, even though GB storage was well below its quota. Three key contributors were:

| Scratch path | Observed inodes | Note |
|---|---:|---|
| `CLM_FATES/cases` | 176,302 | Many replicated CIME Git repositories |
| `.conda/pkgs` | 157,838 | Conda package cache; separate cleanup policy |
| `CTSM_FATES_OUTPUTS/archive` | 92,844 | History/restarts; do not delete active data |

Pack-file maintenance applies **only** to `CLM_FATES/cases/<case>/.git`. It does *not* apply to the source-control repository `~/CLM-FATES-single-site-workflows/.git`.

## Six-site experiment: five 1000-year cases

Five of the six historical cases reached 1000 model years: RU-Fyo, DE-Tha, DK-Sor, NL-Loo, IL-Yat. The sixth, DE-Hai, was a backup-only exception and must not be described as a completed 1000-year run. Case names still end in `_FATES_SPINUP500` even after later continuation to 1000 years.

User-observed checkpoint on 20 October 2026:

| Case | .git inodes before | .git inodes last reported | Loose objects last reported | Status |
|---|---:|---:|---:|---|
| RU-Fyo | 4,442 | 42 | 0 | Packed |
| DE-Tha | 9,501 | 47 | 0 | Packed |
| DK-Sor | 9,546 | 47 | 0 | Packed |
| NL-Loo | 3,215 | 3,215 | 2,917 | **Not yet packed**: `gc.pid` must be investigated |
| IL-Yat | 9,850 | 43 | 0 | Packed |

The four verified packed case directories therefore reduced their combined inode footprint by about **33,160**. A preceding five-case maintenance Slurm job 4441251 failed during all-site preflight because NL-Loo contained a `gc.pid`; the later successful jobs and inode checks establish the above state. These are observations of Git storage, **not** proof of restart-chain health or 1000→3000-year readiness.

## Recommended workflow

1. Complete a simulation batch and verify `CaseStatus`, archive, restart and model results separately.
2. Ensure there is **no Slurm work or other CIME/Git process** modifying the intended cases. The provided script conservatively stops if *any* of the user's Slurm jobs are queued or running.
3. Run an inode / Git health **read-only audit**:
   ```bash
   bash maintenance/cime_git_cleanup/cime_git_maintenance.sh audit
   ```
4. If every repository is idle and has no lock, pack objects sequentially:
   ```bash
   bash maintenance/cime_git_cleanup/cime_git_maintenance.sh run
   ```
   Run expensive maintenance on a **single Slurm CPU**, not as multiple jobs on login nodes. See examples below.
5. Recheck `git fsck --connectivity-only --no-dangling`, `git count-objects -vH`, `du --inodes -s .../.git`, and `myfiles`. Do not rely on an inode reduction alone.

Both modes default to the five six-site case directory basenames. Supply **exact case names** (without paths) for other completed batches, for example:
```bash
bash maintenance/cime_git_cleanup/cime_git_maintenance.sh audit DE-Lnf_FATES_SPINUP1000_S30SHARED DE-Obe_FATES_SPINUP1000_S30SHARED
```
Do **not** include active 1000→3000-year cases.

### Slurm maintenance job for the default five-site batch

From the repository root on IRIDIS6, and **only after the audit passes**:
```bash
sbatch --partition=batch --job-name=cime_git_pack --nodes=1 --ntasks=1 \
  --cpus-per-task=1 --mem=4G --time=01:00:00 \
  --output="$HOME/cime_git_pack_%j.log" \
  --wrap="bash $HOME/CLM-FATES-single-site-workflows/maintenance/cime_git_cleanup/cime_git_maintenance.sh run"
```
This submits a maintenance operation, not a CLM-FATES simulation. It cannot fix active model failures.

## Stale Git locks: stop and investigate

An old `.git/gc.pid` is **not by itself proof** that Git is inactive. The process may have run on another Slurm/login host. The `inspect_gc_lock.sh` helper reports its contents and timestamps; it never deletes it.

```bash
bash maintenance/cime_git_cleanup/inspect_gc_lock.sh NL-Loo_FATES_SPINUP500
```

Before moving any lock, establish from the recorded PID/host, process lists on the recorded host, Slurm/accounting history and lack of other activity that the operation has ended. Do not automatically delete a lock solely because it is older than 24 hours. If uncertain, leave it in place and skip that case. Never use `git gc --force` as a workaround for unexplained locking.

## What packing does and does not do

- `git gc --no-prune` packs Git objects and preserves reachable history; it may still update Git metadata and reflogs. It is **not a read-only command**.
- Do not add the unsupported `--no-detach` option. On this IRIDIS installation, that option caused a previous `git gc` attempt to fail without changing inode usage.
- Do **not** remove per-case `.git` directories or run `git clean`, `rm -rf`, `scancel -u`, or destructive `git gc --prune=now` in this maintenance workflow.
- CIME case Git maintenance and the separate GitHub source repository are distinct concerns.
- Packing Git objects does not change NetCDFs/restarts. Extending 1000→3000 model years still requires independent verification of last successful archive, restarts, pointers and CIME XML continuation settings.
- Future CIME operations will create fresh loose Git objects again; repeat this maintenance **only at safe batch checkpoints**, not every 5-year resubmission.

## Related documentation

- [Six-site spin-up and Research Filestore records](../../examples/FLUXNET_MultiSite_6/README.md)
- [Research Filestore management](../../docs/research_filestore/README.md)
- [MPI, Slurm and CPU affinity](../../IRIDIS6_MPI_CPU_AFFINITY.md)

## 11-site campaign: 9 completed 1000-year runs (user audit, 20 October 2026)

The IRIDIS6 read-only progress report established 9/11 cases at 1000 model years with 1000 archived annual histories, a final 1000-year restart, `RESUBMIT=0`, `st_archive success` and no queued job at the time of the audit. **IT-Noe** was at 5 years and **CH-Aws** had no verified restart; neither is included.

| Eligible | Case name pattern | History/restart status |
|---|---|---|
| BE-Bra, FR-Fon, GL-ZaH, AT-Neu, FI-Sod, CH-Cha, CH-Fru, CH-Lae, CZ-Stn | `<SITE>_FATES_SPINUP500_11P` | User-audited 1000 years; rerun preflight before maintenance |
| IT-Noe | `IT-Noe_FATES_SPINUP500_11P` | 5 years — **excluded** |
| CH-Aws | `CH-Aws_FATES_SPINUP500_11P` | 0 verified years — **excluded** |

The standalone [nine-site audit/packing script](pack_11site_nine_1000yr.sh) verifies the exact nine case names, archive history counts/year span, final restart-directory presence, `CaseStatus`, `RESUBMIT`, Git locks and Git integrity. It will not start unless all nine pass preflight. The script deliberately stops if **any other Slurm job** is present; when running under Slurm it exempts only its own job ID.

From the repository root on IRIDIS6:

```bash
git pull --ff-only
bash maintenance/cime_git_cleanup/pack_11site_nine_1000yr.sh audit
```

Only if the audit reports `AUDIT PASSED`, submit:

```bash
sbatch --partition=batch --job-name=gc_11site_nine --nodes=1 --ntasks=1 \
 --cpus-per-task=1 --mem=4G --time=01:00:00 \
 --output="$HOME/gc_11site_nine_%j.log" \
 --wrap="bash $HOME/CLM-FATES-single-site-workflows/maintenance/cime_git_cleanup/pack_11site_nine_1000yr.sh run"
```

**Do not run a second copy**, do not delete `.git`, and do not manually clear a `gc.pid` that may belong to another host. The script verifies archive structure and the presence of a restart folder, but does not independently inspect NetCDF file contents or establish scientific carbon-pool convergence. The nine cases' post-maintenance inode reductions must be recorded from IRIDIS; this GitHub commit only publishes code, not evidence of completed cleanup.

## Four ICOS/FLUXNET batches: 38 current cases (26 October 2026)

Use [the four-batch audit and packing instructions](FOUR_BATCH_38_CASES.md) and
[the standalone Python tool](pack_four_batch_case_git.py). This covers the
6/8/11/13-site batches, including the six-site campaign's 3000-year continuations
and the currently selected IT-Noe/CH-Aws branch cases. It excludes the 50-site
AmeriFlux preparation campaign and historical/superseded case variants.
