# Four FLUXNET cohorts: EC tower PFT evidence versus final FATES PFT (24 October 2026)

**Source-verified repository integration; scientific screening, not fractional composition validation.** This document combines the original 38-station field-evidence inventory with model-output `FATES_VEGC_PF` at the latest completed-and-published snapshot for 34 stations. It updates, rather than copies, the older 15-site DE-Hai-era table.

## Executive findings

- **38 stations covered** (batches 6/8/11/13). **34** have published complete final PFT distributions, **2** (DE-Lnf, ES-Agu) completed model years but have no GitHub final PFT due to EC-data discovery failures, and **2** (IT-Noe, CH-Aws) are not at 1000 model years in the operator's supplied latest progress.
- Among the 34 with final model PFT outputs: **6 broad dominant-class matches, 2 partial mixed-forest matches, 26 mismatches**. These categories compare *functional identities* only; no model PFT carbon share can be directly subtracted from observed species area, count, basal area or biomass percentages without denominator matching.
- **All 34 final model PFT vectors have zero needleleaf evergreen (`needleleaf_evergreen_extratrop_tree`) and zero needleleaf deciduous (`needleleaf_colddecid_extratrop_tree`) vegetation carbon.** This is a striking cross-cohort inconsistency given multiple spruce- and pine-dominated EC forests. The table proves an output pattern, not its mechanism; inspect active FATES PFT allocation/parameterization, initial surface, biogeography, viability, competition, forcing and effective namelists before attributing cause.
- Dominant modeled PFT groups: **25 deciduous broadleaf (DBF), 3 evergreen broadleaf (EBF), 4 grass-dominant** (2 cool C3 and 2 C4), **1 Arctic C3 grass, 1 tropical hydrodeciduous broadleaf**. Note that the tropical hydrodeciduous type is listed separately but functionally deciduous broadleaf; 26/34 have a deciduous broadleaf tree dominant if it is grouped with DBF.

### Screening counts by batch

| Batch | Final model PFT available | Broad match | Partial mixed | Mismatch | PFT not on GitHub | Not yet 1000 y |
|---|---:|---:|---:|---:|---:|---:|
| 6 | 6 | 2 | 0 | 4 | 0 | 0 |
| 8 | 8 | 2 | 1 | 5 | 0 | 0 |
| 11 | 9 | 1 | 1 | 7 | 0 | 2 |
| 13 | 11 | 1 | 0 | 10 | 2 | 0 |
| **Total** | **34** | **6** | **2** | **26** | **2** | **2** |

### Definition of outcomes

- `BROAD_MATCH`: published station vegetation agrees with dominant physiological PFT class (e.g., DBF beech stand versus FATES extratropical deciduous broadleaf tree). It **does not** imply verified PFT fractional composition, carbon-pool equilibration or matching species.
- `PARTIAL_MIXED`: the dominant modeled broadleaf tree class is plausible but the documented conifer component of a mixed stand is missing from final modeled VegC.
- `MISMATCH`: tower-local vegetation description or reference physiology contradicts the modeled dominant functional type. For BE-Bra and GL-ZaH, field/tower footprint description takes precedence over broad reported MF/GRA labels.
- `PENDING_PFT_PUBLISH`: 1000-year run completed per Slurm progress, but PFT products were not included in GitHub because the end-to-end plotting routine failed in original EC HH CSV discovery.
- `NOT_YET_1000Y`: current branch unfinished; no final-1000-year match claim. `FATES_VEGC_PF` percentages use modeled vegetation carbon as the denominator, NOT tower/species area.

## All 38 stations: tower vegetation versus modeled PFT

### Batch 6

