# OzFlux_JapanFlux_SurfaceFields — surface fields besides texture and PFT, before the spin-up surface is built

Started 3 November 2026; the fourth OzFlux / JapanFlux topic. [OzFlux_JapanFlux_PFT](../OzFlux_JapanFlux_PFT/) fixed the vegetation and [OzFlux_JapanFlux_Soil](../OzFlux_JapanFlux_Soil/) the sand / clay. This folder covers the remaining surface fields that act on soil water, and therefore on GPP, respiration and NEE:
- `zbedrock` — depth to bedrock;
- `ORGANIC` — soil organic matter, 10 levels;
- `FMAX`;
- `SOIL_COLOR`;
- the landunit shares.

These must be settled before the 19 remaining spin-up surfaces are built, because a later change means repeating the 800-year spin-up.

**Status, 4 Nov 2026: recommendation v1 done.** It is [`OZ_JP_RECOMMENDED_SURFACE_FIELDS_20_SITES_20261103.csv`](OZ_JP_RECOMMENDED_SURFACE_FIELDS_20_SITES_20261103.csv), [described below](#recommendation-v1-3-nov-2026). `use_bedrock` is decided: on at AU-ASM only ([decision C](#decision-use_bedrock)). **AU-DaS is no longer processed** (4 Nov 2026: only 14 complete years before the 2022 land clearing; see [PostSpinup](../OzFlux_JapanFlux_PostSpinup/README.md#au-das-excluded-operator-decision-4-nov-2026)). Its rows stay in the tables as records.

## What the pinned model does with these fields

Pinned versions: CTSM `d5ea9d01`, FATES `121723f6`.

| Field | Used? | How |
| --- | --- | --- |
| `zbedrock` | **Only if `use_bedrock = .true.`** | See [the bedrock switch](#the-bedrock-switch) below |
| `ORGANIC` (kg m⁻³, 10 levels) | Yes | `om_frac = min(om_frac_sf · ORGANIC / organic_max, 1)`, with `organic_max` from the CLM parameter file (130). It mixes organic-soil properties into porosity, saturated conductivity, suction, the b exponent and thermal conductivity (`SoilStateInitTimeConstMod`). Model layers below the 10 dataset levels take level 10. Below `zsapric` = 0.5 m, organic matter takes sapric-peat properties |
| `FMAX` | Yes | Maximum saturated fraction. Saturation-excess runoff scales with it and with the water-table depth |
| `SOIL_COLOR` | Yes | Dry / saturated soil albedo class. It matters where the canopy is sparse |
| `PCT_NATVEG` and the other landunits | Yes | Project rule for point surfaces: NATVEG = 100 |

### The bedrock switch

- **The FATES default switches bedrock off.** `namelist_defaults_ctsm.xml` sets `use_bedrock = .false.` when `use_fates = .true.`. No case in this project overrides it.
- **Effect when off:** `zbedrock` is ignored, and every site has the full column hydrologically active: 20 layers to about 8.6 m with `soil_layerstruct_predefined = '20SL_8.5m'`. Stage01 confirms this from the template case.
- **Effect when on:** layers below `zbedrock` are bedrock — no water and no roots.
- **Shallow values need care.** CLM does *not* raise small values. Its search for the bedrock layer starts at the layer that contains `zmin_bedrock` = 0.4 m, which is layer 6 (0.32–0.48 m). So any `zbedrock` from 0.32 m to 0.48 m gives a 0.48 m column, and a value **at or below 0.32 m matches no layer and silently gives the full 8.6 m column**. Shallow sites therefore need a value between 0.33 and 0.48 m.
- **build-namelist allows the switch with FATES.** It only requires `lower_boundary_condition = 2` (zero flux), which is already the default.
- **Rooting depth.** The default FATES parameters put no practical limit on it: `fates_allom_zroot_min_z = fates_allom_zroot_max_z = 100 m` for all 14 PFTs. So roots use whatever soil column CLM provides.

**Consequence.** All 78 finished NORMAL400 spin-ups, and every OzFlux / JapanFlux case built the same way, give each site 8.6 m of soil that roots can drain. At shallow sites this weakens dry-period water stress:
- JP-Fjy: red pine on lava, almost no soil;
- JP-Tmd: about 10 cm of soil over a root-impermeable pumice layer;
- JP-Yms: 47 cm, 53 % stones;
- AU-ASM: siliceous hardpan at about 1 m.

Making `zbedrock` matter is therefore a **namelist decision** (`use_bedrock = .true.` in `user_nl_clm`, the same in AD400, NORMAL400 and the observation run), not just a surface value.

## Gridded depth-to-bedrock evidence (script 02)

[`data/gridded_depth_to_bedrock_at_towers_20261103.csv`](data/gridded_depth_to_bedrock_at_towers_20261103.csv) samples three SoilGrids250m 2017 products (Hengl et al. 2017) as 3×3 windows of 250 m cells:
- `BDTICM`: absolute depth to bedrock, which is regolith thickness;
- `BDRICM`: depth to an R horizon within 2 m;
- `BDRLOG`: probability of an R horizon within 2 m.

| Product | Result at the 20 towers |
| --- | --- |
| BDTICM | 8–48 m everywhere except AU-Tum (2.6 m). JP-Fjy shows 16 m, so the lava is not resolved |
| BDRICM | 152–200 cm, i.e. mostly "no R horizon within 2 m" |
| BDRLOG | 3–45 % |

None of these products sees hardpans, laterite, pumice or lava. They are context for the site evidence, not a substitute for it.

## Stage01 result (IRIDIS6, 3 Nov 2026)

The output is in `$HOME/ozjp_surface_stage01_20261103T135444Z` on IRIDIS6. The console values are transcribed in [`data/stage01_surface_fields_at_towers_20261103.csv`](data/stage01_surface_fields_at_towers_20261103.csv): one f09 row per site and one row per existing OzFlux point surface.

**Template case (`AT-Neu_B03_FIXNC_NORMAL400`).**
- `use_bedrock = .false.` (not set in `user_nl_clm`).
- `soil_layerstruct_predefined = '20SL_8.5m'`, `lower_boundary_condition = 2`, `soilwater_movement_method = 1`.
- `organic_frac_squared = .false.`, `use_fates_planthydro = .false.`, `use_hillslope = .false.`.
- CLM parameter file `ctsm60_params.c260518.nc`: `organic_max` 130, `zbedrock` −1 (no global override), `zbedrock_sf` 1, `om_frac_sf` 1.
- FATES default parameters: `zroot_min_z` = `zroot_max_z` = 100 m for all PFTs.
- **Layer bottoms** of the 20 soil layers (m): 0.02, 0.06, 0.12, 0.20, 0.32, 0.48, 0.68, 0.92, 1.20, 1.52, 1.88, 2.28, 2.72, 3.26, 3.90, 4.64, 5.48, 6.42, 7.46, **8.60**. Then 5 bedrock layers to 49.6 m.

**Point surfaces.**
- All existing OzFlux point surfaces are subsets of the f09 cell. `zbedrock`, `ORGANIC`, `FMAX` and `SOIL_COLOR` equal the cell values.
- The CTSM2000 reference surfaces still carry crop: AU-Cpr 18.85 %, AU-Gin 25.87 %, AU-Tum 8.39 %, AU-DaS 0.50 %, AU-Cow 0.28 %. The spin-up surface must set NATVEG = 100, as the project rule requires.
- No JapanFlux point surface exists yet.

**f09 cells at the towers:**

| Site | f09 `zbedrock` (m) [3×3] | `ORGANIC` L1 / L5 / L10 (kg m⁻³) | FMAX | SOIL_COLOR | f09 NATVEG / CROP / URBAN (%) |
| --- | --- | --- | --- | --- | --- |
| AU-ASM | 31.0 [12.0–47.3] | 6.8 / 4.9 / 1.8 | 0.39 | 16 | 100 / 0 / 0 |
| AU-Cow | **1.12** [1.12–6.96] | 22.6 / 8.1 / 9.7 | 0.39 | 18 | 99.7 / 0.3 / 0 |
| AU-Cpr | 45.0 [7.2–48.8] | 15.3 / 11.0 / 3.2 | 0.39 | 13 | 80.5 / 18.7 / 0.9 |
| AU-DaS | 3.67 [1.43–28.0] | 14.4 / 9.5 / 3.0 | 0.39 | 16 | 99.5 / 0.5 / 0 |
| AU-Dry | 1.79 [1.62–15.0] | 14.4 / 9.5 / 3.0 | 0.39 | 16 | 99.9 / 0.1 / 0 |
| AU-Gin | 4.08 [2.40–35.9] | 38.8 / 18.3 / 4.5 | 0.39 | 17 | 70.3 / 24.5 / 5.2 |
| AU-How | 24.4 [1.43–41.5] | 16.8 / 11.0 / 2.8 | 0.39 | 17 | 99.1 / 0.2 / 0.7 |
| AU-Stp | 26.8 [1.62–48.4] | 25.2 / 19.0 / 8.4 | 0.39 | 16 | 100 / 0 / 0 |
| AU-Tum | **0.91** [0.91–15.8] | 21.3 / 13.0 / 3.7 | 0.39 | 17 | 90.2 / 8.3 / 1.6 |
| JP-Api | 1.33 [0.77–12.6] | 37.9 / 14.6 / 3.2 | 0.363 | 15 | 91.7 / 6.7 / 1.6 |
| JP-Fhk, JP-Fjy (same cell) | 1.98 [1.11–27.8] | 58.3 at all 10 levels | 0.378 | 17 | 82.0 / 7.6 / 10.4 |
| JP-Khw | 2.98 [0.85–8.51] | 22.5 / 8.5 / 2.4 | 0.379 | 16 | 79.4 / 13.3 / 7.3 |
| JP-Spp, JP-Tmd, JP-Tom (same cell) | 12.8 [0.87–12.8] | 63.0 / 13.6 / 2.4 | 0.386 | 14 | 76.2 / 15.1 / 6.1 (lake 2.6) |
| JP-Tak | 2.71 [1.98–9.93] | 51.8 / 13.1 / 1.8 | 0.361 | 16 | 86.0 / 10.2 / 3.8 |
| JP-Tef | 3.61 [1.06–14.9] | 37.9 / 14.6 / 3.2 | 0.387 | 14 | 93.5 / 6.3 / 0.2 |
| JP-Tgf | 27.8 [1.98–33.1] | **103.6** / 50.8 / 20.9 | 0.39 | 16 | 45.5 / 32.4 / 20.0 (lake 2.1) |
| JP-Yms | 3.57 [0.92–18.7] | 22.5 / 8.5 / 2.4 | 0.384 | 17 | 80.4 / 9.6 / 10.0 |

**What this means.**
- **The f09 grid cannot separate neighbouring towers.** JP-Fhk and JP-Fjy (about 1 km apart) fall in one cell, and so do JP-Spp, JP-Tmd and JP-Tom. Several cells are partly urban or crop.
- **Turning on `use_bedrock` with the grid values would be wrong in places.** AU-Tum (a 40 m forest) and AU-Cow (26 m rainforest) would get less than 1.2 m of soil, while JP-Fjy (lava) would get 2 m. If `use_bedrock` is switched on, `zbedrock` must come from site evidence.
- **FMAX** is 0.36–0.39 everywhere, which is the generic value. **SOIL_COLOR** ranges 13–18.

### ORGANIC: f09 against SoilGrids

The soil topic computed ORGANIC candidates as SOC × BD × 1.724 from SoilGrids 2.0. In the top layer they are 2–6 times the f09 values:

| Site | f09 L1 (kg m⁻³) | SoilGrids L1 (kg m⁻³) |
| --- | --- | --- |
| AU-Gin | 39 | 101 |
| AU-Tum | 21 | 172 |
| JP-Tak | 52 | 183 |
| JP-Api | 38 | 139 |

Two values exceed `organic_max` = 130, which would make the top layer behave as peat.

The site measurements point the other way:
- **AU-Gin.** SoilGrids gives AU-Gin 49 g kg⁻¹ SOC at 0–5 cm and still 17 g kg⁻¹ at 1–2 m. That is implausible for a 97–99 % quartz sand (Bassendean sand).
- **AU-DaS.** The savanna plots near AU-DaS measured OC 0.48–0.66 % with BD 1.34–1.52 g cm⁻³ (Grover et al. 2012). That gives ≈14 kg m⁻³, equal to f09 (14.4).
- **JP-Tgf.** Its measured OC is 4.9 % at 0–20 cm. With an Andosol BD of 0.7–1.1 g cm⁻³ that gives 59–94 kg m⁻³, against f09 104.

**Provisional rule:**
- keep f09 `ORGANIC`;
- replace it only where tower-specific SOC and BD exist;
- use SoilGrids values only as a sensitivity case.

The literature search for site SOC stocks is still running.

## Recommendation v1 (3 Nov 2026)

**Inputs:**
- the site soil-depth evidence ([`data/soil_depth_evidence_20261103.csv`](data/soil_depth_evidence_20261103.csv): 57 rows, 20 sites, with quotes, locators and verification levels);
- the SOC stocks from the [carbon topic](../OzFlux_JapanFlux_CarbonStocks/);
- the per-site decisions in [`data/site_surface_decisions_20261103.csv`](data/site_surface_decisions_20261103.csv).

[Script 03](scripts/03_build_surface_field_recommendation.py) builds the table from these.

### `zbedrock`

**Rule:** restrict the column only where a root-restricting or shallow layer is documented. Elsewhere set 8.6 m, so that the full column is used. With this rule, switching on `use_bedrock` changes only the five restricted sites.

| Class | Sites | `zbedrock` | CLM column with `use_bedrock` on |
| --- | --- | --- | --- |
| RESTRICT | AU-ASM | 1.0 m. Siliceous hardpan at ~1 m with roots above it and a perched reservoir; water table 49 m | 1.20 m (layer 9) |
| | JP-Fjy | 0.4 m. Lava, almost no soil | 0.48 m |
| | JP-Tmd | 0.45 m. ~10 cm A over permeable pumice; roots to 0.31–0.55 m nearby | 0.48 m |
| | JP-Tom | 0.55 m. Topsoil 5–10 cm; roots in buried pumice to 0.55 m | 0.68 m |
| | JP-Tef | 0.6 m. O + A + B ≈ 0.6 m over Cretaceous sedimentary rock | 0.68 m |
| FULL_COLUMN, deep | AU-Gin, AU-How | Water table 10–11 m; roots to 9–10 m | 8.6 m |
| FULL_COLUMN, lower bound | AU-Cow (≥ 2.0 m), AU-Cpr (≥ 2.5), AU-DaS (≥ 2.5), AU-Tum (≥ 2.42), JP-Tak (≥ 1.0), JP-Tgf (≈ 2 m ash over clay) | — | 8.6 m |
| FULL_COLUMN, no evidence | AU-Dry, AU-Stp (atlas only), JP-Api, JP-Fhk, JP-Khw, JP-Spp, JP-Yms | — | 8.6 m |

**Sensitivity values** (`sensitivity_zbedrock_m`): AU-Cow 1.5, AU-Dry 1.44, AU-Stp 0.89, JP-Fhk 1.0, JP-Tgf 2.0, JP-Yms 0.45.

**Corrections to the grid and to the soil topic:**
- The f09 grid values for AU-Tum (0.91 m) and AU-Cow (1.12 m) are contradicted by the site profiles.
- The pumice at JP-Tmd / JP-Tom is permeable (Hirano et al. 2003), not root-impermeable as the soil topic had it.

### `ORGANIC`

**Rule:** keep f09 unless a tower-specific (or tower-basin) SOC stock with a stated depth exists. Where one exists, scale the f09 levels above that depth so the stock matches, and keep deeper levels at f09.

| Site | Depth | f09-implied → site SOC (kg C m⁻²) | L1 `ORGANIC` (kg m⁻³) | Basis |
| --- | --- | --- | --- | --- |
| AU-How | 0–100 cm | 5.2 → 15.1 | 16.8 → 48.8 | Chen et al. 2003, 3-site mean |
| JP-Api | 0–20 cm | 3.9 → 11.0 | 37.9 → 106.1 | Koarashi 2009, secondary |
| JP-Tak | 0–100 cm | 7.2 → > 30 | 51.8 → **130 (cap)** | Jia and Akiyama 2005, secondary. Reaches 21.8 after the cap, which is flagged |
| JP-Tef | 0–100 cm | 7.1 → 15.9 | 37.9 → 85.2 | Aguilos et al. 2014 |
| JP-Tom | 0–100 cm | 8.9 → 5.5 | 63.0 → 39.1 | Shibata et al. 2005, tower basin, incl. O horizon |

The other 15 sites keep f09. JP-Spp (18 kg C m⁻²) and JP-Yms (3.0) have stocks without a depth, so they are not used. JP-Tmd keeps f09, with JP-Tom as the nearest evidence.

### Other fields

- FMAX and SOIL_COLOR: f09.
- Landunits: NATVEG 100; crop, urban, lake, wetland and glacier 0. The f09 cells carry up to 32 % crop and 20 % urban. Confirmed against the land cover at the towers [below](#land-cover-and-rivers-at-the-towers-script-04-4-nov-2026).

### Decision: `use_bedrock`

| Option | What changes | Notes |
| --- | --- | --- |
| **A. Keep the FATES default (off)** | Every site gets 8.6 m of soil | Consistent with the 78 finished ICOS / AmeriFlux spin-ups. The five shallow sites get too much plant-available water |
| **B. Switch it on for the OzFlux / JapanFlux sites** | Only AU-ASM, JP-Fjy, JP-Tmd, JP-Tom and JP-Tef change | `use_bedrock = .true.` goes in `user_nl_clm` for AD400, NORMAL400 and the observation run alike. CLM puts a zero-flux base at the bedrock layer. That matches the perched hardpan reservoir at AU-ASM. For the fissured lava and permeable pumice sites it may hold too much water above 0.48–0.68 m; check against soil moisture where it exists (JP-Fjy has none) |
| **C. Switch it on only where the restricting layer is documented under the tower and acts as a barrier** | Only AU-ASM changes | The other four shallow sites have T2 evidence: fissured lava, permeable pumice, or rock whose contact is not stated. A zero-flux base at 0.48–0.68 m is not established there |

**Operator decision, 3 Nov 2026: B.** Superseded on 4 Nov.

**Operator decision, 4 Nov 2026: C, not all 20 sites.** The per-site table is [`data/use_bedrock_decision_20261104.csv`](data/use_bedrock_decision_20261104.csv).
- **AU-ASM:** `use_bedrock = .true.` in AD400, NORMAL400 and the observation run. The hardpan is documented under the tower (T1), and its perched reservoir matches CLM's zero-flux base.
- **The other 19 sites:** FATES default (`.false.`, not set in `user_nl_clm`), as in the 78 ICOS / AmeriFlux spin-ups.
- **JP-Fjy, JP-Tmd, JP-Tom and JP-Tef:** baseline off. An on run is an optional sensitivity case. It needs its own AD400 and NORMAL400, because soil water and carbon come to a different equilibrium.
- **Every site's surface still carries the `zbedrock` of the recommendation CSV.** With the switch off the value is ignored, so a sensitivity run changes only `user_nl_clm`, not the surface.
- **AU-ASM goes first.** Non-Competition-CLM-experiment Stage22 (`examples/OzFlux_Batch01_09/BEDROCK_20261103_SITE_V3_PLAN.md`, branch `feat/ozflux-asm-bedrock-v3-20261103`) builds a v3 candidate surface from Codex's verified Stage13 SITE-SOIL v2. It changes only `zbedrock`, to 1.0 m, and records the namelist requirement for the future AD400 controller.
- **AU-ASM landunits stay as Stage16** (NATVEG 99.9994 %), following the operator rule in that pipeline.

## Land cover and rivers at the towers (script 04, 4 Nov 2026)

[Script 04](scripts/04_landcover_and_waterways_at_towers.py) reads two sources at the coordinates in [`OZ_JP_20_SITE_COORDINATES_20261103.csv`](../OzFlux_JapanFlux_Soil/data/OZ_JP_20_SITE_COORDINATES_20261103.csv):
- ESA WorldCover 10 m 2021 class shares within 250, 500, 1000 and 2000 m: [`data/worldcover_landcover_at_towers_20261104.csv`](data/worldcover_landcover_at_towers_20261104.csv);
- OpenStreetMap distances to the nearest river, stream and water body: [`data/osm_waterways_near_towers_20261104.csv`](data/osm_waterways_near_towers_20261104.csv).

### Cropland: operator rule, 4 Nov 2026

**Rule:** where there is real cropland at the tower, use its real share. The f09 crop share is not used.

**What the pinned model does with a crop share.**
- With FATES, `create_crop_landunit = .false.` (`namelist_defaults_ctsm.xml`).
- `surfrd_wtfates` therefore merges the crop landunit into the natural landunit, and the `PCT_CFT` weights become HLM PFTs 15–16 (`surfrdMod.F90`).
- The project FATES parameter file (`fates_params_default.json`, SHA256 `0819f8fd…`) maps only HLM PFTs 1–14 (`fates_hlm_pftno` = 14). `EDInitMod` takes bare ground from HLM PFT 0 and renormalises the live PFTs to one.
- **Net effect: a crop share is never simulated as crop.** It is dropped and goes to the live PFTs, and bare ground shrinks by the factor NATVEG / (NATVEG + CROP).
- The Stage03 surfaces built so far would give:
  - AU-Cpr: bare 54 % → 43.8 %;
  - AU-Gin: bare 20 % → 14.8 %;
  - AU-Tum: no change (no bare ground).
- **Real cropland would therefore have to enter `PCT_NAT_PFT` as a grass PFT.**

**Result.** Within 2 km, WorldCover shows **0.0 % cropland** at all nine OzFlux towers, including AU-Cpr, AU-Gin and AU-Tum. The other JapanFlux towers show at most 1.9 % within 1 km (JP-Tmd at 250 m) and at most 4.0 % within 2 km (JP-Spp).

**JP-Tgf** shows 16.9 % "cropland" within 250 m and 11.9 % within 500 m. The tower stands in a mown experimental grass field, which WorldCover's cropland class most likely includes (grassland is only 2.3 % within 250 m). This is not crop in the footprint.

**Decision (operator confirmed 4 Nov 2026):** PCT_CROP = 0 and NATVEG = 100 at all 20 sites. The surfaces for AU-Cpr, AU-Gin and AU-Tum must be rebuilt with crop 0, together with soil v1 and these surface fields. That restores the v1.1 bare-ground shares in FATES.

**Built-up land** at the towers is small within 500 m: JP-Fjy 6.9 %, JP-Tgf 27.5 % (the research centre around the field), JP-Spp 0.1 %. Urban also stays 0.

### Sites near rivers and using groundwater

The per-site table is [`data/groundwater_river_flags_20261104.csv`](data/groundwater_river_flags_20261104.csv). It combines the OSM distances with the water-table evidence in `soil_depth_evidence_20261103.csv`.

| Flag | Sites | Evidence |
| --- | --- | --- |
| **RIVER_AND_GROUNDWATER** | **JP-Spp** | 398 m from the Tsukisamu River (月寒川); groundwater-level gauge buried at 1.4 m, so a water table at times shallower than 1.4 m |
| **GROUNDWATER_DEPENDENT** (no river) | **AU-Gin**, **AU-How** | AU-Gin: Banksia roots to ~9 m; water table 9.6 → 10.5–11 m; no river within 10 km. AU-How: roots to ~10 m at the dry-season water table; Howard River 7.8 km |
| SHALLOW_WATER_TABLE | JP-Tgf | Water table within the ~2 m ash loam or the clay below; Hasunuma River 0.8 km |
| NEAR_WATERCOURSE_NO_GW_EVIDENCE | AU-Cow, AU-Tum, JP-Api, JP-Fhk, JP-Fjy, JP-Khw, JP-Tef, JP-Yms | River or stream ≤ 500 m, no water-table evidence. Check only |
| NONE | AU-ASM, AU-Cpr, AU-DaS, AU-Dry, AU-Stp, JP-Tak, JP-Tmd, JP-Tom | AU-DaS is 2.6 km from the Daly River, with deeper groundwater |

**What the model cannot represent.** The single-column CLM has an 8.6 m column, a zero-flux base and no lateral or river inflow. So:
- **AU-Gin and AU-How:** the real water table (about 10–11 m) lies below the model column, so the model can give too much dry-season water stress, and GPP, ET and NEE are biased in the dry season;
- **JP-Spp:** gets no river-fed water;
- **all flagged sites:** the flags are for interpreting the evaluation. They do not change any input.

## Scripts

| Script | Where | What |
| --- | --- | --- |
| [01_surface_fields_at_towers_READONLY.py](scripts/01_surface_fields_at_towers_READONLY.py) | IRIDIS6 login node, read only | Reads three things:<ul><li>the project global surface `surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc` at each tower (nearest cell and 3×3 land cells): `zbedrock`, `ORGANIC`, `FMAX`, `SOIL_COLOR`, `SLOPE`, `STD_ELEV`, landunits;</li><li>the same fields in every existing point surface of the sites;</li><li>the template case's `use_bedrock`, soil layer structure, `organic_max` / `zbedrock_sf` / `om_frac_sf`, the FATES rooting parameters, and the model layer depths.</li></ul> |
| [02_gridded_depth_to_bedrock_at_towers.py](scripts/02_gridded_depth_to_bedrock_at_towers.py) | anywhere (public data) | SoilGrids250m 2017 depth-to-bedrock products at the towers. Done 3 Nov |
| [03_build_surface_field_recommendation.py](scripts/03_build_surface_field_recommendation.py) | anywhere | Builds the recommendation table from the Stage01 values, the gridded products and the per-site decisions. Maps `zbedrock` to the CLM bedrock layer exactly as `initVerticalMod`; scales `ORGANIC` to site stocks. Done 3 Nov |
| [04_landcover_and_waterways_at_towers.py](scripts/04_landcover_and_waterways_at_towers.py) | anywhere (public data) | ESA WorldCover class shares around the towers, and OpenStreetMap distances to rivers, streams and water bodies. Done 4 Nov |

## Next steps

1. AU-ASM: run Non-Competition-CLM-experiment Stage22 on IRIDIS6 to build the v3 surface, and record its SHA256.
2. When each site's spin-up surface is built, apply soil v1 texture together with this table: `zbedrock`, `ORGANIC`, NATVEG 100 and FMAX / SOIL_COLOR unchanged. Record the changed variable names and SHA256 values as the project's surface rules require. Set `use_bedrock` from [`data/use_bedrock_decision_20261104.csv`](data/use_bedrock_decision_20261104.csv).
3. AU-Cpr, AU-Gin and AU-Tum: rebuild with PCT_CROP = 0. Their Stage03 surfaces carry the grid crop share (18.85 %, 25.87 %, 8.39 %), but there is no cropland at the towers ([script 04](#cropland-operator-rule-4-nov-2026)).
3. Optional: read SLGA depth of soil / regolith for the Australian sites once a TERN API key is available.
