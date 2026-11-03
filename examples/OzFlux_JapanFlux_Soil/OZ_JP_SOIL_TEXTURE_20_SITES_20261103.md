# 20 OzFlux / JapanFlux sites — recommended input soil texture for CLM-FATES, with evidence (interim)

3 November 2026. The method is in the [folder README](README.md).

**Status:**
- Each value is a recommendation only. No surface, case or job has been changed.
- The values are interim until two read-only steps are done:
  - IRIDIS6 Stage02, which reads the JapanFlux BADM soil files, the BIF coordinates and the current surface soil;
  - SLGA for the Australian sites.
- Values are USDA sand / clay in %. The 0–30 cm value is the mean of CLM layers 1–5. Exact per-layer values are in the [LONG](OZ_JP_RECOMMENDED_CLM10_SOIL_TEXTURE_LONG_20261103.csv) and [WIDE](OZ_JP_RECOMMENDED_CLM10_SOIL_TEXTURE_WIDE_20261103.csv) tables.

## Recommended input per site

| Site | Tier | **0–30 cm sand / clay** | Class | 30–150 cm (L6–8) | Below 150 cm (L9–10) | Basis | Flags |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AU-ASM | T1 | **74.0 / 15.0** | sandy loam | 72.9 / 18.0 | 70.6 / 23.9 | Tower value 74:11:15 applied 0–100 cm; SoilGrids below | scheme unstated (ISSS reading 59 / 15); hardpan ~1 m |
| AU-Cow | T3 | **38.6 / 32.7** | clay loam | 36.4 / 35.3 | 35.3 / 35.9 | SoilGrids; matches "clay loam" | ORGANIC |
| AU-Cpr | T1 | **94.0 / 2.0** | sand | 75.3 / 16.9 | 65.7 / 24.3 | Sun et al. 2015 0–30 cm applied 0–41 cm; SoilGrids below | grid heavier than pit below 41 cm; scheme unstated (ISSS reading 88 / 2) |
| AU-DaS | T3 | **87.9 / 8.8** | loamy sand | 73.7 / 23.4 | 72.4 / 24.6 | SoilGrids; matches "deep sandy loams" | |
| AU-Dry | T3 | **64.6 / 26.2** | sandy clay loam | 52.6 / 40.2 | 51.9 / 41.1 | SoilGrids | grid heavier than "sandy loam" 0–20 cm |
| AU-Gin | T1N | **97.9 / 1.0** | sand | 98.9 / 0.7 | 98.9 / 0.7 | Bassendean reference profile 5 km ESE, pipette, to 5 m | neighbour profile |
| AU-How | T3 | **62.2 / 20.1** | sandy clay loam | 57.7 / 24.2 | 56.2 / 25.4 | SoilGrids; matches sandy loam A / sandy clay loam B | laterite ~1.2 m |
| AU-Stp | T3 | **53.0 / 32.3** | sandy clay loam | 48.2 / 38.5 | 48.4 / 38.3 | SoilGrids | **REVIEW:** Vertosol needs ≥ 35 % clay |
| AU-Tum | T3 | **53.7 / 20.3** | sandy clay loam | 51.7 / 19.8 | 52.1 / 18.5 | SoilGrids | **REVIEW:** field clay loam / light clay; ORGANIC |
| JP-Api | T3 | **42.4 / 25.6** | loam | 44.3 / 25.1 | 45.2 / 24.7 | SoilGrids | Andosol; ORGANIC |
| JP-Fhk | T3 | **38.2 / 28.0** | clay loam | 38.8 / 27.8 | 39.8 / 27.7 | SoilGrids | coarse volcanic ash / scoria; ORGANIC |
| JP-Fjy | T3 | **41.0 / 27.7** | clay loam | 42.7 / 26.0 | 43.2 / 26.1 | SoilGrids | **lava, almost no soil**; ORGANIC |
| JP-Khw | T3 | **34.8 / 31.5** | clay loam | 33.0 / 38.0 | 33.6 / 37.9 | SoilGrids | ORGANIC |
| JP-Spp | T3 | **40.0 / 24.1** | loam | 41.0 / 26.5 | 40.9 / 28.1 | SoilGrids; matches "Loam" | Andosol; ORGANIC |
| JP-Tak | T3 | **36.8 / 32.3** | clay loam | 41.1 / 27.2 | 42.3 / 26.2 | SoilGrids | Andosol vs Cambisol; ORGANIC |
| JP-Tef | T3 | **42.3 / 24.2** | loam | 43.2 / 26.4 | 44.6 / 25.3 | SoilGrids | **REVIEW:** nearby profiles clay-rich; ORGANIC |
| JP-Tgf | T3 | **51.5 / 15.7** | loam | 53.6 / 16.6 | 55.3 / 16.8 | SoilGrids | Kuroboku Andosol; ORGANIC |
| JP-Tmd | T3 | **46.5 / 15.9** | loam | 49.4 / 17.8 | 48.1 / 18.1 | SoilGrids | **REVIEW:** Tarumae pumice; ORGANIC |
| JP-Tom | T3 | **46.1 / 18.6** | loam | 46.8 / 18.5 | 45.7 / 18.3 | SoilGrids | **REVIEW:** Tarumae pumice; ORGANIC |
| JP-Yms | T3 | **35.5 / 26.8** | loam | 33.8 / 30.3 | 34.2 / 29.9 | SoilGrids | **REVIEW:** granite regosol, sandy; ORGANIC |

