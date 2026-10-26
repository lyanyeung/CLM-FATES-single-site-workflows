# ICOS_PFT: observed vegetation evidence for four FLUXNET multisite campaigns

## Final 38-site PFT table for the FIXNC experiment — 25 October 2026

This is the **current authoritative PFT assignment for all 38 stations** in the fixed-biogeography / no-competition (FIXNC) experiment ([Non-Competition-CLM-experiment](https://github.com/lyanyeung/Non-Competition-CLM-experiment)). Machine-readable copy: [FINAL_38_SITE_FIXNC_PFT_20261025.csv](FINAL_38_SITE_FIXNC_PFT_20261025.csv). It supersedes the PFT columns of the earlier inventories below, which remain as evidence history.

**How to read it**

- **Final `PCT_NAT_PFT`** is the prescribed host natural-PFT composition (sums to 100 within a 100% natural-vegetation point). It is a **named model proxy built from the cited evidence**, not a measured flux-footprint map; the evidence column keeps each source's own denominator (stand species, basal area, carbon, canopy cover or ground cover).
- **Bare ground** (host natural PFT 0) is included wherever non-vegetated ground was measured: IL-Yat, ES-LJu, ES-Agu, IT-Noe, GL-ZaH. In nocomp mode the pinned FATES treats it as a bare-ground patch. Mosses, lichens and biocrust have no FATES PFT and count as bare. Closed forests and managed meadows have no bare-ground evidence and are assigned none. Details: [six-site bare-ground review](SIX_SITE_BARE_GROUND_PFT_EVIDENCE_20261025.md).
- **Host → FATES mapping** (pinned `fates_params_default.json`): ENF = HLM 1 (FI-Hyy uses boreal HLM 2) → `needleleaf_evergreen_extratrop_tree`; DNF = HLM 3 → `needleleaf_colddecid_extratrop_tree`; tropical EBF = HLM 4 → `broadleaf_evergreen_tropical_tree`; EBF = HLM 5 → `broadleaf_evergreen_extratrop_tree`; DBF = HLM 7 (FI-Hyy boreal HLM 8) → `broadleaf_colddecid_extratrop_tree`; evergreen shrub = HLM 9 → `broadleaf_evergreen_extratrop_shrub`; arctic C3 grass = HLM 12; C3 grass = HLM 13 → `cool_c3_grass`. FATES has no forb or needleleaf-shrub PFT: herbaceous swards are C3 grass, and Mediterranean juniper maquis is evergreen shrub.
- **Status:** **IN USE** = written into a FIXNC surface and case on IRIDIS6 (25 sites); **PROPOSED** = evidence-based value, surface not yet built (5); **OPEN** = forest residual still undecided, the value shows what is known (4); **CANDIDATE** = qualitative-only herbaceous proxy, site not yet in a cohort (4).
- Unidentified forest residuals are never filled with grass ([policy](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/docs/PFT_UNKNOWN_RESIDUAL_POLICY.md)); where an operator proxy allocated a residual (BE-Vie, FR-Fon, FI-Sod, FR-Pue), the evidence column says so.

| Site | Cohort | IGBP | **Final `PCT_NAT_PFT` (%)** | Status | Evidence basis | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| DE-Tha | Example | ENF | **ENF 87 / DNF 10 / DBF 3** | IN USE | ICOS footprint cover classes: coniferous 87% (spruce 72%), deciduous 13% (larch 10%); 2% unspecified deciduous → DBF | [ICOS station](https://meta.icos-cp.eu/resources/stations/ES_DE-Tha) |
| NL-Loo | Example (legacy) | ENF | **ENF 93.6 / DBF 2.9 / C3 grass 3.5 / bare 0** | PROPOSED (legacy case unchanged) | 500-m map: Scots pine 89, black pine 3.3, Douglas fir 1.3, birch 2.3, oak 0.6; open 3.5% heather/grass, not bare | [Loobos ESSD 2026](https://essd.copernicus.org/articles/18/2023/2026/), [six-site review](SIX_SITE_BARE_GROUND_PFT_EVIDENCE_20261025.md) |
| BE-Vie | Batch01 | MF | **ENF 64 / DBF 36** | IN USE | Beech 43, Douglas fir 37%; 20% residual of named ENF and DBF species, allocated by operator proxy | [Flechard 2020 S2](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf), [Batch01 follow-up](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/examples/Batch01_10/docs/seven_site_PFT_residual_followup_2026-10-24.md) |
| CH-Dav | Batch01 | ENF | **ENF 100** | IN USE | Spruce >99.5% of inventoried trees | [Revenga et al. 2026](https://besjournals.onlinelibrary.wiley.com/doi/10.1002/2688-8319.70218) |
| CZ-BK1 | Batch01 | ENF | **ENF 100** | IN USE | Spruce 99, fir 1% of investigated stand (both ENF) | [ICOS station](https://meta.icos-cp.eu/resources/stations/ES_CZ-BK1) |
| DE-Hai | Batch01 | DBF | **DBF 100** | IN USE | Beech 64, ash 28, maple 7% of tree carbon; named residual trees all DBF | [BG 2022](https://bg.copernicus.org/articles/19/4315/2022/), [Batch01 follow-up](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/examples/Batch01_10/docs/seven_site_PFT_residual_followup_2026-10-24.md) |
| FI-Sod | Batch01 | ENF | **ENF 100** | IN USE | Scots pine 95% of stand; 5% unidentified, allocated to ENF by operator proxy | [Flechard 2020 S2](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf), [ICOS station](https://meta.icos-cp.eu/resources/stations/ES_FI-Sod) |
| FR-Fon | Batch01 | DBF | **ENF 2 / DBF 98** | IN USE | Sessile oak 79, hornbeam 18% of basal area; other <3% includes Scots pine | [Delpierre 2016](https://doi.org/10.1111/nph.13771), [Batch01 follow-up](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/examples/Batch01_10/docs/seven_site_PFT_residual_followup_2026-10-24.md) |
| FR-Pue | Batch01 | EBF | **DBF 5 / EBF 95** | IN USE | Holm oak 95% of stand; 5% residual allocated to DBF by operator proxy | [Flechard 2020 S2](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf), [ICOS station](https://meta.icos-cp.eu/resources/stations/ES_FR-Pue) |
| IT-Col | Batch01 | DBF | **DBF 100** | IN USE | Beech 100% of stand | [Flechard 2020 S2](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) |
| IT-Ren | Batch01 | ENF | **ENF 97 / DNF 3** | IN USE | Spruce ~85, Swiss stone pine 12 (ENF); larch 3 (DNF) | [Land 2022](https://www.mdpi.com/2073-445X/11/11/1903) |
| RU-Fyo | Batch01 | ENF | **ENF 85 / DBF 15** | IN USE | Spruce 85, birch 15% of stand (Kurbatova 2008: 86/14) | [Flechard 2020 S2](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf), [Kurbatova 2008](https://bg.copernicus.org/articles/5/969/2008/) |
| BE-Bra | Batch02 | MF | **ENF 55 / DBF 23 / unresolved 22** | OPEN | Scots pine 55, pedunculate oak 23% of stand; 22% unclassified | [Flechard 2020 S2](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) |
| CH-Fru | Batch02 | GRA | **C3 grass 100** | IN USE (AD5 candidate) | Mixed herbaceous cover up to ~90% of ground; grass/forb split unknown (herbaceous proxy) | [PMC7485103](https://pmc.ncbi.nlm.nih.gov/articles/PMC7485103/) |
| CH-Lae | Batch02 | MF | **DBF 80 / ENF 12 / unresolved 8** | OPEN | Species canopy cover: beech 40, ash 19, maple 13, lime 8 (DBF); fir 8, spruce 4 (ENF) | [BG 2024](https://bg.copernicus.org/articles/21/3571/2024/) |
| DK-Sor | Batch02 | DBF | **DBF 80 / ENF+DNF 20 (split open)** | OPEN | Beech 80%; spruce + larch 20% combined; larch is DNF, so the 20% cannot all be ENF | [Flechard 2020 S2](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf) |
| ES-LJu | Batch02 | OSH | **bare 49 / C3 grass 31 / evergreen shrub 20** | PROPOSED | Bare soil + gravel + rock 49.1%; Festuca 18.8, Hormathophylla 6.8, Genista 5.5%; 19.8% unnamed vegetation split pro rata | [BG 2010](https://bg.copernicus.org/articles/7/859/2010/bg-7-859-2010.pdf), [Sánchez-Cañete thesis](https://www.ugr.es/~andyk/Theses/TesisKike.pdf), [six-site review](SIX_SITE_BARE_GROUND_PFT_EVIDENCE_20261025.md) |
| FI-Hyy | Batch02 | ENF | **ENF 94.79 / DBF 5.21** | IN USE (AD5 candidate) | 2015 ICOS target stand basal area: pine 23.1, spruce 3.26, hardwood 1.45 m² ha⁻¹ | [Zenodo 5909681](https://zenodo.org/records/5909681) |
| FR-FBn | Batch02 | ENF | **ENF 75 / EBF ≤25 (open)** | OPEN | Aleppo pine ~75% of tree basal area; Quercus ilex subcanopy, but the remaining 25% is not verified as all oak | [Ann. Bot. 2025](https://academic.oup.com/aob/article/135/7/1361/8063930) |
| FR-Hes | Batch02 | DBF | **DBF 100** | IN USE (AD5 candidate) | 2020 basal area: beech ~75, oak ~10, hornbeam ~10; ≲5% unresolved assumed DBF | [BG 2026](https://bg.copernicus.org/articles/23/6491/2026/) |
| IT-MBo | Batch02 | GRA | **C3 grass 100** | IN USE (AD5 candidate) | Basal cover Festuca 25, Nardus 13, Trifolium 14.5%; remainder herbaceous (herbaceous proxy) | [ICOS Italy](https://www.icos-italy.it/monte-bondone-it-mbo/) |
| IT-Noe | Batch02 | CSH | **bare 34 / evergreen shrub 66** | PROPOSED | Ground cover 42–91% (midpoint used); juniper 53, lentisk 22% of vegetated surface | [Italian flux-site chapter](https://openpub.fmach.it/bitstream/10449/25172/2/9783642324239-c2.pdf), [iForest 2012](https://iforest.sisef.org/contents/?id=ifor0605-009), [six-site review](SIX_SITE_BARE_GROUND_PFT_EVIDENCE_20261025.md) |
| AT-Neu | Batch03 | GRA | **C3 grass 100** | IN USE — AD400 complete, Normal400 running | Graminoids 35, forbs 42, other 23% of phytomass; whole herbaceous sward as C3 grass (no forb PFT) | [PMC3899607](https://pmc.ncbi.nlm.nih.gov/articles/3899607/) |
| CH-Cha | Batch03 | GRA | **C3 grass 100** | IN USE — AD400 complete, Normal400 running | Intensively managed ryegrass/clover sward (qualitative; herbaceous proxy) | [FLUXNET site](https://fluxnet.org/sites/siteinfo/CH-Cha) |
| CZ-Stn | Batch03 | DBF | **DBF 100** | IN USE — AD400 complete, Normal400 running | Beech monoculture (qualitative; single PFT) | [Atmosphere 2021](https://www.mdpi.com/2073-4433/12/9/1128) |
| DE-Hzd | Batch03 | DBF | **DBF 100** | IN USE — AD400 complete, Normal400 running | Oak planted on the 2007 Kyrill windthrow (qualitative; single PFT) | [DEIMS Hetzdorf](https://deims.org/bf152bfd-f7b4-4a4b-9785-282a8f8ba539) |
| DE-Lnf | Batch03 | DBF | **DBF 100** | IN USE — AD400 complete, Normal400 running | Pure ~130-yr beech; occasional oak/maple (all DBF) | [Univ. Göttingen](https://uni-goettingen.de/en/701493.html) |
| DE-Obe | Batch03 | ENF | **ENF 100** | IN USE — AD400 complete, Normal400 running | Norway-spruce-dominated stand (qualitative; single PFT) | [FLUXNET site](https://fluxnet.org/sites/siteinfo/DE-Obe) |
| FI-Let | Batch03 | ENF | **ENF 80 / DBF 20** | IN USE — AD400 complete, Normal400 running | Pre-2016-harvest basal area: pine 60, spruce 20, birch 20 (post-harvest 53/47 is a sensitivity) | [Sci. Total Environ. 2023](https://www.sciencedirect.com/science/article/pii/S0048969723040445) |
| GF-Guy | Batch03 | EBF | **tropical EBF 100** | IN USE — AD400 complete, Normal400 running | Undisturbed evergreen tropical rainforest (qualitative; single PFT) | [ICOS station](https://meta.icos-cp.eu/resources/stations/ES_GF-Guy) |
| IL-Yat | Batch03 | ENF | **bare 52 / ENF 48** | IN USE (IL-Yat_B03_FIXNC_BARE52) — AD400 complete, Normal400 running | Measured mean crown cover 48% (72 plots; FVC 0.40–0.70); Aleppo pine >90% of trees; rock outcrop 36.8% | [Sprintsin et al.](https://www.researchgate.net/publication/222415057), [Qubaja 2019 thesis](https://www.weizmann.ac.il/EPS/Yakir/sites/EPS.Yakir/files/publications/rafat_qubaja_phd_thesis_11_dec_2019.pdf), [IL-Yat review](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/examples/Batch03_10/docs/IL_Yat_bare_ground_PFT_literature_20261025.md) |
| IT-Lav | Batch03 | ENF | **ENF 85 / DBF 15** | IN USE — AD400 complete, Normal400 running | Silver fir 70 + spruce 15 (ENF); beech 15 (DBF), tower stand | [Land 2022](https://www.mdpi.com/2073-445X/11/11/1903) |
| CH-Aws | Not assigned | GRA | **C3 grass 100 (candidate)** | CANDIDATE (qualitative; template case unstable) | Alpine pasture species list only (Festuca rubra, Phleum, Trifolium); no bare-ground evidence | [PMC7485103](https://pmc.ncbi.nlm.nih.gov/articles/PMC7485103/) |
| DE-Gri | Not assigned | GRA | **C3 grass 100 (candidate)** | CANDIDATE (qualitative) | Managed meadow species list (Elymus, Alopecurus, Achillea, Rumex, Trifolium); no bare-ground evidence | [ICOS station](https://meta.icos-cp.eu/resources/stations/ES_DE-Gri) |
| DE-RuR | Not assigned | GRA | **C3 grass 100 (candidate)** | CANDIDATE (qualitative) | Intensively managed meadow (Alopecurus, Lolium, Poa); no bare-ground evidence | [ICOS station](https://meta.icos-cp.eu/resources/stations/ES_DE-RuR) |
| ES-Agu | Not assigned | OSH | **bare 49 / C3 grass 29 / evergreen shrub 22** | PROPOSED | Vegetation 51%, gravel/rock/bare soil 49% (Rey et al. 2011); Macrochloa tenacissima 57% of vegetation | [BG 2026](https://bg.copernicus.org/articles/23/2569/2026/), [Sánchez-Cañete thesis](https://www.ugr.es/~andyk/Theses/TesisKike.pdf), [six-site review](SIX_SITE_BARE_GROUND_PFT_EVIDENCE_20261025.md) |
| GL-ZaH | Not assigned | GRA | **bare 43 / evergreen arctic dwarf shrub 53 / deciduous arctic shrub 3 / arctic C3 grass 1** | PROPOSED (needs site FATES map) | Cassiope heath: vascular 57% (Cassiope 53, Salix 3), mosses 8, lichens 3; ~32% uncovered; LAI 0.2–0.3 | [Bay 1998 vegetation map](https://www.zackenberg.dk/fileadmin/Resources/DMU/GEM/Zackenberg/pdf/vegetation-mapping-zackenberg-valley_.pdf), [heath-site thesis](https://www2.dmu.dk/Pub/phd_lgr.pdf), [six-site review](SIX_SITE_BARE_GROUND_PFT_EVIDENCE_20261025.md) |
| IT-Tor | Not assigned | GRA | **C3 grass 100 (candidate)** | CANDIDATE (qualitative) | Nardus stricta-dominated alpine meadow (species only); no bare-ground evidence | [Agric. For. Meteorol. 2017](https://www.sciencedirect.com/science/article/abs/pii/S0168192317300515) |

**Remaining decisions.** OPEN: DK-Sor (split of 20% spruce+larch between ENF and DNF), FR-FBn (share of Quercus ilex in the non-pine 25%), BE-Bra (22% unclassified), CH-Lae (8% unlisted). PROPOSED sites need a surface build; GL-ZaH also needs a site-only FATES parameter map because no default host type maps solely to `broadleaf_evergreen_arctic_shrub`. ES-Agu's "57% of vegetation" denominator should be checked against Rey et al. (2011) Table 1, and ES-LJu's cushion-shrub phenology (HLM 9 vs 10) is a modelling choice.

---

## Consolidated 38-site PFT evidence and model audit — 24 October 2026

**25 October 2026 — bare ground for six sparse/open sites.** [Six-site PFT and bare-ground evidence](SIX_SITE_BARE_GROUND_PFT_EVIDENCE_20261025.md) and its [CSV](six_site_bare_ground_PFT_proposals_20261025.csv) give measured vegetation versus non-vegetated ground and a proposed `PCT_NAT_PFT` including host bare ground (index 0) for GL-ZaH (bare 43), IL-Yat (bare 52, implemented), ES-LJu (bare 49), IT-Noe (bare 34, range 9–58), ES-Agu (bare 49) and NL-Loo (bare 0; open 3.5% is heather/grass). The master CSV carries these in four `BareGround_*` columns. GL-ZaH additionally needs a site-only FATES parameter map, because no default host type maps solely to the evergreen arctic shrub.

**25 October 2026 update — FIXNC cohorts and IL-Yat crown cover.** The master CSV now links every station to the [Non-Competition-CLM-experiment](https://github.com/lyanyeung/Non-Competition-CLM-experiment) cohorts: 2 protected examples, Batch01 (10), Batch02 (10), Batch03 (10: IT-Lav, FI-Let, IL-Yat, DE-Obe, CZ-Stn, DE-Lnf, DE-Hzd, GF-Guy, AT-Neu, CH-Cha) and 6 not assigned (CH-Aws, GL-ZaH, ES-Agu, IT-Tor, DE-Gri, DE-RuR, with reasons). The `FIXNC_Input_PCT_NAT_PFT` values are prescribed model inputs (named proxies), not observations. **IL-Yat** evidence now records the measured mean crown cover of **48%** (crown widths in 72 plots; FVC 0.40–0.70) and 36.8% rock outcrop, so its FIXNC input is **bare ground 52% / ENF 48%** instead of ENF 100 ([literature review](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/examples/Batch03_10/docs/IL_Yat_bare_ground_PFT_literature_20261025.md)). The earlier `FATES_*` model columns are unchanged and still describe the original competition-mode campaign runs.

**Use these links as the authoritative entry points for the current four-batch comparison:**

| Deliverable | Coverage and meaning |
|---|---|
| [**MASTER 38-site observed vs FATES PFT table (CSV)**](MASTER_38_SITE_OBSERVED_VS_FATES_PFT_20261024.csv) | **38 rows × 48 fields**, one per EC station: original field percentages and their measured denominators, original reference URLs, FATES end-spin-up dominant PFT/percentages, earlier CLM host-surface audit where available, and mismatch/status. **25 Oct 2026:** six `FIXNC_*` columns record each site's fixed-biogeography/no-competition cohort (examples, Batch01/02/03, not assigned), case name, prescribed `PCT_NAT_PFT` input, soil-texture input and run status |
| [**Observed PFT percentages: full 38-site report (Markdown)**](38_SITE_OBSERVED_PFT_PERCENT_REPORT_20261024.md) | Per-station source evidence and percentage definitions, differences among tree species share, cover, area, basal area and tree carbon; explicit qualitative-data gaps |
| [**Observed vegetation source table v2 (CSV)**](38_site_observed_PFT_percent_evidence_v2_20261024.csv) | **28** stations with some numeric vegetation evidence (NOT necessarily measured PFT area) and **10** with only qualitative descriptions |
| [**FATES model PFT outcome and site-consistency report**](comparison_20261024/FOUR_BATCH_EC_PFT_VS_FATES_REPORT_20261024.md) | **34** published final 14-class FATES VegC vectors: **6** broad functional matches, **2** partly matching mixed forests, **26** mismatches; 4 sites have no published final model-PFT comparison |
| [**34-site needleleaf disappearance timing (CSV)**](comparison_20261024/four_batch_initial_to_final_needleleaf_extinction_34sites.csv) | First-year needleleaf VegC vs last-year 0% at all 34 published sites; spin-up extinction timing |

**Scientific safeguards:** 28 numeric records do **not** mean 28 valid fixed-biogeography area vectors. The most promising *spatial fraction candidates* are DE-Tha and NL-Loo, both still needing footprint/landunit review. Species proportions (e.g., DE-Hai tree carbon or FI-Let basal area) cannot be equated to FATES modeled vegetation-carbon share or used directly as prescribed PFT area. No station is yet marked as an approved area-fraction forcing prescription.

**Scope:** batches 6, 8, 11 and 13 have 38 tower stations. In the archived October 24 monitoring snapshot, IT-Noe and CH-Aws had not completed their 1000-year runs; DE-Lnf and ES-Agu had completed model years but lacked GitHub-published PFT because the combined plotting pipeline could not locate original EC half-hourly files. These four have explicit missing/pending states in the master comparison rather than invented FATES percentages.

---

## New cross-batch modeled PFT realism report — 24 October 2026

**[Four-batch tower vegetation vs FATES PFT report](comparison_20261024/FOUR_BATCH_EC_PFT_VS_FATES_REPORT_20261024.md)** joins the previously curated 38-site vegetation-evidence inventory, published model-end FATES vegetation carbon shares, and the existing 15-site CLM input surface audit.

- 34/38 station final-model PFT distributions were published (36 runs have reached at least 1000 model years per user-provided Slurm status).
- Dominant-functional-type screening: **6 broad matches**, **2 partial mixed-forest matches**, **26 mismatches**.
- **All 34 published FATES PFT vectors show 0% final needleleaf evergreen or deciduous vegetation carbon**, including spruce/pine tower stations.
- Their first archived model year actually contains **21.59–40.66%** needleleaf VegC (median **35.40%**): needleleaf is present initially and disappears during spin-up, falling below 0.01% by year 50 in **28/34 stations**. [34-site onset-to-extinction analysis](comparison_20261024/four_batch_initial_to_final_needleleaf_extinction_34sites.csv).
- DE-Lnf / ES-Agu have 1000-year models but published PFT is missing because the EC half-hourly source discovery failed. IT-Noe / CH-Aws remained unfinished at the last cited monitoring checkpoint.
- [Detailed 38-site numerical comparison](comparison_20261024/four_batch_EC_original_versus_FATES_PFT_38sites.csv); [full 14-PFT terminal vectors for 6 / 8 / 11 / 13 cohorts](comparison_20261024/).

This is a functional-group *screen*, **not** proof of matching observed area percentages. Original percentages have differing denominators (basal area, stand species share, cover, carbon stocks); modeled `FATES_VEGC_PF` is plant carbon share. No original forcing, active model case, or surface was changed.

---


**Research inventory; not a FATES surface modification. Updated 22 October 2026.**

## Scope

This directory follows the existing cases in `examples/FLUXNET_MultiSite_6`, `FLUXNET_MultiSite_8`, `FLUXNET_MultiSite_11`, and `FLUXNET_MultiSite_13`. The collection comprises **38 distinct stations** (6 + 8 + 11 + 13). It deliberately includes Greenland, Israel, French Guiana, and non-ICOS input packages, preserving actual experiment membership.

Main table: [38_site_PFT_evidence.csv](38_site_PFT_evidence.csv). **Every record is a literature/metadata lead for expert review, not a completed site-level FATES PFT area-fraction target**. Source URLs identify documents/landing pages; some source-specific numerical values, units, stand extents and historical definitions remain to be checked against original tables. The table is an evidence inventory rather than an independently validated extraction.

## Evidence levels and denominator gate

* `NUMERIC_AREA`: measured fraction of surveyed *land area*. This is closest to a CLM/FATES grid-area input, but a fixed-distance circle is **not** a meteorologically weighted EC footprint.
* `NUMERIC_GROUND_COVER`: reported canopy/plant cover of the survey ground. Multiple canopy layers and overlapping species may prevent simple summation.
* `NUMERIC_VEGETATED_COVER`: percentages are conditional on the **vegetated** area; obtain vegetated fraction before computing proportions over ground.
* `NUMERIC_BASAL_AREA`: basal area (cross-sectional tree-stem area), not horizontal ground/canopy area.
* `NUMERIC_SPECIES`: species/stand composition of a specific reference stand. Do not assume the denominator is area, tree count, carbon, volume or basal area without checking the primary reference.
* `NUMERIC_TEMPORAL`, `NUMERIC_CONFLICT`, `NUMERIC_COVER_CONFLICT`: observations differ in survey date/stand or metric; preserve conflicting reports separately.
* `TOTAL_COVER_ONLY`: overall herbaceous cover, **not** relative herbaceous species fractions.
* `QUALITATIVE_ONLY`: no defensible exact vegetation percentage obtained.

The dataset currently has **22 records referencing at least one quantitative observation or conflicting quantitative observations and 16 qualitative-only records**. Those counts **do not imply** 22 ready-to-use PFT fractional compositions. Even a 100% tree species share is not proof that 100% of the EC footprint or FATES grid is naturally vegetated.

## Functional mapping: use cautiously

* **ENF:** evergreen needleleaf (e.g., Picea abies, Pinus sylvestris, Abies alba, Pseudotsuga menziesii).
* **DNF:** deciduous needleleaf (e.g., **Larix decidua**, which must not be merged into ENF).
* **DBF:** deciduous broadleaf (Fagus sylvatica, Quercus robur/petraea, Betula, Acer, Fraxinus).
* **EBF:** evergreen broadleaf (e.g., Quercus ilex). Mediterranean sclerophylls and woody shrubs require checking against the *actual* FATES parameterization before classifying into a supported functional type.
* Herbs, grasslands and shrubs require species-to-PFT mapping, C3/C4 context, grass/woody traits and survey ground-cover verification. A site IGBP class is **not** itself a FATES-specific PFT mixture.

## Priority scientific follow-up

1. **Validate each numerical claim** from the linked source's actual site/table and record source title, author, publication date, measurement year, page/table, denominator and surveyed area. Links alone are not sufficient evidence. Check especially FI-Hyy, FR-Hes, CH-Lae, FR-Pue and the comparative 2020 Table S2.
2. Extract tower-specific **ICOS BADM vegetation records** (TREE, SPP, AGB, BIOMASS) when publicly available; distinguish presence of BADM field names from having a numeric PFT distribution.
3. Request stand inventories and forest management compartment descriptions for remaining qualitative forests (e.g., IT-Lav, DE-Lnf, DE-Obe, DE-Hzd). Quantify disturbance/change where material.
4. For grasslands and drylands (e.g., ES-Agu, DE-Gri, IT-Tor, CH-Aws), search botanical quadrats, vegetation transects, fractional cover and bare ground; report time/management history.
5. Only if field/tower vegetation information remains insufficient, derive an **EC-footprint-weighted high-resolution land-cover** estimate, with classification/temporal uncertainty; then use **original year-2000 CLM surface** as a low-priority historical baseline.
6. Compare the *actual case* effective surface and active FATES parameter-file definitions, and any available per-PFT output. `PCT_NAT_PFT` describes host-CLM landunit input, not observed FATES PFT percentages. `FATES_VEGC_PF` proportions describe biomass/carbon, **not area**.

## Non-invasive policy

No case settings, surface NetCDFs, DATM/forcing files, parameters, CIME restart, Slurm jobs or model archives were changed by this documentation update. A scientific `MATCH` label is prohibited until matching denominators, survey period, model area metric, and relevant FATES PFT definitions are independently established.

Source used for many quantitative **stand composition leads**:
[Flechard et al., 2020, Biogeosciences supplement, Table S2](https://bg.copernicus.org/articles/17/1583/2020/bg-17-1583-2020-supplement.pdf).

This directory intentionally contains no protected FLUXNET/ICOS raw package contents.
