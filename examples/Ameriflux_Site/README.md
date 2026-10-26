# AmeriFlux sites — five batches, 50 stations

This is the central **Ameriflux_Site** collection requested alongside [ICOS sites](../ICOS_sites/). It preserves all existing campaign directories and the earlier [AmeriFlux shared metadata collection](../AmeriFlux_sites/).

## Recommended input PFT percentages — 26 October 2026

[**50-site CLM-FATES recommended inputs v1**](Ameriflux_PFT/RECOMMENDED_INPUT_PFT_50_SITES_20261026.md) provides concrete percentages summing100 for every station, with35 sensitivity/period alternatives and explicit source-to-input assumptions. [Input CSV](Ameriflux_PFT/RECOMMENDED_50_SITE_CLM_FATES_INPUT_PFT_20261026.csv), [CLM `PCT_NAT_PFT` matrix](Ameriflux_PFT/RECOMMENDED_50_SITE_CLM_PCT_NAT_PFT_20261026.csv), and [FATES matrices](Ameriflux_PFT/RECOMMENDED_50_SITE_FATES_PFT_PERCENT_20261026.csv) are intended for FIXNC cold-start design. Model recommendations are separate from measured evidence. Arctic and hydrodeciduous-shrub profiles require the specified private HLM mapping; competition mode does not preserve these fractions.

## Soil texture — 26 October 2026

[**Ameriflux_Soil**](Ameriflux_Soil/) recommends which `PCT_SAND`/`PCT_CLAY` to use on the 10 CLM surface layers, layer by layer. Sources in order: site-measured texture (AmeriFlux ReESH Zenodo records, BADM `SOIL_TEX`, tower literature), then USDA SSURGO at the tower point, then ISRIC SoilGrids 250 m. The current grid surface is kept only when nothing else exists. **All 50 sites now have a recommendation, with evidence:** [FINAL_50_SITE_SOIL_TEXTURE_20261026.md](Ameriflux_Soil/FINAL_50_SITE_SOIL_TEXTURE_20261026.md). 22 are site-measured (21 ReESH, 1 literature), 13 come from SSURGO and 15 from SoilGrids. The [Stage01 script](Ameriflux_Soil/scripts/01_collect_soil_texture_evidence.py) collects and maps all 50 sites on IRIDIS6 and compares them with each case's current `fsurdat`. Organic and permafrost sites are flagged so that `ORGANIC` can be reviewed.

## Vegetation and PFT composition

[**Ameriflux_PFT — 50-site composition index, master table and source report**](Ameriflux_PFT/) consolidates all five batches, with **33 numerical composition/cover leads** and **17 sites whose reviewed evidence is qualitative composition, LAI/density or published model assumptions**. A numerical lead may be a partial tree inventory, a historical transect, basal area, tree counts or canopy cover. It does not by itself establish a complete PFT fraction of tower ground area.

- [Master 50-site observed-vs-FATES evidence CSV](Ameriflux_PFT/MASTER_50_SITE_OBSERVED_VS_FATES_PFT_20261026.csv)
- [Per-site sources, percentage denominators and dates](Ameriflux_PFT/50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md)
- [Consolidated PFT candidates and model precedents](Ameriflux_PFT/FINAL_50_SITE_PFT_CANDIDATES_20261026.csv)
- [Exact 50-site release manifest](Ameriflux_PFT/metadata/sites_50_manifest.csv)

## Original experiments

| Batch | Sites | Original workflow and release manifest |
| --- | ---: | --- |
| Batch01 | 10 | [Workflow](../AmeriFlux_MultiSite_10/) · [sites.tsv](../AmeriFlux_MultiSite_10/sites.tsv) |
| Batch02 | 10 | [Workflow](../AmeriFlux_MultiSite_10_Batch02/) · [sites.tsv](../AmeriFlux_MultiSite_10_Batch02/sites.tsv) |
| Batch03 | 10 | [Workflow](../AmeriFlux_MultiSite_10_Batch03/) · [sites.tsv](../AmeriFlux_MultiSite_10_Batch03/sites.tsv) |
| Batch04 | 10 | [Workflow](../AmeriFlux_MultiSite_10_Batch04/) · [sites.tsv](../AmeriFlux_MultiSite_10_Batch04/sites.tsv) |
| Batch05 | 10 | [Workflow](../AmeriFlux_MultiSite_10_Batch05/) · [sites.tsv](../AmeriFlux_MultiSite_10_Batch05/sites.tsv) |

**Total: 50 distinct tower IDs.** Package names and first/last years are copied exactly from the original manifests, including FULLSET labels and case-sensitive IDs such as US-UMB, US-UMd and US-UiD. Membership is not a new statement about forcing QC or model readiness.

## Scope of this update

The central collection records tower vegetation, observed composition and candidate functional mapping. It preserves the earlier Batch01 evidence and the operator-selected US-Aud C4 70% / bare 30% model assumption. It also records 11 historical ORCHIDEE fCover configurations separately from observations.

No end-spin-up FATES PFT vector was found in the reviewed AmeriFlux GitHub snapshot, so those master-table cells remain blank. The report is not a live query of IRIDIS6. Active cases, forcing, surfaces and jobs are unchanged. Original batch README files remain the dated operational records.
