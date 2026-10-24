# AmeriFlux Batch03 — Stage11c verified QC0 and manual audit

**Observation:** Operator-run 2026-10-24: `stage11c-v1-20261024-event-evidence` passed self-test, `--check` and `--run`, with no original source, candidate forcing, DATM, case or Slurm modification. This is a human-readable summary of the operator log, **not** the underlying SHA-sealed full event CSV.

**Report location on IRIDIS6**:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage11c_qc0_manual_review_20261024T071530Z_ce6fdbb8/`

## Gate-0 verified outcome

| Site | Original source-to-v5 changes | Measured-QC0 values modified | Manual records | Comp. ERA replacements | RH between 0 and 1% |
| --- | ---: | ---: | ---: | ---: | ---: |
| US-MOz | 6 | 1 | 0 | 0 | 0 |
| US-Mpj | 16 | 1 | 5 | 0 | 2 |
| US-NC2 | 83 | 4 | 13 | 38 | 3 |
| **TOTAL** | **105** | **6** | **18** | **38** | **5** |

The Stage11c event ledger shows **zero original missing records** for the changed-variable list. In particular, the 38 `secondary_era_replacement` events at US-NC2 were originally present as numeric input, but were replaced later within the Stage07 QC-v5 procedure. The *reason for each* is a required review; this log does not prove the original value was invalid or that a companion ERA replacement was meteorologically correct.

### Six changed source QC0 temperature values

All six were `TA_F` with the recorded algorithmic reason
`isolated_spike_ERA_confirmed|short_gap_interpolated`, final source
`local_short_interpolation`. None is a formally approved human-reviewed correction.

| Site | Native source time | Original measured-flagged TA (°C) | Candidate TA (°C) | Original same-time companion ERA TA (°C) |
| --- | --- | ---: | ---: | ---: |
| US-MOz | 2016-03-17 22:00 | -15.213 | 12.1715 | 9.601 |
| US-Mpj | 2020-02-11 06:30 | -17.667 | 1.1795 | -3.869 |
| US-NC2 | 2019-01-03 13:00 | -6.759 | 13.3525 | 12.537 |
| US-NC2 | 2019-01-04 03:30 | -14.342 | 9.3935 | 9.524 |
| US-NC2 | 2019-01-04 16:30 | -13.804 | 9.5665 | 11.016 |
| US-NC2 | 2019-01-08 03:30 | -11.506 | 7.5215 | 10.410 |

The isolated-spike/short-gap rule is plausibly suitable for an errant temperature sensor spike; it cannot be signed off solely on magnitude or ERA agreement. Preserve both neighbor observations with source QC, the independent companion ERA, day/night and site-clock information, and the fact that the original source code was QC0. **US-MOz has zero manual notes but one QC0 change**, highlighting why automatic source-QC0 repair requires an independent review.

### Manual-review reason inventory

| Station | Reason | Records |
| --- | --- | ---: |
| US-Mpj | large_or_measured_VPD_reconstruction_review | 2 |
| US-Mpj | near_zero_vapor_pressure_candidate_repaired_ERA_RH_review_required | 1 |
| US-Mpj | very_low_but_positive_RH_preserved_review | 2 |
| US-NC2 | large_or_measured_VPD_reconstruction_review | 8 |
| US-NC2 | near_zero_vapor_pressure_candidate_repaired_ERA_RH_review_required | 2 |
| US-NC2 | very_low_but_positive_RH_preserved_review | 3 |

**Four manual-review rows** (two per site, US-Mpj and US-NC2) did not correspond to a final modified variable. All manual-row saved candidate values matched the final Stage07 values in the operator's successful run. This is not a case of four unexplained ledger changes: unchanged but suspicious low RH can still warrant review.

Pandas emitted two `FutureWarning` lines regarding concatenation with empty/all-NA entries. Those warnings did not affect this verified run; retain prior script/report unchanged for reproducibility.

## Next focused evidence package, not another repair algorithm

[Stage11d](../scripts/stage11/11d_priority_change_context_review.py), now committed but **not yet run against IRIDIS6**, is a read-only ±2-hour original-vs-candidate/ERA time-series context extractor for the **6 QC0 changes, 38 ERA-source replacements, 18 manual entries and 5 positive RH<1% cases**, with overlap deduplication by `(site,time,variable)`. Its principal question is why 38 numeric original readings were overwritten and whether six anomalous QC0 temperatures have credible corroborating neighbors. No value is approved.

**No Post-v5, clock, PFT, DATM or spinup permission has been granted.** Stage07's `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker is still required.
