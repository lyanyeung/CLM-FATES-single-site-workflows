# JapanFlux Stage05AF — actual JP-Khw 2011-12-16 CDS success and independent source payload verified (2026-11-02)

## Actual operator result

Stage05AE original science preflight passed: **19/45** independently evidenced original JPF selected-F QC2 anomalous variable fields, all **45** on source science HOLD. Its four-day remaining CDS manifest was cross-checked against the previous Stage05AB original ZIP/partial inventory and only **one** requested CDS day was submitted: **JP-Khw 2011-12-16 UTC surface_pressure**.

```text
STAGE05AF SOURCE PREFLIGHT PASS
19/45 INDEPENDENT EVIDENCE; ALL 45 HOLD
JP-Khw 2011-12-16 surface_pressure APPROVED FOR ONE CDS REQUEST
STAGE05S SELF-TEST PASS | 3-site/9-day source gates, explicit pilot only, NO NETWORK OR WRITES
=== REQUEST JP-Khw 2011-12-16 ONLY ===
2026-11-02 13:15:22,599 INFO Request ID is e9d0b2f4-d165-4dd1-a39b-a2083b6b048b
2026-11-02 13:15:22,660 INFO status has been updated to accepted
2026-11-02 13:15:36,154 INFO status has been updated to successful
DATASET reanalysis-era5-land-timeseries SITE JP-Khw UTC_DATE 2011-12-16
REQUEST_NONSECRET {"data_format": "csv", "date": "2011-12-16/2011-12-16", "location": {"latitude": 33.13658, "longitude": 130.70834}, "variable": ["surface_pressure"]}
CDS_PILOT_RESPONSE_WRITTEN /home/ly3n24/japanflux_stage05s/downloads/JP-Khw_ERA5Land_timeseries_20111216_CSV_response.zip
DETECTED_PAYLOAD ZIP BYTES 491 SHA256 fb2d7677d7c8a38fe4d5d31eb0af37434cfe0932a59343e36601f61b7e407821
SCIENCE_HOLD: No field contents have yet been verified for UTC, units, grid coordinates or physical plausibility
NO ORIGINAL DATA / FORCING / MODEL CHANGES
```

Afterward the operator ran original source-gated Stage05AB against the six historical December 2011 site-days, which **validated** the actual new ZIP's CRC, one original CSV `sp` variable in Pa, complete 24 valid UTC hours of 2011-12-16, finite surface pressures, nearest original BIF land-grid 33.10000000000104°N/130.69999999999686°E. No new CDS call was made during the read-only Stage05AB verification.

```text
STAGE05AB SIX 2011-CDS DAY EXISTING FILES/CRC/TIME/GRID SOURCE INVENTORY PASS | NO CDS / SLURM / REPAIR
DAY JP-Khw 2011-12-16 ZIP REGULAR PARTIAL ABSENT CSV_ZIP_STATUS COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR SHA256 fb2d7677d7c8a38fe4d5d31eb0af37434cfe0932a59343e36601f61b7e407821 GRID 33.10000000000104 130.69999999999686
DAY JP-Khw 2011-12-17 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT
DAY JP-Yms 2011-12-16 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT
DAY JP-Yms 2011-12-17 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT
COUNTS {'REUSE_VALID_EXISTING_ZIP_FOR_SEPARATE_SOURCE_QC2_REVIEW_NO_REDOWNLOAD': 3, 'NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT': 3}
INVENTORY /home/ly3n24/japanflux_stage05af/inventory_20261102T131536Z/stage05ab_six_2011_CDS_archive_existing_payload_inventory_HOLD.tsv
SOURCE_AUDIT /home/ly3n24/japanflux_stage05af/inventory_20261102T131536Z/stage05ab_six_2011_CDS_original_archive_science_audit.json
NO CDS CALLS, NO ORIGINAL ZIP/SOURCE/FORCING CHANGES; ALL 45 FIELDS HOLD
```

## Current scientific coverage

- **6 of 9** site×UTC-day original ERA5-Land source-reference payloads fully verified. **Three dates** remain absent: **JP-Khw 2011-12-17** and **JP-Yms 2011-12-16/17**.
- Exactly **19 of 45** original source-QC2 variable anomalies already have strong independent reference-hour physical-context evidence: JP-Fjy 6, JP-Khw 8, JP-Yms 5 across 14 original site-native half-hours. **8 other** original UTC-verified source-QC2 fields remain to be checked (JP-Khw3; JP-Yms5) and 18 JP-Tef/Tmd original clock conventions remain unreconciled.
- A successful **single-day** CDS download for Dec16 cannot alone complete cross-midnight anomaly contexts. Original JP-Khw **2011-12-17** pressure reference should be requested next, **only as a single-site/single-day action**, with original Stage05S ZIP/.partial no-overwrite protection and a fresh Stage05AB read-only audit.
- [Stage05AG JP-Khw source-scoped cross-midnight two-day pressure/QC2 comparison](../scripts/stage05/05ag_JP_Khw_2011_two_day_pressure_3_QC2_independent_context_NO_REPAIR.py) is committed but **not yet operator-run**. It requires original Stage05O 27-source QC2/BIF UTC time fields, Stage05R original 87 request variable-hour associations, Stage05AE actual 19 evidence summary, refreshed Stage05AB validated **both** Dec16 and Dec17 ZIPs, and checks the actual SHA/CRC and 48 independent hourly Pa→kPa values against the three 2011 original QC2 `F=ERA` PA entries. The original Dec16 downloaded ZIP SHA256 is pinned. No half-hour forcing repair or observation substitution.
- Tower BIF JP-Khw latitude 33.13658°N, longitude 130.70834°E, elevation 196 m; ERA5-Land model-grid elevation is **not independently checked**. Pressure differences remain **physical context evidence**, not exact replacement observations.

All **45** original source candidate variables remain science HOLD. No changes to source JPF ZIPs, model cases, forcing or Slurm jobs were performed by the auditor.
