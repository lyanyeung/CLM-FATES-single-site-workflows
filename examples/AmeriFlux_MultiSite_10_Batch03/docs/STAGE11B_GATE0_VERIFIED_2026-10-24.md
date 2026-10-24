# AmeriFlux Batch03 — Stage11b verified numeric Post-v5 Gate-0

**Date of successful IRIDIS6 operator check:** 2026-10-24.  
**Scope:** three existing Stage07 versioned *numeric-only* QC-v5 candidates — US-MOz, US-Mpj, US-NC2.  
**Status:** `--self-test`, `--check` and `--run` all passed. No new forcing was generated or approved.

## Verified output

| Site | NO_LEAP records | Raw-to-candidate variable changes | Original QC0 changes | Manual review entries | ERA RH floors | ERA replacement variables | Minimum water-relative RH (%) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| US-MOz | 315,360 | 6 | 1 | 0 | 0 | 0 | 2.206422 |
| US-Mpj | 315,360 | 16 | 1 | 5 | 0 | 0 | 0.439167 |
| US-NC2 | 367,920 | 83 | 4 | 13 | 0 | 38 | 0.077323 |
| **Total** | **998,640** | **105** | **6** | **18** | **0** | **38** | — |

The original release inputs, exact original source timestamps, Stage07 output receipts, full NO_LEAP candidate timeline, VPD/RH/QBOT positive liquid-water physics, TBOT/QBOT/PSRF/precipitation conversions and raw-to-event count ledger passed the Stage11b numeric gates. This outcome does **not** prove changed QC0 values are meteorologically preferable, or that surviving RH below 1% must be wrong. **Very low but positive RH is a science review signal, never an automatic replacement instruction.**

**IRIDIS Stage11b report** (raw CSVs/receipt remain there):  
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage11b_postv5_gate0_three_sites_20261024T065829Z_79a2f708/`

Read-only results: `candidate_sites=3/3 numeric_audit=3/3 postv5_approvals=0 DATM_ready=0 spinup_authorizations=0`.

## What remains scientifically unapproved

1. **Six changes to original QC0 measurements**: one each at US-MOz, US-Mpj and four at US-NC2. Review exact native timestamps, source observation QC, nearby rows, source ERA, modification reason, magnitude and uncertainty.
2. **18 manual-review records**: five US-Mpj and thirteen US-NC2. Manual-review count is not the same as number of modified rows; unchanged suspicious observations can still require review.
3. **38 ERA-source replacement variables at US-NC2**: ERA source and time matching can establish provenance, but not independent tower truth.
4. **Residual positive RH below 1%**: US-Mpj minimum 0.439167%, US-NC2 minimum 0.077323%. These are physically positive under the liquid-water convention; do not assume automatic clipping or rejection. Investigate tower/source plausibility and ice-phase convention.
5. **Whole-workflow readiness**: time offsets, site elevations/measurement heights, PFT/surface matching, CO2 policy, Post-v5 review, DATM and spinup all still require explicit scientific authorization. Stage07's `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker MUST remain.

## Next Stage11c (committed, not yet run on IRIDIS6)

[Stage11c — exact QC0, manual and ERA change audit](../scripts/stage11/11c_qc0_manual_era_change_review.py) reopens the *existing* source-pinned Stage07 candidate and source releases, checks all 105 event tuples `(site,time,variable)` against original and final values, verifies original QC and companion ERA exact native-time values, extracts the six QC0 changes and 18 manual-review entries, and produces low-RH-specific review rows. Successful Stage11c only produces further review evidence, never a forcing replacement or an approved model setup.

For overall 10-site status and blocked humidity episodes, see [Stage10k scientific decision gate](STAGE10K_SCIENTIFIC_DECISION_GATE_2026-10-24.md) and [Stage11a review matrix code](../scripts/stage11/11a_science_decision_matrix.py).
