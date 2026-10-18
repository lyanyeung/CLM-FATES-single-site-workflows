# DE-Hai: CIME Git index.lock launch failure and checkpoint-safe recovery

**Incident record reviewed:** 2026-10-18  
**Experiment:** [`FLUXNET_MultiSite_6`](../README.md)  
**Case:** `DE-Hai_FATES_SPINUP500`  
**Target:** 1000 cumulative model years in 5-year CIME segments  
**Status:** recovered past original failed segment; continuation status must be checked on IRIDIS6

## Verified timeline

| Event | Evidence |
| --- | --- |
| Failed job | `run` 4265928, with old dependent archive job 4265929 blocked |
| Last complete checkpoint before incident | `2665-01-01-00000`, 665/1000 years |
| Independent recovery run | 4395987: `model execution success` and `case.run success` |
| Recovery archive | 4395988: `st_archive success` |
| Recovery checkpoint | `2670-01-01-00000`, 670/1000 years |

At document generation, the newest complete three-component restart found was `2690-01-01-00000` (690/1000 model years). This is a structural snapshot, not a convergence test or proof that all later jobs completed.

## CaseStatus evidence from the local case (selected lines)

The lines below were extracted directly from the case's `CaseStatus` when this report was generated; the original HPC logs and NetCDF files remain on IRIDIS6.

```text
2026-10-14 08:33:36: case.submit starting case.run:4265928, case.st_archive:4265929
2026-10-14 08:34:30: case.run starting 4265928
2026-10-14 08:34:56: case.submit success case.run:4265928, case.st_archive:4265929
2026-10-18 03:47:22: case.submit starting case.run:4395987, case.st_archive:4395988
2026-10-18 03:47:22: case.submit success case.run:4395987, case.st_archive:4395988
2026-10-18 03:48:04: case.run starting 4395987
2026-10-18 03:48:06: model execution starting 4395987
2026-10-18 03:55:19: model execution success 4395987
2026-10-18 03:55:19: case.run success 4395987
2026-10-18 03:55:19:   Timing files created for run 4395987.261018-034804
2026-10-18 03:56:04: st_archive starting 4395988
2026-10-18 03:56:05: st_archive success 4395988
```

## Observed failure (2026-10-14)

The failed 5-year segment (`4265928`) terminated after about 3 seconds, before confirmed new model execution. The batch stderr captured in the diagnostic exchange reported:

```text
ERROR: Command: 'git -C /iridisfs/scratch/ly3n24/CLM_FATES/cases/DE-Hai_FATES_SPINUP500 add CaseStatus' failed
fatal: Unable to create '.git/index.lock': File exists.
```

The error is **a Git metadata lock preventing CIME from recording CaseStatus**, not evidence of numerical divergence or damaged FATES carbon pools. The quoted excerpt summarizes the captured stderr without publishing the complete raw cluster log. On the later investigation, `.git/index.lock` no longer existed, no local Git/CIME process was found, and `git -C <case> status --short` worked. **No deletion of an active Git lock was required or reported.** Exact cause of the original competing/stale lock was not independently established.

## Recovery steps performed (2026-10-18)

1. Inspected Slurm stdout/stderr, `CaseStatus`, `EXEROOT/cesm.exe`, RUNDIR and coordinated archived component restart files.
2. Verified no active new `run` task held the same case and that the Git lock had disappeared.
3. Confirmed the checkpoint for `2665-01-01-00000` and tested CIME namelist generation.
4. Submitted **one** 5-year continuation with automatic resubmission temporarily disabled (`RESUBMIT=0`). Run `4395987` and archive `4395988` succeeded, producing `2670-01-01-00000`.
5. Subsequently staged the complete archive checkpoint and resumed the existing 1000-year experiment, setting the remaining chain to 66 five-year segments (`RESUBMIT=65` at resumption).

Do not rerun the original six-site initial submission or 500-to-1000 preparation against this active case. The original case name still ends in `SPINUP500`, even though its target was extended to 1000 years.

## Future checks

- Confirm each resumed 5-year model run and short-term archive succeed, and validate each new coordinated cpl/datm/clm2 checkpoint.
- Watch for fresh Git index locks, incomplete `CaseStatus` writes or double submissions before taking any corrective action.
- Analyze 500-vs-1000-year carbon-pool convergence only after complete validated model history is available.

## Related reproducibility record

[Six-site 500-to-1000-year continuation](spinup500_to1000_continuation_2026-10-14.md).

**Scope limitation:** This is an operational incident and recovery record, not a statement that forcing QC, land-cover representation or carbon equilibrium is scientifically validated. The full original job stderr should be retained privately with the case archive.
