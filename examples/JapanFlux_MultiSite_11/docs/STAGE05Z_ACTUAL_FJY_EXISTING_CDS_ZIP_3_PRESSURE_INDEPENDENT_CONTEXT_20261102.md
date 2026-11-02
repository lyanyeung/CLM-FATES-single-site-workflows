# JapanFlux Stage05Z: actual pre-existing JP-Fjy CDS-format ZIP verified and 3/3 QC2 pressure source defects supported (2026-11-02)

## Operator-observed read-only audit PASS

The operator inspected the pre-existing JP-Fjy CDS time-series payload rather than issuing another CDS request:

```text
-rw-r--r-- 1 ly3n24 wr 484 Nov  2 11:53 /home/ly3n24/japanflux_stage05s/downloads/JP-Fjy_ERA5Land_timeseries_20050811_CSV_response.zip
0c51e921a3c35b15dae2c33576517e93ca49b2e0ab584212fc8d505fa3efaad3  /home/ly3n24/japanflux_stage05s/downloads/JP-Fjy_ERA5Land_timeseries_20050811_CSV_response.zip
ZIP CRC PASS
ZIP MEMBERS: 1
MEMBER: reanalysis-era5-land-timeseries-sfc-pressure-precipitation7z_b_nxt.csv
BYTES: 1622
CSV SAMPLE:
valid_time,sp,latitude,longitude
2005-08-11 00:00:00,88640.15,35.50000000000107,138.79999999999643
2005-08-11 01:00:00,88643.35,35.50000000000107,138.79999999999643
...
STAGE05Z JP-FJY ORIGINAL SOURCE/PENDING CDS DAY PREFLIGHT PASS
SITE JP-Fjy UTC_DATE 2005-08-11 VARIABLE surface_pressure
SOURCE_ORIGINAL_QC2_FIELDS_ON_DAY 3 REQUIRED_SOURCE_VARIABLE_HOUR_PAIRS 9
TOWER_BIF_LAT_LON_ELEV (35.45454, 138.76225, 1043.0)
STAGE05Z INDEPENDENT JP-FJY CDS ZIP/SOURCE CONTEXT AUDIT PASS | NO CDS / SLURM / REPAIR
CDS_GRID [(35.50000000000107, 138.79999999999643)]
RAW_ZIP_SHA256 0c51e921a3c35b15dae2c33576517e93ca49b2e0ab584212fc8d505fa3efaad3
HOURLY_ROWS 24
CDS_UTC_HOUR 17 SP_KPA 88.65443
CDS_UTC_HOUR 18 SP_KPA 88.62628
CDS_UTC_HOUR 19 SP_KPA 88.67142
ORIGINAL_SOURCE 200508120230 F_PA_KPA 45.16 CDS_CONTEXT_KPA 88.65443;88.62628;88.67142 OUTSIDE 1 STATUS HOLD_GRID_ALTITUDE_UNVERIFIED_NO_POINTWISE_HALF_HOUR_REPLACEMENT
ORIGINAL_SOURCE 200508120300 F_PA_KPA 0.334 CDS_CONTEXT_KPA 88.62628;88.67142;88.69234 OUTSIDE 1 STATUS HOLD_GRID_ALTITUDE_UNVERIFIED_NO_POINTWISE_HALF_HOUR_REPLACEMENT
ORIGINAL_SOURCE 200508120330 F_PA_KPA 45.161 CDS_CONTEXT_KPA 88.62628;88.67142;88.69234 OUTSIDE 1 STATUS HOLD_GRID_ALTITUDE_UNVERIFIED_NO_POINTWISE_HALF_HOUR_REPLACEMENT
INDEPENDENT_PRESSURE_HOURS /home/ly3n24/japanflux_stage05z/existing_zip_audit_20261102T121004Z/stage05z_Fjy_20050811_CDS_surface_pressure_24h_HOLD.tsv
SOURCE_COMPARISON /home/ly3n24/japanflux_stage05z/existing_zip_audit_20261102T121004Z/stage05z_Fjy_20050811_original_JPF_vs_independent_hourly_CONTEXT_HOLD.tsv
AUDIT /home/ly3n24/japanflux_stage05z/existing_zip_audit_20261102T121004Z/stage05z_independent_CDS_original_source_audit.json
ALL_45_SOURCE_FIELDS_REMAIN_HOLD; GRID_HEIGHT_UNKNOWN; NO APPROVED HALF_HOUR_REPAIR
```

