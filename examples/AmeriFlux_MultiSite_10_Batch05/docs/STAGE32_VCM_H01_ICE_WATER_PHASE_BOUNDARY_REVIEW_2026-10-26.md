# Batch05 Stage31 operator PASS and Stage32 phase-aware H01 decision evidence

## Operator Stage31 actually completed (26 October 2026)

```text
STAGE31 SELF-TEST PASS
STAGE31 SUCCESS | SHA verified abda0a706aef79dc0eb7a8b50db1b66ed427c8a756b81965d9bb3dba2e315646
CONTAINER ZIP NETCDF_MEMBERS 1 UTC_HOURS 96 H01_MATCHED_HH 19
STAGE31 GRID_LOCATION 35.90000000000108 -106.50000000001012
STAGE31 ERA5L_RH_pct_min 67.680542
STAGE31 ERA5L_RH_pct_max 78.046519
STAGE31 ERA5L_minus_tower_T_C_min -6.002364
STAGE31 ERA5L_minus_tower_T_C_max -2.4203
STAGE31 ERA5L_RH_grid_vs_source_ERA_pp_abs_max 82.689076
STAGE31 VPD_RH_transport_vs_e_transport_abs_max_hPa 0.76648507
STAGE31 hypothetical_e_transfer_negative_VPD_count 0
STAGE31 H01_MANUAL_HOLD=19 REMAINS; APPROVED166/HOLD46/P2P3_1574/DATM/SLURM UNCHANGED
STAGE31_REPORTS=/home/ly3n24/ameriflux_batch05_stage31/H01_external_reference_20261026T120354Z_3242355
```

**Interpretation:** all 19 original H01 US-Vcm native half-hours (2007-12-15 21:00 through 2007-12-16 06:00) have missing original tower RH. Bundled source processed ERA-inferred RH was **negative −12.21% to −0.71%** (physically inconsistent), but independently retrieved ERA5-Land *grid reference* RH relative to liquid water is **67.68% to 78.05%**, based on actual downloaded and parsed hourly UTC 2 m T and Td. This demonstrates that original source ERA RH is not suitable to reproduce physical humidity under the prior pairing and provides a plausible external reference, **not an actual in-situ humidity measurement or proof of tower RH**. ERA5-Land 2m T is 2.42–6.00°C lower than tower selected T, so transport choices and elevation are material.

**Important uncertainty**: original BIF UTC_OFFSET = -7h source start-date group 2007-01-01, but original DATE_END absent. Source FLUXNET TIMESTAMP_START is start of its native half-hour averaging interval. ERA5-Land hourly time-series T/Td are gridded model meteorology. A direct native-start-time linear interpolation is only a first scientific comparison; source vs ERA temporal phase/averaging and elevation corrections require a separate check.

## Stage32 science: distinguish dewpoint (water) from frostpoint (ice)

Sources:
- ECMWF ERA5 near-surface humidity guide: https://confluence.ecmwf.int/pages/viewpage.action?pageId=185075432 — near-surface dewpoint `Td` is used to compute water-relative actual vapour pressure, and water/ice/mixed saturation denominators can be used for RH at air temperature.
- National Physical Laboratory (NPL) humidity formulas: https://www.npl.co.uk/resources/q-a/dew-point-and-relative-humidity — water Magnus `esw(T)=6.112exp(17.62 T/(243.12+T))` and ice Magnus `esi(T)=6.112exp(22.46 T/(272.62+T))` in hPa, T in °C. Stage32 retains existing Stage31 water formula `6.112exp(17.67 T/(243.5+T))` for exact comparison and uses NPL ice formula only as subzero sensitivity.
- FLUXNET clock convention: https://fluxnet.org/data/aboutdata/data-variables/ — local standard time (no DST), source timestamp semantics.

**Never use `es_ice(Td)` to reconstruct actual vapor pressure from ERA5-Land dewpoint**: a dewpoint is not a frost point. Stage32 computes:
- `e = es_water(Td)` — gridded actual water vapor pressure;
- `RH_water=100 e / es_water(T_grid)`;
- `RH_ice=100 e / es_ice(T_grid)`, for Tgrid below zero;
- `VPD_water=es_water(T_grid)-e`;
- `VPD_ice=es_ice(T_grid)-e`;
- four alternate *research-only* tower-T VPD estimates: preserve gridded RH_water, preserve gridded e over water, preserve gridded RH_ice, preserve gridded e over ice.

Over ice RH can be >100% in cold supersaturated air and ice-based VPD can be negative: the science report **never clips these** to make an aesthetically smooth graph. The current model's VPD convention and source RH processing must be explicitly checked before changing any CLM forcing.

## Stage32 GitHub script and operator command

[Stage32 script](../scripts/stage32/32_Vcm_H01_19HH_ice_water_phase_and_boundary_sensitivity_readonly.py).

Pinned source GitHub commit: `c836fafe1da0e13027fab56b5996bc132f3cdfd4`; verified Git blob SHA: `97d8e6a746e7dd32ca4c26c4a549a9ffd6bc30af`.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage32"
  COMMIT="c836fafe1da0e13027fab56b5996bc132f3cdfd4"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/32_Vcm_H01_19HH_ice_water_phase_and_boundary_sensitivity_readonly.py"
  D31="$HOME/ameriflux_batch05_stage31/H01_external_reference_20261026T120354Z_3242355"
  D18="$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929"
  D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage32/32_Vcm_H01_19HH_ice_water_phase_and_boundary_sensitivity_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "97d8e6a746e7dd32ca4c26c4a549a9ffd6bc30af"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/H01_phase_boundary_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" \
    --stage31-dir "$D31" --stage18-dir "$D18" --stage24-dir "$D24" \
    --out "$OUT" 2>&1 | tee "$BASE/stage32.log"
  echo "STAGE32_REPORTS=$OUT"
  cat "$OUT/STAGE32_H01_PHASE_BOUNDARY_SCIENCE_DECISION.md"
)
```

Expected all read-only science outputs:
- `stage32_H01_19_water_ice_RH_and_four_VPD_trials_UNAPPROVED.csv` exact 19 native half-hours with phase and alternate moisture-transfer methods;
- `stage32_H01_original_plus_minus3hour_source_and_overlay_context.csv` native original and selected **existing versioned overlay** context before and after H01;
- `stage32_H01_8_boundary_method_sensitivity_checks.csv` two edges × four **unapproved** tower-T VPD transfer hypotheses;
- `STAGE32_H01_PHASE_BOUNDARY_SCIENCE_DECISION.md` complete 19-timepoint tables and boundary evidence;
- `stage32_manifest.json` original input checksums and status, no production writes.

**Status:** Stage31 operator successful; Stage32 code committed, IRIDIS6 actual run pending. Science approvals unchanged: Stage24 overlay 166 (original 130 P1 + 36 context/nonoriginal flagged), P1 manual HOLD 46 (including H01 19), original P2/P3 unapproved 1574, unapproved saturation platforms ten. No model-ready forcing or Slurm.
