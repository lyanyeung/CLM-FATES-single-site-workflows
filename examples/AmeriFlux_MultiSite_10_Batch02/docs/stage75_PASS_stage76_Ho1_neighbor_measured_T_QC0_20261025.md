# Stage75 operator PASS — Stage76 native Ho1/Ho2/Ho3 QC0 tower temperature comparison

Date: 25 October 2026. The operator ran Stage75 fixed/pinned Git blob `723cb02fb331cc8b5150442043e04b045a44af10` on IRIDIS6. SHA confirmed, syntax/self-test, read-only check and full isolated `AUDIT PASS`. Original inputs, independently downloaded CDS, DATM forcing, CIME and Slurm were unchanged.

Stage75 exact report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage75_1675_original_TA_QC_and_T_vs_CDS_science_triage_20261025T091912Z_27b0e442`.

## Stage75 science summary

Independent CDS ERA5 has been fully source/payload/calendar/grid SHA verified for **26/26** relevant Ho1+BZS gridyears. The original hard-physics VPD cohort **16,874** is partitioned into **15,199** numerical-only independent-RH source humidity shadow candidates, **998** non-measured original TA_F QC1/QC2 events, and **677** original measured QC0 tower temperatures whose difference from independently retrieved ERA5 2m T exceeds 8°C. They remain distinct, untouched science-HOLD statuses; none were applied to forcing.

| Category | US-Ho1 | US-BZS | All |
| --- | ---: | ---: | ---: |
| Original TA_F QC1 | 167 | 2 | **169** |
| Original TA_F QC2 | 829 | 0 | **829** |
| Native TA_F QC0 versus CDS >8 °C | 623 | 54 | **677** |
| **Temperature science-HOLD** | **1,619** | **56** | **1,675** |

Original US-Ho1 QC0 versus independent CDS >8 °C counts are strongly concentrated in **2000: 505**, **1999: 67**, **2008: 36**, with smaller source episodes in other years. Ho1 2000 accounts for **74.6% of the whole 677-row cross-site difference HOLD** and **81.1% of Ho1's 623 measured T-difference HOLDs**. Longest Ho1 2000 QC0-vs-ERA anomaly in the operator's Stage75 sample spans 70 contiguous half-hours (35 hours), 2000-03-06 04:00 to 2000-03-07 14:30 (tower local native timestamp); median tower minus ERA5 T = −12.90 °C for that episode.

Source T cross-context status in Stage75:

- US-Ho1 measured QC0 delta >8°C: **161** where source FLUXNET `TA_ERA` lies within 3°C of independent CDS T, plus **462** where three related T fields disagree or lack a conclusive alignment. `TA_ERA` and modern CDS reanalysis must **NOT** be interpreted as two independent tower observations.
- US-BZS measured QC0 delta >8°C: **54** where two ERA-related processed sources agree but measured tower T is colder. May indicate local microclimate, tower sensor, product processing or timing; cannot decide without independent ground data.
- US-Ho1 996 QC1/QC2 plus US-BZS 2 QC1 require processed/modeled original temperature provenance, not an arbitrary temperature replacement.

## Stage76 native cross-tower evidence — not yet run on IRIDIS6

[Stage76 source](../scripts/stage76/76_Ho1_Ho2_Ho3_original_QC0_temperature_cross_tower_audit.py) verifies the complete Stage75 SHA-pinned report and original Stage49/61 20-file inventory. It reads the original US-Ho2 / US-Ho3 FULLSET/FLUXMET half-hour primary tower T and T-QC columns, with original **source-file SHA256**, only for the exact 1,619 native US-Ho1 temperature-HOLD times, without interpolating or importing the reanalysis-derived VPD_ERA/TA_ERA as independent evidence.

Ho2/Ho3 records are considered supporting comparisons ONLY if `TA` is a finite, physically plausible **native QC0 measured** value and their native `TIMESTAMP_START` exactly equals the Ho1 source `TIMESTAMP_START`. Each native Ho2/Ho3 record is paired with the Ho1 tower T and independent CDS ERA5 T. Exploratory 3°C proximity yields one of: supporting original Ho1 T; supporting CDS ERA5 T; conflicting neighboring towers; neither; no QC0 neighboring observation. These are **evidence categories** and none releases even one HOLD. Original native time convention parity (historical offset), relative tower sensor height and canopy microclimates are NOT verified and remain science gates.

**US-BZS must not be compared to Maine's Ho2/Ho3** and remains in a distinct 56-event `BZS_HOLD_NO_RELEVANT_NEARBY_TOWER_SOURCE` group for a future local independent meteorological-station / instrument source assessment.

Stage76 source commit: `b892ad95c80ed940e6f5313af74b5789032bb8c9`.
Stage76 exact Git blob: `bf4694181f2dd4625143a7397089aea2c2993832`.

### One-paste on IRIDIS6 (read-only originals, isolated new report)

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage76/76_Ho1_Ho2_Ho3_original_QC0_temperature_cross_tower_audit.py"
  COMMIT="b892ad95c80ed940e6f5313af74b5789032bb8c9"
  EXPECTED="bf4694181f2dd4625143a7397089aea2c2993832"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage76/76_Ho1_Ho2_Ho3_original_QC0_temperature_cross_tower_audit.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage76.log"
)
```

Expected when full source passes: `STAGE76 AUDIT PASS | source-pinned Ho2/Ho3 original measured QC0 T comparisons for 1675 original holds`.

This script has passed source-code structural and Git blob checks but **not Python py_compile or IRIDIS6 source check on the cluster**. User-side command runs py_compile before the checks. If original Ho2/Ho3 source QC fields are absent, Stage76 explicitly returns a no-comparator status rather than guessing. All original, independent CDS, Stage64–75 reports, DATM/NetCDF forcing, CIME and Slurm remain unchanged. Official BIF historical UTC effectiveness still requires validation before any shadow humidity candidate can enter forcing.
