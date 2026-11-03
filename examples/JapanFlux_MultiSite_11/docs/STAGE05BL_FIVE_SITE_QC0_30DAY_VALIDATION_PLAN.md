# Stage05BL: five-site 30-day QC0 context and validation planning

## Objective and status

The user-selected repair scenario remains `existing ERA5-Land grid + local QC2-minus-grid median` for all 45 fields. It has been reproduced on IRIDIS6 as **HOLD-only** shadows in Stage05BF. Stage05AX previously examined selected-QC0/QC1 neighbors only within ±24 h of each flagged half-hour; those results do not tell us whether longer local periods contain QC0 samples useful to plan a validation experiment. Stage05BL audits all 17 original site-variable groups in one five-site batch over 30 days before the first and 30 days after the last flag, without changing the selected method.

The script is committed, self-tested, and tested on a synthetic five-site/45-field archive including source hash tampering. **No actual Stage05BL IRIDIS6 result has been observed yet.**

## Inputs and integrity

The batch reads the SHA-pinned original Stage05AW 45-field ledger, the actual Stage05BF selected ledger from `/home/ly3n24/japanflux_stage05bf/run_20261103T133027Z_2561848/selected_45_HOLD.tsv`, and the five original JPF outer ZIPs. It checks the five outer ZIP SHA256s before and after each source scan, reads each exact named nested archive in memory, and streams its exact FLUXMET_HH CSV to EOF once. It verifies all original flagged F, embedded ERA and QC2 values against Stage05AW and keeps all 45 in HOLD. No source ZIP, forcing, PFT, soil, model case, Slurm or AD400 is written. Inner archive memory is capped at 512 MiB per site. Runtime and actual QC0 availability depend on the operator environment and data.

## Outputs and scientific limits

One fresh child of `~/japanflux_stage05bl/` contains:

1. `qc0_17_group_summary_HOLD.tsv`: for each group, selected source-F QC0 counts in 7-day and 30-day windows that pass broad PA 50–115 kPa, TA −70–65 °C or LW 70–650 W m⁻² screens; nearest qualifying left/right native times and distances; and an optional same-source QC0 masking statistic.
2. `qc0_30day_measured_samples_READONLY.tsv`: group-associated qualifying source-selected QC0 values at other times, for designing a possible later reference match. These are source products and should not be uploaded as raw data to the repository.
3. `summary_HOLD.json`: source scan counts, group counts and output SHA256s; zero approved values.

The broad ranges are only exclusion screens: a `QC0` label and a passing range do not certify sensor accuracy. Zero reported QC0 means **zero passing that filter within the examined window**, not proof that no measurement of any kind exists. The count windows are 7 or 30 days before the first group point through 7 or 30 days after the last; timestamps stay in the original native clock. Tef/Tmd clock conflict remains explicit.

For each group's length, the optional sensitivity masks every consecutive QC0 block with QC0 endpoints within the 30-day window, excludes all block points/endpoints within two hours of any flag in that group, and compares a bridge to the withheld QC0 values. Blocks overlap, are autocorrelated and may be absent. The mean/p95 describe this **bridge against same-source measured values at other times**; neither is an uncertainty interval, event truth, approval or a validation of the user's grid-plus-QC2-median method. Selected grid-plus-median values are not changed.

If useful QC0 periods exist, a later validation would need independently sourced, correctly time-matched grid values for carefully chosen **non-event** QC0 periods, plus a predeclared comparison that avoids training/test leakage. The existing 45 ERA5-Land anomaly comparisons need not be rerun. If none exist for a group, do not manufacture tower anchors; pursue appropriately documented independent station or publisher evidence. UTC, interval matching, Tmd pressure representativeness and the previously identified boundary jumps remain separate review conditions.
