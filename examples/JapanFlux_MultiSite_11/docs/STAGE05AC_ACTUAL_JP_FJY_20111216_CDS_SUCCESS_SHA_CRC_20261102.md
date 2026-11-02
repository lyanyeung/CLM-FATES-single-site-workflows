# JapanFlux Stage05AC — actual first December 2011 ERA5-Land CDS retrieval success and full source audit (2026-11-02)

## Actual operator output

The operator explicitly requested only **JP-Fjy, 2011-12-16 UTC**, independent dataset `reanalysis-era5-land-timeseries`, original JPF BIF tower location `35.45454°N,138.76225°E`, variable **`surface_pressure`**. The original [Stage05S](../scripts/stage05/05s_ERA5Land_timeseries_one_day_CDS_pilot_opt_in.py) safe one-day, no-overwrite request was accompanied by a Stage05AB original six-day absence provenance check.

```text
SIX-DAY ORIGINAL ABSENCE AUDIT VERIFIED
STAGE05S SELF-TEST PASS | 3-site/9-day source gates, explicit pilot only, NO NETWORK OR WRITES
=== REQUEST JP-Fjy 2011-12-16 ===
2026-11-02 12:47:05,466 INFO Request ID is 987925b9-f0ed-454c-9ef2-bd90170254fc
2026-11-02 12:47:05,524 INFO status has been updated to accepted
2026-11-02 12:47:19,024 INFO status has been updated to running
2026-11-02 12:47:26,682 INFO status has been updated to successful
STAGE05S EXPLICIT ONE-DAY CDS PILOT | NO MODEL/SLURM
DATASET reanalysis-era5-land-timeseries SITE JP-Fjy UTC_DATE 2011-12-16
REQUEST_NONSECRET {"data_format": "csv", "date": "2011-12-16/2011-12-16", "location": {"latitude": 35.45454, "longitude": 138.76225}, "variable": ["surface_pressure"]}
CDS_PILOT_RESPONSE_WRITTEN /home/ly3n24/japanflux_stage05s/downloads/JP-Fjy_ERA5Land_timeseries_20111216_CSV_response.zip
DETECTED_PAYLOAD ZIP BYTES 493 SHA256 cc172d7c18e7b7b5199aa7cccc8b941c6115863861860f0618d8b33d4f577c9a
SCIENCE_HOLD: No field contents have yet been verified for UTC, units, grid coordinates or physical plausibility
NO ORIGINAL DATA / FORCING / MODEL CHANGES
```

The user then ran the original, SHA-pinned [Stage05AB](../scripts/stage05/05ab_inventory_six_2011_existing_CDS_ZIP_partial_CRC_READONLY.py) source-gated six-day re-inventory, and the **actual contents** passed:

```text
STAGE05AB SIX 2011-CDS DAY EXISTING FILES/CRC/TIME/GRID SOURCE INVENTORY PASS | NO CDS / SLURM / REPAIR
DAY JP-Fjy 2011-12-16 ZIP REGULAR PARTIAL ABSENT CSV_ZIP_STATUS COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR SHA256 cc172d7c18e7b7b5199aa7cccc8b941c6115863861860f0618d8b33d4f577c9a GRID 35.50000000000107 138.79999999999643 NEXT REUSE_VALID_EXISTING_ZIP_FOR_SEPARATE_SOURCE_QC2_REVIEW_NO_REDOWNLOAD
DAY JP-Fjy 2011-12-17 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT SHA256 NONE GRID NONE NONE NEXT NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT
DAY JP-Khw 2011-12-16 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT SHA256 NONE GRID NONE NONE NEXT NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT
DAY JP-Khw 2011-12-17 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT SHA256 NONE GRID NONE NONE NEXT NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT
DAY JP-Yms 2011-12-16 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT SHA256 NONE GRID NONE NONE NEXT NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT
DAY JP-Yms 2011-12-17 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT SHA256 NONE GRID NONE NONE NEXT NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT
COUNTS {'REUSE_VALID_EXISTING_ZIP_FOR_SEPARATE_SOURCE_QC2_REVIEW_NO_REDOWNLOAD': 1, 'NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT': 5}
INVENTORY /home/ly3n24/japanflux_stage05ac/inventory_20261102T124727Z/stage05ab_six_2011_CDS_archive_existing_payload_inventory_HOLD.tsv
SOURCE_AUDIT /home/ly3n24/japanflux_stage05ac/inventory_20261102T124727Z/stage05ab_six_2011_CDS_original_archive_science_audit.json
NO CDS CALLS, NO ORIGINAL ZIP/SOURCE/FORCING CHANGES; ALL 45 FIELDS HOLD
```

This proves **one real accepted/running/successful CDS request transaction plus a 493-byte ZIP whose SHA, CRC, source/variable CSV members, all 24 UTC time labels and single nearest grid cell passed the existing independent source-science audit**. It does **not** prove that a source-specific three-hour comparison has already been carried out for any of the 2011 original JPF QC2 anomalies.

## Coverage and next steps

- Reference day payloads validated: **4/9**, original 2005 three days and 2011-12-16 JP-Fjy.
- Still without verified payload: **5/9**; JP-Fjy 2011-12-17, JP-Khw 2011-12-16/17, JP-Yms 2011-12-16/17.
- Verified original source QC2 anomalies with strong independent context: **16/45** variable records at 11 site×native half-hours: Fjy3 + Khw8 + Yms5 (2005); **11** UTC-convertible 2011 anomalies still require independent per-event comparison; **18** Tef/Tmd original local-solar timebase science HOLD.
- Separate science gate: complete the JP-Fjy 2011-12-17 UTC request first to cover any cross-UTC-midnight original halfhour candidates. Then check SHA/CRC/complete two-day hourly pressure and original F=ERA QC2 time alignment in a read-only script before updating scientific field evidence counts.
- The site is at **1043m original BIF tower elevation**; independent ERA5-Land nearest grid elevation has NOT been checked, so even large site-grid pressure differences are **not automatically corrected or attributed to one mechanism**.
- Still **all 45 source fields on HOLD**; no model, forcing, original ZIP, AD400 or Slurm changes.
