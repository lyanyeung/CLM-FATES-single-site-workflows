# Batch05 Stage36 PASS — Stage37 original-vs-trial VPD jumps before escalating candidate repairs

## Stage36 actually executed on IRIDIS6 (2026-10-26)

```text
SOURCE VERIFIED
STAGE36 SELF-TEST PASS | 251 exact trial cohort, raw ZIP boundary QC, 0 source/forcing writes
STAGE36 SUCCESS | 251 isolated research-only candidate HH; original source ZIP SHA verified; 502 native ±30min comparisons
STAGE36 TRIAL_SITES {"US-Vcp": 251}
STAGE36 EPISODES 65 SCREEN {"BOUNDARY_OR_UNAPPROVED_NEIGHBOR_REVIEW": 65}
STAGE36 ORIGINAL_QC0_VPD_PROTECTED 0
STAGE36 EXTERNAL_BOUNDARY_GT2_HPA 94 GT4 21
STAGE36_REPORTS=/home/ly3n24/ameriflux_batch05_stage36/isolated_251_trial_20261026T163233Z_909478
```

This scientifically blocks blind application of all 251 candidate native VPD changes to the original source or DATM: **every one of the 65 original P2/P3 episodes has flagged native boundary or unresolved neighbor metadata**. The 94 edges >2 hPa and 21 edges >4 hPa are **hypothetical VPD jumps after substituting the source-ERA-RH-derived research trial**. They do **NOT** necessarily represent jumps *created* by the repair — an original source VPD jump may already be even larger.

All 251 are from **US-Vcp**, and NONE is original QC0 measured source VPD. Do not interpret absence of QC0 as science authorization. Preserve source QC2 provenance and differentiate processed-source ERA vs independently requested *grid-reanalysis* ERA5-Land from an actual field humidity measurement.

### Nonfatal Stage36 SyntaxWarning fixed in GitHub

Python emitted six `SyntaxWarning: invalid escape sequence '\\`'` from backslash-escaped Markdown backticks in the Stage36 report prose (lines 399–401). They do NOT affect any Stage36 value or file; **no Stage36 rerun needed**. The backslash escape issue was corrected in GitHub commit `d75b7e60709de36b06a82836a9e061fca082e89f`, new source blob SHA `5f1830bafe79268231fcdb75e305f6fb612f17e6`. Prior Stage36 results remain valid and reproducible using the original pinned source blob.

## Stage37: actual original VPD vs hypothetical trial VPD at SAME native edge

[Stage37 read-only original-vs-trial jump attribution and maximal same-episode contiguous segments](../scripts/stage37/37_before_after_native_boundary_causality_and_contiguous_segments_readonly.py).

Pinned Stage37 final source commit `d1d8d5494876fee273e870933dcdf3a7466fa6dc`, Git blob SHA `0526cac58a46f61fc0a0ee99c1e21711377067fb`.

The script reads only the **existing verified Stage36 251 candidate CSV, 502 source-ZIP boundary audit CSV, and 65 original Stage27-event summary CSV** plus **Stage35 429 candidate original source dataset** for consistent source values and input hash provenance. **No new download or source ZIP extraction.**

For every REAL external edge (exclude a directly contiguous neighbor that already belongs to the same isolated 251-row trial, and mark across-original-episode adjacency separately):
- `original absolute VPD jump`: original source candidate VPD compared to the **same adjacent native VPD**, using an already user-approved Stage24 value only when that is the existing neighbor selection;
- `trial absolute VPD jump`: proposed source-ERA-RH VPD compared to that **same unchanged neighbor**;
- `delta absolute jump`: trial minus original (positive worsens, negative improves);
- new threshold crossovers of **>2 hPa / >4 hPa**, distinguishing *old jump still present* vs *new jump created*;
- changes in jump size **>0.5 hPa** up/down (heuristic scientific screens, not sensor accuracy standards);
- original neighbor QC0 vs QC2/other, source implied RH under 10%/unphysical, *another still-unapproved original P2/P3*, P1 manual HOLD, or RH saturation-platform diagnostics.
- the largest contiguous 30-min candidate-native segments **within each original source episode** and whether only part of the original anomalous episode is selected. Adjacent trial segments belonging to different original source episodes are explicitly retained as a cross-event science review, not silently treated as a true external source edge.

Inputs and strict Stage35–Stage36 hashes guard that exactly **251 native HH, 502 Stage36 source edges and 65 original episodes** are consistent, that original Stage35 source lane 251 is unchanged and **Stage36's 94/21 trial-edge counts are reproduced**.

Outputs (new research folder, read-only):
- `stage37_EXTERNAL_NATIVE_BOUNDARIES_ORIGINAL_VS_TRIAL_CAUSALITY.csv`
- `stage37_251_NATIVE_CONTIGUOUS_TRIAL_SEGMENT_GATES.csv`
- `stage37_65_EPISODES_BEFORE_AFTER_PRIORITIES.csv`
- `stage37_manifest.json`
- `STAGE37_BEFORE_AFTER_EDGE_AND_SEGMENT_DECISION.md`

### IRIDIS6: one-call run Stage37

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage37"
  COMMIT="d1d8d5494876fee273e870933dcdf3a7466fa6dc"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/37_before_after_native_boundary_causality_and_contiguous_segments_readonly.py"

  D36="$HOME/ameriflux_batch05_stage36/isolated_251_trial_20261026T163233Z_909478"
  D35="$HOME/ameriflux_batch05_stage35/science_VPD_trial_20261026T132821Z_715715"

  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage37/37_before_after_native_boundary_causality_and_contiguous_segments_readonly.py" \
    -o "$SCRIPT"

  test "$(git hash-object "$SCRIPT")" = "0526cac58a46f61fc0a0ee99c1e21711377067fb"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test

  OUT="$BASE/boundary_before_after_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage36-dir "$D36" --stage35-dir "$D35" \
    --out "$OUT" 2>&1 | tee "$BASE/stage37.log"

  echo "STAGE37_REPORTS=$OUT"
  cat "$OUT/STAGE37_BEFORE_AFTER_EDGE_AND_SEGMENT_DECISION.md"
)
```

### How to interpret the results

- Original >4hPa → trial 1hPa: **large pre-existing problem appears numerically reduced**, but original adjacent source QC2/P2P3 sensor provenance can still be wrong. It is NOT an automatic approval.
- Original 0.5hPa → trial 5hPa: **candidate creates a new large discontinuity**. Prioritize event-level method change, full-episode candidate coverage and original timestamps before any versioned repair.
- Original 5hPa → trial 6hPa: both jumps large; possible worsened old problem. Need source/neighbor evidence.
- Trial touching original QC2 or another unapproved source P2P3: do not pretend this is a trustworthy QC0 original neighbor.
- Even a trial reducing all original jumps still requires investigator decision and **separate isolated Post-v5 QC**, rather than mutating original approved 166 or forcing.

**Stage37 source code on GitHub, IRIDIS6 operator run pending.** No new science approval or source/forcing/model modifications made. Original 46 P1 manually held, 1574 P2/P3 science-unapproved, 10 saturation platforms, and 166 prior-approved versioned RH/VPD overlay stay untouched. BIF original timezone date-end remains missing and native-time mapping is provisional.
