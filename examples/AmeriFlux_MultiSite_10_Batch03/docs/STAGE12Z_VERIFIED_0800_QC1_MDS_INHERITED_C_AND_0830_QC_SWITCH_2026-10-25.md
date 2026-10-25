# Stage12z VERIFIED: US-Me6 2017-07-04 08:00 original QC1 MDS right boundary is inherited from Stage12c, followed by original QC1→QC2 discontinuity

**Operator IRIDIS6 log, 2026-10-25 22:52 UTC:** Stage12z pinned Git blob/source syntax, `--self-test`, `--check` and `--run` PASS. Source-only signed report directory:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12z_0800_MDS_source_original_RH_context_20261025T225231Z_2b60b8d8/`

The Stage12z script checked Stage07 source SHA manifest and Stage12y and Stage12c/d/e/g research shadow SHAs and source-native 17520 HH 2017 year. No original data, prior shadow, forcing or model writes.

## Critical original source / Stage12c-d-e-g chronology

| Native time, 2017-07-04 | Measured TA_F °C (QC0) | Original VPD_F hPa | Original VPD_F_QC | Original VPD_F_MDS hPa | Original implied RH % | Paired ERA RH % | ERA RH transferred VPD at QC0 tower T hPa | Signed Stage12g VPD hPa |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 06:00 | 9.85 | 13.952 | **1** | not printed at 06:00 | -14.84 | 73.61 | not printed | 3.205763 |
| 06:30 | 11.95 | 15.816 | 1 | 15.816 | -13.22 | 71.55 | 3.974495 | 3.974495 |
| 07:00 | 15.01 | 17.597 | 1 | 17.597 | -3.20 | 69.77 | 5.154795 | **MISSING / HOLD** |
| 07:30 | 17.33 | 20.445 | 1 | 20.445 | -3.40 | 52.73 | 9.345609 | **MISSING / HOLD** |
| **08:00** | **18.96** | **21.391** | **1** | **21.391** | **2.35** | **43.88** | **12.292544** | **21.391000 (inherited C)** |
| **08:30** | 20.01 | 13.204 | **2** | not printed at 08:30 | **43.53** | **40.87** | not printed | **13.204000** |
| 09:00 | 21.27 | 14.805 | **2** | not printed at 09:00 | 41.42 | 38.55 | not printed | 14.805000 |

**Original source/provenance facts**:
- At 06:30/07:00/07:30/08:00 the original `TA_F_QC=0` (measured) but `VPD_F_QC=1`, `VPD_F=VPD_F_MDS`, `VPD_F_MDS_QC=1`: all four VPDs are gapfills, not measured QC0 humidity.
- 08:00 `VPD_F=21.391` hPa is just below `es_water(18.96C)≈21.9053` hPa, implying actual vapour pressure ≈0.5143 hPa and RH≈2.35%. This is technically within basic physics, yet an *unverified and extreme* dry MDS source value.
- Stage12c at 08:00 already has 21.391 hPa and Stage12d/12e/12g retain exactly the same value. Hence **the right-hand existing finite value is inherited baseline MDS QC1, NOT newly created gridded Stage12g repair**. Stage12c/d/e/g all have VPD MISSING at 07:00 and 07:30.
- **08:00→08:30 original published source VPD changes -8.187 hPa over EXACTLY 30min as provenance flips from QC1 MDS to QC2 ERA downscaled**. Original implied RH jumps from 2.35% to 43.53%. This exceeds the existing 4hPa source discontinuity scientific-warning screen and merits manual boundary review. Do **not** infer this QC1→QC2 switch proves the 08:00 number is false or release the 07:00/07:30 science holds.
- At 08:30 and 09:00 source VPD QC2, original RH≈43.53% and 41.42%, and companion ERA RH≈40.87% and 38.55%, respectively. QC2 appears **much more consistent with companion ERA humidity than the preceding MDS QC1 boundary**, but values are not necessarily a single measured tower sensor.
- The nearest genuine original VPD_F_QC0 plus tower TA_F_QC0 and thermodynamically valid VPD record in original 2017 is **2017-07-05 13:00**, **1770min = 29h30m after 2017-07-04 07:30**. The 24h window has **zero** legitimate original QC0 VPD humidity anchors. These distant QC0 values cannot be interpolated as a direct 07:00 validation.

Earlier Stage12y strictly tested 2017-07-04 06:30/07:00/07:30/08:00 hypothetical source-RH bridge:
- Signed G retained 06:30 = 3.974495 and 08:00 = 21.391, 07:00 & 07:30 held/missing.
- Hypothetical Stage12w companions 07:00 = 5.154795, 07:30 = 9.345609.
- Three adjacent 30min jumps 1.180300 / **4.190815** / **12.045391** hPa; two violate the 4hPa rule. Stage12z reveals further 08:00→08:30 inherited-source 8.187hPa QC1→QC2 provenance discontinuity, which adds context but does **not** authorize changing the inherited 08:00 original research value.

**Scientific status:** 07:00 and 07:30 keep original signed HOLD. Mark original 08:00 QC1 MDS right boundary as **manual-review priority**, retaining its untouched original source and Stage12g value. Preserve 86 original Stage12 scientific holds, 233 separate earlier protected physics holds, all measured tower T/P and native clocks, Post-v5/DATM/spinup=0. No automated repairs, interpolation, source-clock shifts, resubmissions or source-shadow overwrites.

Next source-only Stage12aa may explicitly compare the **07:30→08:00→08:30** QC1→QC2 transitions against same-timestamp ERA-RH reference along the original complete 06:00–09:00 native half-hours, quantify available and unavailable transitions with the original 4hPa safeguard, and inspect all site-year source QC-class changes. This is only a hypothesis test, never source or forcing mutation.
