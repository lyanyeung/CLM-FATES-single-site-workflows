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