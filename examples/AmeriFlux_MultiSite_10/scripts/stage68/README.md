# Stage68 — Start controlled Batch01 temperature **repair trials**, CA-Man first

After seven read-only stages (Stage59–67), the next useful action is to generate an isolated **counterfactual forcing sensitivity** instead of running more flag detectors. This is **not** approval to replace the forcing used by CLM-FATES.

The Phase 1 scope is **CA-Man** only. Stage67 reports 36 high-priority QC0→QC1 source transitions where native BASE temperature is present immediately before the transition, but not at the QC1 timestamp. This can be an ordinary measured-to-gapfill transition. Neither the lack of raw BASE observations in a QC1 interval nor ERA5 disagreement alone proves a gapfill is wrong.

The script `68_build_CA_Man_scoped_TA_trial.py`:
- Requires the exact Stage61, Stage64 and Stage67 report directories, plus the Stage58-pinned CA-Man original forcing file, SHA256 `fac0bc4a82050a087e462c3af1b05ec16e1f3f803a66bde7bf87c0b3a39d3705`.
- Restricts trial editing to QC1 gaps of **one or two consecutive 30-minute records**, both directly bracketed by QC0, with valid candidate-source matches and at least one matching native measured-side sensor.
- Requires observed QC0 anchor temperatures to differ by no more than **3°C per half-hour** across the small gap, before considering interpolation. At every candidate replacement point, require at least **4°C difference** to justify a scientifically salient alternative, no more than **20°C change** without further review, and physical RH/VPD gates.
- For a qualifying **hypothetical trial only**, linearly interpolates air temperature (°C) between the two QC0 anchors. Changes exactly three forcing columns: `TBOT` (K), `TA_USE` (°C), and `VPD_USE` (hPa, recomputed from the adjusted T with **unchanged** `QBOT` and `PSRF`). It never edits a QC0 anchor or any other forcing variable.
- Uses full original-versus-trial streaming cell-level checks and reuses the pinned Stage58 full 1994–2008 NOLEAP/meteorology audit; any introduced physical or structural failure blocks success.
- Writes **only** under a new timestamped `reports/stage68_CA-Man_shadow_TA_trial_*` directory; the output forcing is named `*_TA_SHADOW_TRIAL_NOT_PRODUCTION.csv`. A ledger specifies each changed timestamp, temperature, VPD, RH, method, and scientific HOLD. The original remains byte-for-byte unchanged.
- `--self-test`: synthetic QC1 interpolation, three-column coupling and unchanged-field validation.
- `--check`: stage gate and eligible-event census; **writes nothing**.
- `--trial`: if any eligible event passes, generates isolated complete 15-year shadow forcing and ledger (no submission). If zero events qualify, creates no trial.

**Scientific interpretation:** Short bounded gaps can be tested with interpolation, but interpolation is **not** an evidence-backed substitute for validated FLUXNET gapfill. Only compare candidate versus existing forcing as an explicit counterfactual sensitivity; no automated production replacement. Never use a single ERA5 value as ground truth or auto-edit native QC0 observations. Confirm original tower clock conventions, sensor/channel height and gapfill provenance before approving any final patches.

**Remaining independent holds:** US-Bar 13 QC0→QC1 transitions require understanding native sensor rejection/gapfill methods; US-Bar 2015-11-06 QC0→QC0 −39.877°C originates in native BASE and still requires instrument QA; 10 events lack BASE sources in the checked folders; 14 P1 events lack verified clock alignment; 17 RH<1% records and 184 P2 temperature groups remain unresolved. No production spin-up, DATM/CIME edits, or Slurm jobs authorized by this stage.
