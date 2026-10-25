# Stage12v VERIFIED — 355 of 355 original high-quality MDS VPD gapfills violate water-vapour physics even at original MDS air temperature

**Operator IRIDIS6 result (2026-10-25 18:48 UTC):** pinned Stage12v code SHA/syntax, `--self-test`, `--check`, `--run` all PASS. Source-only SHA-sealed report directory:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12v_MDS_VPD_temperature_and_QC_source_forensics_20261025T184859Z_bb353075/`

The exact **355** original `VPD_F_QC=1` and `TA_F_QC=0` impossible VPD source timestamps are unchanged from verified Stage12t/u; the exact 32 VPD-held neighbor *sides* retain their original scientific HOLD.

| Site | Year | Inconsistent MDS VPD against measured TA | MDS air T available | MDS VPD physically valid at MDS air T | Median MDS T minus measured original tower T, °C | Max MDS T minus measured original tower T, °C | Median MDS VPD above saturation at MDS T, hPa |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| US-Me6 | 2015 | 115 | 115 | **0** | 0 | 0 | 1.020290 |
| US-Me6 | 2017 | 114 | 114 | **0** | 0 | 0 | 1.824867 |
| US-NR1 | 2022 | 126 | 126 | **0** | 0 | 0 | 1.254972 |
| **TOTAL** | | **355** | **355** | **0** | 0 (site-year medians) | 0 (site-year maxima) | |

Original `VPD_F_MDS_QC=1` for 355/355 and `TA_F_MDS_QC=0` for 355/355. The MDS T minus original tower T median and maximum are zero in each site-year. The output does not give minima, and must not be exaggerated into *every* T being exactly identical unless per-row evidence is read. Crucially, **changing from `TA_F` to `TA_F_MDS` restores physical consistency in 0 of 355 cases**, confirming the defect lies in the joint VPD/temperature MDS source combination. No sensor-failure cause has been established.

**Important official quality code interpretation:** This report's script appropriately refrained from inventing QC semantics, but the documented semantics ARE available: per [FLUXNET FULLSET definition](https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/) and the [ONEFlux scientific paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7347557/), half-hourly `VPD_F_MDS_QC` and `TA_F_MDS_QC` 0 = measured, 1 = high-confidence MDS gapfill, 2 = medium-confidence, 3 = low-confidence. Consequently the 355 source VPD values **were designated high-confidence MDS gapfills**, whereas temperature was measured, and the published source still contains impossible implied nonpositive vapour pressure. Quality code does not guarantee cross-field thermodynamic consistency.

Original 32/32 signed held VPD neighbor sides remain physically invalid at MDS T.

**Scientific limitation:** The source values originate in published FLUXMET MDS rather than a directly measured VPD field; `VPD_F_MDS` may have been independently gapfilled with a meteorological-condition analogue that does not physically constrain VPD relative to temperature. This is a hypothesis, not proven cause without ONEFlux method tracing or source provider information.

## Next: strictly read-only ERA-humidity candidate viability audit

For the signed 355 source-invalid QC1 rows, examine same-original-native-record `TA_ERA/VPD_ERA` water relative humidity (0–100%), how ERA RH transfers to unchanged measured site `TA_F`/`PSRF`, ice-phase supersaturation when below 0 °C, original >5 °C tower-versus-companion temperature mismatch and >4 hPa discontinuity against actually usable original QC0 VPD neighboring observations and Stage12g shadow (where finite). Keep original 86 held events and previous 233 held physics rows protected, and never treat 'valid ERA RH' as an approval for replacement. This is a *research classification*, not a repair, nor a model-ready forcing edit.

Original source, T/P, VPD, native time, earlier research shadows and Post-v5/DATM/spinup authorization remain unchanged. Stage12v wrote ONLY its isolated report.
