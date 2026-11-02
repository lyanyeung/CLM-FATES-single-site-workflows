# JapanFlux Stage05U actual 8/8 original QC2 source defects supported by independent ERA5-Land — Stage05V (2026-11-02)

## Actual operator-executed Stage05U result

The operator ran [Stage05U](../scripts/stage05/05u_crosscheck_Khw_original_stage05o_HOLD_with_CDS_stage05t_hourly_NO_REPAIR.py) on previously SHA-verified (i) Stage05O original selected-F anomalous JPF data, and (ii) Stage05T independent downloaded ECMWF ERA5-Land 2005-08-11 UTC CSV/JSON. The operator posted:

```
STAGE05U SELF-TEST PASS | source QC2, numeric units, 3h context and UTC mapping; NO WRITES
STAGE05U INDEPENDENT ERA5-LAND 3h CONTEXT JOIN PASS | NO CDS / ZIP / SLURM / REPAIR
SOURCE_SCOPE JP-Khw 2005-08-11 ORIGINAL_SOURCE_FIELDS 8 UNIQUE_SITE_HALF_HOURS 4
OUTSIDE_CONTEXT_RANGE 8
SOURCE_COMPARISON_CONTEXT /home/ly3n24/japanflux_stage05u/run_20261102T031653Z/stage05u_Khw_20050811_JPF_vs_independent_ERA5L_3hour_CONTEXT_HOLD.tsv
AUDIT_SUMMARY /home/ly3n24/japanflux_stage05u/run_20261102T031653Z/stage05u_source_ERA5L_science_context_summary.json
NO HALF_HOUR ERA5L INTERPOLATION OR PRESSURE_ELEVATION_ADJUSTMENT OR SCIENCE_REPAIR
ALL_45_SOURCE_SELECTED_ANOMALIES_STILL_HOLD
```

The 8 original JPF selected-F values, **all QC2 and numerically equal to the original release's own regression-downscaled ERA**, are joined to *separately downloaded*, hourly ECMWF ERA5-Land gridded references (three neighboring hours, NOT a half-hour replacement). Exact operator values:

| Source native JST 2005-08-12 | Field | Original JPF selected-F (QC=2) | Independent ERA5-Land 3-hour reference minimum–maximum | Source vs independent context |
|---|---|---:|---:|---|
| 02:00 | `LW_IN` | **39.171 W m⁻²** | 391.890–402.753 W m⁻² (hourly mean) | Much too low |
| 02:30 | `LW_IN` | **39.171 W m⁻²** | 391.890–402.753 W m⁻² (hourly mean) | Much too low |
| 02:30 | `PA` | **48.912 kPa** | 97.77343–97.85242 kPa | About half typical local pressure |
| 02:30 | `TA` | **−122.144 °C** | 22.96188–23.222 °C | Physically impossible at the near-surface site |
| 03:00 | `PA` | **0 kPa** | 97.77828–97.88934 kPa | Physically impossible surface pressure |
| 03:00 | `TA` | **−268.276 °C** | 22.96188–23.04397 °C | Physically impossible at site |
| 03:30 | `PA` | **48.922 kPa** | 97.77828–97.88934 kPa | About half typical local pressure |
| 03:30 | `TA` | **−122.665 °C** | 22.96188–23.04397 °C | Physically impossible at site |

The original source `LW_IN` ≈39 W m⁻² is *strongly implausible for this context*, but should not automatically be called mathematically impossible for every geography or atmospheric state. It is approximately one-tenth of independently modeled ~392–403 W m⁻²; **that ratio is diagnostic only**, not a proven unit-conversion error. The ~49-kPa and ~0-kPa surface pressures at an original BIF tower elevation 196 m strongly establish source contamination but a pressure replacement still requires land-grid elevation and appropriate temporal processing.

Independent CDS source: original 1,381-byte ZIP SHA256 `111c761e432f77c7fa287d7b9ee3d29a89405a33ece970f8ac81896ebee818b0` (operator Stage05S/T), 3 x 24 rows, `valid_time` in UTC, grid at ~33.1°N,130.7°E. Original source BIF tower at 33.13658°N,130.70834°E and 196m altitude. Raw independent units 2m temperature K, surface pressure Pa, downward thermal radiation hourly de-accumulated J m⁻²; conversion is K−273.15, Pa/1000 and Jm⁻² /3600 s respectively. The original selected JPF timestamps are in local standard time UTC+9 without DST, verified from original BIF and README.

**What is NOT yet approved or established:** a physically consistent *half-hour* replacement time series, hourly radiation-to-half-hour interpolation, exact effective 2005 JPF source processing bug, ERA5-Land grid elevation representativeness, and any forcing/model write. The independent hourly range is contextual and can verify grossly invalid original values, not certify the true tower half-hour value. All **45** variable-level source anomalies at **35** station×native half-hour events remain **HOLD**; this exercise independently checks only **8** fields at **4** JP-Khw half-hour times. The other **37** original fields are not yet fully supported by separate independent retrievals. JP-Tef/Tmd retain local-solar versus local-standard original README clock conflict and are excluded from UTC joins. JP-Tom/Tgf different-source humidity/VPD provenance is also not resolved.

## Next Stage05V: evidence ledger and remaining independent CDS dates

[Stage05V](../scripts/stage05/05v_JP_Khw_8_field_independent_evidence_and_8_remaining_CDS_day_PREVIEW_NO_REPAIR.py) is **published, not yet run on actual IRIDIS6 source reports**. It reads ONLY Stage05U's actual eight-field row TSV and summary, Stage05S's original nine site×UTC-day preview, and Stage05T's independently downloaded and inspected source provenance JSON. It fails closed unless the exact 8 keys, all QC2, original-F equals same-release ERA, all 8 outside hourly independent context, original CDS ZIP SHA, and prior science HOLD status are verified.

It produces:
- An **8-field evidence TSV** with original values, independent hourly contextual min/max, minimum difference from that range, and evidence strength classified as `NONPHYSICAL` for extremely low near-surface air temperatures or zero pressure, `SEVERE_SITE_PRESSURE_DEFICIT` for ~49 kPa, and `VERY_LARGE_LONGWAVE_DEFICIT` for ~39 W m⁻². Every row explicitly remains `HOLD_NOT_APPROVED_DO_NOT_WRITE_FORCING`.
- A JSON-only **eight remaining site×UTC-day CDS request plan**, excluding the already downloaded JP-Khw 2005-08-11 pilot. This **does not download** the other eight days, run Slurm or change any raw or derived forcing.
- A summary marking **8/8 strong independent evidence** and **37 remaining unverified source-field candidates**, not conflating contextual evidence with approval.

The original [Stage05S explicit one-site one-day CDS pilot script](../scripts/stage05/05s_ERA5Land_timeseries_one_day_CDS_pilot_opt_in.py) can be reused **one date at a time with explicit operator approval** after reviewing Stage05V's remaining-day plan. Avoid prematurely batch-submitting eight network requests before confirming the single-day CDS product's structure/units (Stage05T has now done that for one day), data use terms, and source clock; JP-Tef and JP-Tmd must not be included.

## GitHub science status

Stage05U complete, Stage05V code committed (first IRIDIS execution pending). No source ZIP or model forcing edits, CDS submissions or Slurm calls during Stage05U. No new scientific replacement approved and no AD400/Normal400 submitted through this workflow.
