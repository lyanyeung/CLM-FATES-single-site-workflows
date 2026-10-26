# Batch02 operator Stage100 actual PASS → Stage101 US-GLE true CIME clock/solar evidence

Date: 2026-10-26. Stage100 user-run `EXIT_CODE=0`; source-pinned 16/16 US-GLE annual NC × eight CIME standard meteorology fields checked, source BIF temperature/humidity ZBOT=23.4m and original wind height=22.65m. Prior successful GF-Guy CIME experiment used `QBOT Sa_shum`, `ZBOT Sa_z`, and reference source case `GF-Guy_FATES_SURF2000_CO2405_1PT` exists with CaseStatus model success. This does NOT prove local-to-UTC time semantics or site PFT.

Stage100 operator report path:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage100_GLE_CIME_field_and_clock_preview_READONLY_20261026T111919Z_715b01ee`

## Why a clock verification is essential

FLUXNET source labels are in **local standard time without DST**, original `TIMESTAMP_START` describes the beginning of 30-minute averages. GLE historical BIF UTC_OFFSET = **-7 h** (local = UTC - 7). Source Stage95/99 NetCDF time is currently `days since YYYY-01-01 00:00:00` with **LOCAL START labels** while the source station longitude is retained. The model's CIME time frame could interpret these as UTC or other model clock, so incorrectly using LST labels as UTC could produce strongly mismatched solar radiation day/night. Time midpoint also matters for hourly radiation and precipitation averaging. CTSM documentation discusses offset and midpoint data timing for single-point DATM [CTSM user guide](https://escomp.github.io/CTSM/users_guide/setting-up-and-running-a-case/customizing-the-datm-namelist.html). **Do not automatically shift data or set clock** without a quantitative check and CIME namelist/coupler verification.

## Stage101, fully read-only real source evidence

[Script](../scripts/stage101/101_GLE_DATM_local_UTC_solar_phase_forensics_readonly.py) pinned commit `3fa1f9883661cde8db0ab95c9c1ede180c8f6954`, Git blob `a46ece5e94a89103113a6ac24f49cc931a6052e5`:
- Confirm actual completed Stage99 and Stage100 source manifest/receipt SHA, source 16 years and preserved **science HOLD**.
- Read actual Stage99 2005, 2010, 2015, 2020 GLE yearly NC, original SHA, source local-start time, site LATIXY/LONGXY, all FSDS time series.
- Apply a NOAA-style fractional-year solar approximation to four hypotheses (no clock translation; LST→UTC +7h START; LST→UTC +7h15min MIDPOINT; LST→UTC +7h30min END) and report how many records with FSDS >50 W m⁻² would be under the *astronomical horizon by more than 3 degrees*, plus dark-side shortwave energy fraction. Use data from **four years** to avoid depending on a single cloud regime. This measures physical consistency, **not model success** or perfect source observation timing; the winner is `BEST_DAYLIGHT_CONSISTENCY_DIAGNOSTIC`, not approved conversion.
- Read-only inspect original real successful GF-Guy source CaseStatus, user_nl_datm_streams, CaseDocs/atm_in/datm_in/lnd_in, env_run.xml/env_case.xml. Does **not** call xmlquery, case.setup, create_clone or launch a model.
- Produce newly versioned `solar_FSDS_clock_four_hypotheses.csv`, `GF_Guy_CIME_CaseDocs_original_readonly.json`, `GLE_yearly_NC_SHA_used_for_clock_test.json`, and `GLE_science_and_CIME_action_gates.csv`; do not touch original 16 NC, original case or existing 215 Batch02 NC.

Still requires later decisions: exact CIME/coupler time handling and year-boundary rotation for local→UTC, reference height difference (23.4 vs 22.65 m), tower actual PFT/landunit representation, and new detached case preview/smoke test.

## One-paste IRIDIS6 script

```bash
(
 set +e
 COMMIT="3fa1f9883661cde8db0ab95c9c1ede180c8f6954"
 BLOB="a46ece5e94a89103113a6ac24f49cc931a6052e5"
 SRC="examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage101/101_GLE_DATM_local_UTC_solar_phase_forensics_readonly.py"
 SCRIPT="$HOME/Batch02_stage101_GLE_solar_clock.py"
 LOG="$HOME/Batch02_stage101_GLE_solar_clock.log"
 curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$SRC" -o "$SCRIPT" || exit 1
 test "$(git hash-object "$SCRIPT")" = "$BLOB" || exit 1
 python3 -B -c 'import ast,sys;ast.parse(open(sys.argv[1],encoding="utf8").read());print("SYNTAX PASS")' "$SCRIPT" || exit 1
 python3 -B "$SCRIPT" --self-test || exit 1
 python3 -B "$SCRIPT" --audit 2>&1 | tee "$LOG"
 RC=${PIPESTATUS[0]}
 echo "STAGE101_EXIT_CODE=$RC"
 grep -E '^STAGE101 (SOLAR|BEST|CASEDOCS|SOURCE CLOCK|REPORT|PASS)' "$LOG" | tail -15
)
```
