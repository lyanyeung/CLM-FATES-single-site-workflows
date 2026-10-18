# IT-Noe — negative near-surface RH model abort

**Incident documented:** 2026-10-18  
**Scientific status:** UNRESOLVED; no correction or rerun claimed.

## Experiment and chronology

| Item | Verified value |
| --- | --- |
| Site | IT-Noe |
| Case | `IT-Noe_FATES_SPINUP500_11P` |
| Campaign | FLUXNET_MultiSite_11, 1000-year intended spin-up |
| Successfully archived | First 5 model years; checkpoint `2009-01-01-00000` |
| Last successful model job | `4286711` |
| Last successful archive job | `4286712` |
| Failed continuation | `4286761` (`cesm.exe`, exit code 1) |
| Dependent archive | `4286764` (`DependencyNeverSatisfied`) |
| Failed segment | Second 5-year segment after the 2009 checkpoint |

The initial five-year segment and its archive completed. The next `case.run` generated
namelists, started `srun --mpi=pmix` and entered the land model, but aborted during
model execution. This is not an `sbatch` QoS or Git-lock failure.

## Confirmed failure

- Model-diagnosed RH: **`-0.481600369697994`** (from `lnd.log`; do not interpret as tower RH or input QBOT).
- Abort location: `HumanIndexMod.F90:1019`.
- Visible call chain: `BareGroundFluxesMod.F90:507` -> `HumanIndexMod.F90:1019` -> `abort`.
- The `lnd.log` records a nearby history-output filename containing `2010-01-02` and
  `nstep=112176`, but the **exact failing half-hour timestamp is not yet established**.

### CESM log — exact error/stack excerpt

```text
  max rss=1811636224.0 MB
 ERROR RH is negative ERROR in HumanIndexMod.F90 at line 1019
Image              PC                Routine            Line        Source             
cesm.exe           000000000116FEF2  shr_abort_mod_mp_         110  shr_abort_mod.F90
cesm.exe           0000000000601210  abortutils_mp_end          63  abortutils.F90
cesm.exe           0000000000B74B69  humanindexmod_mp_        1019  HumanIndexMod.F90
cesm.exe           00000000007E09C9  baregroundfluxesm         507  BareGroundFluxesMod.F90
cesm.exe           0000000000609BFE  clm_driver_mp_clm         718  clm_driver.F90
cesm.exe           00000000005B661C  lnd_comp_nuopc_mp         913  lnd_comp_nuopc.F90
libesmf.so         00007F7FBA9B1A98  _ZNK5ESMCI13Metho     Unknown  Unknown
libesmf.so         00007F7FBA9B1A06  _ZN5ESMCI11Method     Unknown  Unknown
```

### Land log — exact end-of-run excerpt

```text
 
 rh =  -0.481600369697994     
 ENDRUN:
 ERROR RH is negative ERROR in HumanIndexMod.F90 at line 1019
```

### Batch stderr — selected diagnostics

```text
IMPORTANT NOTE: LND_TUNING_MODE is clm6_0_1PT which does NOT have tuned settings, so using the closest option which is clm6_0_GSWP3v1
NOTE: LND_TUNING_MODE is clm6_0_GSWP3v1 which is NOT tuned, but is based on clm5_0_GSWP3v1
ERROR: RUN FAIL: Command 'srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores [IRIDIS6_PATH]   >> cesm.log.$LID 2>&1 ' failed
```

## Interpretation and limitations

- `rh < 0` is diagnosed **inside** the model, not necessarily a negative forcing `QBOT`.
- Two-metre diagnostic humidity can depend on surface-layer extrapolation, atmospheric
  forcing, land state and exchange fluxes. Causality is not yet established.
- The land log also contains small solar-radiation-balance warnings, but the provided
  evidence does not establish them as the direct cause of the abort.
- No station data, forcing, source code, namelist, restart or executable was changed
  for this incident report. Do not disable `calc_human_stress_indices` to conceal it.
- Do not resubmit this case without checking the failing forcing/model conditions.

## File-level reproducibility

Full source logs are retained on IRIDIS6 and **not redistributed** in this public repo.
Only narrowly selected error excerpts are reproduced above. These SHA-256 hashes
identify the original source files used in this report:

| Source log basename | SHA-256 |
| --- | --- |
| `cesm.log.4286761.261015-004831` | `9bc4e9c77c2204107954b0bb9b772731a4bfaf21e0b9ec4b37d242d85251e1b4` |
| `lnd.log.4286761.261015-004831` | `d8191f09473fd232fcfb880e14da66d483a9a5925065077033815a34b06af869` |
| `run.IT-Noe_FATES_SPINUP500_11P.err` | `f18f47701b50a8c1b490b1212a7eac7cd94cdee4eaf64b9f5c5d20011734af23` |

## Planned joint diagnosis with CH-Aws

1. Find the precise IT-Noe model timestamp at the RH abort; do not infer it from
   an annual history filename alone.
2. Audit corresponding DATM TBOT, QBOT, PSRF, ZBOT and reconstructed near-surface RH
   with the original FLUXNET provenance and QC flags.
3. Examine `BareGroundFluxesMod` calculations of `q_ref2m` / `rh_ref2m` and the
   `HumanIndexMod` abort, using controlled read-only diagnostics first.
4. Compare with CH-Aws's independently recorded humidity failures, without assuming
   identical forcing defects or endorsing an arbitrary RH floor.
5. Evaluate any scientifically justified changes in **separately versioned** forcing
   trials or model cases. Preserve all original data and incident logs.

Related: [CH-Aws humidity-failure record](CH_Aws_HUMIDITY_FAILURES_2026-10-15.md).
