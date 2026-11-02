# Alice Mulga (AU-ASM) TERN biomass provenance query — evidence through Stage35

**Status:** Reproducible source arithmetic discrepancy requiring publisher clarification (**not** an established defect, not an approved correction). Analysis date: **2026-11-02**. Sources, forcing, surfaces, FATES parameters and CIME/Slurm cases were not modified. All stages in this note were run in read-only forensic modes on IRIDIS6.

## Published dataset and provenance

**Cite:** Cleverly, J. (2022). *Alice Mulga Stem Diameter, Height and Aboveground Woody Biomass Data 2014*. Version 1.0. Terrestrial Ecosystem Research Network. https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed .

The TERN metadata states that individual stems were mapped and measured **in a 0.06 ha subplot during 2014**, including diameter at 20 cm above ground (**D20**, NOT DBH at 1.3 m) and plant height. It states that 2018 stem growth was **derived from dendrometer-informed uniform basal area increment** and that the trees were **not surveyed again as individual stems**. Biomass was estimated with equations referencing **Návar et al. (2013)**, not directly destructively weighed. Published stand-level AGB was scaled to **tonnes per hectare**. The original site-level record has a 100 × 100 m `core1ha` *plot label/dimensions*, which must not be confused with the 0.06 ha *sampled stem area*.

The original released CSVs were acquired and SHA256 verified:
- `Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv`: **222 rows, 111 distinct (siteId,plotId,plantId,stemId) keys, each with one 2014 field row and one 2018 derived row**. SHA256 `7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55`.
- `Alice_Mulga_diameter_height_biomass_data_dictionary_XcBdgzD.csv`: **21 dictionary rows**. SHA256 `82c2d28b8616ee31f1c687ef600f4249592827503adbdcfce73e1e06b6da44fe`.
- `Alice_Mulga_site_level_biomass_data_v3pQRMW.csv`: **2 site-year rows**, 11 columns, `standBiomass_tonnesPerHectare`. SHA256 `f4fcfe46fd5132ed040187ae443441d37822e18c8deb48c01be667af51b9fea8`.

All released source years were parsed using original **D/M/YYYY** strings. All 222 source stem rows are D20 at 0.2 m; none supplies a direct DBH–height pair.

## 1. Independently reproduced stand-vs-stem arithmetic (Stage34)

The stand product's source values are **37.4168 t/ha in January 2014** and **44.6277 t/ha in June 2018**. With TERN's 0.06 ha sampled-stem area, exact `Decimal` calculations give:

| Year | Published stand AGB (t/ha) | Source 111-stem sum (kg) | Sum / (0.06 ha × 1000 kg/t) (t/ha) | Original sum − published stand × 60 (kg) |
|---|---:|---:|---:|---:|
| 2014 | 37.4168 | 2247.437182506 | 37.4572863751 | **+2.429182506** |
| 2018 (derived) | 44.6277 | 2675.232142231 | 44.5872023705167 | **−2.429857769** |

Combined-year discrepancy is **−0.000675263 kg**, compatible with the precision of two stand values published to four decimal places in t/ha. This by itself does **not** establish why the source totals differ.

## 2. Unique tested source-stem arithmetic candidate (Stages34–35)

When examining *each* of 111 original **2014** stem AGB values for a single-value, cross-year inclusion/exclusion hypothesis, exactly **one** source candidate recreates **both** published stand values when rounded to their original four decimal places:

- `siteId`: `Alice Mulga`
- `plotId`: `Alice Mulga, core1ha`
- `plantId`: **`99`**
- `stemId`: **`1b`**
- `scientificName`: *Eremophila latrobei* ssp. *glabra*
- **2014** row: 22/1/2014 phenomenonTime, D20 **4.6 cm**, height **1.9 m**, original AGB **2.429615547 kg**, `stemStatus=Alive`, `comment=NA`.
- **2018** row: 1/6/2018 phenomenonTime, derived D20 **5.3 cm**, height **1.9 m**, derived AGB **3.713499951 kg**, `stemStatus=Alive`, `comment=NA`.

The **arithmetic counterfactual**—*omit that 2014 AGB from the 2014 source sum, and include an additional copy of that original 2014 value in the 2018 derived source sum*—gives:

```text
2014: (2247.437182506 − 2.429615547) kg / 60
    = 37.41679278265 t/ha  -> published rounding 37.4168

2018: (2675.232142231 + 2.429615547) kg / 60
    = 44.62769596296667 t/ha -> published rounding 44.6277
```

The seven explicit Stage35 counterfactuals and their *both-year* match status:

| Test | Matches both published years to 4dp? |
|---|---|
| All original 2014/2018 stem rows in corresponding years | No |
| Omit Plant99 2014 only | No (2014 only) |
| Add extra 2014 Plant99 AGB to 2018 only | No (2018 only) |
| **Omit Plant99 2014; add its 2014 AGB to 2018** | **Yes** |
| Omit Plant99 2014; substitute its 2014 AGB for its 2018 AGB | No |
| Omit Plant99 2014; add extra 2018 Plant99 AGB to 2018 | No |
| Omit Plant99 from both years | No |

