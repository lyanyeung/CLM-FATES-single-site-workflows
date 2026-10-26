# 50 AmeriFlux sites — recommended input soil texture for CLM-FATES, with evidence

26 October 2026. This combines two things:
- the IRIDIS6 [Stage01](scripts/01_collect_soil_texture_evidence.py) run for all 50 sites (ReESH, SSURGO, SoilGrids, literature, and the current surface files);
- the **full AmeriFlux BADM** (BIF xlsx) for all 50 sites, extracted by the operator with [Stage02](scripts/02_extract_full_badm_soil.py).

The per-site values are in [FINAL_RECOMMENDED_INPUT_SOIL_TEXTURE_50_SITES_20261026.csv](FINAL_RECOMMENDED_INPUT_SOIL_TEXTURE_50_SITES_20261026.csv). The method and the order of sources are described in the [folder README](README.md).

**Status:**
- Each value is a recommendation only. No surface file, case or job has been changed. Running cases keep their current gridded `PCT_SAND` / `PCT_CLAY`; this includes Lane A AD400 at CA-TP4, BR-Ma2, CA-Ca3 and CA-LP1.
- Using a new texture means a new surface variant, a new case and a new spin-up.
- The table gives the 0–30 cm value, which is the mean of CLM surface layers 1–5. All 10 layers are set by the per-layer rules. The exact 10-layer `PCT_SAND_L1..L10` / `PCT_CLAY_L1..L10` tables are written by a Stage01 rerun with `--badm-dir`; see "Next step" below.

## Summary

| Tier | Sites | Source |
| --- | ---: | --- |
| **T1 site measured** | **27** | 21 AmeriFlux ReESH plot datasets (Zenodo); 6 full-BADM `SOIL_TEX` profiles: CA-TP1, CA-TP3, CA-TP4, CA-Ca3, CA-Man, US-Wkg |
| **T1N neighbour measured** | **2** | US-Ho2 and US-Ho3 use US-Ho1 ReESH. The towers are 0.8–1.1 km apart, and BADM gives the same soil for all three ([proxy table](data/site_proxy_assignments_20261026.csv)) |
| T2 SSURGO point | 12 | USDA NRCS dominant component at the tower |
| T3 SoilGrids 250 m | 9 | ISRIC SoilGrids 2.0: BR-Ma2, CA-Cbo, CA-LP1, US-Bar (top layers), US-BZS, US-EML, US-Mpj, US-Rpf, US-Uaf |

## Recommended input per site

