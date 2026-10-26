# Batch02 Stage99 operator PASS → Stage100 US-GLE CIME/DATM field/clock contract

Date 2026-10-26. Actual Stage99 operator returned `EXIT_CODE=0`, **US-GLE 16/16 yearly NetCDF with original BIF TA_F height ZBOT=23.4 m**, WIND measured at **22.65 m** separately in global metadata. All original Stage95 meteorology fields and local-start/NOLEAP time remain unchanged, no Slurm/CIME work. Stage99 technical report:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage99_GLE_23p4m_source_ZBOT_16yr_TECHNICAL_ONLY_20261026T043117Z_c311a7a5`

**Important correction to old Stage87 template warning:** The Stage87 NC writer **actually writes BOTH `QBOT` and `SHUM`**, with `SHUM=QBOT` exactly (plus derived RH); they are in fact not mutually exclusive NetCDF representations. Stage87 NC units are **`kg kg-1`, `W m-2`, `m s-1`, `mm s-1`**, not slash-style conventional strings. The historical eight-site GF-Guy proven-layout CIME `user_nl_datm_streams` generator uses **`QBOT Sa_shum`** and **`ZBOT Sa_z`**; its Git blob is `65084885323060329e84b9ac2155463c12885160`. Therefore mapping does NOT require new moisture data or renaming source variables, but the actual CIME datavars/clock namelist still must be tested in a detached case.

## Stage100 actual code

[Stage100](../scripts/stage100/100_GLE_CIME_DATM_stream_contract_readonly.py) pinned commit `bb95f844c95ddc3a261e696fba103bb2eec41057`, Git blob `d9153819ad3060b6609eb53d5d9a8c857d4bfc14`. It:
- verifies exact Git blob of successful historical eight-site stream script and copies **that supported mapping** as an **UNACTIVATED** `user_nl_datm_streams.PROPOSED_NOT_APPLIED` text file under a fresh report folder only;
- checks the user-successful Stage99 16-year pilot manifest, source NC SHA, 17520 annual NOLEAP start-label coordinates, exactly the current Stage87 CF units, eight CIME fields, SHUM==QBOT alias, known BIF wind vs TA height and original science-HOLD metadata;
- reads existence and CaseStatus of original GF-Guy case, but **never executes xmlquery, case.setup, create_clone, case.build, xmlchange or Slurm commands**, and never writes a live user_nl_datm_streams;
- produces `16_year_CIME_DATM_variable_time_evidence.json`, `GF_Guy_source_case_readonly_state.json`, `remaining_GLE_science_and_case_blockers.csv`, original input/outputs SHA receipt and a non-activated example mapping. It preserves **original local standard START labels**, BIF offset **−7** as metadata ONLY (no automatic offset correction), and 0.75 m distinct wind measurement height with source PFT/CIME acceptance still blocked.

**US-GLE does NOT yet have a production DATM case** even if Stage100 passes. The separate Ho1 2000 +18.746°C temperature source discontinuity remains a ten-site issue, and nine other sites lack height prehistory or original official heights.

## One-paste on IRIDIS6

```bash
(
  set +e
  REV="bb95f844c95ddc3a261e696fba103bb2eec41057"
  W="$HOME/Batch02_stage100_GLE"
  mkdir -p "$W"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$REV"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage100/100_GLE_CIME_DATM_stream_contract_readonly.py" -o "$W/100_GLE_CIME_DATM_stream_contract_readonly.py" || exit 1
  curl -fLsS --retry 3 "$RAW/examples/FLUXNET_MultiSite_8/scripts/09_eight_site_spinup500.sh" -o "$W/09_eight_site_spinup500.sh" || exit 1
  test "$(git hash-object "$W/100_GLE_CIME_DATM_stream_contract_readonly.py")" = "d9153819ad3060b6609eb53d5d9a8c857d4bfc14" || exit 1
  test "$(git hash-object "$W/09_eight_site_spinup500.sh")" = "65084885323060329e84b9ac2155463c12885160" || exit 1
  python3 -B -c 'import ast,sys;ast.parse(open(sys.argv[1],encoding="utf-8").read());print("SYNTAX PASS")' "$W/100_GLE_CIME_DATM_stream_contract_readonly.py" || exit 1
  SCRIPT="$W/100_GLE_CIME_DATM_stream_contract_readonly.py"
  python3 -B "$SCRIPT" --self-test || exit 1
  LOG="$HOME/Batch02_Stage100_GLE_CIME_mapping.log"
  python3 -B "$SCRIPT" --audit 2>&1 | tee "$LOG"
  RC=${PIPESTATUS[0]}
  echo "STAGE100_EXIT_CODE=$RC"
  grep -E '^STAGE100 (GLE FIELD/TIME CHECK PASS|HISTORICAL_CIME_MAPPING|SOURCE_GF_GUY_CASE|CIME_CLOCK_HOLD|GLE CIME FIELD PROPOSAL PASS|REPORT|REMAINING HOLD)' "$LOG" | tail -25
)
```

An `EXIT_CODE=0` with `STAGE100 GLE CIME FIELD PROPOSAL PASS` establishes ONLY provenance and layout of the 16-year source. Actual CIME acceptance, clock/offset and site PFT/footprint require separate trial.
