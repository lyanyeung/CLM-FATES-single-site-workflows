# JapanFlux Stage05K — actual JP-Khw original time-zone, units and source-QC evidence (2026-11-01)

## Original operator evidence

Operator ran [Stage05K](../scripts/stage05/05k_JPF_exact_BIFVARINFO_units_QC_time_excerpts_READONLY.py) against the original **JP-Khw** JPF nested ZIP and obtained:

```
STAGE05K SELF-TEST PASS | BIF group-unit-QC-time evidence parsing, NO SOURCE WRITES
SITE: JP-Khw
STATUS: READONLY_BIF_VARIABLE_AND_TIME_METADATA_EXTRACTED
```

Source files:

- `JPF_JP-Khw_FLUXNET_BIFVARINFO_HH_2000-2021_v1.3_r1.csv`: per-variable definitions and exact units.
- `JPF_JP-Khw_FLUXNET_BIF_2000-2021_v1.3_r1.csv`, original line 64: `JP-Khw,3365,GRP_UTC_OFFSET,UTC_OFFSET,9`.
- `README.txt`, original line 69: `time is expressed in local standard time (without DST)`.

These are **original release specific** source records, not general web-derived assertions. With the observed offset, **JP-Khw native half-hour timestamps = JST/UTC+09:00**, hence `UTC = original native time − 9h`; do not relabel original rows. For any other station, obtain its own BIF `UTC_OFFSET` and README evidence before applying the same conversion.

### Verified original variables (JP-Khw only)

| Variable | Original BIFVARINFO_HH unit | Original provenance / consolidation |
|---|---|---|
| `TA_F` | `deg C` | Consolidated from MDS and linearly regressed downscaled `TA_ERA`; `TA_F_MDS` used when MDS QC 0 or 1 |
| `TA_ERA` | `deg C` | Downscaled from ERA, linearly regressed using measured-only site data |
| `PA_F` | `kPa` | Consolidated from measured `PA` and `PA_ERA`; `PA` if measured |
| `PA_ERA` | `kPa` | Downscaled from ERA, linearly regressed using measured-only site data |
| `LW_IN_F` | `W m-2` | Consolidated from MDS and `LW_IN_ERA`; MDS selected when its QC 0 or 1 |
| `LW_IN_ERA` | `W m-2` | Downscaled from ERA, linearly regressed using measured-only site data |
| `VPD_F` | `hPa` | Consolidated from MDS and ERA; `VPD_F_MDS` when QC 0 or 1 |
| `TA_F_QC`, `PA_F_QC`, `LW_IN_F_QC`, `VPD_F_QC` | `adimensional` | `0 = measured; 1 = good quality gapfill; 2 = downscaled from ERA` |

The same source metadata includes definitions for `SW_IN_F_QC` and `PA_F_QC` with identical QC semantics. The reader's time offset and unit parser produced exact field values rather than inference from the physical size of the anomaly.

### Exact conversion examples, JP-Khw only

| Original JP-Khw time (UTC+9; no DST) | UTC |
|---|---|
| 2005-08-12 02:30 | 2005-08-11 17:30 |
| 2005-08-12 03:00 | 2005-08-11 18:00 |
| 2011-12-17 07:00 | 2011-12-16 22:00 |

**Caution:** `ERA5_HH` in the release is **processed/downscaled**; comparing it with the other `FLUXMET_HH` archive table is a same-release check, not an independent ECMWF ERA5/ERA5-Land validation. Even correctly aligned UTC and units do not establish a scientifically sound replacement for the 45 source-impact field rows.

## Audit status

- Stage05I derived source-impact HOLD: **45 variable rows**, **35 site×native-half-hours**, all unapproved.
- Stage05K: **JP-Khw original source units and UTC-offset verified**, no other JPF site verified by this operator printout.
- Next: run the **same Stage05K** for `JP-Fjy, JP-Tef, JP-Tmd, JP-Yms` sequentially without Slurm; confirm each source's units, QC mappings, UTC offset and README. A separate JSON-only cross-site report can be generated once all five metadata JSONs exist, then join with the existing 45-record Stage05I TSV to derive UTC lookup timestamps (not replacement values).
- Original source ZIPs, user FLUXMET products, model forcing and cases remain untouched. No AD400 or Normal400.

The two different JapanFLUX2024 products, JP-Tom and JP-Tgf, still need independent humidity/VPD source investigation and should **not** be treated as JPF-with-UTC-offset-9 solely by analogy.
