# JapanFlux Stage05J actual JP-Khw native BIF metadata and Stage05K exact fields (2026-11-01)

## Operator-executed original release inspection

The operator executed the published `05j_original_JPF_BIF_README_metadata_source_QC_time_READONLY.py` on original **JP-Khw**, without Slurm, meteorological data row scans, or source modification. Output:

```
STAGE05J SELF-TEST PASS | metadata-only synthetic nested ZIP; no source reads
SITE: JP-Khw
STATUS: ORIGINAL_RELEASE_METADATA_READONLY_INSPECTED
METADATA FILES: 8
```

The script examined the published `JPF_JP-Khw_FLUXNET_BIFVARINFO_HH_2000-2021_v1.3_r1.csv` and other source metadata files. It extracted verbatim, source-line-numbered data snippets. Its source document's `VAR_INFO_DEFINITION` entries establish:

- `TA_F_QC`, line 34: **0 = measured; 1 = good quality gapfill; 2 = downscaled from ERA**.
- `SW_IN_F_QC`, line 64: same meanings.
- `LW_IN_F_QC`, line 90: same meanings.
- `VPD_F_QC`, line 142: same meanings.
- `PA_F_QC`, line 158: same meanings.
- `TA_F_MDS`, line 12: MDS gap-filled air temperature.
- `TA_ERA`, line 22: ERA-downscaled air temperature, linearly regressed using **measured only** site data.
- `LW_IN_ERA`, line 78: downscaled ERA longwave, linear regression with measured only site data; a separate `LW_IN_JSB`-based product also appears in source metadata (line 104).
- `VPD_ERA`, line 130: ERA downscaled linearly regressed with measured only site data.
- `VPD_F`, line 136: consolidated from `VPD_F_MDS` and `VPD_ERA`; MDS used when `VPD_F_MDS_QC` is **0 or 1**.
- `PA_ERA`, line 150: pressure downscaled from ERA and linearly regressed with measured only site data.

These **original JP-Khw product-specific** facts validate the original-provenance interpretation of `QC=2` for *this site*. Do not silently transfer the release's exact semantics to all other nine sites before at least cross-site BIF checks. All 45 Stage05I flagged variables have raw QC2 and numerically match embedded ERA, but **the original source's ERA companion is downscaled, not untouched ECMWF ERA5**. Comparisons between two CSVs within one archive are not independent validation of ECMWF data quality.

### Source unit and clock evidence currently incomplete

The operator's Stage05J terminal display filtered to 30 snippets and did not show actual source `VAR_INFO_UNIT` rows, `README` time statements, or UTC offset. The script reported `README.txt` and `DATA_POLICY_LICENSE_AND_INSTRUCTIONS.txt` readable, but `CONCEPTS` tags alone do **not** establish exact units or time conventions. Therefore **source-verified unit fields and exact local clock offset remain OPEN**.

External methodological context can guide verification, not substitute for site release metadata:

- FLUXNET2015 standard micrometeorological processing uses measured/high-quality MDS preferentially and ERA-downscaled values when MDS quality is insufficient. Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC7347557/
- FLUXNET source time convention is **local standard time without DST**, with UTC offset recorded in original site BADM; source https://fluxnet.org/data/aboutdata/data-variables/ . The analogous ICOS JPF-JP-Tmd product has a first acquisition timestamp in UTC 2004-12-31 15:00 corresponding to 2005-01-01 00:00 Japan local standard (https://meta.icos-cp.eu/objects/bnc9Cg8Jxf1opT9_Fq8boBvS). This is strong contextual support but **JP-Khw's exact offset must be audited or explicitly pinned from authoritative metadata before forcing UTC transforms**.

### Why this matters scientifically

On 2005-08-12, the selected JP-Khw `TA_F_MDS` near the catastrophic `TA_ERA` failure was approximately **1.1°C**, while neighboring non-catastrophic ERA-downscaled air temperature was **~23–24°C**. The source metadata confirm which algorithm produced the MDS and ERA values but **do not make MDS a trustworthy automatic repair**. Retain the Stage05I 45-field, 35 station×time **HOLD** pending independent reference and per-variable QC.

## Stage05K next source evidence gate

[Stage05K exact BIF variable/unit/time metadata extractor](../scripts/stage05/05k_JPF_exact_BIFVARINFO_units_QC_time_excerpts_READONLY.py) is committed, **not yet executed on real IRIDIS JPF releases**. It reads one original nested ZIP at a time, inspects the **full small source BIFVARINFO_HH CSV** in grouped rows rather than limiting to high-ranked snippets, retaining direct original `VAR_INFO_UNIT`, `VAR_INFO_DEFINITION`, `VAR_INFO_VARNAME` and other fields when present. It also prints original BIF and README time/offset clues, if present, with source line references and SHA-256 document hashes. **No meteorological source rows read, no Slurm, no model or repaired forcing writes**. Pilot JP-Khw, confirm document fields and actual time evidence before expanding to other JPF stations.

### Science status

Stage05J: source BIF QC provenance for JP-Khw **CONFIRMED**. Stage05I: all 45 selected-F anomalous field rows remain **unapproved HOLD**, and no forcing / AD400 / Normal400 is scientifically authorized. Original JP-Tom/JP-Tgf RH/VPD provenance remains a separate pending review.
