# 20 OzFlux / JapanFlux sites — recommended input soil texture for CLM-FATES, with evidence

3 November 2026, recommendation v1. The method is in the [folder README](README.md).

**Status:**
- Each value is a recommendation only. No surface, case or job has been changed.
- Sources searched:
  - the literature and site pages;
  - SoilGrids at all 20 towers;
  - our own source files on IRIDIS6 (Stage02): OzFlux L6 attributes and JapanFlux BIF / BADM;
  - the current OzFlux surface files.
- SLGA (Australia) is still open; it needs a TERN API key.
- Values are USDA sand / clay in %. The 0–30 cm value is the mean of CLM layers 1–5. Exact per-layer values are in the [LONG](OZ_JP_RECOMMENDED_CLM10_SOIL_TEXTURE_LONG_20261103.csv) and [WIDE](OZ_JP_RECOMMENDED_CLM10_SOIL_TEXTURE_WIDE_20261103.csv) tables.

## Recommended input per site

| Site | Tier | **0–30 cm sand / clay** | Class | 30–150 cm (L6–8) | Below 150 cm (L9–10) | Current surface 0–30 cm | Basis | Flags |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AU-ASM | T1 | **74.0 / 15.0** | sandy loam | 72.9 / 18.0 | 70.6 / 23.9 | 89.8 / 6.2 | Tower value 74:11:15 applied 0–100 cm; SoilGrids below | scheme unstated (ISSS reading 59 / 15); hardpan ~1 m |
| AU-Cow | T3 | **38.6 / 32.7** | clay loam | 36.4 / 35.3 | 35.3 / 35.9 | 86.2 / 4.0 | SoilGrids; matches "clay loam" | current surface contradicts site; ORGANIC |
| AU-Cpr | T1 | **94.0 / 2.0** | sand | 75.3 / 16.9 | 65.7 / 24.3 | 48.4 / 18.6 | Sun et al. 2015 0–30 cm applied 0–41 cm; SoilGrids below | grid heavier than pit below 41 cm; scheme unstated (ISSS reading 88 / 2) |
| AU-DaS | T3 | **87.9 / 8.8** | loamy sand | 73.7 / 23.4 | 72.4 / 24.6 | 63.0 / 17.2 | SoilGrids; matches "deep sandy loams" | |
| AU-Dry | T3 | **64.6 / 26.2** | sandy clay loam | 52.6 / 40.2 | 51.9 / 41.1 | 63.0 / 17.2 | SoilGrids | topsoil heavier than field "sandy loam"; current surface is the alternative |
| AU-Gin | T1N | **97.9 / 1.0** | sand | 98.9 / 0.7 | 98.9 / 0.7 | 36.2 / 31.2 | Bassendean reference profile 5 km ESE, pipette, to 5 m | current surface contradicts site |
| AU-How | T3 | **62.2 / 20.1** | sandy clay loam | 57.7 / 24.2 | 56.2 / 25.4 | 56.8 / 17.8 | SoilGrids; matches sandy loam A / sandy clay loam B | laterite ~1.2 m |
| AU-Stp | **T4 keep** | **19.6 / 54.4** | clay | 18.3 / 55.0 | 19.0 / 51.0 | same | Vertosol (≥ 35 % clay): only the current surface qualifies | L6 soil string conflict |
| AU-Tum | **T4 keep** | **48.4 / 21.0** | loam | 39.3 / 33.7 | 53.0 / 28.0 | same | Alfisol / clay loam B: only the current surface has the clay increase | ORGANIC (SoilGrids much higher) |
| JP-Api | T3 | **42.4 / 25.6** | loam | 44.3 / 25.1 | 45.2 / 24.7 | no case yet | SoilGrids | Andosol; ORGANIC |
| JP-Fhk | T3 | **38.2 / 28.0** | clay loam | 38.8 / 27.8 | 39.8 / 27.7 | no case yet | SoilGrids | coarse volcanic ash / scoria; ORGANIC |
| JP-Fjy | T3 | **41.0 / 27.7** | clay loam | 42.7 / 26.0 | 43.2 / 26.1 | no case yet | SoilGrids | **lava, almost no soil**; ORGANIC |
| JP-Khw | T3 | **34.8 / 31.5** | clay loam | 33.0 / 38.0 | 33.6 / 37.9 | no case yet | SoilGrids | ORGANIC |
| JP-Spp | T3 | **40.0 / 24.1** | loam | 41.0 / 26.5 | 40.9 / 28.1 | no case yet | SoilGrids; matches "Loam" | Andosol; ORGANIC |
| JP-Tak | T3 | **36.8 / 32.3** | clay loam | 41.1 / 27.2 | 42.3 / 26.2 | no case yet | SoilGrids | Andosol (site BIF); ORGANIC |
| JP-Tef | T3 | **42.3 / 24.2** | loam | 43.2 / 26.4 | 44.6 / 25.3 | no case yet | SoilGrids | **REVIEW:** nearby profiles clay-rich; ORGANIC |
| JP-Tgf | T3 | **51.5 / 15.7** | loam | 53.6 / 16.6 | 55.3 / 16.8 | no case yet | SoilGrids | Andosol (BADM); ORGANIC |
| JP-Tmd | T3 | **46.5 / 15.9** | loam | 49.4 / 17.8 | 48.1 / 18.1 | no case yet | SoilGrids | **REVIEW:** Tarumae pumice; ORGANIC |
| JP-Tom | T3 | **46.1 / 18.6** | loam | 46.8 / 18.5 | 45.7 / 18.3 | no case yet | SoilGrids | **REVIEW:** Tarumae pumice (BADM Regosol); ORGANIC |
| JP-Yms | T3 | **35.5 / 26.8** | loam | 33.8 / 30.3 | 34.2 / 29.9 | no case yet | SoilGrids | **REVIEW:** granite regosol, sandy; ORGANIC |

