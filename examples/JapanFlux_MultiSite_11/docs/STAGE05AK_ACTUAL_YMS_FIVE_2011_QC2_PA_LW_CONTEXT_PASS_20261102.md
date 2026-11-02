# JapanFlux Stage05AK — actual JP-Yms December 2011 five source QC2 variable comparisons PASS (2026-11-02)

## Actual operator-run source provenance, unit/time comparison

The operator downloaded the SHA-pinned original Stage05AK script, passed self-test and verified original 2011-12-16 and 2011-12-17 JP-Yms CDS ZIP SHA256 checks. Strict original source Stage05O/05R, Stage05AH prior 22-field provenance, current Stage05AB six-day ZIP CRC/CSV content and grid science gate all passed. The external product was the separate **ERA5-Land hourly time series**, not original embedded `ERA` columns, and no original source ZIP or forcing was changed.

```text
STAGE05AK SELF-TEST PASS | original 27/22+5 mixed Yms PA/LW source scope, CDS 1h DEACCUMULATED strd/3600, cross-midnight UTC and HOLD; NO NETWORK/WRITES
/home/ly3n24/japanflux_stage05s/downloads/JP-Yms_ERA5Land_timeseries_20111216_CSV_response.zip: OK
/home/ly3n24/japanflux_stage05s/downloads/JP-Yms_ERA5Land_timeseries_20111217_CSV_response.zip: OK
STAGE05AK JP-YMS TWO-DAY PA+LW INDEPENDENT HOURLY CONTEXT PASS | NO CDS / SLURM / REPAIR
ORIGINAL_YMS_SOURCE_FIELDS 5 BY_VARIABLE {'LW_IN': 2, 'PA': 3}
OUTSIDE_HOURLY_ENVELOPE {'LW_IN': 2, 'PA': 3} SOURCE_REFERENCE_PAIRS 17
TWO_DAY_INDEPENDENT_HOURLY_VALUES_PER_VARIABLE 48 GRID (34.80000000000106, 135.79999999999654) TOWER_BIF (34.790278, 135.840939, 220.0)
SOURCE_FIELD 201112170600 LW_IN ORIGINAL_F 44.79 UNIT W m-2 REFERENCE_UTC 2011-12-16T20:00Z;2011-12-16T21:00Z;2011-12-16T22:00Z;2011-12-16T23:00Z REFERENCE_VALUES 226.992222;221.921111;239.925000;236.807222 OUTSIDE 1 SCIENCE HOLD_CONTEXT_COMPARISON_ONLY_NOT_YET_APPROVED_AS_STRONG_EVIDENCE
SOURCE_FIELD 201112170630 LW_IN ORIGINAL_F 44.79 UNIT W m-2 REFERENCE_UTC 2011-12-16T20:00Z;2011-12-16T21:00Z;2011-12-16T22:00Z;2011-12-16T23:00Z REFERENCE_VALUES 226.992222;221.921111;239.925000;236.807222 OUTSIDE 1 SCIENCE HOLD_CONTEXT_COMPARISON_ONLY_NOT_YET_APPROVED_AS_STRONG_EVIDENCE
SOURCE_FIELD 201112170630 PA ORIGINAL_F 68.16 UNIT kPa REFERENCE_UTC 2011-12-16T21:00Z;2011-12-16T22:00Z;2011-12-16T23:00Z REFERENCE_VALUES 99.985360;100.061340;100.113080 OUTSIDE 1 SCIENCE HOLD_CONTEXT_COMPARISON_ONLY_NOT_YET_APPROVED_AS_STRONG_EVIDENCE
SOURCE_FIELD 201112170700 PA ORIGINAL_F 37.349 UNIT kPa REFERENCE_UTC 2011-12-16T22:00Z;2011-12-16T23:00Z;2011-12-17T00:00Z REFERENCE_VALUES 100.061340;100.113080;100.187720 OUTSIDE 1 SCIENCE HOLD_CONTEXT_COMPARISON_ONLY_NOT_YET_APPROVED_AS_STRONG_EVIDENCE
SOURCE_FIELD 201112170730 PA ORIGINAL_F 68.202 UNIT kPa REFERENCE_UTC 2011-12-16T22:00Z;2011-12-16T23:00Z;2011-12-17T00:00Z REFERENCE_VALUES 100.061340;100.113080;100.187720 OUTSIDE 1 SCIENCE HOLD_CONTEXT_COMPARISON_ONLY_NOT_YET_APPROVED_AS_STRONG_EVIDENCE
FIVE_FIELD_CONTEXT_TSV /home/ly3n24/japanflux_stage05ak/run_20261102T200119Z/stage05ak_5_JP_Yms_2011_QC2_PA_LW_vs_ERA5L_hourly_CONTEXT_HOLD.tsv
SCIENCE_CONTEXT_JSON /home/ly3n24/japanflux_stage05ak/run_20261102T200119Z/stage05ak_2011_Yms_5_original_source_fields_science_context_REVIEW_ONLY.json
PRESERVE_22_PRIOR_STRONG_EVIDENCE; ALL_45_ORIGINAL_FIELD_CANDIDATES_HOLD_NO_REPAIR
```

