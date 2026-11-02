# JapanFlux Stage05AU — ACTUAL JP-Tmd 2005-08-11 three-variable CDS source QC, 8/8 original QC2 outside context (2026-11-02)

## Actual operator's IRIDIS6 result

The user executed a SHA-pinned original source-BIF-/Stage05AR-/AQ-/AT-gated [Stage05AU](../scripts/stage05/05au_JP_Tmd_20050811_three_variable_8_QC2_CDS_ONE_DAY_CONTEXT_ONLY.py) to download one exact user-JST-hypothesis candidate UTC day of independent ERA5-Land timeseries and compare original JPF JP-Tmd `FLUXMET_HH` QC2 values. Original ZIP, forcing, model cases, PFT, Slurm were unchanged.

```text
STAGE05AU SELF-TEST PASS | Tmd original 8 QC2 TA3 PA3 LW2, 2005-08-11 9h UTC 3-variable source, strd hourly deaccumulated, no CDS/writes
STAGE05AU ORIGINAL JP-TEF 2-DAY EVIDENCE/ZIP SHA RETAINED PASS | NO REDOWNLOAD
STAGE05AU ORIGINAL TMD_2005 8_QC2_SOURCE_FIELDS VERIFIED 8
STAGE05AU READONLY SOURCE/UTC/BIF/CDS PREFLIGHT PASS | NO CDS / NO ORIGINAL WRITES
2026-11-02 22:46:58,761 INFO Request ID is a876974b-1985-4d6a-9b18-d6979dc0ee2b
2026-11-02 22:47:31,876 INFO status has been updated to successful
STAGE05AU EXPLICIT JP-TMD 2005 SINGLE-DAY CDS INDEPENDENT REFERENCE REQUEST
STAGE05AU TMD 2005 CDS 3×24 UTC/CRC/GRID SOURCE PASS | EIGHT ORIGINAL QC2 SOURCE FIELDS CONTEXT ONLY NO REPAIR
CDS_ZIP /home/ly3n24/japanflux_stage05as/downloads/JP-Tmd_ERA5Land_timeseries_20050811_CSV_response.zip BYTES 1380 SHA256 cd722e173c24154ccb5d28a632683cb39473389ac163b12439cce8e870721fe6
RETURNED_CDS_NEAREST_GRID 42.700000000001175 141.49999999999625
NINE_HOUR_CONTEXT_TA_C_MIN_MAX 19.021 20.001
NINE_HOUR_CONTEXT_PA_KPA_MIN_MAX 99.658 99.738
NINE_HOUR_CONTEXT_LW_WM2_MIN_MAX 387.743 400.675
ORIGINAL_QC2 200508120200 UTC_CANDIDATE 200508111700 LW_IN ORIGINAL_F 28.519 MODEL_REFERENCE_ENVELOPE 387.743 400.675 OUTSIDE_CONTEXT 1
ORIGINAL_QC2 200508120230 UTC_CANDIDATE 200508111730 LW_IN ORIGINAL_F 28.519 MODEL_REFERENCE_ENVELOPE 387.743 400.675 OUTSIDE_CONTEXT 1
ORIGINAL_QC2 200508120230 UTC_CANDIDATE 200508111730 PA ORIGINAL_F 49.502 MODEL_REFERENCE_ENVELOPE 99.658 99.738 OUTSIDE_CONTEXT 1
ORIGINAL_QC2 200508120230 UTC_CANDIDATE 200508111730 TA ORIGINAL_F -132.399 MODEL_REFERENCE_ENVELOPE 19.021 20.001 OUTSIDE_CONTEXT 1
ORIGINAL_QC2 200508120300 UTC_CANDIDATE 200508111800 PA ORIGINAL_F 0.0 MODEL_REFERENCE_ENVELOPE 99.658 99.738 OUTSIDE_CONTEXT 1
ORIGINAL_QC2 200508120300 UTC_CANDIDATE 200508111800 TA ORIGINAL_F -284.222 MODEL_REFERENCE_ENVELOPE 19.021 20.001 OUTSIDE_CONTEXT 1
ORIGINAL_QC2 200508120330 UTC_CANDIDATE 200508111830 PA ORIGINAL_F 49.506 MODEL_REFERENCE_ENVELOPE 99.658 99.738 OUTSIDE_CONTEXT 1
ORIGINAL_QC2 200508120330 UTC_CANDIDATE 200508111830 TA ORIGINAL_F -132.688 MODEL_REFERENCE_ENVELOPE 19.021 20.001 OUTSIDE_CONTEXT 1
COVERAGE_INDEPENDENT_CONTEXT 37 /45; REMAINING 8 ALL_45_ORIGINAL_SOURCE_QC2_FIELDS_HOLD
SOURCE_CDS_HOURLY_REFERENCE_TABLE /home/ly3n24/japanflux_stage05au/run_20261102T224656Z/stage05au_Tmd_20050811_9h_three_variable_ERA5Land_hourly_context.tsv
EIGHT_SOURCE_QC2_EVENT_CONTEXT /home/ly3n24/japanflux_stage05au/run_20261102T224656Z/stage05au_Tmd_2005_8_original_QC2_vs_three_variable_hourly_CONTEXT_ONLY.tsv
EIGHT_FIELD_SCIENCE_HOLD_REPORT /home/ly3n24/japanflux_stage05au/run_20261102T224656Z/stage05au_Tmd_2005_8_original_QC2_ERA5Land_independent_context_HOLD.json
NO ORIGINAL ZIP / FORCING / MODEL / SLURM / AD400 OR REPAIR
```

