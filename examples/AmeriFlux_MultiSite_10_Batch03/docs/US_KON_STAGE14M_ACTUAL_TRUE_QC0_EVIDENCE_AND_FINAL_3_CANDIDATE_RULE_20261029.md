# US-Kon — Stage14M ACTUAL 2026-10-29 06:28 UTC QC0 provenance and bounded final-science decision

## Actual result on IRIDIS6

The third, SHA-verified, corrected Stage14M read-only code (commit `0906444ffdbd6749043f943a33e8e0ac60837e47`, blob `9909fddf2a80ed0290b726bfadc120b988ed57fa`) was ACTUALLY executed and completed. Original manifest and selected source both **2004–2019**, native **280,320 NOLEAP 30-minute intervals**. K/L input SHA receipts and original FLUXMET/paired ERA SHA verified. Actual report:

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/US_Kon_14M_original_QC0_9HOLD_44edges_20261029T062839Z_4d82e789
```

- Originally flagged FSDS differences were **pure CSV floating-point reload rounding**: max `1.1368683772161603e-13` W m-2 across 2,248 rows, **0 differences >1e-10**. Similarly WIND max `1.7763568394002505e-15` (3,153 rows), PRECTmms max `9.9963440303163509e-17` (442 rows), TA_USE max `1.7763568394002505e-15` (3,856 rows). TBOT, PSRF, FLDS exactly equal. All NaN/+Inf/-Inf masks identical and no material original nonhumidity scientific edits.
- Actual **184,026** paired original true measured `TA_F_QC==0 AND VPD_F_QC==0` tower-water-RH records in the full site; this is site-wide coverage, not 9 specific hold measurements.
- Of **82** unique native times affected by nine missing events / 44 flagged connected-source interfaces, **22** are genuinely bracketed by original both-QC0 source within ±6 hours.
- Stage14L prior: exact **7** additional finite original QC1/QC2 research-only revisions, selected K **68** exploratory missing fills unchanged, **9** protected HOLDs unchanged. Original 68-seed contact warnings **46→41** over the same 96 interfaces; among 103 expanded interfaces **44 still warn**. **11** of these have VPD changes >10 hPa.

## Nine true original scientific holds, grouped by independent source support

| Native source key | Original tower T/VPD QC | Distance to previous and next BOTH-QC0, hours | Selected T minus companion ERA °C | Decision |
|---|---|---|---:|---|
| 201102220830 | 1/1 | 0.5 / 1.5 | +4.517 | **Keep**; adjacent three-point Feb22 T inconsistency |
| 201102220900 | 0/1 | 1.0 / 1.0 | +5.405 | **Keep**; source T QC0 but >5°C mismatch and neighbour T contradictions; VPD remains QC1 |
| 201102220930 | 1/1 | 1.5 / 0.5 | +4.954 | **Keep**; three-point Feb22 joint T/VPD source ambiguity |
| 201105261100 | 0/1 | 699.0 / 16.5 | -0.026 | **Keep**; QC0 true RH anchors too distant |
| 201109291830 | 1/2 | 286.5 / 474.5 | -6.374 | **Keep**; ERA-based VPD QC2 and source T anomaly |
| 201110150730 | 0/1 | 659.5 / 101.5 | +3.685 | **Keep**; true RH observations too remote |
| 201110230730 | 0/1 | 2.0 / 1.0 | +3.564 | **Primary bounded candidate**; two nearby real RH QC0 anchors and T QC0 |
| 201202251030 | 0/1 | 0.5 / 1.5 | -0.667 | **Primary bounded candidate**; two nearby real RH QC0 anchors and T QC0 |
| 201208050900 | 0/1 | 0.5 / 2.5 | +4.791 | **More cautious bounded candidate**; two real RH QC0 anchors but T differs ~4.8°C from ERA |

**IMPORTANT:** source `TA_F_QC=0` with `VPD_F_QC=1` is **not a measured RH QC0 observation at that same timestamp**. The two endpoints are actual independent source **both-QC0 tower RH**; their interpolation estimates source RH but are still an inferred research candidate. Time proximity does not mean the interpolated VPD is independent measurement.

## Eleven very large remaining VPD jumps and QC type

Actual raw signed flag list includes: 201109281630–1700 (12.082 hPa, QC2/2); 201110031530–1600 (10.233, QC2/2); 201110041830–1900 (10.340, QC2/2); 201110061730–1800 (11.685, QC2/2); 201208040900–0930 (23.530, QC1/1); 201208041000–1030 (12.085, QC1/0, protect real QC0); 201506101330–1400 (14.430, QC2/2); 201506101400–1430 (15.704, QC2/2); 201509061730–1800 (16.780, QC2/2); 201509061930–2000 (11.004, QC2/2); 201510121730–1800 (10.013, QC2/2).

All these are adjacent-source/sensitivity scientific warnings, **not** proof the QC2 adjacent ERA is wrong or that a 23hPa change can be fixed by bulk clipping. As of Stage14M no new actual measured tower humidity source has appeared, so don't add arbitrary neighbourhood ERA-RH source replacements.

## Proposed single final bounded scientific sensitivity gate (not yet run)

Use the existing signed Stage14M report and Stage14K primary source as parent. For ONLY three exact source T-QC0/VPD-QC1 missing slots `201110230730`, `201202251030`, `201208050900`, evaluate: (i) the 14M actual previous and next paired observed QC0-RH anchors, (ii) linear source-native time weighted interpolation of measured **water RH** between those endpoints, (iii) original selected tower T and site PSRF to recover VPD, QBOT, (iv) original candidate versus source companion ERA-RH contrast, (v) full **both** 30min selected source joins, requiring ≤4 hPa VPD, ≤20 pp RHwater, ≤0.003 kg/kg QBOT, (vi) physical water/ice bounds, exact prior SHA checks and source QCs. If a candidate fails ANY check, preserve it as HOLD; no auto-repair of neighbours. Do not release the other six holds, including the full Feb22 three-time event. Write only an independent research sensitivity if numerical checks pass and label it NOT Post-v5/DATM/AD400/Slurm approved.

**Decision pending actual test:** Keep original Stage14K as preferred incomplete numerical research dataset; Stage14L as isolated seven-neighbour alternative; Stage14M purely QC0 provenance. The script's actual numerical candidate values and two-edge RH/VPD/QBOT checks must be observed before final approval.
