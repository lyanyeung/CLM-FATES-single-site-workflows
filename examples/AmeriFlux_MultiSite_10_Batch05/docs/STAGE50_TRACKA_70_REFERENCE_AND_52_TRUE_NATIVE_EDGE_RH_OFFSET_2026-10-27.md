# Batch05 Stage50 — 70 evidence priorities, 52 original-source boundary science HOLDs

## Actual operator result: Stage49 succeeded 27 October 2026

```text
STAGE49 SOURCE VERIFIED
STAGE49 SELF-TEST PASS
STAGE49 SUCCESS | 70 original numeric research events /141 native HH, 52 external-jump science holds with 104 original edges, 253 original neighbor source holds; all 375 reconciled
STAGE49 CANDIDATE_REFERENCE_GATES {"SOURCE_ERA_ONLY_NO_MDS_REFERENCE":44,"SOURCE_MDS_ERA_RH_GT10PP_DISAGREEMENT_HOLD":4,"TOWER_MINUS_ERA_T_GT5C_HOLD":22}
STAGE49 NEW_JUMP_CONTEXT {"JUMP_TO_MEASURED_QC0_NEIGHBOR_REQUIRES_ALTERNATE_RH":35,"JUMP_TO_QC1_NEIGHBOR_OBSERVATION_REVIEW":17}
STAGE49_REPORTS=/home/ly3n24/ameriflux_batch05_stage49/assistant_70_reference_52_jump_20261027T142654Z_3801977
```

These are **original event counts, not native half-hour counts**. 70 source-ERA numerically screened original events encompass 141 source half-hours, including 15 earlier Stage43 standalone unapproved research rows. Every candidate needs original site humidity/tower met QC and independent evidence before scientific approval. 44 have only source processed ERA RH (no native MDS comparison); 4 ERA/MDS RH comparisons differ by more than 10 percentage points; 22 have background tower vs source ERA temperature difference over 5°C. ERA RH, MDS and ERA5-Land are reanalysis-related or processed products, **not automatically independent tower measurements**.

Of the 52 rejected original source-ERA full-event proposals, **35** form unacceptable new VPD jumps relative to a measured original neighbor QC0, and **17** relative to original QC1. Their 104 true original before/after source-native edges are in Stage49; user-approved original QC0 neighbors must NEVER be altered to hide new artificial discontinuities. Stage48 identified **46** events crossing new >2 hPa thresholds, **40** crossing new >4 hPa and **34** in both groups, not 86 distinct events. The other **253** source-neighbor science holds (217 very low RH neighbor, 36 QC2/nonmeasured neighbor) remain source-untouched. Assistant 375 original events and Claude 108 separate original events account for 483 P2/P3 original episodes. All 1574 preselected P2/P3 original native half-hours remain science unapproved; prior Stage24 166 approved repairs, original P1 HOLD46 and ten RH plateau holds untouched.

## Stage50 scientific objective and explicit limitations

[Stage50 source script](../scripts/stage50/50_trackA_eventwide_RH_offset_hypotheses_and_70_reference_queue.py), immutable commit `0104fbb6ce68a15d7c45da6ccc45c620044dca1a`, Git blob `3a354cdcc4c577a69110303aaaaa8ddce4139527`.

[Stage50 one-click IRIDIS6 launcher](../scripts/stage50/run_stage50_iridis6.sh), immutable commit `dcee3cea89bd4737e6328ee3b69e2f8eee651be7`, Git blob `c8cce5f54a3afcad52995bb59c04fd3166b4481e`.

**Track A only, research sensitivity not forcing.** From actual Stage49/48/45/44/27 source reports:

1. Preserve source original site time, original native T/VPD/QC and all 70 source-ERA candidate original event identities. Generate a ranked 70-event science reference-gap table without creating any forcing overlays or ungrounded science approvals.
2. For each of 52 original Stage49 source-ERA proposals that was held for a newly created VPD jump, read all site-native source half-hours for the entire event. Derive ERA-at-original-tower-T VPD. Join the exact **signed source neighbor VPD** from the Stage45 original source-native ±30min edge report, and verify its original-vs-source-ERA jump against the Stage49 104-edge science audit. Refuse to use a missing, unapproved adjacent P2/P3 neighbor as ground truth.
3. Explore **one constant RH percentage-point offset over each complete native original event** using a conservative deterministic −20 to +20 pp grid (0.5 pp increments). Apply at original tower temperature without changing original QC0, source timestamps or neighbor records. Screen 0–100% candidate RH, full-event coverage, internal and both external *new* >2/>4hPa VPD threshold crossings, original VPD repair magnitude <=10hPa and worsening of an existing original edge by <=0.5hPa. These limits are **heuristic numerical screening only**, not physical proof or calibrated humidity.
4. If a mathematically feasible offset is found, label `NUMERIC_EVENTWIDE_BOUNDARIES_POSSIBLE_SCIENCE_HOLD`, write a standalone **unapproved sensitivity CSV**, and explicitly continue science HOLD. If no solution, `NO_FEASIBLE_BOUNDED_EVENT_RH_OFFSET_SCIENCE_HOLD`. Neither should be automatically promoted to model forcing. The true original station humidity source, additional tower/sensor QC and meteorological consistency remain unresolved.
5. Leave original 253 native source-neighbor HOLD events and Claude's 108 original events outside this proposal. **No model case, CIME, DATM, Slurm, approved overlay, original FLUXMET/FULLSET, P1 manual hold or RH platform modifications.**

Expected output:
- `stage50_70_SOURCE_REFERENCE_SCIENCE_PRIORITY.csv`
- `stage50_52_EVENTWIDE_RH_OFFSET_FULL_NATIVE_BOUNDARY_RESEARCH_ONLY.csv`
- `stage50_EVENTWIDE_COUNTERFACTUAL_NATIVE_SOURCE_NO_FORCING.csv`
- `stage50_TEN_SITE_ASSISTANT_HOLD_AND_EVIDENCE_COUNTS.csv`
- `STAGE50_ASSISTANT_REFERENCE_SCIENCE_AND_EVENTWIDE_OFFSET_LIMITS.md`
- `stage50_manifest.json`

Run from any IRIDIS6 login shell. One line is suitable for phone/mobile terminals:

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/dcee3cea89bd4737e6328ee3b69e2f8eee651be7/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage50/run_stage50_iridis6.sh" -o "$HOME/run_stage50.sh" && test "$(git hash-object "$HOME/run_stage50.sh")" = "c8cce5f54a3afcad52995bb59c04fd3166b4481e" && bash "$HOME/run_stage50.sh"
```

**Publication status:** GitHub script and launcher SHA verified, runtime Stage50 on IRIDIS6 **not yet executed**. No new science approvals, no model-forcing writes.
