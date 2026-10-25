# Batch04 Stage21 — FINAL internal original release temperature source availability check

**Status (2026-10-25): Stage20 VERIFIED PASS; Stage21 OPERATOR-VERIFIED IRIDIS6 PASS, 3/3 original FLUXNET station releases, 48/48 CSV headers and all 6 event contracts audited.** No separately named instrument-level TA channel detected in these FLUXNET packages, **8/8 original tower-temperature scientific HOLDs remain**. See [complete verified Stage21 results](STAGE21_VERIFIED_ORIGINAL_TEMPERATURE_SOURCE_COVERAGE_2026-10-25.md) and [verified site contact and source-request pack](STAGE21_SITE_OPERATOR_TEMPERATURE_REQUESTS_2026-10-25.md). Original code/command is retained here solely for reproducibility.

**Why not automatically repair?** Stage20 only found one BIF temperature-related group per site, and in every case that matching row was ERA_VARIABLE=TA. That denotes an ERA-related variable rather than raw TA sensor instrumentation. Stage19 already documented recurring US-SP1 daytime and winter sub-periods versus TA_ERA, a single US-SRG QC0 outlier, and continuous original US-Seg cooling. QC2 substituted temperatures and TA_F=TA_F_MDS equality are NOT independent tower sensor confirmations.

See [Stage20 verified original BIF findings, all three original BIF SHA256 and decision gates](STAGE20_VERIFIED_BIF_TEMPERATURE_PROVENANCE_2026-10-25.md).

## Targeted final internal-only check

The [Stage21 source](../scripts/stage21/21_audit_original_release_temperature_source_coverage.py) checks the **original extracted 16 CSV files for each of US-SP1, US-SRG and US-Seg** and inventories all original file names/product families, first-line headers and TA-like candidate fields. It distinguishes consolidated/gapfilled FLUXMET, BIF metadata and ERA5 products from **possible**, not presumed, raw tower temperature channels. If field names suggest an instrument channel, that is only an unverified *candidate* until its provenance, clock and independent QC are reviewed.

Stage21 also checks any BIF FLUX_MEASUREMENTS variable/method/start metadata groups without treating flux-instrument entries as original TA sensor descriptions. It SHA-pins original native FLUXMET and BIF for the three stations; validates stage12 148/156 repair-state and the exact eight science-HOLD timestamps. It reads CSV headers and BIF metadata rather than reprocessing entire 368k-row files. It NEVER downloads CDS, edits model forcing, resets QC, creates Post-v5/DATM/CIME sources or submits SLURM.

### Exact IRIDIS6 command (curl, not git pull)

~~~bash
(
  set -euo pipefail

  BASE="$HOME/ameriflux_batch04_stage21"
  ROOT="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts"
  NEW="83c99e69cc51f992a1c24382dfd1cfc8b3655dd1"
  OLD="9be06860ee3e9f14e08fb078d22d0090b49d58d4"

  mkdir -p "$BASE"
  SCRIPT="$BASE/21_audit_original_release_temperature_source_coverage.py"

  curl -fLsS --retry 3 \
    "$ROOT/$NEW/$REL/stage21/21_audit_original_release_temperature_source_coverage.py" \
    -o "$SCRIPT"

  curl -fLsS --retry 3 \
    "$ROOT/$OLD/$REL/stage12/12_repair_non_syv_science_holds.py" \
    -o "$BASE/12_repair_non_syv_science_holds.py"

  python3 -B -m py_compile "$SCRIPT"
  python3 -B -m py_compile "$BASE/12_repair_non_syv_science_holds.py"
  python3 -B "$SCRIPT" --self-test

  python3 -B "$SCRIPT" --audit \
    2>&1 | tee "$BASE/stage21_original_temperature_source_coverage_readonly.log"
)
~~~

## Decisive interpretation: no endless rechecks

- If a raw-like TA sensor field is identified, its filename/header alone still cannot establish independent sensor truth; obtain corresponding original raw observation, sensor metadata, native local-standard clock, measurement height, source-side QC and data permissions before considering any temperature replacement.
- If only ERA5/TA_ERA, FLUXMET MDS/consolidated and BIF metadata are present, **stop further internal-only script iterations** for these original QC0 events. Obtain independent tower-met observations directly from AmeriFlux data holders/site operators or trusted archived station data before adjudicating original sensor validity.
- For **US-SP1**, request source measurement details covering 2000-10-09, 2007-10-15–18, 2008-01-15–17 and 2008-02-02–03; investigate time-of-day recurring residual episodes before modelling.
- For **US-SRG**, request original TA source QC and raw temperature on **2019-03-19 11:00–13:30 local standard time**; the 12:00 QC0 anomaly vs ERA remains an *unapproved isolated sensitivity idea*.
- For **US-Seg**, original 2016-12-27 17:00–20:00 raw TA/QC and instrument context may resolve plausibility of a cooling spell; do not correct purely from ERA differences.

**All eight** original tower-temperature science HOLDs remain pending, including the two historical US-SP1 Stage15 trial times. US-Syv **606 inherited science HOLDs** plus **10 skipped Stage07 ERA endpoints** remain deferred. **Post-v5/DATM/CIME/SLURM/spinup NOT APPROVED.**

**Operator provided the actual Stage21 log; the source scan PASSED and found no separate raw TA sensor columns in the original FLUXNET release headers.** This completes the planned internal-only source-availability gate. Do **not** start Stage22 for the same six points without genuinely new independent data. [Proceed to independent source requests](STAGE21_SITE_OPERATOR_TEMPERATURE_REQUESTS_2026-10-25.md) and consider the distinct AmeriFlux BASE products under source-side QC/height/clock checks. No outreach has been sent and no BASE file has been verified in this workflow.
