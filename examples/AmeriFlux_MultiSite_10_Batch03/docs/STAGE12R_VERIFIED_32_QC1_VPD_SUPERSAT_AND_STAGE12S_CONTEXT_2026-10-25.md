# Batch03 Stage12r VERIFIED — all 32 original QC1 VPD edge values violate the Stage12c water-VPD physical bound

**IRIDIS6 operator result: 2026-10-25 09:46 UTC.** Git blob/syntax, `--self-test`, `--check` and `--run` all PASS. An isolated SHA-receipted source-only report was written at:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12r_32_QC1_native_VPD_source_physics_and_ERA_RH_20261025T094639Z_a770eeb8/`

## Exact published output

| Signed original QC1 neighbor state | Site | 32 neighboring *sides* | Stage12c initial water VPD test |
| --- | --- | ---: | --- |
| BOTH_FINITE_DIFFER | US-Me6 | 22 | `C_VPD_NEGATIVE_OR_AT_ABOVE_WATER_SATURATION` |
| RAW_ONLY_FINITE | US-Me6 | 8 | Same |
| BOTH_FINITE_DIFFER | US-NR1 | 2 | Same |

**All 32 source QC1 VPD values exceed or equal** `es_water(TA_USE)` at the same original native timestamp, such that implied water vapour pressure `ea = es(T)-VPD <= 0`. Stage12c correctly rejected them under its pre-existing basic physical check; the presence of a finite raw QC1 number does not confer physical validity. This does not explain *why* the source value conflicts: tower temperature QC/status, source gap-fill chronology, source/companion product representativeness and native clock hypothesis remain open.

Stage12r reproduces **24** signed Stage12d matched companion `TA_ERA/VPD_ERA` RH-only transfer values (22 US-Me6, 2 US-NR1), leaving unchanged Stage12c original site `TA_USE` and `PSRF`. Such transfer is physically internally consistent but is not an independent tower measurement.

The remaining **8 US-Me6 raw-finite source sides** have exact original Stage12d and Stage12e science holds:

| Stage12d hold reason | Stage12e hold reason | Sides | Later finite Stage12g reference |
| --- | --- | ---: | ---: |
| `COMPANION_ERA_T_MISMATCH_GT5C` | `NO_VERIFIED_ERA5LAND_SOURCE_FOR_SITE_YEAR` | 4 | 2 |
| `NEW_EDGE_JUMP_GT4HPA_HOLD` | `NO_VERIFIED_ERA5LAND_SOURCE_FOR_SITE_YEAR` | 4 | 0 |

The latter Stage12e reason means *the sealed Stage12e snapshot had no verified year source* for this particular gap. Subsequent Stage12f/12g sources may have changed available research candidates; Stage12g finite values do **not** release the original held VPD transitions. At all times, original **38 VPD neighbor-jump held native events + 48 site/grid T held native events = 86** remain science HOLD; the separately protected original 233 source physical holds remain protected. No source release, forcing, clock, physics threshold, DATM/CIME/Slurm, Post-v5 or spinup was changed.

## Stage12s next: original 32 source-neighbor time-series context, not automatic fixes

Read signed Stage12r science tables plus pinned Stage07 original FLUXMET and matching native `TA_ERA/VPD_ERA`. At each of 32 original QC1-side timestamps, audit a native **±6-hour half-hour context** with original VPD and temperature QC flags, water saturation, implied RH, paired source `TA_ERA`/VPD_ERA, and signed Stage12r stage-transfer outcomes. Distinguish original measured-QC0 versus QC1 source references; count/locate contiguous water-physics invalidity; assess whether physically inconsistent QC1 VPD is only one timestamp or occurs alongside periods of smoothly varying source T. Maintain the original native clock and all signed science holds. No value imputation, threshold relaxation, model deployment, or automatic acceptance. The Stage12s code is a separate new report-only tool and is not yet tested on IRIDIS6.

**Stage12s operator-ready code (unverified on IRIDIS6):** Git commit `ca6691bf85b6b6a75b3f805297b085c2fe173284`, Git blob `50772a336f3fd15cb0da2caae1f543e5098dfcf0`. The study distinguishes true original tower `TA_F` from potentially fallback-filled Stage12c `TA_USE` before drawing source-temperature conclusions, requires genuinely physically valid QC0 T/VPD before labeling a nearby QC0 reference, and SHA-verifies Stage12r/Stage12q/Stage12c/Stage07 receipts plus full original raw/ERA releases. The source-only check/run have not yet been operator-verified.
