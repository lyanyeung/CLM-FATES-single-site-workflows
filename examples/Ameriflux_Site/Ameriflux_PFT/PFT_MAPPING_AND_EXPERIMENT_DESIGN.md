# PFT interpretation and experiment design

**26 October2026 follow-up:** [Concrete recommended inputs for all50 sites](RECOMMENDED_INPUT_PFT_50_SITES_20261026.md), the host/FATES matrices and35 alternatives now implement explicitly labeled model hypotheses. They preserve the original observational inventory and do not change active inputs. Their applicability is FIXNC cold start, with recorded default14 and proposed site-private HLM mappings. The source-inventory guidance below still applies when interpreting observed percentages.

This document accompanies the [50-site candidate table](FINAL_50_SITE_PFT_CANDIDATES_20261026.csv). It defines how the evidence can inform subsequent experiment configuration. It does not create a surface or initialize model cohorts.

## Four quantities that must retain their meaning

| Quantity | Denominator | Treatment in this collection |
| --- | --- | --- |
| Observed species or vegetation share | Stems, basal area, biomass, community map, ground/canopy cover or an unspecified source basis | Preserve the original basis, survey period, plot extent and residual |
| CLM host surface `PCT_NAT_PFT` | Natural-landunit surface fractions using the applicable CLM type map | Leave unconfigured here; establish natural vegetation/crop/water and bare-ground policy separately |
| FATES initial cohorts and permitted PFTs | Case-specific biogeography, parameter definitions and initialization | Verify the actual parameter file and cold-start/restart behavior before prescribing a case |
| FATES output such as `FATES_VEGC_PF` | Carbon in the modeled vegetation pools | Compare to observations of a compatible quantity; not to an unconverted crown/stem fraction |

The scalar `functional_group_percent_json` values in the master table are summaries of **source measurement groups**, not an array of FATES slots. Their keys identify such restrictions as `immediate_1ha_overstory_stems` or `tabled_juvenile_stems`. Separate years are not additive categories. Missing components are not zeros.

## Functional interpretation

| Botanical group | Broad interpretation | Remaining configuration question |
| --- | --- | --- |
| Pine, spruce, fir, hemlock, cedar, Douglas-fir, juniper | Evergreen needleleaf woody plants | Tree/shrub form and climate-specific parameter traits |
| Larch | Deciduous needleleaf | Do not combine with evergreen conifers |
| Oak, maple, birch, aspen, beech, ash, basswood, hickory | Deciduous broadleaf trees where the named species has that leaf habit | Verify species; evergreen oaks cannot be classified from genus alone |
| Mesquite | Deciduous/drought-deciduous broadleaf woody plant | Tree versus shrub and groundwater/deep-root representation |
| Larrea and other dryland shrubs | Trait-specific evergreen or drought-deciduous shrub groups | Mixed shrub communities cannot all inherit Larrea's phenology |
| Graminoids, grasses, forbs and tundra communities | Species-specific C3/C4 herbaceous groups; possible proxy where no forb/sedge PFT exists | A tussock-community percentage is not a sedge/C3-only percentage |
| Mosses, lichens and biocrusts | Separate observed components | Their absence from a FATES parameterization does not make their ground bare soil |

The earlier Batch01 ledger supplies names and slots for its historical parameter set, including tropical evergreen broadleaf, extratropical evergreen needleleaf, extratropical deciduous broadleaf and C4 grass. These legacy identifiers are retained as provenance only. No actual active parameter file was supplied for this consolidation; do not transfer those slot numbers to another parameter set.

## Fixed-composition and competition experiments

For a **fixed-biogeography/no-competition experiment**, select a dated tower state and state explicitly which measured quantity is being used as a proxy for prescribed area. For example, US-UMB DBF91/ENF9 is a 2010 **tree-basal-area** vector; using it as area requires a new documented assumption. US-Syv local-stem86/14 is especially poor as a footprint-wide area target because the surrounding 1km² has a different dominance pattern. CA-LP1's juvenile-conifer subset cannot stand in for overstory area.

For a **competition experiment**, use the evidence to assess allowed functional groups, plausible initial structure, disturbance and the target period. A final carbon share that differs from the basal-area inventory is a diagnostic lead; agreement cannot be established without matching variables and periods.

The same forcing and soil inputs can support a paired design after the case, active PFT definitions, domain, initialization, measurement heights and forcing-period issues are resolved. The numerical/meteorological workflow status remains in each original batch README.

## Bare ground and published model precedents

[Mahmud et al.2021 Table1](https://doi.org/10.1029/2021JG006400) contains site-based **prescribed ORCHIDEE fCover**. The master CSV preserves source-native group names and exact sums. BS is bare soil; it is not a living FATES PFT. TeBE and TeBD are that model's group labels and can represent shrub or mesquite ecosystems; they cannot be copied into FATES tree types without a growth-form review.

US-Aud retains the prior operator choice **C4 grass70% / bare30%** as a future experimental assumption. This collection does not revoke that choice or claim it is a measured footprint survey. Other published vectors are precedents, not newly approved input files.

Uncovered tree canopy can contain grass, shrubs, litter or rock. Do not derive bare ground as100 minus tree cover. At US-SRM, the explicit published bare range40–50% has a different status from such an arithmetic remainder. Independent canopy/understory ranges should not be summed at their extremes or automatically renormalized.

## Time-dependent sites

US-Me2 crosses the2020 fire,2021 salvage logging and2022 tower relocation. US-Vcm crosses the2013 stand-replacing wildfire; prefire ENF100 is a historical model precedent, and postfire elderberry/aspen regeneration needs separate evidence. US-Slt changes after insect defoliation and mortality. US-GLE, CA-LP1 and US-Mpj have insect/drought disturbance, US-UMd has the2008 girdling experiment, and plantations develop from their establishment years. A static vector across the complete release years is an experiment assumption that must be stated.
