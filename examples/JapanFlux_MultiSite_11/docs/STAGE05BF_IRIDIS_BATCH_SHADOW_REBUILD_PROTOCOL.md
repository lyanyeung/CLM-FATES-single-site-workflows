# Stage05BF: one IRIDIS read-only batch for the selected shadow

## Objective and current execution status

The user selected `ERA5-Land grid + local source-QC2 background median` for all 45 flagged fields. Stage05BF rebuilds this selected method on IRIDIS6 from the **already existing** Stage05AW ledger, Stage05AY native windows and Stage05AZ saved tables. It performs no CDS download, no new ERA5-Land comparison, no original ZIP edits, and no production forcing, PFT, soil, model, Slurm or AD400 changes. It creates a fresh shadow-only output directory and all 45 remain `HOLD_NO_APPROVED_REPLACEMENT`. **Actual IRIDIS6 execution is pending operator output.**

## Gates and reproduction

The script checks the original AW and AY SHA256s, all three operator-reported AZ table SHA256s, and all five original JPF outer-ZIP SHA256s before and after its analysis. The large ZIPs are streamed for SHA256; their meteorological rows are not reprocessed. It reads the existing AZ summary, checks its recorded 5-source/16-CDS gate fields and the 45/17/99 scope, and records the observed summary hash; the 16 CDS ZIPs are **not rechecked** in this run. The old AZ clock-scenario label issue does not affect the selected UTC+9 numerical row; the source time convention for Tef/Tmd remains unresolved.

For the UTC+9 rows, the script verifies exact 45-field coverage and overlapping native windows, flagged original F=ERA QC2, event-excluded source-QC2 paired-background arithmetic and median, candidate grid support, broad value screens and outer group endpoints. It calculates `saved grid context + saved local QC2 median`, then requires the 45 sorted values formatted to six decimals to match the locally calculated canonical SHA256 `5fd381ddefac2d08a3cee7ed8548c73477c115a342f5895b4673b325768803ae`. This confirms agreement **to six decimals only**, not measurement accuracy or scientific approval.

On success it writes a fresh direct child of `~/japanflux_stage05bf` with a 45-field ledger, a 1,677-row local-window preview, 17 boundary-jump descriptions and a summary JSON. Unflagged F strings are unchanged in that preview; the preview is not complete forcing. Any missing source, hash mismatch, incomplete summary, arithmetic mismatch, scope mismatch, nonfinite value or candidate mismatch fails closed before creating the output directory.

The script's self-test and two synthetic tests run locally, including a complete synthetic 45-field/17-group batch with hash tampering rejection. Those are **not real IRIDIS results**. No source input is included in this GitHub repository.

## Scientific interpretation

Grid matching remains an hourly-to-half-hour approximation, and the QC2 median is derived from the same release as the anomalies. The Tef/Tmd clock conflict, Tmd pressure representativeness and 11 of 17 descriptive jump flags from Stage05BE remain unresolved. Hash checks and exact reconstruction demonstrate provenance and reproducibility, not correctness of a repair value. No user authorization to deploy a production forcing is inferred from choosing the shadow method.
