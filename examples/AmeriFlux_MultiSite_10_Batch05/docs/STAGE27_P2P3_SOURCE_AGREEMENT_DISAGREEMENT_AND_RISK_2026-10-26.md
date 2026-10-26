# AmeriFlux Batch05 — Stage26 IRIDIS6 scientific candidate results and Stage27 decision prioritization

## Stage26 confirmed operator execution (2026-10-26)

User-provided Stage26 operator log:

```text
SOURCE VERIFIED
STAGE26 SELF-TEST PASS
STAGE26 SUCCESS | 1574 P2/P3 original native HH; zero forcing approvals
STAGE26 DISTINCT_SOURCE_OPTIONS {"ORIGINAL_RH_WITH_SELECTED_T":5, "SOURCE_ERA_IMPLIED_ACTUAL_VAPOR_PRESSURE_WITH_SELECTED_T":1459, "SOURCE_MDS_RH_WITH_SELECTED_T":551, "SOURCE_PROCESSED_ERA_RH_WITH_SELECTED_T":1574}
STAGE26 MUTUALLY_EXCLUSIVE_SUBGROUPS {"DUAL_SOURCE_MDS_AND_ERA_RH_OPTIONS_DIFFERENCE_CHECK":546, "NATIVE_ORIGINAL_RH_EXISTS_CHECK_SENSOR_PROVENANCE":5, "ONLY_PROCESSED_ERA_RH_SOURCE_OPTION_OR_ERA_E_SHADOW":1023}
STAGE26 SOURCE_HH_WITH_SOME_PHYSICAL_CANDIDATE 1574 NO_SOURCE_PHYSICAL_CANDIDATE 0
STAGE26_REPORTS=/home/ly3n24/ameriflux_batch05_stage26/science_candidates_20261026T035557Z_1589604
```

Ten-site original P2/P3 unapproved half-hour distribution remains US-Vcp 626, US-Wjs 401, US-Vcm 362, US-Var 62, US-WCr 62, US-UMB 23, US-Wkg 22, US-UMd 15, US-Whs 1, US-UiD 0. Original tower-selected TA differs from **source processed** ERA TA by >5°C in **372 of 1,574 HH** (US-Vcp 211, US-Wjs 76, US-Vcm 59, US-Wkg 10, US-UMd 6, US-WCr 5, US-Var 4, US-Whs 1). All 1,574 source ERA RH values are mathematically bounded, **not independently measured or validated**. The separate ERA actual-vapor-pressure option is mathematically possible for 1,459 HH, while it is unavailable/nonphysical for 115 when paired to selected tower TA. Four option counts OVERLAP.

Research-only Stage26 directory:
`/home/ly3n24/ameriflux_batch05_stage26/science_candidates_20261026T035557Z_1589604`

**Unchanged scientific authorization:** 166 Stage24 approved versioned native-time overlay records, including 130 original P1 and 36 context/edge HH. Forty-six original P1 half-hours remain human HOLD. Two saturation platforms (10 original HH) unapproved. All 1,574 original P2/P3 half-hours remain scientifically unapproved.

## Stage27: MDS–ERA disagreement & original episode risk ranking

[Exact Stage27 original HH/episode discrepancy evaluator](../scripts/stage27/27_compare_p2p3_mds_era_and_temperature_risk_readonly.py)

The Stage27 script works only from Stage26 scientific candidate CSVs, Stage25 original P2/P3 source worklist and Stage24 original 166 versioned overlay/HOLD. It SHA-verifies the Stage26 evidence chain from Stage25/Stage24, requires precisely 1,574 original P2/P3 native half-hours, precisely 3,589 *overlapping* candidate records and 483 original P2/P3 episodes. Everything remains **research only**.

**Risk screen thresholds, not science approval criteria:**
- `DUAL_AGREES_LE5PP_REVIEW`: paired original-source MDS RH vs processed-source ERA RH differ by ≤5 percentage points;
- `DUAL_DISAGREES_5_TO20PP`: difference >5 through 20 pp;
- `DUAL_CONFLICT_GT20PP`: difference >20 pp;
- `NATIVE_RH_PRESENT_PROVENANCE`: 5 HH with original source RH available (even if other options exist);
- `ERA_ONLY_SOURCE_REFERENCE_REQUIRED`: 1,023 HH without original RH/MDS RH (source processed ERA RH and possibly its vapor-pressure shadow are not independent checks);
- additional cross-cutting flags: selected tower TA vs source ERA TA >5°C; ERA RH conserved vs ERA actual vapor pressure conserved VPD difference >2 hPa; reconstructed source ERA VPD vs original selected VPD absolute difference >5 or >10 hPa; source-ERA implied water vapor pressure unsuitable when paired to selected TA.

Outputs:
- `stage27_ALL1574_paired_source_comparisons_and_risks.csv` all native anomaly HH and paired differences/flags.
- `stage27_ALL483_original_P2P3_episode_science_risk.csv` original contiguous episode ranks based on number/magnitude of scientific conflicts.
- `stage27_ALL10_site_science_conflict_status.csv` exact site statistics.
- `stage27_DUAL_AGREEMENT_REVIEW_ONLY_NOT_APPROVED.csv` the MDS/ERA-concordant subset, **still pending independent checks**.
- `stage27_EXTERNAL_VALIDATION_AND_CONFLICT_QUEUE.csv` science evidence workload by exact site/time.
- `STAGE27_DECISION_BRIEF_AND_EPISODE_PRIORITIES.md` risk counts, top 20 episodes and next decisions.
- `stage27_summary.json` hashes, source/forcing/Slurm writes false.

**Run on IRIDIS6** (Stage16–26 do not need to be rerun):

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage27"
  COMMIT="42b98a7caf199d0c64b1f37dfbf6012cef1bd0ec"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/27_compare_p2p3_mds_era_and_temperature_risk_readonly.py"
  D26="$HOME/ameriflux_batch05_stage26/science_candidates_20261026T035557Z_1589604"
  D25="$HOME/ameriflux_batch05_stage25/crosswalk_20261026T034622Z_1628022"
  D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage27/27_compare_p2p3_mds_era_and_temperature_risk_readonly.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "5c3fda6db1ea9523da09eaa55ad5ee985f7076ca"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/source_comparison_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage26-dir "$D26" \
    --stage25-dir "$D25" --stage24-dir "$D24" \
    --out "$OUT" 2>&1 | tee "$BASE/stage27.log"
  echo "STAGE27_REPORTS=$OUT"
  cat "$OUT/STAGE27_DECISION_BRIEF_AND_EPISODE_PRIORITIES.md"
)
```

**Operator Stage27 execution not yet confirmed**; no promised MDS–ERA agreement or episode ranking counts are asserted until the exact original operator data are screened.

## Scientific gate for future work

If original source MDS and processed ERA reconstructions agree, that supports a targeted review with external reference data; agreement alone does **not** demonstrate correctness or authorize a replacement. If they conflict, check original source QC, instrument data provenance and seasonal context. Both preserving processed source ERA RH and preserving its original vapor pressure involve distinct assumptions when replacing selected tower T. Real site latitude/longitude/elevation and original native clock-to-UTC offset verification are prerequisites before independent ERA5-Land 2-m temperature and dewpoint comparisons. The 46 manual P1 HOLD and 10 suspect 100%/99.46% RH platforms remain unchanged. No production DATM forcing or model job has been approved.
