# Actual Stage102 PASS → Stage103 GLE detached CIME/stream namelist parser test

26 October 2026: Stage102 actual IRIDIS6 `EXIT_CODE=0` successfully generated **US-GLE 16/16 independent UTC midpoint cyclic NetCDF**, conserving **280320 half-hour source samples** and all original GLE fields and ZBOT. The new source report is:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage102_GLE_UTC_plus7_midpoint_CYCLIC_16NC_TECHNICAL_ONLY_20261026T114427Z_e63d3051`

The Stage102 first **14** UTC half-hours in 2005 are deliberately filled from the 2020 local-year end rather than invented missing real 2004 measurements. An internal **2020-12-31 23:30 LST to 2005-01-01 00:00 LST** cycle seam exists at **model UTC 2005-01-01 07:15** and recurs every 16-year forcing cycle. That provenance remains a science HOLD. Existing Stage95 ten-site 215 annual NC and Stage99 GLE original 16 annual NC are unchanged, and no CIME model job has run.

## Stage103 review and isolated CIME parser

[Stage103 Python driver](../scripts/stage103/103_GLE_seam_CIME_detached_namelist_preflight.py) pinned commit `358a7f51e4749955ed1ccf57916e732ee3cf2532`, git blob `c67aa9c5c4e358b0c2efba99da46e08d8a8341c5`. Three modes:

- `--self-test`: verify 16-source/8-CIME-field/UTC seam invariants, no writes.
- `--check`: **READ ONLY** check exact SHA of all 16 Stage102 NC and original Stage99 source copies, model UTC midpoint axis and 8 climate fields, original GF-Guy source CaseStatus, actual site batch02 subset point surface and untouched site user_mods, and print 8 variable jumps at the *artificial* UTC 07:15 internal seam. The GLE surface may have gridded PFT/crop fractions that cannot stand in for actual EC footprint PFT.
- `--prepare`: first same strict preflight, then **new unique, isolated report-root CIME clone** using proven GF-Guy reference `create_clone --keepexe`, independently copied/sanitized US-GLE 2000 point user_mods, 16 Stage102 UTC NetCDF files, CIME `CLM_USRDAT.UNSET` eight mappings `QBOT Sa_shum`, `ZBOT Sa_z`, `tintalgo=linear`, `taxmode=cycle`, year_first 2005, year_last 2020, year_align 2005, `RUN_STARTDATE=2005-01-01`, `CALENDAR=NO_LEAP`, `ATM_NCPL=48`, short `STOP_OPTION=nsteps`, `STOP_N=1`, `RESUBMIT=0`. It calls only `case.setup` and `preview_namelists` on the detached case; checks generated `CaseDocs/lnd_in` selected the proper GLE 2000 surface, and never executes `case.build`, `case.submit`, `srun` or `sbatch`. The GF-Guy source case, 16+215 NC, original surface, other sites, and original CIME cases are not written. If CIME fails, the unique output folder retains a detailed error and `INCOMPLETE_PREVIEW_DO_NOT_USE` marker.

**Science HOLD is not waived even when prepare passes**: cycle seam/non-observed 2004 boundary, actual model clock/CIME time interpolation on data not yet exercised, GLE 23.4 m TA reference vs 22.65 m WS measurement height, and actual tower vegetation versus reference gridded CLM natural/crop PFT are still not approved. A namelist preview is NOT a running model/data read test.

## IRIDIS6 one-paste

```bash
(
 set +e
 REV="358a7f51e4749955ed1ccf57916e732ee3cf2532"
 BLOB="c67aa9c5c4e358b0c2efba99da46e08d8a8341c5"
 URL="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$REV/examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage103/103_GLE_seam_CIME_detached_namelist_preflight.py"
 SCRIPT="$HOME/Batch02_stage103_GLE_CIME_parser.py"
 LOG="$HOME/Batch02_Stage103_GLE_CIME_parser.log"
 curl -fLsS --retry 3 "$URL" -o "$SCRIPT" || exit 1
 test "$(git hash-object "$SCRIPT")" = "$BLOB" || exit 1
 python3 -B -c 'import ast,sys;ast.parse(open(sys.argv[1],encoding="utf8").read());print("SYNTAX PASS")' "$SCRIPT" || exit 1
 python3 -B "$SCRIPT" --self-test || exit 1
 python3 -B "$SCRIPT" --check || exit 1
 python3 -B "$SCRIPT" --prepare 2>&1 | tee "$LOG"
 RC=${PIPESTATUS[0]}
 echo "STAGE103_EXIT_CODE=$RC"
 grep -E '^STAGE103 (SOURCE|CYCLE_SEAM|SURFACE|CIME_MAP|SCIENCE|CHECK|DETACHED|REPORT|HOLD)' "$LOG" | tail -20
)
```

Success criterion: `STAGE103 DETACHED CIME NAMELIST PASS | GLE Stage102 16NC, 8 fields, site GLE surface; NO MODEL RUN`, followed by `STAGE103 HOLD`. Do not run any `case.submit` command even if output passed.

Potential failures requiring code review: source site Stage03 user_mods land surface filename mismatch, cloned CIME component config unable to accept `CLM_USRDAT.UNSET`, false CIME build requirements, missing `CaseDocs/lnd_in`, GF-Guy reference case changing. These are engineering holds, not reasons to alter original scientific data.
