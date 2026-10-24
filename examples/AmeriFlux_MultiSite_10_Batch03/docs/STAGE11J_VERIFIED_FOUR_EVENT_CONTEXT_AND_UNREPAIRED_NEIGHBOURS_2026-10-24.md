# Stage11j VERIFIED: four introduced-jump source events; 11 potential uncorrected neighbour humidity records

**Date:** 2026-10-24. User's IRIDIS6 terminal log confirmed Stage11j `--self-test` PASS, `--check` PASS, `--run` PASS. Stage07, source, Stage11h, DATM, CIME and Slurm were untouched.

**SHA-recorded read-only report:**
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage11j_four_jump_original_ERA_context_20261024T092017Z_5fc4bfd6/`

**Source provenance:** original FLUXMET site data (source-native clock, QC flags, original temperature/VPD) and release-paired site-downscaled ERA companion; Stage07 sealed processed_v5 forcing and Stage11h sealed shadow candidate.

## The four focus events

| Station | Exact native time | Original VPD QC | Original implied actual vapour pressure (hPa) | Original RH over water (%; inferred) | Paired ERA RH over water (%) | Stage07 RH (%) | Stage11h RH (%) | Stage11i maximum added neighbour VPD jump (hPa) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| US-Mpj | 2018-02-02 17:30 | 2 | +0.075809 | +0.668699 | 20.834339 | 0.668699 | 20.834339 | 2.286140 |
| US-NC2 | 2025-03-18 19:00 | 2 | -0.374674 | invalid | 33.210889 | 0.163385 | 33.210889 | 3.706716 |
| US-NC2 | 2025-03-23 12:30 | 1 | +0.180697 | +0.868664 | 47.793355 | 0.868664 | 47.793355 | 9.761132 |
| US-NC2 | 2025-03-25 09:00 | 1 | +0.014242 | +0.077323 | 49.340146 | 0.077323 | 49.340146 | 8.227839 |

**Important:** the original source US-NC2 202503181900 yields *negative* actual vapour pressure. The Stage07 candidate at that exact time had slightly positive RH 0.163385% because it had already altered VPD. Stage11h then chose the source-companion ERA RH at retained temperature. Do not confuse the original and Stage07 statuses.

All four Stage11h centre candidates are numerically positive and based on the verified companion ERA RH; the large *new* jumps do not by themselves disprove the replacement. Review the quality of the adjacent source records.

## Source-native contexts indicating potential missed neighbour issues

Original source humidity calculated consistently with Stage07's `es_water(T_F)` can be **1–10% RH** and therefore outside the user's previous explicit `<1%` replacement list, even where the paired companion ERA RH is 20–65%. The original source QC1/QC2 flag indicates gapfilled/downscaled provenance rather than direct high-quality QC0 measurement. This difference is a **reason to audit**, not an automatic signal to replace every neighbour.

The following **11 additional, still-as-original-in-Stage07-and-Stage11h, source-native half-hours** satisfy an illustrative *review-only* screen on the Stage11j printed ±3h contexts:

`original_rh < 10%`; `companion_ERA_RH >= 20%`; `companion_ERA_RH - original_rh >= 20 percentage points`; source `VPD_F_QC >= 1`; exact record still has original VPD in Stage07 and Stage11h.

| Site | Original native time | Source computed RH (%) | Companion ERA RH (%) | Reason for review |
| --- | --- | ---: | ---: | --- |
| US-NC2 | 2025-03-18 18:30 | 1.44 | 29.61 | Immediately before an originally physically impossible centre |
| US-NC2 | 2025-03-18 19:30 | 9.89 | 38.46 | Immediately after that centre |
| US-NC2 | 2025-03-23 13:00 | 4.01 | 46.66 | Directly after the newly corrected 12:30 event |
| US-NC2 | 2025-03-23 13:30 | 4.26 | 45.41 | Same source QC1 humidity episode |
| US-NC2 | 2025-03-23 14:00 | 2.96 | 44.24 | Same source QC1 humidity episode |
| US-NC2 | 2025-03-23 14:30 | 2.27 | 43.24 | Same source QC1 humidity episode |
| US-NC2 | 2025-03-23 15:00 | 8.21 | 42.27 | Same source QC1 humidity episode |
| US-NC2 | 2025-03-25 08:00 | 9.42 | 64.02 | Before 09:00 corrected extreme-dry event |
| US-NC2 | 2025-03-25 08:30 | 8.14 | 56.21 | Before corrected event |
| US-NC2 | 2025-03-25 09:30 | 6.70 | 40.46 | After corrected event |
| US-NC2 | 2025-03-25 10:00 | 3.87 | 33.06 | After corrected event |

Values are computed from the operator's Stage11j original T/VPD rows and printed companion RH percentages, rounded to two decimal places. **This is an unverified review candidate *count derived from the pasted context*, not a validated new scientific decision.** The 11 source-native keys are beyond the 53 originally selected replacement keys and are not eligible for automatic writes.

Three more review-screen neighbours (US-Mpj 201802021800 and 201802021830; US-NC2 202503251030) were **already modified during Stage07**, so they must *not* be counted as untouched source values or automatically written again. Stage11j's original source RH can be negative while its Stage07 value is already physically reconciled.

There may be more suspect samples outside these four ±3h windows. This 11-event list is an **event-scoped suggestion**, not an exhaustive full-site or Batch03 anomaly count. Other seven Batch03 sites and their 1,924 scientific humidity issues are not addressed here.

## Interpretation of the four event contexts

1. **US-Mpj 201802021730**: Paired ERA RH is continuous around 20–22%; the already-corrected 18:00/18:30 source-negative humidity points are closer to the companion ERA. The selected 17:30 trial may fit these corrected downstream records, although 17:00 remains comparatively drier. Review instrumentation before signing.
2. **US-NC2 202503181900**: Originally impossible humidity; Stage11h candidate may be more physically coherent, but 18:30 and 19:30 source gaps are unusually dry against companion ERA and should be reviewed as a group.
3. **US-NC2 202503231230**: The old source originally went from negative RH at 12:00 to just positive at 12:30 and stayed ~2–4% RH through 14:30. The companion ERA RH decreased smoothly from ~49% at 12:00 to ~43% at 14:30. 12:30 was repaired alone, leaving a 10.86-to-20.62 hPa VPD jump at 13:00. Event-level source review, not automatic smoothing, is required.
4. **US-NC2 202503250900**: Earlier and later originally unmodified QC1 humidity at 08:00, 08:30, 09:30 and 10:00 has RH ~4–9%, while companion ERA RH is ~33–64%. Isolated 09:00 repair creates a sharp VPD spike boundary. Review if the larger episode includes other flawed source gapfilling.

## Next read-only decision gate

Implement a small **Stage11k context-only classifier**, sourcing the sealed Stage11j CSV+receipt to recalculate the source RH and compare to ERA and Stage07/Stage11h. Verify the 11 untouched events separately from 3 **already Stage07-repaired** neighbour samples. Write only a report for operator inspection; do not alter any Stage07/Stage11h forcing. Never infer that ERA companion is tower ground truth. A human decision extending the repair mask beyond the original 53 would require its own new SHA-sealed user decision list and isolated successor trial.

**Current formal status:** Four hotspots scientifically HOLD, 0 signed additional neighbours, 0 formally Post-v5 approved stations, 0 DATM/spinup authorized. Stage07 and Stage11h `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` remain.
