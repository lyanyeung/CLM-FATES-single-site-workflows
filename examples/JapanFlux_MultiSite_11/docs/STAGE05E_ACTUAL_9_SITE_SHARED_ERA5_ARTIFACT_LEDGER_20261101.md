# JapanFlux Stage05E — actual final 9/9 JPF ERA5 source audit (2026-11-01)

## Verified operator output and recovery

The operator supplied the original Stage05E `STATIONS_LOADED 9 /9` aggregated terminal transcript (251 lines), after verifying that eight Stage05D station JSON files were valid and `JP-Api` was initially a **0-byte JSON**. `JP-Api` was subsequently rerun successfully before this nine-station aggregation. The final transcript explicitly confirms `JP-Api` has 788,928 ERA5_HH source rows, 0 Stage05D flagged intervals, no time errors, and all other JPF source audit reports loaded. There is **no evidence from these results that original ZIPs were damaged**, and no further Slurm usage was required.

**Coverage:** 7 sites have 788,928 ERA5_HH half-hourly source rows (1981–2025); JP-Tef and JP-Tmd each have 771,408 (1981–2024). The Stage05E source text displayed every station's first and last native interval and `TIME_ERRORS {}`. This constitutes per-file temporal screens only, not verification of time-zone, independent ERA, tower data or model forcing.

## Full actual all-year source flag inventory

| Site | Unique flagged half-hours | TA_ERA <−70°C | PA_ERA <50 kPa | LW_IN_ERA <50 W m⁻² | Central repeated TA_ERA (°C) | Central repeated PA_ERA (kPa) | Repeated flagged LW_IN_ERA (W m⁻²) |
|---|---:|---:|---:|---:|---:|---:|---:|
| JP-Api | 0 | 0 | 0 | 0 | — | — | — |
| JP-Fhk | 20 | 15 | 5 | 10 | −253.584 | 21.235 | −10.52 |
| JP-Fjy | 20 | 15 | 15 | 10 | −250.414 | 0.334 | 17.955 |
| JP-Khw | 20 | 15 | 15 | 10 | −268.276 | 0 | 39.171 |
| JP-Spp | 15 | 15 | 5 | 0 | −260.605 | 20.771 | no value below the specified 50 W m⁻² cutoff |
| JP-Tak | 15 | 15 | 5 | 0 | −244.555 | 25.204 | no value below the specified 50 W m⁻² cutoff |
| JP-Tef | 20 | 15 | 5 | 10 | −268.366 | 21.669 | 26.164 |
| JP-Tmd | 20 | 15 | 13 | 10 | −284.222 | 0 | 28.519 |
| JP-Yms | 20 | 15 | 5 | 10 | −252.855 | 37.349 | 44.79 |
| **Total** | **150** | **120** | **68** | **60** | | | |

**Count semantics:** 150 is the total number of station×half-hour starts where at least one Stage05D threshold fired, **not** 150 unique cross-station times, and 120+68+60=248 is the number of variable-specific trigger occurrences with overlaps. `JP-Api` is negative under the limited thresholds, **not scientifically proven error-free**. `JP-Spp` and `JP-Tak` have no flagged LW values under this numerical cutoff, **not proof their LW sources are clean**. These diagnostics are within the same distributed JPF release; they are not independent ECMWF ERA5 data.

## Five exact repeated event dates (native archive time; timezone not verified)

For **each of the eight flagged sites**, the exact same source-date pattern occurs:

1. **1990-04-03**: `LW_IN_ERA` at 02:00/02:30 where flagged; `TA_ERA` at 02:30/03:00/03:30; central low `PA_ERA` at 03:00.
2. **1999-01-19**: same native-clock 02:00/02:30 LW, 02:30/03:00/03:30 TA, central 03:00 PA pattern.
3. **2005-08-12**: same native-clock event structure.
4. **2011-12-17**: native-clock `LW_IN_ERA` at **06:00/06:30**, `TA_ERA` at **06:30/07:00/07:30**, `PA_ERA` at central **07:00**.
5. **2022-04-09**: same native-clock 02:00/02:30 LW, 02:30/03:00/03:30 TA, central 03:00 PA.

Some sites' PA interpolation neighbors (02:30 and 03:30 or 06:30 and 07:30) also cross the arbitrary <50 kPa threshold, while other sites' values remain above 50 despite still being **approximately half normal pressure**; this is an explicit example of **why a threshold screen is only a partial detector**.

The **same numerical central temperature** repeats at all five dates **within each site**, even though adjacent valid weather differs. The same abnormal PA and flagged LW numeric values also repeat by site. Combined with Stage05B/C evidence that the selected `*_F` of some sites equals the embedded `*_ERA` and the separate `ERA5_HH` during fallback intervals, the evidence strongly supports a **common shared processing, sentinel or missing-value propagation issue** in the JPF ERA5-derived release chain. The true upstream root cause has not been independently established.

**Science implication:** these five dates are not all within native tower `FLUXMET_HH` years. Some 1990, 1999 and 2022 events will exist only in the companion ERA5 product and cannot have contaminated selected fluxmet forcing for sites without tower-era records. Conversely, measured tower `TA_F_QC=0` and `LW_IN_F_QC=0` sometimes shield corrupted ERA5 values while `PA_F_QC=2` remains susceptible. Avoid blanket date-based ERA substitution and avoid treating MDS as automatically reliable (e.g. suspicious ~1°C Khw MDS in August 2005). Do not overwrite original ZIPs.

## Next stage — targeted `*_F` source impacts, no Slurm

[Stage05F targeted source impact forensic](../scripts/stage05/05f_source_event_selected_forcing_impact_READONLY.py) consumes the completed **single-site Stage05D JSON** to recover the exact stored source ERA anomaly timestamps. It **requires saved event samples to cover all per-site flagged starts**, failing closed if sample coverage is inadequate. It opens **only one site's native FLUXMET_HH** at a time and extracts selected `*_F`, raw `*_F_QC`, `*_F_MDS` and embedded `*_ERA` values within ±30 minutes of exact suspicious timestamps, distinguishes source-ERA-only vs selected-F physical flags, and counts event-flag QC labels. This is **read-only and no Slurm**, and will not produce a repaired forcing candidate.

The first Stage05F source script is **committed to GitHub but has not been executed on IRIDIS6**, and must be syntax-tested and piloted by the operator before the full eight-site pass.

Then independently verify the external ERA5 source or ERA5-Land at exact anomalous timestamps and distinguish model forcing contamination from same-release raw ERA5 corruption. JP-Tom and JP-Tgf humidity/RH/VPD forensic remains **independent and pending**. No AD400 science authorization.
