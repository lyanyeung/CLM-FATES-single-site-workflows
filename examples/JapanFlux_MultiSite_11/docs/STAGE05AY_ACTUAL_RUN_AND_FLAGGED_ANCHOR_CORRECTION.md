# Stage05AY actual IRIDIS6 run and flagged-anchor correction

The operator supplied the actual terminal log for `run_20261103T070524Z_4159846` using commit `4e52063f6cecfb7fb9ddcc8f685672df55274fc9`. Syntax, self-test and six synthetic tests passed; the script reported all 45 fields / 35 site-native half-hours, the five original outer ZIP SHA256s matching Stage00, Stage05K README matches, and the complete source scan. Previously reviewed ERA5-Land comparisons were not rerun. The reported field table and JSON retain 45/45 SCIENCE HOLD and zero approvals. Full original-window TSV remains on IRIDIS6 and was not supplied with this log; the following analysis is limited to the pasted summary and event rows.

## Critical correction

The first implementation's wide PA screen admitted an independently flagged in-range value as an adjacent anchor. Thus its **41 `QC2_SHADOW_BRIDGE_REVIEW_ONLY` count is an uncorrected software screening count**, not 41 valid candidates. Specifically:

| Site and native event | Incorrect centre shadow | Independently flagged adjacent PA values used as anchors |
|---|---:|---|
| JP-Yms 2005-08-12 03:00 | 67.7975 kPa | 02:30 67.794; 03:30 67.801 kPa |
| JP-Yms 2011-12-17 07:00 | 68.181 kPa | 06:30 68.160; 07:30 68.202 kPa |

Both centre shadows are invalid and must not be used. Log-only comparison of all 41 candidate rows with all 45 flagged keys identified exactly these two cases of a flagged immediate anchor: **39 other rows passed that particular key check**, not a science-quality check. The original four Yms side fields were already labelled `FLAG_INSIDE_SCREEN_BOUNDARY_UNRESOLVED`; the two centres must also remain manual HOLD. This does not prove that the other 39 anchors are normal. The corrected code rejects any flagged immediate boundary and records `FLAGGED_BOUNDARY_UNRESOLVED`; the new regression reproduces this case. Recompute from original inputs or explicitly recheck the saved windows before using even the screening counts. Do not edit the original output to conceal the first result.

## Patterns actually visible in the operator log

The broad screen classified 41 field records in short apparently bounded 1–3-HH outside-range runs and four Yms PA side records inside the broad interval. The screen is not a physical-duration proof, and the two Yms centre runs have invalid flagged boundaries. Selected immediate anchors were source F=ERA QC2, not measured QC0. For native-date co-occurrence, the report lists 24 fields across four sites on 2005-08-12, 16 across five sites on 2011-12-17, and five across two sites on 2022-04-09. Tef/Tmd clock uncertainty prevents claiming exact UTC synchrony.

Several reported triplets show a striking arithmetic signature. JP-Tmd 2005 TA at 02:30/03:00/03:30 is −132.399/−284.222/−132.688 °C, while the immediate 02:00/04:00 QC2 source values are 19.425/18.847 °C: the two side values equal the adjacent-endpoint/central-value averages to rounding (−132.3985 and −132.6875 °C). JP-Khw in the same event shows the same relation: 23.988, −122.144, −268.276, −122.665, 22.946 °C. The PA triplets likewise resemble midpoint interpolation between each outside value and a very low centre. JP-Yms makes a purely absolute threshold particularly misleading: 67.794/37.349/67.801 kPa has a central value outside the broad PA screen, but both flagged flanks lie inside it and are still independently abnormal. Repeated identical anomalous LW_IN values across adjacent half-hours also merit a separate accumulated-radiation/time-processing examination.

These observations are consistent with a corrupted upstream time sample followed by interpolation, and with shared processing affecting multiple releases, but do not locate the fault, identify its upstream value, prove UTC synchrony for solar-clock sites, or rule out other mechanisms. Investigate source windows, actual timestamp conventions, product pipeline, independently preserved ERA inputs and radiation interval semantics. Neither the shape nor the broad-range screen validates a bridge or supplies a certified replacement.

The full window file printed in the operator log is `/home/ly3n24/japanflux_stage05ay/run_20261103T070524Z_4159846/native_windows.tsv`. Inspect the full native windows, MDS and co-timed variables before a reasoned event-by-event method comparison. All fields remain HOLD, no replacements approved; no raw ZIP, forcing, PFT, model case, Slurm or AD400 changes are authorized by this report.
