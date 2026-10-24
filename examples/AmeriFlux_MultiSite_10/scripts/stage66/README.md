# Stage66 — Batch01 BASE numeric temperature sensor audit

This follows Stage65, which located readable BASE_HH ZIP inputs for **50 of 60 targeted event groups** (36 CA-Man, 14 US-Bar; five candidate-time records per event), while four other towers had no BASE archive in the checked directories. Those 250 timestamp matches are **not** 250 verified numeric temperature observations.

The program `66_native_BASE_temperature_numeric_audit.py` verifies provenance against the **exact Stage64 report hashes recorded in Stage65's manifest** and checks 60 distinct Stage65 event IDs (53 QC0→QC1, 7 QC0→QC0).

For each native BASE temperature sensor column matching a numeric-indexed channel name such as `TA_1_1_1`, Stage66 extracts numeric values before/at/after the event and retains the accompanying raw `_QC` fields without interpreting their codes. It counts channels with valid numeric pairs and compares the raw pairwise temperature step with the forcing event's recorded step **provisionally**. It does not select the closest channel as the scientifically correct sensor. Sensor height/instrument identity and timestamp alignment remain unverified. BASE missing at a QC0→QC1 switch may be expected, not a defect in the gap-fill.

Modes:
- `--self-test`: deterministic synthetic multi-sensor and missing-data regression test; no experiment access.
- `--check --stage65-dir ... --stage64-dir ...`: full validation, sensor counts and classifications; **no report writes**.
- `--audit --stage65-dir ... --stage64-dir ...`: identical checks, then creates **only a new versioned directory** under `reports/stage66_native_BASE_TA_numeric_...`.

Reports contain `60_event_native_TA_evidence.csv`, `all_native_sensor_numeric_rows.csv`, `53_QC0_to_QC1_events.csv`, `7_stable_QC0_events.csv` and `manifest.json`.

No original BASE ZIPs, FLUXMET/ERA5 files, forcing, DATM, surface/PFT, CTSM/FATES case, or Slurm job is modified. Neither BASE numerical agreement nor disagreement is automatic authorization for replacement.

**Next gate:** inspect stage66 numerical evidence by sensor, then verify native sensor/channel measurement heights and clock conventions; independently investigate the 10 cases with currently missing BASE source. All 14 clock-ambiguous P1 groups and 17 low-RH cases remain HOLD. The P2 temperature cases are not cleared by this P1-only audit.
