# Stage12af decision — NR1 measured tower temperature interpolation; US-Kon event-scoped plan; MtB conditional ice RH gate

**2026-10-26 operator decision**: The 2022-09-10 US-NR1 11°C readings are anomalous TA_F; replace ALL three by interpolation from surrounding lower tower TA_F. For US-Kon, operator requested optimal scientific repair recommendation. For US-MtB, accept four ice-relative supersaturation values **only if the installed CTSM/FATES forcing pathway demonstrably accepts them**, otherwise retain existing holds. No blanket temperature replacements at other sites yet.

## US-NR1 exact 3 user-authorized TA_F corrections, native time unchanged

| Original native time | Original source `TA_F` °C | Approved corrected `TA_USE` °C | method |
| --- | ---: | ---: | --- |
| 2022-09-10 06:30 | 11.297 | 1.241000 | linear between 06:00=0.762 and 07:00=1.720 |
| 2022-09-10 07:30 | 11.196 | 1.5566666667 | 1/3 step between 07:00=1.720 and 08:30=1.230 |
| 2022-09-10 08:00 | 11.787 | 1.3933333333 | 2/3 step between 07:00 and 08:30 |

Modify both `TA_USE` (°C) and `TBOT` (=273.15+TA_USE K) together, in **new derivative only**. Preserve original published `TA_F`, original QC and original Stage12g. The existing finite `VPD_USE` at these three corrected TA times is 8.427, 8.383 and 9.319 hPa (source gapfilled `VPD_F_QC=1`) and becomes **physically impossible** at corrected 1–1.6°C, so both these VPD and QBOT must become held missing in the user-approved **temperature-only** new derivative pending companion humidity reconciliation. Other three 06:00,07:00,08:30 VPD remain originally missing. No mistaken auto-promotion of temperature approval to humidity replacement approval.

**Recommended six-record humidity-source reconciliation (06:00 through 08:30 inclusive):** paired original-native source `TA_ERA/VPD_ERA` RH ~71.946/71.977/72.009/72.024/72.024/72.248 percent; candidate VPD at corrected tower T approx 1.812/1.873/1.937/1.913/1.891/1.854 hPa. This is continuous with existing Stage12g at 05:30=1.791 hPa and 09:00=1.869 hPa; separate ERA5-Land RH ~90–99% would make candidate VPD much lower and is not automatically selected. Exact unrounded candidate and QBOT are calculated **for review only**; user hasn't explicitly approved RH-source selection for these six.

**Stage12af isolated GitHub application script**:
`examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage12/12af_NR1_20220910_three_approved_T_interpolation_AND_ERA_RH_review.py`, commit `6606df9b80451e889bc9bba204e5af6a9452a70d`, blob `bb12b009a686bbd0465cafebcd8f55e660d710fe`. `--self-test` no reads/writes; `--check` original source/Stage12g SHA/QC physics + three exact corrections, no writes; `--apply` writes only separately corrected NR1 full NOLEAP derivative **INCOMPLETE** with exactly three TBOT+TA_USE fixes and three newly held VPD/QBOT, plus six-row paired ERA-RH candidate **REPORT ONLY** and SHA manifest. No on-HPC run yet verified.

## US-Kon scientific recommendation — do NOT use generic interpolation

Original logged US-Kon `2011-03-24 12:30/13:00/13:30`: tower 19.519 / 5.465 / 17.821°C, grid 6.289 / 6.999 / 7.533°C, source paired ERA 3.784 / 3.973 / 4.465°C. Likely **high outside neighbors** at 12:30/13:30 could be suspect, not the intermediate 13:00. In contrast 2011-10-18 04:30/05:00/05:30/06:00/06:30 original tower 5.041/4.919/11.560/3.969/3.693°C; 05:30 is an isolated high tower-temperature spike and might merit isolated TA interpolation after source `TA_F_QC` and source ERA confidence are checked. Among the 34 VPD-jump centers, 27 have >5°C adjacent original TA_F jumps; all 34 source VPD_F at center imply physically invalid negative RH when combined with TA_F. Blind center-only ERA VPD patch fails >4hPa against retained neighbor in **34/34**. Original source VPD QC1 (MDS) in 33 and QC2 (ERA) in one. Need grouping at source-native episode level, jointly fixing demonstrably implausible **temperature spikes at whichever native index is actually wrong** (not always the held center), then replace invalid original QC1/2 humidity *over contiguous events and contaminated neighbors* with a consistent signed paired original ERA-RH to maintain VPD/QBOT physical closure. Preserve original QC0 measured tower values unless individually approved for demonstrably anomalous source; do NOT globally replace original tower temperatures with gridded T. Check native offsets independently. A specific US-Kon 2008-09-26 05:30 original `VPD_F_QC=0` and raw VPD 18.334 hPa while neighbor QC0 VPD 2.744/2.858 at almost constant tower 16°C. Suggest separately approving local QC0-neighbor median/interpolation 2.801 hPa and QA (original source and replacement retained).

