# AmeriFlux PFT evidence — all 50 stations


## Full BADM cross-check, 26 October 2026

[BADM_PFT_CROSSCHECK_50_SITES_20261026.md](BADM_PFT_CROSSCHECK_50_SITES_20261026.md) compares the full AmeriFlux BADM vegetation records (IGBP and species cover, 50 of 50 sites) with the recommended inputs.

- 42 sites are consistent.
- 5 differ only in metric or year.
- 3 need a decision: US-Ho3 (BADM gives 80/20 within 200 m), US-Syv (tower plots give ENF ≈13, against the 50/50 prior), and US-Wjs (BADM gives ~26% juniper cover, against ENF 15).

No recommended value was changed.

## Recommended CLM-FATES inputs — 26 October 2026

[**50-site recommended input percentages (v1)**](RECOMMENDED_INPUT_PFT_50_SITES_20261026.md) now gives a complete FIXNC prescription for each station, plus 35 sensitivity or period alternatives. [Full input CSV](RECOMMENDED_50_SITE_CLM_FATES_INPUT_PFT_20261026.csv), [CLM host matrix](RECOMMENDED_50_SITE_CLM_PCT_NAT_PFT_20261026.csv), and [FATES natural-landunit / vegetated-only matrices](RECOMMENDED_50_SITE_FATES_PFT_PERCENT_20261026.csv) distinguish proposed model fractions from the original observations below. Nine primary prescriptions require a site-private Arctic or hydrodeciduous-shrub HLM map; defaults do not reproduce those targets. No existing surface, parameter file or case was changed.

## Original observation inventory

Updated 26 October 2026. The five experiment manifests contain **50 distinct stations, 10 per batch**. This collection follows the central-table/report structure of [ICOS_PFT](../../ICOS_sites/ICOS_PFT/).

**Search result: 33 sites with numerical composition/cover leads; 17 with qualitative composition, LAI/density or model-only evidence.** Numbers below keep their measured denominators, period and sampling extent. None is automatically an approved full tower-area prescription.

