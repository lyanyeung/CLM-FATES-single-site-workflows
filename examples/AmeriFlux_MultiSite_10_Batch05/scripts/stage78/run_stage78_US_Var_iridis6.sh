#!/usr/bin/env bash
set -euo pipefail
D="$HOME/ameriflux_batch05_stage78_Var"
mkdir -p "$D"
P="$D/stage78.py"
C="1050db563e5c7aa16c3d580bdbe164e4f6ef6b9e"
R="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage78/78_US_Var_55_negative_RH_direct_approved_378.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$C/$R" -o "$P"
test "$(git hash-object "$P")" = "9b2a40d7d44392997128be1482f7bfd016d02368"
python3 -B -m py_compile "$P"
python3 -B "$P" --self-test
python3 -B "$P" --stage27 "$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604" --stage63 "$HOME/ameriflux_batch05_stage63/exact10_site_204_crosswalk_20261029T025331Z_1904396" --stage76 "$HOME/ameriflux_batch05_stage76_WCr/WCr_direct61_Tplus3_20261029T043428Z_2423219" --out "$D/Var_378_$(date -u +%Y%m%dT%H%M%SZ)_$$" 2>&1 | tee "$D/stage78_run.log"
