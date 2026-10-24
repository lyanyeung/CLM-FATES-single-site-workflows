# Stage65 — Independent native BASE temperature source discovery (Batch01)

After Stage64, 96 P1 episode groups comprise 75 source-QC transitions, seven same-QC0 temperature jumps, and 14 source-clock unresolved cases. Among the 75 transitions, **53 are QC0 → QC1**, the most common switch direction. These 53 cases and the seven QC0 → QC0 cases are the **60 targeted records** for Stage65.

`65_native_BASE_temperature_crosscheck.py` inspects original, per-site `AMF_<site>_BASE-*.zip` archives where available. It searches only for uncompressed-stream-readable `BASE_HH` CSV members **inside** ZIPs, scans the native temperature sensor column names (such as `TA_1_1_1`), and captures the literal BASE `TIMESTAMP_START` values at candidate event `t−1h, t−30min, t, t+30min, t+1h`. The tool **does not extract archives to disk**. It distinguishes unavailable BASE archives, missing BASE_HH CSVs, ambiguous duplicate archives, missing raw TA columns, duplicate timestamps, and exact-time matches.

**Do not infer instrument identity**: a BASE temperature column may describe a different sensor height or instrument from the FLUXMET `TA_F` variable. Check original BADM instrument metadata before interpreting discrepancies.

**Do not infer clock alignment**: matching a literal `TIMESTAMP_START` is only a candidate. Confirm the native site timestamp convention, DST and averaging window before concluding that BASE proves/disproves a jump. ERA5 may share provenance with FLUXMET; not an independent instrument.

Modes:
- `--self-test`: create and inspect one tiny synthetic ZIP in a temporary directory; no experiment files accessed.
- `--check --stage64-dir <exact>`: read-only Stage64 census check and per-site BASE archive discovery, no output files.
- `--audit --stage64-dir <exact>`: stream relevant original BASE members if available and create **only** `reports/stage65_BASE_TA_source_evidence_<UTC>/` with `targeted_60_temperature_events.csv`, `53_QC0_to_QC1_events.csv`, `7_measured_QC0_to_QC0_events.csv`, and `manifest.json` containing input and archive provenance.

If matching BASE observations are absent, keep **SOURCE_EVIDENCE_HOLD** rather than replacing a QC0 or QC1 value. Full production science gate still includes 17 residual RH<1% investigations, 14 source-clock-ambiguous temperature event groups, and final PFT/ZBOT decisions.

The current audit is not authorization to alter original sources, final forcing, DATM, surface data, CTSM/FATES cases, or any Slurm job.
