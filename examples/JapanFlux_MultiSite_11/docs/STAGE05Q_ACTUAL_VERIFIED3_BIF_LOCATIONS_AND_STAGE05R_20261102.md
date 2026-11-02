# JapanFlux Stage05Q original coordinates — actual 3/3 success and next Stage05R (2026-11-02)

## IRIDIS6 operator actual stdout

The operator executed [Stage05Q](../scripts/stage05/05q_three_site_source_BIF_LOCATION_coordinates_READONLY_NO_CDS.py), using the verified original BIF hashes and the earlier completed [Stage05P](STAGE05P_ACTUAL_54_UTC_HOURS_87_ERA5L_VARIABLE_REQUESTS_STAGE05Q_20261102.md) UTC hourly request plan. The output was:

```text
STAGE05Q SELF-TEST PASS | original BADM group coordinate integrity and source HOLD; NO WRITES
STAGE05Q 3_SITE_SOURCE_BIF_COORDINATES_VERIFIED VERIFIED 3 /3
SITE JP-Fjy VERIFIED_ORIGINAL_BIF_COORDINATES GROUPS 1 ISSUES []
SITE JP-Khw VERIFIED_ORIGINAL_BIF_COORDINATES GROUPS 1 ISSUES []
SITE JP-Yms VERIFIED_ORIGINAL_BIF_COORDINATES GROUPS 1 ISSUES []
ORIGINAL_BIF_VERIFIED_COORDINATE_ROSTER /home/ly3n24/japanflux_stage05q/run_20261102T023635Z/stage05q_original_BIF_verified3_CDS_coordinate_roster.tsv
AUDIT /home/ly3n24/japanflux_stage05q/run_20261102T023635Z/stage05q_original_BIF_location_validation.json
NO CDS CALLS, NO SLURM, NO ORIGINAL OR MODEL FORCING CHANGES
```

**Scientifically established**: the JP-Fjy, JP-Khw and JP-Yms original release source BIF bytes match the previously saved Stage05K BIF SHA256; each of the three sites has one location group with a complete, non-conflicting source `LOCATION_LAT`+`LOCATION_LONG` pair; source's `UTC_OFFSET` is +9; no original input was altered. **Important:** the pasted terminal log does not contain actual numeric latitude, longitude or site elevation. Those quantities have been preserved on IRIDIS6 in the cited coordinate roster; **do not invent or publish numeric coordinates from the PASS status alone**. Some site elevations can be optional/missing.

This is site/tower coordinate provenance verification, **NOT** verification of ERA5-Land grid cell, model topography or meteorological representativeness. For the independently retrieved ERA5-Land time-series, ECMWF states the nearest point on the 0.1-degree grid is selected, which is not necessarily exactly the input tower coordinate:
- [CDS ERA5-Land time-series data and 0.1° nearest-neighbor location convention](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries).
- [ECMWF ERA5-Land time-series product guide](https://confluence.ecmwf.int/pages/viewpage.action?pageId=699689224).

## Existing source-time/field scope

| JPF group | Source site list | Source-selected anomalous field records | Unique station×native half-hours | External lookup status |
|---|---|---:|---:|---|
| Original BIF+README standard time with +9 UTC offset | JP-Fjy, JP-Khw, JP-Yms | **27** | **21** | Site time and original BIF coordinates confirmed. ERA5-Land **not downloaded yet** |
| Original README local solar vs BIF UTC+9 conflict | JP-Tef, JP-Tmd | **18** | **14** | Native time HOLD, cannot silently map to UTC |
| Total | Five | **45** | **35** | All source anomalies HOLD; no repairs |

## Next Stage05R — merge verified original source coordinates and exact 54 UTC hours

[Stage05R SHA-gated three-site source-location + ERA5-Land hourly request join](../scripts/stage05/05r_join_stage05p_hours_and_stage05q_verified_BIF_coords_NO_CDS.py) is committed, but not yet run on the operator's real Stage05P/Stage05Q reports.

It reads ONLY existing Stage05P hourly TSV/summary and Stage05Q coordinate roster/audit JSON; verifies site membership, original BIF SHA256 values, WGS84 coordinate bounds, site/source time basis, 54 distinct site×UTC hours and 87 requested variable×hour combinations (`surface_pressure` 54, `2m_temperature` 9, `surface_thermal_radiation_downwards` 24). If anything conflicts, it fails without generating an incorrectly approved independent reference request.

Outputs (new report directory):

- `stage05r_87_originalBIF_geolocated_UTC_hour_reference_plan.tsv`: per site×UTC hour×variable, original BIF coordinate evidence plus exact UTC label, unverified grid-cell status and source event timestamps.
- `stage05r_site_UTC_day_hour_windows_NO_CDS.json`: limited site/day and individual UTC-hour windows, each paired with the original tower latitude/longitude/elevation when present. **No CDS submission and no grid-cell selection**.
- `stage05r_provenance_summary.json`: counts, input file SHA256, source scope and no-write/no-download status.

**No actual ERA5-Land values are present in any stage so far.** A separate user-authenticated CDS request will be needed to obtain external reference values and then physically assess source defects; source `*_ERA` is the JPF release's downscaled same-product ERA, not independent raw ECMWF data. CDS access terms/API request formatting must be checked at the time of retrieval, and licence/credentials must not be published in GitHub. Radiation interval time labeling and elevation differences also require checking before comparisons.

**Nothing is scientifically approved for a replacement** and no AD400/Normal400 has been triggered. JP-Tom/JP-Tgf RH/VPD source review continues to be a separate future requirement.
