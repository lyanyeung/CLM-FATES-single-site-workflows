# AmeriFlux Batch02: Stage54 zero-overlap PASS and Stage55 4,884 existing ERA5 triage

Date: 24 October 2026. The Stage54 numbers below are transcribed
from operator-provided IRIDIS6 output. The original IRIDIS6 Stage54 files
have not been uploaded to this GitHub repository.

## Verified Stage54 result

Exact Stage54 crosswalk PASSED in IRIDIS6:

- Stage53 original RH=0 or >100 user-selected external CDS ERA5 patch:
  **444 timestamps** (US-Ha1 398, US-Ho2 7, US-ICh 9, US-ICt 30).
- Stage11 original cold/physics humidity cohort: **4,884 HOLD timestamps**
  (US-EML 1,327, US-GLE 295, US-Ho1 917, US-ICh 169, US-ICt 2,176).
- Intersection of exact original EC **(site, local timestamp): 0**.
- Distinct combined audited cohort size: **5,328** original site/timestamps;
  this is not the full Stage48 26,332 source hard-physics union.
- No Stage53/Stage11 patch, original data, DATM or model input modified.

IRIDIS6 Stage54 proof:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage54_444_vs_4884_timestamp_crosswalk_20261024T101940Z_bac3a939`

## Why Stage55 uses Stage19 instead of requesting more ERA5

Stage19 previously established a design for **all 4,884 Stage11 targets**
over **five sites, 42 site-years**, from verified independent CDS ERA5
grid-year time-series (5 Stage15 and 34 Stage18 physical receipts).
It calculates the one-product t2m/d2m/sp water RH and corresponding
VPD/QBOT using retained EC site T/PA and flags numeric invalidity,
source QC, temperature provenance, below-zero water vs ice saturation,
neighbour evidence and **US-Ho1 UTC−5 provisional time offset**.
Its Stage19 output is diagnostic and still marked **science HOLD**.

[Stage55 script](../scripts/stage55/55_triage_existing_stage19_4884_ERA5_science_HOLD.py)
reuses a matching completed Stage19 report if one exists on IRIDIS6
under `~/AmeriFlux_Batch02_stage19_full_dewpoint_audit_*/`.
It validates the Stage11 and Stage54 original identity and SHA256,
rechecks the 39 existing independent external CDS ERA5 receipt/NetCDF
SHA256 files by default, and classifies all 4,884 into conservative,
exclusive *review* routes. The route is a prioritization, **not**
permission to replace the original temperature, forcing or model data.

Source QC/phase/temperature gates overlap; a single exclusive route
cannot erase the other flags. The CSV preserves each independent flag
as an additional column. All 4,884 remain HOLD until an explicit
scientific release. US-Ho1 still requires independently verified
time/height provenance before using ERA5 as a tower forcing.

### Stage55 IRIDIS6 commands

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage55/55_triage_existing_stage19_4884_ERA5_science_HOLD.py"
  COMMIT="32704e8a19c0769d3455176c102d8d2745741678"
  EXPECTED="fed667b3f26bd36e4be01252a30a353c9d12d049"
  mkdir -p "$BASE/scripts/stage55"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage55/55_triage_existing_stage19_4884_ERA5_science_HOLD.py" \
    -o "$TMP"
  ACTUAL="$(git hash-object "$TMP")"
  printf 'EXPECTED: %s\nACTUAL:   %s\n' "$EXPECTED" "$ACTUAL"
  test "$ACTUAL" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_Stage55_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Stage55 does not call CDS or download ERA5. If the matching Stage19
report is missing, the Stage55 source check stops with an explicit error.
To regenerate only Stage19's **local diagnostic report from existing
independently downloaded CDS ERA5 files**, run the original
[Stage19 Python code](../scripts/stage19/19_audit_all_era5_dewpoint_targets.py)
with `--check` and then `--write-report`. Those modes
do not submit CDS retrievals and do not modify existing Stage19/Stage11
data or model forcing. The earlier Stage15/18 verified files must still
exist and pass their original SHA256 checks.

New Stage55 outputs on pass:
- `4884_existing_ERA5_candidates_science_routes.csv`
- `five_site_4884_review_summary.csv`
- `science_route_counts.csv`
- `science_triage_manifest.json`.

Only `STAGE55 AUDIT PASS` confirms a completed isolated
science report. Stage55 has been committed to GitHub but **has not yet
passed syntax/self-test against the user's IRIDIS6 environment**.