The ZIP is a complete, source-compatible ERA5-Land-format CSV payload with the expected UTC day, `sp` in Pa and a single nearest land-grid center; 24 hourly original values were parsed. Original source BIF JP-Fjy location is **35.45454°N, 138.76225°E, 1043m**, BIF SHA256 `b59835ff3347fc17058319040155ae0bd65ae2241767c595869fff6be02adc62`. Returned grid is **35.5°N, 138.8°E**. The original CDS request transaction ID for this **pre-existing** file was **not provided**. Stage05S saw the existing target before client submission, and Stage05Z performed zero network requests. Do not retrospectively misreport a newly observed successful request or an original request ID.

### Original selected-source QC2 comparison

| JST 2005-08-12 native start | Original JPF PA, QC2 (kPa) | Three neighboring *independent hourly grid* surface pressures (kPa) | Inference |
|---|---:|---|---|
| 02:30 | 45.160 | 88.65443; 88.62628; 88.67142 | Very severe source-grid context inconsistency |
| 03:00 | 0.334 | 88.62628; 88.67142; 88.69234 | Not plausible at near-surface measurement level |
| 03:30 | 45.161 | 88.62628; 88.67142; 88.69234 | Very severe source-grid context inconsistency |

The three original selected-F records were all originally tagged QC2 and equal to same-release JPF ERA fill values; the newly verified source-independent hourly physical ranges support source processing errors. **High-elevation caution**: the tower has 1043m BIF elevation; the actual ERA5-Land grid geopotential/elevation remains unverified, so even strongly discrepant conditions **cannot** justify using the raw grid pressure as an exact source half-hour replacement. The drastic 0.334/45kPa anomalies are not explained by reasonable terrain representation alone.

## Original evidence coverage

- JP-Khw: 8 original QC2 fields with independent hourly ERA5-Land contexts (actual CDS successful request logged)
- JP-Yms: 5 original QC2 fields with independent hourly ERA5-Land contexts (actual CDS successful request logged)
- JP-Fjy: **3** original QC2 source field comparisons against a separately provided, **pre-existing** CDS-format ERA5-Land ZIP whose SHA, CRC, schema, 24 UTC hours and grid passed; **original CDS request log not observed**
- **16/45** original source anomalous fields at **11** unique site×native half-hours have strong grid-context evidence, **11** further UTC-verified fields remain to be checked, and **18** JP-Tef/Tmd candidate fields lack resolved original time convention
- Actual original reference payloads available for **3 of 9** source site×UTC-day windows; **6** day windows remain without verified payloads. The distinction between 3 valid data payloads and 2 observed successful CDS transaction logs must remain visible.
- All **45** original flags remain source-science HOLD; no approved half-hour replacements, original source edits, forcing edits, Slurm or AD400

## Stage05AA next

[Stage05AA](../scripts/stage05/05aa_merge_16_independent_context_fields_and_6_CDS_days_NO_REPAIR.py) is published but **not yet run on IRIDIS6**. It independently checks Stage05O original 27 UTC-convertible plus 18 time-ambiguous source fields, Stage05Y prior 13-field evidence register / 7-day request plan, Stage05Z actual 3-field and independent source-grid audit. It builds a source-gated **16-field independent-physics evidence register** and revised **six remaining CDS site×UTC-day windows**, preserving all original HOLD values and annotating the original JP-Fjy CDS submission-log uncertainty. Read-only, no CDS, ZIP or model access; first actual operator run pending.

The six remaining day windows are JP-Fjy/JP-Khw/JP-Yms on **2011-12-16** and **2011-12-17** UTC, one day per site. Check for pre-existing ZIP or `.partial` files before any future CDS submissions; do not assume no earlier download merely because the Stage05Y ledger originally listed these as pending.
