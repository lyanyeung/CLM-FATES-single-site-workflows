# Stage12h VERIFIED — US-MtB source T is persistently colder than ERA5-Land; Stage12i pressure-height diagnostic

Original IRIDIS6 Stage12h `--self-test`, `--check`, and `--run` PASSED for three original source years 2020/2022/2024 and all 1,038 precisely matched native RH gap times. SHA-receipted, READ-ONLY diagnostic at:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12h_US-MtB_temperature_and_clock_three_year_diagnostics_20261025T054717Z_58c34b41/`

| Original temperature comparison | 2020 | 2022 | 2024 |
| --- | ---: | ---: | ---: |
| Whole-year tower TA_F minus ERA5-Land T2m mean (C) | -6.681486 | -6.374133 | -6.540747 |
| 1038 held target subset tower minus grid mean (C) | -9.360981 | -8.697723 | -8.903304 |
| Target fraction with absolute tower/grid T >5C | 99.34% | 100.00% | 98.77% |
| Whole-year measured/site TA_F vs paired native TA_ERA MAE (C) | 2.796780 | 2.705542 | 2.792116 |
| Target subset paired native ERA TA comparison MAE (C) | 6.452533 | 6.327997 | 6.223833 |
| Best exploratory additional relative UTC shift (hours) | +6 | +6 | +6 |
| Target MAE after even this extra time-shift (C) | 7.440133 | 7.429261 | 7.624984 |

**All 1,038 Stage12g originally missing source-year target events have original TA_F_QC=0** in the source release (302 + 328 + 408). This means the source supplies measured/QC0 air temperature. Consequently do NOT auto-replace measured tower TA with gridded ERA T, do NOT relax the 5 C screen, and do NOT assume the minimum MAE clock offset is an approved source time base.

### Scientific lead: mountain station versus grid terrain representation

The official [AmeriFlux site search](https://ameriflux.lbl.gov/sites/site-search/) lists **US-MtB Mt Bigelow, lat 32.4160 N, lon -110.7256 E and elevation 2573 m** (IGBP ENF). Strong all-year tower cooler-than-grid T and the published mountain site elevation make mismatched **grid versus tower orography** an important hypothesis; it is NOT yet established merely by a temperature difference.

The next [Stage12i pressure-height and orography script](../scripts/stage12/12i_us_mtb_pressure_orography_READONLY.py) has been added to GitHub **but NOT yet run on IRIDIS6**. It loads exact SHA-proven original source `PA_F`, preserved Stage12e `PSRF`, release-paired native `PA_ERA`, ERA5-Land hourly `surface_pressure`, gridded `T2M` and source tower `TA_F` at their original native midpoint using the same provisional BIF time basis as Stage12h. It compares median source/grid pressure at the original six year/scope slices, all three years' 36 months and exact 1,038 source events. The hypsometric relative height proxy `(Rd*Tbar/g)*ln(P_grid/P_site)` is an APPROXIMATION and is not the actual ERA5-Land grid orography field. It tests purely diagnostic lapse gradient rates **4.0, 6.5 and 9.0 K/km** for all-year and original blocked subsets and reports corresponding raw-vs-height-adjusted MAE (18 science sensitivity rows).

Stage12i never changes original T/P, pressure, source clocks, relative humidity, VPD/QBOT, files, CIME or Slurm. A pressure/elevation explanation, even if strongly supported, would require a separate scientific assessment of how to transfer humidity between elevations rather than unconditionally copying raw gridded RH. Keep the **1,031 temperature disagreement holds**, 4 ice holds, and 233 other original scientific holds untouched; Post-v5/DATM/spinup release stays ZERO.

**Next decision:** if pressure-derived site-grid height difference plausibly explains the persistent T gap AND original paired TA_ERA/source PA support site meteorology, design a physical elevation-aware *research-only humidity sensitivity* with mass/ice/clock and boundary checks; do not automatically declare any pending US-MtB records repaired. If the hypsometric proxy fails to account for the T discrepancy, prioritize coordinate/grid selection and source time metadata, rather than downloading more US-MtB years.
