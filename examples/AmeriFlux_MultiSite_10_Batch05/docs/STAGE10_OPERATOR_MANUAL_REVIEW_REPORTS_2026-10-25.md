# AmeriFlux Batch05 — Stage10 report export: confirmed operator run, 2026-10-25

## Evidence and distinction

The IRIDIS6 operator pasted the complete stdout of the verified Stage10 report exporter:

```text
SOURCE VERIFIED
STAGE10 SELF-TEST PASS | original QC0 anchors, bracketed trial, ERA physics, report only
STAGE10 SUMMARY sites=10/10 events=1750 negative=1559 reports=/iridisfs/home/ly3n24/ameriflux_batch05_stage10/review_20261025T180413Z_682688
ONLY REVIEW CSV/JSON WRITTEN; NO ORIGINAL/FORCING/DATM/CASE CHANGES; NO SLURM
STAGE10_REPORTS=/home/ly3n24/ameriflux_batch05_stage10/review_20261025T180413Z_682688
```

The script printed its resolved output directory under `/iridisfs/home`; the shell echoed `/home`. On this cluster these may refer to the same directory via symlinks/mounts, but **verify with `realpath` before relying on either**.

The actual operator run established successful report generation, not adoption or application of any hypothetical humidity repair. The complete Stage10 audit-summary counts for interpolation could **not** be inferred from the top-level stdout and need the Stage11 read of the actual `audit_summary.json` and ten generated CSV files.

## Actual report rows from operator stdout

| Site | Source abnormal low-derived-RH rows exported |
|---|---:|
| US-UiD | 0 |
| US-UMB | 23 |
| US-UMd | 15 |
| US-Var | 62 |
| US-Vcm | 509 |
| US-Vcp | 629 |
| US-WCr | 88 |
| US-Whs | 1 |
| US-Wjs | 401 |
| US-Wkg | 22 |
| **Total** | **1,750** |

The immutable raw source file SHA256 was verified by the operator's run; ten standalone `*_low_RH_review.csv` plus `audit_summary.json` were generated in the requested reports-only directory. All row-level records remain on IRIDIS6 (not committed to the GitHub repository).

### Most useful next read-only inspection

[Stage11 review-ledger validator and priority selector](../scripts/stage11/11_audit_stage10_review_ledgers_readonly.py) reads the **existing** report CSV/JSON only and prints:

- per-site source-QC distribution for Stage10 event rows;
- negative vs nonnegative RH;
- whether `UNAPPROVED_MATH_FEASIBLE` interpolation exists, with strict source-anchor time and interpolation arithmetic checks;
- `ERA_INTERNAL_NONPHYSICAL` or `ERA_E_WITH_TOWER_T_NOT_FEASIBLE` counts;
- leading QC0/0 negative-RH original measurement exceptions (26 US-WCr and 1 US-Vcm based on Stage09);
- priority examples for manual review.

`Stage11` never changes the generated Stage10 reports, source CSVs, model forcing, clock labels or Slurm queues.

## Execution safeguard

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage11"
  COMMIT="61c5dbf996ebf209f707bfddfd021d521d2d0336"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/11_audit_stage10_review_ledgers_readonly.py"
  REPORTS="$HOME/ameriflux_batch05_stage10/review_20261025T180413Z_682688"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage11/11_audit_stage10_review_ledgers_readonly.py" \
    -o "$SCRIPT"
  # Validate blob SHA against value displayed in README/terminal command.
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  test -f "$REPORTS/audit_summary.json"
  python3 -B "$SCRIPT" --report-dir "$REPORTS" \
    2>&1 | tee "$BASE/stage11.log"
)
```

Stage11 run remains **pending**. Its scientific output must never be treated as automatic approval to replace the original FLUXNET humidity forcing.
