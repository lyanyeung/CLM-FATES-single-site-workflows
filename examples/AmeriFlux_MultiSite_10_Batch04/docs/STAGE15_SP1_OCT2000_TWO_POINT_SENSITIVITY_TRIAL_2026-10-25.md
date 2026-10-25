# Stage15 experimental US-SP1 2000-10-09 two-point TA sensitivity trial

**Status:** Stage14 operator output completed **8/8 VPD/RH physical closure candidates**, three full derived CSVs, all eight tower-temperature scientific HOLDs preserved. All source files and the exact eight repair values are documented in [Stage14 verified report](STAGE14_VERIFIED_8_HUMIDITY_CLOSURE_QC0_T_HOLDS_2026-10-25.md).

## Why examine just two temperatures now?

Stage13 original US-SP1 native local-standard half-hours on **2000-10-09** show:

| Native time | Original TA °C | TA QC | ERA5-Land T2m °C | Interpretation |
|---|---:|---:|---:|---|
| 17:30 | 11.000 | 0 | — | original left anchor |
| **18:00** | **−6.900** | **0** | **14.371** | suspect isolated negative spike |
| **18:30** | **−7.100** | **0** | **13.776** | suspect isolated negative spike |
| 19:00 | 17.545 | 1 | — | original right anchor |

Flanking history: 16:30=14.0 QC0; 17:00=12.6 QC0; 19:30=17.541 QC1; 20:00=17.536 QC1. Each 18:00/18:30 source VPD was also physically impossible at the recorded negative temperatures; Stage14 already recomputed only VPD/RH for them using independent humidity.

For a **strict alternative sensitivity trial, not a declaration of tower-sensor truth**, interpolate T linearly from 17:30 (11.0°C) to 19:00 (17.545°C) across the two suspect native HH:

- 18:00: proposed T=**13.1816666667°C**; ERA5-Land T≈14.371°C, difference ≈1.19°C.
- 18:30: proposed T=**15.3633333333°C**; ERA5-Land T≈13.776°C, difference ≈1.59°C.

The independent grid corroborates approximate *range* but not the precise time trajectory; do not claim scientific validation. Only the alternative full CSV updates the two T values; its `TA_F_QC` is set to **1** to denote gap-filling (original QC0 retained in a separate immutable provenance ledger). Stage14's independently derived RH stays unchanged and VPD is recomputed from the proposed T using identical saturation formula.

**Stage15 code committed (not yet run):** [15_sp1_oct2000_two_point_temperature_sensitivity.py](../scripts/stage15/15_sp1_oct2000_two_point_temperature_sensitivity.py), pinned commit `f8e83e08dc60c1843b12964a4441b508b4705173`.

Script demands exact Stage14 SHA for US-SP1 `3f2489eea6e7016b3c184bd90c93acd6597d32fc3d4cc8872ac28237a5181806`, exact eight-target Stage14 provenance, original flanking TA+QC records, BIF SHA/UTC offset, and existing Stage10 independent 2000 grid with exact-hours temperature agreement <=2.5°C before writing. **If any evidence differs, it halts without editing existing sources.** Only 1 new full source candidate (US-SP1) and one alternative ten-site manifest are created, no other nine station files duplicated.

### IRIDIS6 commands

The existing Stage10 Python helper must be next to the downloaded Stage15 Python script in the established `$HOME/ameriflux_batch04_stage12` local directory:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_stage12"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/f8e83e08dc60c1843b12964a4441b508b4705173"
  FILE="$BASE/15_sp1_oct2000_two_point_temperature_sensitivity.py"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage15/15_sp1_oct2000_two_point_temperature_sensitivity.py" -o "$FILE"
  python3 -B -m py_compile "$FILE"
  python3 -B "$FILE" --self-test
  python3 -B "$FILE" --assess
  python3 -B "$FILE" --trial | tee "$BASE/stage15_trial.log"
)
```

**Important:** In both Stage14 and Stage15, there remain **8 unresolved tower-temperature scientific questions** pending eventual source-of-truth review; the Stage15 two-point alternative does not clear two official HOLDs. Stage14 original version remains the principal temperature-unchanged candidate and Stage15 is a separate sensitivity branch. **US-Syv 606 original science HOLDs and 10 unrepaired Stage07 ERA edges remain deferred.** No DATM/CIME model run is authorised.
