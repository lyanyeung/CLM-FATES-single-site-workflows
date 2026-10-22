# EC tower field vegetation versus final FATES PFT: 15-site evidence-based comparison

**Verified sources reviewed: 22 October 2026.** This evidence table adds actual tower species, functional communities, management and stand structure to the existing IGBP, original CLM point-surface and modeled FATES composition comparison. **Do not interpret vegetation land cover, canopy share, herb phytomass, and model vegetation-carbon share as interchangeable denominators.**

**Classification counts:** 3 broad functional-type matches, 1 partially matched mixed-forest composition, 11 principal vegetation-type mismatches. A broad match is *not* a full site calibration or a verified species-level agreement.

| Site | Real EC vegetation | Final modeled FATES PFT (% living VegC) | Assessment |
|---|---|---|---|
| [DE-Hai](https://fluxnet.org/sites/siteinfo/DE-Hai) | Unmanaged old-growth mixed deciduous beech forest; Fagus sylvatica dominant | `broadleaf_colddecid_extratrop_tree` (99.31%) | **BROAD_MATCH** |
| [RU-Fyo](https://fluxnet.org/sites/siteinfo/RU-Fyo) | ~200-year-old spruce (Picea) forest with birch (Betula); Vaccinium and Sphagnum undergrowth | `broadleaf_colddecid_extratrop_tree` (96.06%) | **MISMATCH** |
| [DE-Tha](https://fluxnet.org/sites/siteinfo/DE-Tha) | 1887-established Norway spruce (Picea abies) dominated forest, with other tree species nearby | `broadleaf_colddecid_extratrop_tree` (99.58%) | **MISMATCH** |
| [DK-Sor](https://fluxnet.org/sites/siteinfo/DK-Sor) | European beech (Fagus sylvatica) dominated deciduous forest | `broadleaf_colddecid_extratrop_tree` (99.59%) | **BROAD_MATCH** |
| [NL-Loo](https://fluxnet.org/sites/siteinfo/NL-Loo) | Scots pine (Pinus sylvestris) dominates; minor Corsican/black pine, birch, Douglas fir and oak | `broadleaf_colddecid_extratrop_tree` (99.47%) | **MISMATCH** |
| [IL-Yat](https://fluxnet.org/2023/06/08/fluorescence-response-to-heat-and-drought-at-the-dry-timberline-lewis-kuniks-fluxnet-secondment-experience/) | Planted semi-arid Aleppo pine (Pinus halepensis) forest | `c4_grass` (100.00%) | **MISMATCH** |
| [AT-Neu](https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/2007jd009286) | Managed montane meadow: C3 grasses Dactylis, Festuca, Phleum, Trisetum; forbs/clovers Ranunculus, Taraxacum, Trifolium | `broadleaf_colddecid_extratrop_tree` (99.08%) | **MISMATCH** |
| [BE-Bra](https://meta.icos-cp.eu/resources/stations/ES_BE-Bra) | 2-ha even-aged Scots pine (Pinus sylvestris) station stand within wider mixed conifer-broadleaf forest; birch, oak, rowan, chestnut around stand | `broadleaf_colddecid_extratrop_tree` (99.44%) | **MISMATCH** |
| [CH-Cha](https://www.swissfluxnet.ethz.ch/index.php/sites/site-info-ch-cha/) | Intensively cut fodder grassland; Italian ryegrass (Lolium multiflorum) and white clover (Trifolium repens) dominant | `broadleaf_colddecid_extratrop_tree` (99.41%) | **MISMATCH** |
| [CH-Fru](https://www.swissfluxnet.ethz.ch/index.php/sites/site-info-ch-fru/) | Grass/pasture mixture incl Lolium multiflorum, Alopecurus pratensis, Dactylis glomerata and Trifolium repens | `broadleaf_colddecid_extratrop_tree` (99.61%) | **MISMATCH** |
| [CH-Lae](https://holukas.github.io/dataset_ch-lae_flux_product/Site_Info.html) | Beech (Fagus sylvatica), ash (Fraxinus excelsior), sycamore maple (Acer pseudoplatanus), silver fir (Abies alba) and Norway spruce (Picea abies) mixed forest | `broadleaf_colddecid_extratrop_tree` (99.21%) | **PARTIAL_MIXED** |
| [CZ-Stn](https://www.mdpi.com/2073-4433/12/9/1128) | Even-aged European beech (Fagus sylvatica) forest; reported as pure beech stand | `cool_c3_grass` (100.00%) | **MISMATCH** |
| [FI-Sod](https://meta.icos-cp.eu/resources/stations/ES_FI-Sod) | Scots pine (Pinus sylvestris) boreal forest with lichen, moss and dwarf-shrub floor | `broadleaf_colddecid_extratrop_tree` (91.72%) | **MISMATCH** |
| [FR-Fon](https://fluxnet.org/sites/siteinfo/FR-Fon) | Mature deciduous oak forest (Quercus spp., including Q. petraea), with hornbeam understory | `broadleaf_colddecid_extratrop_tree` (99.60%) | **BROAD_MATCH** |
| [GL-ZaH](https://www.tandfonline.com/doi/full/10.3402/tellusb.v66.21631) | High-Arctic Cassiope tetragona evergreen dwarf-shrub heath EC footprint, with other Arctic shrubs, mosses and graminoids | `arctic_c3_grass` (69.83%) | **MISMATCH** |

## Quantitative field-composition evidence (where published)

- **NL-Loo:** the FLUXNET site description gives **land-cover fractions within a radius of 500 m**, 89% Scots pine, 3.3% black/Corsican pine, 2.3% birch, 1.3% Douglas fir, 0.6% oak and 3.5% open land. These values describe land cover, NOT plant-carbon shares and NOT direct EC instantaneous footprint weights. [FLUXNET](https://fluxnet.org/sites/siteinfo/NL-Loo).
- **CH-Lae:** a site survey reports canopy composition **40% beech, 19% ash, 13% sycamore maple, 8% silver fir, 4% Norway spruce**, with other species making up the remaining fraction. The comparison to 99.21% FATES broadleaf *vegetation C* only supports dominant-group comparison; it cannot establish equality or a direct discrepancy of exactly 12%. [CH-Lae PI data documentation](https://holukas.github.io/dataset_ch-lae_flux_product/Site_Info.html).
- **BE-Bra:** the **2-ha tower stand is Scots pine** within a roughly **150-ha mixed forest** that itself is described by ICOS as Scots-pine dominated. The archive label MF reflects a broader landscape, while current ICOS main ecosystem calls the local stand ENF. The 2-ha/150-ha values are site extents, **not fractional plant-type cover**. [ICOS](https://meta.icos-cp.eu/resources/stations/ES_BE-Bra).
- **FI-Sod:** the ICOS description reports **73% lichens, 12% mosses and 15% ericaceous shrubs in the sparse ground layer**. This is NOT an estimate of the Scots-pine canopy cover or of FATES vegetation carbon. [ICOS](https://meta.icos-cp.eu/resources/stations/ES_FI-Sod).
- **AT-Neu:** published meadow surveys identify common C3 graminoids and forbs, but **cannot be converted into FATES grass/forb carbon shares** without matching aboveground biomass and phenology observations. [Wohlfahrt et al. site description](https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/2007jd009286).
- **GL-ZaH:** the peer-reviewed **EC flux footprint is dominated by Cassiope heath**, whereas Zackenberg valley vegetation also has Arctic grassland, fen and different dwarf-shrub heaths. The site label GRA cannot substitute for the Cassiope community inside the tower footprint. [Lund et al.](https://www.tandfonline.com/doi/full/10.3402/tellusb.v66.21631).

## Practical consequence for experiments

- **BROAD_MATCH (DE-Hai, DK-Sor, FR-Fon):** existing dynamic FATES case may be retained for its functional-type representation, still subject to original-surface crop/landunit assessment, tower flux tests and species/stand age limitations. FR-Fon passes the prior selected NEE/GPP drift screening, but that is not field validation.
- **PARTIAL_MIXED (CH-Lae):** maintain its dynamic record for comparison but add an appropriately mixed broadleaf+conifer constrained-PFT design if evaluating footprint-specific fluxes. A single broadleaf fixed PFT would eliminate genuine mixed-stand structure.
- **MISMATCH (RU-Fyo, DE-Tha, NL-Loo, IL-Yat, AT-Neu, BE-Bra, CH-Cha, CH-Fru, CZ-Stn, FI-Sod, GL-ZaH):** do not spend more HPC model years extending the current wrong-dominant-PFT dynamics as the main EC representation. Preserve original case as a process/sensitivity reference; inspect CIME/Slurm before halting any active chain. Prioritize field-informed constrained-PFT/no-inter-PFT-competition versions, with correct disturbance/management, or model structural diagnosis. BE-Bra should preserve a pine-dominant canopy; GL-ZaH needs a suitable Arctic dwarf-shrub representation rather than forcing a generic grassland; C3 grass sites need management-capable grassland representation.

## Field evidence gaps

Exact canopy/area/biomass percentages for many sites are unavailable in the cited site descriptions and were **not invented**. Species membership and model PFT category are different taxonomic levels: `broadleaf_colddecid_extratrop_tree` is a model physiology category, not proof that a model predicted `Fagus` or `Quercus`. Model `FATES_VEGC_PF` percentages refer to relative carbon and are not directly comparable with published species area or canopy fractions. The glaciated/bare ground and crop portions in original CLM surface `fsurdat` are further separate from the actual FATES PFT outcome.

The machine-readable [field composition and match status CSV](data/15_site_ec_observed_vegetation_and_fates_match.csv) provides source URLs for all 15 sites. The preexisting [full initial-to-final model table](data/15_site_initial_surface_vs_fates_summary.csv) supplies the surface and FATES stages.