**Tier counts:**
- T1 site measured: 2 (upper layers only).
- T1N neighbour measured: 1.
- T4 keep the current surface: 2.
- T3 SoilGrids: 15.

`ORGANIC` means the SoilGrids organic-matter candidate exceeds 100 kg m⁻³ in the top layers (SOC × bulk density × 1.724; CLM saturates at 130). It is reported and not applied.

**Current surface.** These are the CTSM-2000 point references inside the OzFlux FIXNC candidate surfaces. They are written in [current_surface_soil_layers_OzFlux_20261103.tsv](data/current_surface_soil_layers_OzFlux_20261103.tsv); sand and clay are whole numbers in these files.
- *Far from the site evidence:*
  - AU-Gin: 36 / 31 against about 98 / 1;
  - AU-Cow: 86 / 4, a sand, at a clay loam rainforest;
  - AU-ASM: 90 / 6 against 74 / 15.
- *Identical at two towers 120 km apart:* AU-DaS and AU-Dry.
- No JapanFlux case exists yet, so there is nothing to compare there.

## How the T4 sites were decided

The rule is unchanged: texture classes are never converted to numbers. At AU-Stp and AU-Tum, however, the site's soil order rules out SoilGrids. The current surface is the gridded profile that satisfies the class, so it is kept, which also means no change to the soil.

- **AU-Stp.**
  - A Vertosol has at least 35 % clay throughout. The current surface has 51–56 % at every layer; SoilGrids has 31–39 %.
  - Sources: Nijzink et al. 2022 ("silty clay", grey Vertisol), Whitley et al. 2016 (grey Vertosol), and the Mitchell grass (*Astrebla*) cover, which grows on cracking clays.
  - The OzFlux L6 attribute says "red kandasol". The same string appears in the L6 files of AU-DaS, AU-Dry and AU-How, so it is read as a template copy and not used.
- **AU-Tum.**
  - The L6 attribute is "Alfisol", a soil order defined by a clay-enriched B horizon. The CEOP tower profile has clay loam and light clay horizons over granodiorite.
  - The current surface rises from 20 % clay at 0–30 cm to 32–35 % at 37–104 cm. SoilGrids stays near 20 % at every depth.

If SLGA is obtained, it is checked against the same classes and takes precedence where it agrees.

## Evidence by site

The full records, each with citation, locator, short quote and verification level, are in [literature_soil_evidence_20261103.csv](data/literature_soil_evidence_20261103.csv) (165 rows). Records read from our own source files are marked `SOURCE_FILE_READ`.

### OzFlux

Every L6 file has a `soil` global attribute. These are descriptions only, with no numbers:

| Site | L6 `soil` | Agrees with |
| --- | --- | --- |
| AU-ASM | "red kandosol, sandy loam" | 74 / 15 (a sandy loam) |
| AU-Cow | "red clay loam podzolic soils" | SoilGrids clay loam |
| AU-Cpr | the tower pit A1 description, "loamy sand" | Sun et al. 94 / 2 |
| AU-DaS, AU-Dry, AU-How, AU-Stp | "red kandasol" (identical) | — |
| AU-Gin | "Podosol, Gutless sand" | the neighbour profile |
| AU-Tum | "Alfisol" | the current surface |

**AU-ASM, Alice Springs Mulga.**
- *Texture.* Red Kandosol, "74:11:15 sand:silt:clay" in three sources:
  - the TERN flux-collection record;
  - Chen et al. 2014, *J. Hydrol.* 519:1084;
  - Rumman et al. 2018, *HESS* 22:4875, which cites Eamus et al. 2013 *AFM* 182–183:225 (not read).
- No source gives a depth, method or scheme.
- *Profile.* Unconsolidated loamy sand above a siliceous hardpan at about 1 m (Eamus et al. 2016 *ERL* 11:125011); water table 49 m.
- *Rejected.* The OzFlux page's "50:50 sand:clay" is unsourced.

