# Batch04 Stage17 — remaining six QC0 temperature conflicts, read-only diagnostic

**Status (2026-10-25): Stage16 VERIFIED PASS by IRIDIS6 operator. Stage17 CODE PUBLISHED; NOT YET RUN ON IRIDIS6.** This stage cannot release science HOLDs, approve Post-v5/DATM or submit model jobs.

References: [Stage16 actual verified output](STAGE16_VERIFIED_FULL_SOURCE_AUDIT_2026-10-25.md) and [Stage17 Python source](../scripts/stage17/17_audit_remaining_six_native_temperature_conflicts.py).

Six original events: US-SP1 200710151730 (11.150°C), 200801160800 (−8.211°C), 200801160830 (−4.365°C), 200802030800 (−3.613°C); US-SRG 201903191200 (0.718°C); US-Seg 201612271800 (0.015°C). Original tower TA_QC=0 at all six times. Stage14 numerically repaired humidity physics but did not validate or alter these tower temperatures. The two Stage15 trial times from 2000-10-09 are additionally still science HOLDs: **8/8 held**. US-Syv 606 original science HOLDs plus 10 Stage07 ERA jump-edge skips remain deferred.

## IRIDIS6 command (download pinned source; no git pull)

~~~bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_stage17"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  STAGE17_COMMIT="c28c0faf137fc2aa5170781fcaeed46c07cbd4dd"
  DEPENDENCY_COMMIT="9be06860ee3e9f14e08fb078d22d0090b49d58d4"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$RAW/$STAGE17_COMMIT/$REL/stage17/17_audit_remaining_six_native_temperature_conflicts.py" -o "$BASE/17_audit_remaining_six_native_temperature_conflicts.py"
  curl -fLsS --retry 3 "$RAW/$DEPENDENCY_COMMIT/$REL/stage13/13_inspect_eight_temperature_conflicts.py" -o "$BASE/13_inspect_eight_temperature_conflicts.py"
  curl -fLsS --retry 3 "$RAW/$DEPENDENCY_COMMIT/$REL/stage12/12_repair_non_syv_science_holds.py" -o "$BASE/12_repair_non_syv_science_holds.py"
  curl -fLsS --retry 3 "$RAW/$DEPENDENCY_COMMIT/$REL/stage10/10_era5land_independent_humidity_fill.py" -o "$BASE/10_era5land_independent_humidity_fill.py"
  for script in "$BASE"/*.py; do python3 -B -m py_compile "$script"; done
  python3 -B "$BASE/17_audit_remaining_six_native_temperature_conflicts.py" --self-test
  python3 -B "$BASE/17_audit_remaining_six_native_temperature_conflicts.py" --audit \
    2>&1 | tee "$BASE/stage17_six_T_conflicts_readonly.log"
)
~~~

## Scientific and integrity gates

Stage17 checks the final Stage12 148/156 and Stage14 8/8 receipts, all eight original temperature-HOLD timestamps, Stage14 ten-site SHA manifest, full Stage14 source SHA checks for US-SP1/US-SRG/US-Seg, original BIF SHA and approved coordinates/UTC offset. It compares original and Stage14 tower TA/QC against **already downloaded** independently verified ERA5-Land temperatures at 25 surrounding half-hours (±6 h), prints the nine centered half-hours (±2 h) and reports tower-minus-grid T residuals with a median/MAD neighbor baseline. It does not request new CDS data.

**Do not assume an ERA5-Land temperature mismatch proves an original QC0 sensor measurement is false.** Check stable original neighboring tower observations, sensor/instrument history, source clock and meteorological context before considering any isolated alternative. No automatic interpolation, mutation, Post-v5, DATM, CIME or Slurm work is permitted.

After execution, provide the full file at ~/ameriflux_batch04_stage17/stage17_six_T_conflicts_readonly.log. Until actual IRIDIS6 results are provided, Stage17 remains **NOT VERIFIED**.
