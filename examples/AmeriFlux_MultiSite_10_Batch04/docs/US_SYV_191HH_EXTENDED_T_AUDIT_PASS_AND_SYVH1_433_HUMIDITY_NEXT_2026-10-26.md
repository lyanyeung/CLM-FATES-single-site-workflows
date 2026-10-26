# Batch04 US-Syv — remaining 85 native T source holds +106 extended anomalies successfully repaired; next SYVH1 residual humidity

**Provenance:** Actual operator-returned IRIDIS6 stdout, 2026-10-26 02:47 UTC candidate directory. User had explicitly authorised replacing all remaining US-Syv anomalous original QC0/QC1 T, on top of previously independently verified 106 HH six-interval T alternative. This memo distinguishes **verified completed operator actions** from **new code not yet run on IRIDIS6**.

## Verified operator result — 191 NEW HH, 438288 complete-source SHA audit PASS

| Metric | Value |
| --- | --- |
| Previously manually approved six interval T replacements | **106 HH** |
| Previously remaining science-T-HOLD original QC0/QC1 | **85 HH** |
| Additional contiguous original QC0/QC1 source `TA_F−TA_ERA≤−8°C` native HH verified by strict source boundaries | **106 HH** |
| Newly operator-approved derived research T and VPD/RH changed HH | **191 HH** |
| Cumulative selected user-approved US-Syv replacement HH | **297 HH** (106 prior +191 new) |
| Original source QC0 among 191 | **50 HH** |
| Original source QC1 among 191 | **141 HH** |
| Humidity treatment at all new changed HH | **191/191 matched paired FLUXNET `VPD_ERA` physically admissible at new `TA_ERA`**; derive RH, QC2 |
| Extra humidity HOLD introduced by these selected T replacements | **0** |
| Complete candidate native HH independently audited | **438288** |
| Changed CSV field cells in this last 191-HH pass vs directly preceding Syv candidate | **573** |
| Original raw sources / other nine site manifest entries | **UNCHANGED** |

Complete operator-produced file:
```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_US_Syv_remaining_T_all_QC0_QC1_ERA_research_candidate_not_approved/candidate_20261026T024759Z_6e1e07ad/US-Syv_all_remaining_QC0_QC1_ERA_T_full_FLUXMET_HH.csv
```

**Verified SHA256 `508295cfb64d5cfd116e4e6f91acc304b15ee16d3c6fab4673e07680137592ad`**.

Ten-site research selection at `candidate_20261026T024759Z_6e1e07ad/RESEARCH_TEN_SITE_MANIFEST.tsv`; other nine site source entries unchanged, retaining operator-approved US-SP1 and US-SRG research alternatives. None of this is official tower correction or Post-v5/CLM/CIME model approval.

Source-based 191-HH expanded changes form **28 contiguous actual trial episodes**, not simply the 30 old flagged runs. Important actual operator-verified examples:

- `200305300600→200305301900`: 27 HH, of which 21 were **not** included in historical six source HOLDs.
- `200804041830→200804050430`: 21 HH, of which 16 extended beyond old five-HH HOLD.
- `200804031830→200804040100`: 14 HH, 10 extensions.
- `200705092000→200705100230`: 14 HH, 10 extensions.
- `200205221930→200205230400`: 18 HH, 6 extensions.
- `200703291900→200703292130`: 6 HH (now user-approved temperature replacement, including previously tentative QC0 retention).

The processed reference `TA_ERA` and `VPD_ERA` remain **original FLUXNET packaged ERA5-derived** fields, not independent ERA5-Land downloads. Source QC0/1 provenance stays in each audit ledger, candidate temperature QC2 reflects ERA origin. The model input candidate is research-only.

## Last original science HOLDs: 433 humidity reasons; not all are VPD-physical failures

