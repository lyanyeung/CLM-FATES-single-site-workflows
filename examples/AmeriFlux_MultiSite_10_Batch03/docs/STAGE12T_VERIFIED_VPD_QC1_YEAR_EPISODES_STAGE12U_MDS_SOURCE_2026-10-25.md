# AmeriFlux Batch03 Stage12t VERIFIED — original FLUXMET VPD QC1 physical conflicts, entire three source years

**IRIDIS6 verified:** 2026-10-25 18:13 UTC. Stage12t original pinned Git SHA and Python syntax, `--self-test`, `--check`, and `--run` all PASS. Scientific report only, not model forcing:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12t_original_VPD_QC1_full_year_physics_episodes_20261025T181302Z_7b987cae/`

Exactly 52,560 half-hour source rows across US-Me6 2015/2017 and US-NR1 2022. All 32 existing native QC1-neighbor sides of 38 VPD jump holds reproduce; the original **86 (38 VPD/48 T)** science holds and separately protected **233** physical holds are unchanged, along with all measured T, pressure, native source timestamps, previous research shadows, DATM, CIME and spinup gating.

## Full-year original-source QA — VPD_F >= saturation at matching TA_F

| Site | Year | VPD_F_QC | finite matching TA_F+VPD_F | physically invalid | invalid fraction |
| --- | ---: | --- | ---: | ---: | ---: |
| US-Me6 | 2015 | QC0 | 12612 | 0 | 0.000% |
| US-Me6 | 2015 | QC1 | 3228 | 115 | **3.563%** |
| US-Me6 | 2015 | QC2 | 1680 | 18 | **1.071%** |
| US-Me6 | 2017 | QC0 | 15872 | 0 | 0.000% |
| US-Me6 | 2017 | QC1 | 1608 | 114 | **7.090%** |
| US-Me6 | 2017 | QC2 | 40 | 0 | 0.000% |
| US-NR1 | 2022 | QC0 | 16904 | 0 | 0.000% |
| US-NR1 | 2022 | QC1 | 614 | 126 | **20.521%** |
| US-NR1 | 2022 | QC2 | 2 | 0 | 0.000% |

Total **355 / 5,450 = 6.514% of QC1** source VPD values physically invalid (all with measured `TA_F_QC=0`); 18 QC2 invalid (US-Me6 2015) and **zero QC0 invalid in 45,388 source records**. These are physical consistency tests of two separate released source fields, not proof that either sensor or all gap-filling is generally wrong. In particular, original `TA_F_QC=0` denotes measured air temperature, whereas `VPD_F_QC=1` denotes high-quality MDS gapfill.

Official provenance and source semantics:
- [FLUXNET FULLSET variables](https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/): `VPD_F` consolidates `VPD_F_MDS` and `VPD_ERA`; `VPD_F_QC=0` measured, `=1` good-quality MDS gapfill, `=2` downscaled ERA. `TA_F_QC=0` measured.
- [The FLUXNET2015 dataset and ONEFlux processing pipeline](https://pmc.ncbi.nlm.nih.gov/articles/PMC7347557/): final _F product uses measured or good MDS records, otherwise ERA-downscaled records.

## Longest original QC1-with-QC0-temperature physically impossible runs

| Station | Source-native start -> end | half-hours | duration | max excess VPD above water saturation |
| --- | --- | ---: | ---: | ---: |
| US-NR1 2022 | 202209090800 -> 202209100600 | 45 | **22.5h** | 3.996382 hPa |
| US-NR1 2022 | 202209100830 -> 202209102300 | 30 | **15h** | 5.167442 hPa |
| US-Me6 2017 | 201706290230 -> 201706291330 | 23 | 11.5h | 10.713476 hPa |
| US-Me6 2017 | 201707020230 -> 201707021030 | 17 | 8.5h | 9.439266 hPa |
| US-Me6 2017 | 201706300430 -> 201706301030 | 13 | 6.5h | 10.154140 hPa |
| US-Me6 2017 | 201707030500 -> 201707031030 | 12 | 6h | 5.260706 hPa |

The 32 signed neighbor sides occupy original QC1 physically-invalid runs (median duration 2 half-hours for Me6 2015, 12 HH for Me6 2017 changed sides, 37.5 HH for NR1 2022 sides). Original physically valid QC0 tower-T/VPD reference points within ±24h sometimes exist even when no such references exist within the narrower ±6h; **they are diagnostics, not interpolation permissions**.

## Stage12u recommended source lineage test

Compare full-year `VPD_F` and optionally available released `VPD_F_MDS`, `VPD_F_MDS_QC`, `TA_F_MDS`, `TA_F_MDS_QC`, and native `TA_ERA/VPD_ERA` source in matched records, with equal-time alignment and source SHAs. Stage12u should explicitly report absent MDS columns (never invent their values), test how much of the QC1 original physical invalidity persists under the companion TA_ERA (alternative temperature, not tower truth), count possible gapfill-source discontinuities, and report both source QC0 reference availability and the 32 fixed Stage12s native sides. This is a scientific hypothesis test, not an approval for alternative T or VPD.

**DO NOT** replace good original measured tower T, relax 4hPa adjacent-source jump cutoff, impute over multi-hour events, or deploy incomplete source forcing; original 86/233 holds, native clock, all Post-v5/DATM/spinup status unchanged.
