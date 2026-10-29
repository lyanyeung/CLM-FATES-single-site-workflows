#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage94_Wkg"
mkdir -p "$BASE"
SCRIPT="$BASE/stage94_wkg_original_source.py"
COMMIT="616efeaa9b82c63e8a4c1a31d5add9e5e56592b2"
BLOB="c5f6ff700556d2fafeeef3dd55abcd58e24d2dd1"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage94/94_US_Wkg_20250910_original_source_alternative_fields_precip_provenance_READONLY.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$BLOB"
echo "STAGE94 ORIGINAL GITHUB SOURCE SHA VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
D84="$HOME/ameriflux_batch05_stage84_Vcp/Vcp_direct582_20261029T062857Z_2211876"
D93="$HOME/ameriflux_batch05_stage93_Wkg/Wkg_Sep2025_T_QC0_context_20261029T072420Z_3346776"
OUT="$BASE/original_Wkg_source_companions_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" --stage84 "$D84" --stage93 "$D93" --out "$OUT" 2>&1 | tee "$BASE/stage94_Wkg.log"
echo "STAGE94_REPORTS=$OUT"
echo "STAGE94 READONLY | ORIGINAL/QC/PRIOR1675/DATM/CIME/SLURM UNCHANGED"
