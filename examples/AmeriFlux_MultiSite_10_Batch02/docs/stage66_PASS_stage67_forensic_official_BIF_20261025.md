# AmeriFlux Batch02 — Stage66 PASS, 64-file BADM evidence diagnosis (Stage67)

Live Stage66 operator result (25 Oct 2026):

- Stage66 Git blob 7d2b87abd6ed3c69586064d361870d56c5325ae7 verified, Python syntax/self-test/check/audit passed.
- Searched 11 root directories and 64 file candidates; 26 previously seen Stage65 files.
- US-Ho1: 0 UTC_OFFSET records; 0 exact original-release archive proofs.
- US-BZS: 0 UTC_OFFSET records; 0 exact original-release archive proofs.
- Report: /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage66_AA_Flx_global_BIF_UTC_history_20261025T054649Z_2a6cae25
- Stage64 remains 9,389 unique independent CDS ERA5 humidity candidate values, unchanged and not applied to DATM; US-Ho1 16,788 hard-original-event time HOLD, US-BZS 86, and 69 temperature-source HOLD.

Scientific correction: AmeriFlux/FLUXNET BIF metadata can be downloaded independently from the associated flux files. Requiring BIF and the original primary CSV to be in the same ZIP is overly restrictive as the sole allowable provenance evidence. Separately published BADM may be valid if actual data-product identity, publisher, release date and the relevant UTC_OFFSET period are independently corroborated. None of the current local evidence yet meets that broader test.

Official references:
https://ameriflux.lbl.gov/data/aboutdata/badm-data-product/
https://ameriflux.lbl.gov/resource/badm-for-sites-with-fluxnet-data-product/
https://fluxnet.org/data/fluxnet2015-dataset/

Stage67 (read-only): scripts/stage67/67_forensic_64_BIF_sources_and_official_import.py

Stage67 reads the SHA-pinned Stage66 result, prints each BIF-capable file's parsed row count and parse errors, and explains whether there really are no rows for US-Ho1 or US-BZS or the parser is missing/invalidating metadata. It also detects standalone official BIF files that the operator may already have in ~/AmeriFlux_Batch02_official_BIF (only reads files). It groups site UTC_OFFSET records and UTC_OFFSET_DATE_START independently and labels external publisher verification as still unproven. It does not require same-ZIP evidence to accept a BIF as a metadata candidate; it does not promote candidates to validated UTC time mapping or modify forcing.

To acquire official BIF when unavailable locally, log in to AmeriFlux Download Data and select BADM Only / AA-Flx_BIF for AmeriFlux FLUXNET sites, or a site-specific BIF. Place downloaded, unchanged XLSX/CSV in ~/AmeriFlux_Batch02_official_BIF. Downloading may require AmeriFlux account authentication and license acceptance; no credentials are embedded in scripts. A BIF's filename/date must not be mistaken for proof that an offset applies over all source years.

Stage67 pinned GitHub commit: 05c3465cded98b0ecb1183e4c511746a784eb955
Stage67 pinned Git blob: 36c9d2f5c2381e8cd140a8ed54ab04a0f8688514

## One-paste IRIDIS6

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage67/67_forensic_64_BIF_sources_and_official_import.py"
  COMMIT="05c3465cded98b0ecb1183e4c511746a784eb955"
  EXPECTED="36c9d2f5c2381e8cd140a8ed54ab04a0f8688514"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage67/67_forensic_64_BIF_sources_and_official_import.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage67_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected: STAGE67 AUDIT PASS | source BIF parse vs missing provenance classified.
No raw, Stage64, NetCDF, DATM, CIME or Slurm changes.
Stage67 has been committed and structurally checked, but not run on IRIDIS6.
