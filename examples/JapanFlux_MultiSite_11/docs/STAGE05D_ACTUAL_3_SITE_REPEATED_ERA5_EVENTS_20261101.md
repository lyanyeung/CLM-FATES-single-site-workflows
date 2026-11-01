# JapanFlux Stage05D — actual 3-site full-period ERA5_HH screens (2026-11-01)

## Actual IRIDIS6 execution evidence (operator terminal)

The operator executed the [Stage05D source-only ERA5 scanner](../scripts/stage05/05d_scan_separate_ERA5_HH_all_years_READONLY.py) independently for **JP-Fjy, JP-Yms, and JP-Tef**. Each returned `ERA5_FULL_SCAN_COMPLETED`. These are **separate `ERA5_HH` CSVs from the same JPF published release**, not independently retrieved ECMWF ERA5. All event times below remain **native package timestamps**, whose UTC/JST interpretation is not established. No original files were changed, and no Slurm was used for these invocations.

| Site | Processed ERA5_HH rows | Unique half-hour time points flagged by Stage05D | TA_ERA < −70°C | PA_ERA < 50 kPa | LW_IN_ERA < 50 W/m² | Min TA_ERA | Min PA_ERA | Min LW_IN_ERA |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| JP-Fjy | 788,928 | 20 | 15 | 15 | 10 | −250.414°C | 0.334 kPa | 17.955 W/m² |
| JP-Yms | 788,928 | 20 | 15 | 5 | 10 | −252.855°C | 37.349 kPa | 44.79 W/m² |
| JP-Tef | 771,408 | 20 | 15 | 5 | 10 | −268.366°C | 21.669 kPa | 26.164 W/m² |

For **each of the three stations**, the years flagged by the full Stage05D scan are **1990, 1999, 2005, 2011 and 2022**. Each of these years has exactly **3 TA_ERA rows below −70°C** and **2 LW_IN_ERA rows below 50 W/m²**; Fjy has 3 low-PA half-hours per such year, whereas Yms and Tef have only 1 low-PA half-hour per year under the same fixed threshold. The difference in PA counts reflects the numerical screening cutoff, not evidence that neighbor values are valid pressure.

The exact repetition across **multiple JPF stations and the same five calendar years**, plus the previously established Stage05B interpolation over 2005-08-12 and Stage05C same-release ERA5_HH/FLUXMET equality for Khw/Tmd, strongly supports a **shared nonphysical source-value / sentinel / processing hypothesis**. It does **not** establish the precise upstream root cause, nor establish that independently downloaded raw ECMWF ERA5 has the same problem.

### Scientific boundaries

- Stage05D scans **only** published standalone ERA5_HH sources; it does not prove which of these values contaminate the final selected FLUXMET `*_F` forcing at every site/timestamp. Contamination depends on original tower observations, QC labels and fallback source selection.
- `UNIQUE_FLAGGED_TIMES: 20` represents the unique half-hour start timestamps where at least one of Stage05D's **specific screen thresholds** fired. It is not a complete meteorological anomaly count or a number of tower errors.
- Stage05D printed `YEAR` counts but the supplied terminal output did not print all **exact timestamps** for 1990, 1999 and 2022. The existing JSONs store the first 12 samples per field and watched `20050812`, `20111217`, `20220409` date rows; do not invent exact dates for other years.
- Long-term pre-observation and post-observation years of ERA5_HH are included in the companion ERA product; this differs from native tower-observed coverage and will need explicit forcing policy.
- No ERA5 reconstruction, `_F` replacement, source rewriting, or AD400/Normal400 authorization has occurred.

### Next action — complete all nine JPF sites, still no Slurm

The site selection to finish with the same Stage05D full-period screen is **JP-Api, JP-Fhk, JP-Khw, JP-Spp, JP-Tak, JP-Tmd**. The operator already screened Fjy/Yms/Tef. Run **one site per process serially**, with `nice -n 10` and one output JSON per station. This may involve considerable local decompression, so do not parallelize on the IRIDIS login node.

Use [Stage05E JSON-only summary](../scripts/stage05/05e_summarize_ERA5_audits_from_JSON_NO_ZIP_NO_SLURM.py) to compare the completed 3-to-9 site reports **without reopening any ZIP**, including year-by-year anomaly counts and available sampled timestamps. The script is committed but **not yet executed** by the operator.

After all nine reports, identify the common event dates and actual source provenance, distinguish which `*_F` values are affected and which tower `QC0` observations are protected; independently validate external ERA5/ERA5-Land data when deciding repairs. **Do not auto-repair from within the contaminated JPF ERA5 product.** The separate humidity issues at JP-Tom and JP-Tgf remain under review.
