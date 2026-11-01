# JapanFlux Stage05C actual same-release JPF ERA5 check — 2026-11-01

## Actual operator output and scientific verdict

The operator executed [Stage05C](../scripts/stage05/05c_compare_embedded_ERA_to_release_ERA5_HH_READONLY.py) on **JP-Khw** and **JP-Tmd** at native timestamp **2005-08-12**, comparing the independently named `*_ERA` columns in two CSV products **from each site's same uploaded JPF release ZIP**:

1. `FLUXMET_HH` (embedded `*_ERA` columns; `*_F` and `*_F_QC` also visible).
2. `ERA5_HH` (the separate, published ERA5 product).

**Result:** for **each** of JP-Khw and JP-Tmd, **8/8 rows matched in all 7 tested fields**: `TA, PA, LW_IN, SW_IN, VPD, P, WS` (each field reports `EQUAL: 8`). These results show **the nonphysical values are already present in the separately packaged JPF ERA5_HH data product**, rather than being introduced by the Stage05B join, Stage05C reader, or solely by the FLUXMET_HH table. This is a **same-release corroboration**; it is **NOT an independent download of ECMWF ERA5 or ERA5-Land** and is not proof the upstream reanalysis itself is flawed.

### Exact observed values on 2005-08-12 (native source clock, timezone not established)

| Interval start | Khw TA_F = FLUXMET TA_ERA = ERA5_HH TA_ERA (°C) | Khw PA_F = FLUXMET PA_ERA = ERA5_HH PA_ERA (kPa) | Tmd TA_F = FLUXMET TA_ERA = ERA5_HH TA_ERA (°C) | Tmd PA_F = FLUXMET PA_ERA = ERA5_HH PA_ERA (kPa) |
|---|---:|---:|---:|---:|
| 02:00 | 23.988 | 97.823 | 19.425 | 99.004 |
| 02:30 | −122.144 | 48.912 | −132.399 | 49.502 |
| 03:00 | **−268.276** | **0.0** | **−284.222** | **0.0** |
| 03:30 | −122.665 | 48.922 | −132.688 | 49.506 |
| 04:00 | 22.946 | 97.844 | 18.847 | 99.013 |

For both sites, the standalone `ERA5_HH` `LW_IN_ERA` is also identical to embedded `LW_IN_ERA` and the `LW_IN_F` source at the same timestamps: Khw **39.171 W/m²** and Tmd **28.519 W/m²** at 02:00 and 02:30. Central temperature at Tmd is **below absolute zero (−273.15°C)**; neither central zero pressure nor the interpolated half-pressure steps can represent real atmospheric conditions.

**Interpretation:** This is definitive evidence of **nonphysical values in the downloaded JPF release's ERA5-derived data**. The exact interpolated half-hour values show contamination of the native series at adjacent steps. A common sentinel/placeholder / missing-value / interpolation processing issue is strongly suspected, but **the precise defect is still not located in the upstream processing chain**. Same-release file equality cannot tell us whether raw ECMWF ERA5, external gap processing, shared data pipelines or release packaging introduced the problem.

## Why broader ERA5 screening is now needed

Stage04 scanned the selected `*_F` forcing candidates; in December 2011 JP-Khw/Tmd `TA_F_QC=0` and `LW_IN_F_QC=0` tower values looked plausible even while their paired `*_ERA` columns contained extreme repeats. Therefore **a clean `*_F` screen does not imply a clean ERA5 companion source**.

Use [Stage05D read-only standalone ERA5_HH screen](../scripts/stage05/05d_scan_separate_ERA5_HH_all_years_READONLY.py) to audit the published `ERA5_HH` full original calendar independently of chosen `*_F`. It reads one nested JPF site in bounded process memory per command, checks basic physical thresholds and native time, outputs per-variable and year-wise counts with samples and watched 2005/2011/2022 dates. It does not repair, modify, extract to disk, submit Slurm, or run any model. Its first local synthetic nested-ZIP test and Python syntax check passed; **it has NOT been executed on actual IRIDIS JPF packages yet**.

**Operator requirement: no Slurm for subsequent source inspection by default.** Run one site at a time directly. A reasonable first trio is **JP-Khw, JP-Tmd, JP-Fjy**; check result before continuing to Yms/Tef and remaining four. This avoids decompressing nine original archives concurrently on a login node.

## Scientific status

- Stage05C same-release comparison: **PASS**, 2/2 selected sites; 8/8 native half-hour rows × 7 same-release ERA variables per site.
- Source QC science suitability: **BLOCKED** for corrupted ERA/selected fallback rows.
- Original independently acquired ECMWF ERA5/ERA5-Land: **NOT CHECKED**.
- Scientific repair policy: **NO APPROVED REPLACEMENT YET**. Preserve original JPF and all original `QC=0` selected tower values; confirm original BIF/BADM QC definitions, units and local/UTC clock; compare independently fetched external reanalysis where necessary.
- JP-Tom/Tgf RH>100 and negative VPD are **separate pending humidity forensics**, not solved by this JPF same-release ERA comparison.
