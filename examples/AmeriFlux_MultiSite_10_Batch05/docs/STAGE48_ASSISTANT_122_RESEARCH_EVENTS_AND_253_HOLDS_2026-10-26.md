# AmeriFlux Batch05 — Stage47 proven; Stage48 corrected original event science screen

**27 October 2026 correction:** User actually ran Stage48 v1 twice. Both runs produced `STAGE48 SOURCE VERIFIED`, self-test passed, then stopped at script line 179: `ValueError("source event has gap or ERA trial creates new VPD jump")`. This failure is a real Stage48 filtering/code assumption, **not missing GitHub source, not a completed science repair, and not a site failure**. The program incorrectly equated Stage47's QC1 neighbor-priority lane with all strict source-native event continuity gates having passed.

Stage48 corrected GitHub revision fails closed **at the event level**: among 122 initially shortlisted events (80 QC1 neighbor + 42 numeric source trials), any true native interval gap, QC0 VPD, missing ERA RH, new >2/4hPa VPD threshold crossing, >10hPa change, or additional risky QC1 source neighbor goes to a *new, explicit science HOLD queue*. Remaining eligible original events become **unapproved research-only trial** rows. All 253 already held neighbor events remain held. **The eligible count cannot be asserted as 122 until the corrected program runs on IRIDIS6.** The 375 Assistant events and independent Claude108 are conserved.

## Stage47 actual execution on IRIDIS6, 2026-10-26

```text
STAGE47 SOURCE VERIFIED
STAGE47 SELF-TEST PASS
STAGE47 SUCCESS | ASSISTANT_NEIGHBOR_EVENTS 333 LOW_NUMERIC_EVENTS 42
STAGE47 NEIGHBOR_LANES {"ORIGINAL_NEIGHBOR_EXTREME_LOW_RH_HOLD":217,"SOURCE_QC1_ORIGIN_REVIEW":80,"SOURCE_QC2_OR_NONMEASURED_NEIGHBOR_HOLD":36}
STAGE47 LOW_NUMERIC_EVIDENCE {"MDS_ERA_DISAGREEMENT_REQUIRES_INDEPENDENT_REFERENCE":2,"SOURCE_ERA_ONLY_NO_INDEPENDENT_TOWER_REFERENCE":31,"SOURCE_TOWER_VS_ERA_T_DELTA_GT5C_HOLD":9}
STAGE47_REPORTS=/home/ly3n24/ameriflux_batch05_stage47/assistant_trackA_20261026T195942Z_3223947
```

This is 375 distinct Assistant-owned original **events**, **not** 375 unique source half-hours. Original 1574 unapproved P2/P3 native HH across all ten sites remain unchanged. Claude owns a non-overlapping separate 108 original events. Existing Stage24 approved166, P1 manual HOLD46, and ten RH saturation/platform HOLDs stay exactly unchanged. We will not touch Claude's part until the user resumes it separately.

### Stage48 scientific advance — more than another RH tally

Start with **122 PRELIMINARY original-event source-ERA-RH-at-tower-T options**, then apply all Stage45 source-native numeric gates *again* before generating research-only candidates:

1. **80 neighboring-QC1 events:** a source adjacent record has original QC1, without additional Stage47 severe/extremely-low original neighboring RH, missing native neighbor, QC2/nonmeasured or adjacent unapproved P2/P3 priority; original Stage45 episode did not introduce new >2/>4hPa VPD threshold crossing, had complete source-ERA RH and preserved original QC0, and proposed VPD changes are at most 10hPa. **QC1 is not an independently validated in situ RH reference.** These 80 can enter controlled isolated trial **only if the individual event also has no original native clock gap, no newly introduced 2/4hPa VPD discontinuity and all other source/QC protections pass**. Otherwise send that entire event to a separate HOLD, preserving all source values.
2. **42 previously numerically screened source-ERA events:** full original native event coverage, 0 new >2/>4hPa VPD thresholds, no original QC0 VPD, proposed VPD difference at most 10hPa. The **31 ERA-only**, **9 tower T versus source ERA T >5°C**, **2 MDS–ERA RH disagreements** from Stage47 all retain their individual source/reference science gaps and require external justification before actual production approval.

