#!/usr/bin/env bash
# Stage06L: serial IRIDIS6 batch, one run.
#   06I (corrected 2026-11-07: TA proposals written as plain numbers) reruns on the Stage06G 06E tables;
#   06J finalizes the user-approved G2A/G2B rules (2026-11-06);
#   06K builds the UTC NOLEAP DATM files with G1 (Tgf 2004-2022) into a brand-new directory under $HOME and lists every
#       file whose data differ from the Stage06G 06F files;
#   06M screens LW_IN, SW_IN, VPD, WS and PA on the 06J tables (H rules: evidence and proposals, NOT APPROVED).
# No download, no change to sources, production forcing, cases or Slurm; no stream is activated.
# Usage (after `conda activate clm_fates_env`): bash 06l_iridis_batch_06i_06j_06k_06m.sh <directory holding the hash-checked scripts>
set -euo pipefail
D="$1"; PY="${PY:-python3}"
ROOT=/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE
R06G="$HOME/japanflux_stage06g/run_20261107T043907Z_2701621"
EXP_06I_FP=2cacd1cea8cad721c75a987a5bfeefb54cd586695a077a562769123ea78b37f4
EXP_06I_LIST=170cea394b5f8af37e104d3f80a7657ca86c9e7a316184f2119f1c68872663f8
EXP_06J_FP=9a694d0d8043d87ef619c5332717b0ede75ed7074d250b11a20588b986076e28
EXP_06K_FP=c36b953c4109da0e1eabecb72dd09d4ce6de9252df35405173dbef6591577b69
EXP_06K_CHANGED=6557e50084c2d24cc138cff0015951f988669a86482aa406443037637af8132c
EXP_06K_QBOT=eb54609e91851d3f4662b6b9c2cb25e87671bb72620fa2acd478924f35d860b2
EXP_06K_FILES=6d7b51791b1787f8b813cb388934ce05a3af8d7a00130c5934c9801e6c46c70c
EXP_06M_FP=c0e84f7735022d362093df357f43abdbedc478b92dc7710a7ed05f67eda4e369
EXP_06M_LIST=b532deb2750f57f38e62b1810da80c3fd4e76e6dbd9ecb1f96c85926510b965e
BASE="$HOME/japanflux_stage06l"
[ -L "$BASE" ] && { echo "STOP: $BASE is a symlink"; exit 1; }
mkdir -p "$BASE"; RUN="$BASE/run_$(date -u +%Y%m%dT%H%M%SZ)_$$"
[ -e "$RUN" ] && { echo "STOP: $RUN exists"; exit 1; }
mkdir "$RUN"; echo "STAGE06L RUN $RUN"; hostname
"$PY" -c 'import sys,numpy,netCDF4;print("python",sys.version.split()[0],"numpy",numpy.__version__,"netCDF4",netCDF4.__version__,"hdf5",netCDF4.__hdf5libversion__)'
echo "b96db8e25daf9d84b98246f4571ccb53af3615bbb4f48a91bfc92e041b10b400  $R06G/06f/summary_APPROVED_20261105.json" | sha256sum -c -
cd "$D"
for s in 06i_ta_anomaly_forensics_proposals_READONLY.py 06j_finalize_G2_approved_tables_READONLY.py 06k_build_approved_utc_noleap_datm_GUARDED.py \
         06m_other_variable_screen_proposals_READONLY.py; do
  nice -n 10 "$PY" -B "$s" --self-test | tail -1
done
nice -n 10 "$PY" -B -m unittest discover -b -s "$D" -p 'test_06*.py' 2>&1 | tail -3   # -b: only the summary; a failure stops the batch (pipefail)
echo "STEP 06I"; nice -n 10 "$PY" -B 06i_ta_anomaly_forensics_proposals_READONLY.py --table-dir "$R06G/06e" --root "$ROOT" --layout iridis --out "$RUN/06i" 2>&1 | tee "$RUN/06i.log"
echo "STEP 06J"; nice -n 10 "$PY" -B 06j_finalize_G2_approved_tables_READONLY.py --e-dir "$R06G/06e" --g2-dir "$RUN/06i" --out "$RUN/06j" 2>&1 | tee "$RUN/06j.log"
echo "STEP 06K"; nice -n 10 "$PY" -B 06k_build_approved_utc_noleap_datm_GUARDED.py --table-dir "$RUN/06j" --out "$RUN/06k" --write --ack-utc-plus9-cyclic-shift \
  --compare-06f "$R06G/06f/summary_APPROVED_20261105.json" 2>&1 | tee "$RUN/06k.log"
