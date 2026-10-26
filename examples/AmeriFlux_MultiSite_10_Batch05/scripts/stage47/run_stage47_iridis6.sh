#!/usr/bin/env bash
set -euo pipefail

BASE="$HOME/ameriflux_batch05_stage47"
mkdir -p "$BASE"
PY_COMMIT="1299df67353f4f14a986ac50079f3700d0d4d084"
PY_BLOB="59e06137a4cf84425b33b4526e412d81325454b5"
PY="$BASE/stage47.py"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage47/47_assistant_trackA_neighbor_qc_and_42_numeric_science_evidence_readonly.py"
curl -fLsS --retry 3 \
  "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT/$REL" \
  -o "$PY"
test "$(git hash-object "$PY")" = "$PY_BLOB"
echo "STAGE47 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test

D46="$HOME/ameriflux_batch05_stage46/parallel_science_lanes_20261026T194948Z_3184652"
D45="$HOME/ameriflux_batch05_stage45/all_native_event_edges_20261026T193713Z_3134330"
D44="$HOME/ameriflux_batch05_stage44/whole_batch_physics_20261026T192416Z_3084937"
D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
for d in "$D46" "$D45" "$D44" "$D27"; do
  test -d "$d" || { echo "MISSING ORIGINAL STAGE47 SOURCE $d" >&2; exit 1; }
done
OUT="$BASE/assistant_trackA_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" \
  --stage46-dir "$D46" \
  --stage45-dir "$D45" \
  --stage44-dir "$D44" \
  --stage27-dir "$D27" \
  --out "$OUT" 2>&1 | tee "$BASE/stage47.log"

echo "STAGE47_REPORTS=$OUT"
cat "$OUT/STAGE47_ASSISTANT_SOURCE_NEIGHBOR_AND_42_PILOT_SCIENCE.md"
echo "STAGE47 RESEARCH-ONLY NO SOURCE, DATM OR SLURM WRITES"
