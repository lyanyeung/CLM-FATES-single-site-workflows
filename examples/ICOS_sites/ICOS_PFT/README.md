# ICOS_PFT: observed vegetation evidence for four FLUXNET multisite campaigns

## Consolidated 38-site PFT evidence and model audit — 24 October 2026

**25 October 2026 update — FIXNC cohorts and IL-Yat crown cover.** The master CSV now links every station to the [Non-Competition-CLM-experiment](https://github.com/lyanyeung/Non-Competition-CLM-experiment) cohorts: 2 protected examples, Batch01 (10), Batch02 (10), Batch03 (10: IT-Lav, FI-Let, IL-Yat, DE-Obe, CZ-Stn, DE-Lnf, DE-Hzd, GF-Guy, AT-Neu, CH-Cha) and 6 not assigned (CH-Aws, GL-ZaH, ES-Agu, IT-Tor, DE-Gri, DE-RuR, with reasons). The `FIXNC_Input_PCT_NAT_PFT` values are prescribed model inputs (named proxies), not observations. **IL-Yat** evidence now records the measured mean crown cover of **48%** (crown widths in 72 plots; FVC 0.40–0.70) and 36.8% rock outcrop, so its FIXNC input is **bare ground 52% / ENF 48%** instead of ENF 100 ([literature review](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/examples/Batch03_10/docs/IL_Yat_bare_ground_PFT_literature_20261025.md)). The earlier `FATES_*` model columns are unchanged and still describe the original competition-mode campaign runs.

**Use these links as the authoritative entry points for the current four-batch comparison:**

| Deliverable | Coverage and meaning |
|---|---|
| [**MASTER 38-site observed vs FATES PFT table (CSV)**](MASTER_38_SITE_OBSERVED_VS_FATES_PFT_20261024.csv) | **38 rows × 44 fields**, one per EC station: original field percentages and their measured denominators, original reference URLs, FATES end-spin-up dominant PFT/percentages, earlier CLM host-surface audit where available, and mismatch/status. **25 Oct 2026:** six `FIXNC_*` columns record each site's fixed-biogeography/no-competition cohort (examples, Batch01/02/03, not assigned), case name, prescribed `PCT_NAT_PFT` input, soil-texture input and run status |
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
