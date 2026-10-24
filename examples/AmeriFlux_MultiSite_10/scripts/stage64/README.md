# Stage64 — Batch01 temperature source-transition persistence

Stage63 validated **96 high-priority (P1) temperature episode groups**: 75 source-QC transitions (53 QC0→QC1, 12 QC1→QC0, 6 QC1→QC2, 4 QC2→QC1), seven same-QC0 measured events, and 14 source/clock unresolved events.

`64_review_transition_persistence.py` extends the Stage63 event queue with **independent before/after time-context** retained in the Stage61 report. It does NOT infer that ERA5 represents truth or that a QC switch is erroneous. Source timestamps remain provisional until original tower clock conventions are established.

For each episode the script checks the preceding and following half-hour temperatures, the subsequent candidate rebound, QC segment persistence within the finite ±4-hour Stage61 evidence window, and differences from the companion ERA5 at the immediate step and across nearby records. Stronger ERA disagreement is merely a review signal; shared provenance is possible.

Inputs (both mandatory and exact, not latest-by-mtime): 
- Stage61 `P1_context_source_comparisons.csv`, `manifest.json`
- Stage63 `all_96_P1_source_boundary_review.csv`, `manifest.json`

Modes:
- `--self-test`: synthetic boundary and ERA context test, does not access HPC data.
- `--check`: verifies exact 96 episode cases and expected Stage63 QC transition census, prints the classification and top examples, **no writes**.
- `--audit`: verifies the same cases, then writes **only a new timestamped report directory** beneath `experiments/AmeriFlux_MultiSite_10/reports`. Output: all 96 rows, 75 QC boundaries, 53 QC0→QC1 subset, seven stable measured QC0 cases, 14 unresolved clock cases, and manifest of report input hashes and limits.

For provenance, the program does not edit source files, original archives, existing candidate forcing, DATM, CTSM/FATES cases, PFTs, or Slurm jobs.

**Action after Stage64:** review QC0→QC1 categories in batches; separately inspect native tower/BASE measurements for the seven same-QC0 events (especially US-Bar -39.877°C/30min on 2015-11-06 and US-Aud -29.33°C/30min on 2023-04-30). Resolve the 14 source/clock ambiguities without inventing a time offset. No blanket smoothing, ERA replacement, or automatic temperature repairs. **Seventeen unresolved RH<1% cases, PFT and ZBOT readiness still hold production DATM/spin-up.**

This review covers the **96 P1 episode groups** only. It does not grant automatic approval to the 184 lower-priority groups from Stage60.
