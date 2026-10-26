# AmeriFlux Batch05 — Stage38 fast completion effort: small sites + full original US-Vcp episodes

## Operator Stage37 actual result (26 October 2026)

```text
SOURCE VERIFIED
STAGE37 SELF-TEST PASS
STAGE37 SUCCESS | original251 vs hypothetical251; 65 original episodes; 81 contiguous source segments; 162 UNIQUE external native edges
STAGE37 ACTUAL_OLD_VS_HYPOTHETICAL_TRIAL {
 "original_external_jump_gt2":25,
 "trial_external_jump_gt2":94,
 "original_external_jump_gt4":1,
 "trial_external_jump_gt4":21,
 "newly_crossed_2hPa":84,
 "newly_crossed_4hPa":21,
 "improved_abs_jump_by_at_least0_5hPa":25,
 "worsened_abs_jump_by_gt0_5hPa":123,
 "neighbor_original_QC2_or_unmeasured":162,
 "neighbor_still_unapproved_P2P3":46,
 "neighbor_implied_RH_below10_or_unphysical":135
}
STAGE37 EPISODE_LANES {
 "NEW_GT2_AT_EVENT_BOUNDARY":31,
 "NEW_GT4_AT_EVENT_BOUNDARY":20,
 "SOURCE_NEIGHBOR_QC_OR_OTHER_P2P3_UNRESOLVED":14
}
STAGE37 SEGMENT_LANES {
 "ALREADY_SUSPICIOUS_OR_UNAPPROVED_NEIGHBOR_REVIEW":14,
 "NEW_OR_WORSENED_GT2_BOUNDARY_REVIEW":46,
 "NEW_OR_WORSENED_GT4_BOUNDARY_REVIEW":21
}
STAGE37_REPORTS=/home/ly3n24/ameriflux_batch05_stage37/boundary_before_after_20261026T170105Z_1109806
```

**Interpretation:** selecting the apparently favourable Stage35 source-ERA/RH vs ERA5-Land low-difference 251 P2/P3 native half-hours directly is a poor scientific forcing method: 21 newly introduced >4hPa native boundary discontinuities and 84 newly introduced >2hPa transitions, against only one original >4hPa edge. All 162 true external neighbors are QC2/other non-QC0, including 46 other unapproved P2/P3; 135 have original inferred RH below10% or unphysical. **Do not approve the 251 sparse changes.** The correct next science test is *complete original source event* reconstruction and independent original-source QC, not simply lowering arbitrary threshold.

## Previous answer corrected: exact ten-site cohort includes US-Wkg

Stage27 code's exact ten: `US-UiD, US-UMB, US-UMd, US-Var, US-Vcm, US-Vcp, US-WCr, US-Whs, US-Wjs, US-Wkg`. Earlier chat summary omitted **US-Wkg** and therefore should not be treated as a confirmed ten-site pass/remaining-state report. Stage38 reads **actual exact Stage27 site summary CSV and 1,574 native P2/P3 CSV** on IRIDIS6 and prints current site counts and case-level evidence. A site with zero remaining P2/P3 does **not** imply full forcing/meteorology/model pass.

## Next real work: Stage38 GitHub script

[Stage38 original ZIP source + full original episode method science trials](../scripts/stage38/38_fast_small_site_closeout_and_Vcp_full_episode_method_trials_readonly.py)

Pinned verified current script at `cd56aae11582d1369d8047a9dfad3aa65acc0ad4`, Git blob SHA `cc3fa3cfc3c4b8196dda6540c72da8c56e6a77f6`.

Science workstreams:

**A. Smaller sites:** US-UiD, US-UMB, US-UMd, US-Var, US-WCr, US-Whs, **US-Wkg**. Read original AmeriFlux FLUXNET_HH ZIP in site forcing package; verify each Stage27 anomalous original native T/VPD/QC directly and record original ZIP SHA256 for source reproducibility. For each original P2/P3 episode, generate a source-ERA-RH-to-original-T and source-MDS-RH-to-original-T research-only *full-event* trial. Check full 30min contiguous source-event coverage, no original QC0 VPD, correct humidity physical range and boundary discontinuities before/after. Report *real site-level remaining HH/episode counts* instead of citing previously incomplete user memory. A small site is eligible for expedited science review, never automatically forcing-approved.

**B. US-Vcp:** all **65 original Stage37 flagged episodes** read as *full original source Stage27 episodes*, not partial 251 favourable HH. Compare processed source ERA RH, MDS RH, and independently fetched ERA5-Land RH **only when the external reference covers EVERY original native anomalous HH in an episode**. For each option, reject missing RH, original QC0 measured VPD, non-contiguous episode source times and candidate-created >2/>4 hPa within-event or native pre/post discontinuities. Compare full-episode candidate numeric screening against Stage37 original sparse 251 risk counts. All references remain external gridded reanalysis, not an in-situ measurement.

**Constraints:** NO source ZIP edits, no newly-approved forcing overlay, no changes to Stage24 166 approved RH/VPD, 46 manual P1 HOLD, 1,574 original unapproved P2/P3, ten RH platform suspicious HH or DATM/CIME/Slurm.

## IRIDIS6 single copyable Bash command

