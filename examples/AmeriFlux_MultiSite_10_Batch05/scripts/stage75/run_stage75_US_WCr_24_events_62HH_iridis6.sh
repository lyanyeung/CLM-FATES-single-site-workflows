#!/usr/bin/env bash
set -euo pipefail
D="$HOME/ameriflux_batch05_stage75_WCr"
mkdir -p "$D"
SCRIPT="$D/stage75_WCr.py"
COMMIT="c69db84be73d9de798499873fd27d76389ae969d"
BLOB="dc95f270810244c43fa511c26f06960841a7ee8f"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage75/75_US_WCr_24_event_62HH_native_before_after_READONLY.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$BLOB"
echo "STAGE75 SOURCE SHA VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
D63="$HOME/ameriflux_batch05_stage63/exact10_site_204_crosswalk_20261029T025331Z_1904396"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
python3 -B "$SCRIPT" --stage63-dir "$D63" --stage27-dir "$D27" 2>&1 | tee "$D/stage75_WCr_all_24_events.log"
echo "STAGE75 SOURCE_AUDIT_LOG=$D/stage75_WCr_all_24_events.log"
echo "STAGE75 READONLY - NEXT DIRECT NEGATIVE RH ACTION AFTER SOURCE VERIFICATION"
