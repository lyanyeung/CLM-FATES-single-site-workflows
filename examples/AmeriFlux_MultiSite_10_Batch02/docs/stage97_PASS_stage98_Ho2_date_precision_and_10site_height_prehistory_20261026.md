# Stage97 actual operator PASS — Stage98 official BADM precision correction and height prehistory

Date: 26 October 2026. Actual IRIDIS6 Stage97 operator `EXIT_CODE=0`, source full native 30/60-minute **leap-inclusive** timestamps validated for all 10 original source releases. Eight site original BIF UTC offsets were found (CMW/GLE -7, EML/ICh/ICt -9, Ha1/Ho2/Ho3 -5), while **US-BZS and US-Ho1** FULLSET lack native BIF UTC and TA_F/WS_F measurement heights. Source timezone values do not yet demonstrate DATM stream clock phase or justify an automatic shift.

Stage97 reported 15 `US-Ho2 WS_F` records with `VAR_INFO_DATE` day precision `20140706`, `20190619`, `20240226`, each repeated 5 times across original BIF exports; `VAR_INFO_HEIGHT=28.3` m. This is a **false parse error**, not a sensor height anomaly. The Stage97 parser accepted only 12 digits; AmeriFlux BADM DATE standards formally accept `YYYY`, `YYYYMM`, `YYYYMMDD` and `YYYYMMDDHHMM` ([AmeriFlux DATE Standards](https://ameriflux.lbl.gov/badm_resource/date-variables/)); the measurement-height product reports heights in meters and notes day precision ([AmeriFlux Measurement Height](https://ameriflux.lbl.gov/data/measurement-height/)). Thus all 15 must be reclassified as valid **day-precision source height statements** and collapsed to 3 unique dated records, while retaining original source/provenance. Day precision does **not** prove an exact midnight sensor switch: do not assume it.

## Stage98 audited executable

[Stage98 code](../scripts/stage98/98_resolve_BIF_precision_height_prehistory_readonly.py), pinned commit `5e16855860b29cc8e53b8863a34eec153d804e8b`, Git blob `4bcc90cc4559d455b6de42f871d1ecb44fcd5fcc`, reads only the **SHA-verified immutable Stage97 evidence** and the original Stage07 year/source roster. It normalizes 4/6/8/12-digit BADM dates, rejects original -9999, implausible heights, unapproved unit and impossible dates, checks duplicates and dated contradictory height records, and summarizes per site:
- original first available TA_F / WS_F heights, numerical height values and date **precision**;
- exact forcing source start vs earliest valid height and missing prehistory days, only if supported by the evidence;
- official source UTC offset candidate, previously SHA verified; if not present, remains `UNKNOWN`;
- specific remaining human scientific decisions for prehistory, conflicting instrument height, local timestamp → DATM conversion, site footprint/PFT, and Ho1 2000 QC1→QC2 source transition.

The code writes a **new report only**, not active forcing/NC/CIME. `10_site_height_history_decision_summary.csv`, `all_original_BIF_height_rows_reclassified.csv`, `site_historical_height_evidence.json`, and manifest receipt are isolated under `reports/stage98_*`.

## Run on IRIDIS6

```bash
(
 set +e
 COMMIT="5e16855860b29cc8e53b8863a34eec153d804e8b"
 BLOB="4bcc90cc4559d455b6de42f871d1ecb44fcd5fcc"
 SCRIPT="$HOME/Batch02_stage98_BIF_date_and_height.py"
 RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
 curl -fLsS --retry 3 "$RAW/$COMMIT/examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage98/98_resolve_BIF_precision_height_prehistory_readonly.py" -o "$SCRIPT" || exit 1
 test "$(git hash-object "$SCRIPT")" = "$BLOB" || exit 1
 python3 -B -c 'import ast,sys;ast.parse(open(sys.argv[1],encoding="utf8").read());print("SYNTAX PASS")' "$SCRIPT" || exit 1
 python3 -B "$SCRIPT" --self-test || exit 1
 LOG="$HOME/Batch02_Stage98_heights.log"
 python3 -B "$SCRIPT" --audit 2>&1 | tee "$LOG"
 RC=${PIPESTATUS[0]}
 echo "STAGE98_EXIT_CODE=$RC"
 grep -E '^STAGE98 (US-|HO2|REPORT|PASS)' "$LOG"
)
```

Once the user supplies the Stage98 precise first-height and gap-day table, choose a **site-specific** height policy. US-GLE has both histories from the start and can be prioritized for an **isolated ZBOT prototype**, subject to exact TA vs WS height suitability; other sites must not receive blanket earliest-height backward extrapolation. The Stage95 ten-site 215 NC scientific-HOLD state is preserved.
