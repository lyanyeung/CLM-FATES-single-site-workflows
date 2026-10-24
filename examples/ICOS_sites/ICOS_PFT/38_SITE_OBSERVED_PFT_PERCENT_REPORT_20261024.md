# Observed EC-tower PFT percentages: all 38 stations (evidence audit, 24 October 2026)

**Short answer:** 28/38 stations have at least one reported numeric vegetation-composition or vegetation-cover observation. **Ten stations are qualitative-only** in the checked sources. These 28 numerical observations are **not 28 directly usable PFT land-area vectors**: several represent stem/basal area, wood volume, species abundance, vegetation carbon, herb biomass or total ground cover. Every observation below retains the scientific denominator and site/source. These figures are not generated from FATES outputs.

**[Download/read the detailed, source-attributed 38-station data table](38_site_observed_PFT_percent_evidence_v2_20261024.csv).** The original prior inventory remains preserved at [38_site_PFT_evidence.csv](38_site_PFT_evidence.csv), with [additional 16-site leads](16_site_further_research_leads.csv).

## Completeness by cohort

| Cohort | Stations | At least some numbers | Qualitative only |
|---|---:|---:|---:|
| Batch 6 | 6 | 6 | 0 |
| Batch 8 | 8 | 7 | 1 |
| Batch 11 | 11 | 8 | 3 |
| Batch 13 | 13 | 7 | 6 |
| **Total** | **38** | **28** | **10** |

## Primary distinction for fixed-PFT work

- **Tower source area / physical ground-area candidate:** DE-Tha has ICOS-reported conifer/deciduous composition including larch; NL-Loo has a 500-m-radius land-cover survey. These are the **two strongest area-like numerical leads**, not yet approved model input: the flux-weighted footprint, landunit denominator, land-cover date and valid FATES type coverage require checking.
- **Local species cover, understory/basal cover, or incomplete ground vegetation:** valuable for local composition, but incomplete and not necessarily equivalent to PFT horizontal coverage. Examples: GL-ZaH, CH-Lae, ES-LJu, ES-Agu, FR-Pue, IT-MBo and CH-Fru.
- **Tree stand composition, basal area, wood volume, tree biomass or aboveground phytomass:** useful evidence of which PFT should dominate, but cannot directly set land-area fractions without allometry and area weighting (e.g. DE-Hai, IT-Lav, BE-Vie, FI-Let, AT-Neu).
- **Only IGBP or community names:** not percent measurements; do not invent 100% DBF or 100% GRA for these sites.

## Full 38-site inventory

### FLUXNET_MultiSite_6

