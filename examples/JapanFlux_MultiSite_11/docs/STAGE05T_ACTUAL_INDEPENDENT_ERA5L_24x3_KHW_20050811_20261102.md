# JapanFlux Stage05T — actual first independent ECMWF ERA5-Land numeric comparison (2026-11-02)

## Operator-executed Stage05T success

The operator executed [Stage05T](../scripts/stage05/05t_inspect_independent_CDS_JP_Khw_20050811_ZIP_CSV_READONLY.py) on the SHA-pinned original CDS response ZIP previously downloaded in Stage05S:

```
STAGE05T SELF-TEST PASS | ZIP/CSV sample, source UTC, PA/TA/LW conversions; NO WRITES
STAGE05T CDS PILOT READ-ONLY INSPECTION COMPLETE
CDS_RAW_ZIP_SHA_VERIFIED 111c761e432f77c7fa287d7b9ee3d29a89405a33ece970f8ac81896ebee818b0 BYTES 1381
ZIP_MEMBERS 3 CSV_MEMBERS 3
MEMBER reanalysis-era5-land-timeseries-sfc-2m-temperatureuwt3605a.csv ROWS 24 HEADERS ['valid_time', 't2m', 'latitude', 'longitude']
MEMBER reanalysis-era5-land-timeseries-sfc-radiation-heatmgoan5md.csv ROWS 24 HEADERS ['valid_time', 'strd', 'latitude', 'longitude']
MEMBER reanalysis-era5-land-timeseries-sfc-pressure-precipitationlt7__qks.csv ROWS 24 HEADERS ['valid_time', 'sp', 'latitude', 'longitude']
DECODED_VAR_COUNTS {'2m_temperature': 24, 'surface_thermal_radiation_downwards': 24, 'surface_pressure': 24}
OBSERVED_GRID_COORDS [(33.10000000000104, 130.69999999999686)]
TARGET_SOURCE_HOURS ['14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00']
AUDIT /home/ly3n24/japanflux_stage05t/run_20261102T031049Z/stage05t_CDS_zip_and_CSV_structure_audit.json
INDEPENDENT_NUMERIC_PREVIEW /home/ly3n24/japanflux_stage05t/run_20261102T031049Z/stage05t_20050811_JP_Khw_independent_hourly_values_PROVISIONAL.tsv
NO AUTOMATIC JPF REPAIR; ALL 45 ORIGINAL SOURCE FIELD CANDIDATES HOLD
```

### Independently retrieved original ERA5-Land values

| UTC valid_time | ERA5-Land 2-m air temperature (K; converted °C) | ERA5-Land surface pressure (Pa; converted kPa) | ERA5-Land downward thermal radiation (hourly J m-2; converted mean W m-2) |
|---|---|---|---|
| 2005-08-11 17:00 | 296.372 K = **23.222°C** | 97773.43 Pa = **97.77343 kPa** | 1410804.0 J/m² = **391.89 W/m²** |
| 2005-08-11 18:00 | 296.1659 K = **23.0159°C** | 97778.28 Pa = **97.77828 kPa** | 1418890.0 J/m² = **394.136111 W/m²** |
| 2005-08-11 19:00 | 296.11188 K = **22.96188°C** | 97852.42 Pa = **97.85242 kPa** | 1449910.0 J/m² = **402.752778 W/m²** |

All three source CSVs have exactly 24 hourly records for 2005-08-11 UTC; all report the same gridded location **33.10000000000104°N, 130.69999999999686°E**. The tower's original BIF location is **33.13658°N, 130.70834°E, 196m**. The ERA5-Land grid elevation has **not** been checked, and a nearest-grid reference is **not** a tower measurement or an endorsed forcing replacement.

**Source quality inference:** This is strong independent physical-context evidence that the JPF same-release ERA-downscaled extreme selected-F values (e.g. approximately −122 and −268°C / ~48.9 and 0 kPa in the previously recorded JP-Khw Aug 2005 event) are contaminated rather than real atmospheric conditions. Note these candidate selected-F values were identified earlier in JPF source audits, not measured by the new ERA5-Land product. Use actual Stage05O field rows for exact data ties; do **not** extrapolate a precise correction to original half-hours from the three ERA5-Land hourly points.

### Unit and clock contract

ECMWF's ERA5-Land point time-series product is **hourly**, on the **nearest 0.1° land grid point**, with `valid_time` labels. `t2m` is K, `sp` is Pa, `strd` is an **hourly de-accumulated** energy per area in J/m², not an instantaneous 30-minute flux. Source: [ECMWF ERA5-Land time-series product guide](https://confluence.ecmwf.int/pages/viewpage.action?pageId=699689224) and [CDS dataset](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries).

Under the original JP-Khw BIF `UTC_OFFSET=+9` and original README `local standard time (without DST)`:
- JPF native 2005-08-12 02:30 → 2005-08-11 17:30 UTC.
- JPF native 2005-08-12 03:00 → 2005-08-11 18:00 UTC.

**Separate scientific caveat:** the conventions of the selected FLUXMET half-hour `native_start` and `TIMESTAMP_START/TIMESTAMP_END` should be confirmed before identifying whether a comparison reference is instantaneous or averaged over a given half-hour. For `strd` the ERA5-Land 18:00 UTC value represents an *hourly de-accumulated interval*, not directly the 17:30 instantaneous irradiance. The delta between hourly reference and a source 30-minute mean is only a contextual plausibility diagnostic until matching interval contracts, tower height, grid relief and downscaling are settled.

### Stage05U next analysis

[Stage05U original source selected-F vs independent UTC-hour-context join](../scripts/stage05/05u_crosscheck_Khw_original_stage05o_HOLD_with_CDS_stage05t_hourly_NO_REPAIR.py) is **published but not yet run on IRIDIS6**. It reads the already published Stage05O 27-UTC-field selected F records and Stage05T independent 72 hourly numerical rows plus its SHA-pinned original ZIP inspection audit. It verifies:

- Original 27 source-selected field rows, exact original JP-Khw 2005-08-11 UTC scope, QC=2 HOLD, original `F=ERA` equality;
- ERA5-Land 24 hours per 3 variables and common grid coordinate, source stage05T audit and same raw CDS ZIP SHA;
- Timestamp translation native JP-Khw−9h, without moving other two disputed sites;
- Original source value and native/UTC label are printed beside **two independent bracketing hourly reference values**, not an invented half-hour correction or automatic interpolation;
- Every output stays `HOLD`, with no overwrites, Slurm/CDS calls or forcing modification.

**Status:** First independent ERA5-Land source values **CONFIRMED**; model forcing and all **45** abnormal variable-level JPF candidates across **35 site×native half-hours remain HOLD**. The other 18 source flags at JP-Tef/Tmd still have the original local-solar-vs-standard clock ambiguity. JP-Tom and JP-Tgf source humidity/VPD review is pending.
