# JapanFlux Stage05AE — actual 19 original source QC2 anomalies strongly supported; four CDS site-days remaining (2026-11-02)

## Actual IRIDIS6 operator output

The operator executed the exact GitHub source script [Stage05AE](../scripts/stage05/05ae_merge_19_context_fields_remaining4_CDS_days_NO_REPAIR.py), combining original Stage05O source QC2 and source clock provenance, Stage05AA 16 independently evidenced original source-variable candidates, Stage05AD three JP-Fjy 2011 Dec16/Dec17 QC2 pressure comparisons against separately downloaded ERA5-Land and the latest Stage05AB SHA/CRC/UTC/grid inventory.

```text
STAGE05AE SELF-TEST PASS | 16+3=19 source-QC2 fields, cross-midnight exact source event clocks, four pending days; NO WRITES
STAGE05AE MERGED 19-FIELD INDEPENDENT ERA5L CONTEXT EVIDENCE PASS | NO CDS / SLURM / REPAIR
INDEPENDENT_PHYSICAL_CONTEXT_SOURCE_FIELDS 19 /45 BY_SITE {'JP-Fjy': 6, 'JP-Khw': 8, 'JP-Yms': 5} DISTINCT_SITE_NATIVE_HALF_HOURS 14
UTC_VERIFIED_AWAITING_EXTERNAL_CONTEXT 8 CLOCK_SOURCE_CONFLICT_HOLD 18
CDS_SITE_DAYS_VERIFIED 5 PENDING_DAYS 4
CDS_PENDING JP-Khw 2011-12-16 VARS surface_pressure
CDS_PENDING JP-Khw 2011-12-17 VARS surface_pressure
CDS_PENDING JP-Yms 2011-12-16 VARS surface_pressure,surface_thermal_radiation_downwards
CDS_PENDING JP-Yms 2011-12-17 VARS surface_pressure,surface_thermal_radiation_downwards
UNIFIED_19_FIELD_EVIDENCE /home/ly3n24/japanflux_stage05ae/run_20261102T131152Z/stage05ae_19_JPF_source_QC2_independent_ERA5L_context_HOLD.tsv
SOURCE_SCOPED_4_DAY_REQUESTS_PREVIEW /home/ly3n24/japanflux_stage05ae/run_20261102T131152Z/stage05ae_4_remaining_2011_CDS_site_UTC_days_PREVIEW_ONLY.json
SOURCE_45_FIELD_COVERAGE /home/ly3n24/japanflux_stage05ae/run_20261102T131152Z/stage05ae_45_original_source_fields_independent_context_coverage.json
ALL_45_SOURCE_SELECTED_F_QC2_ANOMALIES_HOLD_NO_APPROVED_REPLACEMENTS
```

The **19/45** independent physical-context anomaly evidence tally refers to **individual original JPF source-selected F QC2 variable records**, not individual timestamps nor approved replacements. They occupy **14 unique site×original native-half-hour timestamps**. Provenance is original JPF selected F matching same-product downscaled ERA, with independent *separately downloaded* gridded hourly ERA5-Land as external contextual comparison, not an exact same-instrument/timestamp substitute.

Portfolio source audit states:
- **JP-Fjy: 6 independent-context source anomalies** (three Aug 2005; three Dec 2011);
- **JP-Khw: 8** (Aug 2005);
- **JP-Yms: 5** (Aug 2005);
- **8** UTC+9 verified source-selected QC2 fields remain unreviewed: JP-Khw **3 PA**, JP-Yms **5 PA/LW_IN**; **18** JP-Tef/Tmd original local-solar-vs-standard source-time conflict fields remain HOLD;
- original **45/45** science HOLD, no half-hour forcing substitutions, no original ZIP edits, no Slurm/AD400.

All first **5/9** independent site×UTC-day source windows have verified ZIP SHA/CRC, CSV, UTC 24-hour timestamps, grid position and variable/units. Four independent reference site-days are missing at the time of the latest Stage05AB audit: two at JP-Khw and two at JP-Yms during Dec 2011. One historic JP-Fjy 2005 ZIP has no observed original CDS request transaction ID despite valid original file content; four other CDS request successes have observed transaction logs.

## Next action, selected strictly as one source-gated date

Request only **JP-Khw 2011-12-16 UTC**, `surface_pressure`, using the existing source-gated [Stage05S](../scripts/stage05/05s_ERA5Land_timeseries_one_day_CDS_pilot_opt_in.py) one-site-one-day workflow. The read-only preflight should verify Stage05AE four remaining original source site-days and the actual latest Stage05AB all-six original site/date inventory, then check **no existing target, .partial, alternative CSV/NC**. Original BIF tower location in existing source manifest should be used; do not invent latitude/longitude, request the other site/days or patch past sources.

After operator-submitted request, re-run the pinned Stage05AB against its six original December site/date windows, requiring source/variable/UTC/ZIP SHA/CRC and physical checks. Successful download/content validation should increase **payload coverage from 5/9 to 6/9**; it should **not increase field anomaly evidence from 19/45** until the second day **JP-Khw 2011-12-17 UTC** is independently retrieved and the original source time-specific 3h context is calculated across day boundaries.

Science caution: JP-Khw nearest-grid surface pressure may differ from true tower pressure because of terrain, but abnormally low original QC2 source values are being investigated. The independent hourly gridded reference is context only, not a half-hour correction, and all original selected F fields remain HOLD.
