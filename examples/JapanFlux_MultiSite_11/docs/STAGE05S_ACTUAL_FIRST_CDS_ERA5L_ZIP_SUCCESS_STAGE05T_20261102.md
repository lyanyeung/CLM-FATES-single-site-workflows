# JapanFlux Stage05S ACTUAL ERA5-Land CDS pilot success, Stage05T native ZIP/CSV scientific review (2026-11-02)

## Actual CDS independently sourced download completed

The operator ran Stage05S first in default preview mode and then explicitly requested **one** 24-hour UTC-day ERA5-Land time-series subset for JP-Khw. Their stdout establishes:

```text
STAGE05S SELF-TEST PASS | 3-site/9-day source gates, explicit pilot only, NO NETWORK OR WRITES
STAGE05S PREVIEW VALIDATION PASS | NO CDS / ZIP / SLURM / FORCING
VERIFIED_SITES JP-Fjy,JP-Khw,JP-Yms UTC_DAY_REQUESTS 9
SOURCE_SCOPE_SITE_HOURS 54 VARIABLE_HOURS 87
PILOT JP-Khw 2005-08-11 VARS 2m_temperature,surface_pressure,surface_thermal_radiation_downwards
PREVIEW_REQUEST_JSON /home/ly3n24/japanflux_stage05s/run_20261102T030141Z/stage05s_9_CDS_timeseries_one_day_requests_PREVIEW_ONLY.json

STAGE05S EXPLICIT ONE-DAY CDS PILOT | NO MODEL/SLURM
DATASET reanalysis-era5-land-timeseries SITE JP-Khw UTC_DATE 2005-08-11
REQUEST_NONSECRET {"data_format": "csv", "date": "2005-08-11/2005-08-11", "location": {"latitude": 33.13658, "longitude": 130.70834}, "variable": ["2m_temperature", "surface_pressure", "surface_thermal_radiation_downwards"]}
2026-11-02 03:01:50,268 INFO Request ID is ee5503ed-0bff-4eb1-8858-7c7b2d10b263
2026-11-02 03:01:50,338 INFO status has been updated to accepted
2026-11-02 03:02:11,661 INFO status has been updated to successful
CDS_PILOT_RESPONSE_WRITTEN /home/ly3n24/japanflux_stage05s/downloads/JP-Khw_ERA5Land_timeseries_20050811_CSV_response.zip
DETECTED_PAYLOAD ZIP BYTES 1381 SHA256 111c761e432f77c7fa287d7b9ee3d29a89405a33ece970f8ac81896ebee818b0
SCIENCE_HOLD: No field contents have yet been verified for UTC, units, grid coordinates or physical plausibility
NO ORIGINAL DATA / FORCING / MODEL CHANGES
```

**This is the first independently downloaded ECMWF ERA5-Land product** in the user's JapanFlux workflow; it is not a same-release JPF `ERA5_HH` field. The request has finished successfully and an original CDS response ZIP (1,381 bytes, SHA256 above) was received, but the **contents have not yet been opened/verified by the operator**. The response may contain one or more CSVs (variable groups) and must be checked before numerical scientific interpretation. The general ECMWF service notice printed in the log does **not** imply this specific request failed; the explicit accepted→successful status and saved artifact show successful retrieval.

Original source trace:
- JP-Khw tower: **33.13658°N, 130.70834°E**, original BIF elevation **196m**, original BIF SHA256 `eef29bcb9bd97874dad32469b1821b61760f3111cbc3836ad6300350b18217b4`.
- The original JPF source native 2005-08-12 02:30 and 03:00 correspond to UTC **2005-08-11 17:30 and 18:00**, based on original README `local standard time (without DST)` plus original `UTC_OFFSET=+9`.
- The actual Stage05S pilot fetched **JP-Khw 2005-08-11 (UTC) entire day**, not only the nine 14:00–22:00 requested UTC hours, because the ERA5-Land timeseries product accepts day intervals.
- Original source `*_F` selected anomalies with QC2 and same-release `*_ERA`: JP-Khw 2005-08-12 02:30 `TA_F=-122.144°C`, `PA_F=48.912 kPa`; 03:00 `TA_F=-268.276°C`, `PA_F=0 kPa`; neighboring `LW_IN_F=39.171 W/m²`. These are still source scientific HOLD; independent product does NOT automatically replace them.

## Cross-check against ECMWF/Copernicus reference documentation

- [ERA5-Land hourly time-series CDS portal](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries?tab=download): the time-series dataset offers point location, date range, CSV and NetCDF data.
- [ECMWF ERA5-Land hourly time-series PUG](https://confluence.ecmwf.int/pages/viewpage.action?pageId=699689224): 0.1° nearest-grid location selection, 24 hourly samples per day, processed cloud-optimized Zarr output to requested CSV/NetCDF. Accumulation variables (downward thermal radiation) have been **hourly de-accumulated**; do not treat them as instantaneous half-hour measurements. Independent raw units TA K, PA Pa and longwave de-accumulated J/m² (hourly mean W/m² is J/m² divided by 3600 s), subject to checking returned CSV schema and interval labels.

The returned grid latitude and longitude may differ from the tower input coordinate (nearest 0.1° grid), and no model-grid elevation/height adjustment has been validated. The CDS response needs actual unit, time and grid checks first.

## Stage05T next step — read-only original CDS ZIP source provenance inspection

[Stage05T](../scripts/stage05/05t_inspect_independent_CDS_JP_Khw_20050811_ZIP_CSV_READONLY.py) is committed, **not yet run by the operator**. It requires the **exact downloaded 1,381-byte original ZIP** with SHA256 `111c761e432f77c7fa287d7b9ee3d29a89405a33ece970f8ac81896ebee818b0` and the already validated Stage05R 87-row timestamp/coordinate plan. It:

1. Verifies original CDS ZIP SHA256 and source BIF identity **before** parsing any ZIP member.
2. Reads ZIP members read-only, listing original member names, CSV headers, sample raw rows, date/time labels, reported grid coordinates if available and recognized variables. Fails/holds on unexpected formats; never modifies original source files.
3. For recognizable CSV variables, records the raw and cautiously converted independent hourly TA (K→°C), PA (Pa→kPa), LW_IN (hourly de-accumulated J/m²→W/m²).
4. Prints the independent **17:00, 18:00 and 19:00 UTC** numerical context for source 2005-08-12 02:30/03:00 JST anomalies. At 17:30 UTC, a half-hour JPF source value cannot be matched to a single independently observed hourly ERA5-Land value without a considered temporal interpolation/representativeness rule.
5. Emits a **derived JSON/TSV** report with units/grid and time interpretation explicitly provisional, never applying a repair, editing forcing, or running Slurm.

The script has been published but its self-test and actual CDS ZIP decoding are **not yet observed on IRIDIS6**. If an unexpected CSV header/format is encountered, preserve raw schema/rows and create a narrowly sourced follow-up parser, not guesses or fabricated data.

## Science status

- **Stage05S actual CDS pilot successful**; one raw CDS ZIP downloaded, SHA256 pinned; CSV content not yet vetted.
- Stage05R three-station original BIF locations, nine UTC-date windows, 54 site×UTC hours / 87 variable-hour selections verified.
- **45 source-selected abnormal variable rows/35 site×half-hours remain HOLD.** Of these 27 fields at Fjy/Khw/Yms have trusted UTC; 18 fields at Tef/Tmd still have unresolved local-solar-vs-standard wording. No automatic correction or model submission.
- JP-Tom and JP-Tgf humidity/VPD original product provenance remains separately outstanding.
