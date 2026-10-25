# Batch05 Stage03 original humidity / ERA5 companion audit — operator run 2026-10-25

## Provenance and completion

The operator supplied the full console output of the published `03_review_humidity_qc_and_era5_clock.py` script. It reports:

```text
STAGE03 SELF-TEST PASS | humidity QC, source clock, missing sentinels; NO ORIGINAL WRITES
STAGE03 SUMMARY: audited=10/10 failed=none
NO WRITES; NO ERA APPROVAL; NO REPAIRS; NO DATM; NO SLURM
```

All ten original native files and all ten corresponding release-bundled `ERA5_HH` companion CSVs were read successfully. All companions have `TA_ERA`, `VPD_ERA` and `PA_ERA`, but **no RH_ERA** was present in the inspected columns. The ERA companion files have source time labels beginning in 1981 and ending in 2021 (US-UMB) or 2025 (other nine); these spans are structural, not validated independent meteorological agreement.

## Exact Stage03 screen counts

| Site | Derived RH (water) <0 | Derived RH <1% | Native RH <1% | Native RH >100% | Native RH <0 | Suspicious QC pattern |
|---|---:|---:|---:|---:|---:|---|
| US-UiD | 0 | 0 | 0 | 0 | 0 | RH missing extensively at Stage02; Stage03 flags none |
| US-UMB | 22 | 23 | 0 | 79 | 0 | negative derived RH: TA_QC=0, VPD_QC=1 |
| US-UMd | 15 | 15 | 0 | 0 | 0 | negative derived RH: 0/1, entirely in 2015 |
| US-Var | 55 | 62 | 69 | 1,163 | 0 | negative derived: 0/1; RH>100: 0/0, 2021–2024 |
| US-Vcm | 389 | 509 | 102 | 0 | 0 | negative derived: mixed 0/0, 0/1, 0/2, 1/2, 2/2 |
| US-Vcp | 585 | 629 | 4 | 0 | 0 | negative derived: 0/1, 0/2, 1/2, 2/2; 404 in 2008 |
| US-WCr | 87 | 88 | 26 | 0 | 2 | negative derived: 0/0, 0/1, 1/2 |
| US-Whs | 0 | 1 | 0 | 14 | 0 | small native RH >100 at examples, TA/VPD 0/0 |
| US-Wjs | 387 | 401 | 0 | 0 | 0 | negative derived: 0/1 and 0/2 |
| US-Wkg | 19 | 22 | 0 | 40 | 0 | negative derived: 0/1 |
| **Total** | **1,559** | **1,750** | **201** | **1,296** | **2** | categories overlap; DO NOT add counts |

The RH calculations are `100 * (1-VPD_F/es_water(TA_F))` using assumed hPa and degC; no ice-phase, altitudinal vapour-pressure or release-unit validation was carried out. No source original RH_QC was available in the selected Stage03 columns.

## Crucial release-companion provenance observations

Stage03 prints **only up to twelve first encountered flagged native examples per site** and then the corresponding companion ERA5 values at unchanged timestamps. These examples establish the following but **not full-period prevalence**:

- **US-Vcm:** at 2007-01-17 04:00, original TA_F=−14.254 degC and VPD_F=2.387 hPa; ERA TA_ERA=−14.254 and VPD_ERA=2.387, so copying both from release-bundled ERA would reproduce the original combination. Derived water RH≈−17.17%. In the first twelve Stage03 event samples, VPD matches ERA in 12/12. ERA-derived vapour partial pressure at that event is negative under the stated formula and is **not** a valid repair.
- **US-Vcp:** 2008-04-09 11:00 native TA_F=−3.424 degC and VPD_F=6.643 hPa; ERA TA_ERA=7.022 degC and VPD_ERA=6.643 hPa. Copying the companion VPD alone would not fix native TA–VPD physics. First twelve samples have identical native/ERA VPD values, with differing TA.
- **US-Wjs:** 2007-08-09 13:30 native TA_F=18.079 degC, VPD_F=25.275 hPa; ERA TA_ERA=27.708 degC, VPD_ERA=25.275 hPa. First twelve samples again have identical VPD but different TA.
- **US-Var:** original RH=0.0 at numerous examples from 2004 even where derived RH from TA/VPD is 30–70%; 1,163 native RH>100 events cluster in 2021–2024. This native RH column must not be used uncritically to reconstruct moisture.
- **US-UMB:** no BIF metadata from Stage02; FULLSET source is distinct and must retain its original package/coordinate provenance.

### Clock gate

Stage03 explored coarse integer-hour shifts (−12..+12) by sparse QC0 temperature-anchor mean absolute difference. Example best-scoring offsets vary by site (US-UiD +2h; US-UMB −1h; US-Vcm −1h; US-Vcp +2h; US-Wjs +3h; US-Wkg 0h). **These are not validated timestamps or offsets**: small samples and local-vs-gridded temperature differences can bias the metric. Do not shift release-labelled time or assume original ERA5 files are independent of already gap-filled FLUXNET variables. Confirm timestamp reference convention before model forcing/repair.

## Stage04 gate (published; operator run pending)

Use [Stage04 read-only full-event exact-label ERA provenance](../scripts/stage04/04_full_native_era_humidity_provenance.py) to count, **for all flagged source timestamps**, exact-label ERA event coverage, original/ERA VPD duplication, discrepancies between tower and ERA T, ERA-internal humidity feasibility, and *hypothetical* tower-T+ERA-vapour-pressure compatibility.

The Stage04 paired calculation is `e_ERA=es_water(T_ERA)-VPD_ERA`, then `VPD_shadow=es_water(T_tower)-e_ERA`. It remains scientifically provisional: ERA grid humidity may need topographic/pressure correction, original ERA companion is not independent, exact timestamp matching is not yet approved, and water/ice saturation treatment remains unresolved. **No modified forcing is written and no automatic replacement is allowed**. Records where ERA's own derived vapour pressure is negative must be held, not copied.

Before any automatic source repair, verify release units and source QC semantics, timestamp convention, elevation/pressure consistency, independent ERA5-Land availability, and manual review of exceptions. Stage02 metadata reviews US-UMB and US-Vcp remain open.
