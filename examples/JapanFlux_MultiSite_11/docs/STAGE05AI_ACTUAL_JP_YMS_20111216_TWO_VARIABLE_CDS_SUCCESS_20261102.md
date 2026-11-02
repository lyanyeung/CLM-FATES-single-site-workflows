# JapanFlux Stage05AI — actual JP-Yms 2011-12-16 two-variable ERA5-Land CDS response, source validation PASS (2026-11-02)

## Actual operator-executed tests, source-scoped single CDS request

The pinned **updated** [Stage05AB](../scripts/stage05/05ab_inventory_six_2011_existing_CDS_ZIP_partial_CRC_READONLY.py) **self-test PASSED on real IRIDIS6**, including checks for original historical one-variable CSV and new Yms `sp,strd` combined-versus-split original CSV package layouts. Original Stage05S one-day manifest/license-source validation self-test passed.

The operator ran Stage05AB on the original Stage05S downloads **before** retrieval: JP-Fjy 2011-12-16/17 and JP-Khw 2011-12-16/17 had valid original ZIPs, while both JP-Yms 2011-12-16/17 had **no ZIP, .zip.partial or alternate CSV/NC**. Stage05AH exact original-source two-date manifest and 22/45 science HOLD ledger passed the explicit science preflight.

One external CDS request was then submitted for exactly **JP-Yms 2011-12-16 UTC** at original JPF BIF tower coordinates **34.790278°N,135.840939°E**, with original source-verified request variables `surface_pressure` and `surface_thermal_radiation_downwards`, dataset `reanalysis-era5-land-timeseries`, data format CSV. Actual transaction:

```text
2026-11-02 19:34:01,169 INFO Request ID is c11ca378-b7bb-4da9-9e31-07b6066dbca7
2026-11-02 19:34:01,224 INFO status has been updated to accepted
2026-11-02 19:34:14,902 INFO status has been updated to running
2026-11-02 19:34:22,542 INFO status has been updated to successful
DATASET reanalysis-era5-land-timeseries SITE JP-Yms UTC_DATE 2011-12-16
REQUEST_NONSECRET {"data_format": "csv", "date": "2011-12-16/2011-12-16", "location": {"latitude": 34.790278, "longitude": 135.840939}, "variable": ["surface_pressure", "surface_thermal_radiation_downwards"]}
CDS_PILOT_RESPONSE_WRITTEN /home/ly3n24/japanflux_stage05s/downloads/JP-Yms_ERA5Land_timeseries_20111216_CSV_response.zip
DETECTED_PAYLOAD ZIP BYTES 948 SHA256 edd1b8acd84b31d8a04f214850dd9f51d9471dbffb91664fa76a54a9b7539c0c
```

The pinned updated Stage05AB then executed on original downloaded file contents and **PASSED** the strict original-source ZIP integrity checks: CRC, authorized raw variable columns, **24 unique complete UTC hourly rows per `sp` and `strd` variable**, same source-accepted independent grid and broad scientific physical numeric ranges. The response grid was **34.80000000000106°N,135.79999999999654°E**. Operator result:

```text
DAY JP-Yms 2011-12-16 ZIP REGULAR PARTIAL ABSENT CSV_ZIP_STATUS COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR SHA256 edd1b8acd84b31d8a04f214850dd9f51d9471dbffb91664fa76a54a9b7539c0c GRID 34.80000000000106 135.79999999999654 NEXT REUSE_VALID_EXISTING_ZIP_FOR_SEPARATE_SOURCE_QC2_REVIEW_NO_REDOWNLOAD
DAY JP-Yms 2011-12-17 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT SHA256 NONE GRID NONE NONE NEXT NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT
COUNTS {'REUSE_VALID_EXISTING_ZIP_FOR_SEPARATE_SOURCE_QC2_REVIEW_NO_REDOWNLOAD': 5, 'NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT': 1}
SOURCE_AUDIT /home/ly3n24/japanflux_stage05ai/after_20261102T193422Z/stage05ab_six_2011_CDS_original_archive_science_audit.json
JP-Yms DEC16 TWO-VARIABLE CONTENT VALIDATED
ZIP_SHA256 edd1b8acd84b31d8a04f214850dd9f51d9471dbffb91664fa76a54a9b7539c0c
```

The ZIP's exact internal CSV member count and layout were not printed by this operator output; the updated Stage05AB source audit accepted whichever of its verified combined/split forms was actually present. **Do not infer a particular archive layout without reading the actual audit JSON.**

## Science portfolio, no original model or meteorological edits

- Fully validated independent reference payloads now **8 of 9** original source site×UTC-day windows. The only missing independently checked site-day is **JP-Yms 2011-12-17 UTC**, with the **same two source variables**.
- Prior actual Stage05AH continues to establish **22 of 45** original source-selected QC2 field anomalies with strong independent grid-hour physical context (JP-Fjy6, JP-Khw11, JP-Yms5), across 17 original site×native halfhours.
- The **five** other original UTC+9-verified JP-Yms QC2 anomaly variable fields still require original matched event-specific cross-day external comparison. Do not claim the ZIP download adds five evidenced source QC2 records.
- **18** JP-Tef/Tmd original local solar vs local standard clock-provenance fields remain unresolved; none can be silently mapped to UTC or automatically repaired.
- ERA5-Land `strd` downward thermal radiation is accumulated energy (J m⁻²) in the relevant hourly accumulation interval. An hourly mean flux comparison may divide by 3600 only with correct interval-end/time alignment and source-hour provenance; it **cannot** become a pointwise 30-min JPF LW_IN repair.
- **All 45 original candidate fields remain science HOLD**, no source JPF ZIP writes, forcing/model/AD400/Slurm, repairs or approval.

Next: preflight source-pinned actual Stage05AH two-day plan and latest Stage05AB file inspection, check no existing JP-Yms Dec17 ZIP/partial/CSV/NC, submit only JP-Yms **2011-12-17 UTC** source-variable `surface_pressure` and `surface_thermal_radiation_downwards`, and repeat the strict upgraded Stage05AB independent source integrity review. **First actual JP-Yms two-day source QC2 scientific comparison is not yet complete.**
