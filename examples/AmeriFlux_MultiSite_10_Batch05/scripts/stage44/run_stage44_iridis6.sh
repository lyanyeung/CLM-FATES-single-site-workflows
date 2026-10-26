#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage44"
mkdir -p "$BASE"
COMMIT="416f4f94e2ca4e9aad401dc185eb98bcf8c62a1e"
BLOB="f24f8cbf2a04ca8ba764ccff14784ec3a69db855"
FILE="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage44/44_all_1574_p2p3_physics_and_event_prioritization_readonly.py"
PY="$BASE/stage44.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$FILE" -o "$PY"
test "$(git hash-object "$PY")" = "$BLOB"
echo "STAGE44 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test

D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
D43="$HOME/ameriflux_batch05_stage43/numeric_15_source_trial_20261026T191656Z_2924371"
for d in "$D27" "$D24" "$D43"; do
  test -d "$d" || { echo "MISSING_ORIGINAL_REPORT $d" >&2; exit 1; }
done

OUT="$BASE/whole_batch_physics_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" \
  --stage27-dir "$D27" \
  --stage24-dir "$D24" \
  --stage43-dir "$D43" \
  --out "$OUT" 2>&1 | tee "$BASE/stage44.log"

echo "STAGE44_REPORTS=$OUT"
cat "$OUT/STAGE44_TEN_SITE_BULK_TRIAGE_AND_NEXT_ACTION.md"
echo "STAGE44 ORIGINAL/DATM/CIME/SLURM UNCHANGED"