Actual operator report: `STILL_UNDECIDED_NON_T_SCIENCE_HOLD_HH 433`. Earlier original US-Syv provenance: 606 Stage05 inherited original HOLDs +10 Stage07 independently skipped endpoints (0 overlap), 616 distinct. The 183 T science-source HOLD timestamps have now been adjudicated (98 prior+85 new); the remaining **433 old non-T HOLD HH** comprise 419 `ERA_PAIR_HUMIDITY_INVALID`, 4 `ERA_RH_OUTSIDE_QCV5_USABLE_RANGE`, and 10 `ERA_VPD_EXCEEDS_SATURATION_AT_RETAINED_TOWER_T`. They may include original physically valid values: do not assume all 433 need numeric VPD edits, and do not assume all 500 previously source-invalid VPD HH still remain after additional T repairs.

### New next script, research-only, 433 exact H/H science source audit

GitHub [`stage_syvh1_433_residual_humidity_era5land_source_safe.py`](../scripts/manual_review/stage_syvh1_433_residual_humidity_era5land_source_safe.py), **pinned commit `190cc7dcfac32378108d32f905bdf6f8ea8d0137`**, **not yet run on operator IRIDIS6**. Also requires the **unchanged source helper** [`10_era5land_independent_humidity_fill.py`](../scripts/stage10/10_era5land_independent_humidity_fill.py), downloaded from the **same pinned commit** beside the new script.

This next script:
1. Exact **433 unique native HH** from original SHA-pinned 606+10 HOLD ledger minus user-approved **106+191** source-temperature trial timestamps; verify source original paired ERA / original BIF UTC clock metadata and SHA-pinned final Syv 438288-HH CSV.
2. `--check`: classify true residual VPD saturation failures vs 18-ish physically valid historic HOLDs **from actual new file**, report reasons and site-years requiring external verified ERA5-Land `2m_temperature`, `2m_dewpoint_temperature`, `surface_pressure`. No downloads, no writes.
3. `--run --max-downloads 5`: fetch up to **five** missing CDS site-years through the unchanged Stage10 helper, validating grid UTC hourly coverage, location, years and SHA receipts; otherwise `--apply-existing` uses only verified already available source evidence without CDS requests. A CDS account / credentials may be needed for `--run`.
4. For numeric invalid VPD at **retained current TA**, first use independent ERA5-Land verified dewpoint/T2m-based RH and compute candidate VPD at retained `TA_F`, otherwise **only** use FLUXNET paired ERA derived RH when **both source `TA_ERA` and `VPD_ERA` are themselves physically admissible**. **Never blindly copy invalid `VPD_ERA` to colder tower T or cap its value**; T, pressure, QC and all other columns are preserved. Underlying original historical source holds are never rewritten.
5. Write new versioned complete **438288-HH candidate** only when at least one correction has trusted humidity support, then independently audit every changed vs unchanged source row and emit evidence source type, source hashes, any still unsolved native HH and the updated exact ten-site research selection.

Run read-only check first:

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  COMMIT="190cc7dcfac32378108d32f905bdf6f8ea8d0137"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$RAW/$COMMIT/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage10/10_era5land_independent_humidity_fill.py" -o "$BASE/10_era5land_independent_humidity_fill.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review/stage_syvh1_433_residual_humidity_era5land_source_safe.py" -o "$BASE/stage_syvh1_433_residual_humidity_era5land_source_safe.py"
  python3 -B -m py_compile "$BASE/"*.py
  python3 -u -B "$BASE/stage_syvh1_433_residual_humidity_era5land_source_safe.py" --check 2>&1 | tee "$BASE/US_Syv_433_humidity_inventory.log"
)
```

If independent site-year data are missing and CDS credentials are available, run with `--run --max-downloads 5`; it downloads at most five yearly grid responses per pass and constructs an independent science candidate using all available trusted evidence. If no download is desired, use `--apply-existing`; this can produce a **partial** data candidate and report remaining originals. Do not infer complete science readiness from numerical fixes without a second full ten-site Post-v5 check.

**No new Syv 433-HH humidity correction has been confirmed in operator logs yet. No Post-v5/DATM/CIME/Slurm/spinup release.**
