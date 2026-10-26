# AmeriFlux Batch05 Stage46 — two-way research ownership: Assistant vs Claude

## Verified run and denominator (2026-10-26, IRIDIS6)

Stage45 succeeded and **all 1,574 original selected P2/P3 native half-hours, all 483 original source events, 9/9 affected site original data sources** were verified against native original T/VPD/QC. The tenth site US-UiD has 0 P2/P3 and was not a missing-source failure. There are **zero new scientifically approved repairs, zero whole-site forcing passes** from this P2/P3 study. Previous Stage24 166 approved original half-hour records, P1 manual HOLD 46 and RH saturation-platform HOLD 10 remain unchanged.

Actual immutable Stage45 operator report:
`/home/ly3n24/ameriflux_batch05_stage45/all_native_event_edges_20261026T193713Z_3134330`.

Stage45 scientific event priority lanes are **exclusive by method of classification**, not necessarily distinct causal mechanisms:

| Stage45 source-event priority | Original source events | Science owner |
|---|---:|---|
| `ORIGINAL_EXTERNAL_NEIGHBOR_QC_OR_RH_UNCERTAIN` | 333 | Assistant |
| `NUMERIC_SOURCE_NATIVE_SCREEN_NO_SCIENCE_APPROVAL` | 42 | Assistant |
| `LARGE_VPD_CHANGE_GT10HPA_REVIEW` | 77 | Claude |
| `NEW_EXTERNAL_OR_INTERNAL_GT2HPA_HOLD` | 22 | Claude |
| `NEW_EXTERNAL_OR_INTERNAL_GT4HPA_HOLD` | 9 | Claude |
| **Total** | **483** | Assistant 375; Claude 108 |

**Do not subtract 42 from 1,574:** 42 denotes numerically screened source *events*, not approved native records. All original 1,574 P2/P3 source native records remain science-unapproved. Separately, previously approved 166 Stage24 records stay approved and unchanged; the source 46 P1 manually held and 10 RH platforms are additional outstanding science holds, separate from the 1,574 original P2/P3 population.

Original P2/P3 native half-hour count / 483 original source events by site: US-UiD 0/0, US-UMB 23/9, US-UMd 15/6, US-Var 62/37, US-Vcm 362/72, US-Vcp 626/171, US-WCr 62/24, US-Whs 1/1, US-Wjs 401/153, US-Wkg 22/10.

The output Stage45 connected contiguous native P2/P3 runs is also **483**, equal to 483 original episodes; there is **no reduction through merging original event IDs** in this specific real operator run. Before/after investigation is therefore focused on actual native original neighbor/source flags, not artificial event joining.

## Stage46 reproducible evidence extractor (GitHub)

