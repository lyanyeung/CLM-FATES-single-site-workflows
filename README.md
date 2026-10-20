# CLM-FATES single-site workflows

<!-- MULTIBATCH_SPINUP1000_STATUS_START -->
## Four FLUXNET multi-site spin-up campaigns — 1000-model-year status (20 October 2026)

**Evidence categories:** "Confirmed" means a dated IRIDIS6 archive inventory has been supplied previously and/or site-specific published numerical diagnostics establish 1000 complete annual model histories. "Not yet confirmed" is **not** the same as failed; it requires a fresh IRIDIS6 live check. Completion is not evidence of carbon-pool convergence. GitHub cannot see live Slurm jobs or Research Filestore files.

| Campaign | Confirmed 1000-year sites | Not confirmed at 1000 years |
| --- | --- | --- |
| [6 sites](examples/FLUXNET_MultiSite_6/) | **5/6:** RU-Fyo, DE-Tha, DK-Sor, NL-Loo, IL-Yat | DE-Hai (previously backup-only; 1000-year completion not verified) |
| [8 sites](examples/FLUXNET_MultiSite_8/) | **0/8 at 1000 years (IRIDIS6 snapshot, 20/10/2026).** | CZ-BK1 **595**, IT-Ren **580**, FR-Hes **360**, FR-FBn **590**, DE-Hzd **590**, CH-Dav **585**, BE-Vie **590**, IT-Lav **590** model years; all Queue=NONE |
| [11 sites](examples/FLUXNET_MultiSite_11/) | **9/11:** BE-Bra, FR-Fon, GL-ZaH, AT-Neu, FI-Sod, CH-Cha, CH-Fru, CH-Lae, CZ-Stn | IT-Noe, CH-Aws (failed/incomplete at last supplied snapshot) |
| [13 sites](examples/FLUXNET_MultiSite_13/) | **Live verification pending.** | All 13 `_S30SHARED` cases require a fresh post-recovery inventory; old `_S30EXCL` cases must not be combined |

**Confirmed minimum: 14 distinct sites** across the four non-overlapping site groups. This is a dated documentary minimum rather than a live aggregate total; 8-/13-site cases may have advanced in the meantime.

### Read-only live progress and protected Research Filestore archival

- [Check all four campaigns on IRIDIS6](scripts/research_filestore/audit_four_batches_live.py): prints annual h0a inventory, contiguous years, archive restart model years, live Slurm job state, and 1000-year milestone.
- [Selective 8-/13-site transfer and SHA-256 verification](scripts/research_filestore/archive_completed_8_13.py): only run for sites independently verified at 1000 years and with no active jobs; keeps the original Scratch data. Use the batch-specific `--sites` selection; do not run an unconditional 8-/13-site migration.
- [Established 11-site transfer tool](scripts/research_filestore/archive_eleven_site_1000yr.py), [Filestore guidance](docs/research_filestore/README.md), [11-site operational record](docs/research_filestore/FLUXNET_MultiSite_11.md).

**Research Filestore destination:** `/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Archives/<BATCH>/<SITE>/<CASE>/`. Copying and SHA-256 confirmation do not permit automatic Scratch pruning; preserve restarts, pointers and active 1000→3000 continuations. Filestore transfer completion must be evidenced by actual receipts/logs on IRIDIS6, not by this README.
<!-- MULTIBATCH_SPINUP1000_STATUS_END -->

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
