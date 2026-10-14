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
