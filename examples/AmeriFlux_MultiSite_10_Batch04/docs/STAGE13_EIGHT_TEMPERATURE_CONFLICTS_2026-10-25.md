# Batch04 Stage13 — exact eight unresolved temperature conflicts (science evidence gate)

The operator supplied the **exact eight events still blocked after Stage12's 148/156 resolution**:

| Site | Native timestamp start | Stage12 status |
| --- | --- | --- |
| US-SP1 | 200010091800 | NEIGHBOUR_OR_GRID_TEMPERATURE_NOT_CONFIRMED |
| US-SP1 | 200010091830 | same |
| US-SP1 | 200710151730 | same |
| US-SP1 | 200801160800 | same |
| US-SP1 | 200801160830 | same |
| US-SP1 | 200802030800 | same |
| US-SRG | 201903191200 | same |
| US-Seg | 201612271800 | same |

All eight originate from `SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID` in the original Stage07/Stage08 HOLD ledgers. **These are temperature-evidence conflicts**, not missing ERA5-Land request years. All eight required independent grid site-years were retrieved and SHA-verification succeeded in Stage12.

Do **not** use another blind CDS download or extend a short-gap interpolation cap without examining the tower record. The immediate ±30-minute checks in Stage12 did not establish a safe temperature value; the independent grid alternative also did not meet the fallback constraints. **This result does not by itself prove the original tower sensor is wrong or that ERA5-Land T2m is correct.**

### Stage13 executable: eight-event numerical review

[Stage13 script](../scripts/stage13/13_inspect_eight_temperature_conflicts.py) reads ONLY:
- exact `qcv5_stage12_non_syv_repaired/candidate_20261025T065108Z_6814ab0c` Stage12 receipt/decision ledger;
- SHA-verified ten-site latest Stage12 source selection for each of three implicated stations;
- immutable original FLUXMET temperature, T-QC, VPD, VPD-QC, PA and potential RH at the exact eight native HH times and ±6-hour window;
- original BIF location/UTC_OFFSET and previously SHA-receipted ERA5-Land T2m/D2m/surface pressure source years, on exact UTC time mapping.

For each event, print the original and current values, nearest QC0/1 accepted tower temperatures on **both sides** (up to 6 hours), linearly estimated tower temperature (for comparison only), grid T2m and RH, and one interpretation:
- `TOWER_QC0_AND_EXTENDED_NEIGHBOURS_AGREE_CHECK_OTHER_VARIABLES`: an original trusted tower temperature has longer-window corroboration; protect it, inspect why prior gate remained flagged.
- `HIGH_CONFIDENCE_TWO_SIDED_TOWER_AND_GRID_T_REPAIR_CANDIDATE`: native temperature is missing/nonQC0, longer reliable neighbouring temperatures agree within 4 °C, and the grid temperature agrees with the neighbour interpolation within 5 °C; safe scientific repair *candidate*, not automatic irreversible approval.
- `HOLD_QC0_CONFLICT_REQUIRES_SCIENCE_JUDGEMENT`, `HOLD_TOWER_BRACKETS_NOT_STABLE`, `HOLD_NO_TWO_SIDED_QC01_TOWER_ANCHORS`, `HOLD_GRID_VERSUS_TOWER_CONTEXT_DISAGREES`: more evidence needed; never silently overwrite original QC0.

Stage13 inspection makes **NO changes** to any data, source, NetCDF, Stage07–12 outputs, DATM or Slurm. The subsequent targeted repair should be derived exclusively from numerical evidence for these eight and should be written to a **new versioned full derived candidate**, preserving the previously resolved 148.

### Run on IRIDIS6

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_stage12"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/62ee93c5475219fb05d891921803cb5e6e33550b"
  FILE="$BASE/13_inspect_eight_temperature_conflicts.py"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage13/13_inspect_eight_temperature_conflicts.py" -o "$FILE"
  python3 -B -m py_compile "$FILE"
  python3 -B "$FILE" --self-test
  python3 -B "$FILE" --inspect 2>&1 | tee "$BASE/stage13_inspect.log"
)
```

The pre-existing pinned `12_repair_non_syv_science_holds.py` and `10_era5land_independent_humidity_fill.py` in the **same folder** are imported as verified calculation/data readers. Do not run CDS again. US-Syv's 606 old HOLDs plus 10 skipped jump edges remain deferred.
