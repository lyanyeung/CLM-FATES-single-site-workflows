# Stage62 — quality-aware P1 temperature triage (Batch01)

The inputs are the **completed Stage60 and Stage61 reports** for ten AmeriFlux Batch01 stations. There are **96 P1 temperature episode groups** (from 422 original >10 °C/30-min step flags, clustered into 280 groups). Stage61b partitions these into **82 provisionally reproduced in FLUXMET** and **14 with unresolved candidate-to-FLUXMET time alignment**.

For the 96 P1 groups, Stage61b reports `FLUXMET TA_F_QC` at the largest step: 19 measured (0), 57 good-quality gapfilled (1), 6 ERA-downscaled (2), 14 missing/not resolved. **The QC code refers to the record at the end of the step.** For diagnosis of a source switch, the QC **30 minutes before** must also be checked; a QC=0 endpoint alone does not prove a sensor jump. Authoritative source definition: https://fluxnet.org/data/fluxnet2015-dataset/subset-data-product/

The program `62_prioritize_temperature_source_qc.py` therefore joins Stage60 episodes, Stage61 strongest-step evidence and Stage61 source context on `(site, episode_id)`. It retrieves the prior record's QC, ranks magnitude and rapid reversals, and separates data-provenance categories. It cannot decide whether a temperature jump is physically real, and does not treat ERA5/FLUXMET cross-correspondence as independent truth.

- `--self-test`: isolated QC interpretation tests, no experiment files required and no output writes.
- `--check`: source CSV/manifest checks and printed queue summary; **no writes**.
- `--audit`: checks and writes **only a new timestamped reports directory**, containing `all_96_P1_temperature_source_triage.csv`, `measured_QC0_manual_review.csv`, `gapfill_QC1_batch_review.csv`, `ERA_downscaled_QC2_review.csv`, `clock_alignment_ambiguous_review.csv`, and `manifest.json`.

Run with explicit `--stage60-dir` and `--stage61-dir`; never modify Stage60/61 reports, archived flux source, candidates, DATM, CTSM/FATES, PFTs or Slurm.

**Next scientific gate:** Investigate high-amplitude QC0 events (e.g. US-Bar and US-Aud) using actual native tower sensor observations/BASE and site clock conventions; batch review source QC transitions and gapfilled intervals; resolve all 14 ambiguous-lag events separately. Document each decision before any isolated repair candidate is generated. The separate 17 unresolved RH<1% records also remain science HOLD.
