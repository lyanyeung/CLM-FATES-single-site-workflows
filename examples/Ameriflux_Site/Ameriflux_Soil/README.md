# Ameriflux_Soil — soil texture evidence and CLM-FATES recommendation for the 50 AmeriFlux sites

Started 26 October 2026. This folder covers the soil side, in the same way [Ameriflux_PFT](../Ameriflux_PFT/) covers vegetation. **Nothing here changes a case, surface file, forcing file or running job.**

## Recommendation: which soil texture to use in CLM-FATES

CLM-FATES reads soil texture from the surface file as `PCT_SAND` and `PCT_CLAY` on 10 layers (node depths 0.007, 0.028, 0.062, 0.119, 0.212, 0.366, 0.620, 1.04, 1.73 and 2.86 m). Silt is the remainder. CTSM converts texture into hydraulic and thermal soil properties through pedotransfer functions. `ORGANIC` (kg m⁻³) mixes in organic-soil properties. The default surface files take texture from a global soil grid, which can be far from the soil under a single tower.

Recommended order, applied **layer by layer**:

| Tier | Source | When used |
| --- | --- | --- |
| **T1 site measured** | (a) **ReESH** (AmeriFlux Regional Ecosystem Soil Hydraulics project): tower-plot samples at the surface, ~10–15 cm and ~50–100 cm, published per site on Zenodo as `ReESH_<SITE>` (CC BY 4.0); (b) **BADM** `SOIL_TEX_SAND/CLAY` in the site's BIF file; (c) tower-specific numbers from papers or site pages | First choice for every layer the samples cover |
| **T2 SSURGO point** | USDA NRCS Soil Data Access: dominant soil component of the map unit at the tower coordinates, by horizon | US sites, layers below the measured depth, or no T1 |
| **T3 SoilGrids 250 m** | ISRIC SoilGrids 2.0, six depths to 2 m | Canada and Brazil, or US gaps |
| T4 keep surface | Current grid values | Only when nothing above exists |

Rules:
- Below the deepest covered depth, the profile that supplied the layer above is extended downward. This happens for every source below 1–2 m.
- ReESH samples are grouped by their depth rank within each plot (surface, shallow, deep). The median across plots is used for each rank.
- Where site and survey topsoils differ by more than 25 sand points, the site is flagged rather than averaged.
- **Organic soils** (US-NC2 Histosol, Imnavait US-ICh/ICt, and the boreal or permafrost sites US-BZS, US-EML, US-Uaf, US-Rpf and CA-Man) need `ORGANIC` reviewed as well as texture. The script reports organic-matter density candidates (ReESH and SSURGO: OM% × bulk density; SoilGrids: 1.724 × SOC × bulk density) but does not apply them.
- Changing soil makes a **new surface variant**: a new case and a new spin-up. Lane A AD400 runs that are in progress (CA-TP4, BR-Ma2, CA-Ca3, CA-LP1) keep their gridded soil. Use the recommendation for the next cases, or as a soil sensitivity test.

## Evidence status, 26 October 2026

"Pending Stage01" means the values come from the IRIDIS run below: SSURGO for US sites, SoilGrids for all sites, plus ReESH and BADM wherever they exist. The preliminary numbers come from the eight sites whose measured values were already read. They are in [data/PRELIMINARY_8_SITE_CLM10_TEXTURE_20261026.csv](data/PRELIMINARY_8_SITE_CLM10_TEXTURE_20261026.csv). Stage01 downloads the raw ReESH files again (MD5 checked) and supersedes them.

