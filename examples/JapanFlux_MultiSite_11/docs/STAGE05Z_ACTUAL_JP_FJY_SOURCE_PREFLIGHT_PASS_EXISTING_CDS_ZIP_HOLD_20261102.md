# JapanFlux Stage05Z actual JP-Fjy source preflight PASS; Stage05S download not attempted due to existing destination (2026-11-02)

## Actual operator output

The operator ran the SHA-verified [Stage05Z](../scripts/stage05/05z_JP_Fjy_CDS_pressure_preflight_and_raw_ZIP_audit_READONLY.py) source-only preflight, then invoked the [Stage05S](../scripts/stage05/05s_ERA5Land_timeseries_one_day_CDS_pilot_opt_in.py) single-day CDS requester for JP-Fjy.

```text
STAGE05Z SELF-TEST PASS | source-specific UTC+9 QC2/ERA equality, one-variable 24-hour independent ZIP; NO WRITES
STAGE05Z JP-FJY ORIGINAL SOURCE/PENDING CDS DAY PREFLIGHT PASS
SITE JP-Fjy UTC_DATE 2005-08-11 VARIABLE surface_pressure
SOURCE_ORIGINAL_QC2_FIELDS_ON_DAY 3 REQUIRED_SOURCE_VARIABLE_HOUR_PAIRS 9
TOWER_BIF_LAT_LON_ELEV (35.45454, 138.76225, 1043.0) BIF_SHA b59835ff3347fc17058319040155ae0bd65ae2241767c595869fff6be02adc62
CDS_REQUEST_ELIGIBLE_SOURCE_HOURS 14:00,15:00,16:00,17:00,18:00,19:00,20:00,21:00,22:00
NO CDS, NO ZIP, NO WRITES. One operator-authenticated Stage05S CDS request may be submitted separately.
=== JP-Fjy ONE-DAY CDS REQUEST ===
RuntimeError: Target already exists: refuse overwrite /home/ly3n24/japanflux_stage05s/downloads/JP-Fjy_ERA5Land_timeseries_20050811_CSV_response.zip
```

**Preflight passed.** Stage05S raised the collision check before `cdsapi.Client()` or `client.retrieve(...)`, so **no new CDS request was submitted in this run and nothing was overwritten**. Importantly, Stage05S's check tests *either* the final `.zip` pathname *or* an adjacent `.zip.partial` pathname, but prints the same target string for either condition. The operator log therefore **does not prove the final ZIP is present or valid**. It may be a complete earlier download, an invalid/stale/wrong-content ZIP, or only a partial leftover. The original observed JP-Fjy download state remains **UNVERIFIED** and the confirmed independently downloaded count stays **2/9** (JP-Khw and JP-Yms on 2005-08-11 UTC). Previously evidenced source anomalies stay **13/45**, 14 UTC-verified source anomalies pending independent comparisons, 18 JP-Tef/Tmd source clock conflict HOLD.

## Next read-only operation, no CDS or forcing writes

1. List exact `JP-Fjy_ERA5Land_timeseries_20050811_CSV_response.zip` and `.zip.partial` with size and timestamps; do not delete, rename or overwrite either.
2. If the **final ZIP** is a real regular file, compute SHA256 and read ZIP entries, integrity-test CRC, and inspect original CSV header/first rows. The SHA must be **observed from this existing file**, never guessed.
3. Reuse Stage05Z in inspection mode, supplying `--inspect-cds-zip` the **same already-existing raw file**, and `--expected-sha256` the observed digest. Stage05Z checks the one-variable original ERA5-Land CSV, 24 UTC hourly `valid_time` values for exactly 2005-08-11, finite surface pressure Pa, grid proximity to the original 35.45454°N/138.76225°E tower, original 1043m BIF altitude/source QC2/UTC+9, and writes only **separate** derived report TSV/JSON. If this passes, the earlier CDS download is retrospectively verified as a compatible *payload*, but **without original CDS request provenance the retrieval itself is not newly proven by this run**.
4. If only `.zip.partial` exists or final ZIP is malformed, return explicit SCIENCE HOLD (do not infer success and do not redownload or overwrite without separate safe recovery decision).

The original high-elevation JP-Fjy site requires **ERA5-Land grid elevation/geopotential check** before treating differences in surface pressure as site-source defects. An hour-resolved nearest-grid pressure is not an approved 30-minute tower pressure replacement.

No changes to original JPF ZIPs or forcing, model cases or Slurm; all 45 original abnormal variable records HOLD.
