# Stage94 user final science decision → Stage95 ten-site versioned forcing/NC and Post-v5

Date: 26 October 2026.

## Operator decision

The user explicitly APPROVED the three exact US-ICt original-QC0 VPD source-change episodes that Stage94 left HOLD: 2016-05-21 15:30 through 2016-05-23 10:30 **87 halfhours** and the isolated original-QC0 VPD values on 2008-08-07 19:00 and 2008-09-18 12:30 **1+1**. These are approval of the **EXISTING Stage92 independently checked numerical candidates**, not permission to remove tower-QC labels, impute new times/values, or activate model meteorology. Stage94 previously authorized 27 other events / 33 original QC0 source-variable changes under the user's explicit neighbor/ERA/physics criteria; therefore **30 episodes / 122 QC0 variable modifications now have operator conditional approval**.

Special US-Ho1 science HOLD stays: the prior original 2000-12-27 08:00 and 08:30 temperatures are **-15.7 C, -15.1 C**, not near zero, so the user's conditional 09:00 ERA temperature replacement does NOT apply. Original 09:00 -15.4 C QC1 → 09:30 3.346 C QC2 source transition +18.746 C remains, as do all original non-QC0 T source provenance flags. New NetCDF are not declared production approved until these, native site time-zone/interval phase, sensor ZBOT, site surface/PFT/landunit and actual CIME DATM/CDEPS checks are resolved.

## Stage95 executable implementation

[Stage95 driver](../scripts/stage95/95_build_versioned_operator_approved_10site_forcing_nc_postv5.py) pinned Git commit `f7d42ef5cecfc847f1436b3626b71e23e1920b62`, blob `d34d08538c35fb84454077ca7d7ada55c4517922` does all following:
- Check the actual original Stage93 report SHA, Stage94 signed decision CSV hashes and explicit three precise US-ICt source events, yielding **122 source-variable / 30 episode decisions**.
- Run source-pinned Stage93 original `verify_inputs()`: all 10 original FLUXNET + ERA pairs, **all 215 original NC file SHA**, selected Stage87/92 forcing source, original QA source events, and original holds.
- Reuse (and SHA verify) Stage09 uniform Post-v5 and Stage07 original independent numeric/provenance audit for each versioned forcing.
- Copy all **ten** existing, numerically reconciled Stage87/92 forcing CSVs to a **new unique version directory**, unchanged value-for-value, with their original QC/event/status proof. Because all QC0 candidate values were already in those CSVs, **no new unverified replacement values are invented**. For each of the 122 approved original QC0 changes, validate the selected exact native timestamp and candidate value in the versioned CSV to ±0.00002 of the rounded original Stage93 report.
- Re-run independent original-to-event-ledger auditing, uniform Post-v5 physical/extreme/source switch checks, and regenerate **215 new NOLEAP annual NetCDF** via the original Stage87 pinned writer, rather than hard-linking the old NC. Independently read back and numerical-field-compare every generated year and every CF/DATM meteorology field to its original previously hashed technical preview. NC record the original user QC0 decisions but retain `science_approval=FALSE_TECHNICAL_PREVIEW_ONLY`.
- Make new unactivated stream text templates, versioned source/provenance decision ledger, per-site numeric/annual extreme reports, final source SHA receipts and a separate **science HOLD marker that stays even after complete build**. No Slurm jobs; never mutate original sources, existing 215 technical preview NC, current CIME case/DATM, or source surface files.
- If an individual site fails, process remaining sites, keep `INCOMPLETE_DO_NOT_USE`, output a per-site progress report. Source integrity errors before starting deliberately fail closed.

On actual IRIDIS6 execution, Stage95 may successfully produce **versioned candidate 10/10 sites and 215/215 new annual NC**, but this is NOT the same as model approval. These steps have been committed and code-pin verified; **operator execution/result has not yet been received**.

## One-paste IRIDIS6 command

Run in `clm_fates_env`, using raw GitHub `curl` downloads, no `git pull` or `python -m py_compile` writing into a shared `/tmp/__pycache__`.

