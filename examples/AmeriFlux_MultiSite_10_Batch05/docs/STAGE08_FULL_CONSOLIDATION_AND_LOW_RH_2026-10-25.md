# Batch05 Stage08: full-row original FLUXNET consolidation and MDS alternative audit

**Operator log, 2026-10-25:** `SOURCE VERIFIED`, `STAGE08 SELF-TEST PASS`, `STAGE08 SUMMARY audited=10/10 failed=none`. Exactly **3,541,632** native half-hours across the 10 Batch05 releases, SHA256 matches each verified original. Source CSVs not overwritten; no DATM/CIME/SLURM.

## Complete all-row consolidation source audit

The checks used *all* source records, not only previously flagged abnormal rows:

| Full-source rule | Tested | Exact match | Deviations |
|---|---:|---:|---:|
| `TA_F_QC=0/1`: `TA_F` vs `TA_F_MDS` | 3,119,032 | 3,119,032 | **0** |
| `TA_F_QC=2`: `TA_F` vs `TA_ERA` | 422,600 | 422,600 | **0** |
| `VPD_F_QC=0/1`: `VPD_F` vs `VPD_F_MDS` | 3,097,311 | 3,097,311 | **0** |
| `VPD_F_QC=2`: `VPD_F` vs `VPD_ERA` | 444,321 | 444,321 | **0** |

The consolidated and MDS quality codes are not interchangeable: `*_F_QC=2` indicates ERA downscaling, while `*_F_MDS_QC=2/3` means medium/poor-quality MDS gapfill. Official variable documentation:
https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/

All F QC2 values fall where the intermediate corresponding MDS QC is **2/3** or **missing**:

- `TA_F_QC2`: 187,740 cases have candidate `TA_F_MDS_QC=2/3`; 234,860 have missing MDS QC/value, total 422,600.
- `VPD_F_QC2`: 209,461 cases have candidate `VPD_F_MDS_QC=2/3`; 234,860 have missing MDS QC/value, total 444,321.
- There are **zero** source-selection contradictions (`F_QC2` with `MDS_QC0/1`), and **zero** source-value disagreements under Stage08's numeric tolerance.

These establish fidelity to the release product's consolidation algorithm, not scientific validity of the resulting mixed-origin humidity.

## Previously flagged event categories (the groups overlap)

- **50,287 unique flagged HH** under original-RH, derived-water-RH and disagreement screens.
- **47,267** `RH_original` vs `RH_water(TA_F,VPD_F)` differ >10 percentage points.
- **1,750** `RH_water(TA_F,VPD_F)<1%`; Stage02–07 show **1,559** of these are strictly negative (physically impossible under the assumed water formula); the other **191** are 0–1% and must **not** be categorically labelled impossible without site/meteorological checks.
- **1,298** original `RH` outside [0,100]% (1,296 >100%, 2 just slightly negative), potentially overlapping other categories.

### MDS-pair mathematical feasibility at 1,750 low-derived-RH records

| Site | Low `RH_water<1%` | Both `TA_F_MDS,VPD_F_MDS` mathematical feasible | MDS-pair mathematically nonphysical | `VPD_F_QC=2` among low events |
|---|---:|---:|---:|---:|
| US-UiD | 0 | 0 | 0 | 0 |
| US-UMB | 23 | 1 | 22 | 0 |
| US-UMd | 15 | 0 | 15 | 0 |
| US-Var | 62 | 7 | 55 | 0 |
| US-Vcm | 509 | 190 | 319 | 96 |
| US-Vcp | 629 | 409 | 220 | 457 |
| US-WCr | 88 | 2 | 86 | 2 |
| US-Whs | 1 | 1 | 0 | 0 |
| US-Wjs | 401 | 87 | 314 | 111 |
| US-Wkg | 22 | 3 | 19 | 0 |
| **TOTAL** | **1,750** | **700** | **1,050** | **666** |

**Important:** 700 mathematically feasible MDS *pairs* are only counterfactual diagnostics. Many are already the same consolidated F values, which failed the low-RH screen because RH is extreme-but-positive; others depend on medium/poor MDS values. The **666** low events inheriting `VPD_ERA` have associated MDS VPD QC2/3; none is automatically qualified for replacement.

Low-derived-RH event source classification (all sites combined):
`TA_F_QC/VPD_F_QC: 0/0=119; 0/1=961; 0/2=479; 1/1=4; 1/2=128; 2/2=59` (total 1,750). In particular **119 are 0/0** and require independent tower measurement/context review, not blind ERA replacement.

## Scientific holds remain

1. `RH` original-column measurement provenance or derivation not verified; the selected files have no `RH_QC`.
2. The released `VPD_F` combines measured/MDS/ERA input **independently** from `TA_F`, which can produce physically conflicting combinations. Copying `VPD_ERA` when VPD QC2 does nothing.
3. Site elevation, atmospheric pressure, cold-weather saturation convention, site-local standard time and independently acquired ERA5-Land need validation before constructing humidity repair candidates.
4. US-UMB original BIF is missing; US-Vcp BIF contains conflicting coordinate/elevation metadata. Do not silently choose station metadata for ERA5-Land acquisition, forcing or ZBOT.
5. None of the scripts produce revised forcing, run a model or mark data model-ready.

## Next Stage09 (published; operator run pending)

[Stage09 read-only, individual low-RH-event triage](../scripts/stage09/09_low_RH_source_resolution_readonly.py) splits the 1,750 cases into **negative RH** and **0–1% RH**, stratifies original RH, MDS/ERA physical compatibility and QC provenance, and identifies the longest low-RH episodes. The ERA implied vapour pressure with the original tower temperature remains a purely *hypothetical* screening candidate, never an adopted value. Stage09 is published but still requires its operator self-test and full IRIDIS6 run.
