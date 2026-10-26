# Stage12ag VERIFIED: US-Kon 35-center original TA_F_QC source audit

**User IRIDIS6 execution 2026-10-26 02:34 UTC**: source SHA / syntax PASS; --self-test PASS; --check PASS; --run PASS. New report-only folder:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12ag_Kon_35_original_T_QC_native_pm2h_repair_decision_20261026T023414Z_2f65dcb1`.

No original or Stage12g forcing edits; the 34 Kon humidity center holds and the single 2008 original source VPD QC0 HOLD remain intact.

## Key QC finding

All 34 US-Kon original center source `TA_F_QC=0` (measured T). Many of the preceding/following excessive-temperature readings are **`TA_F_QC=1` MDS/gapfilled**, not measured tower temperatures; therefore do **NOT** interpolate temperature at the central 34 VPD HOLD records. The original source VPD_F for those centers, meanwhile, is QC1 for 33 and QC2 for 2011-09-29 18:30, and all 34 are physically inconsistent when combined with original source TA_F. The 2008-09-26 05:30 outlier is original `VPD_F_QC=0` (protected, physical inconsistency despite source QC), with 2.744,18.334,2.858 hPa on prior, current, next original native HH at ~16°C.

For the **35 centers × five native HH** Stage12ag source snippets, all original native timestamps were de-duplicated, yielding exactly **149 distinct native HH, 116 original TA_F_QC0 and 33 original TA_F_QC1**. These are local source-context counts only, **NOT the entire site's TA QC count**.

## Exactly 23 high-confidence QC1 isolated tower-temperature repair candidates (not yet user-approved)

Each line below has an original `TA_F_QC=1` and both its **immediate** original-native ±30 min TA temperatures have `TA_F_QC=0`. QC1 T deviates by ≥5°C from the straight interpolation between both observed anchors. The interpolation is recommended for operator approval; **these values are derived from Stage12ag original source print rounded to 0.001°C and are PREVIEW only**. For actual application, recompute from the **full-precision original SHA-pinned Stage07 raw source**, not the printed rounded values. Neither this note nor Stage12ag has applied any repairs.

| Original native YYYYMMDDHHMM | Original source TA_F °C | Interpolated between two QC0 neighbor TA_F °C |
| --- | ---: | ---: |
| 201102211130 | 7.549 | -2.366 |
| 201102220830 | 7.860 | -3.167 |
| 201102220930 | 8.623 | -0.562 |
| 201103150930 | 13.308 | 3.5265 |
| 201103151030 | 16.295 | 5.086 |
| 201103241230 | 19.519 | 5.2015 |
| 201103241330 | 17.821 | 5.7545 |
| 201103241430 | 17.781 | 6.0495 |
| 201103271030 | 10.114 | 1.3635 |
| 201103271130 | 10.700 | 1.538 |
| 201103271230 | 10.539 | 0.8725 |
| 201103300930 | 10.208 | 3.0705 |
| 201103311530 | 16.101 | 9.5715 |
| 201104011030 | 19.510 | 13.6185 |
| 201104071430 | 20.443 | 12.346 |
| 201104071530 | 19.418 | 11.6835 |
| 201110170730 | 14.858 | 6.814 |
| 201110180530 | 11.560 | 4.444 |
| 201110182130 | 11.479 | 4.197 |
| 201110190130 | 11.364 | 1.694 |
| 201110190630 | 11.222 | -0.2455 |
| 201110191130 | 17.192 | 8.3595 |
| 201203050830 | 10.865 | 1.3595 |

## 10 other original QC1 temperature records from 149-row local source context: more evidence required

`201105261000`, `201105261030`, `201109291730`, `201109291830`, `201109291930`, `201110150630`, `201202251100`, `201202251130`, `201208050930`, `201208051000`. Here the context may lack immediate two QC0 neighbor anchors, and/or the source QC1 temperature is less than 5°C from interpolated neighbors. **Do NOT automatically interpolate these.** Widen the native context and examine QC0 temperature anchors/possible runs before a site operator decision. The `201109291830` original VPD source QC2 and source T QC1 need separate companion-ERA temperature/RH treatment.

## Science repair after user approval of the 23, still not authorized

Rebuild `TA_USE` and `TBOT` at only the approved originally QC1 temperature spikes (and no original source or QC0 T changes); then recompute original-native ERA-RH at corrected tower T and preserved pressure, `VPD_USE` and `QBOT` for the 34 QC1/QC2 VPD-held centers **and impacted neighboring gapfilled humidity values**. Never retain old VPD when physically incompatible with new TA. Avoid isolated center-only replacement when it introduces >4 hPa 30-min jumps; edit only explicitly approved QC1/2 times within validated connected source episodes, protect measured original QC0 VPD unless separately approved. US-Kon 2008-09-26 05:30 VPD QC0 deserves a **separate manual override decision**, with two neighboring original QC0 VPD 2.744 and 2.858 hPa implying candidate linear interpolation 2.801 hPa.

No Post-v5, DATM, model run or spinup approval. The 23 interpolation candidates are *not* yet operator-approved or applied.
