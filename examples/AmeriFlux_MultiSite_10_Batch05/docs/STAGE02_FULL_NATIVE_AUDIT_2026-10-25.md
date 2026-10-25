# Batch05 Stage02 operator results — 2026-10-25

**Evidence:** operator's complete console transcript of `02_audit_batch05_metadata_time_met.py` (10/10 sites). No source datasets were modified. This ledger records reported output, **not** a separate model-side reanalysis.

## Overall result

```text
STAGE02 SUMMARY: examined=10/10 time_pass=10 time_review=none metadata_review=US-UMB,US-Vcp science_review=US-UiD,US-UMB,US-UMd,US-Var,US-Vcm,US-Vcp,US-WCr,US-Whs,US-Wjs,US-Wkg failed=none
```

All original native FLUXMET/FULLSET HH records were internally continuous; each reported `LABEL_BOUNDARY_SCREEN FULL_LABEL_YEARS`. This **does not** verify UTC/local alignment, ERA5 time basis, meteorological units, missingness science, or model-ready forcing.

## Site-by-site original data screen

| Site | Original rows | Native range (label years) | IGBP | Derived water RH <1% | Derived water RH <0% | Native RH <1% | Native RH >100% | Native RH missing |
|---|---:|---|---|---:|---:|---:|---:|---:|
| US-UiD | 298,080 | 2008–2024 | GRA | 0 | 0 | 0 | 0 | 173,477 |
| US-UMB | 262,992 | 2007–2021 | BIF unavailable | 23 | 22 | 0 | 79 | 30,295 |
| US-UMd | 333,120 | 2007–2025 | DBF | 15 | 15 | 0 | 0 | 28,558 |
| US-Var | 455,856 | 2000–2025 | GRA | 62 | 55 | 69 | 1,163 | 29,353 |
| US-Vcm | 333,120 | 2007–2025 | ENF | 509 | 389 | 102 | 0 | 25,500 |
| US-Vcp | 333,120 | 2007–2025 | ENF | 629 | 585 | 4 | 0 | 25,893 |
| US-WCr | 473,376 | 1999–2025 | DBF | 88 | 87 | 26 | 0 | 116,241 |
| US-Whs | 333,120 | 2007–2025 | OSH | 1 | 0 | 0 | 14 | 36,562 |
| US-Wjs | 333,120 | 2007–2025 | SAV | 401 | 387 | 0 | 0 | 28,339 |
| US-Wkg | 385,728 | 2004–2025 | GRA | 22 | 19 | 0 | 40 | 8,956 |
| **Total** | | | | **1,750** | **1,559** | | | |

Counts overlap across categories; do not add them to infer unique events. Relative humidity was screen-derived as `100*(1 - VPD/es_water(TA))`, assuming TA degC and VPD hPa; release units and subfreezing water/ice saturation need verification before any correction. Native RH has no dedicated QC column in the Stage02 selected stream; corresponding TA/VPD original QC must be retained in provenance.

### Original metadata exceptions

- **US-UMB:** original FULLSET package, **no BIF found**. Metadata cannot be promoted to a site configuration without independently documented provenance. Do not borrow US-UMd metadata just because the site codes are similar.
- **US-Vcp:** original BIF contains two distinct location groups: latitude 35.8624 / longitude -106.5974 / elevation 2542 m (CDIAC-dump comment), and latitude 35.8642 / longitude -106.5967 / elevation 2500 m (start-date field 200701010000). Both retained; no automatic coordinate choice.
- **US-Vcm:** location elevation values 3003 and 3030 m recorded in BIF; unique latitude/longitude but elevation still needs provenance review.
- **US-Vcm, US-Vcp, US-Wjs:** no BIF height records; do not infer ZBOT from canopy/vegetation height.

### Scientific gates before CLM-FATES forcing

1. Verify FULLSET versus FLUXMET variable units and original source QC semantics.
2. Check ERA5 companion headers, coverage, time basis and offset candidates (no auto clock selection).
3. Investigate all physically impossible TA/VPD-derived humidity and native RH out-of-range events; report source QC, episode timing, and ERA5 availability.
4. Allow ERA5 or ERA5-Land replacement **only after** data source, unit, time and moisture consistency are validated; preserve original TA QC0 when a single-variable repair is physically possible, and avoid silent clock/calendar shifts.
5. Resolve site metadata, elevation, PFT and ZBOT independently; no DATM forcing, CIME case or Slurm job should be launched from Stage02 alone.

Stage03 provides a **read-only** initial provenance/ERA5 clock scout:
[`scripts/stage03/03_review_humidity_qc_and_era5_clock.py`](../scripts/stage03/03_review_humidity_qc_and_era5_clock.py). Its offset search is diagnostic only, not an alignment decision or repair.
