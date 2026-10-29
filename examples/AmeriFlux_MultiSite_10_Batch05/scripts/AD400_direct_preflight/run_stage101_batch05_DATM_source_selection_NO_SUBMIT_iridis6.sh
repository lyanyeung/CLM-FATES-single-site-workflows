#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_directAD400_DATM_source_selection"
mkdir -p "$BASE"
SCRIPT="$BASE/101_batch05_DATM_source_selection.py"
COMMIT="53b5d6ecef634dbe505632e7dd7bf977753bbb7e"
BLOB="f93d24723038af9dfaa17a4ab89871f1d650155c"
PATH_IN_REPO="examples/AmeriFlux_MultiSite_10_Batch05/scripts/AD400_direct_preflight/101_batch05_prepare_DATM_source_selection_and_holds_READONLY.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$PATH_IN_REPO" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$BLOB"
echo "STAGE101 SOURCE GITHUB SHA VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
D84="$HOME/ameriflux_batch05_stage84_Vcp/Vcp_direct582_20261029T062857Z_2211876"
D89="$HOME/ameriflux_batch05_stage89_Whs/Whs_51_T_plus_four_VPD_20261029T070333Z_2322432"
D90="$HOME/ameriflux_batch05_stage90/ten_site_remaining_risks_20261029T070834Z_2339016"
D97="$HOME/ameriflux_batch05_stage97/original_56_holds_five_science_groups_20261029T075507Z_3517881"
D98="$HOME/ameriflux_batch05_directAD400_preflight/readiness_20261029T080621Z_3578563"
D100="$HOME/ameriflux_batch05_directAD400_PFT_soil_surface/pft_soil_surface_scan_20261029T083355Z_3740913"
OUT="$BASE/sparse_DATM_source_selection_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" \
  --stage84 "$D84" --stage89 "$D89" --stage90 "$D90" \
  --stage97 "$D97" --stage98 "$D98" --stage100 "$D100" \
  --out "$OUT" 2>&1 | tee "$BASE/stage101_DATM_selection.log"
echo "STAGE101_REPORTS=$OUT"
echo "STAGE101 SOURCE RECIPE/SCIENCE RISK MATRIX ONLY: NO PRODUCTION DATM, NO SURFACE/CIME, NO SLURM"
