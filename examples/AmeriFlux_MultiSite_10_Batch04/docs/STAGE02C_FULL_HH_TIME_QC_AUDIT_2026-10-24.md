# AmeriFlux Batch04 — Stage02C full native HH audit (operator-verified)

**Date:** 2026-10-24  
**Evidence:** operator-uploaded original terminal output from `scripts/stage02/02c_audit_batch04_HH_time_coverage.py`. No assistant login to IRIDIS6. The Python script only read source `FLUXMET_HH` and printed findings; the operator shell `tee` saved the log.

**Actual program summary:** `STAGE02C SUMMARY: time_pass=10 review=none failed=none`

- Full half-hour time series: **10/10 TIMESTAMP GATE PASS**.
- Every site: zero malformed CSV widths, invalid timestamps, non-30-minute intervals, temporal gaps, missing half-hour slots, or overlaps/out-of-order records.
- Total `FLUXMET_HH` rows: **3,629,232**.
- `TA_F`, `VPD_F`, `PA_F`, `P_F`, `WS_F`, `SW_IN_F`, `LW_IN_F`: reported 0 missing values in the program-selected columns; this does **not** imply all numerical values are physically valid.
- `RH` missing: **364,427 / 3,629,232 (10.04%)** across 10 sites. The script assessed the existing `RH` column, not humidity reconstructed from `TA_F + VPD_F`.
- Sum of simple science flags reported: **557 records RH < 1%**, **1 PA <= 0**, **0 negative VPD**, **0 negative RH**, **0 negative precipitation**, and **0 negative wind**.

| Site | Native HH rows | RH missing | TA_F min (°C*) | PA_F min (kPa*) | RH min/max (%) | RH <1% | PA <=0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| US-Rpf | 298,080 | 38,608 (12.95%) | -39.434 | 87.844 | 9.82 / 99.5 | 0 | 0 |
| US-Seg | 333,120 | 8,012 (2.41%) | -20.147 | 81.775 | 1.428463 / 100 | 0 | 0 |
| US-Ses | 333,120 | 6,549 (1.97%) | -20.24 | 78.132 | 1.478222 / 100 | 0 | 0 |
| US-Slt | 315,552 | 9,055 (2.87%) | -17.9 | 94.9 | 0.164 / 100 | 6 | 0 |
| US-SP1 | 368,208 | 52,522 (14.26%) | -243.686 | 1.499 | 10.57 / 100 | 0 | 0 |
| US-SRG | 315,600 | 7,523 (2.38%) | -12.84 | 85 | 0.8988 / 102.5251 | 3 | 0 |
| US-SRM | 385,728 | 3,929 (1.02%) | -10.88 | 86.947 | 2.320903286 / 98.3142 | 0 | 0 |
| US-Syv | 438,288 | 220,583 (50.33%) | -33.641 | 5.064 | 0 / 100 | 8 | 0 |
| US-Ton | 438,288 | 10,687 (2.44%) | -1.978 | -1.185 | 0.001 / 102.2 | 540 | 1 |
| US-Uaf | 403,248 | 6,959 (1.73%) | -52.622 | 70.623 | 9.9385 / 100.39 | 0 | 0 |

*Units are expected FLUXNET conventions and must be checked against original variable metadata before applying model conversions.*

## Scientific review required, despite 10/10 timestamp PASS

1. **US-SP1 critical:** `TA_F` minimum **-243.686 °C** and `PA_F` minimum **1.499** (likely kPa); not physically plausible for near-surface tower forcing. Audit timestamps, source QC, original values and ERA5/ERA5-Land alternatives **without automatic correction**.
2. **US-Ton critical:** `PA_F` minimum **-1.185** and 1 `PA <=0`; **540** observed `RH <1%` and `RH` max **102.2%**. Review paired `TA_F`, `VPD_F`, `PA_F`, native quality flags, and physical closure.
3. **US-Syv high concern:** `PA_F` min **5.064**, `RH` missing **50.33%**, 8 `RH <1%` (min 0.0). Assess site-level pressure outliers and reconstructability of humidity from independently valid TA/VPD/PA.
4. **US-Slt / US-SRG:** 6 and 3 `RH <1%`, respectively; `US-SRG` RH max **102.5251%**.
5. **US-Uaf:** RH max **100.39%**, requiring bounded-humidity source review. Other sites may have missing RH and/or isolated physically improbable values not caught by a minima-only report.

The output is a *screening*, not an accepted numerical QC decision: it did not audit per-record ERA5 vs FLUXMET consistency, annual missing-data patterns, QC class definitions, units, `RH >100%` counts, extreme temperatures beyond a single minimum, temporal offsets, or source-consistent humidity closure.

**Required next stage:** per-timestamp anomaly and source provenance report (TA/VPD/PA/RH, FLUXMET flags, ERA5 HH same-row alternatives and science-led decisions). Do not automatically replace isolated values using unrelated source combinations, and do not produce production DATM/CLM forcing until science gates pass.

**Coordinate independence:** The user-approved US-Seg `GROUP_ID 1495` latitude/longitude/elevation applies to site metadata. It does not change this HH timestamp or QC result.

**Approval boundary:** 10/10 time PASS; **scientific QC remains HOLD**. No forcing repairs, UTC shifts, ZBOT mapping, PFT/surface changes, DATM inputs or CLM-FATES spin-ups were performed.
