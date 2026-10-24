# Stage51 completed; Stage52 targeted RH>100 phase and US-ICt T-QC audit

Date: 24 October 2026.
Source: operator-provided IRIDIS6 terminal output (log text pasted in
conversation; actual CSVs and raw log not uploaded to GitHub).

## Confirmed operator Stage51 result

`STAGE51 AUDIT PASS | exact 444 source-pinned ERA5 RH candidates`

Source Stage51 audit report (on IRIDIS6):
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage51_444_RH_and_27_joint_T_review_20261024T094847Z_081665b1`.

| Site | Original RH=0, retained site T candidate | Original RH>100, phase review | Original RH=0, joint T/RH review |
| --- | ---: | ---: | ---: |
| US-Ha1 | 2 | 396 | 0 |
| US-Ho2 | 7 | 0 | 0 |
| US-ICh | 0 | 9 | 0 |
| US-ICt | 3 | 0 | 27 |
| **Total** | **12** | **405** | **27** |

The **27** joint-T/RH reviews are all **US-ICt**:
- 27 have original T QC **not 0**. The exact mix of QC1/QC2/QC3/
  missing is NOT provided by the Stage51 operator stdout and must
  be inspected in the report before assigning a scientific route.
- **0** have |original site T - independent CDS ERA5 T2m| >8 Celsius;
  this is an 8 C screening threshold, NOT independent proof that every
  original site T is valid. Do **not** claim all 27 need their original T
  overwritten, nor approve T retention based only on this comparison.
- Stage51 calculated 27 **joint ERA5 T/RH/VPD/QBOT sensitivity alternatives**,
  still with all science approvals false.

The **405** RH>100 phase reviews are 396 US-Ha1 and 9 US-ICh. The
operator result does NOT state whether these are tiny >100 overshoots
or severe outliers, or whether they occur below the freezing point.
The water- versus ice-reference saturation and instrument QC ambiguity
must be examined before using their ERA5 replacement candidates.

Stage50's 444 ERA5 RH replacement candidates exist as a timestamp-exact
separate sparse ledger, and **ALL 10 required independent CDS ERA5
grid-years are verified**. Forcing/raw sources unchanged. The separate
Stage08 4,884 HOLD and Stage07 24 original QC0 edits are still unresolved.

## Stage52 new targeted source-pinned audit

[Read-only Stage52 Python script](../scripts/stage52/52_review_original_RH_supersaturation_and_ICt_temperature_QC.py)

Stage52:
- Verifies the exact Stage50 and Stage51 receipt/report SHA256 and their
  original four-site/444-row timestamp populations.
- For 405 RH>100 records, classifies the exceedance severity
  (100–100.5%, 100.5–101%, 101–105%, >105%), original tower T<0 C,
  original VPD near zero, date/year and ERA5-vs-raw RH.
- For 27 US-ICt joint-T reviews, reports exact original T QC codes,
  original T minus ERA5 T2m, timestamp, the Stage51 ERA5 joint T/RH/VPD/
  QBOT alternative, and any pressure sensitivity.
- Rechecks that 27 exact timestamp keys match the 444-row Stage50 ledger.
- Writes a fresh four-site summary, 405-row severity report,
  27-row detailed temperature-QC report, and full 444-row review queue,
  each SHA256-pinned in a separate audit manifest.

This stage is evidence collection only: all 444 original RH targets are
ERA5 candidates but 0 are approved for DATM until the science decision.
No existing original or prior-stage file is changed. A failed/incomplete
report directory retains an INCOMPLETE_DO_NOT_USE marker.

### IRIDIS6 run

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage52/52_review_original_RH_supersaturation_and_ICt_temperature_QC.py"
  mkdir -p "$BASE/scripts/stage52"
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/$REL/scripts/stage52/52_review_original_RH_supersaturation_and_ICt_temperature_QC.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = \
    "f39506e9c7b2393a14bcc1745e2018c671d81456"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_Stage52_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

If successful: `STAGE52 AUDIT PASS | 405 RH>100 phase cases / 27 US-ICt T-QC cases`.
Stage52 GitHub script syntax guard was corrected in commit ec98ae8a7122e04e73cc45e656b2dfaaeced7058 after an unmatched closing parenthesis was detected by the operator on first attempt. Stage52 still **has not passed live IRIDIS6 execution**. Its outputs
will determine whether raw RH>100 cases are tiny/below-freezing and
which non-QC0 US-ICt original temperatures demand a more explicit
joint replacement decision. Do not treat audit categories as approval.
