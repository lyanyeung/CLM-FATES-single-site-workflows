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

## Four-batch EC tower vegetation and PFT realism — 24 October 2026

[**ICOS_PFT: central report and all result tables**](ICOS_PFT/) brings together the observations and finished simulation outputs for all **38 sites**.

- [**38-site master observed-vs-FATES table**](ICOS_PFT/MASTER_38_SITE_OBSERVED_VS_FATES_PFT_20261024.csv): original species/PFT percentage evidence with denominators and source URLs, and final simulated PFT percentages where GitHub data exist.
- [**38-site observed PFT percentage report**](ICOS_PFT/38_SITE_OBSERVED_PFT_PERCENT_REPORT_20261024.md): 28 numeric observation leads, 10 sites with qualitative-only evidence. Most numerical leads are *not* actual area percentages.
- [**Four-batch model PFT comparison report**](ICOS_PFT/comparison_20261024/FOUR_BATCH_EC_PFT_VS_FATES_REPORT_20261024.md): 34 published model end-state PFT vectors (6 broad-type matches, 2 partial mixed-forest matches, 26 mismatches). Four sites remain without published completed PFT comparisons.

The latest plot/statistical snapshot here is dated 24 October 2026; do not equate simulation completion with full PFT/ecosystem realism. Original tower species shares, CLM `PCT_NAT_PFT`, and FATES `FATES_VEGC_PF` use different denominators.

## Operational status

See the [repository home page](../../README.md) for the most recent documented, **dated** IRIDIS6 status snapshot. GitHub does not automatically query live Slurm queues, and archived model years are not proof of FATES/carbon-pool convergence.

## Directory and naming policy

- **Display / collection name:** **ICOS sites**
- **Existing script / experiment paths:** continue as `examples/FLUXNET_MultiSite_6/`, `_8/`, `_11/`, `_13/` to preserve paths used in reproducible experiments and IRIDIS6 workflows.
- **AmeriFlux experiments:** the parallel [Ameriflux_Site collection](../Ameriflux_Site/) now covers five batches / 50 distinct stations, with its [central PFT evidence index](../Ameriflux_Site/Ameriflux_PFT/). The earlier [shared AmeriFlux metadata](../AmeriFlux_sites/) and [AmeriFlux US-Ha1](../AmeriFlux_US-Ha1/) example remain in their original paths.

Only GitHub documentation is reorganized here. Existing IRIDIS6 cases, Slurm jobs, restart files and outputs are not affected.
