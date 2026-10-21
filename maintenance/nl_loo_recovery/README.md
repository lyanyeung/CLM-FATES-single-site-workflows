# NL-Loo 1370-year checkpoint: conservative recovery after 20 October 2026 crash

**Incident:** On 20 October 2026, `run.NL-Loo_FATES_SPINUP500` job `4459256` on `red6134` failed after 19 seconds. `cesm.log` reported `Caught signal 11 (Segmentation fault)` and `srun: ... task 0: Segmentation fault`; CIME's subsequent `/bin/sh` spawn reported `[Errno 12] Cannot allocate memory`. These observations do not establish the root cause as a model science issue, a memory quota exceedance, or a specific node fault. Archive job `4459257` was blocked by `afterok:4459256(failed)`.

**Preserved state:** Last known fully archived checkpoint: `3367-01-01-00000`, equal to 1370 cumulative years since `RUN_STARTDATE=1997-01-01`. The operator confirmed that CPL, DATM and CLM NetCDF restarts have readable headers, and all three dated archived restart pointers match the checkpoint. Target: 3000 years, 1630 remaining.

## Recovery script

[`recover_nl_loo.py`](recover_nl_loo.py) is a **single-case** script with intentionally separated phases; it does not modify the other five-site experiments. It performs preflight checks before changing files. This code has been published to GitHub but **has not been executed or tested on the live IRIDIS6 case**.

For now, download it to Home and run **inspect only**:

```bash
mkdir -p "$HOME/NL_Loo_recovery_tools"
curl -fL --retry 3 \
  'https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/maintenance/nl_loo_recovery/recover_nl_loo.py' \
  -o "$HOME/NL_Loo_recovery_tools/recover_nl_loo.py"
python3 -m py_compile "$HOME/NL_Loo_recovery_tools/recover_nl_loo.py"
python3 "$HOME/NL_Loo_recovery_tools/recover_nl_loo.py" inspect
```

After reviewing current queue state and full model logs, the guarded steps are:

```bash
SCRIPT="$HOME/NL_Loo_recovery_tools/recover_nl_loo.py"

# ONLY after confirming that 4459257 is the sole blocked NL-Loo job:
python3 "$SCRIPT" cancel-blocked

# Copies archived checkpoint and updates RESUBMIT=0; no Slurm submission.
python3 "$SCRIPT" prepare-test

# Read the SESSION=... path from prepare-test output and inspect its manifest.
python3 "$SCRIPT" submit '/PATH/TO/PREPARED/TEST_SESSION'

# Only after 3372 checkpoint was successfully archived:
python3 "$SCRIPT" verify-test
python3 "$SCRIPT" prepare-continuation
python3 "$SCRIPT" submit '/PATH/TO/PREPARED/CONTINUATION_SESSION'
```

**Safety:** Each submit is one-shot and stamps `SUBMIT_ATTEMPTED` before calling `case.submit`. Never repeat a submission after an uncertain result. `prepare-test` and `prepare-continuation` must not be run on active NL-Loo Slurm jobs. No restart, history file or CIME metadata should be deleted for this recovery. If any preflight reports `STOP`, inspect the case before proceeding; particularly protect unarchived output.

A successful one-segment test moves from 1370 to 1375 years (archive date `3372-01-01-00000`), leaving 1625 years = 325 five-year segments and an expected `RESUBMIT=324` for a newly submitted continuation. Monitor Slurm status, CIME `CaseStatus` and dated restart pointers to verify actual results; `RUNNING` does not mean completion.