```bash
(
  set +e
  C95="f7d42ef5cecfc847f1436b3626b71e23e1920b62"
  C09="6c8888ff3293d5fc0ab15ada7e79bbfc720c7251"
  C94="edf1071e27a76c2cb3f60b740e4ed9b8d4d7415f"
  C87="7e4c3cd653289872d09f7a6a71e75fa35a258c2b"
  REL="examples/AmeriFlux_MultiSite_10_Batch02/scripts"
  W="$HOME/Batch02_stage95_operator_approved"
  mkdir -p "$W"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  curl -fLsS --retry 3 "$RAW/$C95/$REL/stage95/95_build_versioned_operator_approved_10site_forcing_nc_postv5.py" -o "$W/95_build_versioned_operator_approved_10site_forcing_nc_postv5.py" || exit 1
  curl -fLsS --retry 3 "$RAW/$C09/$REL/stage93/93_ten_site_postv5_and_manual_decision_priority.py" -o "$W/93_ten_site_postv5_and_manual_decision_priority.py" || exit 1
  curl -fLsS --retry 3 "$RAW/$C94/$REL/stage94/94_qc0_final_operator_decision_table.py" -o "$W/94_qc0_final_operator_decision_table.py" || exit 1
  curl -fLsS --retry 3 "$RAW/$C09/$REL/stage09/09_post_qcv5_batch02.py" -o "$W/09_post_qcv5_batch02.py" || exit 1
  curl -fLsS --retry 3 "$RAW/$C87/$REL/stage87/87_build_five_verified_Stage07_DATM_noleap_technical_preview.py" -o "$W/87_build_five_verified_Stage07_DATM_noleap_technical_preview.py" || exit 1

  test "$(git hash-object "$W/95_build_versioned_operator_approved_10site_forcing_nc_postv5.py")" = "d34d08538c35fb84454077ca7d7ada55c4517922" || exit 1
  test "$(git hash-object "$W/93_ten_site_postv5_and_manual_decision_priority.py")" = "1d06c2b68d1ebc7f108be32abd358771dc8e9326" || exit 1
  test "$(git hash-object "$W/94_qc0_final_operator_decision_table.py")" = "9193bc91a92e27b0deca87030697ae222919b65a" || exit 1
  test "$(git hash-object "$W/09_post_qcv5_batch02.py")" = "b2353089ff15b95b6a25c5c0e2fcf4e7be2671c7" || exit 1
  test "$(git hash-object "$W/87_build_five_verified_Stage07_DATM_noleap_technical_preview.py")" = "4f62ba03f52b41b98d7b6db3e89af2bf10bee8a1" || exit 1

  python3 -B -c 'import ast,sys;[ast.parse(open(f,encoding="utf-8").read()) for f in sys.argv[1:]];print("ALL 5 SYNTAX PASS")' "$W"/*.py || exit 1
  SCRIPT="$W/95_build_versioned_operator_approved_10site_forcing_nc_postv5.py"
  python3 -B "$SCRIPT" --self-test || exit 1

  LOG="$HOME/Batch02_Stage95_final_versioned_215NC.log"
  python3 -B "$SCRIPT" --build 2>&1 | tee "$LOG"
  RC=${PIPESTATUS[0]}
  echo "STAGE95_EXIT_CODE=$RC"
  grep -E 'STAGE95 USER DECISIONS|STAGE95 SITE PASS|STAGE95 SITE HOLD/FAIL|STAGE95 VERSIONED|STAGE95 PARTIAL|STAGE95 REPORT|STAGE95 SCIENCE HOLD' "$LOG" | tail -30
)
```

Successful summary is `STAGE95 VERSIONED 10 SITE POST-V5 PASS | 122 USER QC0 APPROVED; 215 REGENERATED NOLEAP NC VERIFIED`. It still prints `STAGE95 SCIENCE HOLD` and **does not submit any case**.

After operator execution: first determine exact remaining Ho1 December source/ERA provenance and site clock/interval/ZBOT; then finalize validated DATM mapping/smoke test. Do not spin up before scientific validation.