The five new JP-Yms source-field references are **both ERA5-Land hourly variables**: `sp` Pa / 1000 → kPa, and original timeseries `strd` deaccumulated 1-hour J m⁻² / 3600 → interval mean W m⁻². The longwave hourly `valid_time` denotes the **end of its 1-hour interval**; Stage05AK used a conservative four-hour neighbouring envelope (-1,0,+1,+2 hours relative to 30-minute source floor) rather than pretending hourly gridded values were contemporaneous tower half-hour point measurements. No second deaccumulation of `strd` was applied. Relevant ECMWF dataset metadata: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries and product guide https://confluence.ecmwf.int/pages/viewpage.action?pageId=699689224.

This source-verified result establishes **five additional original variable records outside independent hourly context**, including grossly low pressure 37.349–68.202 kPa vs ~100 kPa, and downward LW 44.79 W m⁻² vs ~222–240 W m⁻². It covers **four** unique original native halfhour timestamps (06:00, 06:30, 07:00, 07:30 JST, with two variable fields at 06:30).

## Evidence counts must distinguish context from science approval

Before Stage05AK: **22/45** original QC2 fields were **already registered with strong independent physical context evidence**, spanning **17** unique original station×native halfhours. Stage05AK reviewed the remaining **5**, all 5 returned `outside_independent_hourly_envelope == 1`; thus **27/45 have now been independently physically compared** and all 27 have contextual discrepancies, across **21** unique station×native halfhours. The 5 new fields remain explicitly labelled `HOLD_CONTEXT_COMPARISON_ONLY_NOT_YET_APPROVED_AS_STRONG_EVIDENCE` in source outputs; this must **not** be silently relabelled as formally approved replacements or automatically added to the previous 22-field approved-*evidence-class* register. No 30-minute meteorological replacement scientifically approved.

The remaining **18/45 original flagged variable fields** (JP-Tef4, JP-Tmd14) have **unresolved time provenance**, because original source README and site-specific materials conflict on local solar versus standard time; **do not infer UTC or download unscoped CDS**. They are at 14 unique source site×native halfhour timestamps. Original source anomalies **45/45** retain science HOLD.

The full source reference registry has **9/9 separately verified site×UTC-day payloads**: the latest Stage05AB validates six Dec2011 days; the three earlier Aug2005 site-days were verified in preceding original Stage05Y/Z/AA. All 9 dates validated does not mean the 18 Tef/Tmd clock-unresolved fields have been assessed.

Next: merge original Stage05AH 22 strong-context source variable records with Stage05AK five **context-only candidate** records in a new source-provenance-gated and science-HOLD unified register. Then address the 18 original JP-Tef/Tmd timebase conflicts by acquiring original site metadata, without source timestamp guessing or automatically repairing forcing.
