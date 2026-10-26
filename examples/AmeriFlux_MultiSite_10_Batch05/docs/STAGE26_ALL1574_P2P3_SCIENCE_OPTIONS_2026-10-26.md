# AmeriFlux Batch05 — Stage25 operator completed; Stage26 distinct scientific reconstructions

## Grounded Stage25 operator results (2026-10-26, IRIDIS6)

```text
STAGE25 SELF-TEST PASS
STAGE25 SUCCESS | 1750 original HH -> 522 original episodes; 166 approved overlay & 46 manual holds crosswalk
STAGE25 P1 176 = 130 approved + 46 manual HOLD
STAGE25 APPROVED_INSIDE_1750 130 APPROVED_TRANSITIONS_OUTSIDE_1750 36
STAGE25 P2_P3 ORIGINAL=1574 ALREADY_APPROVED_IN_OVERLAY 0 STILL_UNAPPROVED 1574
US-UiD 0, US-UMB 23, US-UMd 15, US-Var 62,
US-Vcm 362, US-Vcp 626, US-WCr 62, US-Whs 1,
US-Wjs 401, US-Wkg 22
```

Original P2/P3 worklist evidence groups — mutually exclusive by the **Stage25 first matching priority rule**:
- 924 `UNRESOLVED_PHYSICS_SOURCE_PROVENANCE_INDEPENDENT_MET_REQUIRED`;
- 607 `SOURCE_ERA_QC2_PHYSICAL_SHADOW_VERIFY_REFERENCES_NOT_AUTO_APPROVED`;
- 38 `MDS_QC1_PHYSICAL_SHADOW_VERIFY_QC_AND_CLOCK_NOT_AUTO_APPROVED`;
- 5 `NATIVE_SOURCE_RH_PRESENT_VERIFY_RH_PROVENANCE_AND_TRANSITION`.

These categories are **not** a complete independent determination that 924 rows lack any mathematical alternative. The Stage25 priority rules may mask source pairs that can be used for exploratory comparisons. None of these P2/P3 records has been authorized for corrected forcing.

The three most relevant locations: US-Vcp 626, US-Wjs 401, US-Vcm 362. Together 1,389/1,574 = 88.25% of remaining P2/P3 original native half-hours.

## Stage26 scientific assessment script

[Stage26 all-1574 P2/P3 paired humidity candidate feasibility and evidence partition](../scripts/stage26/26_reconstruct_p2p3_physics_candidates_research_only.py)

GitHub versioned script path:
`examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage26/26_reconstruct_p2p3_physics_candidates_research_only.py`

Use the pinned commit/SHA provided in operator instructions. Stage26 MUST remain `RESEARCH ONLY`, without modifying the existing user-approved Stage24 166, P1 manual HOLD 46, ten RH saturation-platform check records, or DATM/model.

Original Stage16 all-1750 source pairs and successful Stage25 full cohort crosswalk are matched by **exact native site + half-hour timestamp**. Original Stage24 overlay SHA256 is verified to ensure that no previously approved records silently moved or changed.

For every unapproved P2/P3 timestamp, Stage26 separately computes, *if mathematically permissible*:
1. `ORIGINAL_RH_WITH_SELECTED_T`: source original RH (if 0–100%); source RH sensor provenance still uncertain.
2. `SOURCE_MDS_RH_WITH_SELECTED_T`: original paired `TA_MDS,VPD_MDS` yields RH; then reconstruct `VPD=es_water(original_selected_TA)*(1-RH/100)`. Track original MDS quality codes and T difference.
3. `SOURCE_PROCESSED_ERA_RH_WITH_SELECTED_T`: original source-processed `TA_ERA,VPD_ERA` yields RH; recompute new VPD with selected original TA. **This is not independent ERA5/ERA5-Land**.
4. `SOURCE_ERA_IMPLIED_ACTUAL_VAPOR_PRESSURE_WITH_SELECTED_T`: compute original `e_ERA=es(TA_ERA)-VPD_ERA`; preserve original source-ERA vapor pressure when pairing with tower selected T and derive the corresponding RH and VPD. This is a distinct scientific assumption from conserving ERA RH and must **never** be silently conflated.

The report details all original source QC (QC0 measured, QC1 MDS, QC2 source-ERA), candidate physical feasibility, source-temperature differences including >5°C, episode membership, and alternative options per native timestamp. It produces mutually exclusive evidence subgroups from the available original data to guide efficient human science decisions.

Outputs:
- `stage26_ALL_1574_P2P3_candidate_feasibility.csv`: exactly original 1,574 P2/P3 unapproved HH, each classified with full traceability.
- `stage26_RESEARCH_ONLY_source_RH_MDS_ERA_and_ERA_e_options.csv`: multiple *research-only* reconstruction candidates per HH where physically possible, with original QC/provenance/temperature separation and explicit `approved_for_forcing=NO`.
- `stage26_all10_sites_candidate_feasibility.csv`: site-by-site source alternative availability.
- `stage26_scientific_subgroups_by_site.csv`: finer actionable source/physics clusters for efficient focused decisions.
- `STAGE26_SCIENCE_DECISIONS_AND_CANDIDATES.md`: concise mechanism counts and decisions needed.
- `stage26_summary.json`: immutable input hashes and counts; no change to forcing.

### Pinned one-call IRIDIS6 command

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage26"
  COMMIT="5e0a3956360edf44633ee6353f032a9af50e2bc7"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/26_reconstruct_p2p3_physics_candidates_research_only.py"
  D16="$HOME/ameriflux_batch05_stage16/source_pairs_20261025T225516Z_1291407"
  D25="$HOME/ameriflux_batch05_stage25/crosswalk_20261026T034622Z_1628022"
  D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
     "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage26/26_reconstruct_p2p3_physics_candidates_research_only.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "71b6a71e396d4a65b6b792361b46d616e904e9af"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/science_candidates_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage16-dir "$D16" --stage25-dir "$D25" \
    --stage24-dir "$D24" --out "$OUT" 2>&1 | tee "$BASE/stage26.log"
  echo "STAGE26_REPORTS=$OUT"
  cat "$OUT/STAGE26_SCIENCE_DECISIONS_AND_CANDIDATES.md"
)
```

## Science completion gates

- **No automatic repairs from physically feasible shadow candidates** until the scientist validates source humidity and alternate-reference meteorology. Unlike the explicitly investigator-approved P1 Stage20–24 changes, Stage25/26 P2/P3 has zero new scientific approvals.
- Rows without source-supported options need independent reference: station sensor metadata, source site lat/lon/elevation, source-native-to-UTC conversion, and external ERA5-Land 2-m temperature/dewpoint verified at paired times. Other weather station observations would be independent station evidence; ERA5-Land is a reanalysis, not independent in-situ observed truth.
- The 46 P1 investigator HOLD rows and 10 near-saturated plateaus remain separate. The WCr 2025-08-25 12:00→12:30 VPD jump of 6.033 hPa remains unmodified.
- Versioned *full* forcing for all 10 towers and Post-v5 must await the scientific resolution of residual source anomalies, technical compatibility, temporal consistency, and conservation checks.

**Current status:** Stage25 was run successfully on IRIDIS6; Stage26 is on GitHub, pending operator execution. No original source data, DATM, CIME, or Slurm jobs are edited or submitted.
