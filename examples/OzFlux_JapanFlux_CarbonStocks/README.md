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

## Stage01 result (IRIDIS6, 3 Nov 2026; console truncated at JP-Tom)

**JapanFlux BIF files.**
- They hold no biomass, soil-chemistry or `GRP_DM_*` disturbance groups.
- Present groups: site description, IGBP (with history comments), HEIGHTC, LAI, CLIM_AVG and UTC offset. They also hold flux-processing groups (FLUX_REF, UST_THR, ERA_DOWN, ONEFLUX).

**Stand history found in our own files:**

| Site | History |
| --- | --- |
| JP-Fhk | Larch "planted around in 1950, and thinned … in 2014 and 2015" |
| JP-Tef | "Conifer-Hardwood mixed forest until January, 2003, Young larch plantation from late October 2003 (ca. 30000 saplings (ca. 2500 saplings ha-1, 0.04 tC ha-1))" |
| JP-Tmd | IGBP GRA from 2005, OSH from 2011, DBF from 2017 (the post-windthrow trajectory); canopy height 0.5–3 m (2005–2015); LAI 4.2 (2015) |
| JP-Spp | A secondary broadleaf forest "which had grown after wildfire" |
| JP-Khw | Sugi / hinoki "over 50 years old" |
| JP-Tom | BADM Disturbance_and_Management: `DM_EXT_WEATHER` = Other on 2004-09-08 (Typhoon Songda) |
| JP-Tgf | BADM Disturbance_and_Management: `DM_GENERAL` = Undisturbed (2001-01-01). The annual mowing is not recorded there |

**Canopy height (HEIGHTC) and LAI:**

| Site | Canopy height (m) | LAI |
| --- | --- | --- |
| JP-Api | 17 | — |
| JP-Fhk | 21.9–24.8 | 2.8 |
| JP-Fjy | 20 | 5.0 |
| JP-Khw | 10 | — |
| JP-Spp | 20 | 4.0 |
| JP-Tak | 15 | 1.7–5.5 |
| JP-Tef | 1–18 | 1.3–8.0 (2002–2010) |

**OzFlux L6 global attributes.** They give canopy height and vegetation only:
- canopy height: AU-ASM 4.4, AU-Cow 26, AU-Cpr 3, AU-DaS 16.4, AU-Gin 6.8 (mean 4.8), AU-How 16, AU-Stp 0.5, AU-Tum 40 m;
- AU-Dry's attribute reads 0.15 m, which is probably the grass layer;
- the only event in the attributes is AU-Gin's new EC system from 12 Feb 2021.

Every carbon stock, every event and every annual flux therefore has to come from the literature.

## Scripts

| Script | Where | What |
| --- | --- | --- |
| [01_site_metadata_carbon_disturbance_READONLY.py](scripts/01_site_metadata_carbon_disturbance_READONLY.py) | IRIDIS6 login node, read only | Reads the JapanFlux BIF (BADM) groups in every package: biomass, litter, soil chemistry, `GRP_DM_*` disturbance / management, dominant disturbance, site description, stand / species, reference papers. LAI / HEIGHTC are summarised. It also reads the standalone BADM workbooks (JP-Tgf, JP-Tom) and the OzFlux L6 global attributes that mention vegetation or disturbance. Console capped; full TSVs written |
