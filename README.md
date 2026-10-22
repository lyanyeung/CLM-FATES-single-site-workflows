# CLM-FATES single-site workflows

<!-- MULTIBATCH_SPINUP1000_STATUS_START -->
## ICOS sites — four multi-site spin-up campaigns (IRIDIS6 status, 20 October 2026)

**Latest user-supplied IRIDIS6 checkpoint/Slurm snapshot** for batches 8, 11, and 13; for batch 6, no equivalent new snapshot was supplied in this update. All progress numbers represent **archived elapsed model years**, not forcing years or the current timestep within a running five-year job. Slurm statuses are a dated snapshot. Reaching a target does not demonstrate ecological convergence.

| Campaign | Latest confirmed archival / current Slurm status | Next action |
| --- | --- | --- |
| [ICOS Batch 6](examples/FLUXNET_MultiSite_6/) | Previous observation: five cases RU-Fyo, DE-Tha, DK-Sor, NL-Loo, IL-Yat reached 1000 years and were continued toward 3000; DE-Hai was recovered from a verified 810-year checkpoint and its Slurm run was accepted. **No new batch-6 status is included in the operator's current snapshot.** | Run a fresh batch-6 audit before claiming newer progress |
| [ICOS Batch 8](examples/FLUXNET_MultiSite_8/) | **0/8 current targets met.** Seven 1000-year cases: **2 RUNNING / 5 PENDING**, archived 635–655 years; FR-Hes **360/500**, IDLE. **2,620 target model-years remain** across all eight cases. | Monitor seven submitted chains; FR-Hes archiving requires separate investigation |
| [ICOS Batch 11](examples/FLUXNET_MultiSite_11/) | **9/11 completed 1000 archived years**; IT-Noe **5/1000**, IDLE; CH-Aws **NO_ARCHIVE**, IDLE, elapsed years unverified | Inspect IT-Noe and CH-Aws separately; do not mistake stored RESUBMIT for queued jobs |
| [ICOS Batch 13](examples/FLUXNET_MultiSite_13/) | **0/13 completed 1000 archived years**, **2 RUNNING / 11 PENDING**; archived model years total **6,360/13,000**, with **6,640 remaining** | Continue monitoring existing S30SHARED cases; do not resubmit active chains |

**Evidence:** operator-provided read-only `check_four_spinups.py` report dated 20 October 2026; batch-specific exact checkpoint, RESUBMIT and Slurm job IDs are recorded in each linked README. A `PENDING` job may be queued for priority or dependency reasons, and `RUNNING` only proves job activity at the snapshot, not that the next segment is complete. `NO_ARCHIVE` does not establish zero simulated years.

### Read-only monitoring and protected Research Filestore archival

- **[Preferred live four-batch monitor](maintenance/check_four_spinups.py)** ([instructions](maintenance/README.md)): 38 sites, one active CIME case per site, separate model/archive status, checkpoint/resubmit details, and provenance-checked CH-Aws RH42A v8 inherited restart baseline. On IRIDIS6: `git fetch origin main && git show origin/main:maintenance/check_four_spinups.py | python3 -` (no local merge required).
- [Secondary Filestore-oriented four-batch history audit](scripts/research_filestore/audit_four_batches_live.py) uses legacy case naming; **not** the preferred live RH42A monitor.
- [Selective 8-/13-site transfer and SHA-256 verification](scripts/research_filestore/archive_completed_8_13.py): only run after verifying completed, idle cases.
- [Established 11-site transfer tool](scripts/research_filestore/archive_eleven_site_1000yr.py), [Filestore guidance](docs/research_filestore/README.md), [11-site operational record](docs/research_filestore/FLUXNET_MultiSite_11.md).

**Research Filestore destination:** `/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Archives/<BATCH>/<SITE>/<CASE>/`. Confirm copy/checksum receipts before considering Scratch cleanup; do not delete active restart or original CIME cases.
<!-- MULTIBATCH_SPINUP1000_STATUS_END -->

**[ICOS sites — multi-site experiments](examples/ICOS_sites/)** collects the four existing European FLUXNET/ICOS batches (6, 8, 11 and 13). Dataset provenance remains site-specific. **AmeriFlux sites** are maintained separately, starting with [US-Ha1](examples/AmeriFlux_US-Ha1/). Existing workflow paths remain unchanged to avoid breaking IRIDIS6 jobs.

**[AmeriFlux sites](examples/AmeriFlux_sites/)** includes [Batch 01 (10 sites)](examples/AmeriFlux_MultiSite_10/) and **[Batch 02 (10 sites)](examples/AmeriFlux_MultiSite_10_Batch02/)**. Batch02 publishes Stages00–07, its exact release manifest and operating instructions. The operator's 22 October 2026 Stage07 result is **5 numerically verified candidates / 5 humidity-blocked sites (4,904 unresolved records)**; no DATM or model jobs have been created for Batch02. See the [experiment index](examples/README.md) and the Batch02 README for current scope.

Reproducible single-site CTSM/CLM-FATES workflows used on University of Southampton IRIDIS6.

The repository is organized by observing network / case study:

- `examples/ICOS_ES-LJu/` — ES-LJu ICOS/FLUXNET single-site CLM-FATES workflow.
- `examples/OzFlux_AU-How/` — Howard Springs OzFlux single-site CLM-FATES workflow.
- `examples/AmeriFlux_US-Ha1/` — Harvard Forest EMS Tower, 1991–2025 hourly AmeriFlux/FLUXNET forcing with automated physical QC and CLM-FATES workflow.

This repository intentionally does **not** contain raw flux-tower packages, annual DATM NetCDFs, CTSM surface files, or model history files. Those are large and/or subject to source-data terms. The scripts reconstruct the workflow from the original downloaded data.

