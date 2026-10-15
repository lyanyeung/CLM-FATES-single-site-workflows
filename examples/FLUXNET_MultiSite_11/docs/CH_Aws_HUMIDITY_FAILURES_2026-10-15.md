# CH-Aws: 2026-10-15 humidity failure investigation and reproducibility record

> **Status: UNRESOLVED.** The 1000-model-year experiment has **not** started successfully. Three initial-segment failures have been observed. Preserve this record for later debugging; **do not disable** `calc_human_stress_indices` to conceal the diagnostic. This is an experiment log, *not* a scientific certification of reanalysis-derived meteorology.

## Executive summary

At alpine CH-Aws (forcing 2006–2024; 30-minute NO_LEAP data), FLUXNET/EUF model-filled winter `VPD_F` (`VPD_F_QC=2`) produced impossible or near-zero vapor-pressure-derived relative humidity. Stage11 replaced 559 impossible negative-RH values with ERA5-Land-RH-informed experimental estimates, but many **positive yet implausibly low** values remained. CLM-FATES then aborted in `HumanIndexMod.F90:1019` because its internally diagnosed 2-m relative humidity was negative. A further 779 model-informed Stage21 trial edits (total 1,338 edited rows from the original baseline when disjoint) let the simulation progress farther but did **not** resolve the abort. A Stage25 broadened uncertainty-sensitive trial, with its own v3 DATM and case, also exited nonzero; the **specific** RH25A failure message and exact model clock have **not yet been supplied** and must not be invented.

The two known internal RH failures are **not** proof that input `QBOT` was negative. `BareGroundFluxesMod` diagnoses `q_ref2m`, and `HumanIndexMod` checks the RH calculated there. Very dry inputs, surface-layer flux terms, ground state, measurement height (`ZBOT`) and numerical behaviour all warrant inspection. In particular, strict `QBOT>0` checks alone cannot guarantee internal 2-m RH remains nonnegative.

## Environmental and modelling controls

- Platform: University of Southampton IRIDIS6, `clm_fates_env`, CTSM/CLM-FATES single-point workflow.
- Site root: `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws`.
- Model case root: `/iridisfs/scratch/ly3n24/CLM_FATES/cases`.
- Model run root: `/scratch/ly3n24/CTSM_FATES_OUTPUTS`.
- Reused executable: `/scratch/ly3n24/CTSM_FATES_OUTPUTS/GF-Guy_FATES_SURF2000_CO2405_1PT/bld/cesm.exe`.
- `srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores`; Slurm 1 CPU, 8 GB; no `--exclusive`.
- `CALENDAR=NO_LEAP`, `ATM_NCPL=48`, model time step 30 minutes; forcing loop 2006–2024.
- Per-case spin-up target: `STOP_OPTION=nyears`, `STOP_N=5`, `REST_N=5`, initial `RESUBMIT=199`: 200 five-year segments = **1000 model years if every segment completes**. A successful `case.submit` does not imply completion.
- `calc_human_stress_indices='FAST'` is the **required retained** choice; an intermediate diagnostic change to `NONE` was reverted and `CaseDocs/lnd_in` confirmed `FAST`. Do not present `NONE` as a solution.
- Stage15 BIF-derived CH-Aws `ZBOT=1.5 m`; earliest documented `TA_F` height dates to 2022-09-15 and was explicitly backfilled earlier as an assumption. `WS_F` height is unknown; do not manufacture wind metadata.
- The observed humidity evidence comes from Open-Meteo-served historical ERA5 and ERA5-Land reference `T2m/Td2m`; local-standard timestamps `UTC+1` without DST, and **not independent station observations**.

## Exact staged history, inputs, controls and trial outcomes

