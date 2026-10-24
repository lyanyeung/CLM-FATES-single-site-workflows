# Stage57 — Manual review of 63 original EC TA_F values >8 °C from CDS ERA5

Date: 2026-10-24. Source: operator-verified Stage56 PASS.
**Stage57 has not yet been run on IRIDIS6; no individual anomaly has
yet been assigned a scientific conclusion.**

## Exact scope, established by Stage56

| Site | Original tower TA_F vs independent ERA5 T2m >8 °C |
| --- | ---: |
| US-EML | 27 |
| US-GLE | 6 |
| US-ICt | 30 |
| **Total** | **63** |

The Stage56 source-check and audit passed with the following parent report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage56_original_T_if_ERA5_delta_le8C_20261024T104425Z_044e977d`

Out of the other Stage11 events, original tower TA_F was kept in
3,904 cases within ±8 °C, and all 917 US-Ho1 records remain separate
time-alignment HOLD (provisional UTC). This stage examines only the
63 tower-ERA5 disagreement cases, none from Ho1. The separately
staged 444 Stage53 humidity events remain untouched.

## What the read-only evidence actually tests

The [Stage57 script](../scripts/stage57/57_manual_review_63_tower_T_vs_ERA5.py):

1. Verifies Stage56's SHA256 of all output tables, Stage56 input SHA256
   for its Stage55, Stage19, Stage11 and Stage54 parents, and the
   **original same-release EC primary CSV SHA256** from Stage11's
   exact Stage08 input inventory.
2. For each of 63 events, verifies exact **original tower TA_F and
   TA_F_QC** at its real local start timestamp, alongside the
   independently downloaded CDS ERA5 T2m value.
3. Retrieves EC tower samples at ±30, ±60 and ±120 minutes,
   including their original QC, closest valid QC0 tower sample
   within ±6 hours, local same-day temperature median, and
   checks whether discrepancy is positive/negative.
4. Marks an **isolated tower spike candidate** only if both adjacent
   half-hour temperatures are finite and their source QC is 0/1,
   the target deviates from their mean by >5 °C and the two
   neighboring temperatures differ by ≤3 °C. This is a diagnostic
   flag, **not** a correction or proof that a particular observation
   is bad.
5. Identifies groups of problem records separated by no more than
   two hours on the same tower, plus per-site median/max discrepancy,
   sign, QC composition and neighbor-continuity diagnostics.

This is a *manual scientific review* preparation. The current
operator summary does **not** supply the 63 original tower
temperatures, ERA5 temperatures, dates or neighboring tower samples.
Therefore no defensible case-by-case verdict can be reached from
Stage56's aggregate counts alone. Share the Stage57 event table
or upload its generated CSV for individual review of the 63 cases.
Do not infer that a >8 °C difference always means EC instrumentation
failure: weather fronts, terrain/resolution and real tower heat
conditions can contribute.

All 63 rows remain HOLD: **no automatic ERA5 temperature overwrite**.
The 3,904 original-TA-within-8°C Stage56 decisions, Stage53 444
separate RH candidates, and Ho1 provisional UTC are unchanged.

## Pinned operator commands on IRIDIS6

Pinned script commit: `605dde255b3fc38d507e9a497aea8da0190627b0`
Git blob SHA-1: `4786751fb3500b3481a2505ccd778d2a4208a118`

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage57/57_manual_review_63_tower_T_vs_ERA5.py"
  COMMIT="605dde255b3fc38d507e9a497aea8da0190627b0"
  EXPECTED="4786751fb3500b3481a2505ccd778d2a4208a118"
  mkdir -p "$BASE/scripts/stage57"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage57/57_manual_review_63_tower_T_vs_ERA5.py" \
    -o "$TMP"
  ACTUAL="$(git hash-object "$TMP")"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $ACTUAL"
  test "$ACTUAL" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_Stage57_check_$(date -u +%Y%m%dT%H%M%SZ).log"
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_Stage57_audit_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected audit completion:
`STAGE57 AUDIT PASS | exact 63 >8C tower-vs-ERA5 manual-review evidence`.

The isolated directory will include
`63_original_tower_temperature_source_neighbor_evidence.csv`,
`three_site_temperature_anomaly_groups.csv`,
`three_site_review_summary.csv` and a SHA256 provenance
manifest. An interrupted run retains INCOMPLETE_DO_NOT_USE.

To make actual individual determinations, inspect/return the full
63-row table and source-neighbor context; the code intentionally
does not invent scientific verdicts or change EC source/forcing.
