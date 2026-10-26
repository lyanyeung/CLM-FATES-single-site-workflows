# AmeriFlux Batch02 Stage98 operator PASS → Stage99 single-site GLE ZBOT technical pilot

Date: 26 October 2026. Operator actual Stage98 IRIDIS6 `EXIT_CODE=0`, all ten station height history/UTC source metadata inventoried. **Ho2 15 WS_F date-only rows reclassified: 3 independent original day-precision dates (2014-07-06, 2019-06-19, 2024-02-26) at 28.3 m, duplicated across BIF exports (5 per date), not a physically erroneous height.** BADM permits `YYYY`, `YYYYMM`, `YYYYMMDD`, `YYYYMMDDHHMM`; this does NOT establish exact sensor replacement midnight for a day-only record.

Original official Stage98 evidence: US-GLE TA_F **23.4 m**, WS_F **22.65 m**, both valid dated BIF start `2005-01-01 00:00`, official BIF UTC offset **−7 hours**, no sensor-height prehistory gap, 2005–2020 16 annual source years. Original NC use source-local interval-START labels; official UTC offset and phase for CIME are NOT signed off. Other eight sites' TA/WS prehistory gaps range 3 hours–~3.45 years, and BZS/Ho1 FULLSET have NO native height/offset history.

## Stage99 concrete engineering result

[Stage99 source script](../scripts/stage99/99_GLE_versioned_ZBOT_technical_pilot_and_ten_site_gates.py) commit `601f129b96b1acfb90f2a296bb61aa37c121954d`, Git blob `186578eb720c9a43fabc5d6a490ef2a6b3bd3cde`:
- Strict SHA checks Stage95 ten-site/215-NC generation manifest, `SCIENCE_HOLD_DO_NOT_ACTIVATE_DATM_OR_SUBMIT` and Stage98 original source manifest and output receipts. Verifies precisely one deduplicated GLE `TA_F 23.4 m` and `WS_F 22.65 m` dated measurement from 2005-01-01.
- Creates a **new** GLE 16-year NC technical prototype by copying the 16 immutable Stage95 GLE annual files, and adds native `ZBOT(time,lat,lon)=23.4 m` for temperature/humidity reference, while preserving a separate original `wind_sensor_BIF_height_m=22.65` global attribute (a 0.75 m discrepancy intentionally **not reconciled**). The script validates bit-for-bit equality of all original time/geography and seven met variables, all 16 years, original individual file SHA, and exact height dimensionality.
- Preserves source native-local START time; does **not** shift to UTC. Retains `science_approval=FALSE_TECHNICAL_PREVIEW_ONLY`, no production DATM/CIME/Slurm changes.
- Flags a **real additional CIME stream configuration issue**: the previous Stage87 `make_template` refers to `SHUM`, while the NC contains `QBOT`. A correctly mapped datm stream field/variable alias must be validated before any independent CIME smoke-test; no existing template is activated or rewritten as production.
- Writes an original-pinned `ten_site_manual_height_decision_queue.csv` for nine other station gaps and source absence, `CIME_FIELD_AND_TIME_MAPPING_HOLD.json`, a 16-NC SHA manifest and a strict standalone report. No other sites' NC are built or rewritten by Stage99.

All other original Stage95 full 215/215 annual NC remain intact; full 10-site science/HOLD and Ho1 original 2000-12-27 18.746C source T jump stay pending. This is a **technical prototype**, not permission to spin up.

### Run on IRIDIS6

```bash
(
  set +e
  COMMIT="601f129b96b1acfb90f2a296bb61aa37c121954d"
  BLOB="186578eb720c9a43fabc5d6a490ef2a6b3bd3cde"
  SRC="examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage99/99_GLE_versioned_ZBOT_technical_pilot_and_ten_site_gates.py"
  SCRIPT="$HOME/Batch02_stage99_GLE_ZBOT_technical.py"
  LOG="$HOME/Batch02_Stage99_GLE_ZBOT.log"
  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$SRC" -o "$SCRIPT" || exit 1
  test "$(git hash-object "$SCRIPT")" = "$BLOB" || exit 1
  python3 -B -c 'import ast,sys;ast.parse(open(sys.argv[1],encoding="utf8").read());print("SYNTAX PASS")' "$SCRIPT" || exit 1
  python3 -B "$SCRIPT" --self-test || exit 1
  python3 -B "$SCRIPT" --build 2>&1 | tee "$LOG"
  RC=${PIPESTATUS[0]}
  echo "STAGE99_EXIT_CODE=$RC"
  grep -E '^STAGE99 (VERIFIED|SITE|STREAM|GLE 16/16|REPORT|SCIENCE HOLD)' "$LOG" | tail -20
)
```

Expected `STAGE99 GLE 16/16 TECHNICAL NC WITH SOURCE ZBOT PASS`, **plus a continued SCIENCE HOLD**. After operator run, preflight the actual current CIME DATM/CDEPS `user_nl_datm_streams` field names, clock start/end semantics, and decide whether single `ZBOT` at TA height with non-equal WS source height is acceptable for CLM-FATES. For the other nine stations, first fetch the official AmeriFlux [Measurement Height](https://ameriflux.lbl.gov/data/measurement-height/) dataset, which is updated monthly and includes Start_Date and comments for available BASE records, before any bounded prehistory extension. Record any source mismatch to the exact historical FLUXNET package; do not apply BASE history automatically.