| Site / tower IGBP | Original tower species / reported percent lead | Model dominant PFT VegC (%) | Model second PFT VegC (%) | Judgment |
|---|---|---|---|---|
| [DE-Hai](https://bg.copernicus.org/articles/19/4315/2022/) (DBF) | Fagus sylvatica 64%; Fraxinus excelsior 28%; Acer pseudoplatanus 7% | `broadleaf_colddecid_extratrop_tree` **99.31%** | `cool_c3_grass` **0.69%** | **BROAD MATCH** |
| [RU-Fyo](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (ENF) | Picea abies 85%; Betula pendula 15% | `broadleaf_colddecid_extratrop_tree` **96.06%** | `cool_c3_grass` **3.94%** | **MISMATCH** |
| [DE-Tha](https://meta.icos-cp.eu/resources/stations/ES_DE-Tha) (ENF) | 87% coniferous forest (72% spruce); 13% deciduous forest (10% larch); residual 15% other conifer / 3% other deciduous species... | `broadleaf_colddecid_extratrop_tree` **99.58%** | `cool_c3_grass` **0.42%** | **MISMATCH** |
| [DK-Sor](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (DBF) | Fagus sylvatica 80%; Picea abies plus Larix decidua 20% combined | `broadleaf_colddecid_extratrop_tree` **99.68%** | `cool_c3_grass` **0.32%** | **BROAD MATCH** |
| [NL-Loo](https://essd.copernicus.org/articles/18/2023/2026/) (ENF) | Scots pine 89%; black pine 3.3%; birch 2.3%; Douglas fir 1.3%; oak 0.6%; open ground 3.5% | `broadleaf_colddecid_extratrop_tree` **99.47%** | `cool_c3_grass` **0.53%** | **MISMATCH** |
| [IL-Yat](https://meta.icos-cp.eu/resources/stations/ES_IL-Yat) (ENF) | Aleppo pine (Pinus halepensis) plantation | `c4_grass` **100.00%** | — | **MISMATCH** |

### Batch 8

| Site / tower IGBP | Original tower species / reported percent lead | Model dominant PFT VegC (%) | Model second PFT VegC (%) | Judgment |
|---|---|---|---|---|
| [CZ-BK1](https://meta.icos-cp.eu/resources/stations/ES_CZ-BK1) (ENF) | Picea abies 99%; Abies alba 1% | `broadleaf_colddecid_extratrop_tree` **98.70%** | `cool_c3_grass` **1.30%** | **MISMATCH** |
| [IT-Ren](https://www.mdpi.com/2073-445X/11/11/1903) (ENF) | Picea abies approx 85%; Pinus cembra 12%; Larix decidua 3% | `broadleaf_evergreen_extratrop_tree` **93.89%** | `cool_c3_grass` **6.11%** | **MISMATCH** |
| [FR-Hes](https://bg.copernicus.org/articles/23/6491/2026/) (DBF) | Earlier report approx 90% Fagus sylvatica; later study Fagus approx 75%; oak approx 10%; hornbeam approx 10% | `broadleaf_colddecid_extratrop_tree` **99.67%** | `cool_c3_grass` **0.33%** | **BROAD MATCH** |
| [FR-FBn](https://pmc.ncbi.nlm.nih.gov/articles/PMC12491673/) (ENF) | Pinus halepensis nearly 75% of tree basal area; Quercus ilex in subcanopy | `broadleaf_colddecid_extratrop_tree` **98.89%** | `cool_c3_grass` **1.11%** | **MISMATCH** |
| [DE-Hzd](https://meta.icos-cp.eu/resources/stations/ES_DE-Hzd) (DBF) | Oak regenerated/planted following 2007 windthrow | `broadleaf_colddecid_extratrop_tree` **99.11%** | `cool_c3_grass` **0.89%** | **BROAD MATCH** |
| [CH-Dav](https://besjournals.onlinelibrary.wiley.com/doi/10.1002/2688-8319.70218) (ENF) | Picea abies above 99.5% | `broadleaf_evergreen_extratrop_tree` **93.68%** | `cool_c3_grass` **6.32%** | **MISMATCH** |
| [BE-Vie](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (MF) | Fagus sylvatica 43%; Pseudotsuga menziesii 37% | `broadleaf_colddecid_extratrop_tree` **99.36%** | `cool_c3_grass` **0.64%** | **PARTIAL MIXED** |
| [IT-Lav](https://fluxnet.org/sites/siteinfo/IT-Lav) (ENF) | Evergreen conifer forest | `broadleaf_colddecid_extratrop_tree` **99.59%** | `cool_c3_grass` **0.41%** | **MISMATCH** |

### Batch 11

| Site / tower IGBP | Original tower species / reported percent lead | Model dominant PFT VegC (%) | Model second PFT VegC (%) | Judgment |
|---|---|---|---|---|
| [BE-Bra](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (MF) | Pinus sylvestris 55%; Quercus robur 23% | `broadleaf_colddecid_extratrop_tree` **99.44%** | `cool_c3_grass` **0.56%** | **MISMATCH** |
| [FR-Fon](https://doi.org/10.1111/nph.13771) (DBF) | Quercus petraea 79%; Carpinus betulus 18%; others less than 3% | `broadleaf_colddecid_extratrop_tree` **99.60%** | `cool_c3_grass` **0.40%** | **BROAD MATCH** |
| [GL-ZaH](https://fluxnet.org/sites/siteinfo/GL-ZaH) (GRA) | Arctic tundra/heath | `arctic_c3_grass` **69.83%** | `broadleaf_colddecid_arctic_shrub` **30.17%** | **MISMATCH** |
| [IT-Noe](https://dspace.unitus.it/server/api/core/bitstreams/cc582b9f-42e0-4573-85f1-44ed9aeca8bc/content) (CSH) | Juniperus phoenicea 53%; Pistacia lentiscus 22%; Phillyrea angustifolia 6% | Not published | — | **NOT YET 1000Y** |
| [AT-Neu](https://www.mdpi.com/2072-4292/12/14/2254) (GRA) | Dactylis; Festuca; Phleum; Trisetum and forbs | `broadleaf_colddecid_extratrop_tree` **99.08%** | `cool_c3_grass` **0.92%** | **MISMATCH** |
| [FI-Sod](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (ENF) | Pinus sylvestris 95% | `broadleaf_colddecid_extratrop_tree` **91.72%** | `cool_c3_grass` **8.28%** | **MISMATCH** |
| [CH-Aws](https://pmc.ncbi.nlm.nih.gov/articles/PMC7485103/) (GRA) | Festuca rubra; Phleum rhaeticum; Trifolium repens; Taraxacum | Not published | — | **NOT YET 1000Y** |
| [CH-Cha](https://www.swissfluxnet.ethz.ch/index.php/sites/site-info-ch-cha/) (GRA) | Ryegrass and clover managed mixture | `broadleaf_colddecid_extratrop_tree` **99.41%** | `cool_c3_grass` **0.59%** | **MISMATCH** |
| [CH-Fru](https://pmc.ncbi.nlm.nih.gov/articles/PMC7485103/) (GRA) | Mixed grassland plants cover up to about 90% ground | `broadleaf_colddecid_extratrop_tree` **99.61%** | `cool_c3_grass` **0.39%** | **MISMATCH** |
| [CH-Lae](https://bg.copernicus.org/articles/21/3571/2024/) (MF) | Fagus 40%; Fraxinus 19%; Acer 13%; Abies 8%; Tilia 8%; Picea 4% | `broadleaf_colddecid_extratrop_tree` **99.21%** | `cool_c3_grass` **0.79%** | **PARTIAL MIXED** |
| [CZ-Stn](https://www.mdpi.com/2073-4433/12/9/1128) (DBF) | Fagus sylvatica beech monoculture | `cool_c3_grass` **100.00%** | — | **MISMATCH** |

### Batch 13

| Site / tower IGBP | Original tower species / reported percent lead | Model dominant PFT VegC (%) | Model second PFT VegC (%) | Judgment |
|---|---|---|---|---|
| [DE-Lnf](https://www.mdpi.com/1999-4907/12/12/1693) (DBF) | Fagus sylvatica stand, some oak/maple | Not published | — | **PENDING PFT PUBLISH** |
| [DE-Obe](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2026JG009768) (ENF) | Picea abies dominated forest | `cool_c3_grass` **51.81%** | `broadleaf_evergreen_extratrop_tree` **48.19%** | **MISMATCH** |
| [ES-Agu](https://meta.icos-cp.eu/resources/stations/ES_ES-Agu) (OSH) | Macrochloa tenacissima (Stipa tenacissima) dominant | Not published | — | **PENDING PFT PUBLISH** |
| [ES-LJu](https://www.tandfonline.com/doi/full/10.1080/17538947.2016.1247301) (OSH) | Festuca scariosa 19%; Genista pumila 12%; total vegetation around 50% | `broadleaf_colddecid_extratrop_tree` **97.65%** | `cool_c3_grass` **2.35%** | **MISMATCH** |
| [IT-Col](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (DBF) | Fagus sylvatica 100% | `broadleaf_colddecid_extratrop_tree` **99.44%** | `cool_c3_grass` **0.56%** | **BROAD MATCH** |
| [DE-Gri](https://meta.icos-cp.eu/resources/stations/ES_DE-Gri) (GRA) | Elymus repens; Alopecurus pratensis; Achillea; Rumex; Trifolium | `broadleaf_colddecid_extratrop_tree` **99.37%** | `cool_c3_grass` **0.63%** | **MISMATCH** |
| [DE-RuR](https://fluxnet.org/sites/siteinfo/DE-RuR) (GRA) | Rollesbroich managed grassland | `broadleaf_colddecid_extratrop_tree` **99.73%** | `cool_c3_grass` **0.27%** | **MISMATCH** |
| [FI-Hyy](https://pmc.ncbi.nlm.nih.gov/articles/PMC13439358/) (ENF) | 2026 study: Pinus sylvestris 60%; Picea 25%; Betula 15%. 2020 Table S2: pine 75-100%; spruce/birch combined 5-15% | `broadleaf_colddecid_extratrop_tree` **95.43%** | `cool_c3_grass` **4.57%** | **MISMATCH** |
| [FI-Let](https://meta.icos-cp.eu/resources/stations/ES_FI-Let) (ENF) | Scots pine and birch canopy; spruce understory; partly harvested in 2016 | `broadleaf_colddecid_extratrop_tree` **98.73%** | `cool_c3_grass` **1.27%** | **MISMATCH** |
| [FR-Pue](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (EBF) | Quercus ilex 95% (2020 stand composition); separate ICOS source reports greater than 80% cover | `c4_grass` **53.71%** | `broadleaf_hydrodecid_tropical_tree` **46.29%** | **MISMATCH** |
| [GF-Guy](https://meta.icos-cp.eu/resources/stations/ES_GF-Guy) (EBF) | Evergreen tropical broadleaf rainforest | `broadleaf_hydrodecid_tropical_tree` **99.68%** | `c4_grass` **0.32%** | **MISMATCH** |
| [IT-MBo](https://www.icos-italy.it/monte-bondone-it-mbo/) (GRA) | Festuca rubra 25%; Nardus stricta 13%; Trifolium repens 14.5% | `broadleaf_colddecid_extratrop_tree` **99.34%** | `cool_c3_grass` **0.66%** | **MISMATCH** |
| [IT-Tor](https://www.sciencedirect.com/science/article/abs/pii/S0168192317300515) (GRA) | Nardus stricta dominant with mixed alpine forbs | `broadleaf_evergreen_extratrop_tree` **94.49%** | `cool_c3_grass` **5.51%** | **MISMATCH** |

**Original tower percentage scope:** site evidence includes tree carbon stock (DE-Hai), stand species share (RU-Fyo, DK-Sor), tree basal area (FR-FBn, FR-Fon), surveyed area within 500 m (NL-Loo), ground cover (ES-LJu, IT-MBo), and species lists (many grassland sites). They are NOT interchangeable and do not constitute 38 directly measured FATES area-fraction targets. The source-specific denominator and URL for every station are preserved verbatim in the [machine-readable technical comparison](four_batch_EC_original_versus_FATES_PFT_38sites.csv). The `38_site_PFT_evidence.csv` itself is a research lead inventory: source numbers, year, scale and denominator still require independent primary-source confirmation.

## The earlier 15-site original CLM surface-PFT audit is separate from FATES outcome

The previous [15-station host-surface audit](../../../carbon_flux_convergence_diagnostics/data/15_site_clm_surface_pft_distribution.csv) reports `PCT_NAT_PFT` **within the natural-vegetation landunit**, together with gridcell-scale `PCT_NATVEG` and `PCT_CROP`. This is original CLM host-surface composition, **not** the FATES initial or final living vegetation carbon fraction. Whether these old surface fractions exactly match current active per-case `fsurdat` must be checked using each case's effective namelist before attributing causality.

| Site | Old host natural PFT (fraction within NATVEG) | Host NATVEG (% grid) | Host CROP (% grid) | EC class | FATES final dominant |
|---|---|---:|---:|---|---|
| DE-Hai | C3 non-Arctic grass (53.1%) | 61.9 | 38.1 | DBF | `broadleaf_colddecid_extratrop_tree` |
| RU-Fyo | Needleleaf evergreen temperate tree (45.4%) | 96.7 | 3.3 | ENF | `broadleaf_colddecid_extratrop_tree` |
| DE-Tha | C3 non-Arctic grass (55.8%) | 62.7 | 37.3 | ENF | `broadleaf_colddecid_extratrop_tree` |
| DK-Sor | C3 non-Arctic grass (73.4%) | 55.4 | 44.6 | DBF | `broadleaf_colddecid_extratrop_tree` |
| NL-Loo | C3 non-Arctic grass (71.6%) | 66.8 | 33.2 | ENF | `broadleaf_colddecid_extratrop_tree` |
| IL-Yat | Bare ground (52.2%) | 81.6 | 18.4 | ENF | `c4_grass` |
| BE-Bra | C3 non-Arctic grass (73.8%) | 62.6 | 37.4 | MF | `broadleaf_colddecid_extratrop_tree` |
| FR-Fon | C3 non-Arctic grass (71.8%) | 49.2 | 50.8 | DBF | `broadleaf_colddecid_extratrop_tree` |
| GL-ZaH | Bare ground (74.4%) | 100.0 | 0.0 | GRA | `arctic_c3_grass` |
| AT-Neu | C3 Arctic grass (43.5%) | 95.8 | 4.2 | GRA | `broadleaf_colddecid_extratrop_tree` |
| FI-Sod | Needleleaf evergreen boreal tree (54.8%) | 99.8 | 0.2 | ENF | `broadleaf_colddecid_extratrop_tree` |
| CH-Cha | C3 non-Arctic grass (53.1%) | 77.8 | 22.2 | GRA | `broadleaf_colddecid_extratrop_tree` |
| CH-Fru | C3 Arctic grass (44.7%) | 96.1 | 3.9 | GRA | `broadleaf_colddecid_extratrop_tree` |
| CH-Lae | C3 non-Arctic grass (53.1%) | 77.8 | 22.2 | MF | `broadleaf_colddecid_extratrop_tree` |
| CZ-Stn | C3 non-Arctic grass (59.0%) | 52.2 | 47.8 | DBF | `cool_c3_grass` |

**The remaining 23 stations are not covered by that existing original CLM surface audit; their input PFT fractions have not been guessed.** High host crop fractions at forest stations (e.g., DE-Hai 38.1%, DK-Sor 44.6%, FR-Fon 50.8%) are pre-existing surface audit flags; they **do not prove** crops were actively simulated under the effective FATES landunit configuration.

## Interpretation of key sites

- **DE-Hai — BROAD_MATCH.** Beech/ash/maple shares were reported for tree carbon stock; FATES VegC carbon share uses a different denominator. Original host CLM surface has large crop/grass percentages. Field evidence: Fagus sylvatica 64%; Fraxinus excelsior 28%; Acer pseudoplatanus 7%. Original denominator: tree carbon stock.
- **DK-Sor — BROAD_MATCH.** Stand contains conifer/larch fraction (~20%, unknown precise denominator); FATES dominant DBF fits, but no needleleaf is retained. Field evidence: Fagus sylvatica 80%; Picea abies plus Larix decidua 20% combined. Original denominator: stand species composition, metric unspecified.
- **DE-Tha — MISMATCH.** Observed evergreen-needleleaf canopy replaced by non-needleleaf FATES dominance; final needleleaf VegC = 0%. Field evidence: 87% coniferous forest (72% spruce); 13% deciduous forest (10% larch); residual 15% other conifer / 3% other deciduous species not identified. Original denominator: station reported stand composition.
- **RU-Fyo — MISMATCH.** Observed evergreen-needleleaf canopy replaced by non-needleleaf FATES dominance; final needleleaf VegC = 0%. Field evidence: Picea abies 85%; Betula pendula 15%. Original denominator: stand species composition, metric not specified in Table S2.
- **NL-Loo — MISMATCH.** Observed evergreen-needleleaf canopy replaced by non-needleleaf FATES dominance; final needleleaf VegC = 0%. Field evidence: Scots pine 89%; black pine 3.3%; birch 2.3%; Douglas fir 1.3%; oak 0.6%; open ground 3.5%. Original denominator: ground-area share.
- **IL-Yat — MISMATCH.** Observed Aleppo pine plantation versus modeled 100% C4 grass. Field evidence: Aleppo pine (Pinus halepensis) plantation. Original denominator: dominant vegetation, no percentage.
- **BE-Vie — PARTIAL_MIXED.** Fagus 43%, Douglas-fir 37% stand leads; model lacks the ENF component (0% needleleaf VegC). Field evidence: Fagus sylvatica 43%; Pseudotsuga menziesii 37%. Original denominator: stand species composition, metric not specified.
- **CH-Lae — PARTIAL_MIXED.** Mixed broadleaf/fir/spruce stand; correct broadleaf dominant class but FATES needleleaf VegC = 0%. Field evidence: Fagus 40%; Fraxinus 19%; Acer 13%; Abies 8%; Tilia 8%; Picea 4%. Original denominator: reported species cover; 92% listed.
- **GL-ZaH — MISMATCH.** Tower footprint dominated by evergreen Cassiope heath; model is Arctic C3 grass 69.83% plus *deciduous* Arctic shrub 30.17%. Field evidence: Arctic tundra/heath. Original denominator: IGBP/site description.
- **DE-Obe — MISMATCH.** Model ends with cool C3 grass 51.81% and evergreen broadleaf trees 48.19%, instead of observed Picea-dominated ENF. Field evidence: Picea abies dominated forest. Original denominator: dominant forest species.
- **FR-Pue — MISMATCH.** Observed evergreen holm oak (Quercus ilex) versus modeled C4 grass 53.71% + tropical hydrodeciduous tree 46.29%. Field evidence: Quercus ilex 95% (2020 stand composition); separate ICOS source reports greater than 80% cover. Original denominator: noncomparable species composition versus cover.
- **GF-Guy — MISMATCH.** Observed tropical evergreen rainforest versus modeled 99.68% tropical hydrodeciduous tree; phenology mismatch even though both are broadleaf woody. Field evidence: Evergreen tropical broadleaf rainforest. Original denominator: site dominant vegetation.
- **CZ-Stn — MISMATCH.** Observed beech stand versus modeled 100% cool C3 grass. Field evidence: Fagus sylvatica beech monoculture. Original denominator: stand label, not measured grid percent.
- **IT-Tor — MISMATCH.** Observed alpine Nardus grassland versus modeled 94.49% evergreen broadleaf tree. Field evidence: Nardus stricta dominant with mixed alpine forbs. Original denominator: dominant species only.
- **ES-LJu — MISMATCH.** Sparse dryland shrub/herb ground cover with substantial bare ground versus modeled 97.65% temperate deciduous broadleaf-tree VegC. Field evidence: Festuca scariosa 19%; Genista pumila 12%; total vegetation around 50%. Original denominator: fraction of total surveyed ground.
- **DE-Lnf — PENDING_PFT_PUBLISH.** 1000-year simulation reportedly complete; PFT/figures not published because Stage31 original HH EC dataset discovery failed. Do not impute model PFT. Field evidence: Fagus sylvatica stand, some oak/maple. Original denominator: stand description.
- **ES-Agu — PENDING_PFT_PUBLISH.** 1000-year simulation reportedly complete; PFT/figures not published because Stage31 original HH EC dataset discovery failed. Do not impute model PFT. Field evidence: Macrochloa tenacissima (Stipa tenacissima) dominant. Original denominator: dominant dryland vegetation.

## Scientific next steps (no model inputs altered)

1. **System-wide needleleaf diagnosis**: examine actual active FATES parameter JSON, PFT allowed-biogeography masks, `fates_hlm_pft_map`, initial PFT composition, effective `CaseDocs/lnd_in`, flags (`use_fates_fixed_biogeog`, `use_fates_nocomp`), disturbance/competition rules, and whether PFT02/PFT03 started nonzero or died during spin-up. Run read-only audits of *existing* histories before any model modification.
2. **High-priority gross mismatch**: IL-Yat (pine→C4 grass), CZ-Stn (beech→C3 grass), FR-Pue (evergreen oak→C4 grass plus tropical hydrodeciduous), DE-Obe (spruce→C3 grass/EBF), GF-Guy (evergreen rainforest→hydrodeciduous tree), IT-Tor (grassland→EBF tree), plus ENF forests with 0 needleleaf and managed grasslands modeled as DBF.
3. **Quantitative PFT composition**: for mixed forests BE-Vie/CH-Lae and nominal dominant matches DE-Hai/DK-Sor, obtain tower-footprint-weighted area or plant-carbon biomass by functional type and proper survey dates. A high modeled DBF carbon percentage is not a measured stand-area match.
4. **Input surface provenance**: extend the original 15-station `fsurdat`/`PCT_NAT_PFT` audit to all 38 active cases, explicitly retaining `PCT_CROP`, `PCT_NATVEG`, `PFT` denominator, crop landunit flags, and provenance; do not use `PCT_NAT_PFT` as a FATES output.
5. **Complete missing publication**: export PFT-only charts/results for DE-Lnf and ES-Agu from already-generated RFS site subdirectories, without waiting for unavailable original EC HH GPP/NEE files; keep their carbon/PFT results separate from EC validation. Do not infer their final type from neighbors.
6. **No blind spin-up extension**: one thousand completed years is not ecological equilibrium. The latest convergence tables have widespread non-low ecosystem carbon drift and many negative NEE skill scores; treat mismatch cases as process/sensitivity references until the vegetation representation is scientifically reviewed.

## Source lineage and reproducibility

- Original tower evidence (dated, research leads): [`38_site_PFT_evidence.csv`](../38_site_PFT_evidence.csv). 22 entries contain at least one numerical lead, 16 are qualitative-only. These leads need source-level verification; some have conflicting temporal or denominator definitions.
- Earlier dedicated DE-Hai and 5-site audits: [`25_audit_DE_Hai_PFT_vs_EC.py`](../../../FLUXNET_MultiSite_6/scripts/25_audit_DE_Hai_PFT_vs_EC.py), [`26_audit_five_site_PFT_year1000_vs_EC.py`](../../../FLUXNET_MultiSite_6/scripts/26_audit_five_site_PFT_year1000_vs_EC.py), and the original [`15_site_ec_pft_percent_vs_fates_percent.csv`](../../../carbon_flux_convergence_diagnostics/data/15_site_ec_pft_percent_vs_fates_percent.csv). **Those earlier frozen percentages are not substituted for newer end-spin-up results.**
- New exact latest-model numeric vectors for *all fourteen* FATES PFT definitions: [Batch 6](batch6_model_final_pft_vegc.csv), [Batch 8](batch8_model_final_pft_vegc.csv), [Batch 11](batch11_model_final_pft_vegc.csv), [Batch 13](batch13_model_final_pft_vegc.csv). Each row cites the exact original published annual model PFT CSV.
- New 38-site detailed technical crosswalk: [`four_batch_EC_original_versus_FATES_PFT_38sites.csv`](four_batch_EC_original_versus_FATES_PFT_38sites.csv); includes source URL, observed denominator, top two modeled PFTs, functional class aggregated model shares, earlier host CLM surface fields when available and explicit scientific interpretation.
- Archived model plots: [Batch 6](../../../FLUXNET_MultiSite_6/figures/convergence_snapshots/20261024T105141Z_Batch6_latest_science36/), [Batch 8](../../../FLUXNET_MultiSite_8/figures/convergence_snapshots/20261024T110024Z_Batch8_1000year_science36/), [Batch 11](../../../FLUXNET_MultiSite_11/figures/convergence_snapshots/20261024T110403Z_Batch11_1000year_science36/), [Batch 13](../../../FLUXNET_MultiSite_13/figures/convergence_snapshots/20261024T110812Z_Batch13_1000year_science36/). Batch 13 is 11/13 published and its [`PUBLISH_STATUS.json`](../../../FLUXNET_MultiSite_13/figures/convergence_snapshots/20261024T110812Z_Batch13_1000year_science36/PUBLISH_STATUS.json) identifies the two EC-file discovery failures.
- Temporal scope: Batch 6 uses most recent published archive snapshot (DE-Hai 1000, RU-Fyo 1690, DE-Tha 1680, DK-Sor 2425, NL-Loo 1460, IL-Yat 1920 elapsed model years). Batches 8/11/13 use precisely their published 1000-year horizons.

**No input, forcing, CIME case, restarts, Slurm jobs, annual model histories or existing figures were changed by this report.**
