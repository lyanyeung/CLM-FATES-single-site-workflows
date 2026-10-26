# Batch02 Stage95 operator full PASS → Stage96 pre-DATM metadata and science preflight

Date: 2026-10-26. Actual operator run of Stage95 returned `EXIT_CODE=0` and `STAGE95 VERSIONED 10 SITE POST-V5 PASS | 122 USER QC0 APPROVED; 215 REGENERATED NOLEAP NC VERIFIED`. Source-provenance verified Stage87/92 original candidates and all 10 new separated forcing CSV, 215 regenerated NetCDF with annual hashes and independent numerical Post-v5. New full 10-site report folder:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage95_ten_site_122_user_approved_versioned_forcing_215NC_20261026T034516Z_f4afa348`

This is **NOT** permission to submit a production CIME/DATM CLM-FATES case. No model submitted. Site source clock vs UTC, native interval time centering, ZBOT, PFT/footprint and CIME DATM/CDEPS expected stream format all need verification; Ho1 original 2000-12-27 QC1-to-QC2 temperature discontinuity +18.746C also remains unapproved. Nine sites have no *additional named* Ho1 source hold, but they are not automatically production ready.

## Stage96 no-write executable

[Stage96](../scripts/stage96/96_ten_site_DATM_clock_ZBOT_surface_preflight_readonly.py) commit `1ac897bc0747ba47b22b6338d9d0ac4ee93acada` / Git blob `c1a57ddd97395bbf61bf1bf517c634ab59141e8f` reads only the exact Stage95 report, hashes every year of the 215 versioned NetCDF files, verifies NOLEAP complete-year 30/60-minute label coordinates, site identifiers and preserved QC0 approvals. It examines original FLUXNET `TIMESTAMP_START` and `TIMESTAMP_END` when present; **start/end alone do not prove UTC offset or model DATM sampling phase**. It retrieves native original BIF `VAR_INFO_VARNAME=TA_F/WS_F` measurement height histories, flags absent/conflicting history and any first height observation after the forcing period, without inventing a constant height. It audits actual year-2000 CTSM subset point surfaces, % landunit sum, natural PFT sum, >15% crop fraction and surface/NC coordinates; CLM natural PFT is NOT the observed forest inventory or FATES PFT. User-mod CIME stream and actual model forcing hooks are not built or activated.

A new read-only report directory has `10_site_readiness_gates.csv`, `original_source_BIF_surface_NC_evidence.json`, and source SHA manifest. All nine sites and Ho1 are listed separately; site-specific original BIF missing or large crop fraction becomes a science HOLD with exact evidence. The test never grants approval via guessed longitude/time offset, default height or vegetation mapping.

## IRIDIS6 one paste

```bash
(
  set +e
  COMMIT="1ac897bc0747ba47b22b6338d9d0ac4ee93acada"
  BLOB="c1a57ddd97395bbf61bf1bf517c634ab59141e8f"
  REL="examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage96/96_ten_site_DATM_clock_ZBOT_surface_preflight_readonly.py"
  SCRIPT="$HOME/Batch02_stage96_readonly.py"
  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" -o "$SCRIPT" || exit 1
  test "$(git hash-object "$SCRIPT")" = "$BLOB" || exit 1
  python3 -B -c 'import ast,sys;ast.parse(open(sys.argv[1],encoding="utf-8").read());print("SYNTAX PASS")' "$SCRIPT" || exit 1
  python3 -B "$SCRIPT" --self-test || exit 1
  LOG="$HOME/Batch02_Stage96_preDATM.log"
  python3 -B "$SCRIPT" --audit 2>&1 | tee "$LOG"
  RC=${PIPESTATUS[0]}
  echo "STAGE96_EXIT_CODE=$RC"
  grep -E '^STAGE96 (US-|REPORT|RESULT)|^NO SOURCE' "$LOG" | tail -16
)
```

If Stage96 says `structural_fail 0`, that only means source structure was confirmed; unresolved `CLOCK_UTC_OFFSET_AND_INTERVAL_PHASE_NOT_YET_VERIFIED`, ZBOT source/height mapping, FATES PFT/footprint, CIME smoke-test and the Ho1 source-HOLD remain **required** and are not bypassed by the success code. After reviewing its targeted ten-site readiness table, prioritize site-specific BIF height/UTC offset evidence and build a detached smoke-test case only when science choices are defensible. Original Stage95 numeric candidates remain unchanged.
