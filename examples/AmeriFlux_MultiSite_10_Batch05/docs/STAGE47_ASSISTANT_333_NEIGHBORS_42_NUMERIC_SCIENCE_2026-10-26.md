# Stage47: Assistant-owned 375 source-original events, after Stage46 SUCCESS

## Latest actual IRIDIS6 operator state (26 October 2026)

Stage46 source and self-test verified; exact full original 483 event partition succeeded. Actual source provenance:
`/home/ly3n24/ameriflux_batch05_stage46/parallel_science_lanes_20261026T194948Z_3184652`.

There were exactly **1,574 original source-native P2/P3 half-hours in 483 original events**, all original T/VPD/QC fully source-verified at Stage45, **0 newly science-approved**. Stage46 allocated:

- Assistant Track A: **333** neighbor-source QC/RH uncertainty + **42** numerically lower-risk ERA source original events, **375 distinct events**.
- Claude Track B: **77** larger than 10hPa VPD-change priority + **22** newly created >2 hPa + **9** newly created >4hPa discontinuities, **108 distinct events**. The split is **mutually exclusive at original event identity**, although scientific failure mechanisms within one event can overlap.
- Preserve original Stage24 approved **166** RH/VPD fixes, **46** human P1 HOLD, **10** RH saturation/platform source holds, and original **1,574** unapproved P2/P3 source half-hours. None of the 42 numerically low-risk events or previously drafted Stage43 **15** native half-hour research candidates are approved forcing.
- The Stage45 **483 original native connected runs** equal the 483 original source events, so merging timestamp-adjacent events did not shrink this real source work queue.
- US-UiD has zero identified P2/P3 but **no complete forcing pass** has yet been demonstrated.

### Actual Stage46 10-site event allocation

| Site | Assistant uncertain neighbor | Assistant numerical | Claude >10hPa | Claude newly >2hPa | Claude newly >4hPa | Original P2/P3 HH |
|---|---:|---:|---:|---:|---:|---:|
| US-UiD | 0 | 0 | 0 | 0 | 0 | 0 |
| US-UMB | 6 | 3 | 0 | 0 | 0 | 23 |
| US-UMd | 1 | 0 | 5 | 0 | 0 | 15 |
| US-Var | 5 | 0 | 32 | 0 | 0 | 62 |
| US-Vcm | 62 | 5 | 5 | 0 | 0 | 362 |
| US-Vcp | 139 | 4 | 2 | 17 | 9 | 626 |
| US-WCr | 22 | 1 | 1 | 0 | 0 | 62 |
| US-Whs | 0 | 0 | 1 | 0 | 0 | 1 |
| US-Wjs | 94 | 26 | 28 | 5 | 0 | 401 |
| US-Wkg | 4 | 3 | 3 | 0 | 0 | 22 |
| **TOTAL** | **333** | **42** | **77** | **22** | **9** | **1574** |

## Stage47 source code + pinned runtime

- [Science read-only script](../scripts/stage47/47_assistant_trackA_neighbor_qc_and_42_numeric_science_evidence_readonly.py), fixed commit `1299df67353f4f14a986ac50079f3700d0d4d084`, git blob SHA `59e06137a4cf84425b33b4526e412d81325454b5`.
- [Run once on IRIDIS6](../scripts/stage47/run_stage47_iridis6.sh), fixed commit `0a1d9778d19a7bedae996b45b174634b196e7d1f`, Git blob `31ede6d8884b6c5e4eed650028c77e6154202767`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/0a1d9778d19a7bedae996b45b174634b196e7d1f/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage47/run_stage47_iridis6.sh" -o "$HOME/run_stage47.sh"
test "$(git hash-object "$HOME/run_stage47.sh")" = "31ede6d8884b6c5e4eed650028c77e6154202767"
bash "$HOME/run_stage47.sh"
```

Stage47 reads original Stage46, Stage45, Stage44 and Stage27 operator output under the actual previous directories. It asserts total cohorts **375+108=483**, original 1574 native source rows, zero earlier scientific approvals, exact disjoint event ownership and source-native tower T/VPD/QC and processed ERA/MDS RH. The tools only write a **new independent reporting directory**, do not edit source, forcing or run Slurm.

For **333 uncertain-adjacent original events**, it disaggregates actual original `BEFORE` and `AFTER` ±30min neighbor source QC0/1/2 and missing QC, negative RH, RH 0–1%, RH 1–10%, RH >100%, unknown RH, Stage24 previously approved neighbor and another unapproved P2/P3 neighbor. It records whether a hypothetical candidate source-ERA humidity change worsened or improved a boundary by >=0.5hPa, **but low numerical jumps cannot make physically invalid original neighbors ground truth**.

For **42 numerically lower-risk source ERA candidates**, it compares all original site-native time points in each event, full ERA and MDS RH coverage, ERA/MDS agreement <=5 percentage points vs discrepancy >10 points, and source tower temperature vs processed ERA temperature difference >5C. These are reanalysis-related, not independent ground observations; user scientific authorization is still required before any production modification.

Expected outputs:
- `stage47_333_ORIGINAL_NEIGHBOR_QC_RH_JUMP_DIAGNOSIS.csv`
- `stage47_ALL333_NATIVE_ORIGINAL_NEIGHBOR_EDGE_EVIDENCE.csv`
- `stage47_42_NUMERIC_SOURCE_ERA_MDS_SCIENTIFIC_EVIDENCE.csv`
- `stage47_TEN_SITE_ASSISTANT_OWNER_WORKLOAD.csv`
- `STAGE47_ASSISTANT_SOURCE_NEIGHBOR_AND_42_PILOT_SCIENCE.md`
- `stage47_manifest.json`

**Code committed and GitHub SHA-verified; actual IRIDIS6 Stage47 execution still pending.** Preserve 166 approved, 46 P1 manual HOLD, 10 RH plateaus and original unapproved 1574. No new source approval, original FLUXMET/FULLSET, DATM/CIME, or Slurm changes.

## Claude parallel work: exact handoff

Use the already completed Stage46 Claude CSV `stage46_CLAUDE_108_GT10_AND_NEW_JUMP_EVENT_CASES.csv` and the [Stage46 Claude track B handoff](STAGE46_PARALLEL_CLAUDE_ASSISTANT_483_EVENT_HANDOFF_2026-10-26.md). Claude must work on separate read-only reports and independent proposed methods for its 108 events; no competing writes to Assistant-owned scripts, source, approved overlays, DATM or CIME. The CSV lives on the user's private IRIDIS6 filesystem, not automatically exposed to Claude merely by a public GitHub link.
