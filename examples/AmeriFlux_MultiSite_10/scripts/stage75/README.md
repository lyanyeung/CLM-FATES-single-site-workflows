# Stage75 — Batch01 ten-site MET quality and remaining-release-risk matrix

Stage74 **actually ran** on IRIDIS6 and produced a protected CA-Man operator-selected trial: **18 same-source ERA5_HH T/Q/P/VPD half-hours changed, 17 RH/VPD-boundary-risk events left exactly unchanged, one March 2007 QC0-anchor retained**. The 15-year original/trial full-file scan passed; CA-Man's >10°C/30-min step flags decreased **185→152**, with RH<1 remaining **1→1**. This is a **trial**, not source-clock or production approval.

**Stage75 correction (24 October 2026):** The initial audit incorrectly asserted `CA-Man P1 = 36`. Stage70A actually defines **36 reviewed CA-Man QC0→QC1 events as a subset of the 96 total P1 events across all ten sites**; CA-Man can have additional P1 event classes. The updated script now verifies the exact 36 subset via `36_CA-Man_QC0_to_QC1_review.csv`, checks its `19+15+2` classification and P1 membership, and reports the actual CA-Man P1 total without inventing a fixed number. It also permits a reduction (but not an increase) in critical MET flags for the CA-Man trial. The first `--audit` failure was a script census assumption, **not new evidence of a forcing/model error**; no audit outputs were produced by that failed invocation.

Stage75 is an **audit**, not a proposed new correction. It combines the original Stage59/60/70A review and Stage74 operator decision:

- Verify the **10 Stage58-selected original site forcings**, using exact source SHA-256 values from Stage59. For **CA-Man alone**, use the exact Stage74 trial as the *reviewed candidate*, and verify the Stage74 original/trial manifest and decision ledger checksums.
- Run the full Stage58 NOLEAP, range, humidity/VPD closure and 30-minute temperature-step scan against all ten reviewed candidate files. Apply an additional RH **1–5%, 5–10%**, and negative-VPD sensitivity tally. These extra flags do **not** independently prove data errors.
- Reconcile the **17 unresolved RH<1% half-hours** across CA-Ca3 (7), CA-Cbo (2) and US-Bar (8), plus the **one CA-Man already documented but not repaired RH<1% risk**.
- Preserve **96 P1 + 184 P2 = 280** original temperature event groups from Stage70A as *pre-repair source-review groupings*. The Stage74 trial changes some individual step counts, but the original groups cannot be treated as a newly recomputed 280-group partition.
- Expect temperature-step flags across the 10 reviewed candidates to decrease from **422 → 389** (Stage74 CA-Man contributes exactly −33). These are **flags, not 389 confirmed errors or records requiring editing**.
- Summarise per site and identify scientific holds without automatically changing any site input, filing scientific sign-off, or submitting jobs.

The script `75_batch01_MET_release_risk_audit.py` supports `--self-test`, `--check` (read-only) and `--audit` (creates a NEW small review CSV/JSON directory only). Outputs `10_site_MET_release_risk.csv`, `17_unresolved_RH_lt1.csv`, `96_original_P1_pending_or_reviewed.csv`, `184_original_P2_pending.csv`, and `manifest.json`.

Scientific decision principle from [root README](../../../../README.md): prefer source-coherent, bounded meteorological corrections; leave a difficult temperature discontinuity with an explicit human-risk ledger rather than introducing a larger unverified RH/VPD disturbance. This rule is per-event and **does not automatically approve** all other Batch01 temperature or low-RH anomalies. No production forcing, DATM/CIME, Slurm or spin-up is authorized by a Stage75 PASS.
