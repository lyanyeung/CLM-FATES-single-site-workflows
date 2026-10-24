# Stage61 — Batch01 P1 temperature source-evidence audit

Stage60 reported 422 temperature-step flags clustered into 280 two-hour event groups; 96 are P1 review groups, not 96 confirmed errors. Of those, 47 are CA-Man and 20 US-Bar.

The script `61_review_p1_temperature_source_evidence.py` performs **read-only source consultation** and records new reports. It does not modify any source CSV, forcing, DATM, CTSM/FATES case, surface, parameter file, or Slurm job. Its `--check` mode performs report consistency checks without writing.

Inputs: the **exact** Stage59 and Stage60 report directory paths; pinned ten-site `sites.tsv`; each site's original FLUXMET_HH and companion ERA5_HH under its pinned-release raw directory. Source files are streamed; only selected context timestamps at -60, -30, 0, +30, +60 minutes are retained for comparison.

Scientific caveats:
- No offset is treated as an approved clock correction. Even a clear smallest median-absolute difference is **provisional**, requires source timestamp conventions and instrument timing confirmation.
- ERA5_HH may share reanalysis provenance with FLUXMET; it is not independent evidence of sensor error.
- Existing Stage51/Stage54 forcing are neither overwritten nor automatically accepted for spin-up.
- Apparent rapid reversals and large steps may be physically real, site-specific instrument problems, or forcing/source artifacts.
- P1 is an investigation priority only, not an instruction to replace the records.

Expected checks: Stage59 422 step flags, Stage60 280 grouped episodes and 127 rapid-reversal step flags, Stage60 exactly 96 P1 groups. If a count differs, the script stops without preparing a new report.

Outputs in a **new timestamped** `reports/stage61_P1_source_evidence_*` directory:
- `P1_episode_source_evidence.csv`: 96 prioritized event groups with strongest-step evidence
- `FLUXMET_candidate_clock_offset_sensitivity.csv`: source-clock offset diagnostics per affected site
- `P1_context_source_comparisons.csv`: candidate and source temperatures within ±4 hours of P1 groups
- `manifest.json`: report provenance, input checksums, source availability, unresolved scientific gates

Run: `python3 -B scripts/stage61/61_review_p1_temperature_source_evidence.py --stage59-dir <full-stage59-report-path> --stage60-dir <full-stage60-report-path> --check` then replace `--check` with `--audit` once the checks pass.

**Next action:** review all P1 evidence by category. Investigate CA-Man and US-Bar in batches; seek site BASE original sensor data and independent humidity/temperature evidence before any tightly scoped modification. Complete the 17 unapproved RH<1% investigations separately. Production DATM and spin-up remain HOLD.
