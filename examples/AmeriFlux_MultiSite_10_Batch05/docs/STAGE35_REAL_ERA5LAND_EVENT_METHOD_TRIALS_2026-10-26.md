# AmeriFlux Batch05 — Stage34 operator PASS and Stage35 real-reference event-level research candidates

## Stage34 actual IRIDIS6 results confirmed (2026-10-26)

```text
SOURCE VERIFIED
STAGE34 SELF-TEST PASS | 10 operator-pinned CDS ZIP SHA, Stage31 trusted parser, BIF UTC offsets, risk-only science joins
STAGE34 SUCCESS | 10/10 ACTUAL CDS ZIP/NETCDF VALIDATED; MATCHED_NATIVE_HH 429 P1_NON_H01_HOLD 27 RH_PLATFORMS 10 P2P3_REFERENCED 392
STAGE34 SITE_SOURCE US-Vcm P1_MANUAL_HOLD HH 24 RH_REF_MIN_MAX 26.195718 81.792356 REF_ERA_DIFF_GT20 23 REF_MDS_DIFF_GT20 0 CLOSER_MDS 0 CLOSER_ERA 0
STAGE34 SITE_SOURCE US-Vcm P2_P3_ORIGINAL_UNAPPROVED HH 1 RH_REF_MIN_MAX 74.218201 74.218201 REF_ERA_DIFF_GT20 1 REF_MDS_DIFF_GT20 0 CLOSER_MDS 1 CLOSER_ERA 0
STAGE34 SITE_SOURCE US-Vcm RH_SATURATION_PLATFORM_UNAPPROVED HH 4 RH_REF_MIN_MAX 76.18855 83.870845 REF_ERA_DIFF_GT20 0 REF_MDS_DIFF_GT20 0 CLOSER_MDS 0 CLOSER_ERA 0
STAGE34 SITE_SOURCE US-Vcp P1_MANUAL_HOLD HH 3 RH_REF_MIN_MAX 79.477005 79.901184 REF_ERA_DIFF_GT20 3 REF_MDS_DIFF_GT20 0 CLOSER_MDS 0 CLOSER_ERA 0
STAGE34 SITE_SOURCE US-Vcp P2_P3_ORIGINAL_UNAPPROVED HH 382 RH_REF_MIN_MAX 7.090626 56.830259 REF_ERA_DIFF_GT20 6 REF_MDS_DIFF_GT20 280 CLOSER_MDS 10 CLOSER_ERA 323
STAGE34 SITE_SOURCE US-WCr RH_SATURATION_PLATFORM_UNAPPROVED HH 6 RH_REF_MIN_MAX 46.554417 60.030898 REF_ERA_DIFF_GT20 4 REF_MDS_DIFF_GT20 0 CLOSER_MDS 0 CLOSER_ERA 0
STAGE34 SITE_SOURCE US-Wjs P2_P3_ORIGINAL_UNAPPROVED HH 9 RH_REF_MIN_MAX 14.392493 35.01591 REF_ERA_DIFF_GT20 0 REF_MDS_DIFF_GT20 9 CLOSER_MDS 0 CLOSER_ERA 9
STAGE34_REPORTS=/home/ly3n24/ameriflux_batch05_stage34/reference_validation_20261026T131903Z_715715
```

The 429 records are exact **27 P1 manually held source HH, 10 still-unapproved humidity saturation-platform HH, and 392 P2/P3 unapproved source HH**, each paired with downloaded ERA5-Land hourly T/Td/RH by source native timestamp at a 30-minute scientific interpolation stage. The earlier original H01 P1 19 HH have already been investigated in Stages31–33, and **their two adjacent original QC2/QC2 native records have derived RH-water 1.513015% and 3.973442%**. No original sensor data or formal model forcing altered.

## Research interpretation and limitations

US-Vcp original P2/P3 382-source-hour cohort: among 382 reference-matched HH, fresh ERA5-Land RH is >5 percentage points closer to processed source ERA RH than to MDS RH at **323 HH**, closer to MDS at **10 HH**; the remaining **49 HH** are too close/ambiguous or lack both source comparisons. Of 382, **280** differ from original MDS RH by >20 pp, while only **6** differ from processed source ERA RH by >20 pp. This makes the processed source ERA **an effective candidate comparison baseline**, but **cannot validate it as meteorological truth**: the processed source-era and freshly downloaded ERA5-Land are not independent of reanalysis-derived source data. Moreover 34/382 have >5°C gridded-vs-tower air temperature differences; RH and actual vapour-pressure conserved choices are *different*.

US-Wjs first pilot P2/P3 9/9 closer to source processed ERA RH than MDS RH, but this is only **9 of 401 original unapproved P2/P3** at Wjs. Vcm P2/P3 had only one external-matched native time. No blanket inference from the small subset.

Manual P1 H02/H03/H04/H05 27: **26/27** disagree with original processed ERA RH by >20 pp (23/24 Vcm, 3/3 Vcp). These source RH pairings are suspect; downloaded ERA5-Land moisture is research reference, *not original tower-instrument humidity*. The RH platform 10: WCr 6 have fresh grid RH **46.55–60.03%**, Vcm 4 **76.19–83.87%** while original plateaus are 100%/99.46%, suggesting a source-sensor plateau investigation, but actual tower saturation may differ from gridded reference; do not assume all are corrupt.

