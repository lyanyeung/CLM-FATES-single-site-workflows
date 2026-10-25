# AmeriFlux Batch05 Stage04 — complete event-level source/ERA humidity audit

**Date:** 2026-10-25. **Evidence:** operator-submitted complete Stage04 terminal output from `04_full_native_era_humidity_provenance.py`. All ten `SOURCE_PROVENANCE` records were parsed from the supplied log; `STAGE04 SUMMARY audited=10/10 failed=none`. This is a **read-only screening** result, not an approved forcing repair.

## Exact summary (one row per unique abnormal source timestamp)

| Site | Unique abnormal timestamps | RHwater <0 | ERA-T + tower-T vapour-pressure feasible | Paired not feasible | ERA internal nonphysical | VPD native == ERA at same label | Same VPD, TA difference >=0.5C |
|---|---:|---:|---:|---:|---:|---:|---:|
| US-UiD | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| US-UMB | 102 | 22 | 101 | 1 | 0 | 0 | 0 |
| US-UMd | 15 | 15 | 15 | 0 | 0 | 0 | 0 |
| US-Var | 1,294 | 55 | 648 | 646 | 0 | 92 | 66 |
| US-Vcm | 519 | 389 | 465 | 2 | 52 | 96 | 40 |
| US-Vcp | 633 | 585 | 627 | 3 | 3 | 461 | 454 |
| US-WCr | 88 | 87 | 79 | 9 | 0 | 2 | 2 |
| US-Whs | 15 | 0 | 9 | 6 | 0 | 0 | 0 |
| US-Wjs | 401 | 387 | 332 | 69 | 0 | 111 | 111 |
| US-Wkg | 62 | 19 | 60 | 2 | 0 | 0 | 0 |
| **Total** | **3,129** | **1,559** | **2,336** | **738** | **55** | **762** | **673** |

The **2,336/738/55 categories are mutually exclusive** for the 3,129 uniquely flagged source timestamps; all 3,129 have exact-label ERA companion records. The VPD-equal and TA-different flags are overlapping descriptive categories, not additional events. `RHwater<0` is a subset of abnormal timestamps, not another mutually exclusive category.

### Interpretation and handling decisions

- **2,336 "paired feasible"** means only that `e_ERA=es_water(T_ERA)-VPD_ERA` falls in `[0,es_water(T_tower)]` under the assumed units and identical printed time labels. It is NOT a validated new water vapour pressure and not a repair permit.
- **738 "paired not feasible"**: ERA implied `e_ERA` is positive and bounded at ERA temperature, but exceeds the tower-temperature saturation or otherwise violates `[0,es(T_tower)]`. Do NOT copy that vapour pressure unmodified to tower conditions.
- **55 "ERA internal nonphysical"**: `e_ERA` is negative or exceeds saturation under the same assumptions. **52 US-Vcm, 3 US-Vcp**. They are NOT repaired by taking original `TA_ERA/VPD_ERA` at that timestamp.
- **762 native VPD identical to ERA VPD** at the printed same label, and **673** of these have native/ERA temperature differing by at least 0.5C. Copying bundled ERA VPD into these records does nothing. Equality may reflect gapfilling/source relationships but by itself is NOT proof of exact provenance.
- **US-Var** has the largest combined screening burden: 1,294 unique abnormal timestamps, of which 1,163 have native RH >100 (399 between 100 and 100.5 inclusive, 362 >101; 402 in between), mostly 2021–2024. Mild supersaturation/rounding and stronger sensor discrepancies must be handled separately. The original RH column is NOT a qualified forcing source without independent source-flag inspection.
- **US-Vcm** has examples of `RH_original≈89%` while the same original TA/VPD and accompanying ERA TA/VPD produce RHwater<0. This motivates auditing whether RH is independently observed or another processing output; do not blindly use it to repair VPD.
- **US-UiD** has *zero flagged out-of-range values*, but **173,477 missing original RH records** from Stage04; no anomaly flags is not a complete quality pass.
- Stage02 metadata holds remain **US-UMB** (missing FULLSET BIF) and **US-Vcp** (conflicting coordinate/elevation groups).

### Remaining science gates

1. Original `RH` variable origin (measured vs reconstructed vs released derived), and whether it is independent of VPD/temperature; `RH` has no `RH_QC` in the Stage04 selected stream.
2. Frozen-temperature **water vs ice** saturation definition and instrument/vapour-pressure reference convention. The present 55 ERA-internal failures are failures **under the stated water formula and assumed units**, not independent proof the meteorology product is intrinsically broken.
3. Full tower/reanalysis timestamp reference and local/UTC convention: exact matching of printed labels is NOT a validated UTC alignment.
4. Elevated sites: verify site-specific atmospheric pressure, terrain elevation and ERA5 gridpoint representativeness before combining gridded vapour pressure with tower temperature.
5. External ERA5-Land or reliable independent observations must be verified at events where the release-bundled ERA companion is unusable. Avoid unconditional replacement of all low RH with reanalysis.
6. After passing scientific gates, create versioned, immutable overlays and provenance tables; no original source overwrites.

## Next audit

[Stage05 original-RH provenance and phase sensitivity scanner](../scripts/stage05/05_native_RH_provenance_phase_screen.py) is published. It scans ALL original half-hours, stratifies `RH_original` vs TA+VPD-derived RH by TA/VPD QC and subzero regime, identifies differences >10 percentage points, tallies small vs large RH>100 events, and checks the SHA256 of each source against Stage04 fingerprints. It **does not** declare original RH independently measured or produce repaired meteorology. Operator run pending; results must be appended to a separate evidence ledger, not silently inferred.
