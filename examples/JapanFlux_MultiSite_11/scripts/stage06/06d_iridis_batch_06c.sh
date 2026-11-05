#!/usr/bin/env bash
# Stage06D: serial read-only IRIDIS6 batch. Runs Stage06C (humidity E1 and Tgf clock E2 proposals, NOT APPROVED) on
# the Stage06B 05CB tables, and reports whether the Stage06B QBOT data hashes and NetCDF bytes match the local run
# (informational; the 06A fingerprint already matched). No download, no source/forcing/case/Slurm change.
# Usage (after `conda activate clm_fates_env`): bash 06d_iridis_batch_06c.sh <directory holding the hash-checked scripts>
set -euo pipefail
D="$1"; PY="${PY:-python3}"
ROOT=/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE
R06B="$HOME/japanflux_stage06b/run_20261105T042157Z_3076765"
EXP_06C_FP=e4340c0159051919d618a52ce1dc776fd0da13cad95f4fa0790b51e8a0d138a3
EXP_QBOT=26b3a9709a98e417b70681096ccb96a13c99a1163772d951686a0fb15e773e71
EXP_FILES=285903c27511605058047fe6fbe4b50c1e2d54a155ba1da01bb50f36633359ac
BASE="$HOME/japanflux_stage06d"
[ -L "$BASE" ] && { echo "STOP: $BASE is a symlink"; exit 1; }
mkdir -p "$BASE"; RUN="$BASE/run_$(date -u +%Y%m%dT%H%M%SZ)_$$"
[ -e "$RUN" ] && { echo "STOP: $RUN exists"; exit 1; }
mkdir "$RUN"; echo "STAGE06D RUN $RUN"; hostname
"$PY" -c 'import sys,numpy,netCDF4;print("python",sys.version.split()[0],"numpy",numpy.__version__,"netCDF4",netCDF4.__version__)'
cd "$D"
nice -n 10 "$PY" -B 06c_humidity_and_tgf_clock_forensics_proposals_READONLY.py --self-test
nice -n 10 "$PY" -B -m unittest discover -s "$D" -p 'test_06*.py' 2>&1 | tail -3
echo "STEP 06C"; nice -n 10 "$PY" -B 06c_humidity_and_tgf_clock_forensics_proposals_READONLY.py --cb-dir "$R06B/05cb" --root "$ROOT" --layout iridis --out "$RUN/06c" 2>&1 | tee "$RUN/06c.log"
"$PY" -B - "$RUN" "$R06B" "$EXP_06C_FP" "$EXP_QBOT" "$EXP_FILES" <<'PY'
import hashlib,json,sys
run,r06b,fp,qbot,files=sys.argv[1:]
c=json.load(open(run+'/06c/summary_E_NOT_APPROVED.json'));a=json.load(open(r06b+'/06a/summary_CANDIDATE.json'))
q=[];f=[]
for site,e in sorted(a['sites'].items()):
    for n,x in sorted(e['files'].items()):q.append(n+':'+x['data_sha256_by_variable']['QBOT']);f.append(n+':'+x['file_sha256'])
dig=lambda xs:hashlib.sha256('\n'.join(xs).encode()).hexdigest()
ok={'06C_fingerprint_equals_local':c['fingerprint_integers_strings']==fp,'06C_E2_four_confirmed_windows':sum(w['proposed'] for w in c['tables']['JP-Tgf_HH']['E2_windows'])==4}
info={'06B_QBOT_hashes_equal_local':dig(q)==qbot,'06B_netcdf_bytes_equal_local':dig(f)==files}
print('STAGE06D CHECKS',json.dumps(ok));print('STAGE06D INFO (not a pass condition)',json.dumps(info))
if not ok['06C_E2_four_confirmed_windows']:print('STAGE06D HARD CHECK FAILED');sys.exit(2)
print('STAGE06D COMPLETE; PROPOSED VALUES ONLY; NOTHING APPROVED OR WRITTEN TO FORCING')
PY
sha256sum "$RUN"/06c/*
