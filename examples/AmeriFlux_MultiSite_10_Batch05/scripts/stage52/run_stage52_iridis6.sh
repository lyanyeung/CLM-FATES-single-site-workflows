#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage52"
mkdir -p "$BASE"
PY_COMMIT="b700ec732dc92ea33e277b91a8084ddf80b09d37"
PY_BLOB="54596f1bdd15baecd7c9f3bb61178fab4d928053"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage52/52_three_event_raw_humidity_provenance_and_49_source_holds_readonly.py"
PY="$BASE/stage52.py"
curl -fLsS --retry 3 \
 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT/$REL" -o "$PY"
test "$(git hash-object "$PY")" = "$PY_BLOB"
echo "STAGE52 SOURCE VERIFIED"
python3 -B -m py_compile "$PY"
python3 -B "$PY" --self-test
D51="$HOME/ameriflux_batch05_stage51/three_hypotheses_49_offset_holds_20261028T161922Z_2062563"
ROOT="/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"
test -d "$D51" || { echo "STAGE52 MISSING ORIGINAL STAGE51 REPORT $D51" >&2; exit 1; }
test -d "$ROOT" || { echo "STAGE52 MISSING ORIGINAL SOURCE DATA ROOT $ROOT" >&2; exit 1; }
OUT="$BASE/original_three_event_humidity_provenance_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$PY" --stage51-dir "$D51" --sites-root "$ROOT" --out "$OUT" \
  2>&1 | tee "$BASE/stage52.log"
echo "STAGE52_REPORTS=$OUT"
cat "$OUT/STAGE52_THREE_ORIGINAL_HUMIDITY_SOURCE_AUDIT_AND_NEXT_EVIDENCE.md"
echo "STAGE52 READ-ONLY | 166 APPROVED/46 P1 HOLD/10 RH PLATEAU/1574 P2P3/DATM/SLURM/CLAUDE108 UNCHANGED"
