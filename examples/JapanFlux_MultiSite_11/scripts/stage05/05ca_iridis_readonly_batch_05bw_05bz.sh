#!/usr/bin/env bash
# Stage05CA: serial read-only IRIDIS6 batch. Reruns Stage05BW (Yms rain-gauge correction of rule D1) and runs
# Stage05BZ (proposed values for every remaining HOLD cell, D8 checked against the Stage05BT table).
# No download, no source/forcing/case/Slurm change, nothing approved.
# Usage: bash 05ca_iridis_readonly_batch_05bw_05bz.sh <directory holding the hash-checked scripts>
set -euo pipefail
D="$1"; PY="${PY:-python3}"
ROOT=/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE
YMS="$ROOT/JP-Yms/forcing/packages/JapanFlux2024/A20241022-024_2.00_selected.zip"
BT="$HOME/japanflux_stage05bv/run_20261104T045402Z_1120583/05bt_lag/offset_sensitivity_17_groups_HOLD.tsv"
EXP_BW_FP=ea5951e51601a0386fb83056dc1102eae3ee8f6e6d4af333c4fe6aab6d1acc24
EXP_BZ_FP=9bc3512d077992d502a0dc263e12ddedcb1192c48ef2a82afaef359b384aae29
BASE="$HOME/japanflux_stage05ca"
[ -L "$BASE" ] && { echo "STOP: $BASE is a symlink"; exit 1; }
mkdir -p "$BASE"; RUN="$BASE/run_$(date -u +%Y%m%dT%H%M%SZ)_$$"
[ -e "$RUN" ] && { echo "STOP: $RUN exists"; exit 1; }
mkdir "$RUN"; echo "STAGE05CA RUN $RUN"; "$PY" --version; hostname
echo "a112e8650592040b92698280416ac4b308a214ff1c5af8b8ee8d6e1ecf55d37d  $YMS" | sha256sum -c -
echo "070732bcca151a8da0cf16390c24d865efe5c2eae8f517f84f9de943831a240f  $BT" | sha256sum -c -
cd "$D"
for s in 05bw_decided_corrections_shadow_tables_READONLY.py 05bz_proposed_resolution_of_hold_cells_READONLY.py; do nice -n 10 "$PY" -B "$s" --self-test; done
nice -n 10 "$PY" -B -m unittest discover -s "$D" -p 'test_05b[rswz]*.py' 2>&1 | tail -4
echo "STEP 05BW"; nice -n 10 "$PY" -B 05bw_decided_corrections_shadow_tables_READONLY.py --root "$ROOT" --layout iridis --jf2024-yms "$YMS" --out "$RUN/05bw" 2>&1 | tee "$RUN/05bw.log"
echo "STEP 05BZ"; nice -n 10 "$PY" -B 05bz_proposed_resolution_of_hold_cells_READONLY.py --root "$ROOT" --layout iridis --bw-dir "$RUN/05bw" --bt-tsv "$BT" --out "$RUN/05bz" 2>&1 | tee "$RUN/05bz.log"
"$PY" -B - "$RUN" "$EXP_BW_FP" "$EXP_BZ_FP" <<'PY'
import json,sys
run,bw_fp,bz_fp=sys.argv[1:]
bw=json.load(open(run+'/05bw/summary_HOLD.json'));bz=json.load(open(run+'/05bz/summary_NOT_APPROVED.json'))
ok={'05BW_D2_5099':bw['D2_zeroed_cells_total']==5099,'05BW_fingerprint_equals_local':bw['fingerprint_integers_strings']==bw_fp,
    '05BZ_D8_verified_against_05BT':bz['D8_values_verified_against_05BT_table'] is True,
    '05BZ_fingerprint_equals_local':bz['fingerprint_integers_strings']==bz_fp}
print('STAGE05CA CHECKS',json.dumps(ok))
if not (ok['05BW_D2_5099'] and ok['05BZ_D8_verified_against_05BT']):print('STAGE05CA HARD CHECK FAILED');sys.exit(2)
print('STAGE05CA COMPLETE; PROPOSED VALUES ONLY; ZERO APPROVED; NO FORCING WRITTEN')
PY
sha256sum "$RUN"/05bw/* "$RUN"/05bz/*