| Site | Batch | Tier | **Recommended input 0–30 cm: PCT_SAND / PCT_CLAY** | USDA class | Current surface | Basis and notes | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BR-Ma2 | 01 | T3 SoilGrids | **42.7 / 33.9** | clay loam | 52.2 / 36.2 | **Review:** BADM clay 65% at 0–10 cm (Luizão et al. 2004), but no sand reported. Baseline uses SoilGrids; clay-rich sensitivity recommended | BADM SOIL_TEX ×1, SoilGrids |
| CA-Ca3 | 01 | T1 BADM | **41.4 / 19.7** | loam | 67.4 / 6.0 | Full BADM loam 0–60 cm in 10 cm layers (Jassal, UBC); SoilGrids below 60 cm | BADM SOIL_TEX ×6, SoilGrids |
| CA-Cbo | 01 | T3 SoilGrids | **42.7 / 21.3** | loam | 39.8 / 15.8 | No BADM soil records | SoilGrids |
| CA-LP1 | 01 | T3 SoilGrids | **34.2 / 23.4** | loam | 53.0 / 16.0 | No BADM soil records; Lane A AD400 running on current grid soil | SoilGrids |
| CA-Man | 01 | T1 BADM | **1.8 / 90.2** | clay | 36.0 / 22.8 | Full BADM (BOREAS) A 0–11, B 11–38, C 38–74 cm: 87–95% clay; SoilGrids below; peaty gleysol with ~22 cm organic layers | BADM SOIL_TEX ×3, SoilGrids |
| CA-TP1 | 01 | T1 BADM | **98.0 / 0.0** | sand | 39.8 / 15.8 | Full BADM 98/2/0 (sieving), deep sand >3 m; whole profile | BADM SOIL_TEX ×1, SoilGrids |
| CA-TP3 | 01 | T1 BADM | **98.0 / 0.0** | sand | 39.8 / 15.8 | Full BADM 98/2/0 (site page 98/1/<1); whole profile | BADM SOIL_TEX ×1, SoilGrids |
| CA-TP4 | 01 | T1 BADM | **98.0 / 0.0** | sand | 39.8 / 15.8 | Full BADM 98/2/0, SOIL_DEPTH 300 cm; whole profile | BADM SOIL_TEX ×1, SoilGrids |
| US-Aud | 01 | T2 SSURGO | **32.4 / 34.0** | clay loam | 63.0 / 17.2 |  | SSURGO, SoilGrids |
| US-Bar | 01 | T3 SoilGrids | **61.0 / 7.6** | sandy loam | 54.8 / 5.8 | Top layers SoilGrids (matches NEON BART sandy loam); BADM C-layer 74/23/4 applied below 40 cm | BADM SOIL_TEX ×1, SoilGrids |
| US-BZS | 02 | T3 SoilGrids | **40.0 / 8.9** | silt loam | 23.6 / 26.2 | Boreal black spruce; review ORGANIC | SSURGO, SoilGrids |
| US-CMW | 02 | T2 SSURGO | **9.8 / 20.5** | silt loam | 63.0 / 17.2 |  | SSURGO, SoilGrids |
| US-EML | 02 | T3 SoilGrids | **38.2 / 11.8** | silt loam | 53.0 / 16.0 | Tundra, organic surface; review ORGANIC | SSURGO, SoilGrids |
| US-GLE | 02 | T1 measured ReESH | **17.5 / 17.4** | silt loam | 39.8 / 15.8 | ReESH silt loam vs survey ~46–48% sand; run survey-texture sensitivity | ReESH (Zenodo; record in Stage01 metadata.json), SSURGO, SoilGrids |
| US-Ha1 | 02 | T1 measured ReESH | **66.1 / 10.7** | sandy loam | 65.4 / 6.2 | ReESH used; BADM 66/29/6 agrees; organic-rich forest floor | [ReESH 15993458](https://doi.org/10.5281/zenodo.15993458), BADM SOIL_TEX ×1, SSURGO, SoilGrids |
| US-Ho1 | 02 | T1 measured ReESH | **58.4 / 10.9** | sandy loam | 65.4 / 6.2 |  | [ReESH 17344179](https://doi.org/10.5281/zenodo.17344179), BADM classification, SSURGO, SoilGrids |
| US-Ho2 | 02 | T1N Ho1 ReESH | **58.4 / 10.9** | sandy loam | 65.4 / 6.2 | Neighbour proxy: US-Ho1 ReESH (~0.8 km); BADM: upland soils fine sandy loams | BADM classification, SSURGO, SoilGrids |
| US-Ho3 | 02 | T1N Ho1 ReESH | **58.4 / 10.9** | sandy loam | 65.4 / 6.2 | Neighbour proxy: US-Ho1 ReESH (~1.1 km); same BADM soil description | BADM classification, SSURGO, SoilGrids |
| US-ICh | 02 | T2 SSURGO | **6.0 / 1.0** | silt | 53.0 / 16.0 | BADM: porous organic peat over silt and till; review ORGANIC | BADM classification, SSURGO, SoilGrids |
| US-ICt | 02 | T2 SSURGO | **6.0 / 1.0** | silt | 53.0 / 16.0 | BADM: porous organic peat over silt and till; review ORGANIC | BADM classification, SSURGO, SoilGrids |
| US-Kon | 03 | T2 SSURGO | **6.4 / 29.0** | silty clay loam | 15.8 / 28.0 | BADM: silty clay loam (agrees) | BADM classification, SSURGO, SoilGrids |
| US-Me2 | 03 | T1 measured ReESH | **62.7 / 9.7** | sandy loam | 38.0 / 22.8 | ReESH used; BADM 67/26/7 and TERRA-PNW profile agree | [ReESH 15994222](https://doi.org/10.5281/zenodo.15994222), BADM SOIL_TEX ×1, SSURGO, SoilGrids |
| US-Me6 | 03 | T1 measured ReESH | **69.8 / 6.9** | sandy loam | 38.0 / 22.8 | ReESH used; BADM 80/17/3 (2010, no depth) is sandier | [ReESH 15994479](https://doi.org/10.5281/zenodo.15994479), BADM SOIL_TEX ×1, SSURGO, SoilGrids |
| US-MMS | 03 | T1 measured ReESH | **2.4 / 21.7** | silt loam | 31.0 / 20.2 | ReESH silt loam (2% sand). BADM 34/3/63 has no depth and looks inconsistent (silt/clay possibly swapped); not used | [ReESH 15933402](https://doi.org/10.5281/zenodo.15933402), BADM SOIL_TEX ×1, SSURGO, SoilGrids |
| US-MOz | 03 | T1 measured ReESH | **2.0 / 26.2** | silt loam | 31.0 / 20.2 | ReESH used; BADM Weller silt loam A 0–38 cm 7.5/70/15, B 38–165 cm 10.5/60/34 agrees on class | ReESH (Zenodo; record in Stage01 metadata.json), BADM SOIL_TEX ×4, SSURGO, SoilGrids |
| US-Mpj | 03 | T3 SoilGrids | **35.9 / 22.2** | loam | 63.0 / 17.2 |  | SoilGrids |
| US-MtB | 03 | T2 SSURGO | **37.5 / 25.5** | loam | 63.0 / 17.2 |  | SSURGO, SoilGrids |
| US-NC2 | 03 | T1 measured ReESH | **66.8 / 11.3** | sandy loam | 55.6 / 16.6 | Histosol (BADM: terric Haplosaprists); review ORGANIC | [ReESH 17342476](https://doi.org/10.5281/zenodo.17342476), BADM classification, SSURGO, SoilGrids |
| US-NR1 | 03 | T1 measured ReESH | **57.2 / 16.8** | sandy loam | 38.2 / 24.2 | ReESH used; BADM: extremely rocky granite, ~10 cm organic layer | ReESH (Zenodo; record in Stage01 metadata.json), BADM classification, SSURGO, SoilGrids |
| US-NR3 | 03 | T1 measured ReESH | **63.0 / 10.8** | sandy loam | 38.2 / 24.2 |  | [ReESH 17555021](https://doi.org/10.5281/zenodo.17555021), SSURGO, SoilGrids |
| US-Rpf | 04 | T3 SoilGrids | **18.2 / 11.9** | silt loam | — | Boreal/permafrost; review ORGANIC | SSURGO, SoilGrids |
| US-Seg | 04 | T1 measured ReESH | **70.8 / 15.8** | sandy loam | — | ReESH used; BADM: loamy sand top 40 cm, sandy loam below | [ReESH 15996667](https://doi.org/10.5281/zenodo.15996667), BADM classification, SSURGO, SoilGrids |
| US-Ses | 04 | T2 SSURGO | **66.6 / 10.3** | sandy loam | — | BADM: sandy loam below 40 cm (agrees) | BADM classification, SSURGO, SoilGrids |
| US-Slt | 04 | T2 SSURGO | **91.5 / 3.5** | sand | — | BADM: sand ~95% of <2 mm fraction (agrees) | BADM SOIL_TEX ×8, SSURGO, SoilGrids |
| US-SP1 | 04 | T1 measured ReESH | **93.2 / 2.5** | sand | — | ReESH used; BADM 99/0/1 agrees (sandy Alaquod, argillic below 0.8 m) | ReESH (Zenodo; record in Stage01 metadata.json), BADM SOIL_TEX ×1, SSURGO, SoilGrids |
| US-SRG | 04 | T2 SSURGO | **66.0 / 11.0** | sandy loam | — |  | SSURGO, SoilGrids |
| US-SRM | 04 | T1 measured ReESH | **85.5 / 7.3** | loamy sand | — | ReESH used; BADM loamy sand, sand 72–87% / clay 6–15% (unpaired groups) agrees | [ReESH 15997288](https://doi.org/10.5281/zenodo.15997288), BADM SOIL_TEX ×10, SSURGO, SoilGrids |
| US-Syv | 04 | T1 measured ReESH | **61.2 / 10.1** | sandy loam | — | ReESH used; BADM 57/36/6 agrees | ReESH (Zenodo; record in Stage01 metadata.json), BADM SOIL_TEX ×1, SSURGO, SoilGrids |
| US-Ton | 04 | T1 measured ReESH | **20.9 / 23.0** | silt loam | — |  | [ReESH 16031874](https://doi.org/10.5281/zenodo.16031874), SSURGO, SoilGrids |
| US-Uaf | 04 | T3 SoilGrids | **17.8 / 12.3** | silt loam | — | Black spruce on permafrost; review ORGANIC | SSURGO, SoilGrids |
| US-UiD | 05 | T2 SSURGO | **8.0 / 22.0** | silt loam | — |  | SSURGO, SoilGrids |
| US-UMB | 05 | T1 measured ReESH | **93.9 / 3.3** | sand | — | ReESH used; BADM 92.6/6.8/0.6 agrees | [ReESH 16032019](https://doi.org/10.5281/zenodo.16032019), BADM SOIL_TEX ×1, SSURGO, SoilGrids |
| US-UMd | 05 | T1 measured ReESH | **91.1 / 5.1** | sand | — |  | ReESH (Zenodo; record in Stage01 metadata.json), BADM classification, SSURGO, SoilGrids |
| US-Var | 05 | T1 measured ReESH | **20.1 / 19.0** | silt loam | — |  | [ReESH 16032314](https://doi.org/10.5281/zenodo.16032314), SSURGO, SoilGrids |
| US-Vcm | 05 | T2 SSURGO | **70.0 / 7.0** | sandy loam | — |  | SSURGO, SoilGrids |
| US-Vcp | 05 | T1 measured ReESH | **41.9 / 21.1** | loam | — |  | ReESH (Zenodo; record in Stage01 metadata.json), SSURGO, SoilGrids |
| US-WCr | 05 | T1 measured ReESH | **58.1 / 15.3** | sandy loam | — | ReESH used; BADM 0–30 cm 54/33/13 (Cook et al. 2004) agrees | ReESH (Zenodo; record in Stage01 metadata.json), BADM SOIL_TEX ×2, SSURGO, SoilGrids |
| US-Whs | 05 | T2 SSURGO | **66.1 / 10.9** | sandy loam | — |  | SSURGO, SoilGrids |
| US-Wjs | 05 | T1 measured ReESH | **65.2 / 18.1** | sandy loam | — |  | [ReESH 16032863](https://doi.org/10.5281/zenodo.16032863), SSURGO, SoilGrids |
| US-Wkg | 05 | T1 BADM | **68.8 / 12.8** | sandy loam | — | Full BADM A 0–5 cm 67/16/17, B 5–147 cm 70/20/10 (SSURGO had clay loam 39/33) | BADM SOIL_TEX ×2, SSURGO, SoilGrids |


## What the full BADM contains (50 of 50 files read)

| Content | Sites |
| ---: | --- |
| 19 have numeric `SOIL_TEX` | BR-Ma2, CA-Ca3, CA-Man, CA-TP1, CA-TP3, CA-TP4, US-Bar, US-Ha1, US-MMS, US-MOz, US-Me2, US-Me6, US-SP1, US-SRM, US-Slt, US-Syv, US-UMB, US-WCr, US-Wkg |
| 11 have a soil classification or description only | US-Ho1, Ho2, Ho3, ICh, ICt, Kon, NC2, NR1, Seg, Ses, UMd |
| 2 have only soil chemistry | US-Ton, US-Var |
| 18 have no soil records | CA-Cbo, CA-LP1, US-Aud, BZS, CMW, EML, GLE, Mpj, MtB, NR3, Rpf, SRG, Uaf, UiD, Vcm, Vcp, Whs, Wjs |

Raw rows, groups and decisions are in [data/full_badm_50_20261026/](data/full_badm_50_20261026/).

How BADM records were treated:
- A BADM group **without a depth is never used automatically**. CA-TP1/3/4 and US-Bar were placed by hand, each with a written reason, in [badm_manual_depth_assignments](data/badm_manual_depth_assignments_20261026.csv).
- Where ReESH exists it takes priority over BADM. In every such case the BADM texture agrees on the texture class, except US-MMS: its BADM entry of 34/3/63 has no depth and looks internally inconsistent, so it is not used.
- The extraction files were produced by Stage02 at commit `f2c6e90`. The parser has since been improved:
  - the "Total" horizon no longer supplies a depth, so the US-UMB BADM entry is now unused (ReESH is used);
  - single-variable groups are merged, which gives US-MOz Weller A 0–38 cm and B 38–165 cm;
  - an overlapping deeper horizon now starts below the shallower one (US-Wkg B horizon from 5 cm).

  The table above already reflects these changes.

## Decisions and checks still needed

1. **BR-Ma2:** BADM supports more clay than SoilGrids (65% against 34%) but gives no sand. The baseline keeps SoilGrids; a clay-rich sensitivity run is recommended until a K34 sand value is found.
2. **Organic and permafrost sites** (US-NC2, US-ICh, US-ICt, US-EML, US-BZS, US-Rpf, US-Uaf, CA-Man, and the forest sites flagged `ORGANIC_RICH_TOPSOIL`): review `ORGANIC` as well as texture.
3. **US-GLE:** ReESH silt loam against surveys showing ~46–48% sand. Use ReESH and run a survey-texture sensitivity.
4. **Current surfaces with identical texture at distant sites.** These groups share exactly the same 0–30 cm values:
   - 53.0/16.0: CA-LP1, US-EML, US-ICh, US-ICt
   - 39.8/15.8: CA-Cbo, CA-TP1, CA-TP3, CA-TP4, US-GLE
   - 65.4/6.2: US-Ha1, US-Ho1, US-Ho2, US-Ho3
   - 63.0/17.2: US-Aud, US-CMW, US-Mpj, US-MtB

   Check each case's `fsurdat` (column `reference_surface` in the Stage01 summary) before building soil variants.

## Next step: exact 10-layer inputs

Copy the 50 BIF xlsx files to IRIDIS and rerun Stage01 with `--badm-dir` (cached sources make this fast). Outputs `08`/`09` then hold the final per-layer values, and `11` holds the BADM decisions. Building the soil-variant surfaces is a separate, later step.

## Sources

- AmeriFlux BADM, full site downloads `AMF_<SITE>_BIF_<date>.xlsx` (file names and dates in [A_badm_file_inventory.csv](data/full_badm_50_20261026/A_badm_file_inventory.csv)); BADM `SOIL_TEX` standard: https://ameriflux.lbl.gov/data/badm/badm-standards/SOIL_TEX
- AmeriFlux ReESH datasets on Zenodo (CC BY 4.0), records in [data/reesh_records_found_20261026.csv](data/reesh_records_found_20261026.csv) and in the Stage01 `metadata.json`
- USDA NRCS Soil Data Access (SSURGO); ISRIC SoilGrids 2.0 REST API
- Tower literature and site pages: [data/literature_soil_evidence_20261026.csv](data/literature_soil_evidence_20261026.csv)
- BADM-cited studies, including Luizão et al. 2004 (BR-Ma2), BOREAS TE soil data (CA-Man), Jassal/UBC Biomet (CA-Ca3), Cook et al. 2004 (US-WCr) and Humphreys et al. 2006 (CA-Ca3)