| Stage | Evidence and action | Result / caveat |
| --- | --- | --- |
| 03 baseline | `merged_multisource_11_v07a` source-aware CSV, 332,880 half-hours (2006–2024) | SHA256 `61374db9f1cbafcd22c0a4e74eb20d47d213faa59148cb597f284608ff89ccb3` |
| 09/10 | Inspected 559 negative reconstructed RH entries; compared site `TA_F`, `PA_F` and independent reanalysis-delivered T/dewpoint references | 43 winter episodes; 526/559 model differences <=15 percentage points; 33 disagreements >15 points; zero suitable winter QC0/1 tower humidity observations |
| 11 `landrh11a` | Replaced only the 559 **negative** baseline reconstructed-RH values, preserving the source and per-record provenance | SHA256 `130df2cd6c0bf9b89fc4895bca19145e1aca8bf0d4e5d7f48edb85df22035239`; small **positive** RH values left unchanged |
| 13b–15 DATM v1 | 19 annual `CH-Aws_DATM_<year>.nc` in `datm_11_provisional_dynamic_zbot_v1`; `ZBOT=1.5 m` | Structural/numeric audit passed; still PROVISIONAL, not independent scientific verification |
| First run | `CH-Aws_FATES_SPINUP500_11P`, first submitted run `4286717`, old `st_archive=4286718` | Aborted near 2006-01-10, `HumanIndexMod.F90:1019`, internal `rh = -1.15439150258130`; Slurm/archive `DependencyNeverSatisfied` |
| 19 read-only | Compared v07a, landrh11a and DATM 2006; verified both CSV SHA256s | Original DATM forcing RH in 2006 had 12 records <1%, 89 <5%; 2006-01-10 04:30 RH=0.660%, `QBOT=9.3240187e-06` kg/kg |
| 20 read-only | Broadened anomaly flags (QC2 + extremely low positive RH, Stage11 boundaries, jumps), entire 2006–2024 period | 1,080 **unique flagged rows for review**, **not** automatically 1,080 corrupt measurements; QC2 RH<1% = 42, RH<5% = 324, RH<10% = 886; 2006–2013 has ERA5/Land cache, 2014–2024 lacks comparable cache |
| 21 `landrh21a` | Extended double-reanalysis evidence screening; only additional EUF_F/QC2 low-RH candidates, preserving 559 Stage11 edits | **779 new** proposals/edits, years 2006:199; 2007:76; 2008:92; 2009:91; 2010:133; 2011:41; 2012:103; 2013:44. SHA256 `14c481cc7abd3ddeb9e1dabf615b4d694ce73b3dd0347d30dba257afeb479ed8` |
| 22 DATM v2 | Regenerated 19 annual files in separate `datm_11_landrh21a_dynamic_zbot_v2`; ONLY 779 selected QBOT half-hour values intended to change | Read-only audit: 332,880 records, 779 new changes, 559 retained. One untouched VPD float differed by merely `4.440892098500626e-16 hPa` after CSV roundtrip, so one strictly bitwise comparison was patched to a tolerance of `1e-10 hPa`; this is **not** permission for material changes. The initial `--verify` failed solely because `--write` had not yet been run; later v2 forcing provenance is confirmed in Stage24 |
| Second run | `CH-Aws_FATES_SPINUP1000_RH21A`, job `4286891`; associated archive `4286892` | Aborted by `HumanIndexMod.F90:1019`, `rh = -2.92561976750254`, late ATM clock 2006-01-12 03:30; new job not a successful spin-up |
| 24 read-only | v2 comparison around 2006-01-12 failure; validated source tag `landrh21a`, `ZBOT=1.5 m` | 2006-01-12 03:30 and 04:00 input RH respectively **0.03047% and 0.05678%**, both left unchanged by Stage21. ERA5-Land reference **39.193% / 39.226%**, ERA5 **56.148% / 57.097%**. Disagreements **16.96 / 17.87 percentage points** exceeded Stage21 <=15 rule. Both times were EUF_F QC2. v2 2006 annual input RH<1% count=2 |
| 25 `landrh25a` | New versioned, higher-uncertainty RH trial extending model-disagreement window from <=15 pp to conditional <=20 pp for selected low-RH QC2 source events; Stage11/Stage21 changes preserved | Never treat this as validated tower observation; exact additional candidate/edited count **not established from provided output** |
| 26 DATM v3 | New separate `datm_11_landrh25a_dynamic_zbot_v3` with only extra humidity/QBOT changes intended; old v1/v2 retained | User proceeded to Stage27 submission, but complete Stage26 log output is **not in the shared evidence** |
| Third run | `CH-Aws_FATES_SPINUP1000_RH25A`, run job **4286954**, archive job **4286955** | `sacct`: run `FAILED 1:0`, elapsed `00:00:23`; `cesm.exe` step `FAILED 1:0`, elapsed `00:00:21`; archive `PENDING` / `DependencyNeverSatisfied`. **No RH25A model log or diagnosed RH value was provided.** Failure cause and exact model date remain **unconfirmed**. |

### Most diagnostic examples

```text
# Before Stage21; first failure window (2006-01-10, site local standard)
04:30  input RH=0.66019%, ERA5=66.35895%, ERA5-Land=55.02340%, source=EUF_F, VPD_F_QC=2
05:00  landrh11a RH=54.53399%, Stage11 revised
# Stage21 advanced the model farther, but left 2006-01-12 extremely low-RH entries:
2006-01-12 03:00  RH_v2=39.160%
2006-01-12 03:30  RH_v2=0.030469%  QBOT=4.754757e-07 kg/kg  Stage21 flag=false
2006-01-12 04:00  RH_v2=0.056779%  QBOT=8.691575e-07 kg/kg  Stage21 flag=false
2006-01-12 04:30  RH_v2=39.405%
```

