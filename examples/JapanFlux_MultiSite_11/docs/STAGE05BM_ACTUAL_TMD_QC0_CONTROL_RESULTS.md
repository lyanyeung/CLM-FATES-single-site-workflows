# Stage05BM: actual Tmd non-event QC0 controls and review priorities

The operator supplied the Stage05BM terminal output from the predefined plan onwards, not the earlier download-hash or test lines. Three CDS control-day requests succeeded and Stage05BM reported completion, input integrity gates, all 45 HOLD and zero approved values. The operator's run directory is `/home/ly3n24/japanflux_stage05bm/run_20261104T025844Z_890800`; this reviewer did not read IRIDIS6 files directly. Pasted terminal text SHA256 is `e0a71a42ab4e7afac7a7327f5452f519a63bcc10f8d707e7a8f440810ebe6b4c`.

The control days were selected by eligible sample counts before looking at their values. Under UTC+9:

| Tmd control (UTC day) | QC0 half-hours | Mean selected-minus-QC0 | Selected MAE | Descriptive p95 absolute error |
|---|---:|---:|---:|---:|
| TA 2005-08-14, near | 44 | −0.7543 °C | 0.8111 °C | 1.9178 °C |
| TA 2005-08-19, later | 44 | +0.9153 °C | 0.9153 °C | 1.9368 °C |
| LW_IN 2005-09-10, later | 35 | −16.8364 W/m² | 16.8591 W/m² | 41.3713 W/m² |

The p95 is descriptive over autocorrelated half-hours, not a confidence bound. These are other-time controls, not verification of event-time truth. The control-day TA biases change sign. The longwave control is almost entirely negatively biased and is about a month from the event. Weather, season, cloud, site/grid representativeness, input processing and unresolved clock conventions limit transfer to the event or other groups. Four saved clock scenarios give TA MAE ranges of 0.727–0.960 °C for Aug 14 and 0.725–1.054 °C for Aug 19; LW MAE is 16.860–17.455 W/m². These ranges are sensitivities, not error bars or proof of the real clock.

The 2005 Tmd LW selected background correction under UTC+9 is +6.337388888888881 W/m² (existing Stage05AZ group result). The printed selected-error mean and MAE imply the sum of all positive selected errors is `35 * (MAE + mean) / 2 = 0.3966111 W/m²`. Each individual positive error is therefore less than 6.3374; subtracting the fixed offset makes **all** raw-grid errors negative. Consequently the uncorrected grid MAE on these same 35 controls is `-mean_selected + 6.337388888888881 = 23.1738 W/m²`. This derived result is conditional on the printed values and the previously saved median, and will be checked directly from the saved pairs. It shows improvement for this single control day while retaining a notable negative residual; it does not validate the event value or establish that another correction should be applied.

Operator-reported output SHA256: `qc0_control_pairs_HOLD.tsv` = `b9bafeed81f68f30512277baaad5fc20df584ea90174e1f52829aa72358b83e3`; `qc0_control_summary_HOLD.tsv` = `3969077e913fe58ac981547f5c0a7f5ab6e45bef1753a29cf1bc525f80b8c07c`. CDS diagnostic ZIPs: Aug 14 `57cbc820d8a95477c562a01386f29d3c61e9bbe7f35500d72e5254d01b5f82c9`, Aug 19 `42898acd259840d045c77289b6f26e44065e6d7a04aa531507d16bab9bc38acc`, Sep 10 `7ca74d5efb5e8040a35794bebe533dcc8d6f6f2ef91c3742784e0aaa05df30c0`. Previous event-day comparisons were not repeated.

## Practical review

- **TA:** The two later control days show sub-degree mean absolute errors but biases of opposite sign. Tmd's event-local QC2 background is unequal before/after, and the controls do not resolve the event-time bias. Keep the chosen shadows held; extend evidence rather than fitting a correction to these two days.
- **LW:** The selected offset improves the Sep 10 all-day control compared with the raw grid, but the remaining negative bias and descriptive tail deserve review. The day is remote from the August event, and comparisons from 02:00–04:00 native time are a post-hoc subset, not an independent confirmation.
- **PA:** The new TA/LW controls do not validate any PA replacement. Tmd 2022's chosen PA shadow has a left boundary jump approximately −0.134 kPa compared with source QC2, with ~−0.122 kPa arising from the switch to the event-local median; the local QC2 adjacent-change p95 is 0.055 kPa and is descriptive, not an automatic acceptance threshold. Check representativeness and source-clock semantics before deciding. All nine PA groups and both Yms LW groups were above their local descriptive p95 in the previous boundary screen.
- **Clock:** ICOS/BIF evidence supports UTC+9 as a working diagnostic, while the exact-release README says local solar time. This remains unresolved; mean solar time and apparent solar time are also different.

## Stage05BN further analysis

`05bn_tmd_control_diagnostics_READONLY.py` reads the exact SHA-pinned 05BM pairs and 05BF selected ledger; it makes no CDS requests. It checks paired arithmetic, 492 rows, clock-aligned samples, the three UTC+9 aggregate summaries and all 45 HOLD/method statuses, and compares raw-grid versus fixed-event-median predictions for all samples and the post-hoc 02:00–04:00 native subset. This subset may be empty and is not an acceptance test. It writes a new diagnostic directory only. At publication this is an implemented and locally synthetic-tested script; it has **not** yet run on IRIDIS6. The 45 numerical shadows remain unapproved and no production inputs are modified.
