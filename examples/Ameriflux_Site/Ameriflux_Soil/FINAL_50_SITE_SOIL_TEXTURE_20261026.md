# 50 AmeriFlux sites — soil texture for CLM-FATES, with evidence

26 October 2026. These are the recommended values from [Stage01](scripts/01_collect_soil_texture_evidence.py), run on IRIDIS6 for all 50 sites. Tower coordinates come from the BIF files; US-BZS coordinates come from the FLUXNET site page. The method and the order of sources are described in the [folder README](README.md). The per-site numbers are in [data/STAGE01_50_SITE_SOIL_TEXTURE_SUMMARY_20261026.csv](data/STAGE01_50_SITE_SOIL_TEXTURE_SUMMARY_20261026.csv).

**Status:**
- Each value is a **recommendation** only. No surface file, case or job has been changed.
- Running cases still use their current gridded `PCT_SAND` / `PCT_CLAY`. This includes Lane A AD400 at CA-TP4, BR-Ma2, CA-Ca3 and CA-LP1.
- Using a new texture means a new surface variant, a new case and a new spin-up.
- The full 10-layer tables (outputs `08` and `09`) are still on IRIDIS at `$HOME/CLM_FATES_SOIL/AmeriFlux50_20261026/`. They will be added here when copied over.

## Summary

| Tier | Sites | Meaning |
| --- | ---: | --- |
| T1 site measured | **22** | 21 have AmeriFlux ReESH plot samples on Zenodo: soil texture, organic matter, bulk density and hydraulic properties, sampled at ~0, ~10–15 and ~50–100 cm. CA-TP3 has a tower-site literature value. |
| T2 SSURGO point | **13** | USDA NRCS dominant soil component at the tower coordinates, by horizon |
| T3 SoilGrids 250 m | **15** | ISRIC SoilGrids 2.0: every Canadian and Brazilian site, plus US sites where SSURGO has no texture near the surface |

The "recommended 0–30 cm" value is the mean of CLM layers 1–5 (node depths 0.7–21 cm). The deeper layers follow the per-layer source rules: measured values to their sampled depth, then SSURGO or SoilGrids, then extended downward.

## Per-site recommendation and evidence

