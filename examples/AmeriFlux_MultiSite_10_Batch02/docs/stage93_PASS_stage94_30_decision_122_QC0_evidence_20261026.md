# Stage93 operator PASS → Stage94 human scientific disposition (26 October 2026)

## Confirmed completed status

Actual IRIDIS6 original Stage93 report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage93_ten_site_postv5_QC0_manual_triage_20261026T025946Z_97c41d3b`.
`STAGE93 TEN SITE POSTV5 AUDIT PASS` and `EXIT_CODE=0`.
- All original paired sources and complete current 10-site forcing CSV checked.
- 215 annual technical-preview NetCDF SHA checked.
- All 10 passed uniform original Stage09 Post-v5 numerical/physics QC.
- Original QC0 edits: **122**, exactly **30** contiguous site-variable episodes. No full scientific approval (critical). There were 121,296 *flagged timestamps* spanning all QC/extremes, not 121,296 confirmed errors.
- High-priority 8 isolated original QC0 T edits: BZS 1 (22.4365 °C), CMW 1 (20.532 °C), Ho1 5 (~18.45–22.49 °C), ICt 1 (21.718 °C).
- ICt original QC0 VPD 87 native half-hours 2016-05-21 15:30 through 2016-05-23 10:30 (one continuous 43.5h): **MUST see original VPD/RH and source/ERA time context before overwriting 87 measured-coded readings**.
- Ho1 original 2000 December 27 QC1 source TA_F -15.4 °C to QC2/ERA-coded 3.346 °C 30 min later: 18.746 °C source transition, not a new Stage93 QC0 correction, and NOT scientifically resolved by numerical PASS.
- Two independent Stage74 source ERA humidity candidates at Ho1 2011-04-20 13:00 RH 100.002878% and 2012-03-14 13:00 RH 100.000448% skipped as external candidates; complete selected model humidity remained physically valid via separate source algorithm.

## Actual Stage94 scientific evidence printer

[Stage94 exact source](../scripts/stage94/94_qc0_final_operator_decision_table.py) commit `7a075852450b4d80215594c00f4c0c6beab78a3d`, Git blob `6f5110fd68a9d22a35f535f7d2692be7b842b91c`.

Stage94 checks SHA of all immutable Stage93 CSV, reconciles exactly 122 source QC0 records into 30 consecutive episodes, displays per-event original/candidate/ERA ranges, previous and next original native neighbors, and original implied source RH, plus 87-HH ICt subset and original/selected Ho1 QC-source transition. It proposes operator recommendations only for physically/neighbor/ERA-supported cases, with `production_approved=NO` and default `operator_choice=HOLD`. **No correction approval is made by Stage94.**

Use one paste:
```bash
(
  set +e
  COMMIT="7a075852450b4d80215594c00f4c0c6beab78a3d"
  BLOB="6f5110fd68a9d22a35f535f7d2692be7b842b91c"
  REL="examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage94/94_qc0_final_operator_decision_table.py"
  SCRIPT="$HOME/Batch02_stage94_operator.py"
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL" \
    -o "$SCRIPT" || exit 1
  test "$(git hash-object "$SCRIPT")" = "$BLOB" || exit 1
  python3 -B -c 'import ast,sys;ast.parse(open(sys.argv[1],encoding="utf8").read());print("STAGE94 SYNTAX PASS")' "$SCRIPT" || exit 1
  python3 -B "$SCRIPT" --self-test || exit 1
  LOG="$HOME/Batch02_stage94_operator.log"
  python3 -B "$SCRIPT" --audit 2>&1 | tee "$LOG"
  RC=${PIPESTATUS[0]}
  echo "STAGE94_EXIT_CODE=$RC"
  grep -E '^REVIEW |^ICt_87HH_SAMPLE |^HO1_BOUNDARY |STAGE94 REVIEW CATEGORY|STAGE94 REPORT PASS|STAGE94 REPORT |ORIGINAL SOURCE PASS' "$LOG" | tail -90
)
```

Three new CSVs in an isolated report folder:
`30_QC0_episodes_operator_DECISION_TEMPLATE.csv`,
`manual_required_priority.csv`,
`strong_source_evidence_review.csv`.
Allowed operator decisions for each episode: `APPROVE_CANDIDATE`, `KEEP_ORIGINAL`, `USE_VERIFIED_ALTERNATIVE`, `HOLD`. The operator may approve groups by scientifically explicit common criteria rather than hand-authoring 30 CSV choices; preserve the source/time/variable ledger. Future Stage95 should produce versioned formal DATM forcing only after these scientific choices, the Ho1 original source T context, and time/ZBOT/CIME contracts have been checked.

**Do not activate the current Stage87/92 stream templates or spin up yet**. These are numerical previews, and Stage94 only prepares decisions.
