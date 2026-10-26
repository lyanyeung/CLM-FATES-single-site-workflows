# Stage89 PASS → Stage90 targeted source decisions (26 October 2026)

## Actual Stage89 evidence (operator output)

Stage89 verified the original Stage88 24 QC0 changed-variable records and 274 Ho1 2000 native non-QC0 temperature records. In detail:

- BZS 1 temperature: `2012-10-12 16:00`, original `21.56°C`, companion ERA `-0.653°C`, isolated-neighbor interpolation `-0.8765°C`.
- CMW 1 VPD (`16.235 → 15.9587 hPa`, ERA `18.33 hPa`) and 1 temperature (`7.523 → 28.055°C`, ERA `27.19°C`).
- Ha1 **2 original QC0 VPD changes** (`14.404 → 10.461 hPa` vs ERA `1.671`; `15.379 → 8.638 hPa` vs ERA `2.068`) on 2003-05-29 07:00 and 08:00. These two need actual native hourly temperature/VPD neighbors before approval; numerical validity alone does not support a humidity-source change.
- Ho2 19 edits: 7 December 2016 winter VPD near-dry-to-wet candidates and 12 longwave radiation isolated-spike interpolations over 2021–2025; these appear directionally reasonable but the original neighboring series still needs exact source context, especially any QC0 change.
- Ho1 274 non-QC0 original source temperatures split into exactly **2 episodes**: 2000-04-19 09:30 to 2000-04-20 11:00 (52 HH, original source QC1+QC2, |original T-ERA| max 4.52°C and original QC0 tower-T on both sides); and 2000-12-27 09:00 through 2000-12-31 23:30 (222 HH, |T-TA_ERA| max 18.84°C, preceding QC0 -15.1°C, no following QC0 *within 2000*).
- **Important:** Absence of a following QC0 inside the year-2000 Stage85 output does **not** prove absence of the first 2001 QC0 in the original multi-year FULLSET product. Inspect the exact cross-year source before any blanket decision about the 222 December hours.

## Scientific recommendations pending Stage90 source context

Provisional: Original-QC0 isolated short interpolation candidates for BZS/CMW and Ho2 may be accepted **only** if original exact native neighboring records support them and the operator approves; the 2 Ha1 VPD changes should be held until companion temperature and VPD series is shown. Ho1 April 52 gap-filled native source T can be retained with explicit non-measured QC provenance as an initial candidate; do not relabel them as QC0 measurements. Hold the Ho1 December 222 until original source temperature difference episodes, raw 2001 first observations and quality flags are known. Previously approved original **17,294 Ho1 QC0 T**, **1,068 humidity remaps** and **32 VPD retained** must stay unchanged.

## Stage90 executable (IRIDIS6; entirely diagnostic)

[Stage90 full source](../scripts/stage90/90_focus_Ha1_VPD_and_Ho1_Dec_boundary_readonly.py).
Pinned Git commit: `777b36f0b6505d13beff29b5576c8c6f0b3398e4`.
Pinned Git blob: `2d071eb218a41633ae0774139fa2de7bf8d428bf`.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage90/90_focus_Ha1_VPD_and_Ho1_Dec_boundary_readonly.py"
  COMMIT="777b36f0b6505d13beff29b5576c8c6f0b3398e4"
  BLOB="2d071eb218a41633ae0774139fa2de7bf8d428bf"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage90/90_focus_Ha1_VPD_and_Ho1_Dec_boundary_readonly.py" -o "$TMP"
  test "$(git hash-object "$TMP")" = "$BLOB"
  test ! -L "$SCRIPT"
  if test -e "$SCRIPT"; then
    test -f "$SCRIPT"
    test "$(git hash-object "$SCRIPT")" = "$BLOB"
  else
    cp "$TMP" "$SCRIPT"
  fi
  "$PY" -B -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --audit 2>&1 | tee "$HOME/Batch02_Stage90_targeted_review.log"
)
```

Reads SHA-verified original Stage88 and Stage07 primary raw sources. Prints full 24 QC0 original/ERA/candidate values with exact original neighboring values; expanded 5-hour-native-row source context for the **two Ha1 VPD** cases; Ho1 December >8°C and >12°C discrepancy periods and 20 largest differences; actual first original 2001 native source observation and first following 2001 QC0 measured temperature (if present). Outputs source-evidence CSV/JSON only under a NEW isolated `reports/stage90_*` directory, never model input. The existing Stage87 technical NetCDFs are not changed.

**Next:** ask for only the operator's missing science choices after examining the Stage90 evidence; do not re-audit approved Stage85 QC0 tower T/humidity. Five originally humidity-blocked Batch02 sites (EML,GLE,Ho1,ICh,ICt) still need a separate complete forcing source integration and Post-v5; a mere Stage90 diagnostic does not complete them.
