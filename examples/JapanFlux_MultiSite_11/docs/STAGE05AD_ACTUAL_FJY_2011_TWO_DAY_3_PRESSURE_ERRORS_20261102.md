# JapanFlux Stage05AD — actual JP-Fjy 2011-12-16/17 cross-midnight independent ERA5-Land audit PASS (2026-11-02)

## Original CDS request and validated reference responses

The operator executed the SHA-pinned Stage05S one-day JP-Fjy `surface_pressure` request for **2011-12-17 UTC**. Actual external CDS request ID **`af9aaa98-509f-4d47-987d-bd32513600d1`**, statuses `accepted`→`successful`, wrote **492-byte ZIP**, original SHA256 **`f553e574a72e409c988460f7052100496c264321a65a46e5a80a636982d3deed`** at:

```text
/home/ly3n24/japanflux_stage05s/downloads/JP-Fjy_ERA5Land_timeseries_20111217_CSV_response.zip
```

The preceding Dec 16 response had request ID `987925b9-f0ed-454c-9ef2-bd90170254fc`, **493 bytes**, original SHA256 `cc172d7c18e7b7b5199aa7cccc8b941c6115863861860f0618d8b33d4f577c9a`. The operator re-ran Stage05AB on original Stage05S downloads, validating ZIP CRC, 24 UTC hours, variable/units and same grid **35.50000000000107°N,138.79999999999643°E** for each of the two days. Four other original December 2011 site×UTC-day files (JP-Khw/Yms 2011-12-16/17) remained **ABSENT** including `.partial`.

Latest source audit:

```text
STAGE05AB SIX 2011-CDS DAY EXISTING FILES/CRC/TIME/GRID SOURCE INVENTORY PASS | NO CDS / SLURM / REPAIR
COUNTS {'REUSE_VALID_EXISTING_ZIP_FOR_SEPARATE_SOURCE_QC2_REVIEW_NO_REDOWNLOAD': 2, 'NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT': 4}
SOURCE_AUDIT /home/ly3n24/japanflux_stage05ad/inventory_20261102T130521Z/stage05ab_six_2011_CDS_original_archive_science_audit.json
```

## Stage05AD original QC2 source vs 48-hour independent pressure contexts

The operator executed [Stage05AD](../scripts/stage05/05ad_JP_Fjy_2011_two_day_pressure_3_QC2_independent_context_NO_REPAIR.py) with both original SHA-verified CSV ZIPs, original Stage05O source QC2 records and original Stage05R source-hour provenance. The actual result was:

```text
STAGE05AD SELF-TEST PASS | source-verified two-day UTC midnight, exact per-variable Stage05P context, SHA/CRC; NO WRITES
STAGE05AD JP-FJY TWO-DAY INDEPENDENT ERA5L SOURCE PA AUDIT PASS | NO CDS / SLURM / REPAIR
INDEPENDENT_HOURLY_POINTS 48 SOURCE_REQUEST_HOUR_PAIRS 9
ORIGINAL_SOURCE_QC2_FIELDS 3 OUTSIDE_HOURLY_CONTEXT 3
CDS_GRID (35.50000000000107, 138.79999999999643) TOWER_BIF (35.45454, 138.76225, 1043.0)
SOURCE_FIELD 201112170630 PA_F 45.123 REFERENCE_UTC 2011-12-16T21:00Z;2011-12-16T22:00Z;2011-12-16T23:00Z REFERENCE_KPA 88.366360;88.429340;88.489080 OUTSIDE 1 STATUS HOLD_NO_APPROVED_30MIN_PRESSURE_REPAIR
SOURCE_FIELD 201112170700 PA_F 0.334 REFERENCE_UTC 2011-12-16T22:00Z;2011-12-16T23:00Z;2011-12-17T00:00Z REFERENCE_KPA 88.429340;88.489080;88.564720 OUTSIDE 1 STATUS HOLD_NO_APPROVED_30MIN_PRESSURE_REPAIR
SOURCE_FIELD 201112170730 PA_F 45.211 REFERENCE_UTC 2011-12-16T22:00Z;2011-12-16T23:00Z;2011-12-17T00:00Z REFERENCE_KPA 88.429340;88.489080;88.564720 OUTSIDE 1 STATUS HOLD_NO_APPROVED_30MIN_PRESSURE_REPAIR
FIELD_EVIDENCE_TABLE /home/ly3n24/japanflux_stage05ad/source_review_20261102T130521Z/stage05ad_Fjy_2011_3_original_QC2_vs_two_day_independent_CDS_HOLD.tsv
SCIENCE_HOLD_SUMMARY /home/ly3n24/japanflux_stage05ad/source_review_20261102T130521Z/stage05ad_Fjy_two_day_source_CDS_science_HOLD_summary.json
ALL_45_JPF_QC2_FIELD_CANDIDATES_CONTINUE_HOLD_NO_REPLACEMENT
```

The 2011 source selected `F` equals JPF same-release `ERA` at QC2 for all three anomalous pressures. Separate ECMWF hourly contexts strongly contradict all three values, including the extreme `0.334 kPa`. These are **external physical context evidence**, not approved replacement data; original JP-Fjy tower elevation is **1043 m**, and returned grid elevation/geopotential is **not independently verified**.

## Portfolio after Stage05AD

- **19/45** original source field anomalies have strong independently sourced ERA5-Land contextual evidence: JP-Fjy **6** (3 in Aug 2005 +3 in Dec 2011), JP-Khw **8**, JP-Yms **5**; **14 distinct site×source native half-hours**.
- **8** other UTC-verified source fields still await external per-field comparison (JP-Khw **3** + JP-Yms **5**); **18** JP-Tef/Tmd original solar/standard clock conflict fields remain HOLD.
- **5/9** original independent reference site×UTC-day contents validated (three Aug 2005 ZIPs + two Dec 2011 Fjy ZIPs), **4/9** other Dec 2011 days lack reference payloads.
- Successful CDS request transaction logs independently observed for **four** site-days (JP-Khw 2005, JP-Yms 2005, JP-Fjy 2011 Dec16 and Dec17). The existing JP-Fjy 2005 ZIP passed SHA/CRC/CSV/time/grid audit, but original request ID remains unobserved.
- **All 45 original source field candidates are still HOLD**. Neither this stage nor preceding tests performed original ZIP edits, forcing/model changes, Slurm jobs, or scientifically approved 30-minute replacements.

[Stage05AE 19-evidence consolidation + remaining four source-gated CDS date preview](../scripts/stage05/05ae_merge_19_context_fields_remaining4_CDS_days_NO_REPAIR.py) is expected next, **not yet run on the operator IRIDIS6 output**. Subsequent one-by-one independent CDS dates should cover JP-Khw (2011-12-16/17) then JP-Yms (2011-12-16/17), avoiding repeat requests and keeping Tef/Tmd timing unresolved until provenance is independently settled.
