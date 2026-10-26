# AmeriFlux 50-site observed vegetation and PFT percentage evidence

**Evidence snapshot: 26 October 2026.** Membership is the five original 10-site release manifests.

**33/50 sites have at least one numerical vegetation-composition or cover lead; 17/50 have only qualitative composition, LAI/density, or model-assumption evidence in the reviewed sources.** Numerical leads include partial, local, historical and conflicting records; they are not complete prescribed PFT area vectors.

| Batch | Stations | Numerical composition/cover leads |
| --- | ---: | ---: |
| Batch01 | 10 | 7 |
| Batch02 | 10 | 8 |
| Batch03 | 10 | 5 |
| Batch04 | 10 | 8 |
| Batch05 | 10 | 5 |

A numeric percentage flag counts composition/cover evidence, including explicitly scoped historical transects. It excludes tree density and LAI alone. All scalar group aggregations retain the source denominator. No normalization fills missing components.

The separate `published_model_fcover_json` column records 11 relevant sites from [Mahmud et al. (2021), Table 1](https://doi.org/10.1029/2021JG006400). Those are site-based ORCHIDEE configurations, not measured FATES area fractions. Source-native TeBE may stand for a shrub ecosystem in that model; it is not permission to map shrubs to FATES trees.

No end-spin-up FATES PFT vector was found in the reviewed AmeriFlux GitHub records at the pinned repository snapshot. Model-output cells stay blank. This is a GitHub evidence audit, not a live IRIDIS status query.

## Reading the functional groups

ENF/NE = evergreen needleleaf; DBF/BD = deciduous broadleaf; DNF = deciduous needleleaf; EBF = evergreen broadleaf. Grass/herbaceous and shrub functional mappings require species traits and the actual parameter file. Bare ground is a surface fraction, not a living FATES PFT. Ground cover can overlap vertically; basal area, stems, biomass, LAI, crown cover and modeled vegetation carbon are distinct quantities.

## Batch01

### BR-Ma2 — Cuieiras K34

**Vegetation:** Primary terra firme tropical evergreen broadleaf rainforest

**Reported composition:** No measured tower PFT percentage recovered; earlier EBF100 is a published model scenario.

**Functional interpretation:** Tropical evergreen broadleaf dominant; measured area share unresolved

**Measurement basis:** ORCHIDEE MODEL ASSUMED FOREST COVER; NOT K34 MEASURED PFT AREA **Period:** Not specified

**Spatial scope:** K34 tower forest; AmazonFACE plots are separate **Bare ground:** Not quantified for whole tower ground; no bare=0 inference

**Evidence:** `QUALITATIVE_ONLY`. GITHUB_EXISTING_EVIDENCE_RETAINED. Official tower metadata and Chen et al. 2019 model precedent. Locator: Official overview; model precedent cannot validate field area [source 1](https://doi.org/10.1029/2018MS001565), [source 2](https://ameriflux.lbl.gov/sites/siteinfo/BR-Ma2).

**Candidate and limits:** 1:broadleaf_evergreen_tropical_tree K34 field botanical fraction not measured; point surface and FATES cold-start mechanism must be checked

**Next evidence:** Retrieve dated complete tower inventory with consistent area denominator and verify actual FATES parameter names before case setup.

### CA-Ca3 — Buckley Bay HDF88

**Vegetation:** Pole/sapling Douglas-fir stand

**Reported composition:** Douglas-fir75%; western red cedar21%; grand fir4%.

**Functional interpretation:** ENF100% of listed tree cover types

**Measurement basis:** SITE STAND TREE COVER TYPE; NOT FULL EC FOOTPRINT / INITIAL FATES BIOMASS **Period:** 2002-era stand description in 2009 paper

**Spatial scope:** HDF88 stand110ha; annual80% flux source area17ha **Bare ground:** Not quantified for whole tower ground; no bare=0 inference

**Evidence:** `NUMERIC_SPECIES`. PRIMARY_TABLE_RECHECKED. Krishnan et al. 2009, Interannual variability of the carbon balance of three different-aged Douglas-fir stands. Locator: Table1, HDF88 tree cover type; prose planting percentages are inconsistent with table [source 1](https://doi.org/10.1029/2008JG000912).

**Candidate and limits:** 2:needleleaf_evergreen_extratrop_tree Initial stand size and understory unknown; EC footprint representativeness to verify

**Next evidence:** Retrieve dated complete tower inventory with consistent area denominator and verify actual FATES parameter names before case setup.

### CA-Cbo — Borden Forest

**Vegetation:** Naturally regenerated mixed deciduous forest

**Reported composition:** 2006 living-stem species percentages: red maple52.2; white pine13.5; large-tooth aspen7.7; white ash7.1; beech5.6; hemlock3.3; trembling aspen2.5; red ash2.0; black cherry1.9; red pine1.9; elm1.1; sugar maple0.9; yellow birch0.5; choke cherry0.1.

**Functional interpretation:** DBF81.6%; ENF18.7%; rounded sum100.3

**Measurement basis:** 2006 TREE STEM-COUNT SHARES; ROUNDED SUM=100.3 NOT AREA **Period:** 2006

**Spatial scope:** Borden census plots; tower-footprint equivalence not quantified **Bare ground:** Not quantified for whole tower ground; no bare=0 inference

**Evidence:** `NUMERIC_STEMS`. PRIMARY_TABLE_RECHECKED_AUTHOR_COPY. Teklemariam et al. 2009, Eight years of carbon dioxide exchange above a mixed forest at Borden, Ontario. Locator: Table1; living stems; no normalization applied [source 1](https://doi.org/10.1016/j.agrformet.2009.07.011), [source 2](https://www.researchgate.net/publication/223845196_Eight_years_of_carbon_dioxide_exchange_above_a_mixed_forest_at_Borden_Ontario).

**Candidate and limits:** 6:broadleaf_colddecid_extratrop_tree;2:needleleaf_evergreen_extratrop_tree Avoid treating rounded 100.3 as literal FATES area shares; CA-Cbo ZBOT TA source matching BLOCKED; grid crop=26.7178%

**Next evidence:** Retrieve dated complete tower inventory with consistent area denominator and verify actual FATES parameter names before case setup.

### CA-LP1 — Kennedy Siding MPB-06

**Vegetation:** Mountain pine beetle-attacked lodgepole pine stand

**Reported composition:** Brown et al.2010 Table1 MPB-06: juvenile Pinus contorta7470, Abies100, Picea110 stems/ha; total7680. Calculated lodgepole share97.265625% within these three tabled seedling/sapling groups.

**Functional interpretation:** ENF100% only within the tabled juvenile conifer subset; whole canopy unresolved

**Measurement basis:** STEM DENSITIES FOR THREE TABLED SEEDLING/SAPLING SPECIES ONLY; NOT WHOLE OVERSTORY PFT COVER **Period:** Study2007-2008; tower installedJuly2006; juvenile-census year not explicit

**Spatial scope:** MPB-06 Kennedy Siding; three NFI-style ground plots per site,120 degrees apart and50m from tower; not MPB-03 **Bare ground:** Not quantified for whole tower ground; no bare=0 inference

**Evidence:** `NUMERIC_STEMS_SUBSET`. PRIMARY_TABLE_RECHECKED_AUTHOR_COPY. Brown et al.2010, Impact of mountain pine beetle on the net ecosystem production of lodgepole pine stands in British Columbia. Locator: Original Table1 p256, MPB-06 seedling/sapling column; section2.1 sampling. Understory mosses, lichens and dwarf shrubs are separate. [source 1](https://doi.org/10.1016/j.agrformet.2009.11.008), [source 2](https://www.researchgate.net/publication/220009719_Impact_of_mountain_pine_beetle_on_the_net_ecosystem_production_of_lodgepole_pine_stands_in_British_Columbia).

**Candidate and limits:** 2:needleleaf_evergreen_extratrop_tree MPB-06 NOT MPB-03; canopy death/demography and understory not captured by one static percentage; do NOT use 92/8 from MPB-03

**Next evidence:** Retrieve dated complete tower inventory with consistent area denominator and verify actual FATES parameter names before case setup.

### CA-Man — BOREAS NSA old black spruce

**Vegetation:** Northern old black spruce boreal forest with some larch

**Reported composition:** Black spruce99% of total overstory basal area; deciduous component<1%.

**Functional interpretation:** ENF99%; residual~1% unassigned

**Measurement basis:** BLACK SPRUCE SHARE OF OVERSTORY BASAL AREA; NOT TOTAL LAND AREA **Period:** 1999-2000

**Spatial scope:** NOBS/NSA-OBS; four census plots **Bare ground:** Not quantified for whole tower ground; no bare=0 inference

**Evidence:** `NUMERIC_BASAL_AREA`. PRIMARY_TABLE_RECHECKED. Litvak et al. 2003, Effect of stand age on whole ecosystem CO2 exchange in the Canadian boreal forest. Locator: Table2 OBS canopy; seedlings and moss excluded [source 1](https://doi.org/10.1029/2001JD000854).

**Candidate and limits:** 2:needleleaf_evergreen_extratrop_tree;3:needleleaf_colddecid_extratrop_tree [unverified minor component] Remaining 1% not proven larch; CA-Man ZBOT TA mapping BLOCKED

**Next evidence:** Retrieve dated complete tower inventory with consistent area denominator and verify actual FATES parameter names before case setup.

### CA-TP1 — Turkey Point plantation2002

**Vegetation:** Young white pine plantation on former sandy agricultural field

**Reported composition:** Source says the tree stand consists entirely of white pine; ENF100 within the described trees is an interpretation of this categorical statement, not a measured site-area percentage.

**Functional interpretation:** ENF100% of described tree stand

**Measurement basis:** PUBLISHED TREE SPECIES COMPOSITION; DENOMINATOR IN SOURCE NOT FULLY VERIFIED **Period:** 2019 age17 stand description; flux2003-2019

**Spatial scope:** Turkey Point planted stand; understory bryophytes/grasses separate **Bare ground:** Not quantified for whole tower ground; no bare=0 inference

**Evidence:** `QUALITATIVE_SINGLE_SPECIES_ASSERTION`. PRIMARY_TEXT_RECHECKED. Arain et al. 2022, Heat and drought impact on carbon exchange in an age-sequence of temperate pine forests. Locator: Methods, site description; percentage basis not specified as area [source 1](https://doi.org/10.1186/s13717-021-00349-7).

**Candidate and limits:** 2:needleleaf_evergreen_extratrop_tree Forest establishment year 2002 vs ref surface 2000 has 56.8459% crop; sapling initial structure needed

**Next evidence:** Retrieve dated complete tower inventory with consistent area denominator and verify actual FATES parameter names before case setup.

### CA-TP3 — Turkey Point plantation1974

**Vegetation:** White pine plantation

**Reported composition:** White pine94%; jack pine5%; oak1%.

**Functional interpretation:** ENF99%; DBF1% of reported tree composition

**Measurement basis:** PUBLISHED TREE SPECIES COMPOSITION; DENOMINATOR NOT VERIFIED AS COVER **Period:** 2019 age45 stand description; flux2003-2019

**Spatial scope:** Turkey Point planted stand; ground bryophytes separate **Bare ground:** Not quantified for whole tower ground; no bare=0 inference

**Evidence:** `NUMERIC_SPECIES`. PRIMARY_TEXT_RECHECKED. Arain et al. 2022, Heat and drought impact on carbon exchange in an age-sequence of temperate pine forests. Locator: Methods, site description; denominator not specified as cover [source 1](https://doi.org/10.1186/s13717-021-00349-7).

**Candidate and limits:** 2:needleleaf_evergreen_extratrop_tree;6:broadleaf_colddecid_extratrop_tree Forest ref surface 2000 has 56.8459% crop; stand structure and PFT biogeography still unchecked

**Next evidence:** Retrieve dated complete tower inventory with consistent area denominator and verify actual FATES parameter names before case setup.

### CA-TP4 — Turkey Point plantation1939

**Vegetation:** White pine plantation

**Reported composition:** White pine82%; balsam fir11%; native Carolinian broadleaf7%.

**Functional interpretation:** ENF93%; DBF7% of reported tree composition

**Measurement basis:** PUBLISHED TREE SPECIES COMPOSITION; DENOMINATOR NOT VERIFIED AS COVER **Period:** 2019 age80 stand description; flux2003-2019

**Spatial scope:** Turkey Point planted stand **Bare ground:** Not quantified for whole tower ground; no bare=0 inference

**Evidence:** `NUMERIC_SPECIES`. PRIMARY_TEXT_RECHECKED. Arain et al. 2022, Heat and drought impact on carbon exchange in an age-sequence of temperate pine forests. Locator: Methods, site description; denominator not specified as cover [source 1](https://doi.org/10.1186/s13717-021-00349-7).

**Candidate and limits:** 2:needleleaf_evergreen_extratrop_tree;6:broadleaf_colddecid_extratrop_tree Forest ref surface 2000 has 56.8459% crop; PFT traits and age structure still unchecked

**Next evidence:** Retrieve dated complete tower inventory with consistent area denominator and verify actual FATES parameter names before case setup.

### US-Aud — Audubon Research Ranch

**Vegetation:** Semi-arid grassland

**Reported composition:** No independently verified measured PFT-area vector recovered; published ORCHIDEE site configuration C4grass70%, bare30%.

**Functional interpretation:** C4 grass dominant; field fractions unresolved

**Measurement basis:** PUBLISHED ORCHIDEE SITE MODEL FRACTION ASSUMPTION; NOT EC TOWER FOOTPRINT SURVEY **Period:** Published configuration2004-2009

**Spatial scope:** Site-average fCover used by ORCHIDEE **Bare ground:** 30% only as published/operator-selected model cover assumption

**Evidence:** `MODEL_ASSUMPTION_ONLY`. PUBLISHED_MODEL_TABLE_RECHECKED. Mahmud et al.2021, Optimizing Carbon Cycle Parameters Drastically Improves Terrestrial Biosphere Model Underestimates of Dryland Mean Net CO2 Flux and its Inter-Annual Variability. Locator: Table1; prior operator-selected design70/30 retained, not observation [source 1](https://doi.org/10.1029/2021JG006400).

**Candidate and limits:** 14:c4_grass;BARE_GROUND:not_a_FATES_PFT Bare fraction belongs to surface/land units, not fates_pftname; existing surface NATVEG=88.9672% CROP=11.0328%; area policy and actual FATES implementation pending

**Separate published model configuration:** `{"BS": 30, "C4G": 70}` (2004-2009; source-native ORCHIDEE groups). [Table 1](https://doi.org/10.1029/2021JG006400).

**Next evidence:** Retrieve dated complete tower inventory with consistent area denominator and verify actual FATES parameter names before case setup.

### US-Bar — Bartlett Experimental Forest

**Vegetation:** Northern temperate hardwood deciduous forest

**Reported composition:** Reported tree composition: red maple29%; beech25%; eastern hemlock14%; yellow birch9%; paper birch6%; ash5%; sugar maple5%; large-tooth aspen4%; minor other conifers unspecified. Named species sum97%.

**Functional interpretation:** DBF83%; ENF>=14%; residual unresolved

**Measurement basis:** Published species-composition percentages; paper does not explicitly state stems, basal area or horizontal cover **Period:** Paper flux period2004-2016; composition-survey date unspecified

**Spatial scope:** Bartlett tower forest;2004 inventory of12 FIA-style plots across1x1km centered on tower; composition percentage basis not explicit **Bare ground:** Not quantified for whole tower ground; no bare=0 inference

**Evidence:** `NUMERIC_SPECIES_DENOMINATOR_UNSPECIFIED`. PRIMARY_AUTHOR_COPY_RECHECKED_DENOMINATOR_UNSPECIFIED. Ouimette et al.2018, Carbon fluxes and interannual drivers in a temperate forest ecosystem assessed through comparison of top-down and bottom-up approaches. Locator: Section2.1 PDFp4 species composition; PDFp5 plot inventory [source 1](https://doi.org/10.1016/j.agrformet.2018.03.017), [source 2](https://escholarship.org/content/qt1s69x9mm/qt1s69x9mm.pdf).

**Candidate and limits:** 6:broadleaf_colddecid_extratrop_tree;2:needleleaf_evergreen_extratrop_tree Named DBF83 and hemlock14 leave3 percentage points unresolved/rounding. Other conifers are mentioned but ENF17 is not established; percentage denominator and survey date remain unclear.

**Next evidence:** Retrieve dated complete tower inventory with consistent area denominator and verify actual FATES parameter names before case setup.

## Batch02

### US-BZS — Bonanza Creek Black Spruce

**Vegetation:** Open black-spruce peat-plateau forest; evergreen shrubs, feather moss and lichens beneath the trees.

**Reported composition:** Euskirchen et al. (2014) report approximately 20% tree cover at the permafrost forest. Evergreen-shrub understory includes Rhododendron groenlandicum, Vaccinium vitis-idaea and Oxycoccus microcarpus. Ground layer is dominated by lichens and feather moss. Exact remaining PFT cover values were not transcribed from Figure 3.

**Functional interpretation:** Needleleaf evergreen tree cover about 20%, plus evergreen shrubs and nonvascular ground cover; overlapping strata prevent complementing tree cover to bare ground.

**Measurement basis:** Point-intercept cover: species hit at least once / all sampling points; multilayer total may exceed 100%. Four 100 m cardinal transects with points every 2 m. **Period:** Study 2010–2013; exact vegetation-sampling date not specified in the read Methods.

**Spatial scope:** Permafrost-forest tower at the APEX peat-plateau site, corresponding to US-BZS; tower footprints of the three ecosystem sites reported distinct. **Bare ground:** Not quantified; 80% non-tree area is not 80% bare soil.

**Evidence:** `NUMERIC_GROUND_COVER_PARTIAL`. Official search-index overview and primary full text read on 2026-10-26; exact Figure 3 bar heights not digitized.. AmeriFlux US-BZS; Euskirchen et al. 2014, Differential response of carbon fluxes to climate in three peatland ecosystems that vary in the presence and stability of permafrost. Locator: Official site Overview; paper Sections 2.3 and 3.1, Figure 3. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-BZS), [source 2](https://doi.org/10.1002/2014JG002683).

**Candidate and limits:** Qualitative candidate: boreal needleleaf evergreen trees + broadleaf evergreen shrubs; preserve moss/lichen as separate nonvascular cover. ENF metadata is compatible with an open peatland tree canopy and cannot establish 100% tree PFT. Vertical cover overlap and nonvascular representation matter.

**Next evidence:** Retrieve Figure 3 source data/BADM vegetation cover and inventory sampling date; reconcile with the active FATES parameter set.

### US-CMW — Charleston Mesquite Woodland

**Vegetation:** Groundwater-accessing velvet mesquite (Prosopis velutina) woodland with rain-responsive understory, notably big sacaton (Sporobolus wrightii), herbs and shrubs.

**Reported composition:** USGS SIR2005-5163 reports mesquite canopy fraction 0.74 for Charleston in 2001–2003, estimated from high-resolution aerial photographs within 100 m of tower. Lee et al. (2021) separately describe approximately 80% total vegetation cover; this is not an exclusive tree/grass partition.

**Functional interpretation:** Broadleaf deciduous mesquite canopy 74% (historical horizontal crown cover); understory includes C4 bunchgrass but its area fraction is not reported in the passages read.

**Measurement basis:** Mesquite crown projection / ground area within 100 m of flux tower; total vegetation estimate in Lee2021 uses another description and must not be subtracted directly. **Period:** 2001–2003 mesquite cover; Lee2021 describes study with simulations/field observations in 2016–2017.

**Spatial scope:** Charleston mesquite site on the San Pedro River alluvial terrace; not Lewis Springs mesquite site or the separate sacaton grassland. **Bare ground:** Not determined. The 26% outside mesquite crowns includes understory/litter and cannot be called bare ground.

**Evidence:** `NUMERIC_GROUND_COVER_PARTIAL`. Official indexed overview read; USGS primary indexed text p.123 read (direct PDF returned 403); Lee2021 full text read.. AmeriFlux US-CMW; USGS Scientific Investigations Report 2005-5163, Chapter D; Lee et al. 2021, Convergent Hydraulic Redistribution and Groundwater Access Supported Facilitative Dependency Between Trees and Grasses in a Semi-Arid Environment. Locator: Official Overview; USGS p.123, canopy-fraction table and accompanying aerial-photography paragraph; Lee2021 Section 2 and Table 1. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-CMW), [source 2](https://pubs.usgs.gov/sir/2005/5163/pdf/SIR2005-5163.pdf), [source 3](https://doi.org/10.1029/2020WR028103).

**Candidate and limits:** Qualitative candidate: temperate/dryland broadleaf deciduous tree + C4 grass + other understory; exact FATES vector unresolved. 74% mesquite crown cover is not 74% of stems, basal area, or normalized vegetation-only PFT. Groundwater supply is critical to representation.

**Next evidence:** Retrieve BADM/field quadrat understory cover with seasonal date and an explicit canopy/ground-cover convention.

### US-EML — Eight Mile Lake Permafrost thaw gradient, Healy Alaska

**Vegetation:** Moist acidic tussock tundra dominated by Eriophorum vaginatum and Vaccinium uliginosum; deciduous/evergreen dwarf shrubs and moss/lichen ground layer.

**Reported composition:** Primary site description identifies Eriophorum vaginatum sedges; Vaccinium uliginosum, Rubus chamaemorus, Betula nana and Ledum palustre shrubs; Sphagnum, Dicranum, feather moss and lichens. No tower-footprint numerical functional fractions were verified in the sources read.

**Functional interpretation:** C3 sedge/graminoid + deciduous and evergreen shrubs + nonvascular vegetation; OSH is not a shrub-only numerical fraction.

**Measurement basis:** No verified fractional denominator. **Period:** Belshe2012 landscape study; Schuur laboratory site description; current AmeriFlux metadata checked 2026-10-26.

**Spatial scope:** Eight Mile Lake moist tundra/permafrost-thaw gradient; broader watershed land-cover classes are not the tower footprint. **Bare ground:** Not quantified in verified sources.

**Evidence:** `QUALITATIVE_ONLY`. Official indexed metadata, PI website and primary journal site description read.. AmeriFlux US-EML; Schuur Lab Eight Mile Lake; Belshe et al. 2012, Incorporating spatial heterogeneity created by permafrost thaw into a landscape carbon estimate. Locator: Official Overview; PI laboratory site vegetation paragraph; Belshe2012 Section 2.1. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-EML), [source 2](https://www2.nau.edu/schuurlab-p/EightMileLake.html), [source 3](https://doi.org/10.1029/2011JG001836).

**Candidate and limits:** Qualitative candidate: arctic C3 graminoid/sedge + boreal deciduous and evergreen shrubs; retain moss/lichen separately. Thaw gradient shifts from sedge toward shrub communities; watershed spatial heterogeneity and sampling year must be matched before deriving fractions.

**Next evidence:** Use footprint-matched BADM or point-intercept plots; Belshe2012 mapped land-cover and subsequent EML vegetation datasets are evidence leads, not borrowed tower fractions.

### US-GLE — GLEES

**Vegetation:** High-elevation Engelmann spruce/subalpine fir forest substantially disturbed by spruce beetle.

**Reported composition:** Frank et al. (2014) Section 2.1: Picea engelmannii 72% of stems and 84% of basal area; Abies lasiocarpa constitutes the remainder (derived 28% stems, 16% basal area). AmeriFlux reports outbreak peaking in 2008 with mortality of 85% of forested basal area.

**Functional interpretation:** The reported two-species tree inventory comprises evergreen needleleaf taxa. This establishes tree functional identity, while vegetation/ground area and living fractions remain separate.

**Measurement basis:** Tree stems and tree basal area; not horizontal land cover. Composition inventory cited to Speckman manuscript in preparation in Frank2014. **Period:** Historical stand context in 2014 paper; exact species inventory date not stated in Section 2.1. Beetle outbreak peaked in 2008.

**Spatial scope:** GLEES AmeriFlux forest near 41°21.992′N,106°14.397′W; not the whole Medicine Bow National Forest. **Bare ground:** Not quantified; 85% basal-area mortality is not 85% bare ground.

**Evidence:** `NUMERIC_BASAL_AREA_AND_STEMS`. Official overview and primary journal indexed methods read; USDA primary PDF indexed with matching text.. AmeriFlux US-GLE; Frank et al. 2014, Ecosystem CO2/H2O fluxes are explained by hydraulically limited gas exchange during tree mortality from spruce bark beetles. Locator: Official Overview disturbance paragraph; Frank2014 Section 2.1. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-GLE), [source 2](https://doi.org/10.1002/2013JG002597).

**Candidate and limits:** Needleleaf evergreen trees dominate historical tree population; no areal 100% vector approved. Historical composition cannot be applied as a living-canopy fraction after beetle mortality; inventory timing and canopy recovery unresolved.

**Next evidence:** Obtain dated live/dead spruce/fir census, understory regrowth and ground-cover observations through the modeled years.

### US-Ha1 — Harvard Forest EMS Tower (HFR1)

**Vegetation:** Mixed temperate forest dominated by red oak/red maple with hemlock and pine components.

**Reported composition:** Richardson et al. (2009) report basal-area percentages: red oak 36, red maple 22, other hardwoods 14, eastern hemlock 13, red pine 8, white pine 6. Rounded sum 99%. Thus reported broadleaf deciduous groups total 72% and needleleaf evergreen groups 27%.

**Functional interpretation:** Historical measured basal-area grouping: BDT 72%, NET 27%, 1% rounding/unallocated; this is not a crown-cover vector.

**Measurement basis:** Basal area of the historical EMS stand; primary paper rounded species/group percentages. **Period:** Historical site composition quoted in 2009 paper; exact inventory date not specified there. Paper uses Harvard fluxes 1992–2004.

**Spatial scope:** Harvard EMS tower, distinct from Harvard hemlock (US-Ha2), Little Prospect Hill and the harvested Simes Lot. **Bare ground:** Not quantified; basal-area shares carry no bare-soil information.

**Evidence:** `NUMERIC_BASAL_AREA`. Primary PDF p.322 read. HF069 metadata and latest hf069-12 CSV through 2024 retrieved; latest calculation not adopted pending temporal/live-tree aggregation audit.. AmeriFlux US-Ha1; Richardson et al. 2009, Influence of spring phenology on seasonal and annual carbon balance in two contrasting New England forests; HF069 v47 Biomass Inventories at Harvard Forest EMS Tower since 1993. Locator: Official Overview; Richardson2009 p.322 Study sites; HF069 Methods Trees and tables hf069-09, hf069-12. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Ha1), [source 2](https://doi.org/10.1093/treephys/tpn040), [source 3](https://harvardforest1.fas.harvard.edu/exist/apps/datasets/showData.html?id=hf069), [source 4](https://doi.org/10.6073/pasta/83d7c9df96f1a151b5375662d81784ad).

**Candidate and limits:** Provisional historical basal-area proxy: BDT 72/99=72.73%, NET 27/99=27.27% of reported tree basal area; explicit normalization, not measured land-cover fractions. Rounded historical values; canopy footprint and species composition change. Latest HF069 summary values require checking against live-tree date-resolved hf069-09 before use.

**Next evidence:** Recompute yearly live-tree basal-area shares from HF069 using the 34 EMS plots, excluding A4/A5/B5/G3/H3/H4 and all harvest plots; preserve DBH≥10 cm threshold and plot/date selection.

### US-Ho1 — Howland Forest (main tower)

**Vegetation:** Spruce-hemlock dominated temperate/boreal transitional forest with other conifers and a hardwood minority.

**Reported composition:** Richardson et al. (2009) report basal area: Picea rubens 44%, Tsuga canadensis 26%, other conifers 21%, hardwoods 8% (chiefly Acer rubrum and Betula papyrifera). Rounded sum 99%; conifer groups total 91%.

**Functional interpretation:** Historical tree basal area: NET 91%, BDT 8%, 1% rounded/unallocated.

**Measurement basis:** Historical stand tree basal area; rounded species/group proportions, not land area. **Period:** Historical composition attributed to Hollinger1999; restated 2009. Main-tower flux study uses 1996–2004.

**Spatial scope:** Main Howland research tower; do not copy into west or harvested tower as exact tower-specific vector. **Bare ground:** Not quantified.

**Evidence:** `NUMERIC_BASAL_AREA`. Primary PDF text read; official site metadata retrieved via official search listing.. AmeriFlux US-Ho1; Richardson et al. 2009, Influence of spring phenology on seasonal and annual carbon balance in two contrasting New England forests; Hollinger et al. 2004, Spatial and temporal variability in forest–atmosphere CO2 exchange. Locator: Official site identifier; Richardson2009 p.322 Study sites; Hollinger2004 Methods p.1690 and Results p.1692. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1), [source 2](https://doi.org/10.1093/treephys/tpn040), [source 3](https://doi.org/10.1111/j.1365-2486.2004.00847.x).

**Candidate and limits:** Provisional historical tree basal-area proxy NET 91/99=91.92%, BDT 8/99=8.08%; no ground-area claim. Historical rounded inventory and source location coordinates in 2009 prose are coarse. Later composition/canopy mortality may differ.

**Next evidence:** Extract dated main-tower live basal-area inventory and footprint weighting; compare with Hollinger2021 long-term measurements.

### US-Ho2 — Howland Forest (west tower)

**Vegetation:** Closed spruce-hemlock forest with fir, cedar, white pine, maple and birch.

**Reported composition:** Hollinger et al. (2004) sampled 48 plots around each main/west tower. Pooled descriptive groups: spruce + hemlock about 69% live basal area; maple + birch + white pine together 17%; remaining basal area mostly northern white cedar. West-tower total live basal area 56.7±16.5 m²/ha.

**Functional interpretation:** Evergreen conifer majority demonstrated, but the 17% mixed conifer/hardwood group prevents an exact west-tower NET/BDT split.

**Measurement basis:** Live tree basal area; composition is described jointly for two tower plot populations, not a separately tabulated Ho2 PFT partition. **Period:** Historical 2004 publication; exact inventory date not explicit in the read vegetation methods.

**Spatial scope:** 48 circular plots per tower, radius 7.315 m, at 50/100/200/400 m along 30-degree azimuths; main and west towers separated ~775 m. **Bare ground:** Not quantified.

**Evidence:** `NUMERIC_BASAL_AREA_PARTIAL_POOLED`. Official DOI description and primary PDF methods/results read.. AmeriFlux FLUXNET US-Ho2; Hollinger et al. 2004, Spatial and temporal variability in forest–atmosphere CO2 exchange. Locator: Official DOI dataset description; Hollinger2004 pp.1690 and 1692. [source 1](https://ameriflux.lbl.gov/doi/FLUXNET/US-Ho2/), [source 2](https://doi.org/10.1111/j.1365-2486.2004.00847.x).

**Candidate and limits:** Qualitative candidate: NET dominant + BDT minority; exact fractions unresolved. Pooled composition and a mixed 17% group cannot supply two exclusive PFT fractions. Absolute west BA is not a PFT fraction.

**Next evidence:** Obtain Ho2 species-resolved live inventory, survey year and tower-specific plot-weighted composition.

### US-Ho3 — Howland Forest (harvest site)

**Vegetation:** Spruce-hemlock forest subject to shelterwood harvest, with other conifers and hardwoods.

**Reported composition:** Official metadata calls the site a closed conifer forest. The site-listed Scott et al. (2004) harvest study reports preharvest basal area about 30 m²/ha and removal just under 30% of aboveground biomass. No verified postharvest numerical PFT composition was found.

**Functional interpretation:** Needleleaf evergreen majority qualitatively supported; disturbance amount is not a PFT partition.

**Measurement basis:** Absolute preharvest stand basal area and fraction of biomass removed, not species percentages or land-cover area. **Period:** Shelterwood harvest 2001–2002; Scott2004 initial postharvest report; current site metadata checked 2026-10-26.

**Spatial scope:** Harvest tower and managed stand; distinct from the main and west unmanaged tower areas. **Bare ground:** Not quantified; 30% biomass removal cannot be treated as 30% bare soil.

**Evidence:** `QUALITATIVE_ONLY_WITH_DISTURBANCE_NUMERIC`. Official metadata and USDA primary abstract read; exact species-level harvest/postharvest inventory not obtained.. AmeriFlux US-Ho3; Scott et al. 2004, Changes in carbon storage and net carbon exchange one year after an initial shelterwood harvest at Howland Forest, ME. Locator: Official Overview and listed publication; USDA primary publication abstract. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Ho3), [source 2](https://research.fs.usda.gov/treesearch/15706), [source 3](https://doi.org/10.1007/s00267-003-9114-5).

**Candidate and limits:** Qualitative candidate NET dominant + BDT minority with explicit disturbance history; no exact vector. AmeriFlux generic 'minimal disturbance' description conflicts with harvest designation/history; pre/post harvest and regrowth must be handled separately.

**Next evidence:** Retrieve Scott2004 species-resolved pre/post inventories and recent Ho3 BADM; retain harvest years in initialization/management metadata.

### US-ICh — Imnavait Creek Watershed Heath Tundra

**Vegetation:** Dry ridge heath tundra with dwarf evergreen/deciduous shrubs, lichen and sedges; surroundings include extensive tussock tundra.

**Reported composition:** Cristóbal et al. (2017) report vegetation communities around the Heath tower as 20% heath, 72% tussock tundra, with the remaining 8% jointly sedge meadow and bare soil (8% derived complement). Species-level primary description identifies Dryas integrifolia, Carex, dwarf shrubs and lichens.

**Functional interpretation:** Numerical community-patch mixture, not a direct shrub/graminoid PFT split. Both heath and tussock communities contain multiple growth forms.

**Measurement basis:** Area proportions of vegetation community types around tower; mapping radius/precise footprint weighting not specified in the read paragraph. **Period:** 2008–2012 study period; underlying community-map date not explicit in quoted description.

**Spatial scope:** Heath/Ridge tower near 68.607 N,149.296 W; not the full Imnavait catchment and not the Tussock tower. **Bare ground:** Included with sedge meadow in the 8% remainder; separate bare-soil fraction unresolved (cannot assign all 8% to bare ground).

**Evidence:** `NUMERIC_COMMUNITY_COVER_NOT_PFT`. Official indexed overview and primary HESS PDF text read; Zona primary full-text species paragraph read.. AmeriFlux US-ICh; Cristóbal et al. 2017, Estimation of surface energy fluxes in the Arctic tundra using the remote sensing thermal-based Two-Source Energy Balance model; Zona et al. 2023, Pan-Arctic soil moisture control on tundra carbon sequestration and plant productivity. Locator: Official Overview; Cristóbal2017 Section 4.1 pp.1344–1345, especially p.1345; Zona2023 Section 2.1. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-ICh), [source 2](https://doi.org/10.5194/hess-21-1339-2017), [source 3](https://doi.org/10.1111/gcb.16487).

**Candidate and limits:** Qualitative candidate arctic evergreen + deciduous shrubs, C3 sedge/graminoids and moss/lichen; include spatial mixing sensitivity. Published CAVM class/table can mislabel Heath as G4, while PI-informed text calls it dry heath. Patch proportions and functional cover require reconciliation; nonvascular cover overlaps vascular canopy.

**Next evidence:** Obtain tower-specific point-intercept PFT cover and original community map, including separate sedge-meadow and bare-soil areas and footprint weights.

### US-ICt — Imnavait Creek Watershed Tussock Tundra

**Vegetation:** Moist acidic tussock tundra dominated by Eriophorum vaginatum, Sphagnum and dwarf shrubs such as Betula nana and Salix.

**Reported composition:** Cristóbal et al. (2017) report 95% tussock-tundra vegetation community around the Tussock tower. The remaining 5% is not classified in the read paragraph. Species composition within the community is qualitative, not 95% sedge.

**Functional interpretation:** C3 sedge/graminoids + deciduous/evergreen dwarf shrubs + moss; 95% describes community area rather than a single PFT.

**Measurement basis:** Area proportion of vegetation community type around the Tussock tower, not a sedge-only or vegetation-only PFT denominator. **Period:** 2008–2012 study period; exact mapping date not stated.

**Spatial scope:** Biocomplexity/Tussock tower near 68.606 N,149.304 W. **Bare ground:** Not quantified; unclassified 5% cannot be assigned to bare ground.

**Evidence:** `NUMERIC_COMMUNITY_COVER_NOT_PFT`. Official DOI description and primary HESS PDF text read; IGBP OSH corroborated by Batch02 release-metadata README.. AmeriFlux FLUXNET US-ICt; Cristóbal et al. 2017, Estimation of surface energy fluxes in the Arctic tundra using the remote sensing thermal-based Two-Source Energy Balance model. Locator: Official DOI site description; HESS Section 4.1 pp.1344–1345, Table 1 coordinates. [source 1](https://ameriflux.lbl.gov/doi/FLUXNET/US-ICt/), [source 2](https://ameriflux.lbl.gov/sites/siteinfo/US-ICt), [source 3](https://doi.org/10.5194/hess-21-1339-2017).

**Candidate and limits:** Qualitative candidate C3 sedge/graminoid + boreal deciduous and evergreen shrubs; preserve moss/nonvascular coverage separately. A single 95% tussock-community proportion cannot resolve within-community PFT mixtures; multilayer cover and spatial radius are unspecified.

**Next evidence:** Retrieve original point-intercept species/PFT cover, community-map metadata, and separate background nonvascular/bare-surface measurements.

## Batch03

### US-Kon — Konza Prairie LTER (KNZ)

**Vegetation:** Annually burned tallgrass prairie, tower in ungrazed watershed 1D. Dominant perennial C4 grasses: Andropogon gerardii, Panicum virgatum, Schizachyrium scoparium and Sorghastrum nutans; subdominant C3 grasses, forbs and woody plants occur in Konza prairie.

**Reported composition:** Graminoids, almost all grasses, account for 96% of herbaceous biomass in watershed 1D; this is NOT a measured C4 percentage or a ground-area fraction.

**Functional interpretation:** Grass-dominated biomass with C4 dominants; exact C3:C4 and woody/shrub ground-cover shares unresolved.

**Measurement basis:** Oven-dried herbaceous biomass; excludes woody biomass and bare ground. 96% graminoids, approximately 4% non-graminoid herbaceous biomass by complement. **Period:** 1984–2010 end-of-growing-season quadrat clipping; source published 2012. Tower/watershed identity cross-checked in Brunsell et al. 2017.

**Spatial scope:** Watershed 1D, upland and lowland positions; five 20×50 cm quadrats in each of four transects per landscape position. Watershed sample, not half-hourly flux-footprint-weighted vegetation. **Bare ground:** Not quantified; 4% herbaceous residual is not bare ground.

**Evidence:** `NUMERIC_HERBACEOUS_BIOMASS`. VERIFIED_PRIMARY_NUMERIC_NON_AREA_DENOMINATOR_2026-10-26. AmeriFlux US-Kon site overview; Craine et al. (2012), Timing of climate variability and grassland productivity, PNAS 109:3401–3405, doi:10.1073/pnas.1118438109; Brunsell et al. (2017), Assessing the Roles of Fire Frequency and Precipitation in Determining Woody Plant Expansion in Central U.S. Grasslands, doi:10.1002/2017JG004046. Locator: Official Overview: Vegetation IGBP and Description; Craine Materials and Methods paragraph beginning Graminoid ANPP; Brunsell section 2.1 Field Data identifies US-KON as watershed 1D and names dominant C4 grasses. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Kon), [source 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC3295284/), [source 3](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2017jg004046).

**Candidate and limits:** C4 grass dominant; C3 herbaceous contribution and any woody contribution unquantified. No exact percentage vector proposed. Official site description mentions bison/cattle introductions at the broader station; Brunsell explicitly calls the tower watershed ungrazed. Use tower-watershed evidence rather than station-wide management. Biomass share is not fractional cover, leaf area or FATES carbon share.

**Next evidence:** Retrieve contemporaneous watershed 1D species-cover records (Konza LTER vegetation transects) and the release BADM VEG_COVER/VEG_PCT records; quantify bare/rock/litter separately.

### US-Me2 — Metolius mature ponderosa pine

**Vegetation:** Before August 2020: almost entirely Pinus ponderosa overstory with scattered Calocedrus decurrens; sparse Purshia tridentata and Arctostaphylos patula understory. Fire, salvage logging and footprint relocation then changed the site.

**Reported composition:** Pre-fire overstory peak LAI 2.1 m2/m2; understory LAI 0.2 m2/m2; approximately 339 trees/ha. No observed tree-species or ground-area percentage was found. These LAIs must not be converted into ground-cover percentages.

**Functional interpretation:** Pre-fire evergreen needleleaf overstory plus broadleaf shrub understory; post-fire and post-logging composition unresolved.

**Measurement basis:** LAI per ground area, separate canopy strata; species dominance qualitative. **Period:** Pre-fire site description January 2002–August 2020. Green Ridge Fire crossed site 2020-08-20; salvage logging late March–late April 2021; primary flux system moved August 2022.

**Spatial scope:** Pre-fire stand around original tower; almost all trees within flux footprint logged except a smaller low-severity area; 2022 tower centers on salvage/regenerating footprint. **Bare ground:** Official description reports ash/bare soil in intensely burned patches, but does not provide a footprint-wide bare-ground percentage.

**Evidence:** `NUMERIC_LAI_NO_PERCENT_VECTOR`. VERIFIED_OFFICIAL_DISTURBANCE_REQUIRES_PERIOD_SPLIT_2026-10-26. AmeriFlux US-Me2 site overview and AmeriFlux BASE US-Me2 dataset description, doi:10.17190/AMF/1246076. Locator: Overview Description: Site Description before Fire; dataset description headings Green Ridge Fire and Salvage Logging, including August 2022 flux-system move. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Me2), [source 2](https://ameriflux.lbl.gov/doi/AmeriFlux/US-Me2/).

**Candidate and limits:** Pre-fire temperate evergreen needleleaf tree dominant, plus broadleaf shrubs; distinct 2020–2021 burned and post-2021 regenerating states required. No stationary exact vector proposed. ENF category is not a cover measurement. The 2002–2022 forcing release crosses fire and salvage logging. Peak overstory and understory LAIs are not species fractions; current description is not time-invariant vegetation truth.

**Next evidence:** Acquire pre/post-fire plot or lidar species and cover inventories and 2021/2022 footprint maps; date-match each modeled period and quantify live vegetation, dead boles, bare soil and regrowth separately.

### US-Me6 — Metolius Young Pine Burn

**Vegetation:** Open young Pinus ponderosa regeneration after 1979 fire, salvage logging, planting in 1986 and additional planting in 1990. Scattered Purshia tridentata and grasses, predominantly Bromus tectorum, form understory.

**Reported composition:** Ruehr et al. report 2010 summer overstory half-sided LAI 0.8 m2/m2, understory estimated LAI 0.1 m2/m2 and 162 trees/ha. Official site currently states overstory LAI 0.6 for 2010. Neither source supplies a species/ground-cover percentage vector.

**Functional interpretation:** Evergreen needleleaf trees plus broadleaf deciduous shrubs and C3 grasses; their area shares are unmeasured in the read sources.

**Measurement basis:** Leaf area per ground area and tree density; no percent-cover denominator. **Period:** 2010–2011 field observations in Ruehr et al. 2014; stand 22–26 years old then. Official overview describes an approximately 20-year-old stand.

**Spatial scope:** US-Me6 study stand; biomass inventory four plots of 17 m radius and LAI on two transects. No annual flux-footprint weighting given. **Bare ground:** Open stand and gaps are described; ground bare-soil/rock/litter fractions not quantified.

**Evidence:** `NUMERIC_LAI_NO_PERCENT_VECTOR`. VERIFIED_PRIMARY_LAI_OFFICIAL_LAI_DISCREPANCY_RETAINED_2026-10-26. AmeriFlux US-Me6 site overview; Ruehr et al. (2014), Effects of heat and drought on carbon and water dynamics in a regenerating semi-arid pine forest: a combined experimental and modeling approach, Biogeosciences 11:4139–4156, doi:10.5194/bg-11-4139-2014. Locator: Official Overview Description; Ruehr pp. 4140–4141 sections 2.1 Study site and 2.2 Observational data. Paper section 2.3.1 treats understory as pine for model simplification; that is not field composition. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Me6), [source 2](https://bg.copernicus.org/articles/11/4139/2014/bg-11-4139-2014.pdf).

**Candidate and limits:** Temperate evergreen needleleaf trees + deciduous broadleaf shrub + C3 grass, unknown fractions. 0.6 official versus 0.8 paper overstory LAI discrepancy; planted 1986 versus simplified official reforested 1990 description. Stand has regenerated through 2010–2025 release period, so early-stand LAI is not timeless.

**Next evidence:** Release BADM species cover/LAI time series and plot survey maps; resolve LAI definition/date and obtain actual tree crown, shrub, grass and bare-ground cover for modeled periods.

### US-MMS — Morgan Monroe State Forest

**Vegetation:** Secondary deciduous broadleaf forest; Acer saccharum, Liriodendron tulipifera and Quercus spp. are major canopy genera.

**Reported composition:** Denham et al. report Acer saccharum + Liriodendron tulipifera + Quercus spp. together account for 75% of stand basal area; remaining 25% is not species-resolved in this read source. All three named groups map to deciduous broadleaf trees.

**Functional interpretation:** At least the named 75% of basal area is deciduous broadleaf; no complete cover or PFT-area vector established.

**Measurement basis:** Stand tree basal area; 75% combined named species/genera, 25% unspecified residual. Not percent of ground area. **Period:** Site characterization in Denham et al. 2021, accepted 2020. Original basal-area census date is not explicit in the cited description; sap-flow study includes 2012 drought.

**Spatial scope:** Morgan Monroe tower stand, Indiana; basal-area survey extent not specified in the read source. **Bare ground:** Not quantified.

**Evidence:** `NUMERIC_BASAL_AREA_PARTIAL`. VERIFIED_PRIMARY_PARTIAL_BASAL_AREA_2026-10-26. AmeriFlux US-MMS site overview; Denham et al. (2021), Eastern US deciduous tree species respond dissimilarly to declining soil moisture but similarly to rising evaporative demand, Tree Physiology 41:944–959, doi:10.1093/treephys/tpaa153. Locator: Official Overview Vegetation IGBP; Denham p. 946 Site description paragraph beginning Morgan Monroe State Forest. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-MMS), [source 2](https://research.fs.usda.gov/download/treesearch/62689.pdf).

**Candidate and limits:** Temperate deciduous broadleaf tree dominant; residual flora and understory unquantified. Do not assign 100% from DBF label. A historical 2000 stand table exists, but it was not independently read in an official/author-hosted full text during this pass; no historical table percentages are substituted here. Exact survey date and full 25% residual need verification.

**Next evidence:** Retrieve original Schmid et al. 2000 Table 1 and modern tower plot census/BADM; preserve census year, sampled basal area and species residual before deriving PFT composition.

### US-MOz — Missouri Ozark Site

**Vegetation:** Second-growth upland oak–hickory forest with Acer saccharum understory and Juniperus virginiana, including locally disturbed areas.

**Reported composition:** Momen et al. 2017 reports basal-area shares approximately Quercus alba 39%, Juniperus virginiana 10%, Quercus velutina 9%, Carya ovata 7%, Acer saccharum 7%; sum of listed approximate shares 72%, residual approximately 28% unspecified. Geron et al. report canopy cover around tower 85–92%.

**Functional interpretation:** Named deciduous broadleaf taxa total approximately 62% of basal area; named evergreen needleleaf Juniperus approximately 10%; approximately 28% unresolved. These are partial BA shares, not ground cover.

**Measurement basis:** Species shares: total stand basal area. Separate 85–92%: total canopy cover around tower. Never merge these denominators or call canopy openings bare soil. **Period:** Momen water-potential data 2004–2010; stand-composition census date not separately given. Geron site context for PINOT NOIR 2012 published 2016.

**Spatial scope:** Baskett/MOFLUX tower stand in Missouri; canopy-cover description around tower. Species BA survey extent not explicit in Momen paragraph. **Bare ground:** Not quantified. Canopy cover 85–92% implies canopy gaps, not 8–15% bare ground; understory/litter/rock may occupy gaps.

**Evidence:** `NUMERIC_BASAL_AREA_PARTIAL_AND_CANOPY_COVER`. VERIFIED_PRIMARY_PARTIAL_BASAL_AREA_AND_COVER_2026-10-26. AmeriFlux US-MOz site overview; Momen et al. (2017), Interacting Effects of Leaf Water Potential and Biomass on Vegetation Optical Depth, doi:10.1002/2017JG004145; Geron et al. (2016), Large drought-induced variations in oak leaf volatile organic compound emissions during PINOT NOIR 2012, doi:10.1016/j.chemosphere.2015.11.086. Locator: Momen p. 3034 (PDF p. 4) MOFLUX paragraph and Table 1; Geron p. 9 (PDF p. 2), section 1.1 Site description. Geron Table 1 distinguishes MOFLUX footprint from regional FIA, so regional FIA values must not substitute tower values. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-MOz), [source 2](https://scholarworks.iu.edu/dspace/bitstreams/04b5e119-09c9-4835-a0de-c1df14871005/download), [source 3](https://pasteur.epa.gov/uploads/91/documents/Geron%20et%20al%202016%20Chemosphere.pdf).

**Candidate and limits:** Temperate deciduous broadleaf dominant with observed evergreen needleleaf component; retain unresolved remainder. No full site-area vector proposed. Strong drought and mortality in measurement period can alter composition. IGBP DBF does not establish absence of evergreen trees. Residual species remain unresolved; observation dates differ across sources.

**Next evidence:** Read complete MOFLUX inventory/BADM species table with census date and footprint map; identify residual 28%, update mortality and crown-cover fractions.

### US-Mpj — Mountainair Pinyon-Juniper Woodland

**Vegetation:** Pinus edulis and Juniperus monosperma woodland with dominant herbaceous Bouteloua gracilis, a perennial C4 grass.

**Reported composition:** Official site reports Pinus edulis + Juniperus monosperma make up >95% of tree cover; total tree cover approximately 60%. Separate species shares within the pair and herbaceous cover are not given.

**Functional interpretation:** Evergreen conifer canopy dominates tree cover; C4 grass understory present. Percent of tree cover and percent of ground must remain separate.

**Measurement basis:** >95% uses total tree cover as denominator; approximately 60% uses site ground/canopy cover area. These statements are not a complete mutually exclusive PFT-area partition. **Period:** Official undated overview; piñon mortality began July 2013 and continued through 2015. No census date supplied for 60% or >95% statements.

**Spatial scope:** Mesa approximately 25 km south of Mountainair, New Mexico, around flux site; source does not specify cover inventory plot or footprint weighting. **Bare ground:** Not measured. Approximately 40% outside tree canopy may include grass, shrubs, litter, bare soil or rock and must not be assigned to bare ground or C4 grass wholesale.

**Evidence:** `NUMERIC_TREE_COVER_PARTIAL`. VERIFIED_OFFICIAL_NUMERIC_COVER_UNDATED_DISTURBANCE_2026-10-26. AmeriFlux US-Mpj site overview, Mountainair Pinyon-Juniper Woodland. Locator: Overview Description paragraphs on >95% tree cover, approximately 60% total tree cover, Bouteloua gracilis, and 2013–2015 piñon mortality. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Mpj).

**Candidate and limits:** Evergreen needleleaf tree plus C4 grass, unknown within-pair and understory shares. Disturbance-era states required; no exact vector proposed. Piñon drought/ips mortality affected 2013–2015; juniper unaffected per official overview. BIF labels ENF/OSH/WSA retained in Batch03 history; current WSA is context, not a numerical observation. Juniper model classification may depend on parameter-set growth form.

**Separate published model configuration:** `{"BS": 20, "C4G": 20, "TeNE": 60}` (2008-2014; source-native ORCHIDEE groups). [Table 1](https://doi.org/10.1029/2021JG006400).

**Next evidence:** Retrieve before/after-mortality tree crown/species inventories and understory/bare cover; verify geographic footprint and census years before converting any proportions.

### US-MtB — Mt Bigelow

**Vegetation:** Semiarid mature second-growth mixed conifer forest dominated by Pseudotsuga menziesii, Pinus ponderosa and Pinus strobiformis; little understory vegetation.

**Reported composition:** Primary site papers identify the three major evergreen conifers, but no stand-wide species or functional percentage was verified. Yang et al. describe the sampled 1.5 ha catchment as codominated by P. menziesii and P. ponderosa; codominant is not evidence for 50:50.

**Functional interpretation:** Evergreen needleleaf forest; precise species shares and minor woody/herbaceous shares unresolved.

**Measurement basis:** None: species dominance descriptions, not percent composition. **Period:** Tower operating since 2009; cited JGR study published 2022. Selective thinning in 2012 noted by Yang et al. 2020.

**Spatial scope:** Mt Bigelow tower forest, Santa Catalina Mountains, Arizona. Yang 1.5 ha zero-order-basin catchment lies within statistical tower footprint; it is a sample scope, not the entire footprint. **Bare ground:** Not quantified; little understory does not imply quantified bare soil.

**Evidence:** `QUALITATIVE_ONLY`. VERIFIED_OFFICIAL_AND_PRIMARY_QUALITATIVE_2026-10-26. AmeriFlux US-MtB site overview; Javadian et al. (2022), Canopy Temperature Is Regulated by Ecosystem Structural Traits and Captures the Ecohydrologic Dynamics of a Semiarid Mixed Conifer Forest Site, doi:10.1029/2021JG006617; Yang et al. (2020), Tree Physiology doi:10.1093/treephys/tpaa083. Locator: Official Overview ENF; Javadian Site description paragraph lists three dominant conifers and little understory; Yang Materials and methods, Site description describes codominants, 2012 thinning and 1.5 ha footprint catchment. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-MtB), [source 2](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2021JG006617), [source 3](https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2624.pdf).

**Candidate and limits:** Temperate evergreen needleleaf tree dominant; no exact fractional vector supported. Sample catchment and full tower footprint can differ; 2012 thinning and later climate stress may change canopy structure. No numeric composition or bare-ground estimate verified.

**Next evidence:** Tower-footprint tree inventory with species basal area/crown cover, thinning records and ground-cover survey; distinguish sampled tree counts from forest abundance.

### US-NC2 — NC_Loblolly Plantation

**Vegetation:** Managed Pinus taeda plantation established 1992; subdominant/understory Acer rubrum and other broadleaf understory occur.

**Reported composition:** Official source verifies loblolly pine plantation and disturbance chronology. No complete numeric species/functional fraction verified. Noormets et al. report seasonal LAI 3.9–4.3 m2/m2 at growing-season maximum and 2.4–2.8 in winter, partly due to Acer rubrum leaf fall; these are not PFT shares.

**Functional interpretation:** Evergreen needleleaf plantation overstory with deciduous broadleaf subdominants/understory; exact shares unquantified.

**Measurement basis:** Total projected LAI per ground area; no species fraction supplied in the read primary passage. **Period:** Noormets 2012 study includes 2005–2009; official chronology: stand established 1992, drought and management in 2007, thinned October 2009, fertilization January 2011 eastern half and October 2012 whole site.

**Spatial scope:** Parker Tract lower coastal plain North Carolina tower plantation. Noormets LAI on four of thirteen vegetation survey plots; no footprint-weighted species percentages supplied. **Bare ground:** Not quantified; thinning creates canopy gaps without establishing bare-soil area.

**Evidence:** `QUALITATIVE_COMPOSITION_WITH_NUMERIC_TOTAL_LAI`. VERIFIED_OFFICIAL_AND_PRIMARY_NO_PERCENT_VECTOR_2026-10-26. AmeriFlux US-NC2 site/dataset description, doi:10.17190/AMF/1246083; Noormets et al. (2012), The role of harvest residue in rotation cycle carbon balance in loblolly pine plantations. Respiration partitioning approach, doi:10.1111/j.1365-2486.2012.02776.x. Locator: Official dataset Description; Noormets p. 3188 paragraph on US-NC2 LAI and subdominant/understory Acer rubrum. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-NC2), [source 2](https://ameriflux.lbl.gov/doi/AmeriFlux/US-NC2/), [source 3](https://research.fs.usda.gov/download/treesearch/41896.pdf).

**Candidate and limits:** Temperate evergreen needleleaf tree dominant plus temperate deciduous broadleaf understory; no exact composition vector proposed. The forcing window 2005–2025 spans substantial thinning/regrowth; chronology and crown/LAI fractions must be period-matched. Pure-pine statements from limited immediate vicinity or models do not characterize all canopy strata.

**Next evidence:** Full BADM species/cover census, pre/post-2009-thinning inventory and later rotation history; separate overstory basal area, understory LAI and ground fractions.

### US-NR1 — Niwot Ridge Forest (LTER NWT1)

**Vegetation:** Subalpine conifer forest of Abies lasiocarpa, Picea engelmannii and Pinus contorta, selectively logged in early 1900s.

**Reported composition:** Seyednasrollah et al. report Abies lasiocarpa 46%, Picea engelmannii 28%, Pinus contorta 26% by stem density. Named species sum to 100% of reported stem-density accounting.

**Functional interpretation:** Reported tree stems all evergreen needleleaf. This establishes an ENF tree-stem composition, not 100% site-area, ground-cover, LAI or vegetation-carbon fraction.

**Measurement basis:** Tree stem density in stand description, not basal area or ground area. **Period:** Site composition reported in 2021 paper; underlying tree census date not explicit. Separate pigment samples June 2017–June 2018 are not the abundance census.

**Spatial scope:** US-NR1 tower subalpine forest, approximately 3050 m elevation near Nederland, Colorado. Exact census extent not specified in cited paragraph. **Bare ground:** Not quantified. No conversion of 100% tree-stem PFT share into 0% bare ground.

**Evidence:** `NUMERIC_STEMS`. VERIFIED_PRIMARY_COMPLETE_REPORTED_TREE_STEM_ACCOUNTING_2026-10-26. AmeriFlux US-NR1 site overview; Seyednasrollah et al. (2021), Seasonal variation in the canopy color of temperate evergreen conifer forests, New Phytologist 229:2586–2600, doi:10.1111/nph.17046. Locator: Official Overview Description; Seyednasrollah p. 2588 (PDF p. 3), Materials and Methods, Niwot Ridge paragraph explicitly states stem density for each percentage. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-NR1), [source 2](https://research.fs.usda.gov/download/treesearch/63425.pdf).

**Candidate and limits:** Evergreen needleleaf tree pool; boreal/temperate FATES subtype must be checked against the actual parameter set and species trait choices. No ground-area vector proposed. Stem density differs from BA, canopy cover and carbon weighting. Site ecotone and footprint direction vary; date and exact spatial extent of abundance census are missing from paragraph.

**Next evidence:** Retrieve US-NR1 inventory census provenance, size distribution, basal-area/crown cover and understory/ground survey before parameterizing area fractions or comparing with FATES VEGC shares.

### US-NR3 — Niwot Ridge Alpine (T-Van West)

**Vegetation:** Snow-scoured alpine tundra. Official site identifies dry meadow; T-Van papers describe a mosaic of wind-scoured fellfield and dry meadow with small wet-meadow patches in tower footprints.

**Reported composition:** No site-specific numeric PFT/species cover vector verified. Regional dry-meadow sedge dominance and historical Niwot growth-form tables are not substituted for the exact US-NR3 tower footprint.

**Functional interpretation:** Alpine C3 herbaceous graminoids/forbs with possible dwarf shrubs and nonvascular vegetation; detailed footprint shares unresolved.

**Measurement basis:** None: vegetation-community descriptions; no area fractions read for the exact tower footprint. **Period:** Tower since 2007; official overview current at retrieval; cited T-Van synthesis published 2017.

**Spatial scope:** T-Van West tower at 40.0520 N, 105.5864 W, official elevation 3504 m; US-NR4 only 50 m east. Small-scale alpine heterogeneity makes US-NR3/NR4 or Saddle extrapolation unsafe. **Bare ground:** Not quantified. Snow-scoured/fellfield landscape can have rock/bare surfaces, but neither GRA nor regional cover supports 0% bare ground or a fixed number.

**Evidence:** `QUALITATIVE_ONLY`. VERIFIED_OFFICIAL_AND_PRIMARY_QUALITATIVE_FOOTPRINT_HETEROGENEITY_2026-10-26. AmeriFlux US-NR3 site overview; Wieder et al. (2017), Ecosystem function in complex mountain terrain: Combining models and long-term observations to advance process-based understanding, doi:10.1002/2016JG003704; Jay et al. (2023), Topographic Heterogeneity and Aspect Moderate Exposure to Climate Change Across an Alpine Tundra Hillslope, doi:10.1029/2023JG007664. Locator: Official Overview Description: snow-scoured/dry meadow and tower spacing; Wieder section 2.2 Model Forcing and Validation Data describes T-Van footprint mosaic and small wet patches; Jay section 2.1.1 identifies two alpine EC towers and forcing choices. [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-NR3), [source 2](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2016JG003704), [source 3](https://doi.org/10.1029/2023JG007664).

**Candidate and limits:** Cold/alpine C3 herbaceous representation; graminoid/forb/dwarf-shrub/nonvascular distinctions require explicit treatment in FATES. No exact percentage vector proposed. Official dry-meadow label and paper fellfield/dry-meadow mixture require a tower-specific map crosswalk. US-xNW is a different nearby site and must not substitute. Historical growth-form tables and model prescribed PFTs are not direct US-NR3 observations.

**Next evidence:** Acquire georeferenced T-Van West vegetation/rock/bare/nonvascular cover map and wind-dependent EC footprints; request LTER plot data closest to US-NR3 and link census date and spatial support.

## Batch04

### US-Rpf — Poker Flat Research Range: Succession from fire scar to deciduous forest

**Vegetation:** Post-2004-fire regeneration of former black-spruce forest; young aspen-birch forest and deciduous shrubs.

**Reported composition:** No numeric PFT/species fraction verified. AmeriFlux identifies deciduous trees and shrubs; Ueyama et al. (2018) identifies the sampled young forest as aspen-birch.

**Functional interpretation:** Boreal broadleaf deciduous trees plus deciduous shrubs; no measured percentage vector.

**Measurement basis:** Not reported for composition **Period:** Site operating 2008-present; primary vegetation characterization published 2018; rapid postfire succession

**Spatial scope:** US-Rpf tower near Davis Center, 65.1198 N, 147.4290 W; do not substitute US-Prr intact black-spruce site **Bare ground:** Not quantified in verified sources

**Evidence:** `QUALITATIVE_ONLY`. Official site and primary-paper abstract verified; no source-backed numerical vector located. AmeriFlux US-Rpf site overview; Ueyama et al. 2018 Leaf- and ecosystem-scale photosynthetic parameters for the overstory and understory of boreal forests in interior Alaska. Locator: AmeriFlux Overview Description; 2018 article abstract, young aspen-birch forest [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Rpf), [source 2](https://ameriflux.lbl.gov/community/publication/leaf-and-ecosystem-scale-photosynthetic-parameters-for-the-overstory-and-understory-of-boreal-forests-in-interior-alaska/), [source 3](https://www.jstage.jst.go.jp/article/agrmet/74/2/74_D-17-00031/_article/-char/en).

**Candidate and limits:** Boreal broadleaf deciduous tree and shrub PFTs; fractions unresolved Fire-driven succession changes trees/shrubs/ground layer through time; paper-birch versus aspen fractions and shrubs unquantified.

**Next evidence:** Retrieve site-year BADM species cover/density and 2019 Ueyama AFM 275:196-207 site inventory; separate 2008 early succession from later forest.

### US-Seg — Sevilleta grassland

**Vegetation:** Black-grama-dominated C4 desert grassland; August 2009 severe fire.

**Reported composition:** Duman et al. 2021 describes US-Seg as nearly monospecific C4 Bouteloua eriopoda covering approximately 60% of the surface. He et al. 2010 reports older grassland live-plus-litter cover 60% and bare soil 40%, but its listed coordinates differ from this tower.

**Functional interpretation:** Approximately 60% C4-grass surface-cover description; not a complete living-PFT vector.

**Measurement basis:** Surface area in Duman2021; older 60% value includes live vegetation plus litter and is not equivalent to living cover **Period:** Duman2021 site description, underlying cover survey date unspecified; major 2009 disturbance; Petrie2015 moved grassland observations to another unburned tower in 2010-2011

**Spatial scope:** US-Seg tower; historical BIF 34.3623 N,106.7020 W versus current overview 34.3603 N,106.7003 W. Do not transfer nearby US-Sen unburned tower composition silently. **Bare ground:** 40% only in older grassland characterization with coordinate/scope mismatch; not verified present US-Seg bare fraction.

**Evidence:** `NUMERIC_GROUND_COVER_WITH_SCOPE_CAUTION`. Official site and numeric primary-paper description verified; historical bare cover retained with scope limitation. AmeriFlux US-Seg; Duman et al. 2021 Recent land cover changes in the Southwestern US lead to an increase in surface temperature; He et al. 2010 On the impact of shrub encroachment on microclimate conditions in the northern Chihuahuan desert; Petrie et al. 2015. Locator: Duman2021 study sites paragraph, US-Seg surface coverage; He2010 section2.1 paragraph7; Petrie2015 Site pp1227 [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Seg), [source 2](https://par.nsf.gov/servlets/purl/10255415), [source 3](https://doi.org/10.1016/j.agrformet.2020.108246), [source 4](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2009JD013529), [source 5](https://research.fs.usda.gov/download/treesearch/47836.pdf).

**Candidate and limits:** C4 grass dominant; remaining living C3 herb/shrub fractions unresolved 60% surface cover is approximate and undated. Fire, tower relocation, litter, C3 shrubs, and nearby-tower substitutions prevent timeless C4=100%.

**Separate published model configuration:** `{"BS": 40, "C4G": 60}` (2007-2014; source-native ORCHIDEE groups). [Table 1](https://doi.org/10.1029/2021JG006400).

**Next evidence:** Read original US-Seg BADM species-cover groups by date and fire treatment; quantify vegetation/litter/bare independently.

### US-Ses — Sevilleta shrubland

**Vegetation:** C3 Larrea tridentata shrubland interspersed with C4 perennial grasses.

**Reported composition:** Official overview gives Larrea density 0.9 m^-2, with Bouteloua gracilis, B. eriopoda, Sporobolus spp., Hilaria jamesii and Muhlenbergia spp. He2010 reports legacy shrubland vegetation cover approximately30% and bare soil70%, but gives a different tower location. Petrie2015 Figure7 has Larrea cover4.7% in2001 and7.3% in2013 on two325m transects, not a whole flux-footprint census.

**Functional interpretation:** C3 evergreen broadleaf shrub plus C4 grass; no verified site-wide proportion. Legacy 30% total cover does not establish shrub=30%.

**Measurement basis:** 0.9 shrubs per m² (density, not percent); legacy ground area cover; Larrea percentage over two specific transects **Period:** Official overview survey date unspecified; transects2001 and2013; legacy He2010 microclimate period July2007-June2008

**Spatial scope:** Current site34.3350N,106.7448 W; He2010 shrub34.3338N,106.7340 W differs; Petrie transects cannot automatically represent tower footprint **Bare ground:** Legacy70% bare soil from He2010; coordinates differ from US-Ses; not used as current observed fraction.

**Evidence:** `NUMERIC_DENSITY_AND_TRANSECT_COVER_WITH_SCOPE_CAUTION`. Official species/density and primary cover statements read; spatial mismatch explicitly retained. AmeriFlux US-Ses overview; He et al.2010; Petrie et al.2015 Grassland to shrubland state transitions enhance carbon sequestration in the northern Chihuahuan Desert. Locator: Official Description; He2010 section2.1 paragraph7; Petrie2015 Figure7 caption p1233 [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Ses), [source 2](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2009JD013529), [source 3](https://research.fs.usda.gov/download/treesearch/47836.pdf).

**Candidate and limits:** Broadleaf evergreen shrub and C4 grass; quantitative fractions unresolved Ground-cover survey scope differs; Larrea0.9m^-2 as printed in overview requires BADM confirmation. Do not confuse monsoon60% rainfall with vegetation percentage.

**Separate published model configuration:** `{"BS": 20, "C4G": 25, "TeBE": 55}` (2007-2014; source-native ORCHIDEE groups). [Table 1](https://doi.org/10.1029/2021JG006400).

**Next evidence:** Tower-footprint mapped shrub crown cover plus dated grass/litter/bare cover from original BADM or Sevilleta vegetation inventory.

### US-Slt — Silas Little- New Jersey

**Vegetation:** Oak-pine forest affected by2006-2008 moth defoliation and subsequent oak mortality; growing pine contribution.

**Reported composition:** Clark et al.2022 explicitly identifies the oak stand as US-Slt. In2018 pine trees plus saplings accounted for38% of total basal area. The remainder62% is derived hardwood basal area in the paper's pine-versus-hardwood grouping. Older Mirfenderesgi2016 species percentages sum95% and lack explicit denominator: chestnut oak58, black14, scarlet6, white6, post3, pitch pine8; preserve as incomplete historical context.

**Functional interpretation:** Published2018 pine basal area38%; derived non-pine woody basal area62%. NE38 / BD approximately62 is a provisional functional interpretation of that tree+sapling grouping, not measured ground cover.

**Measurement basis:** Total basal area of inventoried live trees+saplings; not land surface cover or stem count **Period:** 2018 after insect mortality; earlier2004-2005 inventory before infestation

**Spatial scope:** Five201m² census plots within100m of flux tower plus periodically sampled1km² grid; selected paper result is US-Slt oak stand, not US-Ced or US-Dix **Bare ground:** Not quantified; remaining non-woody ground is not inferred from basal area

**Evidence:** `NUMERIC_BASAL_AREA`. Official site identity/IGBP verified via network listing; primary dated basal-area fraction read. AmeriFlux site-search US-Slt; Clark et al.2022 Insect infestations and the persistence and functioning of oak-pine mixedwood forests in the mid-Atlantic region, USA; Mirfenderesgi et al.2016. Locator: Clark2022 Materials and methods: L.dispar infestations and forest structure; Results paragraph before Table2 and Figures2A/4; Mirfenderesgi2016 section2.2 [source 1](https://ameriflux.lbl.gov/sites/site-search/), [source 2](https://ameriflux.lbl.gov/sites/siteinfo/US-Slt), [source 3](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0265955), [source 4](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2016JG003467).

**Candidate and limits:** Temperate broadleaf deciduous62 / temperate needleleaf evergreen38 as2018 woody-BA proxy only Composition changed strongly after2007.38% cannot be applied to entire2005-2022 forcing period. Species-level historical percentages incomplete and denominator unstated.

**Next evidence:** Retrieve exact pre- and post-disturbance live basal area tables/raw census; date-specific woody and understory PFT fractions.

### US-SP1 — Slashpine-Austin Cary- 65yrs nat regen

**Vegetation:** Naturally regenerated longleaf/slash-pine stand with dense palmetto, gallberry, wax-myrtle and grass understory; prescribed burns and2016 thinning.

**Reported composition:** Bracho et al.2023 beginning-study total basal area17.53m²/ha: Pinus palustris64.5%, P.elliottii35.5%. Powell et al.2005 describes mixed stand basal area as slash63% and longleaf36%, an unresolved source discrepancy.2018 tower-footprint plots in Silva et al.2021 report approximately70% longleaf and30% slash by tree count.

**Functional interpretation:** Reported main pine basal area is needleleaf evergreen; two pine species occupy same broad PFT. Understory fractions are not included; cannot claim entire ecosystem NE100%.

**Measurement basis:** Bracho2023 total stand basal area at beginning of study; Silva2021 percentage of trees; Powell2005 stand basal area **Period:** Bracho study July2000-Feb2021, initial composition near2000; 2016 basal-area removal20%; Silva plots2018

**Spatial scope:** Austin Cary Forest tower at29.738N,82.2188 W; four50x50m2018 plots within tower footprint; do not merge surrounding cypress wetlands into tree BA **Bare ground:** Not quantified; understory is dense and includes shrubs/grasses

**Evidence:** `NUMERIC_BASAL_AREA_WITH_SOURCE_CONFLICT`. Official identity and three primary compositions read; conflicting species-BA report retained. AmeriFlux US-SP1; Bracho et al.2023 Two decades of carbon dynamics in an actively-managed, naturally-regenerated longleaf/slash pine forest; Powell et al.2005 Ecosystem and understory water and energy exchange for a mature, naturally regenerated pine flatwoods forest in north Florida; Silva et al.2021 Using GatorEye UAV-Borne LiDAR to Quantify the Spatial and Temporal Effects of a Prescribed Fire. Locator: Bracho2023 section2.1 site description p2; Powell2005 Table1 and Study site; Silva2021 section2.1 [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-SP1), [source 2](https://www.fs.usda.gov/nrs/pubs/jrnl/2023/nrs_2023_bracho_001.pdf), [source 3](https://doi.org/10.1016/j.foreco.2023.121408), [source 4](https://research.fs.usda.gov/download/treesearch/19963.pdf), [source 5](https://www.mdpi.com/1999-4907/12/1/38).

**Candidate and limits:** Temperate needleleaf evergreen dominant overstory; shrub and C3/C4 grass weights unresolved Species-BA inversion between sources requires original inventory reconciliation; tree-count and BA denominators differ; prescribed burning changes understory.

**Next evidence:** Read original dated tree inventory and BADM species abundance; resolve Powell/Bracho discrepancy; quantify understory shrub/grass cover.

### US-SRG — Santa Rita Grassland

**Vegetation:** Semidesert C4 grassland dominated by Eragrostis lehmanniana with mesquite recolonization.

**Reported composition:** Scott et al.2015 Table1 reports Santa Rita Grassland woody overstory cover11% (Prosopis velutina) and perennial grass/forb/succulent cover44%, chiefly Eragrostis lehmanniana.

**Functional interpretation:** Mesquite woody cover11%; mixed perennial herbaceous/succulent group44%, C4 grass dominated. Remaining45% is unspecified/possibly overlapping area, not verified bare-ground percentage.

**Measurement basis:** Canopy cover percentage of ground by woody and perennial understory groups; separate layers may overlap **Period:** Hydrological years2009-2014 study; precise cover survey date not stated in Table1

**Spatial scope:** Santa Rita Grassland tower31.789N,110.828 W in Pasture1; not companion US-SRM mesquite tower **Bare ground:** Not explicitly quantified; do not assume100-11-44=45% bare

**Evidence:** `NUMERIC_GROUND_COVER`. Official vegetation and primary numeric table verified. AmeriFlux US-SRG overview; Scott et al.2015 The carbon balance pivot point of southwestern U.S.semiarid ecosystems: Insights from the21st century drought. Locator: Official Description; Scott2015 Table1, gra-s column and site-description paragraph [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-SRG), [source 2](https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2308.pdf), [source 3](https://doi.org/10.1002/2015JG003181).

**Candidate and limits:** C4 grass dominant plus broadleaf deciduous/drought-deciduous mesquite; no complete normalized vector 44% group combines grass/forb/succulents and cannot all be labelled C4; source age and grazing affect current cover.

**Separate published model configuration:** `{"BS": 45, "C4G": 44, "TeBD": 11}` (2009-2014; source-native ORCHIDEE groups). [Table 1](https://doi.org/10.1029/2021JG006400).

**Next evidence:** Match ongoing SRER species-cover transects to tower footprint and survey year; separate C3 forbs/succulents and annual cover.

### US-SRM — Santa Rita Mesquite

**Vegetation:** Velvet-mesquite woody savanna over native and nonnative perennial C4 grasses, subshrubs and succulents.

**Reported composition:** Scott2019 site description: trees(mainly Prosopis velutina)30-35% cover; perennial bunchgrasses15-25%; bare soil40-50% supports annuals when rain permits. Scott2015 Table1 earlier period gives35% mesquite and15% perennial grass/forb/succulent; Scott2009 gives approximately35% mesquite and22% combined perennial understory.

**Functional interpretation:** Ground cover ranges preserve woody30-35 / perennial understory15-25 / bare40-50%; these are ranges, not a compositional simplex. Mesquite BD and C4 grasses dominate relevant plant groups.

**Measurement basis:** Ground-area cover by vegetation layers and bare soil; quoted ranges are independently approximate **Period:** Scott2019 uses2004-2016; Scott2015 hydrological2005-2014; no assumption valid through2025

**Spatial scope:** US-SRM tower31.8214N,110.8661 W,1120m; US-SRS herbicide-treated site is different **Bare ground:** 40-50% explicitly reported by Scott2019; annual cover changes with rain

**Evidence:** `NUMERIC_GROUND_COVER`. Official identity and numeric primary descriptions verified. AmeriFlux US-SRM; Scott et al.2019 Critical Zone Water Balance Over13Years in a Semiarid Savanna; Scott et al.2015; Scott et al.2009 Effects of seasonal drought on net carbon dioxide exchange from a woody-plant-encroached semiarid grassland. Locator: Scott2019 section2 Site Description; Scott2015 Table1 sav-s; Scott2009 section2 paragraph8 [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-SRM), [source 2](https://doi.org/10.1029/2018WR023477), [source 3](https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2308.pdf), [source 4](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2008JG000900).

**Candidate and limits:** Broadleaf deciduous mesquite plus C4 grass, minor C3 subshrubs/forbs and succulents; retain explicit bare40-50% rather than normalize vegetation to100% Ranges should not be summed at their independent extremes.22% understory in2009 includes more groups than15-25% bunchgrass in2019.

**Separate published model configuration:** `{"BS": 50, "C4G": 15, "TeBD": 35}` (2004-2014; source-native ORCHIDEE groups). [Table 1](https://doi.org/10.1029/2021JG006400).

**Next evidence:** Dated species-level canopy/ground cover and tower-footprint masks; choose a defined period and explicitly resolve overlapping vegetation layers.

### US-Syv — Sylvania Wilderness Area

**Vegetation:** Old-growth sugar-maple/eastern-hemlock mosaic; tower's immediate patch differs from surrounding forest.

**Reported composition:** Desai et al.2005: overstory stems in1ha surrounding tower are sugar maple71%, eastern hemlock14%, yellow birch7%, basswood+ironwood8%. The same paper says hemlock dominates the surrounding1km².

**Functional interpretation:** Immediate1ha stem-count grouping gives deciduous broadleaf86% (71+7+8), evergreen needleleaf14%; not flux-footprint canopy cover.

**Measurement basis:** Overstory stems in immediate1ha, not basal area, leaf area or ground cover **Period:** Early site characterization near2002; paper flux study2002-2003

**Spatial scope:** Immediate1ha at US-Syv only; hemlock dominance over1km² makes local stem vector unrepresentative of wider footprint; nearby lake also matters **Bare ground:** Not quantified; regional lakes/wetlands percentages describe whole8500ha Wilderness and are not tower fractions

**Evidence:** `NUMERIC_STEMS`. Primary full text read; denominator/spatial mismatch retained. AmeriFlux US-Syv; Desai et al.2005 Comparing net ecosystem exchange of carbon dioxide between an old-growth and mature forest in the upper Midwest, USA. Locator: Desai2005 section2.1.1 pp35-36, paragraph immediate1ha; official Overview [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Syv), [source 2](https://ameriflux.lbl.gov/doi/FLUXNET/US-Syv/), [source 3](https://co2.aos.wisc.edu/~adesai/documents/Desai-AFM-Sylvania.pdf), [source 4](https://doi.org/10.1016/j.agrformet.2004.09.005).

**Candidate and limits:** Temperate BD86 / temperate NE14 only as local2002 overstory-stem proxy; no site-wide candidate ratio Small patch, stem size weighting, prevailing wind and footprint vary. A86/14 tree count vector cannot stand in for mixed-forest areal cover.

**Next evidence:** Spatially explicit species inventory across1km² and footprint-weighted basal/crown cover; latest BADM with dates.

### US-Ton — Tonzi Ranch

**Vegetation:** Blue-oak savanna with scattered grey pine above annual C3 grasses and herbs.

**Reported composition:** Chen et al.2008 estimates woodland canopy cover approximately43% over1km×1km around tall tower from IKONOS imagery. Official overview says blue oak40% of total vegetation and grey pine3trees/ha. These have different/unclear denominators and are not a complete PFT partition.

**Functional interpretation:** Temperate deciduous blue oak, minor evergreen needleleaf pine, C3 herbaceous understory; woodland canopy43% is observed cover, not oak-only PFT abundance.

**Measurement basis:** Woodland projected canopy fraction of1km² image; official40% total vegetation wording ambiguous; pine3trees/ha is density **Period:** Chen2008 cites Kim2006 IKONOS estimate; exact image date not verified; official overview undated

**Spatial scope:** 1km² centered on Tonzi tall tower38.4311N,120.966 W **Bare ground:** Not quantified;43% tree canopy does not imply57% grass or bare because annual grasses can occur beneath trees

**Evidence:** `NUMERIC_CANOPY_COVER`. Official species description and primary43% canopy-cover estimate verified. AmeriFlux US-Ton overview; Chen et al.2008 Observations and stochastic modeling of soil moisture control on evapotranspiration in a Californian oak savanna. Locator: Official Description; Chen2008 section2.1 paragraph8 and Figure2 [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Ton), [source 2](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2007WR006646).

**Candidate and limits:** Temperate broadleaf deciduous oak + C3 grass; minor temperate needleleaf evergreen grey pine; exact weights unresolved Canopy cover and total-vegetation composition differ; grey pine density cannot become area fraction; annual grass cover varies seasonally.

**Next evidence:** Dated crown-area map by oak/pine, grass cover under/open canopy, and treatment of overlaps with footprint weighting.

### US-Uaf — University of Alaska, Fairbanks

**Vegetation:** Open black-spruce forest on permafrost peat near Smith Lake with extensive shrub, sedge and sphagnum ground layer.

**Reported composition:** Ueyama et al.2024 reports dominant black spruce(Picea mariana)4500trees/ha; forest floor completely covered by understory and sphagnum. Named associates include Betula glandulosa, Ledum groenlandicum, Vaccinium uliginosum, V.vitis-idaea, Rubus chamaemorus, Larix laricina, Carex spp.and Alnus crispa. No species/PFT fraction is supplied.

**Functional interpretation:** Boreal evergreen needleleaf overstory plus deciduous/evergreen shrubs, graminoids and moss; tree density and complete combined ground coverage do not yield PFT fractions.

**Measurement basis:** Trees per hectare; combined forest-floor coverage described qualitatively, not split by species **Period:** Primary study2003-2022; tree-age inventory2012; site description survey dates partly unspecified

**Spatial scope:** US-Uaf at64°52'N,147°51'W,elevation155m; separate from UAF North Campus remote-sensing plot farther east **Bare ground:** Forest floor described as completely covered, suggesting minimal uncovered ground; no independent numeric bare-soil survey

**Evidence:** `NUMERIC_DENSITY_WITH_QUALITATIVE_GROUND_COVER`. Official site and full-text primary vegetation description verified; no observed PFT fraction located. AmeriFlux US-Uaf overview; Ueyama et al.2024 Anomalous wet summers and rising atmospheric CO2 concentrations increase the CO2 sink in a poorly drained forest on permafrost. Locator: PNAS2024 Materials and Methods: Site Descriptions; official Overview [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Uaf), [source 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC11536150/), [source 3](https://doi.org/10.1073/pnas.2414539121).

**Candidate and limits:** Boreal needleleaf evergreen dominant trees, minor needleleaf deciduous Larix; shrub/herb/moss fractions unresolved Moss is not represented by every FATES parameterization; black-spruce density is not percent; tree and ground layers overlap.

**Next evidence:** Site-specific BADM abundance/cover and original understory inventory; distinguish Smith Lake tower from separate North Campus calibration site.

## Batch05

### US-UiD — University of Illinois Restored Native Prairie

**Vegetation:** Restored mixed native prairie; perennial bioenergy/harvest experiment.

**Reported composition:** No measured functional percentage recovered.

**Functional interpretation:** Mixed prairie herbaceous community; C3/C4/forb fractions unresolved

**Measurement basis:** No observed PFT percentage **Period:** Prairie established2008; experiment2008-2011; release2008-2024

**Spatial scope:** Energy Farm restored prairie field **Bare ground:** Not quantified

**Evidence:** `QUALITATIVE_ONLY`. PRIMARY_DATASET_AND_ABSTRACT_READ. CABBI University of Illinois AmeriFlux Measurements; Zeri et al.2011, Carbon exchange by establishing biofuel crops in Central Illinois. Locator: Dataset identifies UiD as restored prairie; Zeri abstract identifies mixed native prairie treatment [source 1](https://cabbi.bio/datasets/university-of-illinois-ameriflux-measurements/), [source 2](https://doi.org/10.1016/j.agee.2011.09.006), [source 3](https://ameriflux.lbl.gov/sites/site-search/).

**Candidate and limits:** C4 grass plus C3 grasses/forb proxy; split unresolved US-UiD is distinct from US-UiA switchgrass and US-UiB miscanthus; a seed mixture is not measured cover.

**Next evidence:** Retrieve UiD field botanical/biomass surveys by year; quantify harvest and establishment.

### US-UMB — University of Michigan Biological Station

**Vegetation:** Northern hardwood forest with aspen, conifer understory and old hemlock patches.

**Reported composition:** Frasson et al.2015 Table1 observed basal-area fractions,2001/2010: P.grandidentata38/37%; P.tremuloides13/12%; B.papyrifera9/7%; Q.rubra10/12%; A.rubrum16/18%; F.grandifolia3/4%; A.saccharum1/1%; P.strobus8/9%.

**Functional interpretation:** 2010 listed tree basal area: DBF91%, ENF9%.2001: DBF90%, ENF8%, unresolved2% due to partial/rounded source values.

**Measurement basis:** Tree basal area from observational permanent-plot censuses; source fractions multiplied by100, not ground area **Period:** 2001 and2010 censuses; published2015

**Spatial scope:** 60 permanent plots of approximately0.1ha within US-UMB flux footprint; not US-UMd girdling treatment **Bare ground:** Not quantified

**Evidence:** `NUMERIC_BASAL_AREA`. PRIMARY_OBSERVATIONAL_CENSUS_TABLE_READ. Frasson et al.2015, Modeling forest carbon cycle response to tree mortality: Effects of plant functional type and disturbance intensity. Locator: Table1 species fraction of observed basal area; section2.1.2 permanent plots and2001/2010 censuses [source 1](https://ameriflux.lbl.gov/doi/AmeriFlux/US-UMB/), [source 2](https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2015JG003035).

**Candidate and limits:** DBF91 / ENF9 as a2010 tree-basal-area proxy only;2001 residual2 retained 2010 basal-area vector does not measure ground cover or prove uniform composition through2007-2021.2001 listed fractions sum98%; no normalization.

**Next evidence:** Retrieve dated US-UMB control footprint tree census/BADM and species basal area.

### US-UMd — UMBS Disturbance / FASET

**Vegetation:** Northern mixed hardwood forest; experimental aspen/birch girdling2008.

**Reported composition:** Aspen+birch represented39% of pretreatment basal area in the39ha treatment; published accounts also report38% and35-40% leaf area on other bases.

**Functional interpretation:** At least39% DBF basal area before treatment; remainder not resolved by this statement

**Measurement basis:** Pretreatment treatment-area basal area; not whole-site PFT area; leaf-area figures separate **Period:** Before spring2008; mortality/leaf-loss follows disturbance

**Spatial scope:** FASET39ha treatment around US-UMd; not US-UMB control **Bare ground:** Not quantified

**Evidence:** `NUMERIC_PARTIAL_BASAL_AREA`. PRIMARY_AUTHOR_MANUSCRIPT_READ. Fahey et al.2016, Evaluating forest subcanopy response to moderate severity disturbance and contribution to ecosystem-level productivity and resilience; Hardiman et al.2013. Locator: Fahey site/experiment description; Hardiman section2.2 [source 1](https://repository.library.noaa.gov/view/noaa/49508/noaa_49508_DS1.pdf), [source 2](https://doi.org/10.1016/j.foreco.2016.06.001), [source 3](https://www.mdpi.com/1999-4907/4/3/537).

**Candidate and limits:** DBF plus ENF admixture; time-dependent canopy structure 39% is a partial deciduous species basal-area share, not a DBF/ENF split. Girdling death is not bare-ground fraction; canopy recovery must be dated.

**Next evidence:** Extract full species basal area for pretreatment and post2008 periods.

### US-Var — Vaira Ranch - Ione

**Vegetation:** Mediterranean annual C3 grassland with herbs; cattle grazing and brush removal.

**Reported composition:** No numeric ground-cover or functional mixture recovered.

**Functional interpretation:** C3 grasses/herbs dominant; cover unresolved

**Measurement basis:** No measured area percentage **Period:** Growing season typicallyOctober-earlyMay; release2000-2025

**Spatial scope:** Vaira grassland opening, distinct from Tonzi oak savanna **Bare ground:** Seasonal senescence not evidence of permanent bare fraction

**Evidence:** `QUALITATIVE_ONLY`. PRIMARY_OFFICIAL_DESCRIPTION_READ. AmeriFlux BASE US-Var dataset description. Locator: Dataset site description; C3 annual grasses and herbs [source 1](https://ameriflux.lbl.gov/doi/AmeriFlux/US-Var/).

**Candidate and limits:** C3 grass/herbaceous proxy; prescribed100% would be a separate assumption Species list includes forbs/clover; grass proxy is not exact taxonomic composition.

**Next evidence:** Find seasonal ground-cover quadrats and litter/bare partition; retain grazing.

### US-Vcm — Valles Caldera Mixed Conifer

**Vegetation:** Mixed conifer forest before stand-replacing wildfire in lateMay2013; tree mortality followed by recovery.

**Reported composition:** No measured PFT fraction recovered; official page reports all trees killed in2013 fire. Li et al.2020 describes elderberry and aspen seedlings1-2m after fire, using records through2018; postfire percentages remain unresolved.

**Functional interpretation:** Prefire ENF dominant; postfire community requires separate evidence

**Measurement basis:** Tree mortality is a disturbance metric; not vegetation area **Period:** Prefire2007-2012; May-June2013 wildfire; postfire record through2018 in Li2020; release2007-2025

**Spatial scope:** US-Vcm tower footprint; do not substitute US-Vcs **Bare ground:** Postfire bare/herb/shrub cover not quantified

**Evidence:** `QUALITATIVE_DISTURBANCE`. PRIMARY_OFFICIAL_DESCRIPTION_READ. AmeriFlux US-Vcm overview; Li et al.2020 Remote Sensing of Environment251:112062; FLUXNET2014 Thompson Ridge fire account. Locator: Overview, stand-replacing fire lateMay2013; Li2020 PDFp4 site context; FLUXNET account confirms2013 event [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Vcm), [source 2](https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2604.pdf), [source 3](https://fluxnet.org/2014/04/30/thompson-ridge-wildfire-takes-out-ameriflux-core-site/).

**Candidate and limits:** Prefire evergreen needleleaf forest; postfire herb/shrub/tree recovery unresolved Official core-site summary says2012 but detailed site overview says lateMay2013; use detailed site record and flag date conflict. A prefire ENF100 model precedent cannot represent all2007-2025.

**Separate published model configuration:** `{"TeNE": 100}` (2007-2012; prefire; source-native ORCHIDEE groups). [Table 1](https://doi.org/10.1029/2021JG006400).

**Next evidence:** Retrieve dated fire severity, surviving/regenerating vegetation and postfire cover surveys.

### US-Vcp — Valles Caldera Ponderosa Pine

**Vegetation:** Ponderosa pine forest with Gambel oak mentioned in published model site description.

**Reported composition:** No measured species/PFT percent recovered.

**Functional interpretation:** ENF dominant; oak and understory shares unresolved

**Measurement basis:** No measured area percentage **Period:** Published model site period2007-2014; release2007-2025

**Spatial scope:** US-Vcp tower, not US-Vcm/US-Vcs **Bare ground:** Not quantified

**Evidence:** `QUALITATIVE_ONLY`. PRIMARY_OFFICIAL_AND_MODEL_TABLE_READ. AmeriFlux US-Vcp overview; Mahmud et al.2021 Table1 species context. Locator: Official overview; Table1 species list [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Vcp), [source 2](https://doi.org/10.1029/2021JG006400).

**Candidate and limits:** Evergreen needleleaf trees with broadleaf oak/understory review Published ENF100 is an ORCHIDEE model configuration, not measured whole-tower cover.

**Separate published model configuration:** `{"TeNE": 100}` (2007-2014; source-native ORCHIDEE groups). [Table 1](https://doi.org/10.1029/2021JG006400).

**Next evidence:** Retrieve species inventory including Quercus gambelii and understory cover.

### US-WCr — Willow Creek

**Vegetation:** Upland maple-basswood-ash hardwood stand.

**Reported composition:** Original Cook et al. conference poster lists basal-area shares: sugar maple40%; basswood36%; green ash14%; red oak7%; red maple1%; paper birch1%; yellow birch<1%; other<1%.

**Functional interpretation:** Listed identified tree taxa are DBF; minor other taxa unresolved

**Measurement basis:** Percent of total tree basal area; total28m2/ha in poster **Period:** Poster reports2000 fluxes; vegetation survey year not specified

**Spatial scope:** Willow Creek stand; Cook2004 estimates main footprint within0.6km **Bare ground:** Not quantified

**Evidence:** `NUMERIC_BASAL_AREA`. PRIMARY_AUTHOR_POSTER_TABLE_AND_SITE_PAPER_READ. Cook et al., Contributions From a Deciduous Forest and Shrub Wetland to Regional Carbon Fluxes in Northern Wisconsin; Cook et al.2004 site paper. Locator: Poster table Forest Species at Flux Towers Sites, Willow Creek column; paper section2.1 [source 1](https://www.researchgate.net/publication/241222633_Contributions_From_a_Deciduous_Forest_and_Shrub_Wetland_to_Regional_Carbon_Fluxes_in_Northern_Wisconsin), [source 2](https://research.fs.usda.gov/treesearch/download/55333.pdf).

**Candidate and limits:** DBF dominant; full DBF100 area prescription remains a proxy Poster basal-area composition is an early snapshot; official dataset reports thinning removed30% overstory biomass in2013-2014, a disturbance not a PFT percentage.

**Next evidence:** Find dated post-thinning species basal area and tower-weighted canopy map.

### US-Whs — Walnut Gulch Lucky Hills Shrub

**Vegetation:** Chihuahuan shrubland with Larrea, Parthenium and Acacia; mixture of shrub phenologies.

**Reported composition:** Woody canopy40%; perennial grass/forb canopy3%.

**Functional interpretation:** Shrubs40% and herbs3% ground canopy cover; species/phenology fractions unresolved

**Measurement basis:** Ground canopy cover by vegetation stratum; not sum-to100 whole-ground classification **Period:** 2012 site characterization in Roby2019 Table1

**Spatial scope:** Lucky Hills study site around flux tower; weighted footprint not specified **Bare ground:** 57% is only arithmetic non-canopy remainder unless independently classified; published model uses bare57

**Evidence:** `NUMERIC_GROUND_COVER`. PRIMARY_TABLE_READ. Roby et al.2019, Environmental and Vegetative Controls on Soil CO2 Efflux in Three Semiarid Ecosystems. Locator: Table1 woody cover40 and perennial grass/forb3; Methods2.1 [source 1](https://doi.org/10.3390/soilsystems3010006), [source 2](https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2525.pdf).

**Candidate and limits:** Evergreen plus drought/cold-deciduous shrubs and herbaceous plants; exact FATES map unresolved Woody fraction cannot all be assigned evergreen shrubs: Acacia and other taxa differ. Strata can overlap; uncovered ground may include litter/rock/biocrust.

**Separate published model configuration:** `{"BS": 57, "C4G": 3, "TeBE": 40}` (2008-2014; source-native ORCHIDEE groups). [Table 1](https://doi.org/10.1029/2021JG006400).

**Next evidence:** Extract species-specific shrub phenology, line-intercept bare/litter/rock/biocrust and seasonal herb cover.

### US-Wjs — Willard Juniper Savannah

**Vegetation:** Juniperus monosperma savanna with intermittently grazed C4 Bouteloua gracilis.

**Reported composition:** No independently measured whole-ground vector recovered.

**Functional interpretation:** Evergreen needleleaf juniper plus C4 grasses

**Measurement basis:** No measured whole-ground PFT fraction **Period:** Official site record; published model period2008-2014

**Spatial scope:** Willard private ranch; tower operationalMay2007 **Bare ground:** Not quantified; no bare0 inference from published two-PFT vector

**Evidence:** `QUALITATIVE_ONLY`. PRIMARY_OFFICIAL_AND_SITE_LAB_READ. AmeriFlux US-Wjs overview; Litvak Lab juniper savanna site. Locator: Official description and lab dominant vegetation list [source 1](https://ameriflux.lbl.gov/sites/siteinfo/US-Wjs), [source 2](https://www.litvaklab.org/juniper-savanna-us-wjs.html).

**Candidate and limits:** Evergreen needleleaf trees plus C4 grass; model precedent15/85 separate IGBP SAV canopy10-30% is class definition, not measured site canopy. Model fCover15/85 does not establish observed absence of bare ground.

**Separate published model configuration:** `{"C4G": 85, "TeNE": 15}` (2008-2014; source-native ORCHIDEE groups). [Table 1](https://doi.org/10.1029/2021JG006400).

**Next evidence:** Retrieve Willard canopy/grass/bare ground field map and dated grazing cover.

### US-Wkg — Walnut Gulch Kendall Grasslands

**Vegetation:** C4 perennial bunchgrasses with sparse woody plants; post2003-2006 drought shift to Lehmann lovegrass.

**Reported composition:** Woody cover3%; perennial grass/forb cover37%. Earlier site description reports canopy~40%.

**Functional interpretation:** Woody3% and herbaceous37% ground canopy cover; C4 dominant but exact herb C3/C4 split unmeasured

**Measurement basis:** Ground canopy cover by stratum; not species fraction or biomass **Period:** 2017 characterization in Roby2019; earlier drought and replacement2007 onward

**Spatial scope:** Kendall grassland study site; flux fetch broadly representative over kilometers **Bare ground:** 60% arithmetic non-canopy remainder is not automatically measured bare soil; model uses bare60

**Evidence:** `NUMERIC_GROUND_COVER`. PRIMARY_TABLE_AND_SITE_PAPER_READ. Roby et al.2019; Scott et al.2010, Carbon dioxide exchange in a semidesert grassland through drought-induced vegetation change. Locator: Roby Table1; Scott section2 site description [source 1](https://doi.org/10.3390/soilsystems3010006), [source 2](https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2525.pdf), [source 3](https://doi.org/10.1029/2010JG001348).

**Candidate and limits:** C4 grasses plus shrub/forb component; model precedent60bare/3TeBE/37C4 separate Perennial grass/forb37% cannot be relabelled observed C4-only37%; seasonal cover and drought replacement matter.

**Separate published model configuration:** `{"BS": 60, "C4G": 37, "TeBE": 3}` (2004-2013; source-native ORCHIDEE groups). [Table 1](https://doi.org/10.1029/2021JG006400).

**Next evidence:** Retrieve dated species/physiology split and non-canopy ground classes.

