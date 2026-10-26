# AmeriFlux Batch02: actual Stage105 PASS → Stage106 true-dated ERA prehistory

Date 2026-10-26. Actual original-cluster Stage105 operator `EXIT_CODE=0`. US-GLE SHA-pinned original independent FLUXNET `ERA5_HH_1981-2025` companion file exists within the original 2005–2020 release. **All 14** original local-standard-time rows for `2004-12-31 17:00,17:30,...,23:30` are present, hence actual **missing count 0/14**. They correspond with UTC_OFFSET=-7 to `2005-01-01 00:00,...,06:30 UTC`, the 14 intervals for which previous Stage102 used artificial Dec2020 late-year meteorology. No new ERA download required. Original release uses source-local labels, **not raw UTC**. Precise original ERA5 source SHA is in original Stage07 and Stage105 receipt.

**One misleading old Stage105 manifest label:** `source_original_2004_local_missing_records=14` was the number of expected inspected intervals, not the number actually missing. The SHA-checked Stage105 `source_ERA5_local_timestamp_provenance.json` correctly reports `original_missing_2004_local_halfhours=[]`. Stage106 uses the exact missing-list as the truth.

## Coordinate check

Original point NC LAT=41.3665, LON=253.7601 (0..360 convention) = **-106.2399** (−180..180) exactly, matching 2026 US-GLE BADM BIF. Original Stage105 printed `TOWER_RELOCATION_HOLD` because BADM says “Change reflects location of new tower”; **this is not coordinate disagreement**. Historical tower relocation/footprint context remains a separate source-representation science issue.

## Stage106 controlled independent candidate

[Stage106 script](../scripts/stage106/106_GLE_2004LST_ERA_backfill_UTCmidpoint_16NC.py), pin commit `728a0100b24cd71098d81bf1306a724111ba83ae`, git blob `4be225f5d26d14b1efb39cd5335f6a2e9c45bfe9`:
1. Fail-closed original SHA checks Stage07 ERA, actual Stage102 16 annual independent UTC-midpoint NC, Stage104 seam distributions and Stage105 prehistory source receipts; all earlier source research and science-HOLD evidence preserved.
2. Extract exactly the **14 real-dated 2004 local-standard ERA rows** and validate both native source `TIMESTAMP_START/END` (30-minute intervals), all seven original ERA variables and plausible units/physics.
3. Convert original native ERA variables with prior Stage07 formula: `TA_ERA (C)→TBOT K`, `PA_ERA kPa→PSRF Pa`, `VPD_ERA hPa` plus vapor saturation to positive RH and QBOT `kg/kg`, `SW_IN_ERA W/m²→FSDS`, `LW_IN_ERA W/m²→FLDS`, `WS_ERA m/s→WIND`, `P_ERA mm per 30 min→PRECTmms mm/s`, `ZBOT=23.4m` (verified original GLE BIF TA sensor; 22.65m WS preserved separately).
4. Report **two distinct** meteorological discontinuities: corrected **within 2005** ERA→tower at UTC Jan1 07:15; and the physical **2020-to-2005 cycle boundary** (now differs because the initial surrogate is replaced). They are not interchangeable. Alert on temperature/pressure worsening rather than approving automatically.
5. If `--check` passes, `--build` creates **a new 16-year 30-minute NOLEAP UTC midpoint candidate** from independent copies of Stage102. **Only the 2005 FIRST 14 native times** have modified meteorology. All 2020→2005 synthetic repeated source weather at the *start* is replaced by the true-dated 2004-local ERA companion. Remaining 280,306 intervals and all unchanged variables/source metadata are verified value-for-value; original Stage95 ten-site 215 NC, Stage99/102 GLE 16-year NC, CIME cases, surfaces and Slurm are unchanged.
6. Output report includes 2004 LST 14 source-to-native-model values CSV, 2005 internal+periodic-edge seam comparison JSON, 16 NC receipts and source hashes; no production approval. A new science-HOLD marker explicitly preserves actual model DATM/coupler smoke test, 0.75m wind vs TA sensor reference height and **PFT/footprint/detailed beetle disturbance** scientific choices.

Actual source BIF (user-provided `AMF_US-GLE_BIF_20260908.xlsx`) has original vegetation annotation `85% Engelmann spruce, 15% Subalpine fir` → **both ENF in coarse FATES**, with historical spruce-beetle disturbance peaking 2008 and **85% forest basal-area mortality**. This is neither 85% cropping nor 85% forest areal loss. The Stage103 gridded landunit `PCT_NATVEG=92.48556%; PCT_CROP=7.51444%` is a **grid cell**, not tower actual canopy/farm fractions. Do not silently overwrite site surface or invent EC footprint percent.

### One-paste IRIDIS6 execution

```bash
(
  set +e
  COMMIT="728a0100b24cd71098d81bf1306a724111ba83ae"
  BLOB="4be225f5d26d14b1efb39cd5335f6a2e9c45bfe9"
  SCRIPT="$HOME/Batch02_stage106_GLE_real_ERA_boundary.py"
  LOG="$HOME/Batch02_stage106_GLE_real_ERA_boundary.log"
  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage106/106_GLE_2004LST_ERA_backfill_UTCmidpoint_16NC.py" -o "$SCRIPT" || exit 1
  test "$(git hash-object "$SCRIPT")" = "$BLOB" || exit 1
  python3 -B -c 'import ast,sys;ast.parse(open(sys.argv[1],encoding="utf8").read());print("SYNTAX PASS")' "$SCRIPT" || exit 1
  python3 -B "$SCRIPT" --self-test || exit 1
  python3 -B "$SCRIPT" --check || exit 1
  python3 -B "$SCRIPT" --build 2>&1 | tee "$LOG"
  RC=${PIPESTATUS[0]}
  echo "STAGE106_EXIT_CODE=$RC"
  grep -E '^STAGE106 (JOIN|PERIODIC_EDGE|SOURCE MATCH|BOUNDARY EVALUATION|NC VERIFICATION|GLE 16/16|REPORT|SCIENCE HOLD)' "$LOG" | tail -40
)
```

Only `STAGE106 GLE 16/16 ERA PREHISTORY NC PASS` plus reliable **physical discontinuity flags** means a candidate has been generated. No model spin-up release. Review actual internal/periodic edge values and verify CIME read in a detached, short test before any long run.
