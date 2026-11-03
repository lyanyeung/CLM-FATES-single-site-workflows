# OzFlux_JapanFlux_Soil — soil texture evidence and CLM-FATES recommendation for the 20 OzFlux / JapanFlux sites

Started 3 November 2026. This is the soil companion of [OzFlux_JapanFlux_PFT](../OzFlux_JapanFlux_PFT/). It uses the same layer rules as [Ameriflux_Soil](../Ameriflux_Site/Ameriflux_Soil/). **Nothing here changes a case, surface file, forcing file or running job.**

**Status, 3 Nov 2026: interim.** The literature search and SoilGrids are complete for all 20 sites. Two read-only steps are still open:
- [Stage02](scripts/02_source_metadata_soil_and_current_surface_READONLY.py) on IRIDIS6: soil records inside our own OzFlux L6 and JapanFlux packages (BIF, BADM), plus the soil in the current surface files.
- SLGA for the Australian sites, which needs a TERN API key.

Both can change the recommendation; see [Next steps](#next-steps).

The per-site recommendation and evidence are in [OZ_JP_SOIL_TEXTURE_20_SITES_20261103.md](OZ_JP_SOIL_TEXTURE_20_SITES_20261103.md).

## Which soil texture to use in CLM-FATES

CLM reads `PCT_SAND` and `PCT_CLAY` on 10 layers from the surface file. The node depths are 0.007, 0.028, 0.062, 0.119, 0.212, 0.366, 0.620, 1.04, 1.73 and 2.86 m, and silt is the remainder. `ORGANIC` (kg m⁻³ organic matter) mixes in organic-soil properties.

Sources are applied **layer by layer**, highest tier first:

| Tier | Source | Used for |
| --- | --- | --- |
| **T1 site measured** | Laboratory sand/silt/clay at the tower or its plots: papers, site pages, data portals | Every layer the samples cover |
| **T1N neighbour measured** | A measured profile on the same soil unit near the tower, with a written reason | Sites with no tower data but a clearly matching profile (AU-Gin) |
| **T2 SLGA 90 m** | TERN Soil and Landscape Grid of Australia v2, six depths to 2 m | Australian sites, below or instead of T1 |
| **T3 SoilGrids 250 m** | ISRIC SoilGrids 2.0, six depths to 2 m | All sites; the only gridded source for Japan |
| T4 keep surface | Current surface values | Only when nothing above exists |

Rules:
- Below the deepest covered depth, the profile that supplied the layer above is extended downward.
- The 0–30 cm value is the mean of layers 1–5.
- A record without a depth is never used automatically. Its application depth is set by hand, with a written reason, in [manual_depth_assignments](data/manual_depth_assignments_20261103.csv).
- **Texture classes are never converted to numbers.** Field textures, soil orders and narrative descriptions are only used to check the gridded values. Where they disagree, the site is flagged.
- **ORGANIC** candidates are reported but not applied. They are computed as SOC (g kg⁻¹) × bulk density (g cm⁻³) × 1.724.
- Changing soil makes a **new surface variant**, which needs a new case and a new spin-up.

### Particle-size schemes

CLM's pedotransfer functions expect USDA sand (50–2000 µm). Australian laboratories and most Japanese soil science use the international (ISSS) scheme: silt 2–20 µm, sand 20–2000 µm. Clay (< 2 µm) is the same in both. ISSS data are converted before use:

| Data available | Conversion |
| --- | --- |
| Fine sand (20–200 µm) reported | Log-linear interpolation inside 20–200 µm: USDA silt = ISSS silt + fine sand × ln(50/20)/ln(200/20) |
| Only total sand | Minasny & McBratney (2001), *Aust. J. Soil Res.* 39:1443 (1620 Australian samples, R² 0.823). Coefficients as reproduced in Hengl, *Predictive Soil Mapping with R*, §3.4.2: USDA silt = −18.3914 + 2.0971 S + 0.6726 Sa − 0.0142 S² − 0.0049 Sa², kept within [S, S + Sa] |

SLGA texture is ISSS, so it is converted with Minasny & McBratney. SoilGrids is already USDA.

A site value whose source does not state the scheme is used as reported. Its ISSS reading is kept as a sensitivity (column `usda_sand_if_ISSS` in [literature_usda_conversion](data/literature_usda_conversion_20261103.csv)).

## Result (interim)

| Tier | Sites |
| --- | ---: |
| T1 site measured | 2 (AU-ASM, AU-Cpr; both upper layers only) |
| T1N neighbour measured | 1 (AU-Gin) |
| T3 SoilGrids | 17 |

- **No measured texture at any JapanFlux tower.** The JapanFlux2024 paper (Ueyama et al. 2025, ESSD) says each site's dataset includes a BADM soil file. The online archive was unavailable during the search, but the packages on IRIDIS6 may contain it; Stage02 looks for it.
- **SoilGrids conflicts with the site descriptions** at AU-Stp (Vertosol, but less than 35 % clay), AU-Tum, AU-Dry, AU-Cpr below 41 cm, JP-Tef, JP-Yms and the two Tomakomai pumice sites. These sites are flagged rather than adjusted.

Files:

| File | Contents |
| --- | --- |
| [OZ_JP_RECOMMENDED_INPUT_SOIL_TEXTURE_20_SITES_20261103.csv](OZ_JP_RECOMMENDED_INPUT_SOIL_TEXTURE_20_SITES_20261103.csv) | Tier, 0–30 cm sand/clay, class, layer sources, flags |
| [OZ_JP_RECOMMENDED_CLM10_SOIL_TEXTURE_LONG_20261103.csv](OZ_JP_RECOMMENDED_CLM10_SOIL_TEXTURE_LONG_20261103.csv) | Per layer: value, source, ORGANIC candidate |
| [OZ_JP_RECOMMENDED_CLM10_SOIL_TEXTURE_WIDE_20261103.csv](OZ_JP_RECOMMENDED_CLM10_SOIL_TEXTURE_WIDE_20261103.csv) | `PCT_SAND_L1..L10`, `PCT_CLAY_L1..L10` |
| [data/literature_soil_evidence_20261103.csv](data/literature_soil_evidence_20261103.csv) | 149 evidence records: citation, locator, quote, verification, curation decision |
| [data/site_soil_decisions_20261103.csv](data/site_soil_decisions_20261103.csv) | Per-site source priority, basis and flags |
| [data/gridded/](data/gridded/) | SoilGrids at the towers: clay/sand/silt (mean, Q0.05, Q0.95), bulk density, SOC and coarse fragments at six depths, plus the 3 × 3-pixel range |
| [data/clm10_candidates_by_source_20261103.csv](data/clm10_candidates_by_source_20261103.csv) | Every source mapped onto the 10 layers |
| [data/OZ_JP_20_SITE_COORDINATES_20261103.csv](data/OZ_JP_20_SITE_COORDINATES_20261103.csv) | Coordinates and where they came from |

## Scripts

| Script | Where | What |
| --- | --- | --- |
| [01_gridded_soil_at_towers.py](scripts/01_gridded_soil_at_towers.py) | WSL or IRIDIS6 login node (internet; `rasterio`) | SoilGrids, and SLGA with `--tern-key-file`. The key is passed to GDAL and never printed. |
| [02_source_metadata_soil_and_current_surface_READONLY.py](scripts/02_source_metadata_soil_and_current_surface_READONLY.py) | IRIDIS6 (read only) | OzFlux L6 global attributes; JapanFlux BIF / BADM / README soil and LOCATION records (data members are never read); soil in every surface file found for the 20 sites |
| [03_build_clm10_soil_recommendation.py](scripts/03_build_clm10_soil_recommendation.py) | anywhere | Builds the tables above from the data files; `--current-surface` adds the Stage02 comparison |

Each script has `--self-test`.

## Next steps

1. **Run Stage02 on IRIDIS6.** It reports:
   - JapanFlux BADM soil files, which could give T1 values at the JapanFlux sites;
   - original BIF coordinates for the six JapanFlux sites whose coordinates came from the literature;
   - the current surface soil for the comparison column.
2. **SLGA for the nine Australian sites.** Get a free TERN API key (account.tern.org.au) and run Stage01 with `--sources SLGA --tern-key-file`. SLGA uses Australian site data and should be better than SoilGrids at AU-Stp, AU-Tum, AU-Dry and AU-Cpr.
3. **Papers that probably hold measured texture but could not be read** (paywalled or offline):
   - Hutley et al. 2011 AFM 151:1417 (all NATT towers);
   - Eamus et al. 2013 AFM 182–183:225 (AU-ASM);
   - Kelley 2002 PhD thesis (AU-How);
   - Koarashi et al. 2009 (JP-Api);
   - Ishizuka et al. 2006 (JP-Spp, JP-Api);
   - Jia & Akiyama 2005 (JP-Tak).
4. After that, rerun Stage03 and finalise. Building soil-variant surfaces is a separate, later step.
