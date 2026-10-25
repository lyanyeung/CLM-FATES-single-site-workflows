# Batch04 Stage19 — multi-day ORIGINAL QC0 temperature regime audit (read-only)

**Status (2026-10-25): Stage18 VERIFIED PASS 6/6; Stage19 operator-verified IRIDIS6 PASS 6/6.** The original pinned command is preserved below. See [Stage19 actual multi-day numbers, episodes, source hashes and scientific decisions](STAGE19_VERIFIED_MULTIDAY_TEMPERATURE_REGIMES_2026-10-25.md). Eight original temperature science HOLDs remain unresolved.

[Stage18 actual measurements, SHA values and science assessments](STAGE18_VERIFIED_ORIGINAL_T_SOURCE_LINEAGE_2026-10-25.md). Stage19 code: [19_multipday_original_temperature_regime_audit.py](../scripts/stage19/19_multipday_original_temperature_regime_audit.py).

## Why this check

- **US-SP1 2007-10:** repeated ~11.15°C at 17:30 on three successive days (Oct 15: 11.150°C; Oct 16: 11.149°C; Oct 17: 11.169°C) and sudden Oct 15 17:30→18:00 +12.070°C under original QC0, while TA_ERA is much warmer. Investigate whether the original product contains multi-hour or repeated-value segments, not just a single source outlier. Consecutive days' values alone do not prove a faulty sensor.
- **US-SP1 2008-01/02:** original QC0 cold series are continuous across multiple half-hours; inspect the actual duration of original TA−TA_ERA ≤−10°C episodes, rather than replacing individual QC0 points.
- **US-SRG 2019-03-19 12:00:** original TA_F=0.718°C QC0 vs TA_ERA=20.399°C. Both immediately adjacent consolidated temperatures are QC2 and equal TA_ERA, so they are ERA-derived, not two observed tower anchors. Stage19 preserves that explicit provenance.
- **US-Seg 2016-12-27 18:00:** contiguous original QC0 cooling trajectory; do not incorrectly infer a single-point temperature error from grid mismatch alone.

Official FLUXNET consolidated micrometeorology flags: HH TA_F_QC=0 is measured, 1 is good-quality MDS gapfill, 2 is ERA-downscaled substitution, and TA_F_MDS_QC=0 denotes measured. These are product provenance flags, not independent physical truth. Confirm the user's v1.3 release-specific implementation separately. Sources: https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/ and https://www.nature.com/articles/s41597-020-0534-3.

## IRIDIS6 single-command execution

Use the clm_fates_env environment, on a login terminal. Download pinned sources with curl, no git pull. The Python script is read-only. The tee command writes only a log under the operator's home directory.

~~~bash
(
  set -euo pipefail

  BASE="$HOME/ameriflux_batch04_stage19"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts"

  STAGE19_COMMIT="58d20dcd5c0bca43dc736c59620ede4834c346e7"
  DEPENDENCY_COMMIT="9be06860ee3e9f14e08fb078d22d0090b49d58d4"
  mkdir -p "$BASE"

  SCRIPT="$BASE/19_multipday_original_temperature_regime_audit.py"
  curl -fLsS --retry 3 \
    "$RAW/$STAGE19_COMMIT/$REL/stage19/19_multipday_original_temperature_regime_audit.py" \
    -o "$SCRIPT"

  curl -fLsS --retry 3 \
    "$RAW/$DEPENDENCY_COMMIT/$REL/stage12/12_repair_non_syv_science_holds.py" \
    -o "$BASE/12_repair_non_syv_science_holds.py"

  python3 -B -m py_compile "$SCRIPT"
  python3 -B -m py_compile \
    "$BASE/12_repair_non_syv_science_holds.py"

  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --audit \
    2>&1 | tee "$BASE/stage19_original_T_multiday_readonly.log"
)
~~~

The audit checks original full-length SHA256 for US-SP1/US-SRG/US-Seg, Stage12 final 148/156 ledger with exact eight held timestamps and Stage14 8/8 humidity closure receipt, plus original BIF SHA, geometry and offset. It scans ±3 days around each event and prints QC counts, contiguous episodes for QC0 original TA_F−TA_ERA ≤−10°C, and an exploratory QC0 band of TA_F within 11.15±0.05°C, together with same-clock ±2 day comparisons. The thresholds are research *screening* definitions, NOT approved data-repair thresholds.

**Science gates:** all eight original temperature disputes remain held until independently investigated. US-Syv's 606 old holds + 10 skipped Stage07 ERA endpoints remain deferred. No forcing/QC/CDS/Post-v5/DATM/CIME/Slurm/model/spinup modifications.

**Return:** the IRIDIS6 output in ~/ameriflux_batch04_stage19/stage19_original_T_multiday_readonly.log. The operator supplied Stage19 `--audit` PASS output with all six target events; the results are archived in [Stage19 verified report](STAGE19_VERIFIED_MULTIDAY_TEMPERATURE_REGIMES_2026-10-25.md). Re-execution is optional for reproducibility; the script is read-only.