The 03:30 and 04:00 interruptions show conspicuous positive-low-RH artefacts **consistent with the model failures**, but timing coincidence and reanalysis disagreement are not proof of singular causation. Site topography, pressure, humidity phase convention at subzero temperatures, time alignment and the land-surface diagnostic formula need dedicated analysis.

## Files and logs retained on IRIDIS6 (do not commit to public GitHub)

- Original/selected candidate directories: `forcing/merged_multisource_11_v07a`, `merged_multisource_11_landrh11a`, `merged_multisource_11_landrh21a`, `merged_multisource_11_landrh25a`.
- Versioned annual NetCDF: `forcing/datm_11_provisional_dynamic_zbot_v1`, `forcing/datm_11_landrh21a_dynamic_zbot_v2`, `forcing/datm_11_landrh25a_dynamic_zbot_v3`.
- Reports: `~/FLUXNET_MultiSite_11/stage19_CH_Aws_meteorology_diagnostics/`, `stage20_CH_Aws_RH_QC_expansion_audit/`, `stage21_CH_Aws_reference_guided_review/`.
- Logs: `~/CH_Aws_2006_RH_failure_audit.log`, `~/CH_Aws_stage20_extended_RH_QC.log`, `~/CH_Aws_stage21_review.log`, `~/CH_Aws_stage21_write_trial.log`, `~/CH_Aws_22_audit.log`, `~/CH_Aws_22_write.log`, `~/CH_Aws_22_verify.log`, `~/CH_Aws_24_failure_diagnosis.log`, plus stage25–27 logs.
- Per-case `CaseStatus`; `cesm.log.*`, `lnd.log.*`, `atm.log.*`; `sacct -j 4286717,4286891,4286954 --format=JobID,JobName%45,State,ExitCode,Elapsed`. CIME/Slurm outputs may be purged by system retention policies.

For analysis scripts and guarded version construction see `../scripts/stage19_to27/` if published alongside this document. The historical Stage09/11 scripts in this repository remain unchanged. Never publish licensed station CSVs, raw reanalysis JSON, private NetCDF, user-specific run logs or scientific products without checking licences.

## Open root-cause questions before revisiting CH-Aws

1. **First retrieve RH25A's exact model logs**, not merely `sacct FAILED`, to identify whether the same HumanIndexMod condition persisted. Which model clock and RH value? Confirm v3 is in the DATM stream and compare v2/v3 samples.
2. Inspect `BareGroundFluxesMod.F90` where `q_ref2m = forc_q + temp2*dqh*(1/temp22m-1/temp2)` and `rh_ref2m = min(100, q_ref2m / qsat_ref2m * 100)` are calculated. Test whether `q_ref2m` can become negative **even when `forc_q>0`**, and record site/surface type, canopy state, humidity fluxes, aerodynamic terms, forcing `QBOT`, diagnostics and exact timestep. Identify physical vs numerical issues before modifying any source.
3. Check whether a `ZBOT=1.5 m` high-alpine configuration, large elevation mismatch and unverified first-known-height backfill exacerbate a surface-layer extrapolation. This is a sensitivity question, not an established cause.
4. Evaluate ice-vs-water saturation calculation below freezing, temperature/dewpoint consistency and local-standard/UTC alignment, including wind and pressure, and prioritize **actual station winter observations** if any can be obtained.
5. Do not use a blanket RH floor or wider >=20-point ERA5 disagreement threshold as automatic scientific correction; reanalysis disagreement identifies substantial uncertainty. If another controlled sensitivity version is justified, retain original/parent hashes, write version-tagged outputs and report the number of proposed/accepted edits.
6. Keep `FAST` enabled. If investigation eventually identifies a CTSM bug, test a source-level fix with a separate executable/case and explicit rationale; no source patch was attempted in these three runs.
7. Verify other site spin-up progress and convergence separately; do not confuse green `case.submit`/Slurm `RUNNING` with completed 1000 years or equilibrium.

## Current disposition

**CH-Aws paused after three unsuccessful first segments on 2026-10-15. No fourth submission recommended.** Other site runs should not be cancelled, edited or auto-resubmitted while this failure is investigated. All current CH-Aws forcing trials and cases are preserved for forensic comparison.
