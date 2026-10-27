#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage49"
mkdir -p "$BASE"
PY_COMMIT="98c6df7f1c8d608abdd16e43713c1643289f62a6"
PY_BLOB="12587f0a351c388cbab59f3b83779b67585ce8b2"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage49/49_assistant_70_candidate_reference_and_52_new_jump_science_audit.py"
PY="$BASE/stage49.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT/$REL" -o "$PY"
test "$(git hash-object "$PY")" = "$PY_BLOB"
echo "STAGE49 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test
D48="$HOME/ameriflux_batch05_stage48/assistant_122_full_event_trial_20261027T141646Z_3720216"
D47="$HOME/ameriflux_batch05_stage47/assistant_trackA_20261026T195942Z_3223947"
D45="$HOME/ameriflux_batch05_stage45/all_native_event_edges_20261026T193713Z_3134330"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
for d in "$D48" "$D47" "$D45" "$D27"; do
  test -d "$d" || { echo "STAGE49 MISSING ORIGINAL REPORT $d" >&2; exit 1; }
done
OUT="$BASE/assistant_70_reference_52_jump_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" \
  --stage48-dir "$D48" \
  --stage47-dir "$D47" \
  --stage45-dir "$D45" \
  --stage27-dir "$D27" \
  --out "$OUT" 2>&1 | tee "$BASE/stage49.log"
echo "STAGE49_REPORTS=$OUT"
cat "$OUT/STAGE49_ASSISTANT_70_SOURCE_EVIDENCE_52_NEW_JUMP_REVIEW.md"
echo "STAGE49 READ-ONLY COMPLETE; 108 CLAUDE EVENTS UNTOUCHED; NO FORCING WRITES"
