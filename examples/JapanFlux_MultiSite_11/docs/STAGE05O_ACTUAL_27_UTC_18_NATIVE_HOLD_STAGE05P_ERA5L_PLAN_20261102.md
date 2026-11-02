# JapanFlux Stage05O actual source-gated scope and Stage05P independent ERA5-Land plan (2026-11-02)

## Actual user-executed Stage05O

The operator ran the committed [Stage05O scoped UTC/source-HOLD splitter](../scripts/stage05/05o_scoped_3site_UTC_2site_solar_README_HOLD_NO_ZIP.py) on IRIDIS6 and supplied this terminal output:

```
STAGE05O SELF-TEST PASS | 3/2 time-provenance gate, UTC arithmetic, NO WRITES
STAGE05O SCOPED READ-ONLY PASS | NO ZIP / NO SLURM / NO REPAIR
LST_VERIFIED 3 /5 | UTC_LOOKUP 27 FIELDS / 21 SITE-HALFHOURS
SOLAR_README_CONFLICT 2 /5 | NATIVE_ONLY_HOLD 18 FIELDS / 14 SITE-HALFHOURS
UTC_TABLE /home/ly3n24/japanflux_stage05o/run_20261102T020608Z/stage05o_verified3_27_UTC_LOOKUP_HOLD.tsv
NATIVE_ONLY_HOLD /home/ly3n24/japanflux_stage05o/run_20261102T020608Z/stage05o_unresolved2_18_NATIVE_ONLY_HOLD.tsv
SUMMARY /home/ly3n24/japanflux_stage05o/run_20261102T020608Z/stage05o_scoped_timebase_summary.json
NO AUTOMATIC +9 MAPPING OF JP-Tef/JP-Tmd; NO SCIENTIFIC APPROVAL
```

**This establishes complete execution of Stage05O against the operator's source-backed Stage05I/05L/05N reports.** It is not evidence that any independent ECMWF data have been retrieved.

### Exact resulting scope

| Time provenance | Original JPF sites | Original candidate fields | Distinct site × native half-hours | UTC availability |
|---|---|---:|---:|---|
| Original README local **standard** time, no DST, original BIF UTC_OFFSET +9 | JP-Fjy, JP-Khw, JP-Yms | **27** | **21** | Original native time − 9h available as a derived lookup |
| Original README local **solar** time, no DST, though original BIF UTC_OFFSET also +9 | JP-Tef, JP-Tmd | **18** | **14** | **Unresolved**; never automatically subtract nine hours |
| **Total** | 5 | **45** | **35** | All still science HOLD |

The distribution of the **27** currently UTC-addressable variables by source site is JP-Fjy 6, JP-Khw 11, JP-Yms 10. JP-Tef 4 and JP-Tmd 14 remain native-clock-only. None of the 45 original QC=2 source-selected `F=ERA` anomalies have been numerically repaired. Original nested JPF ZIPs, selected forcing and model inputs remain unmodified.

Stage05N verified that the Tef/Tmd original 75-line README **line 64 explicitly says `local solar time (without DST)`**. This cannot be dismissed as an excerpt bug. FLUXNET/ONEFlux general standards favor local **standard** time, while source BIF has UTC_OFFSET=9; the conflict is unresolved for this particular release and should not be papered over. Previous [Stage05N evidence](STAGE05N_ACTUAL_SOLAR_VS_STANDARD_README_CONFLICT_STAGE05O_SCOPE_20261102.md).

## Next reproducible step: Stage05P independent-reference retrieval REQUEST PLAN ONLY

[Stage05P](../scripts/stage05/05p_prepare_3site_ERA5Land_hourly_UTC_reference_request_NO_CDS.py) is published to generate a purely derived **hourly UTC request plan** from the **three actual Stage05O outputs above**. It checks all source status, allowed sites, source-field counts, local-to-UTC +9 arithmetic, half-hour validity, source units, QC2 and unresolved two-site HOLD statuses. It makes **NO CDS API calls, no ZIP reads, no Slurm and no forcing writes**. Because **site latitude/longitude have not yet been independently pinned from the original BIF for retrieval**, the request plan leaves location as `REQUIRES_ORIGINAL_BIF_LAT_LON_NOT_GUESSED`. No actual extraction is claimed.

The plan requests three independent ECMWF ERA5-Land **hourly time-series** variables only where scientifically relevant, for UTC event hours and a configurable ±3-hour interval:

| JPF source | Independent ECMWF ERA5-Land hourly time-series variable | Original independent units | Comparison units |
|---|---|---|---|
| `TA_F` | `2m_temperature` | K | °C: K−273.15 |
| `PA_F` | `surface_pressure` | Pa | kPa: Pa/1000 |
| `LW_IN_F` | `surface_thermal_radiation_downwards` | Hourly de-accumulated J/m² | W/m²: J/m² / 3600 s after confirming interval/time labels |

Source docs:
- [CDS ERA5-Land hourly time-series selection, variable names and downloadable options](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries?tab=download).
- [ECMWF ERA5-Land hourly time-series product user guide](https://confluence.ecmwf.int/pages/viewpage.action?pageId=690470575).
- [CDS API setup and user licence agreement](https://cds.climate.copernicus.eu/how-to-api).

**Science cautions:** ECMWF ERA5-Land is hourly; JPF original source selections are half-hourly and may have been regression downscaled. Temporal alignment, land-grid elevation and site representativeness matter. ERA5-Land independently confirms source plausibility but is **not an automatically sanctioned replacement**. Radiation accumulation semantics must be checked before interpreting J/m² as an instantaneous W/m² value. These operations **must never mix with JP-Tef/Tmd source times** until the source 'local solar' vs 'local standard' issue is resolved.

### Next after Stage05P

Read authoritative source site location/height from original JPF BIF files for JP-Fjy, JP-Khw, JP-Yms (and preserve original metadata line and SHA). Then request a small, independent ECMWF ERA5-Land hourly station reference subset from CDS, using the **user's own accepted data terms and configured CDS API credentials**. Do not print or commit credentials. Compare and review the 27 source-selected values with unit conversion and ±3-hour context, then make a per-variable scientific recommendation rather than automatically replacing any values.

The 18 JP-Tef/Tmd field candidates remain on original native clock; a data-producer/ONEFlux clock convention check is the next separate requirement. JP-Tom/JP-Tgf original humidity/VPD source issues remain separate. **No approved AD400 / Normal400 or forcing changes.**
