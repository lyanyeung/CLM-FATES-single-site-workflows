# Stage63 — Batch01 temperature source-QC boundary review

This stage is a strictly scoped continuation of Stage59→Stage62. **No production simulation, original source modification, or forcing repair is authorized.**

## Why this stage exists
Stage62 reports 96 P1 temperature episode groups, with 75 provisional FLUXMET QC transitions, 7 stable-QC events, and 14 events with ambiguous source-clock alignment. QC0 denotes a measured FLUXMET record; QC1 denotes good-quality gapfilling; QC2 denotes downscaled ERA. The **QC of the record before the jump** matters as much as the QC at the jump.

A change of source category does not prove either endpoint is physically wrong. A QC0-to-QC0 jump may reflect a sensor or recording anomaly, or a genuine atmospheric event. FLUXMET and companion ERA5 may share provenance, and source timestamps have not been independently verified.

## Script
`63_audit_source_transition_boundaries.py` links Stage62's `all_96_P1_temperature_source_triage.csv` to Stage61's `P1_context_source_comparisons.csv` using exact (site, episode_id, largest_step_timestamp). It checks Stage61/62 manifests and historical event totals and refuses to proceed if sources disagree.

- `--self-test` checks QC parsing, numerical logic and a synthetic CSV fixture. It does not touch IRIDIS experiment files.
- `--check` validates all available 96 episodes, compares previous/current 30-minute candidate, FLUXMET and ERA5 temperatures, and prints QC switch directions and ranked examples. No output files are written.
- `--audit` performs the same checks, then creates a **new timestamped** reports directory only, containing `all_96_P1_source_boundary_review.csv`, `75_QC_boundary_events.csv`, `same_QC0_measured_events.csv`, `same_QC_other_events.csv`, `14_clock_unverified_events.csv` and `manifest.json`.

Run with exact Stage61 and Stage62 result directory paths; do not depend on 'latest' directory selection.

## Decision policy
1. Group and diagnose the **75 source transitions** by direction (e.g., QC1→QC0 and QC0→QC1). Inspect the original observed time series and the gapfilling algorithm. Do not automatically alter measured values.
2. Independently examine the **7 stable-QC events**, especially large QC0→QC0 jumps at US-Bar and US-Aud. Inspect native tower measurements, neighboring sensors, instrument logs and clock/time convention.
3. Keep the **14 clock-ambiguous cases** as HOLD until the original metadata and exact time alignment are verified.
4. If a source error is confirmed, create a separate, minimal, science-approved sensitivity candidate with explicit event ledger, before/after QA, immutable input hashes and strict unchanged-row comparisons.
5. Low relative humidity (17 unresolved RH<1% rows) remains a separate scientific HOLD.

A quality-control label and extreme-value threshold are **evidence for review, not an automatic replacement rule**.
