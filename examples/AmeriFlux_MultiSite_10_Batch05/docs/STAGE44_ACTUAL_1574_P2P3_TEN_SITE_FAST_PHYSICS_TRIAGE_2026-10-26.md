# Batch05 Stage43 actual source and Stage44 whole-batch 1574 native half-hour review

## Actual Stage43 operator outcome — 26 October 2026

Stage43 succeeded from `/home/ly3n24/ameriflux_batch05_stage43/numeric_15_source_trial_20261026T191656Z_2924371`. Ten **method×original episode** cases passed prior *numeric* native VPD/physical tests; they form **15 unique original half-hours**, all in a VERSIONED UNAPPROVED research-only CSV and no production DATM forcing.

- US-UMB: 3 source ERA event methods / 5 native half-hours (E0004, E0005, E0007)
- US-Vcp: 4 source ERA event methods / 6 native half-hours (E0127, E0168, E0169, E0170)
- US-WCr: 1 source ERA event method / 2 native half-hours (E0013)
- US-Wkg: 2 source ERA event methods / 2 native half-hours (E0009, E0010)

Remaining Stage42 **23 method×event failures, NOT 23 unique events**:
- 9 MDS source humidity coverage/QC unavailable: exclude these incomplete methods for now, preserve original source
- 4 UMB source ERA methods caused newly introduced >4 hPa discontinuities: E0003, E0006, E0008, E0009; do not use this trial formulation as-is
- 4 high-magnitude >10 hPa original VPD to ERA repair: US-Var E0017/E0019/E0033 and US-Vcp E0172; investigate source T, tower/VPD QC and reference humidity
- 6 uncertain original native time neighbors: US-UMB E0001/E0002 and US-Vcp E0144/E0145/E0146/E0171

**0/10 full model-forcing scientific passes.** Stage43 did not change original 1574 P2/P3, Stage24 approved166, original P1 manual HOLD46, 10 RH saturation platform HH, FLUXMET, DATM, CIME or Slurm.

## Stage44 breakthrough: process ALL original 1574 rather than concentrating only on 15

[Stage44 full ten-site 1574 original source-native RH physics and 483 episode triage](../scripts/stage44/44_all_1574_p2p3_physics_and_event_prioritization_readonly.py), pinned GitHub commit `416f4f94e2ca4e9aad401dc185eb98bcf8c62a1e`, Git blob `f24f8cbf2a04ca8ba764ccff14784ec3a69db855`.

[Stage44 one-click launcher](../scripts/stage44/run_stage44_iridis6.sh), pinned GitHub commit `844e5e0207b3af0e8bd0b4e4bf526b6caf071ff3`, Git blob `758f9008297eabe98928e1dc84d5cac6cd081a79`.

Stage44 performs a fast *original-source review, not an unauthorized repair* of ALL previously inventoried **1574 original P2/P3 native half-hours in 483 original episodes** across the ten actual sites, joining Stage24 approved166, original P1 manually held46 and 10 saturation platforms, and previously isolated Stage43 15 native candidate HH. For each source native half-hour:
1. Compute original RH-over-water from original tower T and VPD, distinguish **negative RH**, RH below 1%, RH below 10%, and RH above 100% vs physical reference bounds.
2. Compare already-available **source-processed ERA RH and MDS RH** for physical validity at source tower T, compute hypothetical candidate VPD and magnitude relative to original (not independent ERA5-Land meteorology).
3. Aggregate all 483 original episodes by original source ID/clock, source RH physical anomalies, availability of a COMPLETE event source-ERA (or MDS) humidity time series, protecting any original QC0 measured VPD.
4. Prioritize full original event coverage **with known physically invalid original RH** for the next isolated before/after native ZIP neighbor check, while flagging >10 hPa candidate differences. **No method is auto-approved based only on valid ERA RH, and no unverified native boundary is treated as passed.**
5. Output the exact ten-site full original P2/P3 remaining quantities; verify original 1574 HH, 483 episodes, Stage43 15 previous unapproved trial native HH, and disjoint earlier 166/46/10 original source classes.

Outputs are NEW read-only report files:
- `stage44_ALL1574_NATIVE_HH_ORIGINAL_RH_AND_ERA_MDS_FIRST_PASS.csv`
- `stage44_ALL483_SOURCE_EVENTS_PHYSICS_AND_ERA_COVERAGE.csv`
- `stage44_ALL10_SITE_PRIORITY_AND_REMAINING_COUNTS.csv`
- `STAGE44_TEN_SITE_BULK_TRIAGE_AND_NEXT_ACTION.md`
- `stage44_manifest.json`

### Three-line IRIDIS6 pinned launcher

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/844e5e0207b3af0e8bd0b4e4bf526b6caf071ff3/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage44/run_stage44_iridis6.sh" -o "$HOME/run_stage44.sh"
test "$(git hash-object "$HOME/run_stage44.sh")" = "758f9008297eabe98928e1dc84d5cac6cd081a79"
bash "$HOME/run_stage44.sh"
```

The one-click operator runner checks the exact script source Git blob, compiles Python, invokes the self-test, and reads only the source science reports. **Stage44 is published and SHA-verified; user IRIDIS6 runtime pending.** No Slurm/model jobs or production forcing edits.
