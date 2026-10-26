# Search and provenance —26 October2026

## Membership and existing repository evidence

The membership audit used repository commit [`5b21921cad1d0b0f7c89edb3c1cc5c62d5aa4358`](https://github.com/lyanyeung/CLM-FATES-single-site-workflows/commit/5b21921cad1d0b0f7c89edb3c1cc5c62d5aa4358), its complete recursive file tree, and the five original `sites.tsv` files. The machine-readable [manifest](metadata/sites_50_manifest.csv) preserves each original path, package name and supplied first/last year. Source publications and official pages were checked on26 October2026.

Existing material reviewed: the five batch README files, the shared [AmeriFlux_sites collection](../../AmeriFlux_sites/), seven existing Batch01 vegetation/PFT ledgers, and the [ICOS_PFT master/report/final-candidate structure](../../ICOS_sites/ICOS_PFT/). Original source ledgers and experiment directories are preserved.

The most developed pre-existing PFT file was [Batch01 v4](../../AmeriFlux_sites/metadata/Batch01_EC_FATES_PFT_experiment_candidates_v4_20261023.tsv). Its10 records were carried forward with their denominator and the existing US-Aud operator decision. Primary rechecks recovered CA-Ca3 Table1, CA-Cbo stem census, CA-Man basal area, Turkey Point species descriptions, CA-LP1 juvenile table and the Bartlett author-copy PDF. They did not convert those quantities to measured ground area.

## Search approach

Each exact tower ID was checked against official AmeriFlux/FLUXNET metadata and its cited site literature. Searches combined the ID and site name with species composition, basal area, stem census, canopy/ground cover, vegetation inventory and disturbance. Follow-up papers or author/institution/government copies were used to inspect numerical tables and the sampled extent. The current search is a targeted evidence inventory, not a systematic-review claim that no further data exist.

The `nature-academic-search` multi-source workflow was applied to source discovery and verification. Its specialist academic MCP server was unavailable in this session; GitHub connector access and web retrieval of primary publications, official datasets and institutional copies supplied the evidence instead.

Source priorities were tower/footprint inventory or field cover, followed by tower-relevant published characterization and high-resolution crown mapping. Published model fCover was retained in separate fields. Regional IGBP definitions and coarse-grid surfaces were not used to invent exact site fractions. BIF field absence was not treated as proof that BADM or field inventories do not exist.

## Evidence ledger and retrieval limits

Five [JSON source ledgers](metadata/) preserve source titles, URLs, table/section locators, survey periods, spatial extents, measured denominators, verification notes, uncertainties and next evidence. Values were summarized rather than reproducing protected paper text. Third-party hosting of an author copy is labeled as such; the linked DOI identifies the original publication.

Some direct publisher/official URLs returned403,429 or timeout errors. Where primary content was accessible through an official indexed page or author/institutional copy, the row records that retrieval basis. The USGS Charleston canopy fraction was read from indexed primary text after direct-PDF access failed. No claim is made that complete release BADM files were downloaded for all50 sites.

The downloaded public Harvard HF069 CSV extends through2024. It was examined as a lead, but a new aggregation was not adopted without resolving live-tree, plot and temporal definitions. The reported Harvard percentages therefore retain the published historical Richardson2009 basal-area basis. The similar Howland towers are kept distinct; a pooled main/west description is not re-labelled a tower-specific composition.

## What is counted

There are **33 sites with at least one numerical composition/cover lead** and **17 with other evidence**. A historical nearby transect or an incomplete woody inventory can count as a numerical lead only with its scope restriction preserved; this is not33 verified full-footprint vectors. LAI, tree density, mortality/removal percentages and stand age alone do not count as numerical composition. CA-TP1's categorical entire-white-pine statement remains an explicit qualitative single-species assertion.

The11 historical ORCHIDEE configurations from [Mahmud et al.2021 Table1](https://doi.org/10.1029/2021JG006400) are not added to the observed-evidence count merely because they contain numbers. Their source-native PFT classes and periods are kept separate. The source table's group labels are not FATES indices.

No final AmeriFlux FATES PFT-carbon table was found in the audited repository records. Consequently, all final-output cells remain blank with an explicit not-found-in-reviewed-records status. This does not establish live job status or prove simulations have never run.

## Reproducibility

`python3 scripts/build_inventory.py --check` verifies the50 unique site IDs, batch membership, necessary source fields, scalar percentage ranges,11 published model-vector sums and exact regeneration of the six central tables/reports. Rounded source sums such as CA-Cbo100.3, Harvard99 and Bartlett97 remain documented. No missing observation is filled with zero, and no incomplete vector is renormalized.