`ORGANIC` means the SoilGrids organic-matter candidate exceeds 100 kg m⁻³ in the top layers (SOC × bulk density × 1.724; CLM saturates at 130). It is reported and not applied. The candidates are in the LONG table.

**Current surface.** Only AU-ASM is known so far. Its CTSM-2000 point reference is sand 89–90 / clay 6–7 in all 10 layers, much sandier than both the tower value and SoilGrids. Stage02 adds the other 19 sites.

## Evidence by site

The full records, each with citation, locator, short quote and verification level, are in [literature_soil_evidence_20261103.csv](data/literature_soil_evidence_20261103.csv).

### OzFlux

**AU-ASM, Alice Springs Mulga.**
- *Texture.* Red Kandosol, "74:11:15 sand:silt:clay" in three sources:
  - the TERN flux-collection record;
  - Chen et al. 2014, *J. Hydrol.* 519:1084;
  - Rumman et al. 2018, *HESS* 22:4875, which cites Eamus et al. 2013 *AFM* 182–183:225 (not read).
- No source gives a depth, method or scheme.
- *Profile.* Unconsolidated loamy sand above a siliceous hardpan at about 1 m (Eamus et al. 2016 *ERL* 11:125011); water table 49 m.
- *Rejected.* The OzFlux page's "50:50 sand:clay" is unsourced.
- *Gridded.* SoilGrids 0–100 cm (71–77 / 18–24) agrees within about 5 points.

**AU-Cow, Cow Bay.**
- Acidic, dystrophic brown Dermosol (TERN).
- "Red clay loam podzolic soils" on the OzFlux page; the same sentence appears on the Cape Tribulation page.
- No measurements.

**AU-Cpr, Calperum.**
- *Measured.* Sun et al. 2015, *Biogeosciences* 12:5093, §2.1: "2 % clay, 4 % silt and 94 % sand", bulk density 1.6 g cm⁻³ at 0–30 cm, Tenosol. Sampling points are about 0.1 and 1.3 km from the tower.
- *Tower pit* (University of Adelaide, 2012), field textures and ring bulk density:

  | Depth (cm) | Field texture | Bulk density (g cm⁻³) |
  | --- | --- | --- |
  | 0–41 | loamy sand | 1.67–1.68 |
  | 41–66 | clayey sand | 1.71 |
  | 66–140 | clayey fine sand, calcareous | 1.66 |

**AU-DaS, Daly River Uncleared.**
- Red Kandosol of the Blain soil type, "deep, sandy-loams" (Bristow et al. 2016).
- Nearby plots: bulk density 1.44 g cm⁻³ and carbon 0.56 % at 0–10 cm (Grover et al. 2012).

**AU-Dry, Dry River.**
- No site measurement.
- Nijzink et al. 2022 model input: sandy loam at 0–20 cm (field), heavier below.

**AU-Gin, Gingin.**
- *Tower.* Medium Bassendean sands with discontinuous coffee-rock (Podosol) layers (2025 *ERL*); field capacity 8–10 %.
- *Neighbour profile.* Turner & Laliberté 2020, *J. R. Soc. West. Aust.* 103, Appendix Table 1: a profile 5 km ESE on the same dune sand, pipette method.
  - Sand 97.2–99.3 % and clay 0.6–1.3 % from the surface to 5 m.
  - Bulk density 1.31–1.46 g cm⁻³.

