# Batch03 Stage11e-v2 verified science triage and Stage11f human review gate

**Verified on IRIDIS6:** 2026-10-24, operator-supplied terminal log with syntax check, synthetic self-test, read-only check and full audit.  
**Script:** [11e_v2_priority_scientific_triage.py](../scripts/stage11/11e_v2_priority_scientific_triage.py).  
**Scientific status:** **SOURCE EVIDENCE / CANDIDATE PHYSICS PASS; ZERO APPROVED REPAIRS, ZERO POST-V5/DATM/SPINUP APPROVALS.**

Stage11e-v1 failed a one-record synthetic join before source access; v2 fixed this with an explicit synthetic `expected_n=1` versus strict production `expected_n=62` guard. Stage11e-v2's actual IRIDIS6 data checks subsequently **passed**.

## Validated inventory

- **62/62** unique priority targets, 3 source sites: US-MOz 1, US-Mpj 6, US-NC2 55
- **6/6** source VPD/temperature *original* `TA_F_QC=0` air temperature changes reviewed against immediate native neighbours
- **38/38** US-NC2 original `VPD_F_QC=1` VPD values, already numerically present in source, had **nonpositive implied liquid-water vapour pressure** when combined with their native source T
- **5/5** very low but **positive** liquid-water RH values remain in the unchanged/processed-v5 evidence, all at positive temperature
- All Stage11e audited candidates at the 62 target IDs had **positive water-relative implied vapour pressure** (mathematical screen only)
- **0** repairs, source-QC0 modifications or clock offset changes officially approved

### Six original QC0 temperature changes and neighbour evidence

| Site | Source-native time | Original QC0 T (°C) | Previous T (°C) | Next T (°C) | Candidate T (°C) | Both neighbour source QC0? |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| US-MOz | 2016-03-17 22:00 | -15.213 | 13.382 | 10.961 | 12.1715 | Yes |
| US-Mpj | 2020-02-11 06:30 | -17.667 | 1.176 | 1.183 | 1.1795 | No |
| US-NC2 | 2019-01-03 13:00 | -6.759 | 13.567 | 13.138 | 13.3525 | No |
| US-NC2 | 2019-01-04 03:30 | -14.342 | 9.437 | 9.350 | 9.3935 | No |
| US-NC2 | 2019-01-04 16:30 | -13.804 | 9.058 | 10.075 | 9.5665 | No |
| US-NC2 | 2019-01-08 03:30 | -11.506 | 6.829 | 8.214 | 7.5215 | No |

All six candidate T values equal the arithmetic mean of the two adjacent native half-hour source T readings. **This is evidence of short-gap interpolation, not independent confirmation of sensor failure**. For five events at least one adjacent source record is not QC0, so its QC provenance must be disclosed explicitly before an acceptance decision. The US-MOz event has two QC0 neighbours but still requires station clock, sensor and weather context.

### 38 original US-NC2 QC1 VPD conflicts

All 38 affected source VPD values are original gap-filled `VPD_F_QC=1`, with paired original native-source T and VPD yielding `e_a=es_water(T)-VPD <= 0`. The invalid source combination is independently evident without swapping a separately downloaded reanalysis dataset into it. These source values were subsequently replaced with companion ERA-origin candidates in Stage07; this fixes the numerical water-RH sign in the candidates **but does not independently validate actual tower humidity**.

The 38 rows occur at consecutive half-hour times within *four apparent temporal clusters* directly visible in the Stage11e log:

| Native interval (unapproved UTC conversion) | Expected row count from log |
| --- | ---: |
| 2025-03-21 19:30 – 2025-03-22 01:00 | 12 |
| 2025-03-23 09:00 – 2025-03-23 12:00 | 7 |
| 2025-03-26 08:00 – 2025-03-26 12:30 | 10 |
| 2025-03-27 08:00 – 2025-03-27 12:00 | 9 |
| **Total** | **38** |

Stage11f is intended to formally recompute and checksum these contiguous groups; episode membership is not a reason to replace surrounding otherwise valid source observations.

### Five positive RH below 1%

| Site | Source-native time | Source VPD QC | Stage07 candidate air T (°C) | Candidate RH over water (%) |
| --- | --- | ---: | ---: | ---: |
| US-Mpj | 2018-02-02 17:30 | 2 | 8.822 | 0.668699 |
| US-Mpj | 2018-02-02 19:00 | 2 | 5.798 | 0.439167 |
| US-NC2 | 2025-03-18 19:00 | 2 | 8.664 | 0.163385 |
| US-NC2 | 2025-03-23 12:30 | 1 | 18.135 | 0.868664 |
| US-NC2 | 2025-03-25 09:00 | 1 | 16.214 | 0.077323 |

These are **all at positive temperatures**: water-vs-ice saturation is *not the principal issue for these five exact records*. They remain plausible algebraically (RH strictly positive), but extremely dry and hence require source/instrument/metadata/temporal corroboration. Do not automatically clip to 1%.

### Summary by station

| Site | Unique review targets | Original nonpositive implied vapour pressure at reviewed source rows | Candidate positive implied vapour pressure |
| --- | ---: | ---: | ---: |
| US-MOz | 1 | 0 | 1 |
| US-Mpj | 6 | 2 | 6 |
| US-NC2 | 55 | 47 | 55 |

**Important:** US-NC2's 47 total source-inconsistent review targets include the 38 original QC1 VPD replacements; do **not** present 47 as an additional disjoint number of errors. They are overlapping sets within the 55 target IDs.

## Source report retained on IRIDIS6

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage11e_science_triage_20261024T074227Z_062db11d/`

Contains 62-event physics evidence, six QC0 neighbour-source rows, all 38 original QC1 VPD conflicts, five preserved near-zero RH cases and a SHA-pinned `scientific_hold_receipt.json`.

## Next: Stage11f review package (new code; not yet run on IRIDIS6)

[11f_human_review_signoff_queue.py](../scripts/stage11/11f_human_review_signoff_queue.py) verifies Stage11e-v2's input SHA256 and Stage11d's unchanged-manual receipt, recomputes the contiguous QC1 VPD clusters, preserves six QC0 neighbour **values and QC codes**, and prepares an **unsigned** human-review template for each of the 62 event IDs.

**Do not automatically sign off the 62 events.** Human-reviewed decisions require source quality documentation, native timestamp/clock verification, tower measurement location/height, independent meteorological evidence where available, uncertainty, and written decision rationale. Only then can a separately versioned Post-v5 scientific approval process begin, including full-year meteorological impacts, PFT/surface and CO2 protocol checks.

All Stage07 source and processed-v5 candidates remain immutable; `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` stays in place. **No DATM, CIME cases, restart or Slurm jobs authorized.**
