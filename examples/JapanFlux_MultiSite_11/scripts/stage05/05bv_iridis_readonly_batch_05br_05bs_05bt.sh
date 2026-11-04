#!/usr/bin/env bash
# Stage05BV: one serial, read-only IRIDIS6 batch for Stage05BR/BS/BT.
# Self-tests and synthetic unit tests first; then 05BR (nine JPF ZIPs), 05BS (Tom/Tgf forensics and byte
# regeneration of 05BP/05BQ outputs), 05BT companion (from this run's 05BR table) and 05BT lag (existing 16 CDS
# ZIPs, AW ledger, AY windows). No download, no source/forcing/PFT/soil/case/Slurm/AD400 change, nothing approved.
# Usage: bash 05bv_iridis_readonly_batch_05br_05bs_05bt.sh <directory holding the hash-checked scripts>
set -euo pipefail
D="$1"; PY="${PY:-python3}"
ROOT=/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE
AW="$HOME/japanflux_stage05aw/run_20261103T061649Z/stage05aw_45_original_JPF_F_ERA_QC2_source_vs_ERA5L_independent_context_ALL_HOLD.tsv"
AY="$HOME/japanflux_stage05ay/run_20261103T070524Z_4159846/native_windows.tsv"
EARLY="$HOME/japanflux_stage05s/downloads"; LATE="$HOME/japanflux_stage05as/downloads"
BP_EVENTS="$HOME/japanflux_stage05bp/run_20261104T031424Z_359887/special_derived_screen_events_HOLD.tsv"
BQ_DIR="$HOME/japanflux_stage05bq/run_20261104T032013Z_419230"
# Values produced by the local run on byte-identical ZIPs (see STAGE05BR doc); compared, not assumed.
EXP_BR_FP=fcaa23c06921500e2096384da173eb2173e6030b10a524bfae722f2205406324
EXP_BR_ART=0e61a27488b86c8d3cb439fb96eb9a441b513aab64b5d0724e28ad94d4d63b78
EXP_BS_FP=e1644c006e25346afa05c943988c8ebfd8094c9b63cdcbe6704cfce85a505d3f
EXP_BT_COMP=bac8381e6c542f1cc9d75c4084a743f54f3f68ad340faefad381478669217737
BASE="$HOME/japanflux_stage05bv"
[ -L "$BASE" ] && { echo "STOP: $BASE is a symlink"; exit 1; }
mkdir -p "$BASE"; RUN="$BASE/run_$(date -u +%Y%m%dT%H%M%SZ)_$$"
[ -e "$RUN" ] && { echo "STOP: $RUN exists"; exit 1; }
mkdir "$RUN"; echo "STAGE05BV RUN $RUN"; "$PY" --version; hostname
cd "$D"
for s in 05bp_six_site_meteorology_batch_READONLY.py 05bq_four_site_humidity_and_special_shadows_READONLY.py \
         05br_nine_site_jpf_forcing_variable_qc_READONLY.py 05bs_tom_tgf_humidity_tiny_negative_isolated_forensics_READONLY.py \
         05bt_45_field_companion_artifacts_and_era_lag_sensitivity_READONLY.py 05az_bulk_existing_era5l_source_clock_audit_READONLY.py; do
  nice -n 10 "$PY" -B "$s" --self-test
done
nice -n 10 "$PY" -B -m unittest discover -s "$D" -p 'test_05b[pqrst]*.py' 2>&1 | tail -4
echo "OPERATOR_FILES_ON_DISK"; sha256sum "$BP_EVENTS" "$BQ_DIR/special_shadow_candidates_HOLD.tsv" "$BQ_DIR/summary_HOLD.json"
echo "STEP 05BR"; nice -n 10 "$PY" -B 05br_nine_site_jpf_forcing_variable_qc_READONLY.py --root "$ROOT" --layout iridis --out "$RUN/05br" 2>&1 | tee "$RUN/05br.log"
echo "STEP 05BS"; nice -n 10 "$PY" -B 05bs_tom_tgf_humidity_tiny_negative_isolated_forensics_READONLY.py --root "$ROOT" --layout iridis --out "$RUN/05bs" 2>&1 | tee "$RUN/05bs.log"
echo "STEP 05BT COMPANION"; nice -n 10 "$PY" -B 05bt_45_field_companion_artifacts_and_era_lag_sensitivity_READONLY.py companion --artifact-tsv "$RUN/05br/era_artifact_windows_all_F_fields_HOLD.tsv" --out "$RUN/05bt_companion" 2>&1 | tee "$RUN/05bt_companion.log"
echo "STEP 05BT LAG"; nice -n 10 "$PY" -B 05bt_45_field_companion_artifacts_and_era_lag_sensitivity_READONLY.py lag --aw "$AW" --ay "$AY" --early "$EARLY" --late "$LATE" --source-root "$ROOT" --out "$RUN/05bt_lag" 2>&1 | tee "$RUN/05bt_lag.log"
"$PY" -B - "$RUN" "$EXP_BR_FP" "$EXP_BR_ART" "$EXP_BS_FP" "$EXP_BT_COMP" <<'PY'
import json,sys,hashlib
run,br_fp,br_art,bs_fp,bt_comp=sys.argv[1:]
br=json.load(open(run+'/05br/summary_HOLD.json'));bs=json.load(open(run+'/05bs/summary_HOLD.json'))
bt=hashlib.sha256(open(run+'/05bt_companion/companion_artifact_cells_HOLD.tsv','rb').read()).hexdigest()
lag=json.load(open(run+'/05bt_lag/summary_HOLD.json'))
checks={'05BR_artifact_table_equals_local':br['artifact_window_tsv_sha256']==br_art,
        '05BR_integer_fingerprint_equals_local':br['integer_string_fingerprint']==br_fp,
        '05BS_05BP_05BQ_byte_identical':all(bs['regeneration']['byte_identical'].values()),
        '05BS_integer_fingerprint_equals_local':bs['fingerprint_integers_strings']==bs_fp,
        '05BT_companion_table_equals_local':bt==bt_comp,
        '05BT_lag_UTC9_selected_reproduced':lag['selected_UTC9_canonical_sha256_reproduced']=='5fd381ddefac2d08a3cee7ed8548c73477c115a342f5895b4673b325768803ae'}
print('STAGE05BV CHECKS',json.dumps(checks,indent=1))
print('05BT LAG MIN-MAD OFFSETS',json.dumps(lag['min_QC2_MAD_offset_by_group'],indent=1))
hard=('05BR_artifact_table_equals_local','05BS_05BP_05BQ_byte_identical','05BT_lag_UTC9_selected_reproduced')
if not all(checks[k] for k in hard):print('STAGE05BV HARD CHECK FAILED; STOP AND REPORT');sys.exit(2)
if not all(checks.values()):print('STAGE05BV SOFT DIFFERENCE (fingerprint or companion); REPORT FULL LOG')
print('STAGE05BV COMPLETE; READ-ONLY; ZERO APPROVED; ALL HOLD')
PY
find "$RUN" -type f -name '*.json' -o -type f -name '*.tsv' | sort | xargs sha256sum
