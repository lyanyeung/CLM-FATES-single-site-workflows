#!/usr/bin/env bash
set -euo pipefail

BASE="$HOME/ameriflux_batch05_stage46"
mkdir -p "$BASE"
PY_COMMIT="d34f04afe1de1afe2037b6b6b35452b3be00fe78"
PY_BLOB="f97ad6c63b99e48b1a6a9ccc4ffcef8e7642a663"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage46/46_split_483_events_between_science_tracks_readonly.py"
PY="$BASE/stage46.py"

curl -fLsS --retry 3 \
  "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT/$REL" \
  -o "$PY"
test "$(git hash-object "$PY")" = "$PY_BLOB"
echo "STAGE46 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test

D45="$HOME/ameriflux_batch05_stage45/all_native_event_edges_20261026T193713Z_3134330"
D43="$HOME/ameriflux_batch05_stage43/numeric_15_source_trial_20261026T191656Z_2924371"
for d in "$D45" "$D43"; do
  test -d "$d" || { echo "MISSING_ORIGINAL_SOURCE $d" >&2; exit 1; }
done
OUT="$BASE/parallel_science_lanes_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" \
  --stage45-dir "$D45" \
  --stage43-dir "$D43" \
  --out "$OUT" 2>&1 | tee "$BASE/stage46.log"

echo "STAGE46_REPORTS=$OUT"
cat "$OUT/STAGE46_PARALLEL_ASSISTANT_CLAUDE_SCIENCE_HANDOFF.md"
echo "STAGE46 ORIGINAL/P1HOLD46/APPROVED166/P2P3_1574/DATM/SLURM UNCHANGED"
