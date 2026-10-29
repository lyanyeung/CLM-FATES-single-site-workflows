#!/usr/bin/env bash
set -euo pipefail
D="$HOME/ameriflux_batch05_stage77_Var"
mkdir -p "$D"
SCRIPT="$D/stage77_US_Var.py"
COMMIT="e17752ee7a13eff84b50bcf663cda81bf19e1127"
BLOB="1ab86535a0805ea16cda67b2beb856d8cea6f87a"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage77/77_US_Var_37_events_62HH_original_context_READONLY.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$BLOB"
echo "STAGE77 US-Var SOURCE EXACT SHA VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
D63="$HOME/ameriflux_batch05_stage63/exact10_site_204_crosswalk_20261029T025331Z_1904396"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
python3 -B "$SCRIPT" --stage63-dir "$D63" --stage27-dir "$D27" 2>&1 | tee "$D/stage77_US_Var_original_37_events.log"
echo "STAGE77_VAR_LOG=$D/stage77_US_Var_original_37_events.log"
echo "STAGE77 ORIGINAL/APPROVED_323/PRODUCTION DATM/CIME/SLURM UNCHANGED"