Original FLUXNET half-hour source timestamps are **local-standard time without DST** and the original BIF `UTC_OFFSET_DATE_END` is missing, so native→UTC mapping remains provisional. Gridded ERA5-Land meteorology is not an independent in-situ station observation. Case-level original sensor metadata/QC and boundary continuity remain required for science approval. Water vapor pressure derived from *dewpoint* uses liquid-water saturation; ice RH if applicable is a separate sensitivity, not an automatic replacement of the model's VPD convention.

## Stage35: numerically compare per-event VPD trial assumptions without original writes

[Stage35 scientific research trials script](../scripts/stage35/35_external_reference_to_tower_VPD_trial_and_episode_decision_matrix_readonly.py)

Pinned original GitHub code commit `6f483c5b0b3673ab344b2388ea0cf583ff744c01`, Git blob SHA `6e4669707aad867e3d7efa0b2a89265d309fb4ae`.

Stage35 reads all 429 exact original Stage34 externally referenced source HH and joins original Stage27 1,574 P2/P3 source RH/QC/episode provenance, previous Stage24 166 approved native overlay, 46 P1 HOLD, ten RH saturation platform HH, and Stage33 H01 immediately adjacent 2 native QC2 records. It creates research-only **physical VPD trial values at ORIGINAL T**:
- source processed ERA RH with tower selected T: `VPD_candidate=es_water(T_tower)*(1-RH_source_ERA/100)` (only when 0<= RH <=100);
- fresh ERA5-Land RH with original tower selected T: `VPD_candidate=es_water(T_tower)*(1-RH_fresh_ERA5L/100)`;
- a *separate* fresh ERA5-Land **actual water-vapor-pressure-preserving** VPD, already computed in Stage34.

It flags source vs external RH disagreements >10/>20 pp, native tower-vs-grid T disagreements >5°C, grid-RH vs original VPD delta >5 hPa, and the two alternative trial VPD differences. These are **screening thresholds**, not science acceptance rules.

Six mutually exclusive **human-review lanes**:
1. `P1_HOLD_GRID_REFERENCE_REVIEW` — 27 original still-held non-H01 P1.
2. `SUSPECT_SATURATED_RH_PLATFORM_REVIEW` — 10 still-unapproved original RH plateaus.
3. `P2P3_REANALYSIS_ERA_CONCORDANT_LOW_T_DIFF` — source ERA and fresh ERA5-Land RH within 10pp, source T vs grid T within 5°C, gridded RH trial relative to original source VPD within 5hPa.
4. `P2P3_REANALYSIS_ERA_CONCORDANT_LARGE_T_OR_SOURCE_CHANGE` — ERA RH concordant but temperature or source VPD trial change too large.
5. `P2P3_SOURCE_MDS_MORE_CONCORDANT_REVIEW` — original MDS RH >5 pp closer to external gridded RH than processed source ERA.
6. `P2P3_REANALYSIS_SOURCE_CONFLICT_OR_UNCERTAIN` — unresolved source difference or inconsistent evidence.

The split is *heuristic*; no automatic approval, and no claim processed source-era and fresh ERA5-Land are statistically independent. Original source-native event/episode grouping is preserved; an event with 10 individually favorable screens is still a **research trial**, not source-validated meter data.

Outputs in a NEW directory:
- `stage35_429_NATIVE_TOWER_VPD_TWO_ERA_METHODS_REVIEW_ONLY.csv`
- `stage35_REFERENCED_P2P3_ORIGINAL_EPISODE_DECISION_MATRIX.csv`
- `stage35_ALL_SITE_SOURCE_CLASS_REVIEW_SUMMARY.csv`
- `stage35_H01_TWO_SUSPECT_QC2_NEIGHBORS_NOT_APPROVED.csv`
- `STAGE35_EVENT_METHOD_CHOICE_AND_REVIEW_SUMMARY.md`
- `stage35_manifest.json`

### IRIDIS6 execution

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage35"
  COMMIT="6f483c5b0b3673ab344b2388ea0cf583ff744c01"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/35_external_reference_to_tower_VPD_trial_and_episode_decision_matrix_readonly.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage35/35_external_reference_to_tower_VPD_trial_and_episode_decision_matrix_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "6e4669707aad867e3d7efa0b2a89265d309fb4ae"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/science_VPD_trial_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" \
    --stage34-dir "$HOME/ameriflux_batch05_stage34/reference_validation_20261026T131903Z_715715" \
    --stage27-dir "$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604" \
    --stage24-dir "$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604" \
    --stage33-dir "$HOME/ameriflux_batch05_stage33/H01_neighbors_and_external_refs_20261026T122415Z_3242355" \
    --out "$OUT" 2>&1 | tee "$BASE/stage35.log"
  echo "STAGE35_REPORTS=$OUT"
  cat "$OUT/STAGE35_EVENT_METHOD_CHOICE_AND_REVIEW_SUMMARY.md"
)
```

**Stage35 GitHub code submitted, operator execution PENDING.** All 166 previously approved, 46 P1 manual HOLD, 1574 original P2/P3 unapproved and 10 suspect RH platform HH remain unchanged; no new forcing files, source or model modification permitted.