| Site | Batch | Site-measured texture found | Other evidence | Preliminary top 0–30 cm sand / clay % (class) | Organic soil? |
| --- | --- | --- | --- | --- | --- |
| BR-Ma2 | Batch01 | — | clayey yellow latosol (xanthic Ferralsol) on plateau | pending Stage01 |  |
| CA-Ca3 | Batch01 | — | loamy sand on glacial till (regional series) | pending Stage01 |  |
| CA-Cbo | Batch01 | — | — | pending Stage01 |  |
| CA-LP1 | Batch01 | — | — | pending Stage01 |  |
| CA-Man | Batch01 | — | — | pending Stage01 | black spruce, moss/peat over clay (check) |
| CA-TP1 | Batch01 | — | sandy (former sandy agricultural field) | pending Stage01 |  |
| CA-TP3 | Batch01 | literature numbers | — | 98 / 1 (sand) |  |
| CA-TP4 | Batch01 | — | — | pending Stage01 |  |
| US-Aud | Batch01 | — | — | pending Stage01 |  |
| US-Bar | Batch01 | — | very fine sandy loam / sandy loam over loamy sand | pending Stage01 |  |
| US-BZS | Batch02 | — | — | pending Stage01 | boreal black spruce, organic/permafrost (check) |
| US-CMW | Batch02 | — | — | pending Stage01 |  |
| US-EML | Batch02 | — | — | pending Stage01 | tundra organic over mineral, permafrost (check) |
| US-GLE | Batch02 | — | — | pending Stage01 |  |
| US-Ha1 | Batch02 | ReESH [Zenodo 15993458](https://doi.org/10.5281/zenodo.15993458) | — | 66 / 11 (sandy loam) |  |
| US-Ho1 | Batch02 | ReESH [Zenodo 17344179](https://doi.org/10.5281/zenodo.17344179) | — | 58 / 11 (sandy loam) |  |
| US-Ho2 | Batch02 | — | — | pending Stage01 |  |
| US-Ho3 | Batch02 | — | — | pending Stage01 |  |
| US-ICh | Batch02 | — | silt loam under peaty layer | pending Stage01 | peat over silt loam, permafrost |
| US-ICt | Batch02 | — | silt loam under peaty layer | pending Stage01 | peat over silt loam, permafrost |
| US-Kon | Batch03 | — | — | pending Stage01 |  |
| US-Me2 | Batch03 | ReESH [Zenodo 15994222](https://doi.org/10.5281/zenodo.15994222) + literature numbers | — | 68 / 7 (sandy loam) |  |
| US-Me6 | Batch03 | ReESH [Zenodo 15994479](https://doi.org/10.5281/zenodo.15994479) | — | pending Stage01 |  |
| US-MMS | Batch03 | ReESH [Zenodo 15933402](https://doi.org/10.5281/zenodo.15933402) | — | pending Stage01 |  |
| US-MOz | Batch03 | — | — | pending Stage01 |  |
| US-Mpj | Batch03 | — | — | pending Stage01 |  |
| US-MtB | Batch03 | — | — | pending Stage01 |  |
| US-NC2 | Batch03 | ReESH [Zenodo 17342476](https://doi.org/10.5281/zenodo.17342476) | histosol over loamy marine sediment | pending Stage01 | Histosol (~25 cm organic) |
| US-NR1 | Batch03 | ReESH site summary (PI web page) | — | 57 / 17 (sandy loam) |  |
| US-NR3 | Batch03 | ReESH [Zenodo 17555021](https://doi.org/10.5281/zenodo.17555021) | — | pending Stage01 |  |
| US-Rpf | Batch04 | — | — | pending Stage01 | boreal, organic/permafrost (check) |
| US-Seg | Batch04 | ReESH [Zenodo 15996667](https://doi.org/10.5281/zenodo.15996667) | — | pending Stage01 |  |
| US-Ses | Batch04 | — | — | pending Stage01 |  |
| US-Slt | Batch04 | — | — | pending Stage01 |  |
| US-SP1 | Batch04 | — | — | pending Stage01 |  |
| US-SRG | Batch04 | — | sandy loam surface; some series clay Bt | pending Stage01 |  |
| US-SRM | Batch04 | ReESH [Zenodo 15997288](https://doi.org/10.5281/zenodo.15997288) | sandy loam / loamy sand series with clayey Bt in some units | pending Stage01 |  |
| US-Syv | Batch04 | ReESH site summary (PI web page) | — | 61 / 10 (sandy loam) |  |
| US-Ton | Batch04 | ReESH [Zenodo 16031874](https://doi.org/10.5281/zenodo.16031874) | — | pending Stage01 |  |
| US-Uaf | Batch04 | — | — | pending Stage01 | black spruce, organic/permafrost (check) |
| US-UiD | Batch05 | — | — | pending Stage01 |  |
| US-UMB | Batch05 | ReESH [Zenodo 16032019](https://doi.org/10.5281/zenodo.16032019) + literature numbers | — | 93 / 1 (sand) |  |
| US-UMd | Batch05 | — | — | pending Stage01 |  |
| US-Var | Batch05 | ReESH [Zenodo 16032314](https://doi.org/10.5281/zenodo.16032314) | — | pending Stage01 |  |
| US-Vcm | Batch05 | — | — | pending Stage01 |  |
| US-Vcp | Batch05 | — | — | pending Stage01 |  |
| US-WCr | Batch05 | ReESH site summary (PI web page) | sandy loam / loamy sand | 58 / 15 (sandy loam) |  |
| US-Whs | Batch05 | — | — | pending Stage01 |  |
| US-Wjs | Batch05 | ReESH [Zenodo 16032863](https://doi.org/10.5281/zenodo.16032863) | — | pending Stage01 |  |
| US-Wkg | Batch05 | — | — | pending Stage01 |  |

ReESH records confirmed by search are listed in [data/reesh_records_found_20261026.csv](data/reesh_records_found_20261026.csv): 13 sites. US-NR1, US-WCr and US-Syv also have ReESH summaries on the PI web pages. Stage01 queries Zenodo for **every** site, so more ReESH sites may appear. Literature and site-page evidence, with URLs, is in [data/literature_soil_evidence_20261026.csv](data/literature_soil_evidence_20261026.csv). Class-only descriptions are kept for cross-checking but are never turned into numbers.

## Run Stage01 on IRIDIS6

Run this from a login node, because it needs internet for Zenodo, USDA SDA and ISRIC. It reads BIF coordinates from `sites/MY_EC_SITE/<SITE>/forcing/raw*`. It also reads the surface file used by each existing case (`cases/<SITE>_*/CaseDocs/lnd_in` → `fsurdat`), to compare current and recommended values. SoilGrids is rate-limited to 5 requests a minute, so all 50 sites take about 15 minutes. Results are cached, so a rerun is quick and can be done with `--no-network`.

```bash
python3 -B scripts/01_collect_soil_texture_evidence.py --self-test
python3 -B scripts/01_collect_soil_texture_evidence.py --output-root $HOME/CLM_FATES_SOIL/AmeriFlux50_20261026
```

Outputs:

| File | Contents |
| --- | --- |
| `01_site_coordinates.csv` | Coordinates and where they came from |
| `02`–`05` | Raw source tables: BIF soil rows, ReESH samples, SSURGO horizons, SoilGrids profiles |
| `06_current_surface_layers.csv` | `PCT_SAND`, `PCT_CLAY` and `ORGANIC` in every surface file found |
| `07_clm10_candidates_by_source.csv` | Each source mapped onto the 10 CLM layers |
| `08_RECOMMENDED_CLM10_SOIL_TEXTURE_LONG.csv` | The recommended value for each layer, its source, and the change from the current surface |
| `09_..._WIDE.csv` | Ready-to-use `PCT_SAND_L1..L10` and `PCT_CLAY_L1..L10` |
| `10_RECOMMENDED_SITE_SUMMARY.csv` | Tier, top 0–30 cm texture class and flags |
| `metadata.json` | Provenance |

Useful options:
- `--coords SITE:LAT:LON` when a BIF file has no coordinates.
- `--surface SITE=/path/surfdata.nc` to compare against a specific surface file.
- `--priority` to change the source order.

## Caveats

- ReESH and literature samples cover roughly the top metre, from a few plots. Rock fragments are not represented in CLM.
- SSURGO uses the dominant component of a map unit, not the tower pit. SoilGrids is a 250 m prediction.
- Texture classes such as "sandy loam" are kept only as a check. They are never converted to numbers.
- BADM entries with no depth are assumed to cover 0–30 cm, and the output flags this.
- The UMBS (93/6/1) and Turkey Point TP74 (98/1/<1) values have no sampling depth; 0–50 cm is assumed.
