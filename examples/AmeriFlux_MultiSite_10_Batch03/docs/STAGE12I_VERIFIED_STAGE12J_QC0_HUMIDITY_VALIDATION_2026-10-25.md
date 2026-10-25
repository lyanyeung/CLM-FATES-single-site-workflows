# Batch03 Stage12i VERIFIED: US-MtB mountain/ERA5-Land terrain mismatch

2026-10-25 IRIDIS6 `--self-test`, `--check`, `--run` ALL PASSED for [Stage12i](../scripts/stage12/12i_us_mtb_pressure_orography_READONLY.py). The original SHA-sealed read-only pressure/orography diagnostic is at:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12i_US-MtB_orography_pressure_20261025T064222Z_2944f5f6/`

Original US-MtB Mt Bigelow tower elevation is published as 2,573m. The three SHA-pinned source year grids (ERA5-Land gridcell 32.4N, -110.7E) are from ~1km lower apparent orography than the original mountain tower. Hydrostatic proxy uses **original tower FLUXMET PA_F**, independently checked against unchanged Stage12e `PSRF` with **ERA5-Land actual surface_pressure** and near-surface temperature. The height estimate is NOT a downloaded direct geopotential field and is not proof of the grid true elevation.

| Year | Median original tower pressure | ERA5-Land pressure | Whole-year pressure-derived site-grid relative height | Grid elevation diagnostic proxy | Original whole-year grid→tower T MAE |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2020 | 74,553 Pa | 84,534 Pa | 1,063.4 m | 1,509.6 m | 7.058°C |
| 2022 | 74,463 Pa | 84,494 Pa | 1,060.0 m | 1,513.0 m | 6.781°C |
| 2024 | 74,463 Pa | 84,460 Pa | 1,058.9 m | 1,514.1 m | 6.888°C |

| Calendar year | 1,038-event subset original grid→tower T MAE | Diagnostic 6.5K/km lapse MAE | Diagnostic 9K/km lapse MAE |
| --- | ---: | ---: | ---: |
| 2020 (302 source events) | 9.361°C | 2.789°C | 1.641°C |
| 2022 (328 source events) | 8.698°C | 2.231°C | 1.377°C |
| 2024 (408 source events) | 8.903°C | 2.462°C | 1.545°C |

The original `TA_F_QC=0` at **all 1,038 target site records** means their tower air temperature is preserved. **The original source temperature should NOT be overwritten with warm, lower-elevation ERA5-Land T2m.** This evidence shows that Stage12g's direct `abs(T_tower - T_grid) <= 5°C` source-representation rule is a problematic rejection criterion for THIS mountainous station. It does **not** independently establish whether grid relative humidity, grid specific humidity, grid vapour pressure or a vertically corrected dewpoint should be used at the original high-elevation tower.

## Stage12j: four-method source-native humidity cross-validation on observed VPD QC0

The [Stage12j elevation-aware QC0 validation and strict optional research shadow](../scripts/stage12/12j_us_mtb_elevation_aware_QC0_humidity_crossvalidation.py) is committed but **NOT yet run on IRIDIS6**. It uses Stage12i source SHA and the original Stage12h/Stage12g upstream source QC/temperature evidence and 2020, 2022, 2024 original tower pressure and temperature.

Only originally observed **`VPD_F_QC=0`** AND `TA_F_QC=0` valid tower cold measurements (T<=5C) are model-vs-observed humidity analogues; no QC0 record is edited. Four PREDECLARED grid humidity transfer source formulas:

1. **GRID_RH:** preserve grid T2m/dewpoint-derived RH, recompute VPD/QBOT at original tower TA_F/PA_F.
2. **GRID_Q:** preserve grid specific humidity `q` (calculated with grid surface pressure), apply original tower pressure and temperature.
3. **GRID_E:** preserve grid dewpoint-derived absolute vapour pressure, apply at tower temperature.
4. **LAPSE_TD:** shift grid dewpoint down by actual grid-to-tower air temperature discrepancy, then calculate vapour pressure at the new diagnostic dewpoint.

All four are research hypotheses, not certified source measurements. Separate physical source screens for original QC0 source and candidates require positive water vapour, water-saturation and subzero ice-phase compatibility, original site pressure consistency and a 6.5K/km **pressure-height-normalised** grid-vs-tower temperature agreement within 5C.

A method passes the provisional science gate only when EACH of the three years has **>=50 valid cold QC0 analogues**, >=60% physically admissible candidate coverage, cold-subset VPD MAE <=1.5hPa, absolute bias <=0.7hPa, and fraction of prediction errors >2hPa <=10%. This avoids cherry-picking a humidity formula because it can fill a large number of source gaps. If no method passes, Stage12j reports and holds **all** previously unresolved events. If a method passes, it may construct *only* isolated numeric research candidates for previously held 2020/2022/2024 source VPD QC1/QC2 events, and rejects any newly excessive adjacent VPD jumps over 4hPa. All valid prior Stage12g site humidity, 3 original Stage12g repairs, 233 original Stage12b physics holds and tower T/P/clock remain untouched. `--check` is guaranteed no-write; `--run` creates a single independent incomplete science trial directory (optional full US-MtB research CSV only if the strict method passes). No Post-v5, DATM or spinup release is inferred.

Source model verification and setting/model release are separate decisions: a pressure-height approximation is not a direct ERA geopotential measurement, source native-to-UTC offset is still unapproved, and gridded ERA5-Land remains ERA5-driven, not independent tower RH truth.
