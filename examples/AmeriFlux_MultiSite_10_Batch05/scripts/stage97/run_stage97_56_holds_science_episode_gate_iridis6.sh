#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage97"
mkdir -p "$BASE"
SCRIPT="$BASE/stage97_56_holds.py"
COMMIT="b66016267299d77edd9f40f14ea44f42d34b0989"
BLOB="f3238273ba681692f96a0f00da763007c39e3f80"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage97/97_batch05_56_holds_five_science_groups_episode_decision_matrix_READONLY.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$BLOB"
echo "STAGE97 GITHUB ORIGINAL SCIENCE AUDIT SHA VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test
D96="$HOME/ameriflux_batch05_stage96_P1_platform/three_sites_P1_46_platform10_20261029T075010Z_3490715"
OUT="$BASE/original_56_holds_five_science_groups_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" --stage96 "$D96" --out "$OUT" 2>&1 | tee "$BASE/stage97_56_holds.log"
echo "STAGE97_REPORTS=$OUT"
echo "STAGE97 READONLY | ORIGINAL/QC/56_HOLDS/MAIN1675/STAGE89/DATM/CIME/SLURM UNCHANGED"
