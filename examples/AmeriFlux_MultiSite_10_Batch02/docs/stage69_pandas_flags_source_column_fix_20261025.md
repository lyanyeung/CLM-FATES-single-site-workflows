# Stage69 read-only original VPD source audit: pandas `.flags` fix

25 October 2026. IRIDIS6 downloaded the original Stage69 Git blob `5edf6ca49a1bba1c6292b80322d7e306e1b08549`, and `--self-test` passed, but `--check` failed early at the original hard source label filter.

Observed error:

```
AttributeError: 'Flags' object has no attribute 'astype'
  at load() when checking a.flags.astype(str)
```

Cause: pandas DataFrame has a reserved `.flags` attribute (a `Flags` object). The Stage49/68 CSV has a **column named `flags`**. Attribute dot access cannot safely select this column.

Fix in Git commit `cbddcd0e16005a0da96aa52c20fe301b86fd5706` (blob `a5c678d57b8691a7bd6b37c8241711b828054223`): use `a["flags"].fillna("").astype(str).str.contains("ACTUAL_VAPOR_NONPOSITIVE",regex=False).all()`. The self-test also explicitly verifies the column/attribute collision.

All other Stage69 pandas column lookups were reviewed for known reserved `flags` references. The source-ledger scientific thresholds and VPD/es(T) test were not changed.

## IRIDIS6 pinned command

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage69/69_original_Ho1_BZS_vpd_saturation_failure_diagnosis.py"
  COMMIT="cbddcd0e16005a0da96aa52c20fe301b86fd5706"
  EXPECTED="a5c678d57b8691a7bd6b37c8241711b828054223"
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
  "$PY" -B "$SCRIPT" --audit 2>&1 | tee "$HOME/Batch02_Stage69_fixed.log"
)
```

Expected: `STAGE69 AUDIT PASS | 16874 original negative vapor events physically source-explained`.

Stage69 audit has not yet passed in the provided IRIDIS6 output. This is a script-only correction, **not** an approval for the 16,874 source-HOLD humidity events or the unchanged 9,389 Stage64 water-humidity proposals. No original, CDS, DATM, NetCDF, CIME or SLURM writes occur.
