# Batch04 US-Syv SYVH1 completed 363/433 humidity repairs; last 6 ERA5-Land site-years and 18 old physical holds

**Date 2026-10-26.** This record is from the user's exact IRIDIS6 printed stage_SYVH1 operator-run log, **NOT an inferred model-run success**.

## Completed, operator-verified

- Source contracts passed: previous 106HH +191HH (297HH) user-approved T-replacement full file, original 606 Stage05 source HOLD +10 Stage07 edges, exact 433 residual humidity-only old science records, BIF latitude **46.242**, longitude **−89.3477**, **UTC_OFFSET −6** (tower local-standard native time).
- Initially no independent ERA5-Land year response receipts on Syv. CDS successfully fetched and independently validated full hourly T2m, d2m, SP data for **2019**, **2007**, **2004**, **2008**, **2005**, with response SHA/UTC/grid coordinate/physics receipts. Source SHA-verified by Stage10 helper.
- Actual **VPD/RH repaired 363 HH**, **359** using independently verified ERA5-Land humidity, **4** using physically validated processed FLUXNET paired ERA relative humidity projected to retained site TA. All changed HH preserve existing source tower `TA_F` (including all manually approved T replacements).
- **INDEPENDENT HUMIDITY FULL FILE AUDIT PASS** for all **438288 HH**, **363** modified native HH, **726** modified field cells; original files, all older trials, other 9 site manifest source selections unchanged.
- Result dir (actually created):
  ```
  /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_US_Syv_stage_SYVH1_433_humidity_era5land_candidate_not_approved/candidate_20261026T031156Z_2cc2fb07
  ```
- Syv full output SHA256 **`8c64b0638836e80e4406c452db02fe1eedfc78934c7f98318cdbacceac6dc786`**. Includes an exact 10-site research manifest with all other nine source selection entries unchanged.
- **70 old science-HOLD HH remain** after this candidate: **52 physically invalid VPD without valid source due to missing site-year independent grid** plus **18 physical VPD-valid but historical source ERA-HOLD labels**. This is **not** the same as 70 confirmed wrong humidity measurements.

## Six remaining missing source years (no human decision needed to request verified independent ERA5-Land)

| Year | Residual old source-HOLD HH in that year, including potential physically valid ones |
| --- | ---: |
| 2009 | 31 |
| 2021 | 21 |
| 2006 | 9 |
| 2003 | 7 |
| 2011 | 5 |
| 2002 | 1 |
| **Yearly affected total** | **74** |

**Caution:** 74 is a per-year **source-HOLD** census, not 52 actually humidity-invalid HH. The six years' source-HOLD count includes physical-valid historic flags. Also there are only **six missing year files**, not 74 download requests: Stage10 helper requests complete hourly arrays for each year and ±boundary coverage.

**Next automatic execution:** Use the *same SHA-pinned* SYVH1 script **twice** with `--run --max-downloads 5`: first call downloads up to 5 still-missing site-years and creates a versioned candidate, second downloads the final 1 year and creates a **new independently verified complete 433-target candidate**. The second candidate includes all 11 site-year source receipts; do **not** select the first candidate's partial 70-HOLD lineage for Post-v5. Both calls preserve original sources/older candidates. Or fetch all six site-years with a helper-only orchestrator first, then run `--apply-existing` once; actual parent/source SHA contracts must remain unchanged. The previous working SYVH1 pinned code is at commit `190cc7dcfac32378108d32f905bdf6f8ea8d0137`; previous successful run establishes those source assumptions. The needed `10_era5land_independent_humidity_fill.py` helper resides in same local folder.

**After source downloads:** use new read-only [`stage_syvh2_audit_remaining_humidity_and_18_historical_holds.py`](../scripts/manual_review/stage_syvh2_audit_remaining_humidity_and_18_historical_holds.py), pinned commit `8800a3713b2a9ff5adb1cae071bf3746bb39694d`. It audits source SHA for new last candidate, original 606+10 history, parent 106+191 ledger, 433 residual native HH, the complete full-site candidate, all VPD/TA physics and the precise **historical 18** VPD-physically valid source-labelled HOLD entries. It prints provenance classifications by original VPD QC, native RH/T closure and whether archived flags were about the **invalid paired ERA source** rather than VPD itself. It does not silently clear historical source flags or overwrite any original file.

## Ready-to-run one-block IRIDIS6 commands, with exact verified source revisions

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  OLD="190cc7dcfac32378108d32f905bdf6f8ea8d0137"
  NEW="8800a3713b2a9ff5adb1cae071bf3746bb39694d"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  mkdir -p "$BASE"

  curl -fLsS --retry 3 "$RAW/$OLD/$REL/scripts/stage10/10_era5land_independent_humidity_fill.py" \
    -o "$BASE/10_era5land_independent_humidity_fill.py"
  curl -fLsS --retry 3 "$RAW/$OLD/$REL/scripts/manual_review/stage_syvh1_433_residual_humidity_era5land_source_safe.py" \
    -o "$BASE/stage_syvh1_433_residual_humidity_era5land_source_safe.py"
  curl -fLsS --retry 3 "$RAW/$NEW/$REL/scripts/manual_review/stage_syvh2_audit_remaining_humidity_and_18_historical_holds.py" \
    -o "$BASE/stage_syvh2_audit_remaining_humidity_and_18_historical_holds.py"

  python3 -B -m py_compile \
    "$BASE/10_era5land_independent_humidity_fill.py" \
    "$BASE/stage_syvh1_433_residual_humidity_era5land_source_safe.py" \
    "$BASE/stage_syvh2_audit_remaining_humidity_and_18_historical_holds.py"

  python3 -u -B "$BASE/stage_syvh1_433_residual_humidity_era5land_source_safe.py" --run --max-downloads 5 \
    2>&1 | tee "$BASE/US_Syv_SYVH1_last6_years_part1.log"
  python3 -u -B "$BASE/stage_syvh1_433_residual_humidity_era5land_source_safe.py" --run --max-downloads 5 \
    2>&1 | tee "$BASE/US_Syv_SYVH1_last6_years_part2_FINAL.log"

  FINAL=$(sed -n 's/^US-SYV SYVH1 NUMERICALLY SAFE HUMIDITY CANDIDATE CREATED & FULL AUDIT PASS //p' \
    "$BASE/US_Syv_SYVH1_last6_years_part2_FINAL.log" | tail -n 1)
  test -n "$FINAL" && test -d "$FINAL"
  python3 -u -B "$BASE/stage_syvh2_audit_remaining_humidity_and_18_historical_holds.py" \
    --candidate "$FINAL" --report \
    2>&1 | tee "$BASE/US_Syv_SYVH2_final_18_original_science_hold_audit.log"
)
```

**Need for new manual decisions:** **None right now** for these 52; independent ERA5-Land source retrieval and humidity-only physical reconstruction is a mechanical, earlier approved method. For the **18 old physics-valid source-labelled cases**, only seek user manual choice if the automatic source QC/RH closure check identifies genuinely conflicting or unverified values. Never mark 18 historical science HOLDs as fully closed from VPD saturation alone.

**Completion gate:** Even if all 433 source humidity numerical mismatches are addressed, release of all ten Batch04 sites for Post-v5 DATM and CLM-FATES spinup is a separate independent QA step; do not use this research-only manifest for jobs before it passes.