- [Script](../scripts/stage46/46_split_483_events_between_science_tracks_readonly.py), pinned commit `d34f04afe1de1afe2037b6b6b35452b3be00fe78`, Git blob `f97ad6c63b99e48b1a6a9ccc4ffcef8e7642a663`
- [One-click launcher](../scripts/stage46/run_stage46_iridis6.sh), pinned commit `840a6130ba0e9c8f491120d08232b7128d61de9a`, Git blob `e3f5cf451bbc29c9b2554c73b7b53de94b2f2b7a`

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/840a6130ba0e9c8f491120d08232b7128d61de9a/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage46/run_stage46_iridis6.sh" -o "$HOME/run_stage46.sh"
test "$(git hash-object "$HOME/run_stage46.sh")" = "e3f5cf451bbc29c9b2554c73b7b53de94b2f2b7a"
bash "$HOME/run_stage46.sh"
```

Once executed, the **user's IRIDIS6 local** Stage46 output directory contains:
- `stage46_ASSISTANT_333_NEIGHBOR_QC_AND_42_NUMERIC_EVENTS.csv` — assistant lane 375 source events
- `stage46_ASSISTANT_42_NUMERIC_SCIENCE_APPROVAL_CANDIDATES.csv` — 42 low-numeric-risk source events to verify scientifically, never automatically approve
- `stage46_CLAUDE_108_GT10_AND_NEW_JUMP_EVENT_CASES.csv` — exactly 108 original events with source time range, source native external QC1/QC2, implied adjacent RH, before/after jump and selected original-stage method gate
- `stage46_ALL483_EXACT_SCIENCE_RESPONSIBILITY_MATRIX.csv`
- `stage46_ALL10_SITE_HH_AND_EVENT_COUNTS_BY_OWNER.csv`
- `STAGE46_PARALLEL_ASSISTANT_CLAUDE_SCIENCE_HANDOFF.md`, `stage46_manifest.json` — full source report SHA provenance and no-write status.

**Code and documentation committed; actual Stage46 operator run pending.** Claude cannot read the user's private HPC outputs from this public GitHub link unless they are separately supplied to Claude or it has independent authorized access. Do **not** publish whole licensed original FLUXMET raw CSVs to a public repo solely for collaboration.

## Claude instructions — copy into separate Claude session

> Please lead **Batch05 Stage46 Track B** only. Read this handoff and the original Stage45 algorithm at `lyanyeung/CLM-FATES-single-site-workflows`, then read the exported `stage46_CLAUDE_108_GT10_AND_NEW_JUMP_EVENT_CASES.csv` from the operator if I supply it. You own **77** original episodes with proposed ERA VPD change >10 hPa, **22** with new >2 hPa jumps, and **9** with new >4 hPa jumps: **108 original event cases** in total. Do not work on Assistant Track A (333 uncertain neighbors + 42 lower-numeric-risk events), and do not alter existing Stage24 166 approved, 46 P1 science HOLD, 10 RH saturation-platform HOLD or 1574 original P2/P3. Reconstruct actual original event ±30min source T/VPD/QC, source ERA/MDS RH where available, source timestamps, original-vs-trial native VPD jump causality, and where available independently sourced ERA5-Land reference. Distinguish **ERA humidity physically plausible** from **observationally supported correction**. For every proposed alternative, report exact site, source-native time(s), previous VPD, proposed VPD, original T/QC, source of RH, timestamp provenance, before/after 2/4hPa discontinuity, and justification; unresolved cases must explicitly remain HOLD. Output independent **read-only** scripts and CSV/markdown reports only in a new `examples/AmeriFlux_MultiSite_10_Batch05/claude_stage46_trackB/` folder or under a NEW standalone IRIDIS6 output directory. No modifying production forcing, original source, DATM/CIME, running Slurm model jobs or automatically approving scientific changes. Send back GitHub commit links, hashes, detailed real IRIDIS6 results, and source event/half-hour population counts. Coordinate before merging any approved overlay with the Assistant-owned branch.

## Assistant Track A mandate

Work on **333** events where native original neighboring RH/QC source is uncertain. Distinguish QC1 from QC2/nonmeasured and negative/low-RH adjacent measurements before deciding if a repaired humidity edge is physically meaningful; large jumps to bad neighbors must NOT be interpreted as making repairs worse without further source evidence. In parallel, independently assess **42** lower-numeric-risk source ERA episode candidates (source QC, physical RH/VPD, source reanalysis and independent ERA5-Land where available). There are 0 new approvals, and no automatic production forcing writes.

## Separate, non-Batch05 issues in same terminal pasted logs

- `BE-Bra .../SourceMods` missing during a different model-preparation workflow; a failed `copytree` there did NOT finish that preparation (summary ok=0). Do not count it as a Batch05 AmeriFlux humidity QC event.
- `DK-Sor 2025` original/source merge 2024 regression and 2025 sanity output belong to ICOS/DK-Sor, not these ten AmeriFlux sites. The shell log basename containing 'stage45' does not imply its results apply to Batch05 Stage45.

## Safety and science rules

- Treat source ERA RH and ERA5-Land RH as reanalysis-related, not independent tower ground truth.
- Original source negative RH indicates T+VPD inconsistency, not scientific authorization to use an arbitrary ERA replacement.
- Preserve original native time, original tower T, measured VPD QC0, original approved / manual HOLD and full original episode coverage; do not repair isolated fragments or fill an unmeasured neighbor solely to smooth new VPD.
- Original Stage45 numeric event-pass 42/483 is NOT full met/DATM/land-model numerical acceptance, and US-UiD's zero P2/P3 is NOT a full site pass.
