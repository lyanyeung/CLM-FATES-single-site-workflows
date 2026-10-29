#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_directAD400_preflight"
mkdir -p "$BASE"
SCRIPT="$BASE/stage98_direct_AD400_preflight.py"
COMMIT="5bf67b3f57e3854ca8d51e3ea7cc65ab35f19c21"
BLOB="32ca5b76b83b9c8155855c6228685c3ddd330a63"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/AD400_direct_preflight/98_batch05_ten_site_direct_AD400_science_and_case_preflight_READONLY.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$BLOB"
echo "STAGE98 DIRECT AD400 PRECHECK GITHUB SOURCE SHA VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
D84="$HOME/ameriflux_batch05_stage84_Vcp/Vcp_direct582_20261029T062857Z_2211876"
D86="$HOME/ameriflux_batch05_stage86/ten_site_final_QC_20261029T064013Z_2246464"
D89="$HOME/ameriflux_batch05_stage89_Whs/Whs_51_T_plus_four_VPD_20261029T070333Z_2322432"
D90="$HOME/ameriflux_batch05_stage90/ten_site_remaining_risks_20261029T070834Z_2339016"
D97="$HOME/ameriflux_batch05_stage97/original_56_holds_five_science_groups_20261029T075507Z_3517881"
OUT="$BASE/readiness_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" --stage84 "$D84" --stage86 "$D86" --stage89 "$D89" --stage90 "$D90" --stage97 "$D97" --out "$OUT" \
  2>&1 | tee "$BASE/stage98_direct_AD400_readiness.log"
echo "STAGE98_REPORTS=$OUT"
echo "STAGE98 NO AD5 TRIAL | NO ORIGINAL/QC/DATM/SURFACE/CIME/SLURM WRITES"