| EC site | Reported PFT composition or cover | Percent denominator and scope | Assessment |
|---|---|---|---|
| [DE-Hai](https://bg.copernicus.org/articles/19/4315/2022/) (DBF) | DBF ≥99% of tree carbon: Fagus 64; Fraxinus 28; Acer 7 | Tree carbon stock / live tree C — Hainich tower forest stand | Numeric, different denominator |
| [RU-Fyo](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (ENF) | ENF 85%; DBF 15% (stand species composition) | Flechard Table S2 species proportion; denominator undefined — Fyodorovskoye research forest | Numeric, different denominator |
| [DE-Tha](https://meta.icos-cp.eu/resources/stations/ES_DE-Tha) (ENF) | ENF 87%; DNF 10%; DBF 3% | Species / vegetation proportions reported for EC footprint — Tharandt forest flux footprint | **Area candidate** |
| [DK-Sor](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (DBF) | DBF 80%; ENF+DNF combined 20% (split UNKNOWN) | Tree stand species fraction; exact denominator undefined — Sorø research stand | Numeric, different denominator |
| [NL-Loo](https://essd.copernicus.org/articles/18/2023/2026/) (ENF) | ENF 93.6%; DBF 2.9%; open mosaic 3.5% | Mapped horizontal ground-area fraction — 500-m fixed radius around Loobos flux tower | **Area candidate** |
| [IL-Yat](https://www.weizmann.ac.il/EPS/Yakir/research-activities/field-research/yatir-forest-location-and-background) (ENF) | ENF >90% of reported stand trees; total pine crown cover ~50% on ground | Tree species dominance and crown cover are DIFFERENT denominators — Yatir EC plantation tower / research forest | Numeric, different denominator |

### FLUXNET_MultiSite_8

| EC site | Reported PFT composition or cover | Percent denominator and scope | Assessment |
|---|---|---|---|
| [CZ-BK1](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (ENF) | ENF ~100% among documented spruce/fir stand species | Reported tree-species stand composition; method unspecified — Bílý Kříž forest stand | Numeric, different denominator |
| [IT-Ren](https://www.mdpi.com/2073-445X/11/11/1903) (ENF) | ENF ~97%; DNF ~3% among reported stand species | Stand species shares; census metric unspecified — Renon / Ritten tower stand | Numeric, different denominator |
| [FR-Hes](https://bg.copernicus.org/articles/23/6491/2026/) (DBF) | DBF ≳95% of 2020 basal area; remaining ≲5% unresolved | 2020 tree basal-area shares versus older stand-composition report — Hesse forest near EC tower; dates 2005 vs 2020 | Numeric, different denominator |
| [FR-FBn](https://academic.oup.com/aob/article/135/7/1361/8063930) (ENF) | ENF pine ~75% of tree basal area; EBF share UNKNOWN | Tree basal area (not canopy area or stems) — Font-Blanche mixed forest study plot | Numeric, different denominator |
| [DE-Hzd](https://meta.icos-cp.eu/resources/stations/ES_DE-Hzd) (DBF) | DBF oak regeneration; percentages unavailable | No stand PFT percentage available — Hetzdorf disturbed forest EC tower | **No measured percentage** |
| [CH-Dav](https://besjournals.onlinelibrary.wiley.com/doi/10.1002/2688-8319.70218) (ENF) | ENF Picea >99.5% of research-stand trees | Forest inventory tree species share — Seehornwald Davos research stand | Numeric, different denominator |
| [BE-Vie](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (MF) | DBF 43%; ENF 37%; unresolved 20% of reported stand composition | Stand species percentages; measurement basis unclear — Vielsalm mixed forest stand | Numeric, different denominator |
| [IT-Lav](https://lawexplores.com/carbon-water-and-energy-fluxes-of-terrestrial-ecosystems-in-italy/) (ENF) | ENF 85%; DBF 15% (tower-associated stand composition) | Tree stand species shares; specific measurement denominator not provided — Lavarone micrometeorological tower stand | Numeric, different denominator |

### FLUXNET_MultiSite_11

| EC site | Reported PFT composition or cover | Percent denominator and scope | Assessment |
|---|---|---|---|
| [BE-Bra](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (MF) | ENF 55%; DBF 23%; other 22% unresolved within reported stand species | Flechard Table S2 stand species composition, denominator unspecified — Brasschaat local pine stand within broader mixed forest | Numeric, different denominator |
| [FR-Fon](https://doi.org/10.1111/nph.13771) (DBF) | DBF ≥97% of reported tree basal area | Tree basal area — Barbeau / Fontainebleau EC forest stand | Numeric, different denominator |
| [GL-ZaH](https://www.zackenberg.dk/fileadmin/Resources/DMU/GEM/Zackenberg/pdf/vegetation-mapping-zackenberg-valley_.pdf) (GRA) | Evergreen Arctic dwarf-shrub Cassiope 53% cover; deciduous Arctic Salix 3%; moss8%; lichens3%; graminoids/forbs<1% | Mean species ground cover from FIVE 1997 Cassiope heath plots — Cassiope heath plots in Zackenberg valley, NOT the EC flux-weighted footprint | Numeric, different denominator |
| [IT-Noe](https://openpub.fmach.it/bitstream/10449/25172/2/9783642324239-c2.pdf) (CSH) | At least 75% woody shrub share of *vegetated* surface (Juniperus53 + Pistacia22), other share unresolved | Fraction of already vegetated ground; reported total ground cover varies ~42-91% in area — Arca di Noè / Le Prigionette Mediterranean maquis study area | Numeric, different denominator |
| [AT-Neu](https://pmc.ncbi.nlm.nih.gov/articles/3899607/) (GRA) | C3 graminoids ~35%; forbs ~42%; other herbaceous ~23% of above-ground phytomass | Aboveground phytomass by plant functional group — Managed Neustift EC meadow plot | Numeric, different denominator |
| [FI-Sod](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (ENF) | ENF pine95%; unclassified other5% (stand composition) | Stand species composition; metric undefined in Table S2 — Sodankylä EC forest stand | Numeric, different denominator |
| [CH-Aws](https://pmc.ncbi.nlm.nih.gov/articles/PMC7485103/) (GRA) | Alpine herbaceous/grassland; percentages unavailable | Species/community names only — Alp Weissenstein montane pasture EC site | **No measured percentage** |
| [CH-Cha](https://www.swissfluxnet.ethz.ch/index.php/sites/site-info-ch-cha/) (GRA) | Managed C3 grass/forbs; percentages unavailable | Species mixture without component percentages — Chamau managed grassland EC site | **No measured percentage** |
| [CH-Fru](https://pmc.ncbi.nlm.nih.gov/articles/PMC7485103/) (GRA) | Total mixed herbaceous vegetation cover up to 90% of ground; grasses vs forbs UNKNOWN | Total herbaceous area cover (NOT species percentages) — Früebüel meadow/pasture ground plot | Numeric, different denominator |
| [CH-Lae](https://bg.copernicus.org/articles/21/3571/2024/) (MF) | DBF 80%; ENF 12%; other 8% unreported from listed canopy covers | Species canopy/stand cover (%) — Lägeren forest study area | Numeric, different denominator |
| [CZ-Stn](https://www.mdpi.com/2073-4433/12/9/1128) (DBF) | Pure European beech forest; no surveyed PFT area percentage | Dominance description, NOT measured 100% area — Štítná beech stand | **No measured percentage** |

### FLUXNET_MultiSite_13

| EC site | Reported PFT composition or cover | Percent denominator and scope | Assessment |
|---|---|---|---|
| [DE-Lnf](https://www.uni-goettingen.de/en/701493.html) (DBF) | Beech-dominated managed stand; no quantified fractions | Tree species qualitative — Leinefelde 130-year shelterwood stand | **No measured percentage** |
| [DE-Obe](https://fluxnet.org/sites/siteinfo/DE-Obe) (ENF) | Norway spruce dominated ENF; no quantified stand fraction | Tower site classification / stand narrative — Oberbärenburg forest flux tower | **No measured percentage** |
| [ES-Agu](https://www.mdpi.com/2072-4292/13/15/2970) (OSH) | Total vegetation ground cover ≈65%; fraction of C3 tussock grass UNKNOWN | Plot-level total vegetation ground cover — Balsa Blanca experimental plots, may not equal footprint | Numeric, different denominator |
| [ES-LJu](https://www.researchgate.net/publication/309801467_Quantifying_water_stress_effect_on_daily_light_use_efficiency_in_Mediterranean_ecosystems_using_satellite_data) (OSH) | C3 tussock-grass Festuca 19%; dwarf-shrub Genista 12%; other vegetated ≈19%; nonvegetated ≈50% | Fraction of surveyed ground cover — Llano de los Juanes EC study location | Numeric, different denominator |
| [IT-Col](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) (DBF) | DBF Fagus 100% of reported stand TREE species; natural-land area UNKNOWN | Forest stand tree species composition — Collelongo beech research forest stand | Numeric, different denominator |
| [DE-Gri](https://meta.icos-cp.eu/resources/stations/ES_DE-Gri) (GRA) | C3 grassland/forbs; species percentages unavailable | Species list only — Grillenburg managed meadow inside 40-ha clearing | **No measured percentage** |
| [DE-RuR](https://meta.icos-cp.eu/resources/stations/ES_DE-RuR) (GRA) | C3 meadow/pasture; species percentages unavailable | Species list only — Rollesbroich managed grassland EC fields | **No measured percentage** |
| [FI-Hyy](https://www.sciencedirect.com/science/article/pii/S0168192311000025) (ENF) | Scots pine >60% of trees in tower stand in one study; alternate 2020 stand pine 75–100%, spruce+birch 5–15% | Different tree-stem/stand studies (do not mix denominators) — SMEAR II tower stand vs broader Hyytiälä forest plots | Numeric, different denominator |
| [FI-Let](https://www.sciencedirect.com/science/article/pii/S0048969723040445) (ENF) | Pre-harvest ENF 80%, DBF 20% of tree BASAL AREA; post-selection-harvest ENF53%, DBF47% | Tree basal area for a selection-harvest treatment, NOT canopy ground area — Lettosuo harvested treatment plot; harvest 2016 | Numeric, different denominator |
| [FR-Pue](https://meta.icos-cp.eu/resources/stations/ES_FR-Pue) (EBF) | EBF Quercus ilex >80% OVERSTOREY canopy cover; separate stand inventory lists 95% of trees | Canopy cover versus stand species fractions, independent metrics — Puéchabon evergreen oak forest EC station | Numeric, different denominator |
| [GF-Guy](https://meta.icos-cp.eu/resources/stations/ES_GF-Guy) (EBF) | Tropical evergreen broadleaf forest; no valid numeric PFT composition | Vegetation biome/station description — Guyaflux forest EC tower French Guiana | **No measured percentage** |
| [IT-MBo](https://www.icos-italy.it/monte-bondone-it-mbo/) (GRA) | C3 grasses (Festuca+Nardus) 38% BASAL COVER; forb/legume Trifolium14.5%; remainder unknown | Herbaceous species basal cover (not carbon, leaf area or whole PFT area) — Monte Bondone permanent alpine meadow station | Numeric, different denominator |
| [IT-Tor](https://www.sciencedirect.com/science/article/abs/pii/S0168192317300515) (GRA) | Alpine C3 grassland with Nardus stricta; no site-specific percentages | Vegetation description only — Torgnon alpine managed meadow | **No measured percentage** |

## What the numbers mean in practice

### Particularly relevant physical-coverage evidence

**DE-Tha:** the ICOS station specifies spruce 72%, Scots pine 15%, larch 10%, birch 1%, other deciduous 2%. Functional assignment of that reported vegetation mixture: **ENF 87%, DNF 10%, DBF 3%**. Crucially, larch is deciduous needleleaf and must not be grouped with evergreen needleleaf.

**NL-Loo:** a site-local map within 500 m of the tower finds Scots pine 89%, other/black pine 3.3%, Douglas fir 1.3%, birch 2.3%, oak 0.6%, and open/heather/grass mosaic 3.5%: **ENF 93.6%, DBF 2.9%, open mosaic 3.5%**. Open is **not automatically bare soil** and this is not an EC flux-weighted area.

**GL-ZaH:** the original Zackenberg Cassiope-heath survey (five 1997 plots) found **Cassiope cover 53%, Salix arctica 3%, mosses 8%, lichens 3%, herbs less than 1%**. This is a local vegetation-plot cover reference; the EC footprint is heath-dominated but the entire footprint does not necessarily have these exact shares. The model parameterization also needs a valid representation of evergreen Arctic dwarf shrub.

**ES-LJu:** Festuca scariosa **19% ground cover** (C3 herbaceous) and Genista pumila **12% ground cover** (dwarf shrub), with vegetation around **50% total**. Around 19% additional vegetated cover is not taxonomically resolved; roughly half is nonvegetated. ES-Agu (Balsa Blanca) has **about 65% total vegetation cover**, dominated by Macrochloa tenacissima, but the latter's species-specific fraction is unknown.

**FR-Pue:** evergreen holm oak Quercus ilex represents **more than 80% of overstorey canopy cover** (ICOS); an independent stand species inventory says **95%**. These are different denominators and must not be combined.

### Stand-composition numbers that are real but are not ground-area targets

**DE-Hai:** beech 64%, ash 28%, sycamore 7% of **tree carbon stocks**: deciduous broadleaf class at least ~99% of those reported tree carbon components. The older Table S2 lists beech 64% and ash 27% based on a different source. **Do not substitute ~99% PFT land area**.

**IT-Lav (newly strengthened):** the Lavarone flux-tower stand description gives silver fir **70%**, Norway spruce **15%**, European beech **15%**, corresponding to **ENF 85% and DBF 15% on the reported stand-composition metric**. A separate regional 4-km² forest inventory gives different values, so the two spatial scales must not be mixed.

**CH-Lae:** canopy species cover beech 40%, ash 19%, maple 13%, linden 8%, silver fir 8%, spruce 4%. As listed, **DBF 80% and ENF 12%**, with 8% unresolved. BE-Vie has beech **43%** and Douglas fir **37%** from stand species composition, leaving 20% unresolved.

**FI-Let:** a 2016 selective-harvest *treatment* report gives tree **basal-area** shares before cutting pine 60%, spruce 20%, birch 20% (**ENF 80%, DBF 20%**), changing afterward to pine 2%, spruce 51%, birch 47% (**ENF 53%, DBF 47%**). These are time- and treatment-specific **basal-area** shares, not general horizontal tower-PFT areas. A separate older tree-volume survey gives pine 180, spruce 34 and birch 48 cubic metres/ha; keep that separate.

**IT-MBo:** grass species Festuca rubra 25% plus Nardus stricta 13% (**38% basal cover**) and Trifolium spp. 14.5% basal cover. It does not establish that 52.5% of the whole model landunit is homogeneous C3 grass.

**AT-Neu:** graminoids roughly **35%** and forbs **42%** of above-ground phytomass, leaving other phytomass types unallocated; seasonal biomass is not area.

**IL-Yat:** the tower-lab description says Aleppo pine represents **over 90% of reported forest trees**, while another study reports around **50% crown cover** of the land. Those two numbers answer distinct questions; do not force ENF ground area to >90%.

**IT-Noe:** juniper 53% and mastic tree 22% of the **already vegetated surface** of Mediterranean maquis. Juniper is a coniferous shrub, and should not be mapped automatically onto an evergreen needleleaf *tree* FATES PFT. Total vegetation/soil exposure varies spatially.

**FI-Hyy:** multiple surveys refer to different areas and dates; a study describes **more than 60% of tower-stand trees as Scots pine**, while the 2020 supplement gives pine **75–100%** with accompanying spruce/birch **5–15%**, without a comparable closed-denominator vector. No precise 60/25/15 land-area vector is claimed.

## Ten stations still lacking a defensible numerical PFT split

`DE-Hzd`, `CH-Aws`, `CH-Cha`, `CZ-Stn`, `DE-Lnf`, `DE-Obe`, `DE-Gri`, `DE-RuR`, `GF-Guy`, `IT-Tor`.

These sites need original field vegetation census or plot/quadrat cover, EC-flux footprint definition, survey date, applicable species-to-FATES type crosswalk, and some measure of uncertainty. Most have reliable broad vegetation identity (such as pine forest, beech forest, alpine grassland), but identity alone does not give land-area percentages.

## Quantitative-readiness rules for the next FATES fixed-biogeography experiments

1. Verify original source *denominator* (tree stems / tree carbon / basal area / forest volume / canopy or ground cover / area); if not an area measure, do not copy percentages into a surface-PFT area map.
2. Prefer EC footprint or mapped local-vegetation fractions from the same year, maintaining separately crop, natural vegetation, rock/bare, shrub, grass and multi-strata overstory.
3. Keep tree evergreen-needleleaf ENF distinct from larch DNF and *Juniperus* shrubs; map evergreen versus deciduous broadleaf in subtropical/Mediterranean/tropical forests carefully.
4. Confirm active case `fsurdat`, `PCT_NATVEG`, `PCT_CROP`, `fates_hlm_pft_map`, and FATES settings before constructing **new**, isolated fixed-biogeography/no-competition cases. The older CLM `PCT_NAT_PFT` surface fractions and final FATES `FATES_VEGC_PF` carbon percentages are not observed tower PFT area.

## Traceable evidence

- [Flechard et al. (2020), Table S2: European stand species composition](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf).
- [Tharandt ICOS station composition](https://meta.icos-cp.eu/resources/stations/ES_DE-Tha), [Loobos 500-m vegetation survey](https://essd.copernicus.org/articles/18/2023/2026/), [Lavarone stand](https://lawexplores.com/carbon-water-and-energy-fluxes-of-terrestrial-ecosystems-in-italy/), [Lägeren mixed-canopy composition](https://bg.copernicus.org/articles/21/3571/2024/).
- [Hainich stand tree carbon](https://bg.copernicus.org/articles/19/4315/2022/), [FI-Let 2016 selection harvesting](https://www.sciencedirect.com/science/article/pii/S0048969723040445), [ES-Agu vegetation cover](https://www.mdpi.com/2072-4292/13/15/2970), [FR-Pue ICOS holm oak cover](https://meta.icos-cp.eu/resources/stations/ES_FR-Pue).
- Exact original source URLs and alternative conflicting sources for **each of the 38 stations** are in [version-2 data table](38_site_observed_PFT_percent_evidence_v2_20261024.csv).

**No original model input, tower flux file, archived NetCDF, active experiment or prior GitHub evidence table was modified.**

