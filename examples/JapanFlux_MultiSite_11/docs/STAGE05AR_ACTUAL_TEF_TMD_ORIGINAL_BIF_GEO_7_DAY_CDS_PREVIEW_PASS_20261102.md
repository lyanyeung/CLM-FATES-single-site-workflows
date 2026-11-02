# JapanFlux Stage05AR — ACTUAL two source JPF BIF geolocations / 7 scoped UTC candidate CDS site-days PASS (2026-11-02)

## Original IRIDIS6 operator audit, source data unchanged

```text
=== DOWNLOAD PINNED SOURCE AUDIT ===
STAGE05K_METADATA_DIR=/home/ly3n24/japanflux_stage05k
STAGE05Q SELF-TEST PASS | original BADM group coordinate integrity and source HOLD; NO WRITES
STAGE05AR SELF-TEST PASS | original BIF SHA-locked JP-Tef/Tmd LAT/LONG/ELEV, exactly seven user JST+9 candidate CDS days, NO CDS/WRITES
STAGE05AR TWO ORIGINAL TEF/TMD BIF LOCATION & 7 CANDIDATE CDS DAYS PASS | NO DOWNLOAD / SLURM / REPAIR
SOURCE_BIF_SITE JP-Tef LAT 45.055808 LON 142.107122 ELEV_M 79.47 SOURCE_SHA256 78f02f04892b5731cd33e57b57d00e71bdff4c743ba94f5dd6c69dbd98be0f26
SOURCE_BIF_SITE JP-Tmd LAT 42.735911 LON 141.523147 ELEV_M 117.0 SOURCE_SHA256 d5d99b265b6f4eaa29a059f7cc13ceb0e5f101979276ea090c4ec6cf5dc5c87b
USER_JST_UTCPLUS9_CANDIDATE_UTC_DAYS 7 ORIGINAL_CLOCK_NOT_PROVEN
PREVIEW_CDS_NOT_SUBMITTED JP-Tef 2011-12-16 VARIABLES surface_thermal_radiation_downwards HOURS 18:00,19:00,20:00,21:00,22:00,23:00
PREVIEW_CDS_NOT_SUBMITTED JP-Tef 2011-12-17 VARIABLES surface_thermal_radiation_downwards HOURS 00:00,01:00
PREVIEW_CDS_NOT_SUBMITTED JP-Tef 2022-04-08 VARIABLES surface_thermal_radiation_downwards HOURS 14:00,15:00,16:00,17:00,18:00,19:00,20:00,21:00
PREVIEW_CDS_NOT_SUBMITTED JP-Tmd 2005-08-11 VARIABLES 2m_temperature,surface_pressure,surface_thermal_radiation_downwards HOURS 14:00,15:00,16:00,17:00,18:00,19:00,20:00,21:00,22:00
PREVIEW_CDS_NOT_SUBMITTED JP-Tmd 2011-12-16 VARIABLES surface_pressure HOURS 18:00,19:00,20:00,21:00,22:00,23:00
PREVIEW_CDS_NOT_SUBMITTED JP-Tmd 2011-12-17 VARIABLES surface_pressure HOURS 00:00,01:00,02:00
PREVIEW_CDS_NOT_SUBMITTED JP-Tmd 2022-04-08 VARIABLES surface_pressure HOURS 14:00,15:00,16:00,17:00,18:00,19:00,20:00,21:00,22:00
BIF_COORDINATE_ROSTER /home/ly3n24/japanflux_stage05ar/run_20261102T222416Z/stage05ar_Tef_Tmd_original_BIF_verified2_CDS_coordinates.tsv
SEVEN_DAY_CDS_PREVIEW /home/ly3n24/japanflux_stage05ar/run_20261102T222416Z/stage05ar_7_user_JSTplus9_site_UTC_day_CDS_preview_ONLY.json
SOURCE_TIME_AND_GEO_HOLD_SUMMARY /home/ly3n24/japanflux_stage05ar/run_20261102T222416Z/stage05ar_source_BIF_coordinates_7_day_hypothesis_HOLD_summary.json
ALL_45_SOURCE_QC2_FIELDS_HOLD; NO CDS / FORCING / SLURM / REPLACEMENTS
```

