# Four-batch ICOS/FLUXNET CIME Git packing

This tool reduces Scratch file/inode usage by packing loose objects in the
**38 current per-case Git repositories** selected by the four-batch monitor.
It is separate from Home cleanup in `lyanyeung/maintenance` and from the
50-site AmeriFlux forcing preparation campaign.

| Batch | Cases | Exact naming |
| --- | ---: | --- |
| FLUXNET_MultiSite_6 | 6 | `<SITE>_FATES_SPINUP500`, including cases later continued toward 3000 years |
| FLUXNET_MultiSite_8 | 8 | `<SITE>_FATES_SPINUP500` |
| FLUXNET_MultiSite_11 | 11 | `<SITE>_FATES_SPINUP500_11P`, except the two current branches below |
| FLUXNET_MultiSite_13 | 13 | `<SITE>_FATES_SPINUP1000_S30SHARED` |

The current overrides are `IT-Noe_ERA5_ABW_BRANCH2009` and
`CH-Aws_FATES_SPINUP1000_RH42A_V8_CONT2016`. Historical CH-Aws trials, older
IT-Noe cases, S30EXCL cases, and unrelated single-site experiments are excluded.
The whitelist follows `maintenance/check_four_spinups.py` at repository tree
`f370e4ea7c8c30210fde3dcf57b152d1b2643967`. Case names and historical target
years are not evidence that simulations have completed; use the live monitor
for scientific progress and restart-chain checks.

## Run on IRIDIS6

Requires Linux, Python 3.9+, Git, Slurm `squeue`, and `nice`. No clone or pull is
required. Download the standalone script to Home and inspect the read-only audit:

```bash
(
  set -euo pipefail
  TOOL="$HOME/pack_four_batch_case_git_20261026.py"
  curl -fSL --retry 3 \
    https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/maintenance/cime_git_cleanup/pack_four_batch_case_git.py \
    -o "$TOOL"
  python3 -B "$TOOL" audit
  myfiles
)
```

`audit` reads Git metadata, validates connectivity, and prints per-case inode,
loose-object, packed-object and pack-file counts. It creates no case files,
reports or maintenance lock. Slurm activity is printed but does not prevent a
read-only audit. Missing cases or unexplained Git locks make the audit fail;
they are never silently skipped or automatically repaired.

After `AUDIT PASSED: selected=38 passed=38`, at an idle checkpoint with no
interactive/remote CIME or Git writer, submit **one** sequential maintenance job:

```bash
sbatch --partition=batch --job-name=gc_icos_four_batches \
  --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=4G --time=02:00:00 \
  --output="$HOME/gc_icos_four_batches_%j.log" \
  --wrap="python3 -B '$HOME/pack_four_batch_case_git_20261026.py' run"
```

`run` refuses if **any other job belonging to the user** is queued or running;
only its own `SLURM_JOB_ID` is exempt. It does not cancel, hold or resubmit jobs.
Queue emptiness does not prove the absence of interactive writers on other
hosts; use a known idle maintenance window. A Home advisory lock coordinates
copies of this tool and the generic `cime_git_maintenance.sh`.

Monitor and verify (replace JOBID with the returned Slurm job number):

```bash
tail -f "$HOME/gc_icos_four_batches_JOBID.log"
# After the job finishes:
python3 -B "$HOME/pack_four_batch_case_git_20261026.py" audit
myfiles
```

The final `COMPLETE` line reports actual before/after Git inode counts and
reclaimed entries. `myfiles` reports the real Scratch quota, which may also be
affected by other activity. No amount of savings is promised before IRIDIS
measurement. If `LOOSE=0`, that case is already packed; a high quota may have
other causes such as model histories or caches.

## Exact scope and preservation checks

- Every selected case must pass preflight before the first pack. The tool
  checks private Git-root ownership, CIME markers, locks and connectivity.
  Symlinked/shared object stores, linked worktrees and submodules are refused.
- Packing uses `git gc --no-prune`, with reflog expiration disabled, worktree
  pruning disabled, ref packing disabled and one compression thread. Existing
  dirty/staged/untracked files are allowed and preserved; no `git add`, commit,
  reset, clean or checkout is performed.
- Before and after each case, validate HEAD, refs (including stash), reflogs,
  index bytes, dirty/untracked status and the complete object-ID set, including
  unreachable objects. Run connectivity checks again. Stop on a mismatch;
  successfully packed preceding cases remain packed. This is not a transaction
  across all 38 cases.
- Model run/archive/history/restart paths are not opened. XML is only checked
  for the existence of a CIME marker; no continuation settings are changed.
- Existing `gc.pid` or `*.lock` files stop maintenance. Do not delete them by
  age or use `--force`; inspect their recorded PID/host first.
- This updates Git metadata. It does not delete `.git`, scientific data, or
  model outputs, prove 1000/3000-year completion, or establish convergence.
- Future CIME submissions create new loose objects; repeat at idle checkpoints.

For one complete batch, add `--batch 6`, `8`, `11`, or `13` to **both** the audit
and submitted run command. To restrict further, repeat `--case EXACT_NAME`;
only the fixed 38-name whitelist is accepted. A moved case root can be supplied
with `--case-root /absolute/path/to/cases`; the same argument must be used in
both commands. Do not rename cases just to make an audit pass.

## Validation and status

Local synthetic-repository tests cover actual object packing with old reflogs,
stash, staged/unstaged changes, untracked files and unreachable objects; an
unrelated Slurm job and a lock in the final case block the whole batch before
packing. Slurm self-job exclusion and malformed queue output are checked.
The Linux advisory lock and live IRIDIS filesystem/queue have not been exercised
from the authoring Windows session. Publishing this script is not evidence that
maintenance has run or Scratch quota has decreased.

See [the original maintenance policy](README.md) and
[Git's garbage-collection documentation](https://git-scm.com/docs/git-gc).
