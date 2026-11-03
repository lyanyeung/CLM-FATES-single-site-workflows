# Stage05BG: actual IRIDIS 05BF result and selected-shadow clock sensitivity

## Operator's actual IRIDIS6 Stage05BF output

The operator ran the Stage05BF batch from commit `cab20106f095d5495a1ba2c2a4b5d10d0213e1d0`. Both downloaded file SHA256 checks, script self-test and two synthetic tests passed. The script reported five original ZIP SHA256s checked before and after, 45 selected fields / 17 groups / 35 site-times, 1,677 preview rows with 1,632 unflagged F strings preserved, and zero approved values. Its selected-values canonical SHA256 at six decimal places was `5fd381ddefac2d08a3cee7ed8548c73477c115a342f5895b4673b325768803ae`, matching the prior local selected shadows at that precision. This is operator-supplied real terminal output, not direct access to IRIDIS6 by this reviewer.

Output directory: `/home/ly3n24/japanflux_stage05bf/run_20261103T133027Z_2561848`. Operator-reported output SHA256s:

```text
bd36ee5d5f8297f4edd8a5c08562473e2110fe6da6354dbaaf0754aaa5ad434f  selected_45_HOLD.tsv
63bbe232c65718a2a99e24711891627b2a6df837760184dfca9f54b450f0b8bd  selected_window_preview_NOT_FORCING.tsv
b14be602ef1bedb28721b099e6e9a2b413ab07fb5a91ae4d39b1627b7cbc033c  boundary_17_groups_HOLD.tsv
```

The run read the previously unavailable Stage05AZ `summary_HOLD.json`; its observed SHA256 was `bc5ddc6e8ebcb6add0adb6d4805acb593808d6f4813ed5c46e25bca380b0d9ce`. This summary **records** five source ZIP gates and 16 CDS ZIP integrity gates from that run. Stage05BF rehashed the five original source ZIPs and the prior AW/AY/AZ tables, but did **not** recheck the 16 CDS ZIPs or redo the ERA5-Land comparison. A gate record is provenance evidence; the six-decimal match and successful checks do not validate physical truth. The five original ZIPs and production forcing were not modified.

## Additional local clock-sensitivity experiment

From the already supplied Stage05AZ paste (SHA256 `bd96cc5f0d80fe440c2db3540a8492d75c2641b8ee7bf95b810765f64925a26c`) and locally selected Stage05BE ledger (SHA256 `409e0e9df7155be57bbdc0d18b7c7397b011328292a500806315737296fbd9a6`), `05bg_clock_sensitivity_selected_shadows_READONLY.py` reconstructs the **user-selected grid plus QC2 background median** for all 18 Tef/Tmd fields at four saved offsets: UTC+08:30, UTC+09:00, UTC+09:30 and longitude-derived mean solar time. It recalculates the background median from the paired QC2 samples for **each offset**, so differences combine both reference-time matching and changes in the paired background. The UTC+09 candidate matches the selected 05BE value within 1e-6. No additional CDS access or source file read occurs.

These are *diagnostic scenarios*, not the range of possible true timestamps, confidence intervals, independent tower observations or evidence identifying the publisher's actual clock. The original Stage05AZ output incorrectly labelled the mean-solar offset as a generic fixed offset; here it is identified numerically as longitude × 4 minutes per degree. This corrects the label only. Mean solar differs from apparent solar time, and source interval convention remains unverified.

| Group | Fields | Largest four-scenario spread in group | Largest absolute mean-solar minus UTC+9 difference | Units |
|---|---:|---:|---:|---|
| Tef LW 2011 | 2 | 5.830 | 5.685 | W m⁻² |
| Tef LW 2022 | 2 | 13.786 | 9.602 | W m⁻² |
| Tmd LW 2005 | 2 | 4.992 | 3.354 | W m⁻² |
| Tmd PA 2005 | 3 | 0.01433 | 0.01059 | kPa |
| Tmd PA 2011 | 3 | 0.05140 | 0.02398 | kPa |
| Tmd PA 2022 | 3 | 0.02859 | 0.01683 | kPa |
| Tmd TA 2005 | 3 | 0.19046 | 0.09148 | °C |

Each spread is the largest within-group field-level maximum minus minimum across the four scenarios. Do not add this quantity to the 05BE boundary jumps as though it were an uncertainty budget. Tef 2022 longwave is particularly sensitive in these scenarios; PA time sensitivity does not eliminate the separate unresolved Tmd pressure-background concern. All 45 fields remain HOLD, including 27 at the other three sites which do not have this specific solar/JST conflict.

## Reproducibility and status

Actual local 05BG outputs: 18-field scenario table SHA256 `e48c673ad97f3345f2336d4636fc7cdfcddf7dc85dae2ab608db8afbc231675e`; seven-group summary SHA256 `ef9bb8097bb76e8227c7c14ed4d2d6677e9e88bd0d231e1ed1906f38d6461c53`. The script's self-test and two unit tests pass locally; they include longitude-to-minute labels and fail-closed input hash checks. These 05BG numbers were calculated locally from the operator paste and local 05BE ledger; **05BG was not run on IRIDIS6**. No source ZIP, forcing, PFT, soil, model case, Slurm or AD400 was modified.
