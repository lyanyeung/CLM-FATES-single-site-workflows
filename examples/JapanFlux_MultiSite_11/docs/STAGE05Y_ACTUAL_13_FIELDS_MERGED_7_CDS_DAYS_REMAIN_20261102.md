# JapanFlux Stage05Y actual 13-field independent ERA5-Land evidence merger — completed 2026-11-02

## Operator-observed results

The operator ran the pinned [Stage05Y](../scripts/stage05/05y_merge_Khw8_Yms5_independent_evidence_remaining7_NO_REPAIR.py) on the original Stage05O source-QC2 evidence, actual Stage05V JP-Khw 8-field independent ERA5-Land evidence, actual Stage05X JP-Yms 5-field independent evidence, Stage05W2 original CDS SHA-source audit and Stage05V remaining date plan.

```text
STAGE05Y SELF-TEST PASS | 8+5=13 original QC2 fields, 7 remaining CDS site-days, all 45 HOLD; NO WRITES
STAGE05Y 13-FIELD INDEPENDENT CDS EVIDENCE MERGE PASS | NO CDS / ZIP / SLURM / REPAIR
INDEPENDENTLY_EVIDENCED 13 /45 ORIGINAL_QC2_FIELDS
EVIDENCED_BY_SITE {'JP-Khw': 8, 'JP-Yms': 5}
EVIDENCED_UNIQUE_SITE_HALF_HOURS 8
UTC_VERIFIED_NOT_YET_COMPARED 14 TIME_BASIS_HOLD 18
CDS_DOWNLOADED_SITE_DAYS 2 REMAINING_SITE_DAYS 7
CDS_REMAINING JP-Fjy 2005-08-11 VARIABLES surface_pressure
CDS_REMAINING JP-Fjy 2011-12-16 VARIABLES surface_pressure
CDS_REMAINING JP-Fjy 2011-12-17 VARIABLES surface_pressure
CDS_REMAINING JP-Khw 2011-12-16 VARIABLES surface_pressure
CDS_REMAINING JP-Khw 2011-12-17 VARIABLES surface_pressure
CDS_REMAINING JP-Yms 2011-12-16 VARIABLES surface_pressure,surface_thermal_radiation_downwards
CDS_REMAINING JP-Yms 2011-12-17 VARIABLES surface_pressure,surface_thermal_radiation_downwards
MERGED_SOURCE_EVIDENCE /home/ly3n24/japanflux_stage05y/run_20261102T114507Z/stage05y_13_source_fields_independent_CDS_context_HOLD.tsv
REMAINING_CDS_PREVIEW /home/ly3n24/japanflux_stage05y/run_20261102T114507Z/stage05y_7_remaining_CDS_site_UTC_days_PREVIEW_ONLY.json
SOURCE_COVERAGE_SUMMARY /home/ly3n24/japanflux_stage05y/run_20261102T114507Z/stage05y_45_source_field_science_coverage_summary.json
ALL_45_SOURCE_QC2_FIELDS_HOLD; NO SCIENTIFICALLY_APPROVED_REPLACEMENT VALUES
```

**Verified scientific coverage**: 13/45 original anomalous source-selected variable records (JP-Khw 8 and JP-Yms 5) have *strong independent hourly context evidence* of severe input defects at 8 distinct source site×native half-hours. 14 other fields are from the three original BIF/README time-verified UTC+9 sites but do not yet have source-specific independent comparisons. 18 fields at JP-Tef/Tmd have original README local-solar versus local-standard time provenance conflicts, so must **not** be blindly shifted by nine hours. Every one of 45 remains scientific HOLD; no original source/forcing/model changes, correction values or Slurm submissions.

**Actual external retrieval status**: two site×UTC-day CDS ERA5-Land ZIPs independently downloaded (JP-Khw 2005-08-11 and JP-Yms 2005-08-11); seven further site×UTC-day requests remain. The previously completed Stage05Y is a read-only **audit**, not a third CDS request.

## Next recommended third-site external pressure reference

**JP-Fjy 2005-08-11 UTC**, variable only `surface_pressure`, original BIF tower location **35.45454°N,138.76225°E**, original BIF tower elevation **1043m**, source SHA256 `b59835ff3347fc17058319040155ae0bd65ae2241767c595869fff6be02adc62`. The 2005-08-11 source-relevant UTC hour union is 14:00–22:00 based on original Stage05S preview; the exact source-variable-hour keys must be checked against Stage05R and source event UTC starts rather than assuming a Cartesian product (the Stage05W false gate incident demonstrates why).

Use the already executed [Stage05S single-site/day explicit CDS request](../scripts/stage05/05s_ERA5Land_timeseries_one_day_CDS_pilot_opt_in.py) once for JP-Fjy 2005-08-11 only, gated against the Stage05Y seven-day report. No automatic repeated/batch CDS calls. CDS returns 24 hours of pressure for this full UTC date; after download, inspect its real original SHA and CSV layout before any numerical comparison.

**Important elevation/representativeness issue:** JP-Fjy's original 1043m tower elevation is substantially higher than the other pilots (JP-Khw 196m, JP-Yms 220m). The ECMWF nearest 0.1° grid point may have a different model height and thus different surface pressure. A large but **physically plausible** tower-grid pressure difference is not automatically source corruption. Strictly separate source nonphysical values from elevation-induced offsets; a pressure altitude correction needs independently established grid geopotential, not speculation.

[CDS official hourly time-series](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries) documents the point/hourly product, but **no JP-Fjy independent values are downloaded yet**. The current third-party numerical source flag status remains HOLD.
