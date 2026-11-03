# Stage05BE: user-selected grid + QC2-background shadow, all HOLD

## Decision and boundary

The user selected the `ERA5-Land grid + local QC2 background median` candidate for **all** nine PA, two TA and six LW groups and asked to advance. The selection is recorded as a method choice for further work, not as proof of the numerical values or a waiver of the earlier prohibition on automatic production-forcing changes. All 45 candidate fields remain `HOLD_NO_APPROVED_REPLACEMENT`; zero values have been approved or applied to production. Do not silently switch back to bridge candidates.

The Stage05BE script reads only the exact three pinned Stage05BA/BC derived local tables: the 1,677-row window preview, the 45-field alternative ledger and the 45-field Stage05BA evidence ledger. It checks SHA256 before and after processing, exact keys/counts, original F equality, QC2/F=ERA at flags, selected = saved hourly grid + QC2 median, non-event F text identity, and broad plausibility ranges. This is derived-input integrity, **not** an independent re-read or verification of IRIDIS6 original ZIPs; the previously noted omitted AZ source-gate log/summary remains unresolved.

The local run produced 45 selected shadow values, a 1,677-row preview with 1,632 unflagged F strings preserved, a 17-group boundary table, and a 35-site-time PA/TA/LW context table. The preview is not a complete multivariate source or forcing. The 45 selected values pass only broad range screens, which are not scientific validation. At all 35 site-times, the reconstructed selected-or-original PA/TA/LW fields pass these broad screens; provenance is carried separately for each variable. `LW / (sigma * T_air^4)` is an unclassified descriptive ratio, not a measurement of atmospheric emissivity or a repair acceptance criterion.

## Continuity result requiring review

For each group, the script computes the largest absolute half-hour change across the outside-left QC2 endpoint, all selected candidates and the outside-right QC2 endpoint. It compares that maximum descriptively with the 95th percentile of adjacent **same-release QC2** changes in the available ±24 h window, excluding pairs touching the ±2 h flagged-event buffer. These source changes are autocorrelated and the sample is local; this percentile is neither a physical limit nor a confidence interval. No group is automatically rejected or approved by it.

**11 of 17 groups** have a selected maximum jump above this descriptive local p95: **all nine PA groups and both Yms LW groups**. The other six do not; being below the descriptive p95 does not prove correctness. Examples:

| Group | Selected maximum jump | Local QC2 adjacent-jump p95 | Prior bridge maximum jump | Unit |
|---|---:|---:|---:|---|
| Fjy PA 2005 | 0.0600 | 0.0330 | 0.0010 | kPa / 30 min |
| Tmd PA 2022 | 0.1342 | 0.0550 | 0.0185 | kPa / 30 min |
| Yms LW 2011 | 15.6433 | 14.4940 | 4.4130 | W m⁻² / 30 min |

The bridge comparison illustrates a continuity tradeoff, but the selected method stays the user's grid-adjusted candidate and the same-source comparison cannot establish which method is closer to tower truth. Tmd PA background has separate unresolved JMA context; Tef/Tmd clock remains unverified. TA/LW grids have hourly support, and the two LW half-hours can receive identical selected values under the existing overlap method; this is not evidence that actual subhourly radiation was constant. Review clock, interval semantics, background representativeness and boundary behavior before any per-field production decision.

## Actual local outputs

The verified local run produced the following SHA256s:

```text
409e0e9df7155be57bbdc0d18b7c7397b011328292a500806315737296fbd9a6  selected_45_HOLD.tsv
191e42017eb0c5726702d13dc0faeaeedca8a7d384957f64cf31330fecbf9c83  selected_window_preview_NOT_FORCING.tsv
df630467aa393331c5c4116af687c988976d9b747b5ff1aed87ef3eea66fcb7e  boundary_sensitivity_17_groups_HOLD.tsv
a3f0d5c52b275b46cab5f7f8f4be2ce733f5097a35e311d77d97b1a99ac68312  covariable_context_35_times_HOLD.tsv
```

`05be_selected_grid_adjusted_shadow_READONLY.py --self-test` and three tests pass locally; tests include rejection of altered derived inputs before output and invalid/missing values. The script only accepts a new child of a `japanflux_stage05be` directory, and does not generate or modify a forcing file. It was **not run on IRIDIS6**. PFT, Soil Texture, original ZIPs, production forcing, model cases, Slurm and AD400 were not changed.