Preserve **253 difficult neighboring original-source events** separately without generating replacement force: **217** original RH 1–10% or other extremely-low neighbor source concerns and **36** QC2/nonmeasured native neighbors. A numerical trial must NOT smooth a repair toward the physically dubious neighbor or interpret an ERA/RH source substitute as observed truth. Note RH 1–10% may be rare but physically possible, not automatically declared wrong.

### Source and non-overwrite guarantees

- Revalidate Stage47 source 333+42 and original Stage45 full 483 episodes, Stage44 1574 native rows, Stage27 selected tower T/VPD/QC, existing Stage24 approved166/P1HOLD46/RHplatform10.
- Derive trial VPD `VPD_trial = es(T_original) × (1−source_ERA_RH/100)`, check 0–100% ERA RH and original-temperature water-vapor saturation bounds.
- Reject accidental repair of any original measured QC0 VPD, missing/native-clock gap, wrong original site/timestamp, or conflict with previously approved/held timestamps.
- Crosscheck prior 15 *research-only* Stage43 native HH against the new complete native candidate list; The original 15 are a **separate unapproved Stage43 research output**; new eligible candidates must be crosschecked and de-duplicated where overlapping. If any Stage43 trial does not qualify, it remains safely untouched and absent from the new candidate output. Record the actual overlap, not an assumed 15/15. Do not add "15 extra repairs" to the count.
- Every candidate output row has `science_approval=NO`, `production_DATM_permission=NO`; no Slurm, CIME, original source, DATA, user-approved source or model forcing changes are authorized.
- **Numerical candidate count != scientifically approved count; 0 new approvals, 0/10 full met forcing site acceptance established.**

### Pinned reproducible source code

[Stage48 full-event 122 candidate source pilot / 253 source neighbor HOLD code](../scripts/stage48/48_trackA_full_event_122_unapproved_ERA_pilots_and_253_source_holds.py): commit `30da2fd26999fdb2a8cc88fca6a24cc7a8ac8ae8`, immutable git blob `6fd45f6a0c28b60802dc6b6d653b24651b92a5de`.

[One-click IRIDIS6 runner](../scripts/stage48/run_stage48_iridis6.sh): commit `9b783e012f54f11bf0c9d1b286967906cde73c93`, immutable git blob `5e1a35dfa3771a14b93a7d67d13778b622d6c426`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/9b783e012f54f11bf0c9d1b286967906cde73c93/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage48/run_stage48_iridis6.sh" -o "$HOME/run_stage48.sh"
test "$(git hash-object "$HOME/run_stage48.sh")" = "5e1a35dfa3771a14b93a7d67d13778b622d6c426"
bash "$HOME/run_stage48.sh"
```

Input Stage47 exact original report path:
`/home/ly3n24/ameriflux_batch05_stage47/assistant_trackA_20261026T195942Z_3223947`.

After operator executes, expected new outputs:
- `stage48_ELIGIBLE_SOURCE_ERA_NATIVE_RESEARCH_ONLY.csv`: all source-native HH in the actually eligible subset of initial 122 original events, exact count measured on IRIDIS6; unapproved.
- `stage48_ELIGIBLE_FULL_EVENT_SOURCE_ERA_NUMERIC_GATES.csv`: event-level numeric/source QC details for actual eligible events; count is measured, not assumed.
- `stage48_INITIAL122_FAILED_SCIENCE_GATE_EVENTS.csv`: each rejected preliminary event and its exact original gap/new VPD crossing/QC/ERA source reason, with no repair.\n- `stage48_253_ORIGINAL_NEIGHBOR_SOURCE_HOLDS.csv`: 217 low source original RH + 36 QC2 neighbor events, no source changes.
- `stage48_TEN_SITE_ASSISTANT_TRIAL_AND_HOLD_PROGRESS.csv`
- `STAGE48_ASSISTANT_ELIGIBLE_NUMERIC_AND_SCIENCE_HOLDS.md`, `stage48_manifest.json`.

**Status: Stage48 v1 actually failed twice before writing valid output; corrected script/launcher now committed and SHA pinned, actual corrected IRIDIS6 runtime still pending.** No newly approved forcing; Claude's 108 untouched.
