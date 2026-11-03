# OzFlux_JapanFlux_CarbonStocks — carbon stocks, stand age and disturbance records

Started 3 November 2026; the fifth OzFlux / JapanFlux topic. An 800-year spin-up with fixed vegetation ends close to carbon equilibrium, so the model's mean NEE will be near zero, while most towers are net sinks. This folder collects the observations needed to judge that gap and to cut the evaluation years:
- vegetation and soil carbon stocks;
- stand age;
- dated disturbance and management events;
- published annual NEE / GPP / ER.

**Status, 3 Nov 2026:**
- Literature search for the 9 OzFlux and 11 JapanFlux sites in progress.
- The IRIDIS6 read-only Stage01 script, which reads the metadata already inside our own source files, is published.

## Planned files

| File | Content |
| --- | --- |
| `data/carbon_stock_evidence_<date>.csv` | Aboveground / root / total vegetation carbon, litter, coarse woody debris, SOC stock (with depth), basal area, stem density, canopy height, stand age. Each row carries the value as printed, a kg C m⁻² conversion with the carbon fraction used, the year, the method, the tower specificity, the source, a locator, a verbatim quote and a verification level |
| `data/disturbance_management_events_<date>.csv` | Fire (single events and the fire regime), cyclone / typhoon / windthrow, clearing, clear-cut, thinning, planting, mowing, grazing, insect defoliation, dieback, instrument changes. Each with dates and the effect on the stand |
| `data/published_annual_fluxes_<date>.csv` | Annual NEE / GPP / ER by period, recorded with negative = sink |
| `OZ_JP_CARBON_STATE_20_SITES_<date>.md` | One line per site: stocks, age, events, typical NEE, and whether the stand is near equilibrium or recovering |

## Data restriction: AU-ASM stem and biomass data

TERN Support (A. Singh Ramesh) replied by email on 3 Nov 2026 about the *Alice Mulga Stem Diameter, Height and Aboveground Woody Biomass* dataset (Cleverly 2022):
- **2018 dendrometer-informed values: do not use.** They were published without QC checks, and how they were derived is not documented. Status `EXCLUDED_BY_DATA_PROVIDER`.
- **2014 census values: use with caution.** The new site PI (Dr Anne Griebel) could not locate some of the stems reported as measured. Status `USE_WITH_CAUTION`.
- **Replacement data are pending.** A 2025/26 census of a newly set-up plot, with stem-level data, provenance and the biomass calculation, is in QC for the TERN Data Discovery Portal. If it is not there by late November / early December 2026, contact TERN Support for an update.

This agrees with the [OzFlux_MultiSite_09](../OzFlux_MultiSite_09/) Stage30/31 flags on the 2018-derived stems. Note also that the new plot describes the stand **after** the 2018–2020 mulga dieback, which matches the Mulga2 tower period (2024–2026). It does not describe the pre-dieback state (2013–2017) used for the AU-ASM evaluation window.

## Scripts

| Script | Where | What |
| --- | --- | --- |
| [01_site_metadata_carbon_disturbance_READONLY.py](scripts/01_site_metadata_carbon_disturbance_READONLY.py) | IRIDIS6 login node, read only | Reads the JapanFlux BIF (BADM) groups in every package: biomass, litter, soil chemistry, `GRP_DM_*` disturbance / management, dominant disturbance, site description, stand / species, reference papers. LAI / HEIGHTC are summarised. It also reads the standalone BADM workbooks (JP-Tgf, JP-Tom) and the OzFlux L6 global attributes that mention vegetation or disturbance. Console capped; full TSVs written |