```bash
set -euo pipefail
BASE="$HOME/ameriflux_batch05_stage38"
mkdir -p "$BASE"

COMMIT="cd56aae11582d1369d8047a9dfad3aa65acc0ad4"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
FILE="examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage38/38_fast_small_site_closeout_and_Vcp_full_episode_method_trials_readonly.py"
SCRIPT="$BASE/stage38.py"

curl -fLsS --retry 3 "$RAW/$FILE" -o "$SCRIPT"
test "$(git hash-object "$SCRIPT")" = "cc3fa3cfc3c4b8196dda6540c72da8c56e6a77f6"
echo "SOURCE VERIFIED"
python3 -B -m py_compile "$SCRIPT"
python3 -B "$SCRIPT" --self-test

OUT="$BASE/fast_closeout_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" \
  --stage27-dir "$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604" \
  --stage24-dir "$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604" \
  --stage37-dir "$HOME/ameriflux_batch05_stage37/boundary_before_after_20261026T170105Z_1109806" \
  --stage35-dir "$HOME/ameriflux_batch05_stage35/science_VPD_trial_20261026T132821Z_715715" \
  --sites-root "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE" \
  --out "$OUT" 2>&1 | tee "$BASE/stage38.log"

echo "STAGE38_REPORTS=$OUT"
cat "$OUT/STAGE38_SMALL_SITE_AND_FULL_VCP_EVENT_CLOSURE.md"
```

Output `stage38_TEN_SITE_PROVENANCE_AND_REMAINING_REPAIR_GATES.csv`: exact ten-site current numbers, P2/P3 original source (do not double count separate P1/manual/plateau); `stage38_ALL_SMALL_SITE_AND_VCP_FULL_EPISODE_METHOD_TRIALS.csv` event-by-method source original science gates and VPD boundary/physical plausibility screens; `stage38_manifest.json` original input source hashes, original ZIP hashes, and no model edits.

**The Stage38 code has been added to GitHub but has not yet run on IRIDIS6**. Test `--self-test` and original source SHA; if a source path or field differs, abort/report accurately rather than force a scientific fix.

## Script safety self-test strengthened

The pinned Stage38 revision runs synthetic original two-half-hour site episode source RH trial versus both original neighboring VPD records and checks that a source-original QC0 VPD makes the entire event a `QC0_SENSOR_PROTECTED` science gate, without any production write.

## One-click launcher (preferred)

[Stage38 one-click operator script](../scripts/stage38/run_stage38_iridis6.sh) is pinned at GitHub commit `fbd18d283d593812565eccc214900e74afe6b115`, Git blob `39589e8b0ef66b135ae7fdd97fe5702242726cf9`. It retrieves and SHA-checks Stage38 Python from its pinned commit, performs syntax/self-test/source directory checks, evaluates both original-source workflows and prints the science report. **New output** `stage38_RESEARCH_ONLY_FULL_SOURCE_EPISODE_NATIVE_RH_VPD_CANDIDATES.csv` contains physically feasible, full-coverage event-level **native half-hour RH/VPD research candidates only**: original T and QC remain intact; any source-QC0 measured VPD excludes an event from the native candidate file, and `production_forcing_authorization=NO` for every row. Even events with boundary science concerns remain labeled, not approved. The launcher's Bash run remains untested on IRIDIS6 pending operator execution.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/fbd18d283d593812565eccc214900e74afe6b115/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage38/run_stage38_iridis6.sh" -o "$HOME/run_stage38.sh"
test "$(git hash-object "$HOME/run_stage38.sh")" = "39589e8b0ef66b135ae7fdd97fe5702242726cf9"
bash "$HOME/run_stage38.sh"
```


## Stage38 US-UMB original-source archive discovery failure and repair (26 October 2026)

**Actual initial Stage38 operator attempt stopped before science calculation**:

```text
STAGE38 SOURCE VERIFIED
STAGE38 SELF-TEST PASS
ValueError: expect exactly 1 original site FLUXNET v1.3 r1 package:
 /iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-UMB/forcing/packages
```

This is a **too-strict filename/location assumption**, not proof the US-UMB data are corrupt. Original 166 Stage24 approved, P1 HOLD 46 and P2/P3 1574 remain unchanged.

**Final repaired one-click launcher**: GitHub commit `790dfb27b5a6c1c95fa73a552d5bd555a02a3d55`, blob SHA `2071292ce74b426bc2c6f25228931bcf98efae3d` at [run_stage38_iridis6.sh](../scripts/stage38/run_stage38_iridis6.sh). It pins Stage38 Python commit `60cbc5520441e90105f94c7c0843cdb477186ba5`, blob SHA `d6884f53b3a7f3eae46860862a2c3ea023a585bf`. The Python code now searches source ZIPs and extracted CSVs under each site root, inspects archive embedded original FLUXMET_HH member names rather than guessing the ZIP filename or version, and checks **every original Stage27 T/VPD/QC source half-hour** before accepting any candidate. Multiple distinct matching original source populations block that site instead of choosing arbitrarily. Missing source gives an explicit **per-site ORIGINAL_SOURCE_SITE_HOLD** and continues others; the site is never falsely reported passed. Source file and archive SHA256/path are recorded. No approved overlay or production forcing writes.

Use this **three-line retry**, not the earlier Stage38 launcher:

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/790dfb27b5a6c1c95fa73a552d5bd555a02a3d55/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage38/run_stage38_iridis6.sh" -o "$HOME/run_stage38.sh"
test "$(git hash-object "$HOME/run_stage38.sh")" = "2071292ce74b426bc2c6f25228931bcf98efae3d"
bash "$HOME/run_stage38.sh"
```

**Repair code published; operator rerun pending.** Report `STAGE38 ORIGINAL_SOURCE_SITE_HOLDS` identifies still-missing original sources without misclassifying them as passes; `STAGE38 SITE` and `STAGE38 GATES` report completed science evaluations. No new human-approved forcing repairs.
