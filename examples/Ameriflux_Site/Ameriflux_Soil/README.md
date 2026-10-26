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

## Result: recommended input soil texture for all 50 sites, 26 October 2026

**[FINAL_50_SITE_SOIL_TEXTURE_20261026.md](FINAL_50_SITE_SOIL_TEXTURE_20261026.md)** gives each site's recommended `PCT_SAND` / `PCT_CLAY` with its evidence. The same values are in [FINAL_RECOMMENDED_INPUT_SOIL_TEXTURE_50_SITES_20261026.csv](FINAL_RECOMMENDED_INPUT_SOIL_TEXTURE_50_SITES_20261026.csv).

| Tier | Sites |
| --- | ---: |
| T1 site measured (21 ReESH, 6 full-BADM profiles) | 27 |
| T1N neighbour measured (US-Ho2, US-Ho3 from US-Ho1) | 2 |
| T2 SSURGO point | 12 |
| T3 SoilGrids 250 m | 9 |

Evidence files:
- [Full BADM extraction for all 50 sites](data/full_badm_50_20261026/)
- [Stage01 run summary](data/STAGE01_50_SITE_SOIL_TEXTURE_SUMMARY_20261026.csv)
- [Literature](data/literature_soil_evidence_20261026.csv)
- [ReESH records](data/reesh_records_found_20261026.csv)
- [Manual BADM depth assignments](data/badm_manual_depth_assignments_20261026.csv) and [neighbour proxies](data/site_proxy_assignments_20261026.csv), each with a written reason

[data/PRELIMINARY_8_SITE_CLM10_TEXTURE_20261026.csv](data/PRELIMINARY_8_SITE_CLM10_TEXTURE_20261026.csv) is the hand-read check made before Stage01, and is superseded.

## Extract full BADM soil records (Stage02, laptop or WSL)

```bash
python3 -B scripts/02_extract_full_badm_soil.py --badm-dir /path/to/BADM --output-dir /path/to/BADM_soil_extract
```

## Run Stage01 on IRIDIS6

Run this from a login node, because it needs internet for Zenodo, USDA SDA and ISRIC. It reads BIF coordinates from `sites/MY_EC_SITE/<SITE>/forcing/raw*`. It also reads the surface file used by each existing case (`cases/<SITE>_*/CaseDocs/lnd_in` → `fsurdat`), to compare current and recommended values. SoilGrids is rate-limited to 5 requests a minute, so all 50 sites take about 15 minutes. Results are cached, so a rerun is quick and can be done with `--no-network`.

```bash
python3 -B scripts/01_collect_soil_texture_evidence.py --self-test
python3 -B scripts/01_collect_soil_texture_evidence.py --output-root $HOME/CLM_FATES_SOIL/AmeriFlux50_20261026 \
    --badm-dir $HOME/CLM_FATES_SOIL/BADM_full --coords US-BZS:64.6963:-148.3235
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