| Site | Batch | Tier | Recommended 0–30 cm sand / clay % | USDA class | Current surface 0–30 cm sand / clay % | Evidence available | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BR-Ma2 | 01 | T3 SoilGrids | **42.7 / 33.9** | clay loam | 52.2 / 36.2 | SoilGrids | **Review.** Literature: plateau soils very clayey yellow latosols (xanthic Ferralsol); 250 m SoilGrids may mix sandy valley soils. No tower numbers found. Lane A AD400 running on current grid soil |
| CA-Ca3 | 01 | T3 SoilGrids | **50.2 / 11.2** | loam | 67.4 / 6.0 | SoilGrids | Regional analogue: loamy-sand podzol on till (not tower-confirmed). Lane A AD400 running on current grid soil |
| CA-Cbo | 01 | T3 SoilGrids | **42.7 / 21.3** | loam | 39.8 / 15.8 | SoilGrids |  |
| CA-LP1 | 01 | T3 SoilGrids | **34.2 / 23.4** | loam | 53.0 / 16.0 | SoilGrids | Lane A AD400 running on current grid soil |
| CA-Man | 01 | T3 SoilGrids | **18.1 / 49.0** | clay | 36.0 / 22.8 | SoilGrids | Black spruce, moss/peat over clay; review ORGANIC |
| CA-TP1 | 01 | T3 SoilGrids | **41.6 / 23.5** | loam | 39.8 / 15.8 | SoilGrids | Literature: "former sandy agricultural field"; SoilGrids loam may underestimate sand |
| CA-TP3 | 01 | T1 measured | **98.0 / 1.0** | sand | 39.8 / 15.8 | [literature](https://hydromet.mcmaster.ca/?p=451), SoilGrids | Measured value has no sampling depth; 0–50 cm assumed, extended below |
| CA-TP4 | 01 | T3 SoilGrids | **71.6 / 11.5** | sandy loam | 39.8 / 15.8 | SoilGrids | **Decision needed.** TP3 tower is ~0.8 km away on the same sand plain, measured 98 / 1 / <1. Recommend TP3 measured as neighbour proxy (or as a sensitivity). Lane A AD400 running on current grid soil |
| US-Aud | 01 | T2 SSURGO | **32.4 / 34.0** | clay loam | 63.0 / 17.2 | SSURGO, SoilGrids |  |
| US-Bar | 01 | T3 SoilGrids | **61.0 / 7.6** | sandy loam | 54.8 / 5.8 | SoilGrids | NEON BART megapit: very fine sandy loam / sandy loam over loamy sand (consistent) |
| US-BZS | 02 | T3 SoilGrids | **40.0 / 8.9** | silt loam | 23.6 / 26.2 | SSURGO, SoilGrids | Coordinates from FLUXNET site page (BIF had none); boreal black spruce, review ORGANIC |
| US-CMW | 02 | T2 SSURGO | **9.8 / 20.5** | silt loam | 63.0 / 17.2 | SSURGO, SoilGrids |  |
| US-EML | 02 | T3 SoilGrids | **38.2 / 11.8** | silt loam | 53.0 / 16.0 | SSURGO, SoilGrids | Tundra, organic surface over mineral; SSURGO top horizons organic so SoilGrids used at top; review ORGANIC |
| US-GLE | 02 | T1 measured | **17.5 / 17.4** | silt loam | 39.8 / 15.8 | ReESH Zenodo (record in Stage01 metadata.json), SSURGO, SoilGrids | ReESH silt loam vs SSURGO/SoilGrids ~28–31 points more sand; use ReESH, run a survey-texture sensitivity |
| US-Ha1 | 02 | T1 measured | **66.1 / 10.7** | sandy loam | 65.4 / 6.2 | [ReESH Zenodo 15993458](https://doi.org/10.5281/zenodo.15993458), SSURGO, SoilGrids |  |
| US-Ho1 | 02 | T1 measured | **58.4 / 10.9** | sandy loam | 65.4 / 6.2 | [ReESH Zenodo 17344179](https://doi.org/10.5281/zenodo.17344179), SSURGO, SoilGrids |  |
| US-Ho2 | 02 | T3 SoilGrids | **38.5 / 14.3** | loam | 65.4 / 6.2 | SSURGO, SoilGrids | SSURGO top horizons organic so SoilGrids used near surface; ReESH exists for nearby US-Ho1 (58 / 11) |
| US-Ho3 | 02 | T3 SoilGrids | **40.2 / 11.4** | loam | 65.4 / 6.2 | SSURGO, SoilGrids | As US-Ho2; ReESH exists for nearby US-Ho1 |
| US-ICh | 02 | T2 SSURGO | **6.0 / 1.0** | silt | 53.0 / 16.0 | SSURGO, SoilGrids | Peat over silt loam, continuous permafrost; review ORGANIC |
| US-ICt | 02 | T2 SSURGO | **6.0 / 1.0** | silt | 53.0 / 16.0 | SSURGO, SoilGrids | Peat over silt loam, continuous permafrost; review ORGANIC |
| US-Kon | 03 | T2 SSURGO | **6.4 / 29.0** | silty clay loam | 15.8 / 28.0 | SSURGO, SoilGrids |  |
| US-Me2 | 03 | T1 measured | **62.7 / 9.7** | sandy loam | 38.0 / 22.8 | [ReESH Zenodo 15994222](https://doi.org/10.5281/zenodo.15994222), [literature](https://terraweb.forestry.oregonstate.edu/node/230), SSURGO, SoilGrids | ReESH and TERRA-PNW profile agree (sandy loam) |
| US-Me6 | 03 | T1 measured | **69.8 / 6.9** | sandy loam | 38.0 / 22.8 | [ReESH Zenodo 15994479](https://doi.org/10.5281/zenodo.15994479), SSURGO, SoilGrids |  |
| US-MMS | 03 | T1 measured | **2.4 / 21.7** | silt loam | 31.0 / 20.2 | [ReESH Zenodo 15933402](https://doi.org/10.5281/zenodo.15933402), SSURGO, SoilGrids | Very low sand (loess-derived silt loam); consistent with literature class |
| US-MOz | 03 | T1 measured | **2.0 / 26.2** | silt loam | 31.0 / 20.2 | ReESH Zenodo (record in Stage01 metadata.json), SSURGO, SoilGrids | Very low sand (silt loam); check against MOFLUX soil cores if needed |
| US-Mpj | 03 | T3 SoilGrids | **35.9 / 22.2** | loam | 63.0 / 17.2 | SoilGrids |  |
| US-MtB | 03 | T2 SSURGO | **37.5 / 25.5** | loam | 63.0 / 17.2 | SSURGO, SoilGrids |  |
| US-NC2 | 03 | T1 measured | **66.8 / 11.3** | sandy loam | 55.6 / 16.6 | [ReESH Zenodo 17342476](https://doi.org/10.5281/zenodo.17342476), SSURGO, SoilGrids | Histosol (Belhaven, ~25 cm organic over loamy sediment); ReESH mineral texture used; review ORGANIC |
| US-NR1 | 03 | T1 measured | **57.2 / 16.8** | sandy loam | 38.2 / 24.2 | ReESH Zenodo (record in Stage01 metadata.json), [literature](https://urquell.colorado.edu/data_ameriflux/data_supplemental/ReESHSummary_US_NR1.html), SSURGO, SoilGrids | ReESH used; SSURGO component differs strongly (+42 sand for ReESH) |
| US-NR3 | 03 | T1 measured | **63.0 / 10.8** | sandy loam | 38.2 / 24.2 | [ReESH Zenodo 17555021](https://doi.org/10.5281/zenodo.17555021), SSURGO, SoilGrids |  |
| US-Rpf | 04 | T3 SoilGrids | **18.2 / 11.9** | silt loam | no surface found | SSURGO, SoilGrids | Boreal/permafrost; review ORGANIC; no current surface found |
| US-Seg | 04 | T1 measured | **70.8 / 15.8** | sandy loam | no surface found | [ReESH Zenodo 15996667](https://doi.org/10.5281/zenodo.15996667), SSURGO, SoilGrids |  |
| US-Ses | 04 | T2 SSURGO | **66.6 / 10.3** | sandy loam | no surface found | SSURGO, SoilGrids |  |
| US-Slt | 04 | T2 SSURGO | **91.5 / 3.5** | sand | no surface found | SSURGO, SoilGrids |  |
| US-SP1 | 04 | T1 measured | **93.2 / 2.5** | sand | no surface found | ReESH Zenodo (record in Stage01 metadata.json), SSURGO, SoilGrids |  |
| US-SRG | 04 | T2 SSURGO | **66.0 / 11.0** | sandy loam | no surface found | SSURGO, SoilGrids |  |
| US-SRM | 04 | T1 measured | **85.5 / 7.3** | loamy sand | no surface found | [ReESH Zenodo 15997288](https://doi.org/10.5281/zenodo.15997288), SSURGO, SoilGrids | ReESH much sandier than SoilGrids (+32); ReESH used |
| US-Syv | 04 | T1 measured | **61.2 / 10.1** | sandy loam | no surface found | ReESH Zenodo (record in Stage01 metadata.json), [literature](https://co2.aos.wisc.edu/data/cheas/ancillary/us-syv/soil_properties/ReESHsummary_US-Syv.html), SSURGO, SoilGrids |  |
| US-Ton | 04 | T1 measured | **20.9 / 23.0** | silt loam | no surface found | [ReESH Zenodo 16031874](https://doi.org/10.5281/zenodo.16031874), SSURGO, SoilGrids |  |
| US-Uaf | 04 | T3 SoilGrids | **17.8 / 12.3** | silt loam | no surface found | SSURGO, SoilGrids | Black spruce on permafrost; review ORGANIC; no current surface found |
| US-UiD | 05 | T2 SSURGO | **8.0 / 22.0** | silt loam | no surface found | SSURGO, SoilGrids |  |
| US-UMB | 05 | T1 measured | **93.9 / 3.3** | sand | no surface found | [ReESH Zenodo 16032019](https://doi.org/10.5281/zenodo.16032019), [literature](https://flux.org.ohio-state.edu/site-description-umbs/), SSURGO, SoilGrids | ReESH much sandier than SoilGrids (+32); ReESH used |
| US-UMd | 05 | T1 measured | **91.1 / 5.1** | sand | no surface found | ReESH Zenodo (record in Stage01 metadata.json), SSURGO, SoilGrids | ReESH much sandier than SoilGrids (+34); ReESH used |
| US-Var | 05 | T1 measured | **20.1 / 19.0** | silt loam | no surface found | [ReESH Zenodo 16032314](https://doi.org/10.5281/zenodo.16032314), SSURGO, SoilGrids |  |
| US-Vcm | 05 | T2 SSURGO | **70.0 / 7.0** | sandy loam | no surface found | SSURGO, SoilGrids |  |
| US-Vcp | 05 | T1 measured | **41.9 / 21.1** | loam | no surface found | ReESH Zenodo (record in Stage01 metadata.json), SSURGO, SoilGrids |  |
| US-WCr | 05 | T1 measured | **58.1 / 15.3** | sandy loam | no surface found | ReESH Zenodo (record in Stage01 metadata.json), [literature](https://co2.aos.wisc.edu/data/cheas/ancillary/us-wcr/soil_properties/ReESHsummary_US-WCr.html), SSURGO, SoilGrids | Consistent with tower soil pit (sandy loam / loamy sand) |
| US-Whs | 05 | T2 SSURGO | **66.1 / 10.9** | sandy loam | no surface found | SSURGO, SoilGrids |  |
| US-Wjs | 05 | T1 measured | **65.2 / 18.1** | sandy loam | no surface found | [ReESH Zenodo 16032863](https://doi.org/10.5281/zenodo.16032863), SSURGO, SoilGrids |  |
| US-Wkg | 05 | T2 SSURGO | **39.0 / 33.1** | clay loam | no surface found | SSURGO, SoilGrids |  |

## Decisions and checks still needed

1. **CA-TP4:** choose between SoilGrids (71.6 / 11.5) and the CA-TP3 measurement from ~0.8 km away (98 / 1). This applies only to a future soil variant; the running AD400 is not touched.
2. **BR-Ma2:** SoilGrids gives 42.7 / 33.9. The literature describes the K34 plateau soils as very clayey. A tower particle-size measurement is needed before a clay value higher than SoilGrids is used.
3. **Organic and permafrost sites** (US-NC2, US-ICh, US-ICt, US-EML, US-BZS, US-Rpf, US-Uaf, CA-Man, and the forest sites flagged `ORGANIC_RICH_TOPSOIL`): texture alone does not describe these soils. Stage01 reports organic-density candidates; `ORGANIC` should be reviewed as well.
4. **Current surfaces with identical texture at distant sites.** Stage01 found these groups sharing exactly the same 0–30 cm values:
- CA-LP1, US-EML, US-ICh, US-ICt: 53.0/16.0
- CA-Cbo, CA-TP1, CA-TP3, CA-TP4, US-GLE: 39.8/15.8
- US-Ha1, US-Ho1, US-Ho2, US-Ho3: 65.4/6.2
- US-Aud, US-CMW, US-Mpj, US-MtB: 63.0/17.2

   This can happen through the CTSM soil-map-unit lookup, but it can also mean that a case's `fsurdat` points to another site's or a template's surface file. Check the `reference_surface` column of `10_RECOMMENDED_SITE_SUMMARY.csv` before changing any soil.
5. **Batch04/05 sites** (US-Rpf onward) have no surface file yet, so no current-versus-recommended comparison exists.

## Sources

- AmeriFlux ReESH datasets on Zenodo (CC BY 4.0), record list in [data/reesh_records_found_20261026.csv](data/reesh_records_found_20261026.csv). Stage01 queried Zenodo for every site and verified MD5 checksums on download.
- USDA NRCS Soil Data Access (SSURGO): `SDA_Get_Mukey_from_intersection_with_WktWgs84`, dominant component horizons.
- ISRIC SoilGrids 2.0 REST API, mean values at 0–5, 5–15, 15–30, 30–60, 60–100 and 100–200 cm.
- Tower literature and site pages, with URLs, in [data/literature_soil_evidence_20261026.csv](data/literature_soil_evidence_20261026.csv). These include TERRA-PNW US-Me2, OSU UMBS, McMaster Turkey Point, CHEAS Willow Creek, NEON BART, Minick et al. (2019) for US-NC2, UAF Imnavait, and the Santa Rita soils report.
