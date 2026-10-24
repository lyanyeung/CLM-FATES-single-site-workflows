# Batch04 Stage09 — immediate direct native-source humidity repair after Stage08

**Date:** 2026-10-24. **Current status:** Stage08 seven-station full candidate output verified; Stage09 script has been committed, **not yet executed on IRIDIS6**.

- **Stage08 baseline**: `qcv5_stage08_remaining_seven_candidates/candidate_20261024T120137Z`, with full derived outputs and SHA receipts.
- **Stage09 targets**: US-Rpf's **688** invalid paired ERA humidity HOLD entries and US-SRM's **1** analogous HOLD; leave **US-Syv** for later as explicitly requested by the user.
- **Stage09 performs actual data fixes** when justified; it does not just write a report.

## Repair policy

1. If the tower original `TA_F,VPD_F` pair is physically consistent at an ERA-invalid HOLD, **retain original VPD_F**, including QC0. If the original raw `RH` is missing/negative/>100.05%, derive only `RH=100*(1−VPD_F/es_water(TA_F))`; never force an invalid companion ERA humidity value into it.
2. If the original tower VPD is missing, negative or exceeds `es_water(TA_F)`, identify exact contiguous native HH invalid time runs. For **1–4 half-hour records only**, interpolate the **VPD_F** between two valid, source-native **QC0/QC1** endpoints in the **same calendar year**, provided endpoint temperature difference <=8°C and VPD difference <=5 hPa and every interpolated value is physically valid at its **unchanged tower TA_F**. Recompute matching RH for those repaired VPD values.
3. If the gap is >4 HH, boundaries invalid, year crossed or interpolation gives supersaturated/invalid humidity, **retain HOLD**. Do not silently clip or use broken packaged `TA_ERA,VPD_ERA`.
4. Do not touch US-Seg/US-Ses/US-Slt/US-SRG/US-Uaf Stage08 derived outputs, or the three earlier Stage07 outputs; other sites can be referenced by already recorded SHA and paths.
5. Create **two complete new source-length derived FLUXMET HH CSVs** for US-Rpf and US-SRM, sparse change ledger, grouped invalid original-VPD episodes, remaining HOLD CSV for Stage08, and SHA256 receipt. All original/Stage08/Stage07 are immutable; mark **INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP**.

## Run on IRIDIS6

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/c794f403bac063092d17030d1939121fae3b94a9"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage09"
  SCRIPT="$BASE/scripts/stage09/09_repair_ERA_invalid_native_humidity_short_gaps.py"
  mkdir -p "$(dirname "$SCRIPT")"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage09/09_repair_ERA_invalid_native_humidity_short_gaps.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --apply 2>&1 | tee "$BASE/stage09_apply.log"
)
```

**Important:** Stage09 scientific results (actual safely repaired vs remaining 688+1 cases) cannot be stated until the operator runs the script. It will fail without modifying sources if the Stage08 SHA differs. Existing total Batch04 1,450 inherited HOLD entries are not all resolved by this station-focused step. No source, processed_v5, DATM or CLM-FATES model changes are permitted.
