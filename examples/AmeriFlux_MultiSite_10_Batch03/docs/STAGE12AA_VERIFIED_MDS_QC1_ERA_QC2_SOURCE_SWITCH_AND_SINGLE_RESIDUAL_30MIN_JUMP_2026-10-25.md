# Stage12aa VERIFIED — US-Me6 2017-07-04 MDS QC1 to ERA QC2 original source switch and one residual hypothetical ERA-RH jump

**Operator IRIDIS6 2026-10-25 23:05–23:06 UTC**: pinned script SHA and syntax, `--self-test`, `--check`, and `--run` ALL PASS. Signed source-only output folder:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12aa_20170704_original_QC1_QC2_native_ERA_RH_20261025T230548Z_3a2b96b6/`

No changes to original published FLUXMET, immutable original signed Stage12g shadow, native tower T/P/clock, Post-v5, DATM, spinup. Original 86 and separately protected 233 scientific HOLD records remain unchanged.

## Exact original seven native half-hour source records

| Native time (2017-07-04) | Tower TA_F °C | Original FLUXNET VPD_F hPa | Original source QC | Implied original RH % | Existing Stage12g VPD hPa | Same-native companion ERA-RH at unchanged tower TA_F VPD, hPa | Paired TA_ERA minus tower TA_F °C |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 06:00 | 9.85 | 13.952 | 1 (MDS) | -14.84 | 3.205763 | 3.205763 | -0.736 |
| 06:30 | 11.95 | 15.816 | 1 (MDS) | -13.22 | 3.974495 | 3.974495 | -1.995 |
| 07:00 | 15.01 | 17.597 | 1 (MDS) | -3.20 | **MISSING / HOLD** | 5.154795 | -4.215 |
| 07:30 | 17.33 | 20.445 | 1 (MDS) | -3.40 | **MISSING / HOLD** | 9.345609 | -2.913 |
| 08:00 | 18.96 | 21.391 | 1 (MDS) | **2.35** | 21.391000 (original Stage12c baseline retained) | 12.292544 | -0.921 |
| 08:30 | 20.01 | 13.204 | 2 (ERA) | 43.53 | 13.204000 | 13.827916 | -0.743 |
| 09:00 | 21.27 | 14.805 | 2 (ERA) | 41.42 | 14.805000 | 15.529364 | -0.776 |

All 7 original tower temperatures are QC0 measured; paired ERA temperature mismatch stays within 5°C at each selected point. The 06:00–08:00 source VPD QC1 is MDS high-quality gapfill, NOT a measured QC0 humidity series; 08:30/09:00 original source QC2 is ERA-sourced. Original 07:00 and 07:30 VPD science held as missing in signed Stage12g.

## Exactly SIX actual adjacent original 30min source-time edges

| Consecutive original native time | Original published source VPD absolute Δ, hPa | Unchanged Stage12g absolute Δ, hPa | Entirely hypothetical same-native paired ERA-RH VPD absolute Δ, hPa |
| --- | ---: | ---: | ---: |
| 06:00→06:30 | 1.864 | 0.768732 | 0.768732 |
| 06:30→07:00 | 1.781 | missing | 1.180300 |
| **07:00→07:30** | 2.848 (source values thermodynamically impossible) | missing | **4.190815 (over 4)** |
| 07:30→08:00 | 0.946 (07:30 physically impossible) | missing | 2.946934 |
| **08:00→08:30** | **8.187 (QC1 MDS→QC2 ERA provenance change)** | **8.187** | **1.535372** |
| 08:30→09:00 | 1.601 | 1.601 | 1.701448 |

Original-source QC1→QC2 08:00→08:30 jump 8.187 hPa collapses to 1.535372 hPa when the whole 06:00–09:00 sequence is *hypothetically* sourced from companion ERA-RH at unchanged measured tower TA_F. This suggests that mixed independently gapfilled humidity source types can create a discontinuity but **does NOT prove** causation or that the alternative reflects actual tower humidity. The companion ERA product is processed, not an independent direct instrument reading.

One residual original-native ERA-RH-only **07:00→07:30 = 4.190815 hPa**, exceeding the adopted 4 hPa numerical diagnostic by **0.190815 hPa**. Five of the six paired ERA-RH transitions pass; **not all six**. The 4hPa threshold is a protective research-selection guard, **not a physical law**, and should not be quietly relaxed or used to automatically reject a real meteorological change. Tower temperature 15.01→17.33°C increases 2.32°C; paired original-native ERA-RH drops 69.769→52.734% (17.035 percentage points). A symmetric exact mathematical decomposition of the VPD increase (VPD=es_water(T)*[1-RH/100]) gives approximately **1.054 hPa (25.2%) due to temperature change**, and **3.137 hPa (74.8%) due to companion humidity drop**. This is an attribution of *the mathematical candidate calculation*, not a proof of observed causal meteorology.

**Source context:** No genuinely measured original source VPD_F_QC0 with measured T QC0 in ±24 h of 2017-07-04 07:30. Nearest original 2017 QC0 valid VPD at July 05 13:00 (29.5 h away), insufficient for direct local truth. Original 08:00 source VPD QC1 is inherited from Stage12c and implies RH 2.35%, which is suspicious; retain its original numerical value for provenance/manual review, **do not rewrite it**.

**Science status:** 07:00 and 07:30 original HOLD, 08:00 inherited VPD manually reviewed, original 86 plus 233 holds unchanged. No Post-v5/DATM/spinup. Stage12ab next should examine whether the residual 07:00→07:30 4.190815 hPa source companion ERA-RH change is dominated by warming versus RH decrease; check alternative original measured tower humidity evidence / precise native timing separately without changing clock. Preserve both candidate values and all original underlying files. No automatic interpolation/smoothing to force continuity.

## Stage12ab next-stage source-only script (GitHub committed, not yet executed on IRIDIS6)

[Stage12ab exact six original-native 30min ERA-RH VPD temperature-versus-humidity decomposition](../scripts/stage12/12ab_Me6_20170704_original_ERA_RH_jump_decomposition_READONLY.py), pinned revision `432259defea816e61567c17cfcd32d6f8e576e2d`, Git blob `424646717e247a7b3266e8246af38d1ca0c405d1`. This signed-source math report preserves the verified Stage12aa SHA and original source QC and checks all 7 source-native observations / 6 contiguous 30min edges; only `--run` creates a new isolated source-only report. The original 07:00→07:30 signal mathematically decomposes into 1.054264 hPa (temperature) and 3.136551 hPa (companion ERA RH), summing to 4.190815 hPa, still 0.190815 hPa beyond the scientific guard. The script **has not yet passed IRIDIS6 self-test, check or run**; do not claim it is verified or use the result to release a science hold.
