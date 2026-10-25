# Stage84 PASS — US-Ho1 2000 ERA VPD/T source mismatch: two manual-review episodes, no forcing change

Date: Sunday 25 October 2026. Actual user-provided IRIDIS6 Stage84 original script Git blob `9118b2a8a7e93d5fa7e78762de5beb14f0dd23f2` matched and self-test, `--check`, and `--audit` **all PASS**.

Isolated on-cluster source result:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage84_Ho1_2000_32_raw_ERA_VPD_vs_ERA_T_source_20261025T225213Z_82b02e9f`.

## Completed science evidence

- FLUXNET native `VPD_F_QC=2` and exact `VPD_F=VPD_ERA` in **17,568/17,568** original Ho1 2000 half-hours; original `TA_F_QC=0` measured source in **17,294** HH, supported by Stage83 original FULLSET source SHA.
- **1,068** physically incompatible pairs `VPD_ERA > eswater(original measured TA_F)` become numerically compatible with `eswater(original TA_ERA)`; this supports the *source pairing mismatch hypothesis*, not a finding that original temperature observations are bad.
- The **different**, disjoint **32** `VPD_ERA > eswater(TA_ERA)` original January 2000 HH persist even with downscaled temperature. Stage84 independently reproduced the source records and isolated **two** contiguous intervals, no original/source/model edits.
- Episode A: native local **2000-01-24 22:30 through 2000-01-25 05:00**, **14 HH / 7 h**; maximum raw ERA VPD excess above eswater(TA_ERA) **0.155156 hPa**, minimum diagnostically implied water-basis RH **−7.180354%**.
- Episode B: native local **2000-01-25 15:00 through 2000-01-25 23:30**, **18 HH / 9 h**; maximum raw ERA VPD excess **0.193342 hPa**, minimum implied RH **−8.302726%**.
- On Jan 24 the earliest flagged datum exceeds eswater only by **0.000129 hPa**, for which numerical precision/rounding matters; differences up to **0.193342 hPa** require more than round-off-level evaluation.
- These negative RH values are **implied mathematical diagnostics**, never direct measured RH. Saturation-over-ice is lower for subfreezing T, and using it *worsens*, not cures, these 32 physically inconsistent VPD/temperature combinations. Original ERA-downscaling pipeline fields can be independently linearly regressed, and not intrinsically a physically guaranteed T/RH pair.
- The original TA_F_QC0 local source temperature is not automatically false just because NOAA Bangor (~46 km away) or ERA-derived temperature differ; the airport is not forest canopy ground truth.

## Human-review decision

**YES — human review is recommended, but scoped to TWO episodes, not all 1,068 mixed-source events or every numerical humidity shadow.** Inspect the Stage84 individual 32 rows and their ±6 h native source context, using original ERA T, ERA VPD, TA_F QC, provenance, and QC, and independently acquired source-paired ERA5-L temperature/specific humidity/surface pressure with correct temporal labels and the site historical UTC effective-period verification. Do NOT presume FLUXNET `TA_ERA` and `VPD_ERA` are direct same-physics companion measurements; these were downscaled/bias corrected separately.

Manual outcome choices: (a) rounding-level insignificant, (b) ERA-downscaling product T/VPD inconsistency, (c) clock/index alignment risk, (d) unresolved independent-source and metadata uncertainty. None directly authorizes replacing original measured temperature or touching CLM-FATES forcing.

**Important log-copy quality check:** The user's pasted Stage84 per-row listing and daily summary show **32/32 source TA_F_QC=0**, but the episode summary displays an apparent QC0 count of `4` and `8` rather than `14` and `18`. Other pasted column headers are visibly truncated. Treat this as possible log formatting/copy corruption, **not as verified science**. Verify the output `32_Ho1_2000_original_VPD_ERA_gt_eswater_TA_ERA_source_cases.csv` and episode CSV from the Stage84 manifest with exact SHA256 and recompute per-episode QC0 counts before signing off on the table. If CSVs genuinely disagree, stop and correct only new diagnostic output, keeping all original data immutable.

## Next model-science decision, AFTER human review

For model meteorology, do not combine the original independently ERA-downscaled VPD with a different original tower TA_F as if physically paired and then patch individual `TA_F_QC0` readings solely because `VPD>es(T)`. Instead evaluate a science-controlled **shadow-only** alternative with thermodynamically paired grid-year data: independent ERA5 / ERA5-L T, specific humidity/dewpoint and pressure at the *same time/grid/vertical level* (and clearly documented water/ice RH convention); derive VPD/RH/QBOT consistently and preserve provenance flags. Compare with the existing source forcing under the same scientifically certified historical tower calendar before authorizing any NetCDF/DATM simulation changes.

Other Batch02 sources remain subject to their independent site-level validation. The broader existing original **16,874 Ho1+BZS humidity-hard source HOLDs**, **15,199 numeric-only humidity shadow candidates**, **1,675 temperature source science HOLDs**, and separate Stage64 **9,389 numeric humidity candidates** remain **not officially approved for forcing**.

No source file, archived Stage49–84 report, model forcing NetCDF, DATM, CIME or Slurm files were modified for Stage84.
