# Batch04 US-Syv — SYVH2 final QA, 18 native QC0 RH closure and one rounding exception (2026-10-26)

## Operator-confirmed scientific status

- All **11 relevant independent ERA5-Land site-years** retrieved, SHA/grid/UTC validated.
- Latest operator-verified SYVH1 candidate: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_US_Syv_stage_SYVH1_433_humidity_era5land_candidate_not_approved/candidate_20261026T033139Z_a8699ac8`, full 438288 native half-hour SHA256 **`265d92fc7d3cc8c3d3dff6b93067d9fc380969131ab044c08bd192c1ceb9b1cc`**.
- The **415 originally physically invalid VPD** source-HOLD half-hours have been corrected with **415 independently verified ERA5-Land T2m/d2m/SP relative humidity**, projected to retained source-selected `TA_F`. All user-approved previous **106 +191 =297** temperature alternatives preserved and ten-site manifest other nine entries unchanged.
- Final **18 old historical ERA-grid humidity source HOLD** native half-hours are **all in 2021** with original **`TA_F_QC=0`, `VPD_F_QC=0`**; VPD is **already physically valid**, but derived RH differs from `100·(1−VPD/es_water(TA))` by **0.787–1.497 percentage points**. Original source reason: 17 ERA_PAIR_HUMIDITY_INVALID, 1 ERA_RH_OUTSIDE_QCV5_USABLE_RANGE. **Recommended: retain original T and VPD with both QC0; recompute derived RH only for 18**, and preserve historical source ERA fault codes in a separate immutable archive/provenance ledger.
- One unexpected full-file numerical flag at **2008-03-09 13:00**, `TA_F=-6.234°C`, `VPD_F=3.842hPa`. Thermodynamic saturation `3.841976803313088hPa`; excess `0.0000231966869hPa` (relative 0.0006038%). Source VPD saved to three decimals; its ±0.0005hPa resolution encompasses this tiny difference. **Keep source TA/VPD/QC unchanged; audit and document rounding-compatible exception, never blindly cap VPD.** No other strict global VPD-physical failures in full 438288-HH latest site scan.

## Next operation — new independent research candidate, not yet performed on IRIDIS6

[Source SHA-pinned SYVH3 last-18-RH-only closure code](../scripts/manual_review/stage_syvh3_close_18_qc0_vpd_valid_derived_rh_and_rounding_audit.py), GitHub commit `349a56d277af0ad62a1d31a5d8812f2b622670e6`.

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="349a56d277af0ad62a1d31a5d8812f2b622670e6"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  mkdir -p "$BASE"
  SCRIPT="$BASE/stage_syvh3_close_18_qc0_vpd_valid_derived_rh_and_rounding_audit.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/stage_syvh3_close_18_qc0_vpd_valid_derived_rh_and_rounding_audit.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --assess 2>&1 | tee "$BASE/US_Syv_SYVH3_18_QC0_RH_preflight.log"
  python3 -u -B "$SCRIPT" --apply 2>&1 | tee "$BASE/US_Syv_SYVH3_18_QC0_RH_candidate.log"
)
```

This creates a new full **438288-HH** US-Syv research-only source version and a new exact ten-site research manifest, auditing every changed and unchanged native row, and permits **only 18 RH cell changes**. Independently validate the one rounding exception. All 297 approved temperature repairs, 415 independent ERA5-Land humidity repairs, original observed source values, and other 9 site source selection pointers remain unchanged.

**No additional human decision necessary at present** for those source-verified 18 QC0 VPD records. If the operator-run --assess finds unexpected QC/provenance/physics, stop and escalate only those exceptional native HH. **Post-v5 / DATM / CIME / Slurm / CLM-FATES is still blocked** until final all-ten-site selected forcing input QA. The SYVH3 script is committed but not yet executed on IRIDIS6.
