# ICOS sites

This page is the **ICOS sites** collection for the European FLUXNET / ICOS multi-site CLM-FATES experiments in this repository. It groups the existing campaigns; it does **not** change each flux-tower dataset's original network provenance. Some input data were distributed through FLUXNET2015 or other European networks rather than directly through ICOS.

## Multi-site spin-up experiments

| Campaign | Sites | Model-year objective | Scripts and site-specific README |
| --- | ---: | --- | --- |
| [ICOS sites — Batch 6](../FLUXNET_MultiSite_6/) | 6 | Five cases: 3,000-year continuation; DE-Hai: 1,000-year recovery | [Scripts](../FLUXNET_MultiSite_6/scripts/) |
| [ICOS sites — Batch 8](../FLUXNET_MultiSite_8/) | 8 | Seven sites: 1,000 years; FR-Hes: first 500 years | [Scripts](../FLUXNET_MultiSite_8/scripts/) |
| [ICOS sites — Batch 11](../FLUXNET_MultiSite_11/) | 11 | 1,000 years per site | [Scripts](../FLUXNET_MultiSite_11/scripts/) |
| [ICOS sites — Batch 13](../FLUXNET_MultiSite_13/) | 13 | 1,000 years per site, `S30SHARED` cases | [Scripts](../FLUXNET_MultiSite_13/scripts/) |

**Total: 38 case slots** across the four research campaigns. The same observation network label is not a claim of uniform licensed data source or independently validated land-surface forcing. Consult the individual README files and data-source manifests for each site's true provenance, quality-control decisions and PFT/meteorological caveats.

## Operational status

See the [repository home page](../../README.md) for the most recent documented, **dated** IRIDIS6 status snapshot. GitHub does not automatically query live Slurm queues, and archived model years are not proof of FATES/carbon-pool convergence.

## Directory and naming policy

- **Display / collection name:** **ICOS sites**
- **Existing script / experiment paths:** continue as `examples/FLUXNET_MultiSite_6/`, `_8/`, `_11/`, `_13/` to preserve paths used in reproducible experiments and IRIDIS6 workflows.
- **Future AmeriFlux experiments:** separate collection; the existing [AmeriFlux US-Ha1](../AmeriFlux_US-Ha1/) remains unchanged.

Only GitHub documentation is reorganized here. Existing IRIDIS6 cases, Slurm jobs, restart files and outputs are not affected.