Recommended priorities:
1. Original `TA_F_QC` for all 34 held centers and ±2 native HH; identify extreme temperature sequence, classify isolated jump vs contiguous apparently shifted timestamp and compare original paired ERA TA.
2. Identify QC0 **anchors**. For isolated single or two contiguous bad T with legitimate anchors on both sides, interpolate only flagged T; otherwise hold rather than extrapolate.
3. Calculate same-native companion ERA-RH at corrected temperature and site pressure, update VPD+QBOT across all source-inconsistent QC1/QC2 within connected episode. Keep unchanged QC0 humidity unless individually approved.
4. Reject new VPD jumps >4hPa outside explicitly user-authorized local events; compare full event neighborhood, not just a single held center. All repair outputs in new isolated SHA-sealed derivatives.
5. Preserve 2008 anomalous QC0 as separate specific manual decision.

## US-MtB conditional retained water-RH

On 2024-02-11 05:00–06:30, grid ERA5-Land water RH 92.510%,94.484%,95.152%,94.479% and original tower T approximately -8.39,-8.30,-8.50,-8.64°C. Water-RH-derived candidate VPD 0.244,0.181,0.156,0.176 hPa. Ice-relative RH may exceed 100% on T below freezing. The planned forcing is a **specific humidity QBOT** dataset, not a direct RH forcing. CTSM supports specific humidity forcing and can compute ice saturation separately; but official generic documentation does not establish that user's exact checked out Fortran source/compiled FATES/CTSM case accepts ice-supersaturated atmospheric QBOT at these exact records without an abort, clipping or internal logic change. Operator approval explicitly conditions release on this verification; keep four science holds pending exact installed source check/standalone forcing acceptance. No arbitrary RHice=100 clipping.

No Post-v5/DATM/spinup approval; remain Stage12 science selection.

## IRIDIS6 execution verified — 2026-10-26 01:33:49 UTC

The operator ran pinned Stage12af original Git blob `bb12b009a686bbd0465cafebcd8f55e660d710fe`. SHA/AST, `--self-test`, `--check` and `--apply` all **PASS**. Operator-approved **temperature only**, new immutable derivative:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage12af_NR1_20220910_user_approved_three_T_only_20261026T013349Z_34ff1cda`

The original three anomalous `TA_F` source points are explicitly `TA_F_QC=1`; all three interpolation temperature anchors `202209100600`, `202209100700`, `202209100830` passed source `TA_F_QC=0` within script verification. Signed new derivative `TA_USE`: 1.241000, 1.556666667, 1.393333333°C; corresponding `TBOT`: 274.391000, 274.706667, 274.543333 K. Their previous Stage12g QC1 VPD 8.427, 8.383 and 9.319 hPa became physically impossible at approved temperature and were **HOLD as missing VPD/QBOT** in new derivative. Three other old humidity holds in six-row interval remain unchanged. Exact six original-native companion ERA-RH proposal (RH pct): 71.945909,71.976540,72.009137,72.024243,72.023933,72.248312; **proposed not approved/applied** VPD hPa: 1.811838,1.873343,1.936537,1.912989,1.890739,1.853710; corresponding proposed QBOT kg/kg: .004091,.004236,.004385,.004335,.004282,.004243. All Post-v5/DATM/spinup approvals still zero. Original Stage12g and raw tower files remain immutable.

**Decision gate:** user to authorize or decline the six-record native companion ERA-RH repair, only after this actual temperature-only fix; do not silently convert previous scientific recommendation into operator approval.

## Stage12ag Kon follow-on source-QC audit (created after verified Stage12af)

[Stage12ag exact Kon 35 native QC source-neighbor review](../scripts/stage12/12ag_Kon_35_native_center_and_neighbors_temperature_QC_READONLY.py) is committed to GitHub at `3fed5356d9237726031fe83d8cc410499271f9b6` (Git blob `9b19c5fdca36c4b4b0bb5544e2e26e6917fb28a7`). The script SHA-validates signed successful Stage12ae report `stage12ae_all_42_pending_original_tower_ERA_ERA5Land_neighbors_20261026T011243Z_c5cc64fe` and prints every original `TA_F_QC` from ±2 original native half-hours around the **34 US-Kon VPD QC1/QC2 jump-held events** and the **single original 2008 QC0 VPD anomaly**. It lists paired original ERA and gridded ERA5-Land temperatures and the source original and current forcing VPD. Outputs are **read-only science reports** and cannot authorize or modify tower temperature or any humidity model forcing. **As of this note it has not been run on IRIDIS6.**
