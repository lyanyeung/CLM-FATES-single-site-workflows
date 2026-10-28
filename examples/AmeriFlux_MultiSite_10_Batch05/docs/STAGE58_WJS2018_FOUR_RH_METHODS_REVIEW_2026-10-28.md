# Stage58 — US-Wjs March 2018, compare four RH repair hypotheses without science approval

User-executed Stage57 succeeded on 28 October 2026, including one real CDS ERA5-Land point-timeseries download for 2018-03-11/13. Exact original output:
`/home/ly3n24/ameriflux_batch05_stage57/wjs2018_actual_ERA5Land_20261028T195055Z_4119241`.
Stage56 separately verified and versioned the user-approved 174 native half-hours including UMB 2009 2 HH and Wjs 2021 6 HH. **Wjs March 2018 30 HH remain science HOLD**.

At March 2018 Wjs QC0 anchors, tower RH (100.000% at 2018-03-11 19:00 and 92.127% at 2018-03-12 10:30) is respectively 33.237315 and 33.90575 percentage points wetter than the downloaded ERA5-Land grid RH (66.762685% and 58.221250%). Applying grid RH at tower T would imply VPD 2.02307736 and 3.56227871 hPa, vs actual QC0 VPD 0 and 0.672. **Direct grid RH replacement is therefore not approved**. Even grid RH bias adjustment can exceed 100%, which must be explicitly flagged rather than silently passed off as a tower measurement.

[Stage58 read-only method comparison](../scripts/stage58/58_Wjs2018_compare_30HH_humidity_methods_READONLY.py) compares each of the 30 original VPD-QC1, missing-RH half-hours:
1. Original source VPD baseline.
2. Linear original tower-RH interpolation across 15.5 h between QC0 anchors.
3. AmeriFlux product processed-source ERA RH at tower original TA.
4. Freshly downloaded ERA5-Land grid RH at original tower TA.
5. Sensitivity only: independent grid RH plus interpolated tower-minus-grid RH anchor bias, reporting every RH value clipped to 100% or 0%.

Four candidate methods vs one original baseline; candidate approval remains **NO** for all. For each method, evaluate original QC0 left/right boundary VPD differences, maximum internal jump, number of new >2 and >4 hPa jumps, physical VPD and bias-correction clip counts. The 15.5-hour interpolation passing a numerical boundary screen is **not evidence** of actual 15-hour station humidity.

Source code immutable commit `87b511c9e5efbc68c8ef7393b71afa085ed74997`, blob `e600e0c0e65519053100043c839a6d376e9ae517`.
[Stage58 IRIDIS6 launcher](../scripts/stage58/run_stage58_iridis6.sh) immutable commit `57db605f8d579db50d7a582c4d7ff3e4a55a3dcd`, Git blob `626de6f3e34561c8c03835a7789a663d18502669`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/57db605f8d579db50d7a582c4d7ff3e4a55a3dcd/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage58/run_stage58_iridis6.sh" -o "$HOME/run_stage58.sh" && test "$(git hash-object "$HOME/run_stage58.sh")" = "626de6f3e34561c8c03835a7789a663d18502669" && bash "$HOME/run_stage58.sh"
```

Status: GitHub source/launcher committed, pins checked; Stage58 still requires operator runtime validation. The script requires no CDS download and no Slurm submission, and cannot touch original sources, prior 174, or production DATM.

## First operator attempt and syntax-only patch (2026-10-28)

Operator verified the launcher/source SHA; `python3 -B -m py_compile` stopped **before data reading or any output directory write**:

```text
STAGE58 SOURCE VERIFIED
File ".../stage58.py", line 206
  2018_original_HOLD_HH=30,scientific_approvals_new=0,
      ^
SyntaxError: invalid decimal literal
```

Python keyword argument names cannot begin with a number. Replaced ONLY this invalid manifest-key identifier with `Wjs_2018_original_HOLD_HH=30`. This is metadata naming only; the four candidate method formulas, 30 source HOLDs and original 174 overlay are unchanged.

- Corrected Stage58 Python source commit `36b69555042813317de01d6dd57c71f44eff6795`, Git blob SHA `eaee8cffe61a53b59b5fd0223fad1bf9e89d693d`.
- Corrected launcher commit `02abb45713b3cbd0f5c2258640bd8da9d82611b5`, Git blob SHA `fa670f6b3d2d318f14440036704f0aa45633560b`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/02abb45713b3cbd0f5c2258640bd8da9d82611b5/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage58/run_stage58_iridis6.sh" -o "$HOME/run_stage58.sh" && test "$(git hash-object "$HOME/run_stage58.sh")" = "fa670f6b3d2d318f14440036704f0aa45633560b" && bash "$HOME/run_stage58.sh"
```

Corrected source/launcher SHA verified through GitHub. An actual IRIDIS6 compilation and execution of the corrected version is required to establish success; the first attempt was syntax-only failure.