**AU-How, Howard Springs.**
- *Profile.* Red Kandosol: sandy loam A, sandy clay loam B, weathered laterite below about 1.2 m (Schymanski et al. 2008, citing Kelley 2002).
- *Bulk density.* 1.42 g cm⁻³ at 5 cm to 1.7 at 1 m (Chen et al. 2003).
- *Not used.*
  - The UWA LEAP page value (58 / 38 / 4 "by volume", no depth) is probably laser data.
  - The Shi et al. 2025 values are class lookups.

**AU-Stp, Sturt Plains.**
- *Soil.* Grey cracking-clay Vertosol, "silty clay" (Nijzink et al. 2022).
- *Not used.*
  - The UWA LEAP laser value (34 / 51 / 14 "by volume", no depth) has implausibly low clay for a Vertosol.
  - The Whitley et al. 2016 values come from the soil atlas and are identical to its Daly River values.

**AU-Tum, Tumbarumba.**
- *Profile on granodiorite* (CEOP station page):

  | Depth (cm) | Field texture |
  | --- | --- |
  | 2–8 | clay loam |
  | 8–40 | light clay |
  | 40–162 | clay loam |
  | 162–242 | sandy clay loam |

- *Classification conflict.* Redoxic Hydrosol (TERN) versus red Dermosol 3–4 m deep (COSMOS). Both come from search snippets only.

### JapanFlux

No source gives measured sand / silt / clay at any JapanFlux tower.

- **JP-Api:** Andosol / moderately moist brown forest soil BD(d) (FFPRI); about 11 kg C m⁻² in the top 20 cm (Koarashi et al. 2025).
- **JP-Fhk:** coarse-grained volcanic ash of Mt Fuji (NIES, AsiaFlux).
- **JP-Fjy:** immature soil on the AD 937 Kenmarubi lava, "almost no soil layer apart from litter" (FFPRI). Texture matters less here than soil depth; a shallow `zbedrock` is the relevant choice.
- **JP-Khw:** moderately moist brown forest soil BD on crystal schist (FFPRI).
- **JP-Spp:** moderately moist black soil Bl D / Andosol on volcanic ash (FFPRI; Yamanoi et al. 2015); "Loam" (AsiaFlux); 18.0 kg C m⁻².
- **JP-Tak:** sources disagree.
  - Dystric Cambisol (AsiaFlux).
  - Kuroboku / Andosol (ICOS station page; Ohtsuka 2012), with more than 300 t C ha⁻¹ to 1 m.
- **JP-Tef:**
  - *Tower.* Gleyic Cambisol on Cretaceous sedimentary rock.
  - *Nearby profiles.* Hokkaido University FRED profiles in Teshio Experimental Forest are silty clay to light clay at the surface and heavy clay below. Their bulk density is 0.23–0.46 g cm⁻³ in A horizons.
- **JP-Tgf:** Kuroboku (humic Andosol) in Kanto Loam over Joso clay; organic carbon 4.9 % at 0–20 cm (Suh et al. 2009).
- **JP-Tmd:** volcanogenous regosol, an A horizon of about 10 cm over Tarumae pumice.
- **JP-Tom:**
  - *Tower.* Volcanogenous regosol.
  - *Nearby profiles.* FRED profiles have a sandy loam A horizon of 4.5–10 cm over pumice gravel and a buried sand layer, to 55–72+ cm.
- **JP-Yms:** Regosol on weathered granite, "sandy loam or loamy sand" with 53 % fine granitic gravel by weight (Kominami et al. 2008); soil depth about 47 cm (snippet).

Coordinates for JP-Api, JP-Fhk, JP-Spp, JP-Tak, JP-Tgf and JP-Tom come from the JapanFlux2024 paper (Table 1). Stage02 checks them against the original BIF / BADM.

## Decisions still needed

1. **AU-Stp, AU-Tum, AU-Dry, AU-Cpr (below 41 cm):**
   - Use SLGA if a TERN key is available.
   - Otherwise keep SoilGrids and run a heavier-texture sensitivity.
2. **JP-Tef, JP-Yms, JP-Tmd, JP-Tom:**
   - SoilGrids contradicts the site descriptions.
   - Wait for the Stage02 BADM result before choosing.
3. **ORGANIC:** decide whether to apply site or SoilGrids organic matter at the Andosol and forest sites (most JapanFlux sites, AU-Tum and AU-Cow).
4. **Shallow soils:**
   - JP-Fjy (lava);
   - AU-ASM (hardpan ~1 m);
   - AU-How (laterite ~1.2 m);
   - JP-Yms (~47 cm).

   For these sites, decide whether to set `zbedrock`, which is separate from texture.
