# Batch02 Stage92 operator PASS → Stage93 actual ten-site Post-v5 / source QC0 manual triage

Date 26 Oct 2026. Actual IRIDIS6 Stage92 operator confirms `FIVE SITE CANDIDATE PASS`, 5 independent candidate forcing CSV, 98 NEW annual NOLEAP NC technical previews. Together with Stage87 previously-built five-site 117 yearly NC technical previews, exactly 10 sites / 215 technical annual NetCDF produced. **No scientific production DATM signoff**. Stage92 2 original source ERA5 RH >100% (US-Ho1 2011-04-20 13:00: 100.002878%; 2012-03-14 13:00: 100.000448%) were correctly not used as external RH patches; residual humidity was handled by separate engine checks, final numeric audits passed. Do not conflate source RH candidate HOLD with impossible final forcing.

## Urgent true human review scope

Stage87 first five: BZS 1 original QC0 variable edit; CMW 2; Ha1 2; Ho2 19; Ho3 0 = 24.
Stage92 five: EML 3; GLE 0; Ho1 5; ICh 0; ICt 90 = 98.
**Total = 122 changed native source QC0 variable records**. This number is **not** the number of flagged extreme records, and must not be equated with 15998 Ho1 Stage92 review flags. Prior Ho1 2000 17,294 QC0 source T preserved (17246 after NOLEAP removing measured 48 Feb29 half-hours); 1,068 manually accepted humidity-only corrections remain retained and must not be re-reviewed. Ho1 Dec27 09:00 QC1 -15.4 °C → 09:30 QC2/ERA 3.346 °C = +18.746 °C source jump; keep exact-source provenance and don't declare tower-observed until temperature time-series source transition resolved.

## Stage93 integrated evidence

[Stage93 script](../scripts/stage93/93_ten_site_postv5_and_manual_decision_priority.py) commit `6c8888ff3293d5fc0ab15ada7e79bbfc720c7251`, Git blob `1d06c2b68d1ebc7f108be32abd358771dc8e9326`.
It verifies exact old and new manifests, raw site paired ERA hashes, every one of the 215 technical NC file SHA, original source/forcings; uses the original Stage09 uniform `science_review` routine (pinned Git blob `b2353089ff15b95b6a25c5c0e2fcf4e7be2671c7`) on each of the 10 actual final-forcing candidate files. It checks final RH and QBOT numerical physics, original QC0 changed events, source switching, jumps, and extreme counts, and directly inspects raw original ±1 native source records and VPD-derived RH for the exact 122 records. It groups all 122 source QC0 changes into per-site/per-variable 30/60-minute continuous episodes for rapid human decisions. It separately prints original and selected Ho1 Dec27 and Jan01 source boundary, and does not mark any production DATM science approved.

Stage93 files (only inside a new unique `reports/stage93_*` directory): `ten_site_postv5_extreme_summary.csv`, `all_122_QC0_original_source_candidate_nearest_neighbors.csv`, `QC0_human_review_priority_episodes.csv`, `US-Ho1_2000_temperature_QC_transition_boundary.csv`, `annual_postv5_extreme_counts.csv`, `site_failures.csv`, checksum manifest. Source/forcing/NC/CIME/Slurm inputs untouched.

## IRIDIS6 one paste, nonfatal to login session

```bash
(
  set +e
  REL="examples/AmeriFlux_MultiSite_10_Batch02/scripts"
  COMMIT="6c8888ff3293d5fc0ab15ada7e79bbfc720c7251"
  BLOB93="1d06c2b68d1ebc7f108be32abd358771dc8e9326"
  BLOB09="b2353089ff15b95b6a25c5c0e2fcf4e7be2671c7"
  W="$HOME/Batch02_stage93_manual"
  mkdir -p "$W"
  BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  curl -fLsS --retry 3 "$BASE/$COMMIT/$REL/stage93/93_ten_site_postv5_and_manual_decision_priority.py" -o "$W/93_ten_site_postv5_and_manual_decision_priority.py" || exit 1
  curl -fLsS --retry 3 "$BASE/$COMMIT/$REL/stage09/09_post_qcv5_batch02.py" -o "$W/09_post_qcv5_batch02.py" || exit 1
  test "$(git hash-object "$W/93_ten_site_postv5_and_manual_decision_priority.py")" = "$BLOB93" || exit 1
  test "$(git hash-object "$W/09_post_qcv5_batch02.py")" = "$BLOB09" || exit 1
  python3 -B -c 'import ast,sys;[ast.parse(open(p,encoding="utf8").read()) for p in sys.argv[1:]];print("SYNTAX PASS 2/2")' "$W"/*.py || exit 1
  python3 -B "$W/93_ten_site_postv5_and_manual_decision_priority.py" --self-test || exit 1
  LOG="$HOME/Batch02_stage93_manual.log"
  python3 -B "$W/93_ten_site_postv5_and_manual_decision_priority.py" --audit 2>&1 | tee "$LOG"
  RC=${PIPESTATUS[0]}
  echo "STAGE93_EXIT_CODE=$RC"
  grep -E 'REVIEW PASS|REVIEW FAILURE|HUMAN_EPISODE|HUMAN_QC0_BY_SITE|HUMAN_EPISODES|STAGE93 TEN SITE|STAGE93 PARTIAL|STAGE93 REPORT' "$LOG" | tail -70
)
```
Return priority episodes and/or `QC0_human_review_priority_episodes.csv` result to generate the final manual scientist operator decision. The exact pipeline is **scientific audit**, not itself an approval or forcing patch.
