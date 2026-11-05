#!/usr/bin/env bash
# Stage06B: serial IRIDIS6 batch. Stage05CB finalizes the user-approved tables from the Stage05CA 05BZ outputs;
# Stage06A builds the UTC NOLEAP DATM candidates into a brand-new directory under $HOME.
# No download, no change to sources, production forcing, cases or Slurm; no stream is activated.
# Usage (after `conda activate clm_fates_env`): bash 06b_iridis_batch_05cb_06a.sh <directory holding the hash-checked scripts>
set -euo pipefail
D="$1"; PY="${PY:-python3}"
BZ="$HOME/japanflux_stage05ca/run_20261105T030635Z_2576314/05bz"
EXP_CB_FP=94d826ee58c5a9ee724db069b7d2757535ef3710aeaa1d3f4cb3df514922e6fa
EXP_06A_FP=e67f0e64de13a9656b2bfafb100c6a9bcae8539b65e019a69fd978479acd0f3c
BASE="$HOME/japanflux_stage06b"
[ -L "$BASE" ] && { echo "STOP: $BASE is a symlink"; exit 1; }
mkdir -p "$BASE"; RUN="$BASE/run_$(date -u +%Y%m%dT%H%M%SZ)_$$"
[ -e "$RUN" ] && { echo "STOP: $RUN exists"; exit 1; }
mkdir "$RUN"; echo "STAGE06B RUN $RUN"; hostname
"$PY" -c 'import sys,numpy,netCDF4;print("python",sys.version.split()[0],"numpy",numpy.__version__,"netCDF4",netCDF4.__version__,"hdf5",netCDF4.__hdf5libversion__)'
echo "5a7d855167097014f9ff97de61ed579e4ea995e7ac50854905cd4af881af4b9e  $BZ/approval_list_NOT_APPROVED.tsv" | sha256sum -c -
cd "$D"
for s in 05cb_finalize_approved_preforcing_tables_READONLY.py 06a_build_utc_noleap_datm_candidates_GUARDED.py; do nice -n 10 "$PY" -B "$s" --self-test; done
nice -n 10 "$PY" -B -m unittest discover -s "$D" -p 'test_0*.py' 2>&1 | tail -4
echo "STEP 05CB"; nice -n 10 "$PY" -B 05cb_finalize_approved_preforcing_tables_READONLY.py --bz-dir "$BZ" --out "$RUN/05cb" 2>&1 | tee "$RUN/05cb.log"
echo "STEP 06A"; nice -n 10 "$PY" -B 06a_build_utc_noleap_datm_candidates_GUARDED.py --cb-dir "$RUN/05cb" --out "$RUN/06a" --write --ack-utc-plus9-cyclic-shift 2>&1 | tee "$RUN/06a.log"
"$PY" -B - "$RUN" "$EXP_CB_FP" "$EXP_06A_FP" <<'PY'
import json,sys
run,cb_fp,a_fp=sys.argv[1:]
cb=json.load(open(run+'/05cb/summary_APPROVED_20261105.json'));a=json.load(open(run+'/06a/summary_CANDIDATE.json'))
ok={'05CB_145855_approved':cb['approved_cells_total']==145855,'05CB_fingerprint_equals_local':cb['fingerprint_integers_strings']==cb_fp,
    '06A_226_files':len(a['site_year_rows'])==226,'06A_fingerprint_equals_local':a['fingerprint_without_QBOT_and_file_bytes']==a_fp}
print('STAGE06B CHECKS',json.dumps(ok))
print('STAGE06B OPEN ITEMS',json.dumps({s:{'humidity':e['humidity_status'],'clock_review_years':e['clock_review_years']} for s,e in a['sites'].items()}))
if not (ok['05CB_145855_approved'] and ok['06A_226_files']):print('STAGE06B HARD CHECK FAILED');sys.exit(2)
print('STAGE06B COMPLETE; APPROVED TABLES + DATM CANDIDATES (NOT ACTIVATED); NO CASE, NO SLURM')
PY
sha256sum "$RUN"/05cb/* "$RUN"/06a/*.tsv "$RUN"/06a/*.json
du -sh "$RUN/06a"
