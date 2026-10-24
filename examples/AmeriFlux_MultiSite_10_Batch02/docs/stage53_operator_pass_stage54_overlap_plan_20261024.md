# AmeriFlux Batch02 — Stage53 operator PASS; Stage54 exact-overlap gate

Date: 2026-10-24. Based on operator-provided IRIDIS6 stdout, not an
uploaded copy of the Stage53 CSV or log.

## Stage53 completed on IRIDIS6

Exact pinned GitHub SHA verified by operator:
`824f18c7868fa451274b1e359906ece2fd84a199`.
Execution passed syntax check, self-test, Stage53 --check and --stage.

`STAGE53 STAGING PASS | all 444 same-ERA5 RH replacements with paired VPD/QBOT`

Isolated report on IRIDIS6:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage53_444_ERA5_RH_only_staging_20261024T100652Z_543ef3f1`

Exact:
- 444 original RH=0 or RH>100 records (39 zero, 405 >100).
- Same independent CDS ERA5 time-series dataset for replacement water RH,
  10 source ERA5 grid-years already SHA-verified.
- VPD and QBOT computed in one coherent water-basis formulation using
  the independent ERA5 RH and unchanged EC tower temperature and pressure.
- 27 US-ICt TA QC1/2 cases (14 QC1; 13 QC2) retain original T
  and separate T-QC review. 405 RH>100 cases retain phase/QC review.
- The Stage53 patch is a user-selected sparse **staging** ledger, not
  proof of model-ready forcing. The original Stage08/11 4,884 HOLD
  cohort remains independent. **0 actual data/forcing/DATM/model writes**.

## Stage54: exact identity crosswalk before any data integration

[Stage54 Python](../scripts/stage54/54_crosswalk_444_ERA5_RH_stage11_4884_HOLD.py)
compares exact original tower site and *local start timestamp*:
Stage53 `(site, timestamp_start)` and Stage11
`(site, time)`, normalizing formatting but not shifting
timezones. Prior Stage19 explicitly used Stage11's `site,time` column
identities and described the 4,884 Stage11 rows as scientific HOLD.

Stage54 checks upstream Stage53/Stage11 manifests and SHA256, enforces
the exact 444 and 4,884 source populations and flags any same-site/time
intersection. Its isolated reports contain:
- exact Stage53/Stage11 overlapping original site/timestamps,
- Stage53 unique after subtracting overlap,
- Stage11 HOLD unique after subtracting overlap,
- site-level overlap counts.

It **does not** choose between revisions, remove any scientific HOLD,
apply fixes, recompute other events, or change model inputs. If overlap
exists, that exact site/time requires an explicit single authoritative
science and variable-wise decision, not an automatic double patch.
If overlap is zero, the Stage11 4,884 remain unresolved separately.

### Pinned IRIDIS6 command

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage54/54_crosswalk_444_ERA5_RH_stage11_4884_HOLD.py"
  COMMIT="20a3d90a443e364b68ab48cc58c0367d6f92ac22"
  EXPECTED="f74d004bf9277c0583309387ea1352703da76db7"
  mkdir -p "$BASE/scripts/stage54"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage54/54_crosswalk_444_ERA5_RH_stage11_4884_HOLD.py" \
    -o "$TMP"
  ACTUAL="$(git hash-object "$TMP")"
  printf 'EXPECTED: %s\nACTUAL:   %s\n' "$EXPECTED" "$ACTUAL"
  test "$ACTUAL" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_Stage54_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Only `STAGE54 AUDIT PASS | exact 444-vs-4884 crosswalk`
shows the Stage54 report was successfully produced and source
invariants were rechecked. Stage54 has NOT yet been run on live IRIDIS6.
