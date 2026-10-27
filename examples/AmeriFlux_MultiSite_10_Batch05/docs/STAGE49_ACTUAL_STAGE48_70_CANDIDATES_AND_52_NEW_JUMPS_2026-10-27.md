# AmeriFlux Batch05 Stage49 | Assistant-only research verification after actual Stage48 success

## IRIDIS6 actual Stage48 outputs, October 27 2026

Exact original operator output directory:
`/home/ly3n24/ameriflux_batch05_stage48/assistant_122_full_event_trial_20261027T141646Z_3720216`

```text
STAGE48 SOURCE VERIFIED
STAGE48 SELF-TEST PASS
STAGE48 SUCCESS | INITIAL122 122 ELIGIBLE_RESEARCH_EVENTS 70 ELIGIBLE_NATIVE_HH 141 ADDITIONAL_GATE_HOLDS 52 ORIGINAL_NEIGHBOR_HOLDS 253 PREVIOUS_STAGE43_HH_OVERLAP 15
STAGE48 NEW_HOLD_REASONS {"NEW_EXTERNAL_GT2": 46, "NEW_EXTERNAL_GT4": 40}
STAGE48 RESEARCH_ONLY ALL 375 ACCOUNTED | CLAUDE108 UNTOUCHED | NO SOURCE/DATM/SLURM WRITES
```

All **375 Assistant** original Stage46 P2/P3 events are classified exactly: **70** original event-complete low-*numeric*-risk source ERA pilot methods (141 native half-hours); **52** events from Stage47's original initial 122 priorities now HOLD because a candidate introduced at least one new external VPD >2 hPa or >4 hPa discontinuity; **253** original source-neighbor problem events (217 physically very low RH neighboring records + 36 QC2/nonmeasured neighbors) remain on HOLD. For the 52, **46** have new >2hPa, **40** have new >4hPa, and their intersection is **34** events. The 52 event count **must not** be added to 46+40 separately. Original Stage43 15 previously UNAPPROVED source native research candidate rows are included in the 141, not an additional 15 repairs.

**Site counts, from actual Stage48 terminal evidence:**

| Site | Original P2/P3 HH | Numeric candidate original events | Native HH within candidates | Original low RH neighboring HOLD | QC2 neighboring HOLD |
|---|---:|---:|---:|---:|---:|
| US-UiD | 0 | 0 | 0 | 0 | 0 |
| US-UMB | 23 | 3 | 5 | 2 | 2 |
| US-UMd | 15 | 0 | 0 | 1 | 0 |
| US-Var | 62 | 4 | 5 | 1 | 0 |
| US-Vcm | 362 | 17 | 30 | 39 | 5 |
| US-Vcp | 626 | 11 | 17 | 113 | 13 |
| US-WCr | 62 | 5 | 9 | 3 | 13 |
| US-Whs | 1 | 0 | 0 | 0 | 0 |
| US-Wjs | 401 | 28 | 73 | 54 | 3 |
| US-Wkg | 22 | 2 | 2 | 4 | 0 |
| **TOTAL** | **1574** | **70** | **141** | **217** | **36** |

Stage24 **166 previously approved** RH/VPD records remain unchanged, and **46 P1 manual HOLD**, **10 source RH plateau HOLD** and all original **1574 P2/P3** source half-hours remain unapproved. **0/10** overall site forcing validation passed as a consequence of this study. Claude separately owns 108 original high-risk events and has not been touched today.

## Stage49: what it does—and cannot decide

[Read-only Stage49 source audit](../scripts/stage49/49_assistant_70_candidate_reference_and_52_new_jump_science_audit.py), immutable GitHub commit `98c6df7f1c8d608abdd16e43713c1643289f62a6`, Git blob `12587f0a351c388cbab59f3b83779b67585ce8b2`.

[One-click IRIDIS6 runner](../scripts/stage49/run_stage49_iridis6.sh), immutable commit `2412a72ff8e3665dfddafddc35a6d6ee4f29f25e`, Git blob `fa47192607915ecbb0c3162f18116f6c07ea4d79`.

This code reads **only** previous exact operator-generated original Stage48, 47, 45 and 27 CSVs, and checks source-original T/VPD/QC and event ID/time. It writes **new scientific evidence reports only**, no source or model-forcing modifications.

- All **70 numeric candidate events**: verify their exact 141 original site-native T/VPD/ERA-RH rows, original non-QC0 VPD, original T/VPD science provenance, before/after original native ±30 min VPD jump, source processed ERA vs MDS RH availability/disagreement, and magnitude of tower-vs-ERA temperature discrepancy. For each event, assign a *science evidence gap*, **not a production pass**. Processed source ERA RH, MDS and ERA5-Land reanalysis are not independent tower-observed humidity.
- All **52 new-jump source method HOLDS**: reconstruct the two actual external native original ±30 min boundaries per original event (104 edges), compare old vs ERA trial VPD jumps, original adjacent QC0/1/2 and original neighbor implied RH; classify which observed adjacent source anchors need further meteorological evidence before a new, episode-complete *alternative trial* could be contemplated. **Do not relax the threshold just because the proposed ERA data themselves are plausible**; in particular protect genuine measured QC0 VPD neighbor records.
- The other **253 source neighbor HOLD** cases retain original source and science blocks, and are summarized separately by site. **Claude Track B 108 events remain completely out of scope**.

Expected outputs:
- `stage49_70_NUMERIC_CANDIDATE_EVENT_REFERENCE_QC_GATES.csv`
- `stage49_52_NEW_JUMP_HOLD_EVENT_PHYSICAL_DIAGNOSIS.csv`
- `stage49_104_TRUE_NATIVE_BOUNDARY_BEFORE_AFTER_DETAILS.csv`
- `stage49_ALL10_SITE_ASSISTANT_REMAINING_WORK.csv`
- `STAGE49_ASSISTANT_70_SOURCE_EVIDENCE_52_NEW_JUMP_REVIEW.md`
- `stage49_manifest.json`

### Exact immutable one-line mobile-safe launcher

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/2412a72ff8e3665dfddafddc35a6d6ee4f29f25e/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage49/run_stage49_iridis6.sh" -o "$HOME/run_stage49.sh" && test "$(git hash-object "$HOME/run_stage49.sh")" = "fa47192607915ecbb0c3162f18116f6c07ea4d79" && bash "$HOME/run_stage49.sh"
```

**Stage49 script/runner/docs committed with immutable SHA pins; no operator Stage49 result yet.** Source approved 166, P1 held46, 10 RH source plateau and all 1574 P2/P3 remain unchanged until an explicit future scientific approval.
