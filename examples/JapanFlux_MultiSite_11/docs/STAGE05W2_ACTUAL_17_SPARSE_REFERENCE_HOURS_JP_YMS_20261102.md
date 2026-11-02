# JapanFlux Stage05W2 — ACTUAL corrected sparse-hour CDS audit PASS (2026-11-02)

## Actual IRIDIS6 operator result

The operator executed [Stage05W2](../scripts/stage05/05w2_JP_Yms_sparse_source_hours_CDS_ZIP_READONLY.py) against the **original JP-Yms independently downloaded CDS ERA5-Land ZIP** and source-derived Stage05O, Stage05R and Stage05V outputs. Real terminal output:

```text
/home/ly3n24/japanflux_stage05s/downloads/JP-Yms_ERA5Land_timeseries_20050811_CSV_response.zip: OK
STAGE05W2 SELF-TEST PASS | 9-hour UNION is not necessarily 18 variable-hour pairs; source-QC2 checks; NO WRITES
STAGE05W2 SOURCE-EXACT SPARSE-HOUR AND SECOND CDS ZIP AUDIT PASS | NO CDS / SLURM / REPAIR
ORIGINAL_JP_YMS_SOURCE_HOURS 14:00,15:00,16:00,17:00,18:00,19:00,20:00,21:00,22:00
ORIGINAL_VARIABLE_HOUR_PAIRS 17 BY_VARIABLE {'surface_pressure': 9, 'surface_thermal_radiation_downwards': 8}
CDS_ZIP_SHA256 4bf228a3a53ab7fc6751b8e7438fb459570536ce6f54af2f81de5afc083b59d5 CSV_MEMBERS 2 HOURLY_NUMERIC_VALUES 48
CDS_GRID [34.80000000000106, 135.79999999999654]
ERA5L 2005-08-11T17:00Z surface_thermal_radiation_downwards 411.743333 W m-2 hourly mean
ERA5L 2005-08-11T18:00Z surface_thermal_radiation_downwards 418.053889 W m-2 hourly mean
ERA5L 2005-08-11T19:00Z surface_thermal_radiation_downwards 405.383889 W m-2 hourly mean
ERA5L 2005-08-11T17:00Z surface_pressure 98.89343 kPa
ERA5L 2005-08-11T18:00Z surface_pressure 98.88828 kPa
ERA5L 2005-08-11T19:00Z surface_pressure 98.93342 kPa
CDS_VALUES /home/ly3n24/japanflux_stage05w2/run_20261102T110019Z/stage05w2_Yms_20050811_independent_ERA5L_2x24_HOLD.tsv
AUDIT_REPORT /home/ly3n24/japanflux_stage05w2/run_20261102T110019Z/stage05w2_CDS_source_and_sparse_hour_scope_audit.json
NO JPF HALF-HOUR REPAIR; ALL 45 SOURCE FLAGS HOLD
```

### Correction of the previous Stage05W failure

[Original Stage05W](../scripts/stage05/05w_JP_Yms_20050811_independent_CDS_zip_source_audit_NO_REPAIR.py) failed at a false, source-unsupported invariant requiring **nine UTC hours × two requested variables = eighteen** distinct variable-hour cells. Stage05P actually constructs requested hour context **per original flagged variable**, which can overlap only partially. Stage05W2 rebuilt original QC2+local-standard UTC+9 provenance from Stage05O and compared per-variable, per-hour, per-source-half-hour keys to Stage05R. **Actual correct result: 17 cells**, partitioned **9 pressure + 8 longwave**, across **9 unique UTC hours**. The failed predecessor remains unchanged for reproducibility; never treat it as the source of a CDS data failure.

### Independently retrieved physical context (not replacement forcing)

| Valid UTC hour, 2005-08-11 | Independent ERA5-Land surface pressure (kPa) | Independent ERA5-Land downward LW (W m⁻², hourly mean) |
|---|---:|---:|
| 17:00 | 98.89343 | 411.743333 |
| 18:00 | 98.88828 | 418.053889 |
| 19:00 | 98.93342 | 405.383889 |

CDS point request used original JP-Yms BIF location **34.790278°N, 135.840939°E**, tower elevation **220m** and original BIF SHA256 `7c0a5ba5f137e28518f69ed14b255834fb5b223ac325556719abe5a55e8b0f56`. The returned nearest-grid coordinate was **34.80000000000106°N, 135.79999999999654°E**. The external **ERA5-Land grid elevation is unverified**. Independent grid meteorology is not in itself the exact JPF 30-min tower value; downward thermal radiation was an ERA5-Land hourly de-accumulated integral divided by 3600 seconds to obtain mean W m⁻², not half-hour observed radiation.

**No original JP-Yms source anomalous values are shown in Stage05W2's stdout.** Therefore, independent source-defect evidence for any particular JP-Yms field is not yet established. Stage05W2 confirms only original clock source window/metadata provenance, actual downloaded 2×24 hourly independent reference, and grid/unit plausibility. The previous JP-Khw Stage05V evidence register still covers the **only eight independently compared QC2 fields**.

### Stage05X next scientific task

[Stage05X original JP-Yms source QC2 versus independent CDS hourly context](../scripts/stage05/05x_JP_Yms_original_QC2_vs_independent_CDS_hourly_CONTEXT_READONLY.py) is committed but **not yet run on the user's actual Stage05O/W2 reports**. It verifies the full Stage05O original 27-field UTC-verified QC2 HOLD registry, includes JPF selected F vs SAME-RELEASE ERA equality and BIF UTC+9, uses the independently downloaded Stage05W2 48-hourly-point TSV/audit (including original CDS ZIP SHA256 and exact 17-cell source window provenance), and builds only contextual 3-hour per-variable comparisons. For each actual JP-Yms selected-F field on 2005-08-11 UTC, output the original local timestamp, original QC2 value, original same-product ERA, independently sourced 3-hour values, difference/outside-range indicator, and an explicit **SCIENCE HOLD**. Do **not** assume how many JP-Yms source fields the date contains prior to reading actual records.

Next after Stage05X is decide whether each field is strongly inconsistent and compare other remaining site/day windows, not automatically repair FATES input or force hourly-to-halfhour extrapolation.

### Portfolio status

- Actual independent CDS ZIPs: **2 of 9** site×UTC-day windows, both **2005-08-11** at JP-Khw and JP-Yms. **7 remain**.
- Independent per-source-field context: **8 original JP-Khw field candidates** presently evidenced, **JP-Yms original candidate tie remains pending Stage05X**.
- Original source candidate total **45 field records at 35 unique site×half-hour times**. **27** at source-standard-time UTC-verified JP-Fjy/Khw/Yms; **18** at JP-Tef/Tmd original `local solar time` versus general ONEFlux `local standard time` source convention conflict.
- Original JPF ZIP, flux meteorology, forcing, cases unmodified; no extra CDS calls or Slurm jobs in Stage05W2. All **45** original source records continue **HOLD**, none repaired or approved for AD400.
