# OzFlux_JapanFlux_SurfaceFields — surface fields besides texture and PFT, before the spin-up surface is built

Started 3 November 2026; the fourth OzFlux / JapanFlux topic. [OzFlux_JapanFlux_PFT](../OzFlux_JapanFlux_PFT/) fixed the vegetation and [OzFlux_JapanFlux_Soil](../OzFlux_JapanFlux_Soil/) the sand / clay. This folder covers the remaining surface fields that act on soil water, and therefore on GPP, respiration and NEE:
- `zbedrock` — depth to bedrock;
- `ORGANIC` — soil organic matter, 10 levels;
- `FMAX`;
- `SOIL_COLOR`;
- the landunit shares.

These must be settled before the 19 remaining spin-up surfaces are built, because a later change means repeating the 800-year spin-up.

**Status, 3 Nov 2026:**
- Done: pinned-source check, gridded depth-to-bedrock evidence (script 02, committed), and the IRIDIS6 read-only Stage01 script.
- Pending: the site literature (soil depth, restrictive layers, rooting depth, water table), the Stage01 run, and the recommendation.

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
- **Effect when on:** layers below `zbedrock` are bedrock — no water and no roots. CLM raises any value below 0.4 m (`zmin_bedrock`) to that minimum.
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

## Scripts

| Script | Where | What |
| --- | --- | --- |
| [01_surface_fields_at_towers_READONLY.py](scripts/01_surface_fields_at_towers_READONLY.py) | IRIDIS6 login node, read only | Reads three things:<ul><li>the project global surface `surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc` at each tower (nearest cell and 3×3 land cells): `zbedrock`, `ORGANIC`, `FMAX`, `SOIL_COLOR`, `SLOPE`, `STD_ELEV`, landunits;</li><li>the same fields in every existing point surface of the sites;</li><li>the template case's `use_bedrock`, soil layer structure, `organic_max` / `zbedrock_sf` / `om_frac_sf`, the FATES rooting parameters, and the model layer depths.</li></ul> |
| [02_gridded_depth_to_bedrock_at_towers.py](scripts/02_gridded_depth_to_bedrock_at_towers.py) | anywhere (public data) | SoilGrids250m 2017 depth-to-bedrock products at the towers. Done 3 Nov |

## Next steps

1. Run Stage01 on IRIDIS6.
2. Collect site evidence on soil depth, restrictive layers, rooting depth and water table (literature search in progress).
3. Recommendation table for each site:
   - a plant-accessible `zbedrock`;
   - a 10-level `ORGANIC` from site SOC and bulk density where they exist, otherwise SoilGrids, against the current grid values;
   - `FMAX` / `SOIL_COLOR` kept unless contradicted;
   - NATVEG = 100.

   Plus a separate decision on `use_bedrock`.
