# JapanFlux Stage05AA — actual 16-field evidence merge PASS; Stage05AB six December 2011 reference ZIP inventory next (2026-11-02)

## Actual IRIDIS6 run

```text
STAGE05AA SELF-TEST PASS | prior13 + Fjy3, existing ZIP provenance distinction, six days; NO WRITES
STAGE05AA 16-FIELD EXTERNAL ERA5L CONTEXT EVIDENCE MERGE PASS | NO CDS / SLURM / REPAIR
SOURCE_FIELDS_WITH_STRONG_INDEPENDENT_CONTEXT 16 /45
BY_SITE {'JP-Fjy': 3, 'JP-Khw': 8, 'JP-Yms': 5} DISTINCT_ORIGINAL_SITE_HALF_HOURS 11
FJY_REQUEST_LOG_PROVENANCE PREEXISTING_ZIP_ONLY_NO_ORIGINAL_CDS_SUBMISSION_LOG
OTHER_UTC_VERIFIED_FIELDS_PENDING 11 CLOCK_CONFLICT_FIELDS_HOLD 18
CDS_SITE_DAYS_WITH_VERIFIED_CONTENT 3 SUCCESSFUL_REQUEST_LOGS_OBSERVED 2 REMAINING_DAYS 6
CDS_STILL_PENDING JP-Fjy 2011-12-16 VARIABLES surface_pressure
CDS_STILL_PENDING JP-Fjy 2011-12-17 VARIABLES surface_pressure
CDS_STILL_PENDING JP-Khw 2011-12-16 VARIABLES surface_pressure
CDS_STILL_PENDING JP-Khw 2011-12-17 VARIABLES surface_pressure
CDS_STILL_PENDING JP-Yms 2011-12-16 VARIABLES surface_pressure,surface_thermal_radiation_downwards
CDS_STILL_PENDING JP-Yms 2011-12-17 VARIABLES surface_pressure,surface_thermal_radiation_downwards
UNIFIED_16_FIELD_SOURCE_EVIDENCE /home/ly3n24/japanflux_stage05aa/run_20261102T122621Z/stage05aa_16_JPF_source_fields_ERA5L_context_HOLD.tsv
SIX_REMAINING_SOURCE_GATED_DAYS /home/ly3n24/japanflux_stage05aa/run_20261102T122621Z/stage05aa_6_remaining_CDS_site_UTC_days_PREVIEW_ONLY.json
SCIENCE_COVERAGE_SUMMARY /home/ly3n24/japanflux_stage05aa/run_20261102T122621Z/stage05aa_45_source_field_independent_evidence_portfolio.json
ALL_45_SOURCE_QC2_FIELDS_STILL_HOLD_NO APPROVED_REPAIR
```

The source-backed status is **16/45 original QC2 field anomalies strongly contradicted by external hourly ERA5-Land gridded meteorological contexts** at **11 distinct site×native half-hours** (JP-Fjy 3; JP-Khw 8; JP-Yms 5). Of the remaining **29**, **11** have verified local standard time and source UTC alignment but lack independently checked reference days, and **18** are at JP-Tef/Tmd where original local-solar versus standard-time documentation conflicts.

The three site×UTC-day 2005-08-11 reference ZIP payloads (JP-Fjy, JP-Khw, JP-Yms) passed checks. **Only two actual successful CDS submission logs are available** (JP-Khw and JP-Yms); the JP-Fjy ZIP pre-existed the current submit attempt and its earlier request ID is unknown. This distinction is preserved.

## Six possible December 2011 external reference days

The Stage05AA *historical* six-day list is a plan, **not evidence all six files are absent**:

| Site | UTC day | Requested independent reference variables |
|---|---|---|
| JP-Fjy | 2011-12-16 | surface_pressure |
| JP-Fjy | 2011-12-17 | surface_pressure |
| JP-Khw | 2011-12-16 | surface_pressure |
| JP-Khw | 2011-12-17 | surface_pressure |
| JP-Yms | 2011-12-16 | surface_pressure; surface_thermal_radiation_downwards |
| JP-Yms | 2011-12-17 | surface_pressure; surface_thermal_radiation_downwards |

### Stage05AB published, first real IRIDIS run pending

[Stage05AB](../scripts/stage05/05ab_inventory_six_2011_existing_CDS_ZIP_partial_CRC_READONLY.py) checks the original `$HOME/japanflux_stage05s/downloads` read-only, validating exact Stage05AA six-day and Stage05R original BIF/UTC/variable source scope. Every site/date checks the original Stage05S output patterns:

- `JP-<site>_ERA5Land_timeseries_20111216_CSV_response.zip` and the 20111217 counterpart;
- possible `.zip.partial` incomplete downloads and actual `.csv` or `.nc` alternate output payloads.

For a pre-existing regular `.zip`, it computes the **actual SHA256**, checks ZIP member paths and CRC, requests only the original source-variable-specific CSVs, expects **24 UTC valid_time rows per variable for that one day**, verifies finite `sp`/ `strd` numeric values and units, consistency of the grid between variables and proximity to original BIF tower coordinates. A valid existing ZIP may be reused for a separate later **source-field anomaly comparison**; its original CDS request log is **not thereby proved**. Incomplete/corrupt/partial/ambiguous files remain science HOLD and are never overwritten. No file (including partial/CSV/NC) is declared a possible future one-day opt-in CDS request; Stage05AB itself makes **zero** requests.

**Stage05AB scientific limitation:** Validation of gross numerical physical plausibility and 24 hourly rows does not certify 30-minute source repairs. The grid's elevation remains unverified, especially JP-Fjy (1043m original tower). For downward thermal radiation, `strd` energy per hour divided by 3600 is an hourly average, not an exact half-hour observed mean.

All original 45 source field anomalies remain HOLD. Stage05AB writes only new report TSV/JSON, never original JPF ZIPs, forcing, model cases or Slurm jobs.
