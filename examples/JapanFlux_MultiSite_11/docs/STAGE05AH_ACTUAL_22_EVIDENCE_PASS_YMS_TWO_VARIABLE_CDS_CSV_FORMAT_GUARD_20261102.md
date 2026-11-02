# JapanFlux Stage05AH — actual 22-source-field evidence PASS; two JP-Yms CDS days remain; Stage05AB two-variable ZIP parser patch (2026-11-02)

## Actual IRIDIS6 read-only scientific ledger merge

The operator executed the pinned Stage05AH using the original 27 UTC-confirmed (JST UTC+9) and 18 native time-ambiguous QC2 source entries, Stage05AE unified 19 independent source-variable physical-context records, Stage05AG corrected JP-Khw 2011 three pressure source-variable comparisons and the actual Stage05AB reference-ZIP SHA/CRC/UTC/grid inspection:

```text
STAGE05AH SELF-TEST PASS | 19+3=22 original source QC2 fields, 5 Yms UTC-ready, 18 clock conflict, 2 CDS days; NO WRITES
STAGE05AH 22 SOURCE FIELDS INDEPENDENT CONTEXT MERGE PASS | NO CDS / SLURM / REPAIR
STRONG_CONTEXT_EVIDENCE 22 /45 BY_SITE {'JP-Fjy': 6, 'JP-Khw': 11, 'JP-Yms': 5} DISTINCT_SITE_NATIVE_HALF_HOURS 17
UTC_VERIFIED_AWAITING_INDEPENDENT_REVIEW 5 TIMEBASE_CONFLICT_HOLD 18
CDS_SITE_DAYS_VALIDATED 7 REMAINING_YMS_SITE_DAYS 2
CDS_REMAINING JP-Yms 2011-12-16 VARIABLES surface_pressure,surface_thermal_radiation_downwards
CDS_REMAINING JP-Yms 2011-12-17 VARIABLES surface_pressure,surface_thermal_radiation_downwards
SOURCE_EVIDENCE_TSV /home/ly3n24/japanflux_stage05ah/run_20261102T191634Z/stage05ah_22_original_source_QC2_ERA5L_independent_context_HOLD.tsv
REMAINING_DAYS_PREVIEW /home/ly3n24/japanflux_stage05ah/run_20261102T191634Z/stage05ah_2_remaining_JP_Yms_CDS_site_UTC_days_PREVIEW_ONLY.json
SCIENCE_COVERAGE_SUMMARY /home/ly3n24/japanflux_stage05ah/run_20261102T191634Z/stage05ah_45_original_source_field_science_coverage_NO_REPAIR.json
ALL_45_SOURCE_QC2_FIELDS_HOLD; NO REPLACEMENTS APPROVED
```

This confirms **22/45** original JPF QC2 selected-source variable records have strong independent external ERA5-Land *physical-context* evidence at **17** site×native half-hours, not approved corrections or replacements. **Five** remaining UTC-verified original QC2 source fields belong to JP-Yms, and **18** other JP-Tef/Tmd flagged source-variable fields still have source time basis conflicting between local solar and local standard time; they cannot be assigned a verified UTC timestamp yet. All 45 original source flags remain science HOLD.

Independent ERA5-Land source payload availability: **7 of 9** site×UTC-day windows have passed original ZIP SHA/CRC/content/24h/variable/grid checks. The remaining two original source-scoped UTC days are **JP-Yms 2011-12-16 and 2011-12-17**, both with:
- `surface_pressure` → CDS raw CSV `sp`, units Pa; conversion to kPa is `/1000`;
- `surface_thermal_radiation_downwards` → CDS raw CSV `strd`, units J m⁻² accumulated in the hourly time step; for hourly average W m⁻², divide by 3600 **after verifying the time interval and accumulation semantics**. This does not authorize pointwise 30-minute longwave replacements.

## Prevent format mismatch before JP-Yms two-variable retrieval

Stage05S already builds a **single-day request with both original source variables** in one CDS API call. However, the original Stage05AB independent ZIP source validator assumed that two variables must be in **two separate CSV members with 4 columns each**. A possible valid original CDS format is **one combined CSV member** with `valid_time,latitude,longitude,sp,strd`, and incorrectly rejecting this would be a code limitation rather than a science data failure.

The source script was patched: [Stage05AB original six-day audit, combined or split source CSV handling](../scripts/stage05/05ab_inventory_six_2011_existing_CDS_ZIP_partial_CRC_READONLY.py), commit `cbbdb1c2b02dbab971ea206f72df5a17a787fd20`, Git blob SHA256? **Git blob SHA** `15152d551dbeb9c43d462013db3bec34af789e95` (not the file-byte SHA256). New behavior:
- Retains original provenance checks for Stage05AA six site-days and Stage05R 87 source-bounded UTC variable-hour pairs, plus no symlink/no overwrite/CRC/zip member traversal paths.
- Accepts only **one combined** `sp,strd` CSV or **two split** `sp` and `strd` CSVs for JP-Yms, or single-column `sp` CSV for each JP-Fjy/JP-Khw day.
- Requires **24 unique whole-hour UTC rows per variable** and exact expected day, source raw column names, finite numbers, consistent nearest model grid cell, near-original BIF coords and broad physical pressure/radiation bounds. Each of the two requested variables must be present once: exactly **48 independent variable×hour values** per JP-Yms source day. Unrequested or duplicated fields fail the audit.
- Includes a newly written **in-memory, no-network/no-disk regression self-test** for combined CSV, split CSV, duplicate/missing variable and historical `sp`-only case. **First real IRIDIS run of this patched Stage05AB is pending**, and syntax/self-test must PASS before it is used.

## Next operator action

Pin and run patched Stage05AB `--self-test` and full **pre-download read-only original six-day inventory** to confirm the two JP-Yms date targets and all their `.zip`, `.zip.partial`, `.csv`, `.nc` variants are absent. Cross-check the Stage05AH remaining exact two day/source/variable science manifest, which contains original JP-Yms BIF coordinates. Then optionally submit **only JP-Yms 2011-12-16 UTC**, `surface_pressure` + `surface_thermal_radiation_downwards`, through original Stage05S, protecting all alternative filenames from overwrite. Rerun patched Stage05AB to read the **actual** untouched returned ZIP and decide whether content is valid; a successful CDS request alone does not change 22-source-field evidence.

After Dec16 ZIP contents are verified, obtain Dec17 only as another source-scoped single-day action. Then compare the five original JP-Yms source-variable records against exact source-hour matched independent 48-hour pressure/longwave contexts. No source JPF, model, forcing, Slurm, AD400, 30-minute point replacements or science approval is performed during the validation.
