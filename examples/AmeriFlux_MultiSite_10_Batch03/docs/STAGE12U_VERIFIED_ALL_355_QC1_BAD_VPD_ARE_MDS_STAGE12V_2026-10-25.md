# Batch03 Stage12u VERIFIED — exactly 355 original QC1 VPD physical violations are MDS provenance

IRIDIS6 operator run on 2026-10-25 18:35 UTC: Stage12u pinned SHA/syntax, `--self-test`, `--check`, and `--run` **PASSED**. Immutable source-only science report:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12u_original_MDS_QC1_VPD_cross_temperature_source_20261025T183511Z_57431d0b/`

This checks the exact source-native half-hour timestamps and original signed Stage12t/12s evidence (US-Me6 2015 and 2017, US-NR1 2022). The 355 original `VPD_F_QC=1`, measured `TA_F_QC=0`, `VPD_F>=es_water(TA_F)` values **all have finite `VPD_F_MDS` and all equal the original consolidated `VPD_F`**. Original FLUXMET inputs actually include `VPD_F_MDS`, `VPD_F_MDS_QC`, `TA_F_MDS`, and `TA_F_MDS_QC` for all three source years. The separate raw `VPD` source column is absent. Do not invent an unavailable raw sensor VPD observation.

## Whole-year source/physics sensitivity

| Source site-year | QC1 impossible at original measured tower TA | Match original VPD_F_MDS | Original VPD physically allowed at *paired* TA_ERA | Native VPD_ERA physically allowed at measured tower TA | Native VPD_ERA physically allowed at paired TA_ERA |
| --- | ---: | ---: | ---: | ---: | ---: |
| US-Me6 2015 | 115 | 115 | 42 | 115 | 115 |
| US-Me6 2017 | 114 | 114 | 15 | 114 | 114 |
| US-NR1 2022 | 126 | 126 | 75 | 126 | 126 |
| **TOTAL** | **355** | **355** | **132** | **355** | **355** |

The original MDS VPD is **not** rescued by changing to the same-time companion ERA temperature in 223/355 cases; 132 would pass only the elementary nonnegative vapour-pressure screening under an alternative T. Conversely native `VPD_ERA` is physically consistent at original `TA_F` in **355/355**, but that is a reference and *not* evidence that the ERA substitute is ecologically or observationally correct at the tower. Time offset alignment is still an unapproved hypothesis.

Among the signed **32 neighbor sides of 38 still-held VPD-jump events**, raw QC1 VPD is physically valid at paired ERA temperature in **5/32** side comparisons (Me6 2015 4, Me6 2017 1, NR1 2022 0), while same-time native companion `VPD_ERA` passes basic physical screening at original tower T on all 32 sides. Neighbor *sides* are not necessarily unique independent source records.

## Next source-level test (Stage12v)

The retained `VPD_F_MDS_QC`, `TA_F_MDS` and `TA_F_MDS_QC` values now allow a decisive, non-destructive follow-up: check whether the MDS VPD is consistent **with MDS temperature**, quantify MDS/observed temperature offsets and physically invalid rates under both, examine actual MDS QC values without assuming their quality-score semantics, and retain the exact original signed native 32 held neighboring sides. All values must be read from the sealed Stage12u report and/or verified original FLUXMET source. This is a science-only audit, never automatic forcing release.

**Safety status:** Original 86 Stage12g scientific hold source records (38 VPD, 48 T), separately protected original 233 physics holds, measured tower T/P, source native clock, all Stage12c/d/e/g shadow forcing, and Post-v5/DATM/spinup prohibitions remain unchanged. Stage12u wrote zero source/forcing/model files, only the above report.
