# Batch02 Stage86 operator PASS → Stage87 build existing FIVE numerically ready site DATM NetCDF technical preview

Date: 26 October 2026. Operator Stage86 read-only result verified Ho1 year-2000 Stage85 manual source decision exact SHA (17,294 native QC0 TA_F untouched, 1,068 humidity-only VPD remaps, 32 original VPD retained, 274 QC!=0 HOLD), historical Stage07 incomplete trial, ONE incomplete Stage08 root `raw_RH_sensitivity_20261022T013805Z_aadaffee` holding only five previously complete Stage07 candidate site references, and ZERO Stage09 Post-v5 runs. Explicit numerical ten-site selection counts: **0 completed Stage08**, **0 completed Post-v5**. The other nine stations have NOT been formally cleared. Historical five Stage07 numeric sources are BZS, CMW, Ha1, Ho2, Ho3; historical five original Stage07 humidity blockers are EML, GLE, Ho1, ICh, ICt.

## Speed path without inventing scientific decisions

New [Stage87](../scripts/stage87/87_build_five_verified_Stage07_DATM_noleap_technical_preview.py) **immediately builds source-pinned annual NetCDF4_CLASSIC technical previews for exactly the five already numerically complete Stage07 sites**. Source forcing CSV checksums are checked against Stage07 original saved `output_sha256.json`; original Stage07 incomplete marker and source site status records are untouched. Coordinates come only from existing Batch02 site 2000 point surfaces; native HH 30min for BZS, CMW, Ho2, Ho3 and HR 60min for Ha1. Half-hourly NOLEAP years have 17,520 source rows/year and Ha1 hourly NOLEAP 8,760. Expected annual file counts by original site years: BZS 15, CMW 21, Ha1 35, Ho2 27, Ho3 19 = **117 annual NetCDF technical preview files** plus 5 stream XML *templates* that are NOT ACTIVATED. All nine CLM1PT-style variables TBOT, QBOT, SHUM, RH, PSRF, FSDS, FLDS, WIND, PRECTmms are stored, plus one point grid lat/lon and original SHA/preview-only metadata. Original RH derives from preserved Stage07 T/QBOT/pressure for a consistency check. No user science decisions are inferred or overwritten by merely generating these files.

**IMPORTANT distinction:** Existing Stage07 candidate files may contain automated QC0 source edits and QCv5 adjustments requiring human signoff; Stage87 confirms their original NUMERICAL candidate status and generates a *technical-preview* NetCDF, **NOT** validated/approved site meteorology. Stage09 Post-v5, site QC0 and RH edits, local time/NOLEAP centering, sensor height ZBOT, domain/site footprint/PFT, actual DATM-vs-CDEPS stream format and smoke test remain pending. Existing Stage85 Ho1 2000 candidate does NOT belong to those five sources, is not modified, and MUST be integrated into a separate Ho1 complete-year selection later. Existing Stage08 5-site partial outputs are neither ignored as evidence nor treated as complete.

Original source script commit `e3c7ab2e57e2796ad88187f4ef7b7ea1164abc3b`, Git blob `4f188cd785f31812bd8ec002b05dafda09e884b2`. Structural text lint/Git hash checked; real IRIDIS6 Python self-test and source checks still need operator run.

## One-paste IRIDIS6 execution

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage87/87_build_five_verified_Stage07_DATM_noleap_technical_preview.py"
  COMMIT="e3c7ab2e57e2796ad88187f4ef7b7ea1164abc3b"
  EXPECTED="4f188cd785f31812bd8ec002b05dafda09e884b2"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage87/87_build_five_verified_Stage07_DATM_noleap_technical_preview.py" \
    -o "$TMP"
  echo "EXPECTED $EXPECTED"
  echo "ACTUAL   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  test ! -L "$SCRIPT"
  if test -e "$SCRIPT"; then
    test -f "$SCRIPT"
    test "$(git hash-object "$SCRIPT")" = "$EXPECTED"
  else
    cp "$TMP" "$SCRIPT"
  fi
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --build \
    2>&1 | tee "$HOME/Batch02_Stage87_five_site_DATM_technical_preview.log"
)
```

Expected on-cluster summary only if the build actually succeeds: `STAGE87 BUILD PASS | FIVE SITES 5 NC ANNUAL FILES 117 STREAM TEMPLATES 5`, report `reports/stage87_five_site_DATM_NetCDF_technical_preview_<UTC>_<ID>`. A new `INCOMPLETE_DO_NOT_USE` marker stays if any file fails. Files are isolated/new. No source DATM/CIME/Slurm modifications.

## After Stage87

The remaining **five** EML, GLE, Ho1, ICh, ICt need actual complete-year numerical trial forcing. Do not run old Stage10 and claim this incorporates Stage85; the Ho1 2000 annual humidity-only candidate must be overlaid into full Ho1 release by exact native timestamps, with the other 274 non-QC0 records retained as *non-measured provenance*. For other unresolved humidity rows, source-validated independent shadow candidates must be compared and an explicit candidate policy recorded; do not infer that a numerical adjustment is a measured observation. Once ten complete site-year series can pass actual readback/Post-v5 and provenance checks, create remaining Batch02 technical NC and merge manifest references without overwriting the existing Stage87 files. Scientific production approval requires separate source decisions and case/site metadata gates.
