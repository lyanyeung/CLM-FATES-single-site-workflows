# AmeriFlux Batch04 — Stage03 priority anomaly and FLUXNET ERA-derived reference diagnosis

**Date:** 2026-10-24. **Execution evidence:** operator-supplied IRIDIS6 output from `scripts/stage03/03_audit_batch04_extreme_met_and_ERA5.py --sites US-SP1 US-Syv US-Ton`. No changes to native source, ERA5 files, surfaces, forcing or jobs.

**Actual terminal marker:** `STAGE03 SUMMARY: flagged=US-SP1,US-Syv,US-Ton none_of_selected_flags=none failed=none`.

| Site | Native source rows | Stage03 category counts | Dates |
| --- | ---: | --- | --- |
| US-SP1 | 368208 | TA_F < -80 °C: 3; PA_F < 50 kPa: 2 (overlap at one timestamp) | 2004-12-04; 2016-10-09 |
| US-Syv | 438288 | PA_F < 50 kPa: 3; RH < 1%: 8; 1% <= RH < 5%: 52 | 2004-12-03/04; 2021; 2025 |
| US-Ton | 438288 | PA_F < 50 kPa: 3 (including PA_F <=0: 1); RH <1%: 540; 1% <=RH<5%: 1; RH>100%: 1811 | 2003; 2004-12-03; 2021–2025 |

## Key high-priority original source examples

- US-SP1 `201610092000`: `TA_F=-243.686`, `PA_F=1.499`; both `TA_F_QC=2` and `PA_F_QC=2`. Same-label `TA_ERA=-243.686, PA_ERA=1.499`. At `201610091930` and `201610092030` native temperatures `-109.923`, `-111.323` and `TA_ERA` exactly equal.
- US-SP1 `200412040100`: `PA_F=1.499, PA_F_QC=2`, `PA_ERA=1.499`, while native `TA_F=10.54` and `TA_ERA=-243.686`.
- US-Syv `200412040000`: `PA_F=PA_ERA=5.064, PA_F_QC=2`, `TA_F=-1.91` but `TA_ERA=-271.171`; neighbouring half-hours have `PA_F` 49.026 and 49.149 with `PA_F_QC=2`, and `TA_ERA` approximately -136 °C.
- US-Ton `200412032200`: `PA_F=PA_ERA=-1.185, PA_F_QC=2`; `TA_F=5.986` but `TA_ERA=-257.363`. Neighbouring `PA_F` 49.032 and 49.034 with `PA_F_QC=2`, `TA_ERA` ~-127 °C.
- US-Syv low RH in 2021 and one 2025 record: the selected `TA_F_QC`, `VPD_F_QC`, `PA_F_QC` often equal 0. Reconstructed relative humidity from tower `TA_F + VPD_F` also very low. Subzero liquid-water versus ice saturation reference and source RH must be scientifically reviewed, not blindly replaced.
- US-Ton 540 `RH<1%` in 2003, with numerous values `RH=0.001` and `PA_F_QC=2` in presented examples; 1811 `RH>100%` events from 2021–25. At 2025-11-16 10:00, `RH=102.2`, `VPD_F=0` and `RH(TA,VPD)=100%`.

## Crucial ERA interpretation (avoid incorrect replacement)

Official FLUXNET2015 variable documentation identifies `TA_ERA`/`PA_ERA` as **downscaled and calibrated ERA-derived product variables**, and `TA_F`/`PA_F` as consolidated native + derived variables, with `*_F_QC=2` denoting ERA-downscaled values. They are **not guaranteed to be independent raw ERA5 reference observations**. The v1.3 r1 AmeriFlux FLUXNET product is processed with updated ONEFlux; verify its exact version-specific data dictionary before applying the convention to every field.

References:
- [FLUXNET FULLSET variable codes](https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/)
- [Improved AmeriFlux FLUXNET v1.3 release notes](https://ameriflux.lbl.gov/resource/details-for-improved-ameriflux-fluxnet/)
- [ONEFlux dataset technical paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7347557/)

The exact equality of some `PA_F` with `PA_ERA` at `PA_F_QC=2` is expected for a consolidated ERA fallback and does **not** provide independent corroboration. The severe `TA_ERA` and `PA_ERA` abnormalities in multiple stations also make this product unsuitable as a trusted unvalidated repair source at those timestamps.

## Science gates and next steps

1. **READ ONLY:** forensic comparison of `TA`, `TA_F_MDS`, `TA_F`, `TA_ERA`, `PA`, `PA_F`, `PA_ERA` with original QC categories and neighbouring time rows. Inspect ERA-derived anomalies and shared 2004-12-03/04 artefacts across sites. No unit, time-zone or independent-source claims from the same-label comparison alone.
2. **READ ONLY:** run Stage03 on seven remaining sites; do not assume no extreme flags because previous Stage02C only screened limited categories.
3. For any candidate repair, first obtain genuinely independent ERA5 or ERA5-Land source (not `TA_ERA`/`PA_ERA` copied from the same FLUXNET release), verify time/grid/units/provenance, and document per-timestamp changes in a ledger. Do not combine inconsistent source variables for humidity.
4. Treat RH and saturation boundaries carefully in cold conditions; derive and vet water-vapor variables with consistent temperature, VPD and pressure, explicitly accounting for vapor pressure over liquid water vs ice before declaring humidity mathematically invalid.

**Status:** Stage02 post-approval metadata **10/10 PASS**; Stage02C HH chronology **10/10 PASS**; Stage03 priority site scientific QC **HOLD**, with 3/3 sites flagged. **0 repair or model jobs approved.**
