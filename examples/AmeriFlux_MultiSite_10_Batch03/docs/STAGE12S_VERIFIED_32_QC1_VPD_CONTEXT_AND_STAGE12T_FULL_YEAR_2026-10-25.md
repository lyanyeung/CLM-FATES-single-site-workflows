# Batch03 Stage12s VERIFIED — 32 source QC1 VPD sides, measured TA QC0, ±6h source-native context

**IRIDIS6 operator log on 2026-10-25 18:05 UTC:** The initial Python attempt under conda `(base)` stopped at `ModuleNotFoundError: No module named 'numpy'`. After `conda activate clm_fates_env`, the pinned Stage12s Git blob and syntax, `--self-test`, `--check`, and `--run` **all passed**. The first failure was environmental, not source data or a repaired result. Signed source-only report:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12s_32_QC1_native_VPD_pm6h_source_context_20261025T180547Z_6a9cc5ab/`

Exactly **32 QC1 source-neighbor sides × 25 half-hour native source rows = 800 context records**. The 25-point windows overlap; 800 is not 800 independent native observations. All 32 *source* air temperature `TA_F_QC` codes are **QC0** while the paired VPD source is **QC1** and `VPD_F >= es_water(TA_F)`. This means a non-positive implied water vapour pressure under the original paired tower source, not grounds to alter tower TA. Measured-QC0 source temperature does not establish the scientific truth of either humidity source.

| Original source region/class | QC1 side count | QC0 original TA at focal sides | Median excess raw VPD above original water es, hPa | Median tower-minus-paired ERA T, C | Median invalid half-hours / 25 in ±6h window | QC0 physically valid VPD anchor before | After |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| US-Me6 raw vs Stage12d finite difference | 22 | 22 | 2.039440 | +1.3470 | 6 | 4 | 7 |
| US-Me6 raw finite vs Stage12e missing | 8 | 8 | 0.918402 | +3.5640 | 6 | 1 | 3 |
| US-NR1 raw vs Stage12d finite difference | 2 | 2 | 2.238138 | −1.9615 | **22** | 0 | 0 |

The QC0 anchor counts describe **focal side-windows with at least one** valid source QC0 VPD in the preceding/following six hours, not distinct QC0 source measurements. Site/year source epochs overlap, and these counts must not be used as an interpolation release.

## Original eight US-Me6 source VPD QC1 with no Stage12e reference

| Original native timestamp | Tower TA QC0, C | RAW VPD QC1, hPa | RAW VPD minus es(T), hPa | Tower minus paired ERA TA, C | Invalid half-hours within ±6h | Stage12d HOLD |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2015-08-30 06:30 | 8.45 | 12.219 | +1.164058 | −1.503 | 7 | NEW_EDGE_JUMP_GT4HPA_HOLD |
| 2015-08-30 07:00 | 8.32 | 10.974 | +0.016090 | −2.022 | 7 | NEW_EDGE_JUMP_GT4HPA_HOLD |
| 2015-09-17 17:00 | 8.51 | 14.812 | +3.712018 | −5.157 | 3 | COMPANION_ERA_T_MISMATCH_GT5C |
| 2017-07-02 07:00 | 16.83 | 25.149 | +5.993367 | +7.437 | 17 | COMPANION_ERA_T_MISMATCH_GT5C |
| 2017-07-04 07:00 | 15.01 | 17.597 | +0.545530 | +4.215 | 6 | NEW_EDGE_JUMP_GT4HPA_HOLD |
| 2017-07-04 07:30 | 17.33 | 20.445 | +0.672746 | +2.913 | 6 | NEW_EDGE_JUMP_GT4HPA_HOLD |
| 2017-07-05 06:30 | 17.69 | 21.782 | +1.555044 | +5.683 | 5 | COMPANION_ERA_T_MISMATCH_GT5C |
| 2017-07-05 07:00 | 19.79 | 23.107 | +0.039916 | +6.676 | 5 | COMPANION_ERA_T_MISMATCH_GT5C |

Four Stage12d temperature mismatches and four 4 hPa transition holds remain. In Stage12g, two of the former have **research-only** finite references, not validation of the original 38 VPD jump events. Original scientific 86 (38 VPD/48 T), protected earlier 233 holds, source temperature and pressure, native clocks and Post-v5/DATM/spinup restrictions remain unchanged.

## Next — Stage12t read-only three original source-year census

[Stage12t exact source 2015/2017 US-Me6 + 2022 US-NR1 full-year native QC/episodes](../scripts/stage12/12t_NR1_Me6_original_VPD_QC1_full_year_episodes_READONLY.py) checks **52,560 native half-hours** across three site-years (17,520 each), stratifies physical impossibility by original VPD QC and tower T QC, maps source QC1+T QC0 invalid runs and the same 32 signed focal sides, and looks for genuinely original source QC0-T and QC0-VPD physically valid anchors within ±24h. Sources, signed reports, and original site inputs are SHA-verified. Only a new isolated report is written by `--run`; `--check` is read-only. This is not a data repair and **is not yet verified on IRIDIS6**.