**AU-Cow, Cow Bay.** Acidic, dystrophic brown Dermosol (TERN). No measurements.

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
- *Neighbour profile.* Turner & Laliberté 2020, *J. R. Soc. West. Aust.* 103, Appendix Table 1, about 5 km ESE on the same dune sand, pipette method.
  - Sand 97.2–99.3 % and clay 0.6–1.3 % from the surface to 5 m.
  - Bulk density 1.31–1.46 g cm⁻³.

**AU-How, Howard Springs.**
- *Profile.* Red Kandosol: sandy loam A, sandy clay loam B, weathered laterite below about 1.2 m (Schymanski et al. 2008, citing Kelley 2002).
- *Bulk density.* 1.42 g cm⁻³ at 5 cm to 1.7 at 1 m (Chen et al. 2003).
- *Not used.*
  - The UWA LEAP page value (58 / 38 / 4 "by volume", no depth).
  - The Shi et al. 2025 class lookups.

**AU-Stp, Sturt Plains.** See *How the T4 sites were decided*. The UWA LEAP laser value (34 / 51 / 14 by volume, no depth) is not used.

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

No source gives measured sand / silt / clay at any JapanFlux tower. Our own packages contain no texture either:
- the nine JPF releases' BIF files have no `GRP_SOIL*` groups;
- the JapanFLUX2024 BADM soil templates of JP-Tgf and JP-Tom have only the soil classification filled in.

- **JP-Api:** Andosol / moderately moist brown forest soil BD(d) (FFPRI); about 11 kg C m⁻² in the top 20 cm (Koarashi et al. 2025).
- **JP-Fhk:** coarse-grained volcanic ash of Mt Fuji (NIES, AsiaFlux).
- **JP-Fjy:** original BIF says "Soil is poorly developed due to underneath volcanic lava, land surface is covered with a very thin layer of litter". The lava is the AD 937 Kenmarubi flow.
- **JP-Khw:** moderately moist brown forest soil BD on crystal schist (FFPRI).
- **JP-Spp:** moderately moist black soil Bl D / Andosol on volcanic ash (FFPRI; Yamanoi et al. 2015); "Loam" (AsiaFlux); 18.0 kg C m⁻².
- **JP-Tak:** original BIF says "black-brick soils with a dark and thick surface layer", which is Kuroboku (Andosol). This agrees with Ohtsuka 2012, more than 300 t C ha⁻¹ to 1 m. AsiaFlux's "Dystric Cambisol" is the outlier.
- **JP-Tef:**
  - *Tower.* Original BIF says "mainly a Gleyic Cambisol" with a ~10 cm organic horizon.
  - *Nearby profiles.* Hokkaido University FRED profiles in Teshio Experimental Forest are silty clay to light clay at the surface and heavy clay below.
- **JP-Tgf:** BADM soil file gives WRB Andosol ("Kuroboku soil"), USDA Andisols. Kanto Loam over Joso clay; organic carbon 4.9 % at 0–20 cm (Suh et al. 2009).
- **JP-Tmd:** volcanogenous regosol, an A horizon of about 10 cm over Tarumae pumice.
- **JP-Tom:**
  - *Tower.* BADM soil file gives WRB Regosol ("Volcanogenous regosol"), USDA Entisols.
  - *Nearby profiles.* FRED profiles have a 4.5–10 cm sandy loam A horizon over pumice gravel.
- **JP-Yms:**
  - *Tower.* Original BIF says the forest is "built up on weathered granite".
  - *Texture class.* Regosol, "sandy loam or loamy sand" with 53 % fine granitic gravel by weight (Kominami et al. 2008); soil depth about 47 cm (snippet).

All 20 tower coordinates are now taken from our own source files (L6, BIF or BADM). The six JapanFlux coordinates first taken from the JapanFlux2024 paper agree with them.

## Decisions still needed

1. **SLGA** for the nine Australian sites. It needs a TERN API key, and matters most at AU-Dry, at AU-Cpr below 41 cm, and as a check at AU-Stp and AU-Tum.
2. **JP-Tef, JP-Yms, JP-Tmd, JP-Tom.**
   - SoilGrids contradicts the site descriptions, and no numeric alternative exists.
   - Options: keep SoilGrids, or run a texture sensitivity: heavier at JP-Tef, sandier at JP-Yms and the Tomakomai pumice sites.
3. **ORGANIC.** Decide whether to apply site or SoilGrids organic matter at the Andosol and forest sites: most JapanFlux sites, AU-Tum and AU-Cow.
4. **Shallow soils.** Decide whether to set `zbedrock`, which is separate from texture, at:
   - JP-Fjy (lava);
   - AU-ASM (hardpan ~1 m);
   - AU-How (laterite ~1.2 m);
   - JP-Yms (~47 cm).