| File | Contents |
| --- | --- |
| [Master 50-site table](MASTER_50_SITE_OBSERVED_VS_FATES_PFT_20261026.csv) | Exact release membership, observed evidence, scalar groups, candidate mapping, published model fCover and missing FATES output status |
| [Full source report](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | Per-site measurement basis, source locator, date, footprint scope and unresolved issues |
| [Evidence CSV](50_site_PFT_evidence.csv) | All 50 observed-composition records |
| [50-site candidate table](FINAL_50_SITE_PFT_CANDIDATES_20261026.csv) | Final consolidated research candidates; filename does not imply approved surface fractions |
| [Further research](50_site_further_research_leads.csv) | Concrete next evidence for each station |
| [Source records and membership](metadata/) | Five curated JSON source ledgers and exact 50-release manifest |
| [Mapping and experiment design](PFT_MAPPING_AND_EXPERIMENT_DESIGN.md) | Source-to-functional mapping and requirements for fixed or competition experiments |
| [Search and provenance](SEARCH_AND_PROVENANCE_20261026.md) | GitHub reuse, primary-source checks and limits of the search |

## Five-batch composition index

A concise index follows. Read the full report before selecting a modeling proxy. Percentages may describe stems, basal area, specific transects or overstory alone.

| Batch | Site | IGBP | Observed/source functional composition | Basis |
| --- | --- | --- | --- | --- |
| Batch01 | [BR-Ma2](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | EBF | Tropical evergreen broadleaf dominant; measured area share unresolved | QUALITATIVE_ONLY |
| Batch01 | [CA-Ca3](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | ENF100% of listed tree cover types | NUMERIC_SPECIES |
| Batch01 | [CA-Cbo](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | DBF | DBF81.6%; ENF18.7%; rounded sum100.3 | NUMERIC_STEMS |
| Batch01 | [CA-LP1](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | ENF100% only within the tabled juvenile conifer subset; whole canopy unresolved | NUMERIC_STEMS_SUBSET |
| Batch01 | [CA-Man](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | ENF99%; residual~1% unassigned | NUMERIC_BASAL_AREA |
| Batch01 | [CA-TP1](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | ENF100% of described tree stand | QUALITATIVE_SINGLE_SPECIES_ASSERTION |
| Batch01 | [CA-TP3](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | ENF99%; DBF1% of reported tree composition | NUMERIC_SPECIES |
| Batch01 | [CA-TP4](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | ENF93%; DBF7% of reported tree composition | NUMERIC_SPECIES |
| Batch01 | [US-Aud](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | GRA | C4 grass dominant; field fractions unresolved | MODEL_ASSUMPTION_ONLY |
| Batch01 | [US-Bar](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | DBF | DBF83%; ENF>=14%; residual unresolved | NUMERIC_SPECIES_DENOMINATOR_UNSPECIFIED |
| Batch02 | [US-BZS](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | Needleleaf evergreen tree cover about 20%, plus evergreen shrubs and nonvascular ground cover; overlapping strata prevent complementing tree cover to bare ground. | NUMERIC_GROUND_COVER_PARTIAL |
| Batch02 | [US-CMW](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | DBF | Broadleaf deciduous mesquite canopy 74% (historical horizontal crown cover); understory includes C4 bunchgrass but its area fraction is not reported in the passages read. | NUMERIC_GROUND_COVER_PARTIAL |
| Batch02 | [US-EML](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | OSH | C3 sedge/graminoid + deciduous and evergreen shrubs + nonvascular vegetation; OSH is not a shrub-only numerical fraction. | QUALITATIVE_ONLY |
| Batch02 | [US-GLE](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | The reported two-species tree inventory comprises evergreen needleleaf taxa. This establishes tree functional identity, while vegetation/ground area and living fractions remain separate. | NUMERIC_BASAL_AREA_AND_STEMS |
| Batch02 | [US-Ha1](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | DBF | Historical measured basal-area grouping: BDT 72%, NET 27%, 1% rounding/unallocated; this is not a crown-cover vector. | NUMERIC_BASAL_AREA |
| Batch02 | [US-Ho1](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | Historical tree basal area: NET 91%, BDT 8%, 1% rounded/unallocated. | NUMERIC_BASAL_AREA |
| Batch02 | [US-Ho2](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | Evergreen conifer majority demonstrated, but the 17% mixed conifer/hardwood group prevents an exact west-tower NET/BDT split. | NUMERIC_BASAL_AREA_PARTIAL_POOLED |
| Batch02 | [US-Ho3](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | Needleleaf evergreen majority qualitatively supported; disturbance amount is not a PFT partition. | QUALITATIVE_ONLY_WITH_DISTURBANCE_NUMERIC |
| Batch02 | [US-ICh](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | OSH | Numerical community-patch mixture, not a direct shrub/graminoid PFT split. Both heath and tussock communities contain multiple growth forms. | NUMERIC_COMMUNITY_COVER_NOT_PFT |
| Batch02 | [US-ICt](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | OSH | C3 sedge/graminoids + deciduous/evergreen dwarf shrubs + moss; 95% describes community area rather than a single PFT. | NUMERIC_COMMUNITY_COVER_NOT_PFT |
| Batch03 | [US-Kon](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | GRA | Grass-dominated biomass with C4 dominants; exact C3:C4 and woody/shrub ground-cover shares unresolved. | NUMERIC_HERBACEOUS_BIOMASS |
| Batch03 | [US-Me2](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | Pre-fire evergreen needleleaf overstory plus broadleaf shrub understory; post-fire and post-logging composition unresolved. | NUMERIC_LAI_NO_PERCENT_VECTOR |
| Batch03 | [US-Me6](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | Evergreen needleleaf trees plus broadleaf deciduous shrubs and C3 grasses; their area shares are unmeasured in the read sources. | NUMERIC_LAI_NO_PERCENT_VECTOR |
| Batch03 | [US-MMS](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | DBF | At least the named 75% of basal area is deciduous broadleaf; no complete cover or PFT-area vector established. | NUMERIC_BASAL_AREA_PARTIAL |
| Batch03 | [US-MOz](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | DBF | Named deciduous broadleaf taxa total approximately 62% of basal area; named evergreen needleleaf Juniperus approximately 10%; approximately 28% unresolved. These are partial BA shares, not ground cover. | NUMERIC_BASAL_AREA_PARTIAL_AND_CANOPY_COVER |
| Batch03 | [US-Mpj](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | WSA | Evergreen conifer canopy dominates tree cover; C4 grass understory present. Percent of tree cover and percent of ground must remain separate. | NUMERIC_TREE_COVER_PARTIAL |
| Batch03 | [US-MtB](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | Evergreen needleleaf forest; precise species shares and minor woody/herbaceous shares unresolved. | QUALITATIVE_ONLY |
| Batch03 | [US-NC2](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | Evergreen needleleaf plantation overstory with deciduous broadleaf subdominants/understory; exact shares unquantified. | QUALITATIVE_COMPOSITION_WITH_NUMERIC_TOTAL_LAI |
| Batch03 | [US-NR1](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | Reported tree stems all evergreen needleleaf. This establishes an ENF tree-stem composition, not 100% site-area, ground-cover, LAI or vegetation-carbon fraction. | NUMERIC_STEMS |
| Batch03 | [US-NR3](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | GRA | Alpine C3 herbaceous graminoids/forbs with possible dwarf shrubs and nonvascular vegetation; detailed footprint shares unresolved. | QUALITATIVE_ONLY |
| Batch04 | [US-Rpf](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | DBF | Boreal broadleaf deciduous trees plus deciduous shrubs; no measured percentage vector. | QUALITATIVE_ONLY |
| Batch04 | [US-Seg](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | GRA | Approximately 60% C4-grass surface-cover description; not a complete living-PFT vector. | NUMERIC_GROUND_COVER_WITH_SCOPE_CAUTION |
| Batch04 | [US-Ses](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | OSH | C3 evergreen broadleaf shrub plus C4 grass; no verified site-wide proportion. Legacy 30% total cover does not establish shrub=30%. | NUMERIC_DENSITY_AND_TRANSECT_COVER_WITH_SCOPE_CAUTION |
| Batch04 | [US-Slt](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | DBF | Published2018 pine basal area38%; derived non-pine woody basal area62%. NE38 / BD approximately62 is a provisional functional interpretation of that tree+sapling grouping, not measured ground cover. | NUMERIC_BASAL_AREA |
| Batch04 | [US-SP1](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | Reported main pine basal area is needleleaf evergreen; two pine species occupy same broad PFT. Understory fractions are not included; cannot claim entire ecosystem NE100%. | NUMERIC_BASAL_AREA_WITH_SOURCE_CONFLICT |
| Batch04 | [US-SRG](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | GRA | Mesquite woody cover11%; mixed perennial herbaceous/succulent group44%, C4 grass dominated. Remaining45% is unspecified/possibly overlapping area, not verified bare-ground percentage. | NUMERIC_GROUND_COVER |
| Batch04 | [US-SRM](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | WSA | Ground cover ranges preserve woody30-35 / perennial understory15-25 / bare40-50%; these are ranges, not a compositional simplex. Mesquite BD and C4 grasses dominate relevant plant groups. | NUMERIC_GROUND_COVER |
| Batch04 | [US-Syv](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | MF | Immediate1ha stem-count grouping gives deciduous broadleaf86% (71+7+8), evergreen needleleaf14%; not flux-footprint canopy cover. | NUMERIC_STEMS |
| Batch04 | [US-Ton](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | WSA | Temperate deciduous blue oak, minor evergreen needleleaf pine, C3 herbaceous understory; woodland canopy43% is observed cover, not oak-only PFT abundance. | NUMERIC_CANOPY_COVER |
| Batch04 | [US-Uaf](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | Boreal evergreen needleleaf overstory plus deciduous/evergreen shrubs, graminoids and moss; tree density and complete combined ground coverage do not yield PFT fractions. | NUMERIC_DENSITY_WITH_QUALITATIVE_GROUND_COVER |
| Batch05 | [US-UiD](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | GRA | Mixed prairie herbaceous community; C3/C4/forb fractions unresolved | QUALITATIVE_ONLY |
| Batch05 | [US-UMB](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | DBF | 2010 listed tree basal area: DBF91%, ENF9%.2001: DBF90%, ENF8%, unresolved2% due to partial/rounded source values. | NUMERIC_BASAL_AREA |
| Batch05 | [US-UMd](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | DBF | At least39% DBF basal area before treatment; remainder not resolved by this statement | NUMERIC_PARTIAL_BASAL_AREA |
| Batch05 | [US-Var](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | GRA | C3 grasses/herbs dominant; cover unresolved | QUALITATIVE_ONLY |
| Batch05 | [US-Vcm](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | Prefire ENF dominant; postfire community requires separate evidence | QUALITATIVE_DISTURBANCE |
| Batch05 | [US-Vcp](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | ENF | ENF dominant; oak and understory shares unresolved | QUALITATIVE_ONLY |
| Batch05 | [US-WCr](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | DBF | Listed identified tree taxa are DBF; minor other taxa unresolved | NUMERIC_BASAL_AREA |
| Batch05 | [US-Whs](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | OSH | Shrubs40% and herbs3% ground canopy cover; species/phenology fractions unresolved | NUMERIC_GROUND_COVER |
| Batch05 | [US-Wjs](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | SAV | Evergreen needleleaf juniper plus C4 grasses | QUALITATIVE_ONLY |
| Batch05 | [US-Wkg](50_SITE_OBSERVED_PFT_PERCENT_REPORT_20261026.md) | GRA | Woody3% and herbaceous37% ground canopy cover; C4 dominant but exact herb C3/C4 split unmeasured | NUMERIC_GROUND_COVER |

## Published modeling precedents kept separate

[Mahmud et al. (2021) Table 1](https://doi.org/10.1029/2021JG006400) supplies 11 relevant historical ORCHIDEE fCover configurations. The machine-readable JSON preserves the original group names: BS=bare soil; TeNE=temperate needleleaf evergreen; TeBE=temperate broadleaf evergreen; TeBD=temperate broadleaf deciduous; C4G=C4 grass. These are candidate precedents. Shrub versus tree growth form and bare-ground treatment must be checked independently in FATES. US-Aud retains the existing operator-selected 70% C4/30% bare experimental policy, with its model-assumption label.

## Rebuild and validate

```bash
python3 scripts/build_inventory.py --build
python3 scripts/build_inventory.py --check
```

Python standard library only. The script checks 50 unique IDs, 10 per batch, exact release membership, source fields, percentage-versus-LAI/density classification, numerical ranges, complete published model-vector sums, and reproducibility of generated tables. Source percentages are never silently normalized. It writes only documentation tables inside this directory.

No surface, parameter file, forcing, CIME case, restart or Slurm job was modified. Exact active FATES names/indices remain unverified for new configurations. Blank modeled-PFT columns mean not found in the reviewed GitHub snapshot, not proof that a model has never run.
