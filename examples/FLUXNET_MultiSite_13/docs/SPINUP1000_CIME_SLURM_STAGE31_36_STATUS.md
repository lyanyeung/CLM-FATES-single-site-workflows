# CLM-FATES: 13-site 1000-year case configuration and shared-node recovery

**Checkpoint:** 18 October 2026. This documents *intended configurations*, submitted/failed attempts and operational fixes. **Do not equate case creation, first Slurm submission, model execution, 1000-year completion, and ecosystem carbon-pool convergence.** The final result of Stage 36 was not supplied at the time of this checkpoint.

## Original scientific and CIME design

- 13 sites, each site using its own (2000-era reference) point surface dataset and Stage30 consolidated MET/ZBOT annual DATM files (271 files in total).
- CIME clone from a previously working **GF-Guy** FATES executable with `create_clone --keepexe`, preserving site-specific surface and DATM stream `taxmode=cycle`.
- Compset `I1PtClm60FatesRsGs`; grid `CLM_USRDAT`; `RUN_TYPE=startup`; calendar `NO_LEAP`; `ATM_NCPL=48`; a **fixed site-specific first-forcing-year global CO₂ annual mean** (not local tower CO₂).
- Initial `STOP_OPTION=nyears`, `STOP_N=5`, `REST_N=5`, `RESUBMIT=199`: **200 successive jobs × 5 model years = 1000 model years per station**, provided that model/archiving and every dependency succeeds.
- **Important:** 5 years is the runtime *segment*, whereas full site-specific historical MET years constitute the *forcing cycle*. These are not interchangeable.

## What actually happened: do not rerun historical failure stages

| Stage | Attempt | Observed outcome and standing |
|---|---|---|
| **31** | First 13-case 1000-year setup/submission | 13 initial `run` jobs and their `st_archive` dependencies submitted. **Mistaken `--exclusive`** requests a whole node for each run; queue later showed `QOSMaxNodePerUserLimit` when user's node allocation was saturated. Superseded for shared-node experiments. |
| **33** | Guarded change to shared-node on existing Stage31 case | Halted safely because Stage31 job **4396937** already reached RUNNING; not an all-case fix. |
| **34** | Create 13 `_S30SHARED` cases | **13/13 prepared**, but inherited `--exclusive` in `.case.run`. Stopped before any Stage34 initial submission. |
| **35** | Edit 13 prepared case batch files | Removed **65** embedded exclusivity occurrences in `.case.run`, `case.st_archive`, and `env_batch.xml`; first DE-Lnf `./case.submit` returned `rc=0` but wrapper declared status uncertain/error. The real Slurm Job ID/CaseStatus must be checked before any retry. |
| **36** | Attempt recovery using 8-/11-site validated PMIx/shared-core method | Recovery script exists, with read-only audit and guarded submit. **No success log was supplied at this checkpoint; no submission/completion claim is made.** |

Stage31's ">> 13 job IDs submitted" is distinct from the **post-correction** Stage34/35/36 family. Do not confuse `_S30EXCL` with `_S30SHARED`, and do not resubmit a case with credible prior Slurm/CaseStatus evidence.

## Previously proven IRIDIS6 shared-node setup

The actual reference experiments are:

1. [`FLUXNET_MultiSite_8/scripts/10_resume_shared_node_spinup500.sh`](../../FLUXNET_MultiSite_8/scripts/10_resume_shared_node_spinup500.sh): nonexclusive **1 CPU / 8 GB** Slurm allocation and restart-safe CIME regeneration.
2. [`FLUXNET_MultiSite_8/scripts/12_resume_eight_site_srun_pmix500.sh`](../../FLUXNET_MultiSite_8/scripts/12_resume_eight_site_srun_pmix500.sh): PMIx launch and shared-node case validation.
3. [`FLUXNET_MultiSite_11/scripts/stage17/17_11site_spinup500_srun_pmix.sh`](../../FLUXNET_MultiSite_11/scripts/stage17/17_11site_spinup500_srun_pmix.sh) and [`stage18/18_upgrade_prepared_11site_to_spinup1000_submit_all.sh`](../../FLUXNET_MultiSite_11/scripts/stage18/18_upgrade_prepared_11site_to_spinup1000_submit_all.sh): validated 11-site workflow and 1000-year configuration.

For each run **and** archive job, expected resources are:

```bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
# No --exclusive
```

CIME `MPI_RUN_COMMAND`:

```text
srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores
```

**Crucial implementation detail:** patch **`env_batch.xml`** and use **`./case.setup --reset`** for cases in an appropriate, audited stopped/unsubmitted state to regenerate `.case.run` and `case.st_archive`. Verify the generated scripts and `./preview_run`. Editing `.case.run` in isolation is not sufficient because CIME can regenerate its original directives; also verify `EXEROOT` and `BUILD_COMPLETE` after setup resets. Do not rebuild the proven GF-Guy binary without a specific reason.

**Why this matters:** multiple single-core jobs on the same node can be assigned separate CPU cores by Slurm. `--exclusive` instead reserves the whole node, causing inefficient allocation and `QOSMaxNodePerUserLimit` Pending when the user's node cap is met. It is not a solution to inter-job CPU oversubscription and is not the intended design.

## Operational safety

- Do **not** run `scancel -u ly3n24`; it would cancel unrelated running experiments.
- **Before any further submission**, check `squeue`, `sacct`, each case's `CaseStatus`, `RESUBMIT`, `CONTINUE_RUN` and previous case-specific submit log. Stage35's nonzero wrapper outcome with `case.submit rc=0` is insufficient evidence for safe resubmission.
- Keep old `_S30EXCL` and later `_S30SHARED` case configurations and results separate; never silently reuse a restart belonging to a different case.
- Preserve the full stage chronology as **audit history**. `stage31` and `stage34` are not recommended final recipes. Stage36 can only be called verified after seeing its actual run logs and Slurm job status.
- Source MET uncertainty, PFT validity, IT-Col height proxy and long-term carbon pool convergence remain **scientifically open**.

## Future result review

A spin-up is a model-equilibration experiment. When running, inspect `CaseStatus` and restart/archive completeness per 5-year segment, then use annual/last-cycle `TOTECOSYSC`, slow and fast carbon pools, GPP and NEE comparisons; don't infer convergence merely from completing 1000 nominal years.
