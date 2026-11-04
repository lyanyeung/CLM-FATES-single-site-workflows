#!/usr/bin/env bash
# Stage05BX: serial read-only IRIDIS6 batch for Stage05BW (approved D1/D2 and delegated C2/C3 shadow tables).
# Requires the JapanFlux2024 JP-Yms package uploaded beforehand (SHA-256 checked here). Also prints the existing
# Stage05BV 05BT offset rows at 540 and 600 min for the D8 review. No download, no source/forcing/case/Slurm change.
# Usage: bash 05bx_iridis_readonly_batch_05bw.sh <directory holding the hash-checked scripts>
set -euo pipefail
D="$1"; PY="${PY:-python3}"
ROOT=/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE
YMS="$ROOT/JP-Yms/forcing/packages/JapanFlux2024/A20241022-024_2.00_selected.zip"
BT="$HOME/japanflux_stage05bv/run_20261104T045402Z_1120583/05bt_lag/offset_sensitivity_17_groups_HOLD.tsv"
EXP_BW_FP=2365a73416b9908f0d092b5e18f54dd317d555b8e1609eb9093d8fc9c2b76f9d
BASE="$HOME/japanflux_stage05bx"
[ -L "$BASE" ] && { echo "STOP: $BASE is a symlink"; exit 1; }
mkdir -p "$BASE"; RUN="$BASE/run_$(date -u +%Y%m%dT%H%M%SZ)_$$"
[ -e "$RUN" ] && { echo "STOP: $RUN exists"; exit 1; }
mkdir "$RUN"; echo "STAGE05BX RUN $RUN"; "$PY" --version; hostname
echo "a112e8650592040b92698280416ac4b308a214ff1c5af8b8ee8d6e1ecf55d37d  $YMS" | sha256sum -c -
echo "070732bcca151a8da0cf16390c24d865efe5c2eae8f517f84f9de943831a240f  $BT" | sha256sum -c -
cd "$D"
nice -n 10 "$PY" -B 05bw_decided_corrections_shadow_tables_READONLY.py --self-test
nice -n 10 "$PY" -B -m unittest discover -s "$D" -p 'test_05b[rsw]*.py' 2>&1 | tail -4
echo "STEP 05BW"; nice -n 10 "$PY" -B 05bw_decided_corrections_shadow_tables_READONLY.py --root "$ROOT" --layout iridis --jf2024-yms "$YMS" --out "$RUN/05bw" 2>&1 | tee "$RUN/05bw.log"
echo "05BT OFFSET ROWS 540 AND 600 (from Stage05BV run)"
"$PY" -B - "$BT" <<'PY'
import csv,sys
for r in csv.DictReader(open(sys.argv[1],encoding='utf-8'),delimiter='\t'):
    if r['offset_minutes'] in ('540','600'):
        print('\t'.join(r[k] for k in ('site','variable','group_start','offset_minutes','qc2_pairs','qc2_median_source_minus_grid','qc2_MAD','candidates_NOT_APPROVED','max_adjacent_jump_with_QC2_flanks')))
PY
"$PY" -B - "$RUN" "$EXP_BW_FP" <<'PY'
import json,sys
run,fp=sys.argv[1:];s=json.load(open(run+'/05bw/summary_HOLD.json'))
ok={'05BW_D2_5099':s['D2_zeroed_cells_total']==5099,'05BW_fingerprint_equals_local':s['fingerprint_integers_strings']==fp}
print('STAGE05BX CHECKS',json.dumps(ok))
if not ok['05BW_D2_5099']:print('STAGE05BX HARD CHECK FAILED');sys.exit(2)
print('STAGE05BX COMPLETE; SHADOW TABLES ONLY; ZERO FORCING WRITTEN')
PY
sha256sum "$RUN"/05bw/*