## Scientific assessment

Original JP-Tmd 2005-08-12 local native (operator JST+9 hypothesis) eight QC2 variable fields at four distinct original source halfhours match defective same-release downscaled ERA-selected source. Independent model 9-hour reference 14:00–22:00 UTC at nearest ERA5-Land 0.1° grid has:
- `t2m - 273.15`: **19.021–20.001 °C**; original TA: **−132.399, −284.222, −132.688 °C**; 3/3 outside.
- `sp /1000`: **99.658–99.738 kPa**; original PA: **49.502, 0, 49.506 kPa**; 3/3 outside.
- `strd /3600`: **387.743–400.675 W m⁻²**; original LW_IN: **28.519 W m⁻² ×2**; 2/2 outside.

CDS original site-specific one-day ZIP has exactly 3×24 UTC-hour records, validated ZIP CRC/CSV/units/physical values/nearest source grid; 1380 bytes SHA256 `cd722e173c24154ccb5d28a632683cb39473389ac163b12439cce8e870721fe6`. Original site BIF (42.735911N/141.523147E, 117m) SHA `d5d99b265b6f4eaa29a059f7cc13ceb0e5f101979276ea090c4ec6cf5dc5c87b`. This is an independent gridded hourly **CONTEXT ONLY**, not actual tower 30-min replacements or source clock proof; original Tef/Tmd README still explicitly claims local solar time, and user-selected JST+9 is a working hypothesis.

**Cumulative independent reference coverage: 37/45 original selected F=ERA QC2 variable flags; 8 remaining.** Prior Fjy/Khw/Yms 27, then Stage05AT Tef2011 two, then Stage05AU Tmd2005 eight. All 45 original fields remain SCIENCE HOLD; **no replacement values approved**.

## Remaining exact source scope (four site×candidate-UTC days)

| Station | Original native source date | Candidate UTC date | Flagged fields |
|---|---|---|---:|
| JP-Tef | 2022-04-09 | 2022-04-08 | 2× LW_IN (both original 26.164 W m⁻²) |
| JP-Tmd | 2011-12-17 | 2011-12-16, 2011-12-17 | 3× PA (49.448, 0, 49.514 kPa) |
| JP-Tmd | 2022-04-09 | 2022-04-08 | 3× PA (49.616, 0, 49.579 kPa) |

The final 2011 JP-Tmd pressure context crosses candidate-UTC midnight and requires **both 2011-12-16 and 2011-12-17** CDS-day payloads. Therefore the remaining **8 field flags require exactly FOUR not-yet-verified site×UTC-day source payloads**, not eight separate CDS requests. Preserve operator JST+9 diagnostic hypothesis/README discrepancy and all original science HOLD until physical reference comparisons completed.
