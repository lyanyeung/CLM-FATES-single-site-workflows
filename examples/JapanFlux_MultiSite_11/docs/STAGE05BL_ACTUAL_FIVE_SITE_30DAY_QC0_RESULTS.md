# Stage05BL: actual five-site 30-day QC0 results

The operator supplied complete Stage05BL terminal output: downloaded script and test SHA256 checks passed, self-test passed, two synthetic tests passed, and all five original source ZIP scans completed. The source row counts were Fjy 368,160, Khw 385,728, Tef 403,200, Tmd 333,072 and Yms 420,768. These are operator-reported results; the reviewer did not read IRIDIS6 directly. All 45 fields remain HOLD, with zero values approved. The chosen `grid + source-QC2 median` method is unchanged.

Output directory: `/home/ly3n24/japanflux_stage05bl/run_20261103T182225Z_886037`. Operator-reported SHA256: `qc0_17_group_summary_HOLD.tsv` = `b6e242ebc7fb523325c60df1ed8d30de071059504b5be03b709ae5eae2e5ed8c`; `qc0_30day_measured_samples_READONLY.tsv` = `1eafeb78c609aee5dbe3673473d5d916fb1fda6e81c84aca00f3f4c8d6b3f23b`. The terminal-paste attachment SHA256 is `b2854d7980768d88c31f121fe982b8df8883373992d4a01f59d192a787aee5f5`.

## Actual measured-context availability

Of 17 groups, **two** had selected-F QC0 values passing broad range screens in ±30 days, both JP-Tmd 2005. All other 15 had zero **passing-screen selected-F QC0** within the examined windows. This is not proof no station measurement exists in any form, no QC0 outside the windows, or no QC0 value rejected by the screens.

| Site / group | Qualifying QC0 within ±30 d | Within ±7 d | Nearest before | Nearest after group end | Overlapping QC0 bridge-mask blocks | MAE / p95 against masked QC0 |
|---|---:|---:|---|---|---:|---:|
| Tmd TA, 2005-08-12 02:30–03:30 | 1,375 | 271 | None within window | 2005-08-13 12:30 native, 33 h | 1,371 | 0.2653 / 0.8170 °C |
| Tmd LW, 2005-08-12 02:00–02:30 | 69 | 0 | None within window | 2005-09-09 16:30 native, 686 h | 66 | 1.7771 / 5.4670 W m⁻² |

The nearest after times and distances are referenced to each group's last flagged start. The blocks overlap heavily and their point errors are autocorrelated; these descriptive metrics compare a **QC0 endpoint bridge against QC0 values at other times**, not against the actual anomaly or against the selected grid-plus-QC2-median method. They are neither independent replicates nor uncertainty bounds, and cannot approve a repair. The Tmd solar-versus-UTC+9 source-clock conflict remains, although ICOS metadata and BIF support UTC+9 for diagnostics. The gap before the nearest LW control is approximately 28.6 days, so cloud/seasonal representativeness must be considered.

## Consequences for next work

The TA and LW QC0 subsets are useful for designing **new non-event control** comparisons against independently retrieved, correctly time-matched ERA5-Land grid data, without repeating the 45 already-completed anomaly comparisons. Such a control must define dates and calibration/test separation before viewing results, record source/QC provenance and clock sensitivity, and acknowledge possible shared reanalysis inputs and spatial representativeness. Control QC0 at other times is not event-time truth. For the 15 groups with no passing QC0 in the examined range, use documented external observations or release provenance where available, and retain HOLD rather than manufacture tower anchors. Tmd PA is particularly important because prior whole-record source audit described the selected PA series as continuously QC2 for the examined release. No code here changes the chosen method or production forcing, and no PFT, soil, model case, Slurm or AD400 work is implied.
