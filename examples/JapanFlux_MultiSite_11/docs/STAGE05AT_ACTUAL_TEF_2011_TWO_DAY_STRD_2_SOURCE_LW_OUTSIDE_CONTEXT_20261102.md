# JapanFlux Stage05AT — ACTUAL JP-Tef Dec 2011 two-day independent ERA5-Land LW_IN context PASS (2026-11-02)

## Actual IRIDIS6 operator execution

```text
STAGE05AT SELF-TEST PASS | exact source 2011 Tef two LW QC2 events, day16 SHA 533b + day17 24UTC STRD/3600, 8h cross-midnight context; NO CDS/WRITES
STAGE05AT FIRST-DAY SOURCE ZIP VERIFIED /home/ly3n24/japanflux_stage05as/downloads/JP-Tef_ERA5Land_timeseries_20111216_CSV_response.zip SHA256 533b462fa0804a3d34428b6dd5f9b38b8a9e70dbc705af481c18ec614ea16148
STAGE05AT TWO_ORIGINAL_LW_QC2_NATIVE_EVENTS 2 VALUE_W_M2 26.164
STAGE05AT SECOND-DAY_REQUEST_SCOPE {"data_format": "csv", "date": "2011-12-17/2011-12-17", "location": {"latitude": 45.055808, "longitude": 142.107122}, "variable": ["surface_thermal_radiation_downwards"]}
STAGE05AT READONLY PILOT PREFLIGHT PASS | NO CDS / NO ORIGINAL WRITES; run explicit --submit to retrieve second UTC day
2026-11-02 22:40:51,005 INFO Request ID is f1620c90-21f0-48ee-ade5-b6c128b3d803
2026-11-02 22:41:12,261 INFO status has been updated to successful
STAGE05AT EXPLICIT JP-TEF SECOND-DAY CDS REFERENCE REQUEST JP-Tef 2011-12-17
STAGE05AT SECOND CDS UTC DAY ZIP CRC/24UTC/GRID PASS | TWO-DAY JP-TEF LW CONTEXT ONLY NO REPAIR
DAY17_ZIP /home/ly3n24/japanflux_stage05as/downloads/JP-Tef_ERA5Land_timeseries_20111217_CSV_response.zip BYTES 474 SHA256 81043becb8ccce9936164d7e1e3afdc56c55a84b077b314c4672339f3a81f532
MODEL_GRID 45.10000000000121 142.09999999999621 HOURS_DAY16_24_DAY17_24
REFERENCE_8h_STRD_W_M2_MIN_MAX 193.696111 222.535556
ORIGINAL_QC2 201112170600 CANDIDATE_UTC 201112162100 LW_W_M2 26.164 OUTSIDE_8h_CONTEXT 1 SCIENCE HOLD_CONTEXT_ONLY_NO_STRONG_CLASS_AUTO_APPROVAL
ORIGINAL_QC2 201112170630 CANDIDATE_UTC 201112162130 LW_W_M2 26.164 OUTSIDE_8h_CONTEXT 1 SCIENCE HOLD_CONTEXT_ONLY_NO_STRONG_CLASS_AUTO_APPROVAL
INDEPENDENT_8H_CONTEXT_TSV /home/ly3n24/japanflux_stage05at/run_20261102T224049Z/stage05at_Tef_2011_two_day_hourly_LW_independent_context.tsv
TWO_DAY_SOURCE_SCIENCE_HOLD_JSON /home/ly3n24/japanflux_stage05at/run_20261102T224049Z/stage05at_Tef_2_original_LW_QC2_ERA5L_two_day_context_HOLD.json
ALL_45_ORIGINAL_SOURCE_QC2_FIELDS_HOLD; NO ORIGINAL FORCING/SLURM/REPAIR
```

## Scientific interpretation

These **two JP-Tef source-selected `LW_IN_F_QC=2`** original `2011-12-17 06:00,06:30` half-hour values are both **26.164 W m⁻²**, whereas independent ERA5-Land hourly `strd` already de-accumulated J m⁻² /3600 gives a conservative cross-midnight (2011-12-16 18:00 through 2011-12-17 01:00 UTC) hourly envelope **193.696111–222.535556 W m⁻²**. They are both outside that interval (2/2). The comparison is physically compelling independent context against original defective downscaled same-release ERA-selected values, but **not exact flux-tower 30-minute reconstruction**; source sensor, site-versus-grid and hourly representativeness remain distinct.

**Clock provenance remains an explicitly operator-selected JST UTC+9 hypothesis**: original JP-Tef 75-line README SHA `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5` says local solar time; no exact source clock transformation proof. The two anomalies are therefore **CONTEXT_ONLY**, not automatically promoted to prior source-verified STRONG_CONTEXT group, and not approved for forcing replacement.

Current independent-source coverage: **27 previously compared** JPF Fjy6/Khw11/Yms10 plus **2 now independently compared Tef fields** = **29/45 context reviewed**; prior 22 strong, original Yms5 context-only, new Tef2 context-only; **16 fields still need independent context** (Tef 2022×2, Tmd 2005×8, Tmd 2011×3, Tmd 2022×3). Source population 45/45 remains HOLD.

Original external CDS source ZIPs: first day `20111216` 467 bytes SHA `533b462fa0804a3d34428b6dd5f9b38b8a9e70dbc705af481c18ec614ea16148`; second day `20111217` 474 bytes SHA `81043becb8ccce9936164d7e1e3afdc56c55a84b077b314c4672339f3a81f532`; grid 45.10000000000121N 142.09999999999621E. First and second CDS request logs were observed successful, CRC/24-UTC-hour/variable checks passed. No original JPF ZIP, forcing, model, Slurm, AD400 or PFT changes.

## Next Stage05AU

Prioritize **JP-Tmd candidate UTC 2005-08-11** because **8 original source QC2 fields** (TA 3, PA 3, LW_IN 2) fall on the same already Stage05AR geolocated date. Its independently sourced single-day CDS request is `reanalysis-era5-land-timeseries` at original BIF tower (42.735911N,141.523147E,117m) for `2m_temperature,surface_pressure,surface_thermal_radiation_downwards` (all 24 UTC hours, compare original scoped 14:00–22:00 UTC). Convert: `t2m-273.15` °C, `sp/1000` kPa, `strd/3600` W m⁻², **not second-difference**. Keep original selected F, QC2 and JST+9 diagnostic hypothesis. A strict independent source ZIP validation and original-source-to-reference context audit should precede any repair decision.

Do not download the same Tef days again. Remaining site×UTC-day windows of seven after first two: Tef `2022-04-08`, Tmd `2005-08-11`, `2011-12-16`, `2011-12-17`, and `2022-04-08`.
