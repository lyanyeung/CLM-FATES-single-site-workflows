# JapanFlux Stage05AB — actual all six December 2011 CDS site-day payloads absent (2026-11-02)

## Actual operator-executed read-only inventory

The operator ran the SHA-pinned [Stage05AB](../scripts/stage05/05ab_inventory_six_2011_existing_CDS_ZIP_partial_CRC_READONLY.py) using the completed original source Stage05AA six-day science ledger and Stage05R 87-row original site/hour/variable BIF provenance. Actual terminal output:

```text
STAGE05AB SELF-TEST PASS | 6 exact site-days, 8 expected CSV members, hold existing .zip/.partial/.csv; NO NETWORK/WRITES
STAGE05AB SIX 2011-CDS DAY EXISTING FILES/CRC/TIME/GRID SOURCE INVENTORY PASS | NO CDS / SLURM / REPAIR
DAY JP-Fjy 2011-12-16 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT SHA256 NONE GRID NONE NONE NEXT NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT
DAY JP-Fjy 2011-12-17 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT SHA256 NONE GRID NONE NONE NEXT NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT
DAY JP-Khw 2011-12-16 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT SHA256 NONE GRID NONE NONE NEXT NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT
DAY JP-Khw 2011-12-17 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT SHA256 NONE GRID NONE NONE NEXT NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT
DAY JP-Yms 2011-12-16 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT SHA256 NONE GRID NONE NONE NEXT NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT
DAY JP-Yms 2011-12-17 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT SHA256 NONE GRID NONE NONE NEXT NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT
COUNTS {'NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT': 6}
INVENTORY /home/ly3n24/japanflux_stage05ab/run_20261102T123642Z/stage05ab_six_2011_CDS_archive_existing_payload_inventory_HOLD.tsv
SOURCE_AUDIT /home/ly3n24/japanflux_stage05ab/run_20261102T123642Z/stage05ab_six_2011_CDS_original_archive_science_audit.json
NO CDS CALLS, NO ORIGINAL ZIP/SOURCE/FORCING CHANGES; ALL 45 FIELDS HOLD
```

No regular ZIP, ZIP partial, alternative CSV, or alternate NetCDF response file was reported present for any of the six 2011 site×UTC dates. This observation is **timestamp-scoped to the actual original download directory at the Stage05AB execution**, not a guarantee no files will appear later. **All six requests are eligible for individual operator-authorized CDS submission**, subject to ongoing CDS credential and license requirements and Stage05S no-overwrite protections. Stage05AB did not submit a CDS request.

| Site | UTC date | Required independent ERA5-Land variables |
|---|---|---|
| JP-Fjy | 2011-12-16 | surface_pressure |
| JP-Fjy | 2011-12-17 | surface_pressure |
| JP-Khw | 2011-12-16 | surface_pressure |
| JP-Khw | 2011-12-17 | surface_pressure |
| JP-Yms | 2011-12-16 | surface_pressure + surface_thermal_radiation_downwards |
| JP-Yms | 2011-12-17 | surface_pressure + surface_thermal_radiation_downwards |

## Decision and next operator action

Start with **one independently source-scoped CDS request**, **JP-Fjy 2011-12-16 UTC**, using the original [Stage05S](../scripts/stage05/05s_ERA5Land_timeseries_one_day_CDS_pilot_opt_in.py) with `--site JP-Fjy --utc-date 2011-12-16 --submit`. The existing Stage05R source-BIF site/day/variables request plan is already validated, and Stage05S refuses any existing target or `.zip.partial`. After a real download, use the same [Stage05AB](../scripts/stage05/05ab_inventory_six_2011_existing_CDS_ZIP_partial_CRC_READONLY.py) with a new derived output directory to confirm real ZIP CRC, one CSV×24 hourly UTC rows, `sp` variable in Pa, grid location and actual ZIP SHA256. No pressure anomaly interpretation or repair before full source-hour context is available and actual grid altitude is assessed (JP-Fjy tower BIF elevation 1043 m).

A historical site-day request manifest lists both 2011-12-16 and 2011-12-17 due to 2011 December source candidate events crossing UTC-day boundaries. **One 24-hour response must not be treated as sufficient for event contexts extending to 2011-12-17**; preserve any missing context as science HOLD until the second day has been independently verified.

## Science portfolio state after Stage05AB

- 45 original source selected `F=ERA` QC2 anomalous field records at 35 station×native half-hour times, all HOLD.
- 16/45 original records strongly contradicted by independent ERA5-Land nearby-hour physical context (JP-Fjy 3 / JP-Khw 8 / JP-Yms 5; 11 unique station×half-hour timestamps).
- 11/45 other original fields have source-confirmed local-standard UTC+9 but independent context is not yet checked.
- 18/45 JP-Tef and JP-Tmd records unresolved local-solar vs local-standard time origin.
- 3/9 external reference site×UTC-day payloads passed earlier SHA/CRC/schema/time/grid audit (JP-Fjy/Khw/Yms 2005-08-11); two corresponding CDS transaction success logs observed (Khw,Yms), but prior JP-Fjy original CDS request ID remains unavailable.
- Six December 2011 source site×UTC-day response payloads **all absent** in the Stage05AB inspected directory. No model/forcing edits, Slurm, CDS downloads or repairs during Stage05AB.

The source-validated read-only six-day inventory must not be conflated with an approval to replace 30-minute JPF tower observations by gridded hourly ERA5-Land.
