# Batch03 Stage11N — US-NC2 original clock and grid availability verified

**Date:** 2026-10-24. Source: operator-provided full IRIDIS6 read-only Stage11N output. `--self-test` PASS; four exact native half-hour boundaries checked; Stage11N did not write forcing, original, ledger, report, model job or UTC shift.

```
STAGE11N SUMMARY: 4/4 native boundaries checked; published_offset_present=True; grid_2025_candidate_present=False; offset_authorized=0; boundary_repair_authorized=0; Postv5_approved=0; DATM_ready=0; spinup=0
```

## Verified original BIF metadata

- **Site:** `US-NC2`
- **Original release:** `AMF_US-NC2_FLUXNET_2005-2025_v1.3_r1`
- **BIF GROUP_ID 12759:** `LOCATION_COMMENT=Tower location`; `LOCATION_ELEV=5 m`, `LOCATION_LAT=35.8030`, `LOCATION_LONG=-76.6685`
- **BIF GROUP_ID 12767:** `UTC_OFFSET=-5`
- **Scientific status:** UTC−5 is a *published metadata value*, not a separately approved clock mapping for native timestamps. Distinguish fixed local standard time from daylight time; do not silently use DST.

All eight original half-hour source endpoints exist and are adjacent:

| Edge | Native timestamp A | Native timestamp B | Source TA_F (°C), A→B | Source VPD_F (hPa), A→B | Original VPD_F_QC |
| --- | --- | --- | --- | --- | --- |
| MAR18_NEW_START | 202503181800 | 202503181830 | 13.899 → 10.966 | 14.210 → 12.900 | 2 → 2 |
| MAR23_OLD_START | 202503230830 | 202503230900 | 12.948 → 13.818 | 14.315 → 19.544 | 1 → 1 |
| MAR23_NEW_END | 202503231500 | 202503231530 | 17.634 → 17.821 | 18.501 → 16.448 | 1 → 1 |
| MAR25_NEW_END | 202503251000 | 202503251030 | 17.430 → 18.070 | 19.128 → 20.786 | 1 → 1 |

## External evidence status

Pre-existing Stage09 ERA5-Land evidence search path:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/external_evidence/era5land_timeseries/US-NC2/2025`

**Result:** no standard existing 2025 US-NC2 bundle was found **at this path**, not proof that no file exists anywhere on IRIDIS6 or in the CDS. The previously completed Stage09 queue was scoped to seven different Batch03 stations; the downloaded 32 station-years do not establish US-NC2 coverage.

## Planned Stage11O (separate CDS retrieval)

[Stage11O code](../scripts/stage11/11o_us_nc2_2025_march_era5land_evidence.py) is prepared, **not yet executed**. Request only 2025-03-16 to 2025-03-27 inclusive (288 UTC hourly records) at original BIF location 35.8030/-76.6685, variables `2m_temperature`, `2m_dewpoint_temperature`, `surface_pressure` from `reanalysis-era5-land-timeseries`, `data_format=netcdf`. This is the same CDS point-timeseries schema previously used successfully in Batch03 Stage09b. The location is nearest-grid sampled (0.1-degree grid); the actual returned grid coordinate must be verified, with CF units K/K/Pa and exact hourly UTC coverage.

Stage11O `--check` and `--self-test` are zero-write; `--download` creates only **new** isolated evidence and SHA256 receipt. Never overwrite sealed Stage07, Stage11h, Stage11l, event decision CSV, tower/ERA release source, DATM or model case. Even after download, test UTC−5 and nearby clock sensitivity **as hypotheses only**; no offset adoption or science correction without additional evidence. Postv5/DATM/spinup statuses remain zero.

Sources:
- [ECMWF ERA5-Land hourly time-series CDS](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries)
- [ECMWF point-series user guide](https://confluence.ecmwf.int/pages/viewpage.action?pageId=627854121)
