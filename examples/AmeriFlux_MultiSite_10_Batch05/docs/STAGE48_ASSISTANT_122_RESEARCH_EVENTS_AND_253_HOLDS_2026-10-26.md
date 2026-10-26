# AmeriFlux Batch05 — Stage47 actual operator result, Stage48 Assistant Track A source science pilot

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

Build **122 complete original-event, source-ERA-RH-at-original-tower-T numerical research candidates** from two Stage47 categories:

1. **80 neighboring-QC1 events:** a source adjacent record has original QC1, without additional Stage47 severe/extremely-low original neighboring RH, missing native neighbor, QC2/nonmeasured or adjacent unapproved P2/P3 priority; original Stage45 episode did not introduce new >2/>4hPa VPD threshold crossing, had complete source-ERA RH and preserved original QC0, and proposed VPD changes are at most 10hPa. **QC1 is not an independently validated in situ RH reference.** These 80 can enter controlled isolated trial only, not be declared scientifically correct or model-ready.
2. **42 previously numerically screened source-ERA events:** full original native event coverage, 0 new >2/>4hPa VPD thresholds, no original QC0 VPD, proposed VPD difference at most 10hPa. The **31 ERA-only**, **9 tower T versus source ERA T >5°C**, **2 MDS–ERA RH disagreements** from Stage47 all retain their individual source/reference science gaps and require external justification before actual production approval.

Preserve **253 difficult neighboring original-source events** separately without generating replacement force: **217** original RH 1–10% or other extremely-low neighbor source concerns and **36** QC2/nonmeasured native neighbors. A numerical trial must NOT smooth a repair toward the physically dubious neighbor or interpret an ERA/RH source substitute as observed truth. Note RH 1–10% may be rare but physically possible, not automatically declared wrong.

### Source and non-overwrite guarantees

- Revalidate Stage47 source 333+42 and original Stage45 full 483 episodes, Stage44 1574 native rows, Stage27 selected tower T/VPD/QC, existing Stage24 approved166/P1HOLD46/RHplatform10.
- Derive trial VPD `VPD_trial = es(T_original) × (1−source_ERA_RH/100)`, check 0–100% ERA RH and original-temperature water-vapor saturation bounds.
- Reject accidental repair of any original measured QC0 VPD, missing/native-clock gap, wrong original site/timestamp, or conflict with previously approved/held timestamps.
- Crosscheck prior 15 *research-only* Stage43 native HH against the new complete native candidate list; **15/15 must be present exactly once, matching original VPD and trial value**. Do not add "15 extra repairs" to the count.
- Every candidate output row has `science_approval=NO`, `production_DATM_permission=NO`; no Slurm, CIME, original source, DATA, user-approved source or model forcing changes are authorized.
- **Numerical candidate count != scientifically approved count; 0 new approvals, 0/10 full met forcing site acceptance established.**

### Pinned reproducible source code

[Stage48 full-event 122 candidate source pilot / 253 source neighbor HOLD code](../scripts/stage48/48_trackA_full_event_122_unapproved_ERA_pilots_and_253_source_holds.py): commit `921d7f7c54d6f7847e6f7165c9d74afb0c9c9844`, immutable git blob `ebb31061a00efe5de4b33e374f535f65ff2b4fdd`.

[One-click IRIDIS6 runner](../scripts/stage48/run_stage48_iridis6.sh): commit `b8a3e009f8a108092fe93b4eabffb75f56216b46`, immutable git blob `42a864ff56216bf6972e09a0fff8c15bed5ce559`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/b8a3e009f8a108092fe93b4eabffb75f56216b46/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage48/run_stage48_iridis6.sh" -o "$HOME/run_stage48.sh"
test "$(git hash-object "$HOME/run_stage48.sh")" = "42a864ff56216bf6972e09a0fff8c15bed5ce559"
bash "$HOME/run_stage48.sh"
```

Input Stage47 exact original report path:
`/home/ly3n24/ameriflux_batch05_stage47/assistant_trackA_20261026T195942Z_3223947`.

After operator executes, expected new outputs:
- `stage48_VERSIONED_FULL_EVENT_SOURCE_ERA_122_EVENT_NATIVE_CANDIDATES_UNAPPROVED.csv`: all source native half-hours covered by the 122 original full-event research candidates, exact count measured on IRIDIS6 (not guessed), no approval.
- `stage48_ALL122_COMPLETE_EVENT_SCIENCE_NUMERIC_GATES.csv`: 122 candidate event-level local numerical/VPD/source provenance science gates.
- `stage48_253_ORIGINAL_NEIGHBOR_SOURCE_HOLDS.csv`: 217 low source original RH + 36 QC2 neighbor events, no source changes.
- `stage48_TEN_SITE_ASSISTANT_TRIAL_AND_HOLD_PROGRESS.csv`
- `STAGE48_ASSISTANT_122_TRIAL_EVENTS_253_SOURCE_HOLDS.md`, `stage48_manifest.json`.

**Status: Stage48 code/docs committed to GitHub, immutable SHA verified; actual IRIDIS6 runtime not yet reported.** This stage advances 80 more candidate events to controlled isolated numerical research, not science approval. Claude's 108 untouched.
