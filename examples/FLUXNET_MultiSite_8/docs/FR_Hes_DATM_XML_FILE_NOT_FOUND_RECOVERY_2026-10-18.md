# FR-Hes: DATM stream XML FileNotFoundError and checkpoint-safe recovery

**Incident record reviewed:** 2026-10-18  
**Experiment:** [`FLUXNET_MultiSite_8`](../README.md)  
**Case:** `FR-Hes_FATES_SPINUP500`  
**Target:** 500 cumulative model years in 5-year CIME segments  
**Status:** recovered past original failed segment; continuation status must be checked on IRIDIS6

## Verified timeline

| Event | Evidence |
| --- | --- |
| Failed job | `run` 4270886, with old dependent archive job 4270887 blocked |
| Last complete checkpoint before incident | `2217-01-01-00000`, 220/500 years |
| Independent recovery run | 4395989: `model execution success` and `case.run success` |
| Recovery archive | 4395990: `st_archive success` |
| Recovery checkpoint | `2222-01-01-00000`, 225/500 years |

At document generation, the newest complete three-component restart found was `2242-01-01-00000` (245/500 model years). This is a structural snapshot, not a convergence test or proof that all later jobs completed.

## CaseStatus evidence from the local case (selected lines)

The lines below were extracted directly from the case's `CaseStatus` when this report was generated; the original HPC logs and NetCDF files remain on IRIDIS6.

```text
2026-10-14 09:34:35: case.submit starting case.run:4270886, case.st_archive:4270887
2026-10-14 09:34:36: case.submit success case.run:4270886, case.st_archive:4270887
2026-10-14 09:35:13: case.run starting 4270886
2026-10-18 03:47:24: case.submit starting case.run:4395989, case.st_archive:4395990
2026-10-18 03:47:24: case.submit success case.run:4395989, case.st_archive:4395990
2026-10-18 03:48:04: case.run starting 4395989
2026-10-18 03:48:06: model execution starting 4395989
2026-10-18 03:55:36: model execution success 4395989
2026-10-18 03:55:37: case.run success 4395989
2026-10-18 03:55:37:   Timing files created for run 4395989.261018-034804
2026-10-18 03:56:04: st_archive starting 4395990
2026-10-18 03:56:05: st_archive success 4395990
```

## Observed failure (2026-10-14)

The failed run `4270886` exited after about 27 seconds, while CIME regenerated DATM namelists and **before `cesm.exe` entered the model-execution stage**. The captured Python traceback ended with:

```text
CIME/case/case_run.py -> case.create_namelists()
components/cdeps/datm/cime_config/buildnml -> streams.create_stream_xml(...)
stream_cdeps.py:365 -> with open(streams_xml_file, "a", encoding="utf-8")
FileNotFoundError: [Errno 2] No such file or directory
```

The traceback did **not include the actual attempted XML path**. `buildnml` constructs it from `confdir` and `datm.streams<inst_string>.xml`. Later checks showed `Buildconf/datmconf` existed, as did the executable and the intact 2217 checkpoint. Since the directory existed on later inspection and the one-segment rerun passed, **the exact transient underlying cause is unconfirmed**; do not claim it was proved to be a filesystem race, permission problem, or permanently missing directory.

This namelist-generation incident is distinct from the three previously versioned FR-Hes forcing corrections documented in the eight-site QC notes; the recovered experiment retained its existing `processed_v5_manual_v1` DATM source.

## Recovery steps performed (2026-10-18)

1. Inspected Python traceback, `Buildconf/datmconf`, Slurm output, `CaseStatus`, executable and three-component restart files.
2. Confirmed the archived `2217-01-01-00000` checkpoint and a writable DATM configuration directory; regenerated namelists as a controlled preflight, without changing model science inputs.
3. Submitted **one** 5-year continuation with auto-resubmit disabled (`RESUBMIT=0`). Run `4395989` and archive `4395990` succeeded, producing `2222-01-01-00000`.
4. Restaged that coordinated checkpoint, then resumed the existing 500-year experiment with 55 remaining 5-year segments (`RESUBMIT=54` at resumption).

Do not restart this experiment from its first model year, rebuild the shared executable without evidence, overwrite FR-Hes manual-v1 forcing, or rerun the initial eight-site submission on an active case.

## Future checks

- Monitor for repeated DATM XML `FileNotFoundError`; if it recurs, capture the resolved output path, directory inode/mount state, and full traceback **before** modifying directories.
- Verify that every 5-year segment and subsequent archive produce a complete coordinated checkpoint.
- Evaluate 500-year carbon pools and EC GPP/NEE separately; one successful restarted segment is not evidence of scientific convergence.

## Related reproducibility records

- [Eight-site srun/PMIx and checkpoint recovery](srun_pmix_resume_2026-10-14.md).
- [Eight-site QC and DATM decisions](QC_and_DATM_decisions.md).

**Scope limitation:** This is a CIME setup-stage incident and recovery record. It does not certify input meteorology, tower-footprint PFTs or ecosystem equilibrium. Complete raw cluster logs remain on IRIDIS6, not in this repository.
