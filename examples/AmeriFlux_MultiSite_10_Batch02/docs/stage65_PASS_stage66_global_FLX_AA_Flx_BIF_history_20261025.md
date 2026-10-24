# Stage65 operator PASS; Stage66 global FLUXNET BIF, UTC_OFFSET history and provenance

Operator Stage65 (pinned Git blob 6cef393ba8666e3ae9454dbb2b64822c3e8b76b7) passed self-test, read-only source check and full audit. Its exact report is:
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage65_metadata_xlsx_BIF_and_69T_triage_20261024T233546Z_05d7f38e

Stage65 found 13 candidate source/metadata files per US-BZS and US-Ho1 and 10 candidate BIF objects per site, but **zero** same-release original FLUXNET primary/BIF proof. It classified 69 original temperature science HOLDs into 37 warm-context, 18 neighbor/source QC, and 14 suspected sensor bound/flatline cases. Stage64's 9,389 existing water-humidity candidates remain intact and NOT approved for DATM.

IMPORTANT SOURCE CORRECTION: FLUXNET2015 metadata may be distributed globally in FLX_AA-Flx_BIF_HH_YYYYMMDD.xlsx and similar AA-Flx resolution-specific XLSX BIF files, not just AMF_US-xxx_BIF.xlsx inside the station ZIP. FLUXNET2015 metadata may include multiple UTC_OFFSET entries with UTC_OFFSET_DATE_START, so one undated or modern offset must never be applied blanket to 1996-2023.

Official references:
https://www.nature.com/articles/s41597-020-0534-3
https://ameriflux.lbl.gov/data/aboutdata/badm-data-product/
https://ameriflux.lbl.gov/data/badm/badm-standards/
https://fluxnet.org/data/fluxnet2015-dataset/

Stage66 implementation:
scripts/stage66/66_find_global_FLX_AA_Flx_BIF_and_UTC_offset_history.py

It checks the operator-pinned Stage65 report, Stage64 prior and primary-source SHA, then searches bounded original-package folders for global AA-Flx/AA-Net and site-specific CSV/XLSX BIFs, and BIF members of matching ZIP packages. It groups UTC_OFFSET, UTC_OFFSET_DATE_START and UTC_OFFSET_DATE_END strictly by SITE_ID plus GROUP_ID, flags multiple periods, and reports distinct offset values. It checks exact original source CSV SHA within a candidate archive separately from simply finding a global BIF. Unproven source linkage stays HOLD. All operations are read-only except a new isolated SHA manifest and audit report.

Stage66 Git commit: c9cf074f8eb905e57f3496c0f9e314c6035d58b7
Stage66 Git blob SHA: 7d2b87abd6ed3c69586064d361870d56c5325ae7

## IRIDIS6 one-paste command

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage66/66_find_global_FLX_AA_Flx_BIF_and_UTC_offset_history.py"
  COMMIT="c9cf074f8eb905e57f3496c0f9e314c6035d58b7"
  EXPECTED="7d2b87abd6ed3c69586064d361870d56c5325ae7"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage66/66_find_global_FLX_AA_Flx_BIF_and_UTC_offset_history.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage66_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Completion marker:
STAGE66 AUDIT PASS | global FLUXNET BIF and period-aware UTC metadata inventoried

Stage66 has been committed but not yet executed on IRIDIS6. US-Ho1 original 16,788 hard-source events and US-BZS 86 retain their no-UTC-assumption HOLD. No modification to original EC, 9,389 candidate ledger, DATM, model or Slurm jobs.
