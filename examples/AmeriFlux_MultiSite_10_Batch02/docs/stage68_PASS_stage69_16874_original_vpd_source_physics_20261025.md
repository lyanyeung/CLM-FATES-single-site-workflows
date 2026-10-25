# Batch02 Stage68 PASS — Stage69 original VPD / water saturation science diagnosis

Operator IRIDIS6 Stage68 (25 October 2026) passed Python self-test, source check and final AUDIT, based on two independently uploaded official site BIF source workbooks.

Stage68 original report: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage68_official_uploaded_BIF_Ho1_BZS_UTC_shadow_20261025T075428Z_11c5b183`.

### Stage68 findings

- US-Ho1 nominal published BIF `UTC_OFFSET=-5` and **16,788** original hard source humidity records were mapped one-to-one from tower-local to *provisional* UTC.
- US-BZS nominal BIF `UTC_OFFSET=-9` and **86** original hard records were mapped likewise.
- The nominal UTC conversions use `UTC = tower_local - UTC_OFFSET`; midnight/year-rollover records are preserved, and no historical-period applicability was claimed.
- Original site BIF workbooks on the IRIDIS6 cluster were **not reverified there byte-for-byte** (`original_XLSX_reverified_locally=False`). Their SHA256 values were independently checked in the ChatGPT attachment container, and the extracted JSON is pinned in GitHub.
- Neither official site BIF includes `UTC_OFFSET_DATE_START`, which means long historical validity is not formally proven by these 2026-file snapshots alone.
- US-Ho1 original Stage48 `ACTUAL_VAPOR_NONPOSITIVE=16,788`, `RH_INFERRED_LT0=16,788`, `HARD_WITH_TA_QC0=15,792`, `RH_FIELD_MISSING_RECORDS=16,764`.
- US-BZS original `ACTUAL_VAPOR_NONPOSITIVE=86`, `RH_INFERRED_LT0=86`, `HARD_WITH_TA_QC0=84`, `RH_FIELD_MISSING_RECORDS=86`.
- All **16,874** events remain scientific HARD HOLD. Stage64 **9,389** independent numeric humidity proposals remain unchanged, *not applied to model forcing*.

### Why all inferred RH becomes negative

Stage48 original rule uses `es_water(T) [hPa] = 6.112 * exp(17.67*T/(T+243.5))` for degrees C, `e_actual = es_water(T) - VPD_original`, and `RH_derived = 100*e_actual/es_water`. Therefore any native VPD exceeding the water-basis saturation pressure for the **original** native T will give nonpositive implied actual vapour and negative implied RH. Original tower air temperature QC0 is not evidence that the original VPD is physically correct; also the `RH_derived` result is not an independent measurement. Investigate VPD provenance, native VPD original QC, temperature source, source units and bad segments rather than presuming an ERA5 T replacement.

### Stage69 scope

[Stage69 original VPD water saturation physical diagnosis](../scripts/stage69/69_original_Ho1_BZS_vpd_saturation_failure_diagnosis.py) verifies Stage64/68 source-report SHA256, reproduces exact 16,874 `es_water(T) - VPD <= 0` cases, cross-tabulates original T and VPD QC, bins `VPD/es_water`, inventories year-level and contiguous half-hour source anomalies, and explicitly tests VPD divided by 10 or 100 as **unit-sensitivity hypotheses only**. This does not authorize VPD changes or forced corrections. Stage69 is local source analysis and does not require another ERA5 download.

Stage69 commit `6622fd79d8ae8ead0450268c4c0f035b39f2b3e4`, Git blob `5edf6ca49a1bba1c6292b80322d7e306e1b08549`.

## Pinned IRIDIS6 command

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage69/69_original_Ho1_BZS_vpd_saturation_failure_diagnosis.py"
  COMMIT="6622fd79d8ae8ead0450268c4c0f035b39f2b3e4"
  EXPECTED="5edf6ca49a1bba1c6292b80322d7e306e1b08549"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage69/69_original_Ho1_BZS_vpd_saturation_failure_diagnosis.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage69_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected `STAGE69 AUDIT PASS | 16874 original negative vapor events physically source-explained`.

Stage69 is committed and statically checked; it has not been executed yet on IRIDIS6. No original observations, Stage64/68 reports, independent CDS, NetCDF forcing, DATM, CIME or Slurm are modified.
