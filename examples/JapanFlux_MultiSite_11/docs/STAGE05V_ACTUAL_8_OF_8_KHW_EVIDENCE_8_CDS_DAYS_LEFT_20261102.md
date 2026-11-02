# JapanFlux Stage05V — actual independent-source evidence PASS, 8 remaining CDS source windows (2026-11-02)

## Actual IRIDIS6 result

The operator ran the Stage05V evidence registration and remaining-window audit:

```
STAGE05V SELF-TEST PASS | 8 exact source QC2 candidates, 9-1=8 CDS days; NO WRITES
STAGE05V INDEPENDENT SOURCE DEFECT EVIDENCE AUDIT PASS | NO CDS / ZIP / SLURM / REPAIR
JP-Khw 2005-08-12 JST: 8/8 QC2 SOURCE ANOMALY FIELDS IN 4 HALF-HOURS
OTHER_SOURCE_FIELDS_CONTINUE_HOLD 37
REMAINING_INDEPENDENT_CDS_SITE_DAYS 8
SOURCE_EVIDENCE_TABLE /home/ly3n24/japanflux_stage05v/run_20261102T032324Z/stage05v_8_original_Khw_fields_independent_CDS_evidence_HOLD.tsv
REMAINING_REQUESTS_PREVIEW /home/ly3n24/japanflux_stage05v/run_20261102T032324Z/stage05v_8_remaining_CDS_site_UTC_days_PREVIEW_ONLY.json
SCIENCE_SUMMARY /home/ly3n24/japanflux_stage05v/run_20261102T032324Z/stage05v_science_HOLD_summary.json
NO REPLACEMENT VALUES; ALL 45 ORIGINAL-SOURCE FIELD CANDIDATES STILL HOLD
```

All **8** JP-Khw candidate fields (4 unique half-hours, 2005-08-12 JST) differ severely from the real independent ECMWF ERA5-Land neighboring-hour context; some violate basic near-surface physical limits. The source was JPF FLUXMET selected F, QC2, exactly equal to the same JPF release ERA-downscaled value. Stage05V does **NOT** approve repairs, 30-minute ERA interpolation or forcing writes.

### Science coverage split (do not miscount)

| Source set | Source-selected candidate variable fields | Independent CDS stage |
|---|---:|---|
| JP-Khw 2005-08-12 JST | **8** | Actual independent ERA5-Land retrieved; strong contextual evidence |
| Other JP-Fjy/JP-Khw/JP-Yms records, local-standard UTC+9 verified | **19** | Eight site×UTC-day windows not yet downloaded |
| JP-Tef/JP-Tmd original `local solar time` README vs BIF UTC+9 conflict | **18** | Native-only HOLD. **Not included** in those eight CDS dates |
| **Total** | **45** | **All HOLD**, none numerically repaired |

The outstanding **eight** independently downloadable site×UTC-day windows are:

| Site | UTC day | ERA5-Land reference variables |
|---|---|---|
| JP-Fjy | 2005-08-11 | surface_pressure |
| JP-Fjy | 2011-12-16 | surface_pressure |
| JP-Fjy | 2011-12-17 | surface_pressure |
| JP-Khw | 2011-12-16 | surface_pressure |
| JP-Khw | 2011-12-17 | surface_pressure |
| JP-Yms | 2005-08-11 | surface_pressure + surface_thermal_radiation_downwards |
| JP-Yms | 2011-12-16 | surface_pressure + surface_thermal_radiation_downwards |
| JP-Yms | 2011-12-17 | surface_pressure + surface_thermal_radiation_downwards |

The already downloaded JP-Khw 2005-08-11 UTC CDS response is a distinct, successful pilot and must **not** be downloaded again or counted among those eight.

## Stage05W recommended second CDS test

Prioritize **JP-Yms 2005-08-11 UTC** because both surface pressure and downward longwave can be examined, and this provides a second independent grid location rather than repeating JP-Khw. Existing pinned [Stage05S](../scripts/stage05/05s_ERA5Land_timeseries_one_day_CDS_pilot_opt_in.py) supports a single operator-selected site/day request to `reanalysis-era5-land-timeseries`; no new API client is required. Its one-day request returns full hourly UTC values, not a sparse set.

Do **not** automatically batch-request all eight windows just because the earlier one-day pilot succeeded. The CDS time-series product is an experimental/alternative processed service according to the [ECMWF official product guide](https://confluence.ecmwf.int/pages/viewpage.action?pageId=576394633), and accumulation variables are hourly de-accumulated; preserve the returned CSV's grid and time labels and compare first with source-provenance and expected units. [CDS original catalog](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries).

[Stage05W original-response ZIP/CSV audit](../scripts/stage05/05w_JP_Yms_20050811_independent_CDS_zip_source_audit_NO_REPAIR.py) can be run **after** the single-day JP-Yms download. It is source-gated to the expected JP-Yms original BIF coordinate metadata, Stage05V list of eight pending days, Stage05R 87-variable-hour plan, the second raw CDS ZIP, and the known CDS CSV `valid_time` schema. It produces only derived raw reference previews and a source audit; no forcing corrections. It is committed but **not yet run against IRIDIS6 original files**. The returned ZIP SHA256 is unknown until the second CDS request has actually completed; never invent it.

## Independent evidence and remaining limitations

- Independent hourly ECMWF ERA5-Land is not the JPF release's within-product regression-downscaled `ERA5_HH`.
- The 2005-08-11 JP-Khw grid is ~33.1°N/130.7°E; the original BIF tower is 33.13658°N/130.70834°E at 196m. Grid terrain and representativeness remain to be checked.
- ERA5-Land `surface_pressure` is in Pa → kPa /1000, and `surface_thermal_radiation_downwards` is an hourly de-accumulated J m⁻² → W m⁻² /3600. The radiation value is **not** an observed instantaneous half-hour tower LW flux.
- All **45** original source-selected anomalies remain a science HOLD; **8 have strong independent contextual evidence**; 19 more time-verified fields require additional CDS days; 18 Tef/Tmd time-unresolved source fields require independent time provenance before any UTC comparison or repair. JP-Tom/JP-Tgf non-JPF RH/VPD work remains outstanding.

**Never change original JPF ZIPs, source meteorological variables, selected forcing or model cases; no Slurm or AD400 on evidence alone.**
