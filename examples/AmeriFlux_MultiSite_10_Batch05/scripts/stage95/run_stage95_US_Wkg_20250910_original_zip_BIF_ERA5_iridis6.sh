#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage95_Wkg"
mkdir -p "$BASE"
SCRIPT="$BASE/stage95_wkg_archive.py"
COMMIT="ae956bd6cf28e10471a953387b76c0c269398084"
BLOB="b4e79dc92abb05283650a6337dfe3cfd4c04104e"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage95/95_US_Wkg_20250910_archive_BIFVARINFO_ERA5_lineage_READONLY.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$BLOB"
echo "STAGE95 ORIGINAL GITHUB CODE SHA VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
D84="$HOME/ameriflux_batch05_stage84_Vcp/Vcp_direct582_20261029T062857Z_2211876"
D94="$HOME/ameriflux_batch05_stage94_Wkg/original_Wkg_source_companions_20261029T072933Z_2405803"
OUT="$BASE/Wkg_archive_lineage_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" --stage84 "$D84" --stage94 "$D94" --out "$OUT" 2>&1 | tee "$BASE/stage95_wkg.log"
echo "STAGE95_REPORTS=$OUT"
echo "STAGE95 READONLY SOURCE SCIENCE | ORIGINAL/QC/PRIOR1675/DATM/CIME/SLURM UNCHANGED"
