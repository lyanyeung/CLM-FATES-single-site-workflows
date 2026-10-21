# FR-Hes: Scratch quota failure during CIME short-term archiving (21 October 2026)

**Experiment:** [FLUXNET_MultiSite_8](../README.md)  
**Case:** `FR-Hes_FATES_SPINUP500`  
**Target:** 500 cumulative model years, in 5-year segments  
**Evidence:** operator-provided IRIDIS6 `CaseStatus`, `sacct`, short-term archive stdout/stderr, restart-file checks, and `squeue` output from 20–21 October 2026.  
**Latest observed state (21 October 2026):** FR-Hes continuation **running**, not finished. Run job `4505446` was `RUNNING` on `red6086`; dependent archive job `4505447` was `PENDING (Dependency)`.

## Diagnosis: model succeeded but archive failed

On 18 October 2026, five model years advanced FR-Hes from the previously archived `2357-01-01-00000` checkpoint (360 elapsed model years) to the `2362-01-01-00000` restart date (365 elapsed years). Model run `4398054` completed successfully at 08:48:02 BST. Short-term archive job `4398055` failed within one second (Slurm exit `1:0`) before writing an archived 2362 checkpoint.

The archive stderr **identified a specific Scratch quota/inode problem in CIME case Git bookkeeping**, not a demonstrated FATES physics, meteorological forcing or surface-data fault:

```text
ERROR: Command: 'git -C /iridisfs/scratch/ly3n24/CLM_FATES/cases/FR-Hes_FATES_SPINUP500 add CaseStatus'
failed with error 'fatal: Unable to create
.../FR-Hes_FATES_SPINUP500/.git/index.lock': Disk quota exceeded'
```

Three 2362 restart files remained in the run directory, with valid `ncdump -k` header recognition:

| Component | File suffix | Observed size | `ncdump -k` |
| --- | --- | ---: | --- |
| CPL | `cpl.r.2362-01-01-00000.nc` | 32,764 bytes | `cdf5` |
| DATM | `datm.r.2362-01-01-00000.nc` | 20,399,560 bytes | `classic` |
| CLM | `clm2.r.2362-01-01-00000.nc` | 3,451,872 bytes | `cdf5` |

This verifies file existence and readable NetCDF headers, **not by itself** all restart variables or complete cross-component consistency. Before repair, generic `run/rpointer.cpl`, `run/rpointer.atm`, and `run/rpointer.lnd` still referenced 2222; never restart from those stale pointers without controlled restaging.

## Recovery performed on 21 October

1. The operator checked that FR-Hes had no queued/running Slurm jobs and no existing `.git/index.lock`. Scratch had **651/2000 GB** used and **502,558/614,400 files** used at the check, leaving approximately **111,842 file slots**. Other active experiments still consume quota; these numbers are a dated observation, not a guarantee of future headroom.
2. Saved `env_run.xml` and `CaseStatus` to `$HOME/FR_Hes_recovery_20261021/`; set `RESUBMIT=0` to prevent an automatic continuation during repair.
3. Manually submitted the existing `case.st_archive` via Slurm as job `4504414`. The job ended `COMPLETED (0:0)` at **02:13:15 BST** on 21 October, with an empty stderr and `st_archive success 4504414` in `CaseStatus`.
4. Archive stdout explicitly listed copying the three `2362-01-01-00000` restart component files to `archive/FR-Hes_FATES_SPINUP500/rest/2362-01-01-00000/` and archiving associated land history. Two `ncdump -v locfnh` warnings for `clm2.rh0a`/`clm2.rh0i` were **non-fatal in this observed archive**. Archived restart pointers and content checksums were **not independently supplied in the conversation**; verify them on IRIDIS6 if a future fault occurs.
5. The operator subsequently reported `squeue` entries: **`run.FR-Hes_FATES_SPINUP500` 4505446 RUNNING (red6086)** and **`st_archive.FR-Hes_FATES_SPINUP500` 4505447 PENDING (Dependency)**. Thus a continuation submission was accepted and began executing. This is **not evidence that the current five-year segment or the complete 500-year experiment finished**.

The intended restart after 2362 is **365/500 years** complete, **135 years** remaining = **27 five-year segments**; a new `case.submit` from that checkpoint would normally use `RESUBMIT=26` for the 26 later automatic submissions, subject to verified CIME state. The actual post-prepare manifest and active case's `RESUBMIT` were not included with the latest queue report and should be checked rather than assumed.

## Read-only monitoring and acceptance criteria

```bash
NAME=FR-Hes_FATES_SPINUP500
CASE=/iridisfs/scratch/ly3n24/CLM_FATES/cases/$NAME
ARCH=/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive/$NAME/rest

squeue -u ly3n24 -o '%.12i %.65j %.12T %R' | grep -E 'JOBID|FR-Hes' || true
sacct -j 4505446,4505447 -X --format=JobID,JobName%45,State,ExitCode,Elapsed
tail -n 35 "$CASE/CaseStatus"
cd "$CASE" && ./xmlquery RESUBMIT --value
find "$ARCH" -mindepth 1 -maxdepth 1 -type d -name '????-01-01-00000' | sort | tail -n 5
```

A checkpoint is accepted only when the corresponding `case.run success` and `st_archive success` appear and the dated CPL, DATM and CLM restart files **and pointers** agree in the archive. `RUNNING` and `PENDING (Dependency)` are normal interim states, not completed results.

**Do not** re-submit the original case or manually restart `case.st_archive` while these jobs are active; do not rerun whole-batch creation/recovery scripts. Preserve working restarts, CIME metadata, forcing and surface files. If quota fails again, inspect live headroom and archive stderr before attempting any repair. The small, unrelated `QBOT` edit confirmation reported near the latest queue output does **not** identify FR-Hes or demonstrate a change to this site's active forcing, so it is not treated as part of this incident.

## Related documentation

- [Earlier FR-Hes DATM stream-XML setup failure, 14–18 October](FR_Hes_DATM_XML_FILE_NOT_FOUND_RECOVERY_2026-10-18.md) — **a different failure mechanism**.
- [Eight-site checkpoint-safe recovery runbook](resume_after_inode_quota_2026-10-20.md).
- [Eight-site QC and DATM decisions](QC_and_DATM_decisions.md).

**Reproducibility/privacy:** Only summarized observations, code references and job IDs are recorded in GitHub. Raw forcing data, full cluster logs, output NetCDFs and restart binaries remain on IRIDIS6; this is a dated operator observation, not live telemetry or a verified carbon-pool convergence analysis.
