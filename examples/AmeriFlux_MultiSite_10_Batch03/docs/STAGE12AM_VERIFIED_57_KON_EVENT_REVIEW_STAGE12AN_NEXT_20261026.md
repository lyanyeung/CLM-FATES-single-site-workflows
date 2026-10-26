# Stage12am v2 verified 2026-10-26 03:45 UTC — 57 US-Kon original-native humidity holds

## Actual operator IRIDIS6 results

The operator's pinned Stage12am v2 source Git SHA / syntax, --self-test and --run **PASS**. Full independent SHA-sealed source-only scientific review:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12am_Kon_57_humidity_ERA_episode_original_source_review_20261026T034540Z_379e08c6/`

- Exactly **34 older** source-original Stage12g VPD-jump center holds and **23 more** humidity gaps created when the operator approved 23 source `TA_F_QC=1` temperature interpolations in Stage12ah.
- All **57/57** exact original-native companion ERA-RH candidate VPD/QBOT are numerically basic-water-physics valid under current corrected Stage12ak tower T and site pressure. Source humidity is companion ERA gapfill, **not a true QC0 tower RH observation**.
- Source-ERA T difference ≤5°C for **23/23** new temp-edited and **32/34** older VPD-jump centers: **55/57**.
- Two original VPD held centers fail the predeclared tower-versus-ERA-T 5°C threshold:
  - `201102220900`: site T −1.754°C, paired ERA T −7.159°C, |ΔT|=5.405°C. Source `TA_F_QC=0` but paired ERA T mismatch; **HOLD**.
  - `201109291830`: site T 15.617°C, paired ERA T 21.991°C, |ΔT|=6.374°C. Original `TA_F_QC=1`, `VPD_F_QC=2`, additional unapproved temperature provenance. **Separate hard HOLD**, never silently change original T or substitute ERA T.
- All **57** have at least one original as-is adjacent held or >4 hPa event conflict requiring *connected-episode* treatment; none should be injected alone into original Stage12ak. Neighbor population is **114 repeated center-neighbor sides**, not 114 distinct source observations.
- Particularly strong paired ERA-RH event consistency examples: `201103241230,1300,1330,1400,1430` candidate VPD ≈ 5.049758,5.151759,5.288014,5.420175,5.437978 hPa; several source MDS QC1 values in that event were much larger than physically possible at corrected source tower T.
- Original 2008-09-26 05:30 user-approved observed QC0 VPD exception = 2.801 hPa still maintained; source PSRF Stage12ak 3 event interpolations are **research-only** and none of the 57 source humidity edits applied by Stage12am.

## Stage12an next

[Stage12an US-Kon 55 center connected native ERA-RH research-only candidate](../scripts/stage12/12an_Kon_55_source_ERA_RH_connected_event_candidates_RESEARCH_ONLY.py) is pinned to Git commit `cfc5a3caf1a6b62d0a9d6f7fedeb27a5307eaa76`, Git source blob `c77ae98feeb7158c05eab74519854d12dc8e68cd`. As of this note **script is committed but not yet tested on IRIDIS6**.

It SHA-verifies Stage12ak+Stage12am receipts/actual source+source-ERA original files. It excludes the two hard temperature holds and groups exact **55 eligible held centers** into connected 30-min events; where an event boundary is inconsistent, reviews the original source neighbor QC and at most 48 additional original QC1/QC2 humidity values with paired native ERA-RH, while protecting every original VPD QC0 point, all unrelated held VPD data and the original native T/P/clock. An event numerically PASSes only if all patch-patch and exterior 30-min VPD jumps ≤4hPa, all candidate source QC/temperature/pressure/water/ice physics checks pass, and its exterior source VPD is not missing. Blocked groups remain held; **no silent override** of two hard T holds or other legacy source science HOLDs.

- `--self-test`: no file IO
- `--check`: full provenance & numeric event review, no writes
- `--trial`: new isolated full NOLEAP science-only US-Kon successor **only** for numerically passing source event groups, plus candidate table, event pass/reject reasons, original source edge ledger, and SHA receipt. **No original input, earlier Stage12 source, DATM, CIME or Slurm modifications**.
- Trial output missing count **not yet known** and must not be invented. Existing source currently 389 missing Kon VPD/QBOT; new research successor's reduction depends on actual event boundary/QC audit.

No scientific operator adoption of original companion ERA-RH, no Post-v5/DATM/spinup authorization. Separately user-approved Stage12ah temperature edits and original QC0 VPD exception remain immutable.
