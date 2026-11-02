# JapanFlux Stage05R — actual BIF-verified 3-site location + 87-hour-variable plan (2026-11-02)

## Real operator Stage05R result

The operator executed the pinned [Stage05R original BIF coordinate + stage05P hourly UTC join](../scripts/stage05/05r_join_stage05p_hours_and_stage05q_verified_BIF_coords_NO_CDS.py) against actual IRIDIS6 files. Output:

```
STAGE05R SELF-TEST PASS | original BIF SHA gate, 87 variable-hours, UTC and coordinates; NO WRITES
STAGE05R GEOLOCATED REQUEST PLAN PASS | NO CDS, NO ZIP, NO SLURM
SITE_COORDINATES_SOURCE_VERIFIED 3 /3
SITE JP-Fjy LAT 35.45454 LON 138.76225 ELEV_M 1043.0 SOURCE_BIF_SHA b59835ff3347fc17058319040155ae0bd65ae2241767c595869fff6be02adc62
SITE JP-Khw LAT 33.13658 LON 130.70834 ELEV_M 196.0 SOURCE_BIF_SHA eef29bcb9bd97874dad32469b1821b61760f3111cbc3836ad6300350b18217b4
SITE JP-Yms LAT 34.790278 LON 135.840939 ELEV_M 220.0 SOURCE_BIF_SHA 7c0a5ba5f137e28518f69ed14b255834fb5b223ac325556719abe5a55e8b0f56
SITE_UTC_HOURS 54 VARIABLE_HOUR_PAIRS 87
UTC_DAY_WINDOWS 9
VARIABLES {'surface_pressure': 54, '2m_temperature': 9, 'surface_thermal_radiation_downwards': 24}
GEOLOCATED_UTC_REQUEST_PLAN /home/ly3n24/japanflux_stage05r/run_20261102T025031Z/stage05r_87_originalBIF_geolocated_UTC_hour_reference_plan.tsv
UTC_DAY_WINDOWS /home/ly3n24/japanflux_stage05r/run_20261102T025031Z/stage05r_site_UTC_day_hour_windows_NO_CDS.json
PROVENANCE_SUMMARY /home/ly3n24/japanflux_stage05r/run_20261102T025031Z/stage05r_provenance_summary.json
NO INDEPENDENT WEATHER VALUES DOWNLOADED; ALL 45 ORIGINAL SOURCE FLAGS HOLD
```

The original site/source SHA and coordinates below are **source-grounded operator output, not unverified general-web site search**.

| Site | Original BIF lat (°N) | Original BIF lon (°E) | Original BIF altitude m | Source original BIF SHA256 |
|---|---:|---:|---:|---|
| JP-Fjy | 35.45454 | 138.76225 | 1043.0 | `b59835ff3347fc17058319040155ae0bd65ae2241767c595869fff6be02adc62` |
| JP-Khw | 33.13658 | 130.70834 | 196.0 | `eef29bcb9bd97874dad32469b1821b61760f3111cbc3836ad6300350b18217b4` |
| JP-Yms | 34.790278 | 135.840939 | 220.0 | `7c0a5ba5f137e28518f69ed14b255834fb5b223ac325556719abe5a55e8b0f56` |

**Reference request scope**: exactly **3** local-standard-time/BIF-verified sites, **9** site×UTC-day windows, **54** site×UTC-hour labels, **87** variable-hour pairs (surface pressure 54, 2m temperature 9, downward longwave 24). A CDS **time-series** request selects complete date ranges; making nine site/day API requests would download all **24 hours per day**, possibly more than the sparse 87 variable-hour pairs; post-processing must subset to the verified Stage05R UTC labels, not assume a sparse file. All three sites have known original tower elevation; **ERA5-Land elevation and grid-cell representativeness remain unverified**.

## Data source cross-check 2026-11-02

Verified directly against current Copernicus Climate Data Store and ERA5-Land time-series product guide:

- [ERA5-Land hourly time-series dataset download form](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries?tab=download). Collection ID `reanalysis-era5-land-timeseries`. Data selection: variable(s), geographical **location**, **start/end date**, output **CSV or NetCDF**. A user must accept the terms through CDS before retrieval.
- [ECMWF ERA5-Land time-series product user guide](https://confluence.ecmwf.int/pages/viewpage.action?pageId=699689224). UTC hourly (24 records/day); nearest **0.1°** grid point to requested location, not necessarily same tower elevation. Timeseries accumulated variables such as `surface_thermal_radiation_downwards` are **hourly de-accumulated J m⁻²**, divide by 3600 seconds only after checking the validity/end-hour labels.
- [Live independently documented CDS API time-series example](https://popecol.org/docs/env-data/index.html): `cdsapi.Client().retrieve('reanalysis-era5-land-timeseries', {'variable':[...], 'location': {'latitude':..., 'longitude':...}, 'date':'YYYY-MM-DD/YYYY-MM-DD', 'data_format':'netcdf'}, target)`. The current CDS download form offers `csv` too. The example is useful to check the request-field shape, not to infer actual site values.

These sources do **not** imply independent ECMWF values have already been downloaded. The original JPF embedded `*_ERA` variables are **linearly regressed/downscaled within the same release**, and cannot substitute for independently retrieved ECMWF ERA5-Land reference.

## Stage05S first independent pilot (committed code, not run by operator yet)

[Stage05S single-day ERA5-Land time-series preview and explicit opt-in pilot retrieval](../scripts/stage05/05s_ERA5Land_timeseries_one_day_CDS_pilot_opt_in.py) accepts the genuine Stage05R 9-window JSON and source provenance JSON:

1. **Default --preview**: validates original site membership, nine windows, 54 UTC site-hours, 87 variable-hour provenance, and exact original BIF/UTC source gate; writes a new JSON listing the **nine site/day requests**. **No CDS, no credential handling, no Slurm, no edits**.
2. **--submit --site JP-Khw --utc-date 2005-08-11** (operator must invoke explicitly): constructs one **single-site, one-day CDS time-series API** request with the verified original site coordinates and variables required for that date, uses user's private `~/.cdsapirc` via installed `cdsapi`. It records downloaded raw response in an isolated folder, with SHA256 and payload-magic check. Does not echo the CDS key, run other dates, parse/overwrite meteorological sources, or approve a repair.
3. **No automatic expansion**: review API output format, request success, actual UTC timestamps, returned 0.1-degree grid location, and variable units and radiation interval semantics before any further requests.

The user may need to separately configure their private CDS API profile and accept the ERA5-Land timeseries CC-BY data licence at the [CDS portal](https://cds.climate.copernicus.eu/). Never paste API credentials into GitHub, logs or ChatGPT. If the CDS API schema changes, inspect the dataset's up-to-date **Show API Request** snippet and modify Stage05S; do not bypass source/provenance scientific gates.

## Unresolved science

The Stage05I **45 source-selected field anomalies at 35 site×native half-hours are still HOLD**. Only **27** fields / **21** distinct source-half-hours at Fjy/Khw/Yms have trusted local standard time UTC mapping. **18** fields / **14** unique source-half-hours at JP-Tef/Tmd have original `local solar time` README, conflicting with general ONEFlux local-standard convention; cannot simply map their native time via UTC+9.

No ERA5-Land values have been obtained, no Slurm, and original package/forcing/model cases remain unchanged. No AD400 or Normal400 authorised. Separate JP-Tom/Tgf VPD/RH source provenance is outstanding.
