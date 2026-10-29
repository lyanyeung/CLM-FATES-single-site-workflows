#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage93_Wkg"
mkdir -p "$BASE"
SCRIPT="$BASE/stage93_Wkg_20250910.py"
COMMIT="049b7a4865e0e1df6d36d147ba1839b4744c1c96"
BLOB="defc924070f58e2e9f981bbe22c2e105f96fa770"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage93/93_US_Wkg_20250910_T_VPD_native_QC0_local_physics_READONLY.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$BLOB"
echo "STAGE93 GITHUB ORIGINAL SOURCE SHA VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
D84="$HOME/ameriflux_batch05_stage84_Vcp/Vcp_direct582_20261029T062857Z_2211876"
D92="$HOME/ameriflux_batch05_stage92_T/seven_T_extended_source_20261029T071754Z_3310751"
OUT="$BASE/Wkg_Sep2025_T_QC0_context_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" --stage84 "$D84" --stage92 "$D92" --out "$OUT" 2>&1 | tee "$BASE/stage93_Wkg.log"
echo "STAGE93_REPORTS=$OUT"
echo "STAGE93 READONLY SOURCE SCIENCE | ORIGINAL/QC/PRIOR1675/DATM/CIME/SLURM UNCHANGED"