Two **original site BIF `LOCATION_LAT`, `LOCATION_LONG`, `LOCATION_ELEV`** WGS84 source records have been SHA256-matched to prior exact Stage05K original metadata and re-extracted from the source JPF package via the pinned Stage05Q location parser. These are **source tower coordinates** not ERA5-Land returned grid coordinates; the grid elevation and tower/grid meteorological representativeness remain unverified.

| Site | Original BIF lat | Original BIF lon | Original BIF elevation | Source BIF SHA256 |
|---|---:|---:|---:|---|
| JP-Tef | 45.055808 | 142.107122 | 79.47 m | `78f02f04892b5731cd33e57b57d00e71bdff4c743ba94f5dd6c69dbd98be0f26` |
| JP-Tmd | 42.735911 | 141.523147 | 117 m | `d5d99b265b6f4eaa29a059f7cc13ceb0e5f101979276ea090c4ec6cf5dc5c87b` |

The source clock is the operator selected **`JST_UTC_PLUS9_DIAGNOSTIC_ONLY`** hypothesis: candidate UTC = original source native timestamp − 9 hours; original source JPF JP-Tef/Tmd 75-line README explicitly states local solar time, so the actual source timebase has not been proved from release documentation. Prior Stage05AM/AN/AO original 18 QC2 field checks were successful; 27 other source fields independently assessed; all **45 original QC2 field candidates retain science HOLD**.

## Next Stage05AS (script published; real CDS download not yet observed)

[Stage05AS one-day opt-in ERA5-Land time-series original ZIP/CSV retrieval & science content validation](../scripts/stage05/05as_Tef_Tmd_source_BIF_JST_candidate_7day_ONE_DAY_CDS_ERA5Land_OPT_IN.py) validates the **actual Stage05AR** report JSON, ensures exact original BIF source SHA/coordinates, exact seven candidate source site/day/variable/hour scopes and all science holds, before performing any explicit user CDS action.

- Safe no-CDS preflight: script without `--submit` prints seven validated site/day request candidate records and writes no original data.
- One pilot allowed **JP-Tef UTC candidate date 2011-12-16** and `surface_thermal_radiation_downwards` only. User explicitly runs `--submit --site JP-Tef --utc-date 2011-12-16` with available `~/.cdsapirc` and accepted CDS licence.
- CDS dataset `reanalysis-era5-land-timeseries`, original source tower BIF location `45.055808°N,142.107122°E`, full UTC 2011-12-16 00:00..23:00 requested, not just 18:00–23:00.
- Preserve returned download at unique `$HOME/japanflux_stage05as/downloads/JP-Tef_ERA5Land_timeseries_20111216_CSV_response.zip`. Download to `.zip.partial` first. Check ZIP CRC, 24 nonduplicated UTC hours, CSV variable `strd`, plausible deaccumulated hour-long J m⁻² and independent nearest grid ~0.1°, then promote to ZIP. Failed/invalid payload left as partial, without overwrite or automatic retry.
- ECMWF `reanalysis-era5-land-timeseries` `strd` is **already de-accumulated hourly J m⁻²**, so /3600 to obtain mean W m⁻², never second hourly differencing. Timestamp `valid_time` labels interval end, not a contemporaneous 30-minute tower point; source tower and returned grid elevation cannot be equated.
- JP-Tef source QC2 flags at 2011-12-17 local 06:00/06:30 correspond to JST-hypothesis UTC 2011-12-16 21:00/21:30. Adjacent 2011-12-17 reference model hours are **NOT** validated by a one-day CDS request. The next step after this first pilot is separately request/validate the 2011-12-17 UTC day, and only then do complete two-day physical context checks.
- Script may be tested syntactically and via offline `--self-test` on IRIDIS before any submission. It was NOT run with actual Stage05AR input/CDS in this authoring session.
- No original JPF source ZIP/forcing/model changes, no Slurm/AD400 and no half-hour repairs; all original 45 science field HOLD preserved.
