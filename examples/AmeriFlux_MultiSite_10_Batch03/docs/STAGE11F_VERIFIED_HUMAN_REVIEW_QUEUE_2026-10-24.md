# AmeriFlux Batch03 — Stage11f verified human science review queue

**Validation date:** 2026-10-24. Operator-confirmed IRIDIS6 Python syntax, `--self-test`, `--check` and `--run` all **PASS**.

**Scope:** US-MOz, US-Mpj, US-NC2; exactly **62 unique** source-native `(site, time, variable)` priority review targets. Inputs SHA-locked to Stage11e-v2 and Stage11d. No original meteorology, candidate forcing, DATM, case, restart or Slurm changes.

**Stage11f input script:** [11f_human_review_signoff_queue.py](../scripts/stage11/11f_human_review_signoff_queue.py)

**Report on IRIDIS6:**

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage11f_human_science_review_20261024T074958Z_6ae6d5d7/`

Principal files:
- `62_human_scientific_review_queue.csv` — unsigned, all 62 event IDs, priority and status (all unapproved)
- `4_US-NC2_QC1_VPD_episodes.csv` — exact native half-hour grouped records
- `6_original_QC0_T_neighbor_QC_detail.csv` — original/source candidate T and both neighbouring source QC
- `5_positive_RH_below_1pct_source_reviews.csv` — extreme but positive, source-dependent humidity cases
- `4_unmodified_manual_records.csv` — original suspicious events preserved unchanged
- `SCIENTIFIC_HUMAN_SIGNOFF_GUIDE.md` and `read_only_scientific_hold_receipt.json`

## Exact 62-record human review priority census

| Site | Changed source QC0 TA, P0 | Original nonpositive-ea QC1 VPD, P0 | Positive RH<1%, P1 | Other manual VPD review, P1 | Unique total |
| --- | ---: | ---: | ---: | ---: | ---: |
| US-MOz | 1 | 0 | 0 | 0 | 1 |
| US-Mpj | 1 | 0 | 2 | 3 | 6 |
| US-NC2 | 4 | 38 | 3 | 10 | 55 |
| **TOTAL** | **6** | **38** | **5** | **13** | **62** |

The prioritization is mutually exclusive for display; the underlying science-review reason flags can overlap. The Stage11f priority totals are not the same concept as all 18 Stage11c manual-review rows.

### Six original QC0 air temperature changes

Every candidate value is the exact mean of the two adjacent source values, but the source QC composition differs and **none is formally approved**.

| Site | Source-native time | Original TA_F (°C) | Left TA_F (°C, QC) | Right TA_F (°C, QC) | Stage07 candidate (°C) |
| --- | --- | ---: | --- | --- | ---: |
| US-MOz | 2016-03-17 22:00 | -15.213 | 13.382 (QC0) | 10.961 (QC0) | 12.1715 |
| US-Mpj | 2020-02-11 06:30 | -17.667 | 1.176 (QC1) | 1.183 (QC1) | 1.1795 |
| US-NC2 | 2019-01-03 13:00 | -6.759 | 13.567 (QC1) | 13.138 (QC1) | 13.3525 |
| US-NC2 | 2019-01-04 03:30 | -14.342 | 9.437 (QC1) | 9.350 (QC1) | 9.3935 |
| US-NC2 | 2019-01-04 16:30 | -13.804 | 9.058 (QC1) | 10.075 (QC0) | 9.5665 |
| US-NC2 | 2019-01-08 03:30 | -11.506 | 6.829 (QC1) | 8.214 (QC0) | 7.5215 |

Original spike size, companion ERA agreement and a neighbouring QC0 each provide different levels of evidence. In particular, **US-MOz** is the strongest neighbour-measured case (both neighbours QC0), whereas US-Mpj and US-NC2 still depend substantially on source gapfill QC1.

### Four original US-NC2 QC1 VPD physics-conflict episodes

All 38 source `VPD_F_QC=1` values yielded **nonpositive implied water vapour pressure** with paired native-source TA. The Stage07 `secondary_era_replacement` made candidate humidity mathematically positive but is not independent tower validation.

| Episode | Native-start | Native-end | Rows | Duration (rows × 30 min) | Min source implied e_a (hPa) | Median candidate water RH |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 01 | 2025-03-21 19:30 | 2025-03-22 01:00 | 12 | 6.0 h | -2.649475 | 33.296980% |
| 02 | 2025-03-23 09:00 | 2025-03-23 12:00 | 7 | 3.5 h | -6.007006 | 59.548193% |
| 03 | 2025-03-26 08:00 | 2025-03-26 12:30 | 10 | 5.0 h | -3.678934 | 51.013397% |
| 04 | 2025-03-27 08:00 | 2025-03-27 12:00 | 9 | 4.5 h | -2.994605 | 38.256219% |
| **Total** | — | — | **38** | **19.0 h** | — | — |

All timestamps are **source-native only**. No UTC offset, model-day classification or local-clock conversion has been approved.

### Five very low positive liquid-water RH candidates

| Site | Native time | Native VPD source QC | Stage07 TA (°C) | Stage07 RH over water |
| --- | --- | ---: | ---: | ---: |
| US-Mpj | 2018-02-02 17:30 | 2 | 8.822 | 0.668699% |
| US-Mpj | 2018-02-02 19:00 | 2 | 5.798 | 0.439167% |
| US-NC2 | 2025-03-18 19:00 | 2 | 8.664 | 0.163385% |
| US-NC2 | 2025-03-23 12:30 | 1 | 18.135 | 0.868664% |
| US-NC2 | 2025-03-25 09:00 | 1 | 16.214 | 0.077323% |

Each is positive under the water-phase equation at a **positive** air temperature. It can be a source/provenance/representativeness issue and should not be clipped or rewritten on the basis of a 1% threshold alone.

## What is still required

**Next operation is a human scientific evaluation**, not another automatic repair algorithm. Make a *separate working copy* of the unsigned review queue, never alter Stage11f's hash-sealed results. For each selected event, record provenance or instrument documentation, independent humidity evidence where available, native clock and site height/elevation, alternative-candidate uncertainty, and a written reason to `KEEP_CANDIDATE`, `REVERT_CANDIDATE` or `CONTINUE_HOLD`.

**These action labels are a proposed future human review convention, not decisions already taken.** Do not treat an editable working sheet as model authorization. Before a new versioned forcing candidate can be prepared, independent scientific and Post-v5 gates (full annual chronology/QC, PFT/surface, CO2 protocol, DATM) must be reviewed in a separate controlled approval step.

**Current scientific/model status:** 0 approved changes; 0 clock offsets; 0 Post-v5 accepted sites; 0 DATM-ready sites; 0 spinups authorized. The Stage07 `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker stays in place.

Source: operator Stage11f-v1 `--run` terminal log (2026-10-24), with original sealed CSVs on IRIDIS6.
