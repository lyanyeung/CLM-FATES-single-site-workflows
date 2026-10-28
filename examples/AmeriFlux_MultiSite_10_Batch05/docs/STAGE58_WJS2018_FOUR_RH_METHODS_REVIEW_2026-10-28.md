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

## Actual Stage58 IRIDIS6 result — 2026-10-28 22:47 UTC

After the corrected Stage58 source and launcher, the operator reports actual successful execution:
```
STAGE58 SOURCE VERIFIED
STAGE58 SELF-TEST PASS
STAGE58 SOURCE VERIFIED | original 174 overlay unchanged, 30 held original Wjs HH
STAGE58 QC0 ANCHOR BIASES RH_pp LEFT 33.237 RIGHT 33.906 LEFT_RH 100.000 RIGHT_RH 92.127 SPAN_HOURS 15.5
STAGE58 SUCCESS | 30 held HH compared, 174 original overlay SHA preserved; no approvals
```

Per-method original QC0-adjacent transition results:

| Method | First edge VPD jump hPa | Last edge VPD jump hPa | Maximum consecutive VPD jump hPa | >2 hPa transitions | RH clips |
|---|---:|---:|---:|---:|---:|
| Original unchanged | +5.398 | −7.397 | 7.397 | 3 | 0 |
| RH linear interpolation (15.5 h) | +0.0151 | +0.0786 | 0.0919 | 0 | 0 |
| AmeriFlux source-processed ERA RH | +1.4076 | −1.2059 | 1.4076 | 0 | 0 |
| Downloaded ERA5-Land RH at tower T | +1.8950 | −2.3445 | 2.3445 | 1 | 0 |
| ERA5-Land RH + linearly interpolated QC0 anchor RH bias | 0 | +0.2949 | 0.2949 | 0 | **28/30** |

Result:
`/home/ly3n24/ameriflux_batch05_stage58/wjs2018_compare_four_methods_20261028T224753Z_551429`.

**Scientific interpretation.** RH-linear interpolation between 19:00 QC0 RH=100% and next-day 10:30 QC0 RH=92.127% is by far the smoothest number series but cannot prove actual humidity stayed nearly saturated across 15 hours. Processed source ERA RH yields numerically valid candidates but shows 19–26pp drier RH than original QC0 tower anchor data. Direct downloaded ERA5-Land RH is 33.2–33.9pp drier at both measured ends, and >2hPa at the trailing edge. ERA5-Land + RH bias correction forces 28/30 source hours above 100% RH to be clipped to exactly 100%, so is scientifically unacceptable as an evidence-derived continuous station humidity series. All 30 half hours remain **science HOLD**; no new approval and the previously approved 174 overlay is unchanged.

Next Stage59 checks the **original FLUXMET humidity field availability, original sensor/filled provenance and weather context**, rather than approving 15h interpolation from boundary smoothness. It requires no new CDS download and produces only new reports. [Stage59 Python](../scripts/stage59/59_Wjs2018_original_humidity_and_weather_field_provenance_READONLY.py) immutable commit `0ed28039bc79f9a7dfd02dc75e946d98908af14c`, blob `786ca0cde9ab6245634e7c49a39ac7f21f001902`; [Stage59 launcher](../scripts/stage59/run_stage59_iridis6.sh) immutable commit `644317d9a45757c7f50772f61e3d77f1720ba36b`, blob `b9009d8a7611d8eb8dd691924eb95716358f8235`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/644317d9a45757c7f50772f61e3d77f1720ba36b/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage59/run_stage59_iridis6.sh" -o "$HOME/run_stage59.sh" && test "$(git hash-object "$HOME/run_stage59.sh")" = "b9009d8a7611d8eb8dd691924eb95716358f8235" && bash "$HOME/run_stage59.sh"
```

Stage59 GitHub code hash verified. Actual Stage59 IRIDIS6 compile/self-test and run pending. Stage59 does **not** modify any approved or original model inputs.

## Actual Stage59 operator PASS, new original VPD_MDS science-priority evidence (28 October 2026)

```
STAGE59 SELF-TEST PASS
STAGE59 SUCCESS | 49 raw original FLUXMET HH inspected, 30 Wjs-2018 QC1 HOLD unchanged, 174 approved unchanged
STAGE59 SATURATED_SOURCE_QC0_LEFT_PLATEAU 9 HH 201803111500 201803111900
STAGE59 FIELD VPD_F_MDS 30 /30
STAGE59 FIELD VPD_F_MDS_QC 30 /30
STAGE59 FIELD RH 0 /30
```

Original source file:
`/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-Wjs/forcing/raw/AMF_US-Wjs_FLUXNET_2007-2025_v1.3_r1/AMF_US-Wjs_FLUXNET_FLUXMET_HH_2007-2025_v1.3_r1.csv`
SHA256 `9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6`.
Original Stage59 report:
`/home/ly3n24/ameriflux_batch05_stage59/wjs2018_original_49HH_weather_source_20261028T233732Z_861557`.

At the original 2018-03-11 19:00→19:30 boundary, T changed from −0.057 to −0.401°C, wind from 3.687 to 3.858 m/s, pressure from 81.271 to 81.288 kPa, measured-selected VPD jumped from 0 to 5.398 hPa while the RH original field went from 100% to missing and VPD QC from 0 to 1. Demonstrates a likely VPD observation-to-filled-source transition, but cannot independently establish a sensor defect or 15 h near-saturation humidity. Source precipitation `P_F` was zero in printed key records, but zero precipitation does not exclude fog/dew nor demonstrate no sensor platform issue. The 9 original QC0 saturated half hours precede the 30 held VPD-QC1 half hours.

**Critical new lead:** original source includes `VPD_F_MDS` and its QC at all 30 held half hours. Their **values and QC distribution have not been shown yet**. The next decision must examine whether `VPD_F` simply inherits MDS gap-filled VPD; MDS is model/gap-fill provenance, never independent measured tower RH.

Stage60 read-only source/QC comparison script: [Stage60 Python](../scripts/stage60/60_Wjs2018_original_VPD_MDS_QC_49HH_READONLY.py) commit `e3a8032b9e21d6ade1475e7caa2b3d93b81ecf6d`, blob `3a7cf4365b7168620c758992e7c33e0faee0a1b2`; [launcher](../scripts/stage60/run_stage60_iridis6.sh) commit `c5e2c156bc95fcb925d2e5f897638bc12f5acb79`, blob `0c6c050e0fb05f09a1153030b6df21c5efca83c5`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/c5e2c156bc95fcb925d2e5f897638bc12f5acb79/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage60/run_stage60_iridis6.sh" -o "$HOME/run_stage60.sh" && test "$(git hash-object "$HOME/run_stage60.sh")" = "0c6c050e0fb05f09a1153030b6df21c5efca83c5" && bash "$HOME/run_stage60.sh"
```

Stage60 code and immutable source SHA are GitHub verified; actual IRIDIS6 Stage60 compile, self-test and execution are **pending**. Earlier Stage56 174 and Stage59 original 30 HH HOLD remain unchanged; this step does no external downloads or Slurm submission.
