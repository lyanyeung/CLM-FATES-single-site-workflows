# JapanFlux Stage05AQ — ACTUAL operator JST+9 hypothesis preview PASS, 18 native source fields and seven candidate ERA5-Land UTC days (2026-11-02)

## Actual IRIDIS6 result

The operator executed the source- and Git SHA-pinned [Stage05AQ](../scripts/stage05/05aq_Tef_Tmd_operator_JST_plus9_18_QC2_CANDIDATE_UTC_ERA5L_PLAN_NO_DOWNLOAD.py) with the explicit `--operator-time-hypothesis JST_UTC_PLUS9_DIAGNOSTIC_ONLY`. Real output:

```text
STAGE05AQ SELF-TEST PASS | user JST+9 hypothesis, 18 native QC2 -> candidate UTC only, bounded ERA5L preview; no CDS/forcing/repairs
STAGE05AQ OPERATOR JST+9 CANDIDATE UTC 18 SOURCE FIELDS PASS | NO CDS / FORCING / SLURM
CANDIDATE_UTC_FIELDS 18 ORIGINAL_CLOCK_NOT_SOURCE_PROVEN REMAIN_HOLD 45
SITE_DAY_CDS_PREVIEWS 7
DAY_CANDIDATE_NOT_REQUESTED JP-Tef 2011-12-16 VARS surface_thermal_radiation_downwards HOURS 18:00,19:00,20:00,21:00,22:00,23:00
DAY_CANDIDATE_NOT_REQUESTED JP-Tef 2011-12-17 VARS surface_thermal_radiation_downwards HOURS 00:00,01:00
DAY_CANDIDATE_NOT_REQUESTED JP-Tef 2022-04-08 VARS surface_thermal_radiation_downwards HOURS 14:00,15:00,16:00,17:00,18:00,19:00,20:00,21:00
DAY_CANDIDATE_NOT_REQUESTED JP-Tmd 2005-08-11 VARS 2m_temperature,surface_pressure,surface_thermal_radiation_downwards HOURS 14:00,15:00,16:00,17:00,18:00,19:00,20:00,21:00,22:00
DAY_CANDIDATE_NOT_REQUESTED JP-Tmd 2011-12-16 VARS surface_pressure HOURS 18:00,19:00,20:00,21:00,22:00,23:00
DAY_CANDIDATE_NOT_REQUESTED JP-Tmd 2011-12-17 VARS surface_pressure HOURS 00:00,01:00,02:00
DAY_CANDIDATE_NOT_REQUESTED JP-Tmd 2022-04-08 VARS surface_pressure HOURS 14:00,15:00,16:00,17:00,18:00,19:00,20:00,21:00,22:00
QC2_CANDIDATE_UTC JP-Tef 201112170600 201112162100 LW_IN F 26.164
QC2_CANDIDATE_UTC JP-Tef 201112170630 201112162130 LW_IN F 26.164
QC2_CANDIDATE_UTC JP-Tef 202204090200 202204081700 LW_IN F 26.164
QC2_CANDIDATE_UTC JP-Tef 202204090230 202204081730 LW_IN F 26.164
QC2_CANDIDATE_UTC JP-Tmd 200508120200 200508111700 LW_IN F 28.519
QC2_CANDIDATE_UTC JP-Tmd 200508120230 200508111730 LW_IN F 28.519
QC2_CANDIDATE_UTC JP-Tmd 200508120230 200508111730 PA F 49.502
QC2_CANDIDATE_UTC JP-Tmd 200508120230 200508111730 TA F -132.399
QC2_CANDIDATE_UTC JP-Tmd 200508120300 200508111800 PA F 0.0
QC2_CANDIDATE_UTC JP-Tmd 200508120300 200508111800 TA F -284.222
QC2_CANDIDATE_UTC JP-Tmd 200508120330 200508111830 PA F 49.506
QC2_CANDIDATE_UTC JP-Tmd 200508120330 200508111830 TA F -132.688
QC2_CANDIDATE_UTC JP-Tmd 201112170630 201112162130 PA F 49.448
QC2_CANDIDATE_UTC JP-Tmd 201112170700 201112162200 PA F 0.0
QC2_CANDIDATE_UTC JP-Tmd 201112170730 201112162230 PA F 49.514
QC2_CANDIDATE_UTC JP-Tmd 202204090230 202204081730 PA F 49.616
QC2_CANDIDATE_UTC JP-Tmd 202204090300 202204081800 PA F 0.0
QC2_CANDIDATE_UTC JP-Tmd 202204090330 202204081830 PA F 49.579
CANDIDATE_UTC_TSV /home/ly3n24/japanflux_stage05aq/run_20261102T221456Z/stage05aq_18_original_QC2_JST_PLUS9_candidate_UTC_SCIENCE_HOLD.tsv
SOURCE_BOUNDED_CDS_PREVIEW /home/ly3n24/japanflux_stage05aq/run_20261102T221456Z/stage05aq_Tef_Tmd_candidate_CDS_site_UTC_days_PREVIEW_ONLY.json
SCIENCE_TIME_ASSUMPTION_LEDGER /home/ly3n24/japanflux_stage05aq/run_20261102T221456Z/stage05aq_45_original_source_fields_time_assumption_NO_REPAIR.json
ALL_45_QC2_FIELDS_HOLD; EXTERNAL_CLOCK_PROOF_STILL_MISSING; NO REPLACEMENTS
```

**Interpretation:** The operator elected JST UTC+9 as a source clock hypothesis; original JPF Tef/Tmd 75-line README explicitly claims local solar time. The arithmetic candidate UTC times are correctly derived via native minus nine hours, but **not source-proven UTC**. **No independent ERA5-Land CDS downloads** for these seven candidate site-days were performed by Stage05AQ.

## Exact next Stage05AR

Before any external request, source-verify JP-Tef/JP-Tmd tower site latitude, longitude, and optional elevation using the **original nested JPF BIF** (`LOCATION_LAT`, `LOCATION_LONG`, `LOCATION_ELEV` grouped together), original site `UTC_OFFSET=9`, and optionally source BIF SHA256 against previously extracted Stage05K reports. Reuse the previously actual-used [Stage05Q original source BIF location parser](../scripts/stage05/05q_three_site_source_BIF_LOCATION_coordinates_READONLY_NO_CDS.py), without assuming JP-Tef or JP-Tmd locations from ICOS/web references.

Once original source positions are verified, attach them to exactly seven Stage05AQ candidate site×UTC-days and original per-day variable subsets. Flag all requests with `JST_UTC_PLUS9_DIAGNOSTIC_ONLY`, retain original README solar time conflict, and keep site grid elevation/nearest model grid cell unverified until returned.

Historical Stage05S generic downloader explicitly excludes Tef/Tmd and must **not** be silently patched to accept them; create a separate bounded, user-confirmed source-verified one-site-one-day request stage afterward. No forcing/Slurm/AD400 updates or original source ZIP edits; **45/45** original QC2 fields science HOLD.
