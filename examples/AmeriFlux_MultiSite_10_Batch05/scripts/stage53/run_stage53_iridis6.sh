#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage53"
mkdir -p "$BASE"
PY_COMMIT="e65e5713cf984171608e85acf12419ffee97d36e"
PY_BLOB="6bbcfd7d38832b164d0a31256abc8dbd6ee2a5f0"
REL="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage53/53_show_three_events_before_during_after_tower_vs_source_ERA_readonly.py"
SCRIPT="$BASE/stage53.py"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$PY_COMMIT/$REL" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "$PY_BLOB"
echo "STAGE53 SOURCE VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test

D51="$HOME/ameriflux_batch05_stage51/three_hypotheses_49_offset_holds_20261028T161922Z_2062563"
D52="$HOME/ameriflux_batch05_stage52/original_three_event_humidity_provenance_20261028T162951Z_2137755"
test -d "$D51" && test -d "$D52"
OUT="$BASE/actual_tower_and_source_ERA_three_events_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" --stage51-dir "$D51" --stage52-dir "$D52" --out "$OUT" \
  2>&1 | tee "$BASE/stage53.log"
echo "STAGE53_REPORTS=$OUT"
echo "STAGE53 READONLY ORIGINAL/PREVIOUS APPROVALS/DATM/SLURM/CLAUDE108 UNCHANGED"