Current software context for the ES-LJu example:

- CTSM: `ctsm5.4.056`
- FATES: `sci.1.92.7_api.46.0.0`
- CIME: `cime6.5.5`
- compset: `I1PtClm60FatesRsGs`
- grid: `CLM_USRDAT`
- compiler / MPI: Intel / OpenMPI
- calendar: `NO_LEAP`

- `examples/AmeriFlux_US-Ha1/` — Harvard Forest EMS Tower, 1991–2025, hourly AmeriFlux/FLUXNET forcing with automated physical QC and CTSM/FATES workflow.

- `examples/FLUXNET_MultiSite_6/` — Six-site FLUXNET input preparation, surface extraction, meteorological QC v1–v5, and documented outstanding issues.

## CLM-FATES Spin-up Failure Diagnostics

[**Failed-site diagnostics and incident tracking**](diagnostics/spinup_failures/) gathers read-only investigations for interrupted or scientifically suspect spin-ups. Start with the [IT-Noe negative-RH failure investigation](diagnostics/spinup_failures/IT-Noe/README.md) and its [independent ICOS ERA5 source-audit script](diagnostics/spinup_failures/IT-Noe/it_noe_era_source_audit.py). The original 11-site, CH-Aws, and FR-Hes experiment records remain unchanged. **Diagnostic flags do not imply approved meteorological correction or successful restart.**

## IRIDIS6 MPI / Slurm CPU affinity

**Read [IRIDIS6 MPI, Slurm CPU affinity and OpenMPI troubleshooting](IRIDIS6_MPI_CPU_AFFINITY.md)** before launching multiple single-core CLM-FATES cases on shared IRIDIS6 nodes. It documents a reproduced mismatch between a one-core Slurm allocation and OpenMPI's actual binding, both MPI test launchers, the tested `srun --mpi=pmix` fix, and the difference between CPU allocation, affinity, walltime, and real model progress. Runnable diagnostics are in [`diagnostics/iridis6/`](diagnostics/iridis6/).

**Eight-site experiment:** [`examples/FLUXNET_MultiSite_8/`](examples/FLUXNET_MultiSite_8/) now includes the checkpoint-safe `srun` recovery script, test evidence, and detailed operating instructions. This supersedes the October 13 `mpirun` shared-node resumption method; do not repeat the original eight-site creation/submission script against active cases.

- `examples/FLUXNET_MultiSite_11/` — Eleven-site FLUXNET/ICOS/EUF source-aware meteorological QC; ERA5-Land winter humidity, pressure/longwave trial corrections, and scientific-review ledgers.

## DK-Sor CO2 sensitivity experiment

[**DK-Sor: Fixed vs NOAA Historical CO2 (1996–2024)**](examples/FLUXNET_MultiSite_6/experiments/DK-Sor_CO2_sensitivity/)

This experiment investigates how time-varying atmospheric CO2
influences CLM-FATES simulations of GPP and NEE at DK-Sor.

Two historical simulations are designed to use the same
1000-year spin-up restart and meteorological forcing:

- **Fixed CO2:** 361.93 ppm throughout 1996–2024.
- **Dynamic CO2:** NOAA globally averaged monthly atmospheric CO2
  covering the historical observation period.

The objective is to evaluate whether historical CO2 forcing
changes simulated carbon fluxes, seasonal dynamics, interannual
variability and agreement with eddy-covariance observations.

The experiment includes:

- Scientific hypotheses and experimental configuration.
- Read-only IRIDIS6 monitoring scripts.
- GPP and NEE comparison and visualization scripts.
- Documentation of reproducibility and scientific limitations.

**Status:** NOAA historical simulation underway.
The full fixed-CO2 historical control and 29-year comparison
are not yet completed.

## Southampton Research Filestore: six-site 1000-year history archival

See the repository-wide [Research Filestore management guide](docs/research_filestore/README.md), [six-site archival case study](docs/research_filestore/FLUXNET_MultiSite_6.md), and independent [read-only archive audit script](scripts/research_filestore/audit_six_site_archive.py): five published 1000-year spin-up cases with carbon-pool and GPP/NEE figures, a separate DE-Hai backup-only case, the 2026-10-18 Scratch file-count quota incident, safe archival paths, and read-only verification code. Successful migration and Scratch deletion must be confirmed from live checksum manifests; this repository does not contain raw NetCDF or restart files.

## CIME Git cleanup and Scratch inode maintenance

[**CIME case Git maintenance guide and reusable scripts**](maintenance/cime_git_cleanup/) — safe audit, sequential `git gc --no-prune` packing, stale `gc.pid` inspection, IRIDIS6 Slurm execution, and the October 2026 five-site 1000-year case study. **Do not delete per-case `.git` directories** or remove a Git lock without checking its recorded host and PID. The maintenance process does not alter CLM-FATES restart or history files and does not replace scientific convergence or continuation checks.

## Eleven-site 1000-year spin-up results (20 October 2026)

[Nine of eleven FLUXNET sites have completed their 1000-model-year simulations](examples/FLUXNET_MultiSite_11/README.md): BE-Bra, FR-Fon, GL-ZaH, AT-Neu, FI-Sod, CH-Cha, CH-Fru, CH-Lae and CZ-Stn. IT-Noe and CH-Aws remain incomplete. **Execution completion does not establish spin-up convergence.** The [11-site Research Filestore archive guide](docs/research_filestore/FLUXNET_MultiSite_11.md) and [non-destructive transfer/checksum script](scripts/research_filestore/archive_eleven_site_1000yr.py) describe transferring model output to Southampton Research Filestore. Archive migration must be verified live; no transfer or Scratch deletion is claimed by this GitHub update.
