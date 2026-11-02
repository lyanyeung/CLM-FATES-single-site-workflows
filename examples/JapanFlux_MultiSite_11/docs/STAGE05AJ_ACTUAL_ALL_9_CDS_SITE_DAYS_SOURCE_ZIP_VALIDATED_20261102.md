# JapanFlux Stage05AJ — actual 9/9 independently sourced ERA5-Land CDS site-day files fully verified (2026-11-02)

## Actual operator-run final JP-Yms two-variable CDS retrieval

The operator executed original SHA-pinned Stage05S source-scoped single-day request **JP-Yms 2011-12-17 UTC** with **surface_pressure** and **surface_thermal_radiation_downwards**, at the site original source BIF coordinates **34.790278°N,135.840939°E**. Observed original CDS request:

```text
STAGE05AB SELF-TEST PASS | original six site-days, Yms combined/split sp+strd CSV, Fjy/Khw pressure-only, SHA/CRC/24UTC, NO NETWORK/WRITES
STAGE05S SELF-TEST PASS | 3-site/9-day source gates, explicit pilot only, NO NETWORK OR WRITES
JP-Yms FINAL DAY SOURCE PREFLIGHT PASS
2026-11-02 19:41:04,534 INFO Request ID is 6df4be6f-a33d-4ddd-83ed-61c35195c90b
2026-11-02 19:41:04,603 INFO status has been updated to accepted
2026-11-02 19:42:58,609 INFO status has been updated to successful
DATASET reanalysis-era5-land-timeseries SITE JP-Yms UTC_DATE 2011-12-17
REQUEST_NONSECRET {"data_format": "csv", "date": "2011-12-17/2011-12-17", "location": {"latitude": 34.790278, "longitude": 135.840939}, "variable": ["surface_pressure", "surface_thermal_radiation_downwards"]}
CDS_PILOT_RESPONSE_WRITTEN /home/ly3n24/japanflux_stage05s/downloads/JP-Yms_ERA5Land_timeseries_20111217_CSV_response.zip
DETECTED_PAYLOAD ZIP BYTES 953 SHA256 bb50100065193cff70429c626603cd60e957882624db5fbee056f97a23b032f6
```

The operator subsequently ran the updated Stage05AB ZIP original CRC/24UTC/variable/grid/physics inspector on **all six** December-2011 original site-days. All six original ZIPs passed with regular-file status, no `.zip.partial`, and independent returned grid locations:

```text
DAY JP-Fjy 2011-12-16 ... COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR SHA256 cc172d7c18e7b7b5199aa7cccc8b941c6115863861860f0618d8b33d4f577c9a GRID 35.50000000000107 138.79999999999643
DAY JP-Fjy 2011-12-17 ... COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR SHA256 f553e574a72e409c988460f7052100496c264321a65a46e5a80a636982d3deed GRID 35.50000000000107 138.79999999999643
DAY JP-Khw 2011-12-16 ... COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR SHA256 fb2d7677d7c8a38fe4d5d31eb0af37434cfe0932a59343e36601f61b7e407821 GRID 33.10000000000104 130.69999999999686
DAY JP-Khw 2011-12-17 ... COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR SHA256 f590c32432ffac5c10460ea074ea8fc05fb9b8742af96f8301e9d35ed6fb6188 GRID 33.10000000000104 130.69999999999686
DAY JP-Yms 2011-12-16 ... COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR SHA256 edd1b8acd84b31d8a04f214850dd9f51d9471dbffb91664fa76a54a9b7539c0c GRID 34.80000000000106 135.79999999999654
DAY JP-Yms 2011-12-17 ... COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR SHA256 bb50100065193cff70429c626603cd60e957882624db5fbee056f97a23b032f6 GRID 34.80000000000106 135.79999999999654
COUNTS {'REUSE_VALID_EXISTING_ZIP_FOR_SEPARATE_SOURCE_QC2_REVIEW_NO_REDOWNLOAD': 6}
INVENTORY /home/ly3n24/japanflux_stage05aj/inventory_20261102T194259Z/stage05ab_six_2011_CDS_archive_existing_payload_inventory_HOLD.tsv
SOURCE_AUDIT /home/ly3n24/japanflux_stage05aj/inventory_20261102T194259Z/stage05ab_six_2011_CDS_original_archive_science_audit.json
VERIFIED JP-Yms 2011-12-16 edd1b8acd84b31d8a04f214850dd9f51d9471dbffb91664fa76a54a9b7539c0c
VERIFIED JP-Yms 2011-12-17 bb50100065193cff70429c626603cd60e957882624db5fbee056f97a23b032f6
ALL 9 SOURCE CDS SITE-DAYS VERIFIED
NO ORIGINAL SOURCE REPAIR APPROVED
```

The other three source site-days (JP-Fjy, JP-Khw and JP-Yms Aug 2005) were previously validated by Stage05Y/05Z/05AA. The six December ZIPs plus three historical August ZIPs **total 9/9 independent ERA5-Land site×UTC-day reference windows**; the Stage05AJ latest output contains a new check of the **six 2011 dates**, and relies on previous evidence for the other three. It is not a fresh nine-archive ZIP scan.

## Next scientific step: five still-uncompared original JP-Yms variable QC2 fields

Stage05AH actual science proof retained **22/45** source-selected F=ERA QC2 anomalous variables independently corroborated as grossly inconsistent with nearby hourly ERA5-Land physical contexts (JP-Fjy6 / JP-Khw11 / JP-Yms5; 17 original site×native halfhour timestamps). **Five** further original QC2 variable fields at JP-Yms are UTC+9 source timebase-verified, but not yet independently compared with the new Dec 2011 48 hourly observations each of `sp` and `strd`. **18** other original JP-Tef/Tmd fields remain on source solar-versus-standard time conflict HOLD.

ECMWF's ERA5-Land *hourly time-series* product explicitly lists `surface_thermal_radiation_downwards` as **de-accumulated hourly energy**, J m⁻². It is not the raw original ERA5-Land forecast's 00 UTC→forecast step cumulative value; no second de-accumulation should be applied to this CSV. Convert each complete 1-hour energy to hourly mean downward flux W m⁻² via `strd / 3600`. Its `valid_time` marks the hour end, hence a measured 30min JPF LW_IN event and model hourly mean should be compared over adjacent, source-aligned intervals as **physical context only**, not as a pointwise 30min proxy, particularly across UTC midnight.

Public product evidence for this caveat:
- ECMWF ERA5-Land hourly time-series Product User Guide: https://confluence.ecmwf.int/pages/viewpage.action?pageId=699689224 — methodology and parameter table list radiation fields as de-accumulated
- CDS dataset https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries

The operator's actual latest JP-Yms returned source-grid position is **34.80000000000106°N,135.79999999999654°E**, and independent model-grid geopotential is **not independently verified**. The source QC2, exact JST→UTC date mapping, variable association and 48-hour reference must be verified before deciding how many of the five pending original fields have strong independent physical evidence.

All 45 originally flagged variable records remain HOLD. No source ZIP, forcing, model, Slurm, AD400 or scientifically approved 30-minute replacement was performed or authorized.
