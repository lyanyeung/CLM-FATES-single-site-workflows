# JapanFlux Stage05X — actual JP-Yms 5/5 original QC2 anomalies independently supported (2026-11-02)

## Actual operator-executed Stage05X

```text
STAGE05X SELF-TEST PASS | Yms original source F=ERA QC2, independent 24x2 hourly source context; NO WRITES
STAGE05X JP-YMS ORIGINAL QC2 VS INDEPENDENT ERA5L CONTEXT PASS | NO CDS / SLURM / REPAIR
SITE JP-Yms UTC_DATE 2005-08-11 SOURCE_FIELDS 5 UNIQUE_SOURCE_HALF_HOURS 4
BY_VARIABLE {'LW_IN': 2, 'PA': 3}
OUTSIDE_3H_CONTEXT 5
SOURCE_TO_REFERENCE_EVIDENCE /home/ly3n24/japanflux_stage05x/run_20261102T112146Z/stage05x_JP_Yms_20050811_original_F_vs_independent_ERA5L_3h_CONTEXT_HOLD.tsv
SUMMARY /home/ly3n24/japanflux_stage05x/run_20261102T112146Z/stage05x_original_source_and_independent_ERA5L_review.json
ALL_45_ORIGINAL_QC2_FIELDS_REMAIN_HOLD_NO_APPROVED_REPLACEMENTS
```

This is an **actual independently downloaded** ERA5-Land reference (not the embedded, downscaled original JPF `*_ERA`), tied to original local standard time (JST UTC+9) and original selected JPF source `F`, raw QC2, equality `F=ERA`. At JP-Yms, five original anomalous variables occur in **four** half-hours. The Stage05W2 independent CDS response had **two** original CSVs of 24 hourly observations each, request ZIP SHA256 `4bf228a3a53ab7fc6751b8e7438fb459570536ce6f54af2f81de5afc083b59d5`; gridded location **34.80000000000106°N,135.79999999999654°E**. Original source BIF site location **34.790278°N,135.840939°E, elevation 220m**.

| Original JPF native JST 2005-08-12 | Variable | JPF selected F, QC2 | Independent ERA5-Land nearby 3h range | Qualitative conclusion |
|---|---|---|---|---|
| 02:00 | LW_IN | 44.790 W m-2 | 405.383889–418.053889 W m-2 *hourly mean* | Very large context inconsistency |
| 02:30 | LW_IN | 44.790 W m-2 | 405.383889–418.053889 W m-2 *hourly mean* | Very large context inconsistency |
| 02:30 | PA | 67.794 kPa | 98.88828–98.93342 kPa | Severe station-pressure inconsistency |
| 03:00 | PA | 37.349 kPa | 98.88828–98.94534 kPa | Severe station-pressure inconsistency |
| 03:30 | PA | 67.801 kPa | 98.88828–98.94534 kPa | Severe station-pressure inconsistency |

Every row was flagged `OUTSIDE=1` and `STRONG_CONTEXTUAL_INCONSISTENCY_PENDING_PHYSICS_REVIEW`, **NOT** replacement approved. Original `PA` values around 37–68 kPa at a 220m tower elevation are markedly different from normal ~99 kPa gridded nearby conditions. `LW_IN` around 45 Wm-2 is strongly inconsistent with neighboring independent ~405–418 Wm-2. This difference is a **contextual anomaly diagnostic**, not proof of a specific factor-of-ten coding error or a validated half-hour replacement.

### Overall original JPF candidate count

| Group | Independently evidenced source-selected fields | Other UTC-verified source fields requiring separate independent comparison | Original time basis unresolved |
|---|---:|---:|---:|
| JP-Khw (2005-08-12 02:00–03:30 JST) | 8 | 3 | 0 |
| JP-Yms (2005-08-12 02:00–03:30 JST) | 5 | 5 | 0 |
| JP-Fjy | 0 | 6 | 0 |
| JP-Tef + JP-Tmd | 0 | 0 | 18 |
| **Total** | **13** | **14** | **18** |

Total original source candidates: **45** variable fields /35 distinct site×native half-hours. Only **2/9** independent CDS site×UTC-day responses downloaded (JP-Khw and JP-Yms, both 2005-08-11 UTC); **7** are not yet requested. JP-Tef/Tmd original README says *local solar time* vs BIF +9 and other sites' *local standard time*; never automatically map to UTC. All **45** remain source science HOLD. No original ZIP modifications, forcing replacement, AD400, Slurm or CDS calls during Stage05X.

## Stage05Y — consolidate 13-field evidence and 7 remaining independent site/day requests

[Stage05Y](../scripts/stage05/05y_merge_Khw8_Yms5_independent_evidence_remaining7_NO_REPAIR.py) (code committed, **not yet executed on real IRIDIS files**) reads actual Stage05V 8-field evidence TSV/summary, actual Stage05X 5-field comparator TSV/summary, source-time-gated Stage05O 27 UTC fields +18 native-only HOLDs and Stage05V eight remaining days, plus the actual source-verified Stage05W2 audit. It creates a **unified 13-field science HOLD evidence register** and **7 remaining CDS site×UTC-day requests** after excluding the newly downloaded JP-Yms 2005-08-11 UTC response. It verifies exact 8+5 field counts, original source QC2 and equal internal ERA, nonduplicated original variable keys and original source units. It never retrieves CDS, modifies ZIPs/forcing or approves half-hour correction. **Do not claim its execution succeeded until operator outputs its PASS.**

Next recommended independent single-day retrieval (only by explicit operator action) is **JP-Fjy 2005-08-11 UTC, surface_pressure**, for a third original BIF-verified site. The existing [Stage05S](../scripts/stage05/05s_ERA5Land_timeseries_one_day_CDS_pilot_opt_in.py) CDS submission workflow can issue *one site/day request at a time* with private CDS credentials and original source-scoped time. The delivered ERA5-Land hourly product must undergo SHA-pinned grid/time/units/original source alignment validation before being interpreted as source error evidence.

Source docs for independent product: [ECMWF CDS ERA5-Land hourly time-series](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries) and [ERA5-Land user guide](https://confluence.ecmwf.int/pages/viewpage.action?pageId=699689224).
