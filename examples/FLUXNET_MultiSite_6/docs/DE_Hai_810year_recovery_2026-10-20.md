# DE-Hai — 810/1000-year checkpoint recovery (20 October 2026)

## Evidence supplied from IRIDIS6 (observed, not a successful restart claim)
- Existing case: `DE-Hai_FATES_SPINUP500`; model start `2000-01-01`, `CONTINUE_RUN=TRUE`.
- `STOP_N=5`, `REST_N=5`, `RESUBMIT=37`, `BUILD_COMPLETE=TRUE`.
- Existing launcher: `srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores`.
- Last successful archive: job `4397990` on 2026-10-18; last successful model run: `4397989`.
- Subsequent failed model run: `4398068`, `model execution error` at 08:48:47, from `cesm.exe`; the **root cause of this second failure is not established**, because the user-provided `cesm.log.4398068.261018-084235` contents were not available.
- Latest observed archived checkpoint directory: `2810-01-01-00000` = **810 elapsed model years**. Three archived `rpointer.{cpl,atm,lnd}.2810-01-01-00000` files were present, referencing the expected cpl/datm/clm2 restart filenames. These observations alone do not verify complete NetCDF integrity.
- Active run pointers were stale, referencing `2670-01-01-00000` for all three components, despite the newest 2810 archive.
- No `.git/index.lock` was observed.
- 190 years remain: 38 five-year jobs. Existing `RESUBMIT=37` is consistent with the *next submission plus 37 resubmissions*, assuming no job is already active.
- No fresh `squeue`, `myfiles`, `sacct` result proving an idle case and sufficient inode headroom has been supplied in this exchange.

## Safe recovery

Use [24_recover_DE_Hai_810_to1000.py](../scripts/24_recover_DE_Hai_810_to1000.py), a one-site-only, deliberately staged helper. It has three commands:

```bash
cd /iridisfs/home/ly3n24/CLM-FATES-single-site-workflows
git pull --ff-only origin main
SCRIPT="$PWD/examples/FLUXNET_MultiSite_6/scripts/24_recover_DE_Hai_810_to1000.py"
python3 "$SCRIPT" inspect
myfiles
# Inspect the actual failure before changing any files:
tail -n 100 /scratch/ly3n24/CTSM_FATES_OUTPUTS/DE-Hai_FATES_SPINUP500/run/cesm.log.4398068.261018-084235
# Only after inspection, if no more recent restart exists and inode space is sufficient:
python3 "$SCRIPT" prepare | tee "$HOME/DE_Hai_810_prepare.log"
SESSION=$(grep '^SESSION=' "$HOME/DE_Hai_810_prepare.log" | tail -1 | cut -d= -f2-)
test -f "$SESSION/PREPARED" || { echo 'Not prepared: STOP'; exit 1; }
# Only after human review of $SESSION/manifest.json, current Slurm and log evidence:
python3 "$SCRIPT" submit "$SESSION"
```

`inspect` is read-only and checks the pinned checkpoint, job queue, configuration, pointer files and basic NetCDF/HDF5 signature. `prepare` backs up the existing case configuration/pointers, preserves failed-segment history, stages the complete archived checkpoint, validates SHA256 and runs CIME preview; it **does not submit**. `submit SESSION` rechecks the source archive, live pointers, inputs and queued jobs, writes a one-shot marker, and submits the existing case once.

**Do not** rerun the six-site 500-to-1000 launcher, the five-site 1000-to-3000 launcher, or regenerate model forcing or surface datasets. Avoid manual deletion of git locks or restart files. If there are active DE-Hai jobs or newer unarchived restarts, stop and investigate. Preserve previous checkpoint data and raw error logs outside GitHub. The helper does not claim to fix the as-yet-unknown underlying cause of the failed `cesm.exe` run (possibly resource/quota related).

## After attempted submission
Verify the returned run/archive job IDs in `CaseStatus`, `squeue` and `sacct`, then confirm `model execution success`, `st_archive success`, and the next checkpoint `2815-01-01-00000`. Thereafter monitor every five-year segment, Scratch inode usage, and completion at `3000-01-01-00000` (1000 elapsed model years). **This record does not claim recovery has been run, the Slurm job submitted, or the experiment completed.**
