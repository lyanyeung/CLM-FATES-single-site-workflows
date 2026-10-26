# Stage87 operator PASS → Stage88 exact decision dossier (26 October 2026)

**Actual operator evidence** (2026-10-26 00:39 UTC):
- Stage87 source blob `4f62ba03f52b41b98d7b6db3e89af2bf10bee8a1` checksum matched; self-test and Stage07/source/surface checks passed.
- Existing five Stage07 numeric candidates converted into **117 yearly NOLEAP NetCDF previews** (US-BZS 15, US-CMW 21, US-Ha1 35 at native 60 min, US-Ho2 27, US-Ho3 19). Five stream templates are **NOT ACTIVATED**.
- Operator report is `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage87_five_site_DATM_NetCDF_technical_preview_20261026T003934Z_30692f63`.
- No raw sources, active forcing, CIME or Slurm jobs were modified.
- This does **not** establish science approval, completed five remaining sites, Post-v5, ZBOT or historical time interpretation.

## Remaining manual science gates, not to be falsely auto-approved

1. Exactly **274 original US-Ho1 2000 TA_F_QC != 0** temperatures have still not been approved as genuinely measured; the existing gap-filled `TA_F` may be usable with honest provenance, but this is a distinct quality-policy decision. **Do not re-open the previously approved 17,294 QC0 T, 1,068 humidity-only adjustments or 32 reviewed original VPD values.**
2. Exactly **24 Stage07 original QC0 changed-variable records** across five sites (BZS 1, CMW 2, Ha1 2, Ho2 19, Ho3 0); review each original/ERA/final/reason. These are *changed-variable records*, not necessarily 24 different timestamps.
3. Original Stage07 humidity failures at EML 1,327; GLE 295; Ho1 937; ICh 169; ICt 2,176 (**4,904 historical Stage07 failure rows**). The later Stage08/11 exact cohort of **4,884** is different; do not conflate. Five blocked sites need numerically complete source candidate construction and Post-v5 before their technical NC can be built. The later Stage64/Stage74 science-shadow counts do not mean these have been released.
4. Time and interval/UTC calibration, local clock provenance, per-site ZBOT and tower footprint/PFT remain production case gates; do not set arbitrary values or claim model spinup can start.

## Stage88: one-copy, three checks (IRIDIS6, `clm_fates_env`)

This read-only-science audit constructs **two small separate review CSVs and one JSON manifest**, all in a new `reports/stage88_*` folder. It SHA-checks the source ledgers and Stage85 manual decision; checks 117-file Stage87 *manifest* (not a bytewise reread of all 117 NetCDFs); provides original-nearest QC0 tower T on both sides of each Ho1 QC!=0 row. Neighbors are context **only**, not permission to interpolate or replace. No raw/source/current forcing/DATM/NetCDF/CIME/Slurm changes.

Script: [Stage88 priority decision dossier](../scripts/stage88/88_collect_exact_manual_decisions_readonly.py).

Pinned commit: `c7c8165a195a373c0a1482e81c3f1dfd0d11efd2`
Git blob: `11657ca7294247c101be9125c7902f0f12c817f1`

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage88/88_collect_exact_manual_decisions_readonly.py"
  COMMIT="c7c8165a195a373c0a1482e81c3f1dfd0d11efd2"
  BLOB="11657ca7294247c101be9125c7902f0f12c817f1"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage88/88_collect_exact_manual_decisions_readonly.py" -o "$TMP"
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
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit 2>&1 | tee "$HOME/Batch02_Stage88_exact_manual_review.log"
)
```

Expected successful log ends `STAGE88 AUDIT PASS | 24 QC0 source edits, 274 Ho1 nonQC0 T source HOLD; NO SOURCE/MODEL WRITES` and `REPORT ...`.

## Immediate next decision after Stage88

Inspect only `24_original_QC0_modified_variable_records_REVIEW.csv` and `274_Ho1_2000_nonQC0_temperature_neighbor_context_REVIEW.csv`. Decide once at the **source-QC policy** level whether quality-coded gapfilled `TA_F` may be used for nonQC0 Ho1 rows with clearly retained QC provenance; any unsafe transitions or invalid values remain individual holds. Do **not** extrapolate this policy to other sites/years unless the operator explicitly chooses. QC0 edits can be independently triaged from original/ERA/final values, rather than a blanket approval based on a Stage87 numeric PASS.

Stage88 creates no complete 10-site selected forcing; the remaining 5-site integrated source selection, approved Ho1 Stage85 year-2000 overlay, independent Post-v5, and production DATM remain separate future stages.
