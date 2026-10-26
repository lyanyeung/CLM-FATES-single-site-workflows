# AmeriFlux Batch05 — Stage44 actual all 1574 physics; Stage45 verify true native original source boundaries

## Operator-proven Stage44 results (26 October 2026)

- `STAGE44 SOURCE VERIFIED`; `STAGE44 SELF-TEST PASS`; `STAGE44 SUCCESS`
- `1,574` original P2/P3 half-hour rows, `483` original source events over exact ten sites.
- Original selected tower T and VPD imply **1,477 negative RH**, **97 RH in [0,1)%**. This is a **preselected P2/P3 anomaly population**, not evidence that entire tower forcing has this distribution and not 1574 newly uncovered bad measurements.
- Source-processed ERA humidity is 0–100% for every input half-hour and covers **483/483 original source events**. This is source input availability, NOT an actual validated source-native original-neighbor/boundary check, nor a fully validated ERA5-Land reference.
- Stage44 original event first-pass: **445 original events with at least one negative water-implied RH** and **38 original events RH <1% without negative RH**.
- Stage43 prior operator-verified 10 numerically clean method×event source pilots, 15 native half-hours, still UNAPPROVED (US-UMB 5, US-Vcp 6, US-WCr 2, US-Wkg 2).
- Original 166 user-approved Stage24 RH/VPD records unchanged; **46 original P1 manual HOLD, 10 RH saturation-platform HOLD, all original 1574 P2/P3 not yet science-approved**; original FLUXMET, DATM/CIME/Slurm untouched.

## Stage45 substantive next research task

[Stage45 original 483 source event and true contiguous P2P3 run boundary science gate](../scripts/stage45/45_actual_483_event_full_native_era_boundaries_and_connected_runs.py), immutable GitHub commit `5307765b4865364ba5d41a2e1525edf5a12532bc`, Git blob `2369ec2a6abb1c6ef1df8d5d23f6b70b68f144ba`.

[Stage45 one-click IRIDIS6 launcher](../scripts/stage45/run_stage45_iridis6.sh), immutable GitHub commit `000a856d9c20dd60c5a05ad69de4f742efda7e55`, Git blob `1cfa9269225d333d12679454ba46c63cab6056a7`.

Stage45 reads actual IRIDIS6 Stage44 first-pass output and exact Stage27 native P2/P3 source, Stage24 original approved/held records. For all nine sites with original P2/P3, source locator requires exact original native `TA_F, VPD_F, TA_F_QC, VPD_F_QC` equality to Stage27 (numeric tolerance 0.002). Six previously SHA-known FLUXMET ZIPs are pinned to actual immutable SHA256; other sites' original FLUXMET HH ZIP vs extracted copies must all agree on verified native records and ±30min neighbor rows. **US-UMB uses its actual verified 2007–2021 original FULLSET_HH product, whose 23/23 original T/VPD/QC were confirmed by Stage41**, not an imaginary FLUXMET_HH source. If a site lacks trustworthy source, it remains an explicit `STAGE45 ORIGINAL_SOURCE_SITE_HOLD`; the rest continue.

Two coupled decision layers:
1. **483 original source episode screens**: restore original SHA-verified source local-standard half-hour VPD and T/QC; compare source ERA RH at original tower temperature against same original source ±30min neighbors and any original within-event half-hour transitions; report original and hypothetical jumps >2 / >4 hPa, *newly crossed* thresholds, incomplete event coverage, gaps, modified QC0 protections, unknown neighbor provenance, original source RH extreme and VPD modifications >10 hPa.
2. **Maximal contiguous P2/P3 connected runs**, possibly across original Stage27 episode boundaries. Evaluate before/after at the *real outer ends of the entire adjacent original anomaly component*, rather than count split episode boundaries as false discontinuities. **Never bridge gaps**, never use neighbor that is itself another unapproved P2/P3 as verified meteorological truth. A "numeric low-risk" run remains `science_approval=NO` and cannot be fed to DATM automatically.

Generated output under `$HOME/ameriflux_batch05_stage45/all_native_event_edges_...`:
- `stage45_ALL_VERIFIED_NATIVE_P2P3_AND_ERA_TRIAL.csv`
- `stage45_483_ORIGINAL_EVENTS_TRUE_NATIVE_VPD_QC.csv`
- `stage45_CONNECTED_P2P3_CONTIGUOUS_RUN_METHOD_GATES.csv`
- `stage45_TRUE_ORIGINAL_EVENT_AND_JOINED_RUN_EXTERNAL_EDGES.csv`
- `stage45_ALL10_SITE_REAL_SOURCE_BATCH_PROGRESS.csv`
- `STAGE45_ALL483_EVENT_NATIVE_ERA_BOUNDARY_REPORT.md`
- `stage45_manifest.json` (SHA/provenance, zero scientific approvals, zero production edits)

### Directly copy to IRIDIS6 (no git pull required)

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/000a856d9c20dd60c5a05ad69de4f742efda7e55/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage45/run_stage45_iridis6.sh" -o "$HOME/run_stage45.sh"
test "$(git hash-object "$HOME/run_stage45.sh")" = "1cfa9269225d333d12679454ba46c63cab6056a7"
bash "$HOME/run_stage45.sh"
```

**Stage45 script committed and GitHub SHA-verified, user runtime still pending.** It reads and analyzes source data, writes new reports only, never changes source FLUXMET/FULLSET or operational DATM/CIME/Slurm and never approves new RH/VPD repairs.
