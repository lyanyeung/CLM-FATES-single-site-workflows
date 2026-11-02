# AU-ASM source-priority decision: 2018 FIRST (2026-11-02)

**Operator instruction:** Prioritise the *latest relevant 2018 vegetation/biomass evidence*. The Stage30–35 historical source-data discrepancy is archived in GitHub; do **not** create further speculative aggregation/counterfactual stages or send new support emails unless new information arrives. Do not silently approve old, questionable derived biomass simply because it is labelled 2018.

## Tier A — 2018 *potential direct field dataset*, FIRST

- [TERN/ARDC: Vegetation Data, Direct Measure of Stems, Standing Above Ground Biomass, Alice Mulga SuperSite, Core 1 ha, 2018](https://researchdata.edu.au/vegetation-data-direct-ha-2018/1340784), identifier **`supersite.1041`**, legacy TERN network, edition **5**; Eamus and collaborators.
- Its independently indexed metadata describes **measurements taken in 2018**, including **D20 at 20 cm above ground** and plant **height**, allometry using **Paul et al. (2016)** and **Návar et al. (2013)**, and **2011–2018 dendrometer records**. Data year 2018.
- It has a legacy catalog resource link `https://supersites.tern.org.au/knb/metacat/supersite.1041/html`, which is **NOT** itself verified as a downloadable 2018 stem table. Live legacy link redirected/failed in current research lookup. **No original edition-5 2018 stem/height/AGB file has been downloaded or SHA256 verified.**
- Do NOT infer this independent registry entry is the same stem cohort, survey plot, allometric pipeline or original file as the separate published Cleverly 2022 source. Its metadata says 2018 *measurements* while the latter explicitly describes a **2018 derived extrapolation without stem resurvey**: this contradiction is a reason to get original records, not to collapse the releases.
- **Next intake:** acquire the underlying `supersite.1041` edition-5 original resource(s), record exact URL/source license/SHA256, inspect actual 2018 timestamps, site/plot/stem identifiers, D20 measurement point, measured height, AGB calculation columns, biological status, sapwood/dendrometer context and sampled plot area. Only then consider using it for empirical 2018 structural and AGB constraints.
- The 2018 edition-5 catalog metadata is **not a validated field-data sample**, and does not establish canopy cover, PFT fractions or model DBH.

## Tier B — accessible 2018 *derived* release, SECONDARY source

- TERN [Cleverly (2022), Alice Mulga Stem Diameter, Height and Aboveground Woody Biomass Data 2014](https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed) contains **111 original stem IDs**, each with 2014 observed and 2018 **derived** rows (222 total). It explicitly says no new individual stem survey in 2018.
- Source CSV SHA256 `7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55`.
- Official site-level source CSV SHA256 `f4fcfe46fd5132ed040187ae443441d37822e18c8deb48c01be667af51b9fea8`; its **2018 derived** stand `44.6277 t/ha` is a released calculated number, **not independently validated field AGB**. Source actual sampled stem area `0.06 ha`; `core1ha` is the enclosing plot label.
- D20 at **0.2m** is **NOT** FATES DBH at **1.3m**. Do not infer DBH–height fits from D20.
- Existing source-derived **2018 heights** should be used only as **provisional structural scenario/sensitivity**, not independent 2018 measurements (many heights equal the 2014 original).
- **2018 AGB remains SCIENCE HOLD**: Stage30 found 48/111 flagged source stems; Stage31 found breakdown in D20–AGB Spearman associations; Stage32 found 37/103 Acacia stems with 2018 derived AGB under 0.2× or over 5× the 2014 empirical D20–AGB reference.
- The source-aggregation arithmetic match of Eremophila Plant99/Stem1b for 2014 vs 2018 stand numbers is archived in [Stage35 technical note](STAGE35_TERN_AGB_PROVENANCE_QUERY_20261102.md) and is **NOT** proven publisher code corruption or an approved correction.
- For reference to real 2014 canopy structure only, **27/103 distinct Acacia stem IDs** exceed the default FATES7 `H(DBH)` height plateau of **4.735410175m**. This evidence does not itself approve FATES4, PFT fractions or a surface.

## Model and archive decision

**Now:** Prioritise 2018 independent structural/AGB files; classify the secondary 2018 records carefully, retain original SHA256 inputs, and pause any further speculative historic source-repair iterations. Keep the existing AU-ASM meteorological forcing candidate, source L6, Stage16 reference surface, and FATES active parameter files unchanged.

**Later, only after raw survey source passes**: audit actual 2018 species, structural height distribution, D20/DBH definition, basal area, cover and sampling area. If only D20 is provided, the model-specific H(DBH) comparison needs an external taper/DBH source; do NOT invent one. Do not scale stand AGB as a direct carbon flux, nor infer tree/area cover from observed stem shares. Revisit soil stratigraphy and forcing scientific QC before any new model case or AD400 spin-up.

**Stage36 published (not yet operator-run):** `scripts/stage36/36_asm_2018_first_independent_survey_locator_and_source_audit_READONLY.py`. It pins prior successfully verified original stem, stand and Stage35 data, inventories the 111 **derived** 2018 source records, and probes only two **catalogue URLs** for the independent 2018 release. It does not invent/auto-download any raw 2018 field filename, and records an explicit absence of the original field data when not available. Outputs JSON and a clearly labelled secondary-source TSV in new HOME only. No source/model writes, Slurm or AD400 authorised.
