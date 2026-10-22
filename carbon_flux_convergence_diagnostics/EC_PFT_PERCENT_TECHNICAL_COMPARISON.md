# Technical comparison of observed EC functional PFT and FATES PFT fractions

**22 October 2026** | 15 original single-site dynamic-competition FATES simulations. Report real vegetation species and any field percentages with their correct denominators; distinguish them from simulated `FATES_VEGC_PF` shares.

## EC observed functional PFT (%) vs FATES end-spinup VegC (%): technical comparison

| EC site | EC tower actual dominant functional PFT | Published EC vegetation percentage | Observed percentage denominator | FATES final dominant PFT | FATES VegC (%) | Match? |
|---|---|---|---|---|---:|---|
| [DE-Hai](https://bg.copernicus.org/articles/19/4315/2022/index.html) | `broadleaf_colddecid_extratrop_tree` | Beech 64%, ash 28%, maple 7% | Tree carbon stocks | `broadleaf_colddecid_extratrop_tree` | 99.31% | **YES** |
| [RU-Fyo](https://fluxnet.org/sites/siteinfo/RU-Fyo) | `needleleaf_evergreen_extratrop_tree` | Spruce dominant, birch present; percentage NOT REPORTED | Not reported | `broadleaf_colddecid_extratrop_tree` | 96.06% | **NO** |
| [DE-Tha](https://meta.icos-cp.eu/resources/stations/ES_DE-Tha) | `needleleaf_evergreen_extratrop_tree` | ENF 87% (72% spruce, 15% Scots pine); other 13% incl 10% deciduous needleleaf larch | Tower stand tree species composition | `broadleaf_colddecid_extratrop_tree` | 99.58% | **NO** |
| [DK-Sor](https://ign.ku.dk/english/lter-denmark/dk-sor/) | `broadleaf_colddecid_extratrop_tree` | European beech dominant; species percentage NOT REPORTED | Not reported | `broadleaf_colddecid_extratrop_tree` | 99.59% | **YES** |
| [NL-Loo](https://essd.copernicus.org/articles/18/2023/2026/) | `needleleaf_evergreen_extratrop_tree` | ENF 93.6% (Scots pine 89%; Corsican or black pine 3.3%; Douglas fir 1.3%); DBF 2.9%; open 3.5% | Land-cover area within 500 m of tower | `broadleaf_colddecid_extratrop_tree` | 99.47% | **NO** |
| [IL-Yat](https://fluxnet.org/sites/siteinfo/IL-Yat) | `needleleaf_evergreen_extratrop_tree` | Aleppo pine plantation; percentage NOT REPORTED | Not reported | `c4_grass` | 100.00% | **NO** |
| [AT-Neu](https://pmc.ncbi.nlm.nih.gov/articles/PMC3856878/) | `C3_graminoids_plus_forbs` | Grass component approximately 20–40% of aboveground biomass; forbs substantial | Grass share of aboveground herb biomass (not full PFT C) | `broadleaf_colddecid_extratrop_tree` | 99.08% | **NO** |
| [BE-Bra](https://meta.icos-cp.eu/resources/stations/ES_BE-Bra) | `needleleaf_evergreen_extratrop_tree` | Scots pine local tower stand within mixed forest; percentage NOT REPORTED | Not reported; 2-ha local stand within 150-ha forest | `broadleaf_colddecid_extratrop_tree` | 99.44% | **NO** |
| [CH-Cha](https://www.swissfluxnet.ethz.ch/index.php/sites/site-info-ch-cha/) | `C3_graminoids_plus_forbs` | Italian ryegrass + white clover dominant; split NOT REPORTED | Not reported | `broadleaf_colddecid_extratrop_tree` | 99.41% | **NO** |
| [CH-Fru](https://www.swissfluxnet.ethz.ch/index.php/sites/site-info-ch-fru/) | `C3_graminoids_plus_forbs` | Ryegrass, meadow foxtail, cocksfoot, clover, forbs; shares NOT REPORTED | Not reported | `broadleaf_colddecid_extratrop_tree` | 99.61% | **NO** |
| [CH-Lae](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2023JG007421) | `broadleaf_colddecid_extratrop_tree + needleleaf_evergreen_extratrop_tree` | Deciduous broadleaf ~70%; evergreen needleleaf ~30% | Tree individuals (not canopy/biomass/C) | `broadleaf_colddecid_extratrop_tree` | 99.21% | **YES** |
| [CZ-Stn](https://www.mdpi.com/2073-4433/12/9/1128) | `broadleaf_colddecid_extratrop_tree` | European beech monoculture; numeric proportion NOT REPORTED | Qualitative monoculture (not a measured 100%) | `cool_c3_grass` | 100.00% | **NO** |
| [FI-Sod](https://meta.icos-cp.eu/resources/stations/ES_FI-Sod) | `needleleaf_evergreen_extratrop_tree` | Scots pine dominant; canopy percentage NOT REPORTED; ground: lichen 73%, moss 12%, shrub 15% | Ground-layer percentages only; not canopy PFT percentages | `broadleaf_colddecid_extratrop_tree` | 91.72% | **NO** |
| [FR-Fon](https://www.sciencedirect.com/science/article/abs/pii/S0048969722030789) | `broadleaf_colddecid_extratrop_tree` | Sessile oak 79% + hornbeam 18% = 97% cited deciduous broadleaf tree species | Stand basal area by tree species | `broadleaf_colddecid_extratrop_tree` | 99.60% | **YES** |
| [GL-ZaH](https://www.tandfonline.com/doi/full/10.3402/tellusb.v66.21631) | `broadleaf_evergreen_arctic_shrub` | Cassiope tundra heath EC footprint dominant; numerical footprint PFT shares NOT REPORTED | Not reported for tower footprint | `arctic_c3_grass` | 69.83% | **NO** |

**Binary dominant functional-type match: 4/15 YES, 11/15 NO.** The 4 YES sites are DE-Hai, DK-Sor, CH-Lae and FR-Fon. **CH-Lae matches only the dominant broadleaf type**, *not the observed mixed composition* (tree individuals ~70% deciduous vs 30% conifer, whereas FATES VegC is 99.21% deciduous broadleaf). Never interpret YES as species-level agreement or a demonstrated percentage match.

**Critical denominator distinction:** EC percentages reflect **tree carbon stocks** at DE-Hai; **tree species/stand composition** at DE-Tha; **area within 500 m** at NL-Loo; **aboveground phytomass** at AT-Neu; **tree individuals** at CH-Lae; **basal area** at FR-Fon. FI-Sod lichen/moss/shrub percentages are *ground layer only* and cannot be interpreted as canopy PFT shares. FATES percentages are **relative live vegetation carbon** from `FATES_VEGC_PF` at the archived endpoint for all 15 sites. These metrics cannot be directly subtracted as if they shared a denominator. “NOT REPORTED” means the listed source did not provide a verified local quantitative share; it does not mean zero vegetation or 100% stand purity.

This is a **dominant-PFT-only** screening, not a quantitative composition similarity statistic or a proof of ecosystem equilibrium. For sources and a machine-readable technical record see [technical comparison CSV](data/15_site_ec_pft_percent_vs_fates_percent.csv).


## Technical interpretation

An EC site with observed `broadleaf_colddecid_extratrop_tree` and a modeled dominance by the same PFT receives **YES** for *dominant PFT identity*, even if the reported species-level proportions and the simulated live-vegetation-carbon fractions are numerically different. At mixed sites such as CH-Lae, this must be labeled a **dominant-only match** because the observed 30% conifer trees by count cannot be compared directly with the non-dominant model 0.79% VegC without stem-size/biomass conversion.

For grasslands, actual graminoid and forb species form a mixed **C3 herbaceous community** rather than a uniquely quantified generic FATES grass slot. For GL-ZaH, `Cassiope tetragona` is an Arctic evergreen dwarf shrub (`broadleaf_evergreen_arctic_shrub` analogue), not an `arctic_c3_grass`.

## Sources and percentage scope

- DE-Hai: [Biogeosciences site vegetation/tree carbon](https://bg.copernicus.org/articles/19/4315/2022/index.html).
- DE-Tha: [ICOS Tharandt tree composition](https://meta.icos-cp.eu/resources/stations/ES_DE-Tha).
- NL-Loo: [ESSD Loobos tower dataset and 500-m vegetation map](https://essd.copernicus.org/articles/18/2023/2026/).
- AT-Neu: [Managed Neustift grassland aboveground phytomass composition](https://pmc.ncbi.nlm.nih.gov/articles/PMC3856878/).
- CH-Lae: [JGR remote-sensing forest study; ~70% broadleaf, 30% conifer tree individuals](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2023JG007421).
- FR-Fon: [Fontainebleau stand basal-area composition](https://www.sciencedirect.com/science/article/abs/pii/S0048969722030789).
- FI-Sod: [ICOS Scots pine canopy and ground-layer vegetation](https://meta.icos-cp.eu/resources/stations/ES_FI-Sod).
- BE-Bra: [ICOS pine EC tower stand vs wider mixed landscape](https://meta.icos-cp.eu/resources/stations/ES_BE-Bra).
- GL-ZaH: [Tellus B Cassiope heath EC footprint](https://www.tandfonline.com/doi/full/10.3402/tellusb.v66.21631).

Quantitative species-level PFT fractions are not verified in the cited source for every site. A precise site EC-PFT vector suitable for numerically matching the FATES carbon share would require a consistent plant inventory with biomass/carbon allometry and flux-footprint weighting. See [related field evidence](EC_TOWER_VEGETATION_AND_MODEL_MATCH.md) and [original land-surface to FATES comparison](INITIAL_VEGETATION_AND_PFT_TRANSITIONS.md).
