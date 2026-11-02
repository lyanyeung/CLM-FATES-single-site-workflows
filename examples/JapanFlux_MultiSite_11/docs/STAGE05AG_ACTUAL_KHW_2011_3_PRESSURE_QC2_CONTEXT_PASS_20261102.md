# JapanFlux Stage05AG — actual corrected JP-Khw 2011 two-day independent pressure/source QC2 comparison PASS (2026-11-02)

## Operator-observed corrected script and original CDS ZIP content

The operator used the source-exact corrected Stage05AG, including regression self-test that allows JP-Khw **2005** historical mixed `LW_IN`/`PA`/`TA` QC2 anomalies while constraining **2011** source fields to `PA` only. Both original independently sourced CDS ZIPs were hash checked before the science source comparison. No data were re-downloaded.

```text
STAGE05AG SELF-TEST PASS | actual 2005 Khw LW/PA/TA mixed-field regression + 2011 PA-only, UTC+9, two-day context; NO WRITES
/home/ly3n24/japanflux_stage05s/downloads/JP-Khw_ERA5Land_timeseries_20111216_CSV_response.zip: OK
/home/ly3n24/japanflux_stage05s/downloads/JP-Khw_ERA5Land_timeseries_20111217_CSV_response.zip: OK
STAGE05AG JP-KHW TWO-DAY INDEPENDENT ERA5L SOURCE PA AUDIT PASS | NO CDS / SLURM / REPAIR
ZIP_SHA256_BY_DAY {'2011-12-16': 'fb2d7677d7c8a38fe4d5d31eb0af37434cfe0932a59343e36601f61b7e407821', '2011-12-17': 'f590c32432ffac5c10460ea074ea8fc05fb9b8742af96f8301e9d35ed6fb6188'}
INDEPENDENT_HOURLY_POINTS 48 SOURCE_REQUEST_HOUR_PAIRS 9
ORIGINAL_SOURCE_QC2_FIELDS 3 OUTSIDE_HOURLY_CONTEXT 3
CDS_GRID (33.10000000000104, 130.69999999999686) TOWER_BIF (33.13658, 130.70834, 196.0)
SOURCE_FIELD 201112170630 PA_F 49.506 REFERENCE_UTC 2011-12-16T21:00Z;2011-12-16T22:00Z;2011-12-16T23:00Z REFERENCE_KPA 99.029360;99.117340;99.150080 OUTSIDE 1 STATUS HOLD_NO_APPROVED_30MIN_PRESSURE_REPAIR
SOURCE_FIELD 201112170700 PA_F 0.0 REFERENCE_UTC 2011-12-16T22:00Z;2011-12-16T23:00Z;2011-12-17T00:00Z REFERENCE_KPA 99.117340;99.150080;99.195720 OUTSIDE 1 STATUS HOLD_NO_APPROVED_30MIN_PRESSURE_REPAIR
SOURCE_FIELD 201112170730 PA_F 49.571 REFERENCE_UTC 2011-12-16T22:00Z;2011-12-16T23:00Z;2011-12-17T00:00Z REFERENCE_KPA 99.117340;99.150080;99.195720 OUTSIDE 1 STATUS HOLD_NO_APPROVED_30MIN_PRESSURE_REPAIR
FIELD_EVIDENCE_TABLE /home/ly3n24/japanflux_stage05ag/fixed_review_20261102T185321Z/stage05ag_Khw_2011_3_original_QC2_vs_two_day_independent_CDS_HOLD.tsv
SCIENCE_HOLD_SUMMARY /home/ly3n24/japanflux_stage05ag/fixed_review_20261102T185321Z/stage05ag_Khw_two_day_source_CDS_science_HOLD_summary.json
ALL_45_JPF_QC2_FIELD_CANDIDATES_CONTINUE_HOLD_NO_REPLACEMENT
```

This is source-specific original `F=ERA` QC2 against *independent* ERA5-Land hourly physical context, **not** a resolution or replacement. The near-grid pressure 99.029–99.196 kPa is not an exact model/grid-adjusted measurement at the JP-Khw tower (196 m original BIF tower elevation; ERA5-Land returned grid elevation unverified). Yet the 0 kPa candidate is physically impossible, and the two 49 kPa values are grossly inconsistent with the independent physical context.

## Evidence and provenance ledger

Previous actual Stage05AE: **19/45** independent strongly inconsistent original source variable fields across **14** unique original station×native-halfhour times (JP-Fjy 6, JP-Khw 8, JP-Yms 5). Successful Stage05AG adds **exactly 3** new previously unreviewed original JP-Khw source-variable PA candidates at three unique native halfhours: evidence **22/45**, 17 unique original station×native-halfhours (JP-Fjy **6**, JP-Khw **11**, JP-Yms **5**).

- **5** UTC-verified original source candidates remain without separate reference context; all at JP-Yms and require **surface_pressure** plus **surface_thermal_radiation_downwards** across UTC **2011-12-16/17**.
- **18** JP-Tef/Tmd candidate fields remain unresolved source local-solar versus local-standard clock basis, not assigned UTC.
- **7 of 9** original site×UTC-day independent reference payloads validated; remaining only **JP-Yms 2011-12-16 and 2011-12-17**.
- JP-Khw 2011-12-16 CDS request transaction ID was observed `e9d0b2f4-d165-4dd1-a39b-a2083b6b048b`; the JP-Khw 2011-12-17 ZIP was **pre-existing** at the latest operator run; its original request ID has **not** been provided. Verified 2011-12-17 file CRC/SHA/UTC/grid do not imply a newly observed CDS successful request.
- Original JPF 45 field anomalies continue science **HOLD**, original source/forcing/model unchanged, no Slurm/AD400 and no scientifically approved replacement.

Next publish/execute Stage05AH: merge prior Stage05AE 19-field source science registry + Stage05AG 3 original 2011 JP-Khw PA fields into 22-source-field independent context/HOLD evidence, and output two original source-gated JP-Yms 2011-12-16/17 CDS-day preview. Use the exact original Stage05O source UTC/HOLD tables and latest Stage05AB ZIP inventory to disallow unvalidated source candidate alteration. Then request a single JP-Yms reference UTC date only after no-overwrite preflight.
