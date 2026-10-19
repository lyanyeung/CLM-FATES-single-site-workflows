# CLM-FATES single-site workflows

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