echo "STEP 06M"; nice -n 10 "$PY" -B 06m_other_variable_screen_proposals_READONLY.py --table-dir "$RUN/06j" --root "$ROOT" --layout iridis --out "$RUN/06m" 2>&1 \
  | tee "$RUN/06m.log" | cut -c1-600   # the full JSON line stays in 06m.log
"$PY" -B - "$RUN" "$EXP_06I_FP" "$EXP_06I_LIST" "$EXP_06J_FP" "$EXP_06K_FP" "$EXP_06K_CHANGED" "$EXP_06K_QBOT" "$EXP_06K_FILES" "$EXP_06M_FP" "$EXP_06M_LIST" <<'PY'
import json,sys
run,i_fp,i_list,j_fp,k_fp,k_changed,k_qbot,k_files,m_fp,m_list=sys.argv[1:]
l=lambda p:json.load(open(run+p))
i=l('/06i/summary_G2_NOT_APPROVED.json');j=l('/06j/summary_APPROVED_20261106_G2.json');k=l('/06k/summary_APPROVED_20261106.json');m=l('/06m/summary_H_NOT_APPROVED.json')
ok={'06I_fingerprint_equals_local':i['fingerprint_integers_strings']==i_fp,'06I_list_equals_local':i['approval_list_sha256']==i_list,
    '06J_5904_list_rows_approved':j['approved_list_rows_total']==5904,'06J_fingerprint_equals_local':j['fingerprint_integers_strings']==j_fp,
    '06K_215_files':len(k['site_year_rows'])==215,'06K_fingerprint_equals_local':k['fingerprint_without_QBOT_and_file_bytes']==k_fp,
    '06K_changed_vs_06F_equals_local':k['changed_vs_06F_sha256']==k_changed,
    '06M_1589_list_rows':m['approval_list_rows']==1589,'06M_fingerprint_equals_local':m['fingerprint_integers_strings']==m_fp,
    '06M_list_equals_local':m['approval_list_sha256']==m_list}
info={'06K_QBOT_equal_local':k['QBOT_digest']==k_qbot,'06K_netcdf_bytes_equal_local':k['file_bytes_digest']==k_files}
print('STAGE06L CHECKS',json.dumps(ok));print('STAGE06L INFO (not a pass condition)',json.dumps(info))
print('STAGE06L 06K',json.dumps({s:{'years':x['years'],'accepted_clock_limit_years':x['accepted_clock_limit_years'],'humidity_screen':x['humidity_screen']} for s,x in k['sites'].items()}))
print('STAGE06L 06K removed_vs_06F',json.dumps(k['removed_vs_06F']))
print('STAGE06L 06M',json.dumps({'episodes':m['episodes'],'episodes_proposed':m['episodes_proposed'],'by_check_class':m['episodes_by_check_class'],'rule_totals':m['rule_totals']}))
print('STAGE06L 06M LW systematic years',json.dumps({t:x['stats']['LW_systematic_years'] for t,x in m['tables'].items() if x['stats']['LW_systematic_years']}))
print('STAGE06L 06M recurring night SW',json.dumps({t:x['stats']['SW_night_clusters'] for t,x in m['tables'].items() if x['stats']['SW_night_clusters']}))
if not (ok['06J_5904_list_rows_approved'] and ok['06K_215_files'] and ok['06M_1589_list_rows']):print('STAGE06L HARD CHECK FAILED');sys.exit(2)
print('STAGE06L COMPLETE; G2 TABLES APPROVED, DATM BUILT (NOT ACTIVATED), H RULES PROPOSED ONLY; NO CASE, NO SLURM')
PY
sha256sum "$RUN"/06i/approval_list_G2_NOT_APPROVED.tsv "$RUN"/06i/ta_anomaly_episodes.tsv "$RUN"/06j/* "$RUN"/06k/*.tsv "$RUN"/06k/*.json "$RUN"/06m/*
du -sh "$RUN/06k"
