# Batch05 Stage06 — complete RH severe-disagreement episodes, source-column inventory, and official QC meaning

**Operator result:** `STAGE06 SELF-TEST PASS`; `STAGE06 SUMMARY audited=10/10 failed=none`. All ten original source SHA256 fingerprints matched Stage05. **READ ONLY**; original forcing and model jobs not changed.

## Full ten-site results

`RH_difference_gt10pp` is defined only when original RH is 0–100%, `TA_F`/`VPD_F` are finite and `abs(RH - 100*(1-VPD_F/es_water(TA_F))) > 10` percentage points.

| Site | Source rows | Severe-difference HH | Distinct contiguous events | Longest HH | Longest duration | First timestamp of longest |
|---|---:|---:|---:|---:|---|---|
| US-UiD | 298,080 | 3,644 | 565 | 34 | 17 h | 2024-12-05 00:30 |
| US-UMB | 262,992 | 17 | 2 | 16 | 8 h | 2015-02-15 01:00 |
| US-UMd | 333,120 | 23 | 10 | 13 | 6.5 h | 2015-02-15 01:00 |
| US-Var | 455,856 | 282 | 37 | 67 | 33.5 h | 2004-07-02 04:30 |
| US-Vcm | 333,120 | 16,065 | 1,860 | 297 | 148.5 h | 2023-03-04 05:00 |
| US-Vcp | 333,120 | 10,509 | 1,923 | 99 | 49.5 h | 2019-06-01 12:30 |
| US-WCr | 473,376 | 12,425 | 1,614 | 161 | 80.5 h | 1999-05-05 08:30 |
| US-Whs | 333,120 | 0 | 0 | 0 | 0 h | — |
| US-Wjs | 333,120 | 4,302 | 771 | 94 | 47 h | 2012-12-14 12:30 |
| US-Wkg | 385,728 | 0 | 0 | 0 | 0 h | — |
| **Total** | **3,541,632** | **47,267** | **6,782** | — | — | — |

No unsuffixed `TA` or `VPD` source columns were found in **any** of the ten selected FLUXMET/FULLSET HH files. This is a fact about **these selected files only**, not proof that independent tower observations are absent from other packages or the AmeriFlux base archive.

The 47,267 differences by `TA_F_QC/VPD_F_QC`: `1/1=38,278`; `2/2=8,981`; `1/2=8`; `0/0=0`. Distinct episodes are contiguous **30-minute** spans of this specific >10pp difference; they are **not** synonymous with all physically noncompliant `TA_F/VPD_F` values.

### Notable overlapping site periods

US-UMB and US-UMd both have severe differences starting at the printed local-standard time **2015-02-15 01:00**. This is a useful cross-site source-event comparison candidate; identical printed timestamps alone do not prove same meteorological event without checking site timezone, provenance and site data.

## Important new confirmation from official published FLUXNET conventions

The official **FLUXNET FULLSET Data Product** defines consolidated half-hourly `TA_F_QC` and `VPD_F_QC` codes:

- `0` = measured;
- `1` = good-quality MDS gapfill;
- `2` = downscaled from ERA.

It also states `TA_F` consolidates `TA_F_MDS` and `TA_ERA`, whereas `VPD_F` consolidates `VPD_F_MDS` and `VPD_ERA`, selecting the MDS variable where the MDS quality is 0 or 1, otherwise the ERA downscale. Official docs use `TA_F` deg C, `VPD_F` hPa, `RH` percent. Therefore `QC2` source duplication with the original `ERA5_HH` companion is **expected** and not a coincidental identical value.

Documentation:

- https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/ (fields TA_F, TA_F_QC, VPD_F, VPD_F_QC, RH, and units).
- https://fluxnet.org/data/fluxnet2015-dataset/variables-quick-start-guide/ (quality flag convention).
- https://fluxnet.org/data/fluxnet2015-dataset/ (FLUXNET timestamps: **local standard time, no DST**, with UTC offset specified in site metadata).

**Qualification:** Batch05 includes 2025-era `AMF_*_FLUXNET` releases and one distinct US-UMB 3-5 FULLSET. The published FLUXNET2015 definitions are the appropriate interpretation for familiar variable names, but site-specific version differences and original metadata must be checked. In particular, documentation does **not** certify whether the unsuffixed `RH` column is an independent sensor measurement, and it is not accompanied by RH_QC in the Stage05/06 selected source report.

### Scientific consequence

Previously proposed unconditional `VPD_F -> VPD_ERA` replacement must **not** be done. Many QC2 values already ARE `VPD_ERA`; their physically problematic combinations with TA_F can reflect mismatch between independent gapfill pathways (e.g. measured tower `TA_F_QC=0` and ERA `VPD_F_QC=2`). Whole-pair replacement with ERA also fails the Stage04 internal-humidity screen for 55 events (52 US-Vcm, 3 US-Vcp) under its stated water-formula assumption.

## Next Stage07

[Stage07 read-only official QC lineage and ERA inheritance test](../scripts/stage07/07_verify_fluxnet_qc_lineage_and_era_inheritance.py) verifies `QC2` source equality against actual release-companion ERA files at every flagged native time label; checks optional MDS columns **only if they are truly present**; quantifies `QC1` MDS and `QC2` ERA relationships rather than treating RH as a repair source; refuses changed native file SHA. It keeps **all forcing untouched**. Operator execution pending.
