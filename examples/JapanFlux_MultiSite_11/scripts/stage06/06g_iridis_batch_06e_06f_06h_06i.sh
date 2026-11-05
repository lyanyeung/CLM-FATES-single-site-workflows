#!/usr/bin/env bash
# Stage06G: serial IRIDIS6 batch.
#   06E finalizes the user-approved Stage06C rules (F1-F4, 2026-11-05) from the Stage06B 05CB tables and the Stage06D
#       06C outputs; 06F builds the UTC NOLEAP DATM files with the E3 years into a brand-new directory under $HOME and
#       lists every file whose data differ from the Stage06B 06A candidates;
#   06H (evidence) and 06I (G2 TA anomaly proposals, NOT APPROVED) read the 06E tables and the original packages.
# No download, no change to sources, production forcing, cases or Slurm; no stream is activated.
# Usage (after `conda activate clm_fates_env`): bash 06g_iridis_batch_06e_06f_06h_06i.sh <directory holding the hash-checked scripts>
set -euo pipefail
D="$1"; PY="${PY:-python3}"
ROOT=/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE
R06B="$HOME/japanflux_stage06b/run_20261105T042157Z_3076765"
R06D="$HOME/japanflux_stage06d/run_20261105T183840Z_717241"
EXP_06E_FP=42fec54f88e823c65138e2a3d55a0ef1d5b324e693c58787a82e3414c1f913b5
EXP_06F_FP=2d794754e781911ccb2df11ff388d718ed8888a5f5ca07e4e21c7d1fd17f9ea0
EXP_06F_CHANGED=201895779bf88ab5252c773e42616b665f279bf72c3a648ca10220a4d03cd612
EXP_06F_QBOT=1db3202077d26ce26ead7f66221d69050409f629e0a545c3c82ce6517daa1a15
EXP_06F_FILES=6269cf668ed0d2a6aa0ec81c0712290e5e9075db091435ec33b4aaec4367f1ad
EXP_06H_FP=2b0ce5cb9979c7a80f62fae67483ef3673e22c8777a1dd2f38fdd6b5561838b3
EXP_06I_FP=9808de668695d806ae78b1c4da08a4970d80325e51d60c44e3a5f221f335372f
BASE="$HOME/japanflux_stage06g"
[ -L "$BASE" ] && { echo "STOP: $BASE is a symlink"; exit 1; }
mkdir -p "$BASE"; RUN="$BASE/run_$(date -u +%Y%m%dT%H%M%SZ)_$$"
[ -e "$RUN" ] && { echo "STOP: $RUN exists"; exit 1; }
mkdir "$RUN"; echo "STAGE06G RUN $RUN"; hostname
"$PY" -c 'import sys,numpy,netCDF4;print("python",sys.version.split()[0],"numpy",numpy.__version__,"netCDF4",netCDF4.__version__,"hdf5",netCDF4.__hdf5libversion__)'
echo "841fc01b8c4940cbd95f71cc99d97602bba57a1dc274782c05c769f5a70bf7a4  $R06D/06c/approval_list_E_NOT_APPROVED.tsv" | sha256sum -c -
cd "$D"
for s in 06e_finalize_E_approved_tables_READONLY.py 06f_build_approved_utc_noleap_datm_GUARDED.py 06h_residual_humidity_flags_evidence_READONLY.py 06i_ta_anomaly_forensics_proposals_READONLY.py; do
  nice -n 10 "$PY" -B "$s" --self-test | tail -1
done
nice -n 10 "$PY" -B -m unittest discover -b -s "$D" -p 'test_06*.py' 2>&1 | tail -3   # -b: only the summary; a failure stops the batch (pipefail)
echo "STEP 06E"; nice -n 10 "$PY" -B 06e_finalize_E_approved_tables_READONLY.py --cb-dir "$R06B/05cb" --e-dir "$R06D/06c" --out "$RUN/06e" 2>&1 | tee "$RUN/06e.log"
echo "STEP 06F"; nice -n 10 "$PY" -B 06f_build_approved_utc_noleap_datm_GUARDED.py --table-dir "$RUN/06e" --out "$RUN/06f" --write --ack-utc-plus9-cyclic-shift \
  --compare-06a "$R06B/06a/summary_CANDIDATE.json" 2>&1 | tee "$RUN/06f.log"
echo "STEP 06H"; nice -n 10 "$PY" -B 06h_residual_humidity_flags_evidence_READONLY.py --table-dir "$RUN/06e" --root "$ROOT" --layout iridis --out "$RUN/06h" 2>&1 | tee "$RUN/06h.log"
echo "STEP 06I"; nice -n 10 "$PY" -B 06i_ta_anomaly_forensics_proposals_READONLY.py --table-dir "$RUN/06e" --root "$ROOT" --layout iridis --out "$RUN/06i" 2>&1 | tee "$RUN/06i.log"
"$PY" -B - "$RUN" "$EXP_06E_FP" "$EXP_06F_FP" "$EXP_06F_CHANGED" "$EXP_06F_QBOT" "$EXP_06F_FILES" "$EXP_06H_FP" "$EXP_06I_FP" <<'PY'
import json,sys
run,e_fp,f_fp,f_changed,f_qbot,f_files,h_fp,i_fp=sys.argv[1:]
j=lambda p:json.load(open(run+p))
e=j('/06e/summary_APPROVED_20261105_E.json');f=j('/06f/summary_APPROVED_20261105.json');h=j('/06h/summary_EVIDENCE.json');i=j('/06i/summary_G2_NOT_APPROVED.json')
ok={'06E_160285_list_rows_approved':e['approved_list_rows_total']==160285,'06E_fingerprint_equals_local':e['fingerprint_integers_strings']==e_fp,
    '06F_217_files':len(f['site_year_rows'])==217,'06F_fingerprint_equals_local':f['fingerprint_without_QBOT_and_file_bytes']==f_fp,
    '06F_changed_vs_06A_equals_local':f['changed_vs_06A_sha256']==f_changed,'06H_fingerprint_equals_local':h['fingerprint_integers_strings']==h_fp,
    '06I_5904_list_rows':i['approval_list_rows']==5904,'06I_fingerprint_equals_local':i['fingerprint_integers_strings']==i_fp}
info={'06F_QBOT_equal_local':f['QBOT_digest']==f_qbot,'06F_netcdf_bytes_equal_local':f['file_bytes_digest']==f_files}
print('STAGE06G CHECKS',json.dumps(ok));print('STAGE06G INFO (not a pass condition)',json.dumps(info))
print('STAGE06G 06F',json.dumps({s:{'years':x['years'],'accepted_clock_limit_years':x['accepted_clock_limit_years'],'humidity_screen_after_E1':x['humidity_screen_after_E1']} for s,x in f['sites'].items()}))
print('STAGE06G 06I',json.dumps({'episodes':i['episodes'],'episodes_proposed':i['episodes_proposed'],'rule_totals':i['rule_totals']}))
if not (ok['06E_160285_list_rows_approved'] and ok['06F_217_files'] and ok['06I_5904_list_rows']):print('STAGE06G HARD CHECK FAILED');sys.exit(2)
print('STAGE06G COMPLETE; E TABLES APPROVED, DATM BUILT (NOT ACTIVATED), G2 PROPOSED ONLY; NO CASE, NO SLURM')
PY
sha256sum "$RUN"/06e/* "$RUN"/06f/*.tsv "$RUN"/06f/*.json "$RUN"/06h/* "$RUN"/06i/*
du -sh "$RUN/06f"
