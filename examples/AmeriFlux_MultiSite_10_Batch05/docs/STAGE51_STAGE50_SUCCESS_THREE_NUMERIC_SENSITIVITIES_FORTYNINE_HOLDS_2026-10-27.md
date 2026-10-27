# Stage51 | AmeriFlux Batch05, verified Stage50 science screening and remaining work

## Actual IRIDIS6 Stage50 result (27 October 2026)

```text
STAGE50 SOURCE VERIFIED
STAGE50 SELF-TEST PASS
STAGE50 SUCCESS | 70 source-reference pending; 52 original-new-jump HOLD, full-event source-native boundary sensitivity, 253 neighbor source holds; zero approvals
STAGE50 LOW_RISK_REFERENCE {"SOURCE_ERA_ONLY_NO_MDS_REFERENCE":44,"SOURCE_MDS_ERA_RH_GT10PP_DISAGREEMENT_HOLD":4,"TOWER_MINUS_ERA_T_GT5C_HOLD":22}
STAGE50 RH_OFFSET_BOUNDARY_SENSITIVITY {"NO_FEASIBLE_BOUNDED_EVENT_RH_OFFSET_SCIENCE_HOLD":49,"NUMERIC_EVENTWIDE_BOUNDARIES_POSSIBLE_SCIENCE_HOLD":3}
STAGE50_REPORTS=/home/ly3n24/ameriflux_batch05_stage50/full_native_boundary_sensitivity_20261027T174050Z_733866
```

**Crucial interpretation:** 3 original events passed a **mathematical** bounded constant RH offset sensitivity (−20 to +20 percentage points, 0.5-pp grid) at original tower T and true source-native original signed-neighbor VPD. Their original humidity is **not proved valid**, and the offset is not measured or independently calibrated. **All 52 events remain science HOLD**, including those 3. The other 49 **failed this particular family of constant RH offsets and boundary constraints**, *not* every possible independent source/reanalysis-derived or site observation-based method.

The remaining Assistant Track A population is **375 original events**: 70 previously numeric passing but scientifically unapproved source-ERA candidates (141 native HH, including Stage43 15 earlier unapproved), 3 offset sensitivity-only numerical candidates, 49 offset-family nonfeasible source events, 217 originally low-RH neighboring source holds and 36 QC2/nonmeasured neighboring source holds. Equivalently 70 + 3 + 49 + 253 = 375. Claude Track B's disjoint 108 original events not touched. Original 1574 P2/P3 native records remain unapproved. Previously approved Stage24 166 native RH/VPD edits, 46 P1 science holds, 10 source RH plateau science holds, official FLUXMET/FULLSET and model forcing/CIME/Slurm unchanged.

## Next exact source-science check, Stage51

[Source-only Stage51 candidate verification and failed-constraint triage](../scripts/stage51/51_trackA_three_numeric_hypotheses_and_49_failed_offset_mechanisms_readonly.py). Fixed original GitHub commit `36da8349e3ba95ab4729a2b6b9eab04b8c63abc1`, blob SHA `fd7a1a25501f893bf35e219e33d9702bd0c944e7`.

[IRIDIS6 one-click launcher](../scripts/stage51/run_stage51_iridis6.sh). Fixed commit `0fe30e5a15ca87c0477fc2acb117fdef8e8f2d52`, blob SHA `241e8a09a7a0c19735aa7bbcf36533598264b58d`.

1. Read **actual original** Stage50/49/45/44/27 SHA provenance and full source-native event half-hours. Recompute all Stage50 81 constant RH-offset hypotheses on each of 52 held original source-ERA event methods. Preserve original non-QC0 site T/VPD, native source timestamps, and source ERA RH from the recorded Stage27/44 values.
2. Verify exactly the **3 numerical hypotheses** reported by Stage50 against their source-native hypothesis rows, no new internal and external >2 / >4 hPa threshold crossings, no >10 hPa VPD modifications, true original signed-neighbor source VPD and QC, and no original edge worsened >0.5 hPa. Each is explicitly marked `NUMERIC_ONLY_MUST_VALIDATE_ORIGINAL_STATION_METEO`, not scientifically approved.
3. For exactly **49** original events with no feasible constant RH offset under this search, record numbers of offset alternatives failing physical RH bounds, VPD-change magnitude and before/after new jump constraints. Record a *closest (still failed)* trial as a **diagnostic only**, never as repair data, and be explicit that independent actual observed RH and other methods were **not** tested by this Stage51 script.
4. Preserve **70** earlier source-ERA numeric events with their original scientific evidence gap (44 ERA-only RH, 4 MDS-vs-ERA RH >10pp, 22 original tower-versus-ERA temperature >5°C), 253 original neighbor science holds, 108 independent Claude events.
5. Produce new read-only reports only. Source original FLUXMET/FULLSET, approved166, P1hold46, RH plateau10, all P2P3 1574, DATM/CIME and Slurm untouched. **No actual scientific acceptance/forcings.**

Expected source-local new outputs:
- `stage51_THREE_NUMERIC_EVENT_HYPOTHESES_NEED_TOWER_VALIDATION.csv`
- `stage51_THREE_EVENT_ALL_NATIVE_HH_UNAPPROVED_EVIDENCE.csv`
- `stage51_FORTYNINE_NO_FEASIBLE_BOUNDED_OFFSET_GATE_DIAGNOSIS.csv`
- `stage51_SEVENTY_REFERENCE_GAP_SCIENCE_QUEUE.csv`
- `stage51_TEN_SITE_ASSISTANT_EVENT_CONSERVATION.csv`
- `STAGE51_ASSISTANT_THREE_HYPOTHESES_FORTYNINE_HOLDS_NO_APPROVAL.md` and `stage51_manifest.json`

### Mobile-compatible immutable source command

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/0fe30e5a15ca87c0477fc2acb117fdef8e8f2d52/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage51/run_stage51_iridis6.sh" -o "$HOME/run_stage51.sh" && test "$(git hash-object "$HOME/run_stage51.sh")" = "241e8a09a7a0c19735aa7bbcf36533598264b58d" && bash "$HOME/run_stage51.sh"
```

**Status: script/launcher/docs committed and their immutable GitHub SHA verified; Stage51 has not yet been executed on the user's IRIDIS6.**
