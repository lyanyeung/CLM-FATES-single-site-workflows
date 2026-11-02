# Stage05W — Actual second CDS ZIP downloaded, awaiting CSV inspection (2026-11-02)

The operator ran a source-gated JP-Yms single-day `reanalysis-era5-land-timeseries` request (original BIF location 34.790278°N, 135.840939°E; elevation 220 m), selecting `surface_pressure` and `surface_thermal_radiation_downwards` for **2005-08-11 UTC**. The original Stage05W source-request preflight passed. The existing Stage05S CDS request logged `accepted` followed by **`successful`**, with CDS request ID `15164c26-0daa-4b45-a512-08d506fad40a`.

Exact downloaded unmodified response on IRIDIS6:
```text
/home/ly3n24/japanflux_stage05s/downloads/JP-Yms_ERA5Land_timeseries_20050811_CSV_response.zip
DETECTED_PAYLOAD ZIP BYTES 936
SHA256 4bf228a3a53ab7fc6751b8e7438fb459570536ce6f54af2f81de5afc083b59d5
```

This is the second independently retrieved source/day after the JP-Khw 2005-08-11 pilot (original SHA256 `111c761e432f77c7fa287d7b9ee3d29a89405a33ece970f8ac81896ebee818b0`). **2/9** independently required site×UTC-day windows are downloaded; **7** are not yet requested. The JP-Yms ZIP contents **have NOT yet been opened**, so numeric values, rows/variable, returned grid coordinates, validity times and units are not confirmed. The only externally supported per-field anomalies remain **JP-Khw eight original QC2 source-selected fields at four half-hours**; the remaining **37** include 19 UTC-convertible source records requiring other external comparisons and 18 JP-Tef/Tmd native-time-only source records pending local solar-versus-standard source clock reconciliation. All **45** original flags remain scientific HOLD.

## Next step — run Stage05W on this exact raw CDS ZIP

The [read-only Stage05W original ZIP SHA and CSV structure audit](../scripts/stage05/05w_JP_Yms_20050811_independent_CDS_zip_source_audit_NO_REPAIR.py) is published but **has not been executed against this actual operator ZIP**. Pass the observed new SHA above as `--expected-sha256`, and the completed Stage05V remaining-site/day JSON and Stage05R 87 source-verifed UTC-hour table. The script checks exact archive identity, expected 2 CSVs × 24 hourly values, UTC timestamps, nearest-grid position, source BIF/UTC scope, and provisional Pa→kPa / hourly accumulated J m⁻²÷3600→W m⁻² conversions; **no CDS call, source modification, forcing repair, Slurm or AD400**.

If the actual ZIP's CSV schema differs from the earlier JP-Khw response, preserve original metadata and review the schema instead of inventing values. Hourly ERA5-Land radiation remains contextual to the JPF half-hour source signal, not a correction.
