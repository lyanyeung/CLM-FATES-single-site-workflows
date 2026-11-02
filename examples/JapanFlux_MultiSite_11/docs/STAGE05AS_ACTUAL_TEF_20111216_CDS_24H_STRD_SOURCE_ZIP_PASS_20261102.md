# JapanFlux Stage05AS — ACTUAL JP-Tef 2011-12-16 independent ERA5-Land hourly strd pilot PASS (2026-11-02)

## Operator-executed real ERA5-Land CDS response

The operator ran SHA-pinned [Stage05AS](../scripts/stage05/05as_Tef_Tmd_source_BIF_JST_candidate_7day_ONE_DAY_CDS_ERA5Land_OPT_IN.py) on actual Stage05AR original-site-BIF source geolocation evidence and Stage05AQ user JST+9 diagnostic candidate UTC. Syntax and self-test passed, seven site×UTC-day candidate preview PASS without requests, then an **explicit single CDS request** to `reanalysis-era5-land-timeseries` was accepted and successful.

```text
STAGE05AS SELF-TEST PASS | seven exact source BIF sites/days, one-day CDS ZIP 24UTC/units/grid, already deaccumulated STRD; NO NETWORK/WRITES
STAGE05AS SEVEN-DAY VERIFIED SOURCE-BIF AND JST-HYPOTHESIS PREVIEW PASS | NO CDS / SLURM
2026-11-02 22:32:10,961 INFO Request ID is 8a7f0dc3-15f6-43de-9d1f-9eadecc339e6
2026-11-02 22:32:11,027 INFO status has been updated to accepted
2026-11-02 22:32:34,725 INFO status has been updated to successful
STAGE05AS EXPLICIT ONE-DAY CANDIDATE JST+9 DIAGNOSTIC CDS REQUEST | NO MODEL / REPAIR
DATASET reanalysis-era5-land-timeseries SITE JP-Tef CANDIDATE_UTC_DAY 2011-12-16
ORIGINAL_BIF_SHA256 78f02f04892b5731cd33e57b57d00e71bdff4c743ba94f5dd6c69dbd98be0f26
ORIGINAL_TOWER 45.055808 142.107122 79.47
REQUEST_NONSECRET {"data_format": "csv", "date": "2011-12-16/2011-12-16", "location": {"latitude": 45.055808, "longitude": 142.107122}, "variable": ["surface_thermal_radiation_downwards"]}
OUTPUT_ZIP_TARGET /home/ly3n24/japanflux_stage05as/downloads/JP-Tef_ERA5Land_timeseries_20111216_CSV_response.zip
CDS_RETURNED_PARTIAL_BYTES 467
STAGE05AS ORIGINAL CDS ZIP CRC / 24UTC / VARIABLE / GRID SCIENCE PASS | NO REPAIR
RETURNED_ZIP /home/ly3n24/japanflux_stage05as/downloads/JP-Tef_ERA5Land_timeseries_20111216_CSV_response.zip BYTES 467 SHA256 533b462fa0804a3d34428b6dd5f9b38b8a9e70dbc705af481c18ec614ea16148
VERIFIED_HOURLY_VALUES 24 RAW_COLUMNS ['strd']
MODEL_GRID 45.10000000000121 142.09999999999621 ORIGINAL_TOWER 45.055808 142.107122
ORIGINAL_CDS_SOURCE_AUDIT /home/ly3n24/japanflux_stage05as/stage05as_JP-Tef_2011-12-16_original_CDS_source_payload_VALIDATED_NOT_REPAIR.json
ORIGINAL_CLOCK_STILL_USER_JST_ASSUMPTION; ALL 45 QC2 FIELDS HOLD; NO FORCING/MODEL/SLURM
```

The real original CDS ZIP is **467 bytes, SHA256 `533b462fa0804a3d34428b6dd5f9b38b8a9e70dbc705af481c18ec614ea16148`**, single CSV `strd` field and exactly 24 distinct UTC hours; zip CRC and physical value envelope passed. Source tower original BIF is **45.055808°N/142.107122°E, 79.47 m**, and CDS returned nearest model grid **45.1°N/142.1°E**. Model grid elevation has NOT been verified.

For this ECMWF ERA5-Land `reanalysis-era5-land-timeseries` product, hourly `strd` are *already deaccumulated* hourly integrated J m⁻². Divide by 3600 seconds to compare an hourly mean downward longwave flux in W m⁻²; **do not difference adjacent hours again**. The `valid_time` labels end of corresponding hour, so nearby-hour contextual comparisons are not exact 30-min tower replacements.

Original two JP-Tef source-selected LW_IN_QC2 values remain 26.164 W m⁻² at original native/JST-hypothesis `2011-12-17 06:00/06:30` → candidate UTC `2011-12-16 21:00/21:30`. Stage05AQ's conservative independent hourly context window crosses UTC midnight into **2011-12-17 00:00 and 01:00**, which were **NOT** retrieved by Stage05AS day16. Therefore **the two-day numerical source-context audit is incomplete**, despite successful first-day CDS validation.

## Next Stage05AT

[Stage05AT dedicated second-day JP-Tef 2011-12-17 original CDS ZIP validation + both-day two original 26.164 W m⁻² QC2 source-context comparison](../scripts/stage05/05at_JP_Tef_20111217_second_CDS_day_two_day_LW_QC2_CONTEXT_ONLY.py) has now been **committed**. Its real IRIDIS test/CDS second-day run is **pending**. It checks the first downloaded 467-byte source ZIP SHA plus original Stage05AS JSON, actual Stage05AR source BIF/7-day roster, and exact Stage05AQ two December 2011 LW original native times. No timebase approval/automatic repair.

Use source-gated same-day Stage05AR stage/coordinates, pin and reuse the successful Stage05AS ZIP parsing science checker, rehash unchanged original day16 ZIP against known SHA, then obtain explicitly approved **JP-Tef 2011-12-17** CDS timeseries `strd` for 24 UTC hours. Check returned ZIP CRC, all 24 hours, variable and grid, then compare original two QC2 native source LW values against a conservative two-day hourly context; label as `CONTEXT_ONLY` candidate, not strong-approved or 30-min replacement. Keep original JPF 75-line `local solar time` README conflict and operator JST+9 hypothesis explicit, all original 45 source fields scientific HOLD. No PFT, Slurm, source ZIP or forcing changes.