**Interpretation limit:** This is a unique match **within these seven tests and the single-2014-stem transfer search**. It is not a unique explanation among all conceivable original processing operations. The actual publisher's inclusion rules, code and input-version history are not available to this audit; source filtering, grouping, allocation, allometry, aggregation or release-version differences could also explain the arithmetic. **No erroneous join, actual source reallocation, or data-entry mistake has been proven. No corrected source files have been produced.**

## 3. Related *separate* 2018 derived-AGB consistency concerns (Stages30–32)

The exact original 2014/2018 stem pairs show major internal inconsistency for many 2018 derived AGB values even if the stand arithmetic candidate were resolved.

- Stage30 source QC: **48 of 111 unique stems** received at least one *screening* flag (not 48 confirmed errors). Across the cohort: **37** derived AGB decreases, **36** D20-up + height-stable + AGB-down stems, **20** changes exceeding 50 kg in absolute value.
- Stage31 within-species D20–AGB Spearman rank correlations:
  - *Acacia aneura* (n=43): **0.9990556** (2014) → **0.2371875** (2018 derived).
  - *Acacia aptaneura* (n=60): **0.9452423** → **0.3182653**.
  - Identical derived AGB values were repeated across different stems; presence of additional undisclosed model inputs cannot be excluded.
- Stage32 **in-sample** log(2014 estimated AGB) vs log(2014 D20) reference: *A. aneura* R² **0.9999665**, *A. aptaneura* R² **0.9481079**. Applied to corresponding derived 2018 D20, **37/103** Acacia stem AGB values fell below 0.2× or above 5× the empirical baseline prediction. The 2014 reference AGB was *already allometrically estimated*, so this is **not independent biomass validation**.

The stand CSV is based on the same product lineage and is **not independent confirmation** of 2018 per-stem AGB. These concerns are distinct from the Plant99 single-value aggregation arithmetic.

## 4. Questions for TERN dataset curator or original data author

1. What exact inclusion/exclusion and date-grouping rules, source version and program produce `standBiomass_tonnesPerHectare` from the original stem CSV for 2014 and 2018? Does the **0.06 ha** stem survey represent the exact numerator used in each record?
2. Is Plant **99**, Stem **1b**, *Eremophila latrobei* ssp. *glabra*, treated differently in stand aggregation? Can a grouping/row-selection audit explain the reproduced two-year `2.429615547 kg` arithmetic?
3. Are the 2018 `aboveGroundBiomass_kilograms` values aligned by `(siteId,plotId,plantId,stemId)`, and which exact equation, input variables, coefficients, and processing code (Návar et al. 2013 adaptation) were applied? Why do large D20 stem classes sometimes receive much smaller 2018 derived AGB than very small D20 stem classes?
4. Was there any later version, QA-removal, partial-subplot sampling or release mismatch between the site-level stand and stem products? Are the provenance scripts / mapping table available?

If clarification indicates a documented site-vs-stem cohort or parameter difference rather than an error, the audit's status should be revised accordingly. **Do not state that the published dataset is wrong before publisher confirmation.**

## 5. Reproducible source-auditing code and machine-readable outputs

GitHub repository: https://github.com/lyanyeung/CLM-FATES-single-site-workflows/tree/main/examples/OzFlux_MultiSite_09 .

- `scripts/stage30/30_asm_2018_derived_D20_AGB_outlier_source_reconciliation_READONLY.py`
- `scripts/stage31/31_asm_TERN_2018_AGB_join_formula_consistency_READONLY.py`
- `scripts/stage32/32_asm_2014_D20_AGB_empirical_baseline_vs_2018_derived_READONLY.py`
- `scripts/stage33/33_asm_TERN_site_level_AGB_original_source_intake_READONLY.py`
- `scripts/stage34/34_asm_TERN_006ha_stand_AGB_source_reconciliation_READONLY.py`
- `scripts/stage35/35_asm_Plant99_AGB_year_grouping_counterfactual_and_provenance_READONLY.py`

Verified IRIDIS6 output folders (for operator, *not* checked into GitHub):
- Stage34 `/home/ly3n24/ozflux_stage34_20261102T193337Z`
- Stage35 `/home/ly3n24/ozflux_stage35_20261102T194156Z`

Official source files and output TSV/JSON reports remain on IRIDIS6. GitHub holds source code and research notes only, not original raw CSV data.

**Science decision:** original source and all model inputs unchanged. 2018 derived AGB remains HOLD for quantitative FATES calibration; 2014 observed stem heights remain useful for allometry height-cap structure screening (27 of 103 original Acacia stem IDs exceed default FATES7 height plateau 4.735410175 m). D20 measured at 0.20 m must never be silently treated as FATES DBH at 1.30 m. PFT, soil, meteorological forcing and full AD400 approval are **not** implied by this source audit.
