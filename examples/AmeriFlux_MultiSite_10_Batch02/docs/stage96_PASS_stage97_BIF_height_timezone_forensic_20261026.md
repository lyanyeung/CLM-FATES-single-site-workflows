# Actual Stage96 operator PASS, and Stage97 science metadata forensics

Date: 26 October 2026. Actual IRIDIS6 Stage96 returned `EXIT_CODE=0` / `10/10 sites, 215 annual NC, structural_fail 0`. It was **only structural preflight**: no DATM activation and no scientific clearance for exact station clock phase, measurement heights, or PFT/footprint.

Operator original Stage96 inventory:
- US-BZS / US-Ho1: exact historical FLUXNET-BIF `VAR_INFO_VARNAME=TA_F/WS_F` measurement-height dates absent (FULLSET packages, use official metadata, never substitute guessed heights). Ho1 additionally retains original 2000-12-27 QC1 -15.4°C → QC2 3.346°C +18.746°C uncertainty.
- US-CMW, US-EML, US-Ha1, US-Ho2, US-Ho3, US-ICh, US-ICt: some official historical temperature and/or wind heights began after the forcing start, requiring source pre-history evidence or an explicit later justified extension, not silent backcasting.
- US-Ho2: 15 original BIF `WS_F:invalid_BIF_height_or_date:ValueError` observations; Stage96's bare ValueError count is insufficient to decide whether these are missing sentinels, time parser errors, units or true contradicted height values.
- US-GLE: original BIF temperature and wind heights present without first-year prehistory warning; still cannot call DATM scientifically approved.
- All ten: new Stage95 preview annual NC lacks `ZBOT`; original source interval and official UTC_OFFSET / model local-to-UTC phase not yet verified; natural PFT fraction and landunits structurally verified but FATES PFT/footprint not independently approved. None are active CIME cases.

## Stage97, isolated read-only exact source forensic

[Script](../scripts/stage97/97_forensic_BIF_ZBOT_UTC_and_site_release_gates.py), pinned `a27e58b215d19e2fabec96a16a8c3d1ad89a8ef1`, Git blob `8e383c8847fad25a475a4d4e56602dbc40158328`:
1. Verifies Stage95 full 10-site/215 new annual NC scientific-hold manifest and Stage96 original ten-site SHA receipts.
2. Streams the **entire** original FLUXNET primary `TIMESTAMP_START/END` for each site, checks native 30/60-min interval identity, uninterrupted year start/end, **leap-inclusive original record count** separately from Stage95 365-day NOLEAP annual NC, repeated/omitted/retrograde intervals. No guess from longitude or DST conversion.
3. Scans every official native `*BIF*.csv`, exact variable group records `VAR_INFO_VARNAME=TA_F/WS_F`, original raw `VAR_INFO_DATE`, `VAR_INFO_HEIGHT`, units, date group and site; prints all rejected height records with original strings, site/time, parser reason, and accurate count.
4. Finds original site `UTC_OFFSET`, `TIMEZONE`, `SITE_UTC_OFFSET` fields in release BIF, with source path, group and values. A value may be a **candidate** for metadata, not proof that CIME DATM expects shifted UTC timestamps.
5. Labels each site/variable as `NO_VERIFIED_NATIVE_HEIGHT`, `BIF_MALFORMED_OR_CONFLICTING_HEIGHT_HOLD`, `HISTORY_BEFORE_FIRST_HEIGHT_NOT_ESTABLISHED_HOLD`, or `FULL_PERIOD_START_DATED_HEIGHT_AVAILABLE_NUMERIC_CANDIDATE`. Does not invent or write heights. Continues when a site's evidence is unavailable.
6. Writes `10_site_time_height_readiness.csv`, `all_raw_BIF_TA_WS_height_rows.csv`, `invalid_BIF_height_rows_needing_science_review.csv`, full provenance JSON and SHA receipts to new unique `reports/stage97_*`. **No source/NetCDF/CIME/DATM/Slurm files modified**.

AmeriFlux's [official data variables guidance](https://ameriflux.lbl.gov/data/aboutdata/data-variables/) states that half-hour/hour records use START and END and are reported in local standard time *without DST*, with UTC offset in site BADM. Official [Measurement Height](https://ameriflux.lbl.gov/data/measurement-height/) provides site-team height metadata for BASE releases, but measurements there must be independently tied to the exact FLUXNET-variable/source period before applying to the model.

## One paste on IRIDIS6

```bash
(
  set +e
  COMMIT="a27e58b215d19e2fabec96a16a8c3d1ad89a8ef1"
  BLOB="8e383c8847fad25a475a4d4e56602dbc40158328"
  REL="examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage97/97_forensic_BIF_ZBOT_UTC_and_site_release_gates.py"
  SCRIPT="$HOME/Batch02_stage97_BIF_clock_readonly.py"
  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$SCRIPT" || exit 1
  test "$(git hash-object "$SCRIPT")" = "$BLOB" || exit 1
  python3 -B -c 'import ast,sys;ast.parse(open(sys.argv[1],encoding="utf-8").read());print("SYNTAX PASS")' "$SCRIPT" || exit 1
  python3 -B "$SCRIPT" --self-test || exit 1
  LOG="$HOME/Batch02_Stage97_BIF_clock.log"
  python3 -B "$SCRIPT" --audit 2>&1 | tee "$LOG"
  RC=${PIPESTATUS[0]}
  echo "STAGE97_EXIT_CODE=$RC"
  grep -E '^STAGE97 (US-|FORENSIC|REPORT|RESULT)' "$LOG" | tail -20
)
```

Expected `STAGE97 RESULT | 10 sites examined; original source clock/BIF rows inventoried; forensic_fail 0 | NO DATM/ZBOT/CIME/SLURM MODIFICATIONS`. This is **source forensic progress**, not case readiness. For actual per-height numbers and Ho2 malformed BIF source lines, inspect `invalid_BIF_height_rows_needing_science_review.csv` and `10_site_time_height_readiness.csv`, not just the summary.
