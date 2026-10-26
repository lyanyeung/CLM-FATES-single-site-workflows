# AmeriFlux Batch05 — Stage35 executed / Stage36 first **isolated** trial with original source boundary QC

## Actual Stage35 operator results (26 October 2026)

```text
SOURCE VERIFIED
STAGE35 SELF-TEST PASS
STAGE35 SUCCESS | 429 original native HH; P1 HOLD 27; RH platforms 10; P2P3 392; science approvals 0
STAGE35 REVIEW_LANES {
 "P1_HOLD_GRID_REFERENCE_REVIEW":27,
 "P2P3_REANALYSIS_ERA_CONCORDANT_LOW_T_DIFF":251,
 "P2P3_REANALYSIS_ERA_CONCORDANT_LARGE_T_OR_SOURCE_CHANGE":77,
 "P2P3_SOURCE_MDS_MORE_CONCORDANT_REVIEW":11,
 "P2P3_REANALYSIS_SOURCE_CONFLICT_OR_UNCERTAIN":53,
 "SUSPECT_SATURATED_RH_PLATFORM_REVIEW":10
}
STAGE35 EPISODES 91
STAGE35_REPORTS=/home/ly3n24/ameriflux_batch05_stage35/science_VPD_trial_20261026T132821Z_715715
```

The **251 P2/P3 native half-hours** are *not* approvals. They passed three screening checks: processed source ERA and newly downloaded ERA5-Land RH within 10 RH percentage points, original tower vs ERA5-Land temperature within 5°C, and fresh-grid-RH transported-to-tower-T VPD vs original native source VPD within 5 hPa. These are **heuristics, not scientifically established accuracy of humidity sensors**. Freshly downloaded ERA5-Land is reanalysis-related, as is source processed ERA, so their agreement is not statistically independent field confirmation.

The other 141 externally matched P2/P3 original HH are not in the first research trial: 77 ERA-concordant but large T or VPD change, 11 MDS-preferred vs source ERA, 53 uncertain/conflicting. The remaining 1182 original P2/P3 HH were **not externally referenced in Stage34**. Original 46 P1 human HOLD (H01 19 and four other events 27), both 10-HH RH saturation platforms and existing 166 versioned Stage24-approved overlay remain untouched.

## Stage36 focus: evidence directly from ORIGINAL source ZIPs

[Stage36 isolated 251 native trial and true original FLUXMET ±30 minute science boundary scanner](../scripts/stage36/36_build_251_isolated_ERA_RH_trial_and_check_original_FLUXMET_boundaries.py)

Pinned GitHub commit `7a6f26a9fc5e587ce06aae139529ba3f276060c6`; Git blob `fda0ba51717d1e0094e4a8e5109695f890884f63`.

Stage36 is a read-only screening script:
1. Requires exactly 429 original Stage35 matched rows, 392 original P2/P3, and **251** Stage35 favourable candidate native times, with exact source Stage27 original 1574 / 483 episodes, Stage24 **166 approved / 46 manual HOLD / ten saturation platforms**. Protects all source files by SHA.
2. Reads the actual operator-pinned **original original AmeriFlux FLUXNET source ZIPs** under `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/packages/` (read-only); expected original ZIP SHA256 values from the user-confirmed Stage29 original BIF audit:
   - US-Vcp: `3cae4d7e148dba9ac5e1850cbfb41c1cda80ff0420a352709be324b187162329`;
   - US-Wjs: `75c7132fe8695a61f32dd4ad64235e97dccc786fcea75eb09a37d4ac1ea9ccda`;
   - US-Vcm: `2f336f2ade57f39ec575b0f3e7186ba2a36e3242d3fa5212cac20d474f3e604c` (only if a selected native time happens to be Vcm).
3. For each of 251 native original times, compares original source `TA_F`, `VPD_F`, `TA_F_QC`, `VPD_F_QC` to Stage35/Stage27; any science source mismatch STOPS. It never changes original source sensor QC0: flags native source QC0 measured VPD as protected for investigator review.
4. Creates *hypothetical* native VPD trial `e_sat_water(T_tower)*(1-RH_processed_source_ERA/100)`, with original tower T unchanged, alongside the alternative `e_sat_water(T_tower)*(1-RH_fresh_ERA5Land/100)`. Each is physically bounded but not independently source-validated.
5. Reads the **true original preceding and following native source half-hours from the original ZIP**, 2 comparisons per candidate (**502** expected). If a neighbor is also in this research trial, compare both trial values; if in the existing **166 approved**, use the existing overlay value *for diagnostic only*; if in a P1 HOLD, another unapproved P2/P3, or RH saturation platform, explicitly flag this and keep its source VPD for diagnostic, **not as validated truth**.
6. Screens boundary VPD differences >2/>4 hPa, suspect neighbor RH below 10% (or >100%) and original QC2/other nonmeasured source provenance. Flags partial original anomalous episodes where only some source-native half-hours were Stage35 favourable candidates.
7. Groups trials into their exact original Stage27 episodes, producing compact episode-level investigator review decisions rather than requesting individual 251 permissions. None of the categories authorizes production forcing.

Source publication is different from Stage24 approved overlay: Stage36 *writes a new file named `TRIAL_ONLY`*, not an approved forcing overlay or modified source package. No CIME, DATM or Slurm work.

Outputs:
- `stage36_251_ISOLATED_TRIAL_ONLY_source_ERA_RH_at_original_T.csv`
- `stage36_502_ORIGINAL_ZIP_NATIVE_NEIGHBOR_VPD_QC_TRANSITIONS.csv`
- `stage36_ALL_EPISODE_RISK_AND_TRIAL_DECISION_MATRIX.csv`
- `stage36_manifest.json`
- `STAGE36_ORIGINAL_FLUXMET_BOUNDARY_AND_TRIAL_SCIENCE_REPORT.md`

### One-call IRIDIS6

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage36"
  COMMIT="7a6f26a9fc5e587ce06aae139529ba3f276060c6"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/36_build_251_isolated_ERA_RH_trial_and_check_original_FLUXMET_boundaries.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage36/36_build_251_isolated_ERA_RH_trial_and_check_original_FLUXMET_boundaries.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "fda0ba51717d1e0094e4a8e5109695f890884f63"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/isolated_251_trial_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" \
    --stage35-dir "$HOME/ameriflux_batch05_stage35/science_VPD_trial_20261026T132821Z_715715" \
    --stage27-dir "$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604" \
    --stage24-dir "$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604" \
    --sites-root "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE" \
    --out "$OUT" 2>&1 | tee "$BASE/stage36.log"
  echo "STAGE36_REPORTS=$OUT"
  cat "$OUT/STAGE36_ORIGINAL_FLUXMET_BOUNDARY_AND_TRIAL_SCIENCE_REPORT.md"
)
```

**Stage36 code is on GitHub; its IRIDIS6 execution is not yet confirmed.** Scientific input evidence and source time ranges were operator-confirmed in Stages27/29/34/35. If the exact ZIP SHA, source FLUXMET HH time coverage or native original TA/VPD differ, Stage36 stops *rather than creating falsely validated test data*. No automatic authorization for any new source or model forcing.
