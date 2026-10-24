# Stage11d — verified three-site priority source context (2026-10-24)

**Status:** IRIDIS6 `--self-test`, `--check` and `--run` all PASS. This is a GitHub summary transcribed from an operator-provided Stage11d terminal log; the event-level CSVs and SHA256 receipts remain on IRIDIS6 and are not reproduced here.

**Input scope:** 105 Stage11c original-to-candidate changes plus 18 manual-review entries and five positive RH<1% records at three sites. Category overlap is explicitly deduplicated by (site, native timestamp, variable).  
**Output:** 62 unique scientific-review targets, exactly **558 native half-hour context records** (+/-2 hours, nine rows each).

| Site | Unique priority targets | Nine-row context records | Overlap beyond distinct review IDs |
| --- | ---: | ---: | ---: |
| US-MOz | 1 | 9 | 0 |
| US-Mpj | 6 | 54 | 2 |
| US-NC2 | 55 | 495 | 3 |
| **Total** | **62** | **558** | **5** |

The original source and companion ERA timestamps matched at the centre of **all 62** context windows. *This does not establish independently verified site humidity or approve an offset.*

## Exact source VPD replacement provenance

**38 / 38** US-NC2 ERA-source VPD replacements have the exact Stage07 event reason

`TA_VPD_inconsistent_VPD_only|remaining_gap_filled_ERA`

and original **`VPD_F_QC=1`** (gap-filled source VPD, not a native measured QC0 value). The original VPD values were **numerically present** in FLUXMET; the Stage07 QC-v5 algorithm discarded those values upon testing the original T/VPD pair, then filled the resulting candidate gap with an ERA-source value. The reason string establishes the *algorithmic pathway*; it does not by itself identify whether the original source values are definitely inaccurate or ERA replacements are closer to true tower meteorology.

### Six original source QC0 temperature changes

All six `TA_F`, with `isolated_spike_ERA_confirmed|short_gap_interpolated`. *The event date/times below are source-native times, not approved UTC conversions.*

| Site | Source-native time | Original TA (°C) | Candidate TA (°C) | Original companion ERA TA (°C) |
| --- | --- | ---: | ---: | ---: |
| US-MOz | 2016-03-17 22:00 | -15.213 | 12.1715 | 9.601 |
| US-Mpj | 2020-02-11 06:30 | -17.667 | 1.1795 | -3.869 |
| US-NC2 | 2019-01-03 13:00 | -6.759 | 13.3525 | 12.537 |
| US-NC2 | 2019-01-04 03:30 | -14.342 | 9.3935 | 9.524 |
| US-NC2 | 2019-01-04 16:30 | -13.804 | 9.5665 | 11.016 |
| US-NC2 | 2019-01-08 03:30 | -11.506 | 7.5215 | 10.410 |

An ERA-consistent interpolation of a large QC0 temperature spike is a *reviewable algorithmic candidate*, not approval to overwrite a measured-flagged source record without corroborating native-neighbour observations, station metadata and sensor information.

### Four manual-review rows with no final variable modification

| Site | Source-native time | Variable | Source VPD QC | Reason |
| --- | --- | --- | --- | --- |
| US-Mpj | 2018-02-02 17:30 | VPD_F | 2 | very_low_but_positive_RH_preserved_review |
| US-Mpj | 2018-02-02 19:00 | VPD_F | 2 | very_low_but_positive_RH_preserved_review |
| US-NC2 | 2025-03-23 12:30 | VPD_F | 1 | very_low_but_positive_RH_preserved_review |
| US-NC2 | 2025-03-25 09:00 | VPD_F | 1 | very_low_but_positive_RH_preserved_review |

These values remain flagged for science review, not forcibly altered. Overall Stage11c/Stage11d counted **five** positive RH<1% target events, and **18** manual rows, with four unchanged manual rows; they are overlapping sets, not independent additive case counts.

## Permanent Stage11d report on IRIDIS6

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage11d_priority_source_context_20261024T072456Z_8e3c6249/`

Main evidence:
- `priority_review_target_index.csv`
- `plus_minus_2h_native_source_ERA_candidate_context.csv`
- `six_measured_QC0_changes.csv`
- `38_ERA_replacements_evidence.csv`
- `four_unmodified_manual_holds.csv`
- `read_only_provenance.json`

## Stage11e: final scientific triage (code committed; IRIDIS run pending)

[Stage11e](../scripts/stage11/11e_priority_scientific_triage.py) reads only the sealed Stage11d evidence, recalculates the original `TA_F + VPD_F` implied water vapour pressure for all 62 targets, diagnoses **what physical condition each of the 38 US-NC2 source-QC1 VPD values actually violates**, checks six QC0 temperature edits against the immediate +/-30 minute native neighbours, and gives separate ice-phase cautions for the five very-low-positive RH cases.

The Stage11e source/ERA comparison is *not* an independent measurement; the output is a human science decision queue, **not an approved repair or readiness certification**.

**All approvals remain zero:** humidity correction, original QC0 replacement, clock adjustment, Post-v5, DATM, PFT/CO2 protocol or spinup. Stage07's `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker must remain.

## Stage11e-v1 self-test failure and corrected v2

The operator attempted [Stage11e-v1](../scripts/stage11/11e_priority_scientific_triage.py) on IRIDIS6 after downloading and verifying the script. The syntax check passed, but the `--self-test` stopped in `triage()` with `ValueError: Target-centre merge lost or duplicated a review record` **before source reports were read or any data modified**. Root cause: `triage()` mandated `len(primary)==62` even when invoked on its *one-record synthetic self-test*. The error alone does not establish a real Stage11d join problem.

[Stage11e-v2](../scripts/stage11/11e_v2_priority_scientific_triage.py), committed 2026-10-24, supplies `expected_n=62` for production, `expected_n=1` for the synthetic test and explicit negative tests for a mismatched source key and default 62-record enforcement. It retains the existing sealed Stage11d evidence, no-approval guards, and no-modification behavior. **The corrected v2 has not yet been run on actual IRIDIS6 evidence**; no Phase-0 or Post-v5 acceptance has changed.
