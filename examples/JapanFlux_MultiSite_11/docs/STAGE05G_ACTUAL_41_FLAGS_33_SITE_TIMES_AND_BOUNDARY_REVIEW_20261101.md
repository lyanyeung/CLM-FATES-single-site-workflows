# JapanFlux Stage05G — actual 41 selected-F source-matched anomalous variable records (2026-11-01)

## Primary evidence

Operator executed [Stage05G](../scripts/stage05/05g_aggregate_selected_forcing_source_impact_NO_ZIP_NO_SLURM.py) against all eight validated Stage05F JSONs and posted its **full 41-row selected-F anomaly ledger**. This document is grounded in that original operator ledger, not in a new source scan or claimed repair.

**All 41 variable-level entries** in the posted ledger are classified `FLAGGED_ERA_EQUALS_NONPHYSICAL_SELECTED_F`, with:
- `selected_F_screen_nonphysical=1` under earlier source screening thresholds;
- `selected *_F` numerically **equal** to the package's same-release `*_ERA` column;
- **raw source `*_F_QC=2`** on each listed variable record.

Stage05G produces a derived TSV and JSON, does not edit any ZIP or force, and does not submit Slurm. The user posted only the printed 41 affected rows, not the full Stage05G output metadata; the unique site×half-hour count below is **calculated by deduplication of the posted records** and can be independently checked from the Stage05G JSON on IRIDIS.

## Exact affected site-variable totals

| Site | TA_F anomalous field rows | PA_F anomalous field rows | LW_IN_F anomalous field rows | Field flags total | Unique site×native half-hours |
|---|---:|---:|---:|---:|---:|
| JP-Fjy | 0 | 6 | 0 | 6 | 6 |
| JP-Khw | 3 | 6 | 2 | 11 | 7 |
| JP-Tef | 0 | 0 | 4 | 4 | 4 |
| JP-Tmd | 3 | 9 | 2 | 14 | 10 |
| JP-Yms | 0 | 2 | 4 | 6 | 6 |
| **TOTAL** | **6** | **23** | **12** | **41** | **33** |

The three **site-specific native event dates with current selected-F threshold flags** are 2005-08-12, 2011-12-17 and 2022-04-09. This is not a full global climate quality flag inventory. The two older ERA source events (1990-04-03 and 1999-01-19) have no Stage05G selected-F threshold flag in the source audit presented; some 1999 source events are inside JP-Tak's tower years but its selected F is protected by original measured source rows.

### Read-only exact problematic examples from posted ledger

- **JP-Fjy, PA_F**: 2005-08-12 02:30 = 45.16 kPa; 03:00 = 0.334; 03:30 = 45.161. Equivalent 2011-12-17 06:30 = 45.123; 07:00 = 0.334; 07:30 = 45.211. All `QC2`, `PA_F=PA_ERA`.
- **JP-Khw, 2005-08-12**: LW_IN_F 02:00/02:30 = 39.171 W/m²; TA_F 02:30 = −122.144°C, 03:00 = −268.276°C, 03:30 = −122.665°C; PA_F 02:30 = 48.912 kPa, 03:00 = 0, 03:30 = 48.922 kPa. PA_F at 2011-12-17 06:30/07:00/07:30 = 49.506/0/49.571 kPa; 2011 TA_F, LW_IN_F were selected differently from the corrupt `*_ERA`.
- **JP-Tef LW_IN_F**: 2011-12-17 06:00/06:30 and 2022-04-09 02:00/02:30 each exactly 26.164 W/m², `QC2`.
- **JP-Tmd, 2005-08-12**: LW_IN_F 02:00/02:30 = 28.519 W/m²; TA_F 02:30/03:00/03:30 = −132.399/−284.222/−132.688°C; PA_F = 49.502/0/49.506 kPa on same three TA intervals. PA_F at 2011-12-17 06:30/07:00/07:30 = 49.448/0/49.514; at 2022-04-09 02:30/03:00/03:30 = 49.616/0/49.579 kPa.
- **JP-Yms**: LW_IN_F 2005-08-12 02:00/02:30 and 2011-12-17 06:00/06:30 = 44.79 W/m²; PA_F 2005-08-12 03:00 and 2011-12-17 07:00 = 37.349 kPa. All listed entries `QC2`.

These source timestamps are not yet mapped to verified UTC/JST and have not been matched against independently sourced ECMWF ERA5 or ERA5-Land.

## Interpretation and important threshold gap

These 41 per-variable records are **confirmed nonphysical/very-low-threshold failures that exactly reproduce the already-flagged source ERA values**. They are **not necessarily the complete set of altered F values**. A pressure at 60–75 kPa might be incorrect if surrounding values are ~100 kPa but would evade the prior `PA_F < 50` screen. Similarly, a repeated very low LW_IN at 60–100 W/m² might escape a `LW_IN < 50` threshold. The earlier analysis showed exact half-hour interpolation of corrupted source values, making this gap specifically relevant. Do not automatically set to a new value without independent evidence.

Published FLUXNET meteorological QC semantics clarify that for standard half-hour `TA_F_QC` and similar meteorology, `0=measured`, `1=good MDS gapfill`, and `2=downscaled ERA`; see the [FLUXNET variable list](https://www.fluxnet.org/wp-content/uploads/FLUXNET2015_SUBSET_variable_list_20170509.pdf) and [FLUXNET2015 processing article](https://pmc.ncbi.nlm.nih.gov/articles/PMC7347557/). This is strong standard-based provenance support for the observed `QC2` and `F=ERA` pattern. **Exact JPF release's BIF QC mapping still needs direct confirmation.** Do not conflate this JPF FLUXMET_HH pipeline with the two separately packaged JapanFlux2024 `COREVARS_HH` products for JP-Tom/Tgf; their provenance must be audited separately.

## Next stage

[Stage05H exploratory PA/LW boundary screen from existing Stage05F and 05G JSON/TSV](../scripts/stage05/05h_PA_LW_event_boundary_relative_screen_NO_ZIP_NO_SLURM.py) is a new **read-only, no ZIP, no Slurm, no repair** audit of *all available target-event context rows*, including selected `PA_F` and `LW_IN_F` values not yet flagged under absolute thresholds.

Stage05H uses first/last available selected-F context values as day-specific flanks, applies deliberately **exploratory relative screens**: `PA_F < 0.85 × min(flanks)` (both flanks >70 kPa), `LW_IN_F < 0.60 × min(flanks)` (both flanks >120 W/m²). This is intended to identify suspicious interpolated shoulder values that escaped simple cutoffs, not to certify baseline weather, derive repair values, or approve physical consistency. All flagged values stay in context with original QC/raw ERA. The script is committed but **not executed against operator Stage05F/05G files yet**.

**Science status:** original release ZIP untouched; no approved forcing overlay, no model job, no AD400. A later independent reference check of original ERA5/ERA5-Land and tower QC/metadata is necessary before any change. JP-Tom and JP-Tgf humidity/VPD investigations remain separately outstanding.
