# AmeriFlux Batch05 Stage12: original meteorological context for priority humidity anomalies

**Executed 2026-10-25 19:24 UTC (operator log).** Stage12 pinned GitHub script source verified, syntax check passed, self-test passed. Ten original source SHA256 checks passed, Stage10 original report ledgers retained unchanged, and **no original source / Stage10 / forcing / model / Slurm changes**.

```text
STAGE12 SUMMARY sites=10/10 original_events=1750 priority_unique=382 context_rows=4966 approved=0 reports=/iridisfs/home/ly3n24/ameriflux_batch05_stage12/context_20261025T192426Z_1264512
ONLY NEW REVIEW CSV/JSON FILES WRITTEN; NO SOURCE/STAGE10/FORCING/MODEL/SLURM
```

Operator's shell `$HOME` alias:
`/home/ly3n24/ameriflux_batch05_stage12/context_20261025T192426Z_1264512`

## Actual evidence

| Site | Stage10 low water-derived RH<1% source events | Stage12 unique priority events | Native source context rows |
|---|---:|---:|---:|
| US-UiD | 0 | 0 | 0 |
| US-UMB | 23 | 7 | 91 |
| US-UMd | 15 | 0 | 0 |
| US-Var | 62 | 42 | 546 |
| US-Vcm | 509 | 85 | 1,105 |
| US-Vcp | 629 | 41 | 533 |
| US-WCr | 88 | 39 | 507 |
| US-Whs | 1 | 0 | 0 |
| US-Wjs | 401 | 160 | 2,080 |
| US-Wkg | 22 | 8 | 104 |
| **TOTAL** | **1,750** | **382** | **4,966** |

The operator's Stage12 report exporter identified the following **overlapping** priorities in the Stage10 source-ledger data:
- **229** `BRACKETED_MATH_UNAPPROVED` — mathematical interpolations having both qualifying source-QC0 measured anchors (within ±3 hours), not approved as replacements.
- **11** `BRACKETED_NONPHYSICAL` — proposed bracketed interpolation fails the specified water-saturation check.
- **27** `MEASURED_QC00_NEGATIVE` — consolidated measured TA and VPD with slightly/formula-negative derived water RH (US-WCr 26, US-Vcm 1); original source RH boundary values mandate verification before attributing a sensor defect.
- **170** `ERA_PAIR_HOLD` — companion ERA's own TA/VPD physically nonconsistent in 55 cases or an ERA-implied-vapour-pressure/tower-T mismatch in 115 cases.

Four membership totals sum to **437**, but only **382 unique half-hours**, with 55 overlap memberships. **1,368** of the 1,750 low-RH flagged events were outside these four selected priorities; they remain in the original Stage10 CSV and have NOT been reviewed in Stage12. `context_rows=4966` is **13 native rows per selected event** (6 half-hours before, target, 6 after); overlapping target contexts may refer to the same source timestamp and are purposely retained for every event, not 4,966 unique dates.

The three report artifacts saved on IRIDIS6:
- `stage12_priority_targets.csv` — 382 unique priority source timestamps, joined with original Stage10 flags and unapproved candidate values;
- `stage12_original_native_context.csv` — 4,966 rows of raw original tower and companion MDS/ERA inputs around those priorities;
- `stage12_summary.json` — ten original SHA fingerprints, site counts, category overlap counts, contextual row count, and `ALL_CANDIDATES_UNAPPROVED`.

These are not saved on GitHub as CSV data: paths and verified source fingerprints are tracked here, original science files stay on IRIDIS6.

## Next science gate

Stage13 should consume Stage12 CSV/JSON directly, verify their exact source-time consistency and 13 native contexts per target, quantify VPD contrasts and anchor gaps for **229 bracketed but unapproved** candidates, and independently screen the **27 QC0/0 negative** cases for rounding/saturation boundaries. It should print plain-text, read-only summaries with examples, and **must not approve any repair**.

Scientific holds remain: the selected source `RH` values lack independently verified provenance; differences in native saturation convention can explain small formula-negative values; QC2 consolidated VPD already inherits ERA, and MDS QC2/3 does not justify automatic adoption; exact station coordinates/elevations and original data source metadata are still unresolved for some sites. No time shifts, forcing modifications or Slurm.
