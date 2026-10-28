# US-MtB high-elevation humidity research handoff to Claude — 2026-10-28

## Workstream ownership
Claude: US-MtB only (high-elevation grid-representativeness, humidity source/physics and model compatibility); ChatGPT: US-Me6 only. **The user makes every final repair decision.** Only read-only source and new reports are authorized now; no changes to original FLUXMET/ERA, existing approved shadow, Post-v5, DATM, Slurm or AD400.

## Official station and mismatch
- US-MtB Mt Bigelow (AmeriFlux), **32.4160 N, -110.7256 W**, official elevation **2573 m**, ENF, montane evergreen conifers. Source: https://ameriflux.lbl.gov/sites/siteinfo/US-MtB and release https://ameriflux.lbl.gov/doi/FLUXNET/US-MtB (2009–2024 FLUXNET-1F v1.3_r1).
- Actual IRIDIS6 Stage12h 2020/2022/2024 tower minus ERA5-Land T mean **-6.681/-6.374/-6.541 °C**; target-event mean **-9.361/-8.698/-8.903 °C**. **All 1038 target tower TA_F_QC=0**: never replace original measured tower T with warmer low-altitude grid T.
- Stage12i median tower pressure **74553/74463/74463 Pa** vs grid **84534/84494/84460 Pa**. Hypsometric *proxy*, not directly downloaded grid orography, suggests tower ~**1063.4/1060.0/1058.9 m** above grid; inferred proxy grid height ~1510 m. Check actual ERA5-Land geopotential/static grid terrain before claiming this is measured. Diagnostics at 6.5 K/km reduce target T MAE to 2.789/2.231/2.462 °C, at 9 K/km to 1.641/1.377/1.545 °C; this is NOT automatic license to correct humidity.
- ECMWF ERA5-Land is ~9 km, forced by ERA5 atmospheric fields and includes an internal altitude-related lapse-rate correction. Documentation: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview , https://essd.copernicus.org/articles/13/4349/2021/index.html . Distinguish product companion TA_ERA/VPD_ERA from separately downloaded ERA5-Land T2m/D2m/SP.

## Four humidity hypotheses: all Stage12j original tower QC0 validation gates FAILED
| Transfer hypothesis | QC0 VPD MAE hPa: 2020 / 2022 / 2024 | fraction abs error >2hPa | decision |
|---|---|---|---|
| GRID_RH: grid RH at measured tower T/P | 1.105 / 0.994 / 1.139 | 15.31% / 10.31% / 14.80% | FAIL |
| LAPSE_TD: adjusted grid dewpoint | 1.147 / 1.037 / 1.186 | 16.47% / 11.24% / 17.01% | FAIL |
| GRID_Q: transfer q | 1.182 / 1.099 / 1.271 | 18.17% / 13.83% / 22.02% | FAIL |
| GRID_E: transfer absolute vapor pressure | 1.439 / 1.464 / 1.795 | 24.89% / 25.39% / 39.16% | FAIL |

Original per-year acceptance includes >=50 actual measured QC0 analogue samples, >=60% physically admissible coverage, VPD MAE <=1.5 hPa, abs bias <=0.7 hPa, and **<=10% errors >2 hPa**. Do not change these predeclared criteria silently.

Stage12k v2 validated **1035** held three-year records (15 with T>5C excluded from cold QC0 evaluation but preserved in overall counts); **323** had <20 same-year/month/temp-bin measured QC0 analogues, 712 >=20. At true measured VPD 0–0.25 hPa the grid-RH large-error tail was 58.49/65.52/55.56%; **313** consecutive QC0 large-error episodes, longest **27 HH**. This is a real tail-reliability problem, not only a mountain temperature mean-bias issue. Full six-site Stage12g snapshot historically had US-MtB **2840** missing humidity HH. These 2840, the 1038 three-year target subset and 1035 persistent holds are **not additive** and the latter are not a new full-site census.

## Special four frozen-phase records, 2024-02-11 native 05:00/05:30/06:00/06:30
Tower T ~-8.39/-8.30/-8.50/-8.64 C; grid T ~-3.64/-3.99/-4.23/-4.35 C; gridded RH relative to liquid water ~92.509627/94.483866/95.151813/94.478945%. At original tower T/P compute e, q, QBOT, VPD and RH with respect to water and ice. User permits retaining only after verifying the **actual installed CTSM/CLM/FATES** q-to-RH/ice supersaturation guards accept them; do not clip ice RH, do not assert compatibility from model manuals alone.

## Exact known IRIDIS6 signed source directories
Under /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03:
- reports/stage12h_US-MtB_temperature_and_clock_three_year_diagnostics_20261025T054717Z_58c34b41/
- reports/stage12i_US-MtB_orography_pressure_20261025T064222Z_2944f5f6/
- science_trials/stage12j_US-MtB_QC0_elevation_aware_humidity_trial_20261025T065237Z_699cdb7f/
- reports/stage12k_US-MtB_GRID_RH_QC0_error_regime_20261025T070844Z_8ffe36dc/
- science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f/

Re-use SHA and source manifest guards in existing Stage12h, 12i, 12j, 12k scripts:
https://github.com/lyanyeung/CLM-FATES-single-site-workflows/tree/main/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage12
See the corresponding four verified Stage12H/I/J/K documents in docs/. Do not use guessed raw data filenames, time offsets or assumed station measurement heights.

## Deliverable checklist for Claude (research only)
1. Verify official site elevation, original tower PA_F and measurement height, native time convention and UTC mapping; **retrieve direct ERA5-Land grid geopotential/orography** and grid selection. Distinguish terrain vs station time vs 2m representativeness. Do not infer an approved 6-hour shift from a diagnostic MAE minimum.
2. Reproduce the original three-year QC0 truth comparisons and all four failed hypotheses. Investigate seasons/temperature/VPD error tails, pressure, low-VPD 0–0.25 hPa, long continuous bad runs, source-ERA vs independent ERA5-Land, and missing years. Validate any proposed new method against **real original VPD QC0**, with blocked-day validation and predeclared thresholds.
3. Check four Feb 2024 frozen-phase candidates and actual installed model humidity physics; physical possibility is not code acceptance. Include both water/ice saturation and original pressure/T.
4. Produce source-native **±2-hour context tables**: original tower TA_F/TA_F_QC, VPD_F/VPD_F_QC, PA_F; companion source TA_ERA/VPD_ERA; independent ERA5-Land T2m/D2m/SP and actual grid orography; RH_water, RH_ice, VPD/QBOT proposed and original, plus source SHA and provenance.
5. Present three feasible decision paths to the user (strict HOLD pending independent evidence; limited verified research subset; physically and empirically validated height-aware transfer), each with how many of the 2840 historical gaps are actually eligible, QC0 validation uncertainty, and remaining HOLD. **Do not choose or execute a repair on the user's behalf.**

**Do not touch US-Me6 or shared previous Stage12g six-site research shadows.** No model jobs, DATM, production release, or blanket file writes.
