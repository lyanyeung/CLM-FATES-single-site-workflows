# JapanFlux Stage05A — actual science forensic findings and Stage05B design (2026-11-01)

**Input:** operator's `$HOME/japanflux_stage04/stage05a_event_samples.txt`, generated successfully by [Stage05A](../scripts/stage05/05a_summarize_existing_stage04_QC_NO_ZIP_NO_SLURM.py) from the completed **11-site** Stage04 JSON. This is **no new ZIP scan**, **no Slurm**, and **no edits**. Event times below are in the native CSV timestamp convention; **UTC/JST not independently established**. Original source QC labels are preserved literally and **not semantically classified**.

## Major new finding: precisely time-coincident anomalies among distinct JPF sites

The same native timestamps recur at multiple geographic towers, with `QC_RAW=2` for most examined abnormal values. This creates a testable **common-input/common-processing hypothesis**, not evidence of independent physical extremes at the tower locations.

| Native start → end | Site | Exact flagged `*_F` values | Original QC text |
|---|---|---|---|
| 2005-08-12 02:30→03:00 | JP-Khw | TA −122.144 °C, PA 48.912 kPa | 2, 2 |
| 2005-08-12 03:00→03:30 | JP-Khw | TA −268.276 °C, PA 0 kPa | 2, 2 |
| 2005-08-12 03:30→04:00 | JP-Khw | TA −122.665 °C, PA 48.922 kPa | 2, 2 |
| 2005-08-12 02:30→03:00 | JP-Tmd | TA −132.399 °C, PA 49.502 kPa | 2, 2 |
| 2005-08-12 03:00→03:30 | JP-Tmd | TA −284.222 °C, PA 0 kPa | 2, 2 |
| 2005-08-12 03:30→04:00 | JP-Tmd | TA −132.688 °C, PA 49.506 kPa | 2, 2 |
| 2005-08-12 03:00→03:30 | JP-Fjy | PA 0.334 kPa | 2 |
| 2005-08-12 03:00→03:30 | JP-Yms | PA 37.349 kPa | 2 |
| 2005-08-12 02:00→03:00 | JP-Khw | LW 39.171 W m−2 at 02:00 and 02:30 | 2 |
| 2005-08-12 02:00→03:00 | JP-Tmd | LW 28.519 W m−2 at 02:00 and 02:30 | 2 |
| 2005-08-12 02:00→03:00 | JP-Yms | LW 44.79 W m−2 at 02:00 and 02:30 | 2 |
| 2011-12-17 06:00→07:30 | JP-Khw, JP-Tmd, JP-Fjy, JP-Yms, JP-Tef | Low PA or LW values at same/adjacent steps | 2 |
| 2022-04-09 02:00→03:00 | JP-Tef | LW 26.164 W m−2 twice (same as its 2011-12-17 LW minimum) | 2 |

**Check exactly what the original FLUXMET_HH input says:** `*_F`, `*_F_QC`, `*_F_MDS`, `*_F_MDS_QC` and `*_ERA` on the same half-hours; test common-source processing independently of the original QC code definition. Keep anomalous original observations intact. Do not automatically substitute ERA5 and do not call QC=2 “ERA” without source metadata evidence.

## Distinct JapanFLUX2024 humidity problem

**JP-Tom `COREVARS_HH` (2003–2013):** `RH_F>100`: 6,583 half-hours, `VPD_F<0`: 7,336 half-hours. First recorded RH examples include 2013-01-02 19:00 (104%) and 2013-01-03 00:00 (103%), `RH_F_QC=0`. Its first listed negative-VPD candidates are numerical round-off `-3.55e-15`, `-1.78e-15` hPa, also `QC=0`. But `VPD_F` minimum is **−2.91356 hPa**, so significant events must be distinguished from tiny floating-point negatives, and RH/VPD must be joined by exact native timestamp rather than counts added together. `P_F<0`: 4322, all as small as at most about −2.00e−15 (rounding candidate).

**JP-Tgf `COREVARS_HH` (2002–2022):** `RH_F>100`: 9,493; `VPD_F<0`: 9,514; early matched RH/VPD examples on 2002-05-23 23:00→23:30 have RH=101.098574...%, VPD=−0.210743... hPa and `QC=1`. The minimum VPD is −4.979288... hPa. One `PA_F=0` kPa occurs 2003-12-31 23:30→2004-01-01 00:00 (`QC=0`); one `SW_IN_F=−70.11575` W m−2 occurs 2015-12-15 14:30→15:00 (`QC=0`). `P_F<0` occurs at only 3 steps, minimum −1.31894e−15 (rounding candidate).

**Critical caution:** Stage05A event samples are capped at **12 flagged rows/variable from Stage04**, with four printed per flag in the operator output. They are not complete anomaly event lists. Stage04 `raw_QC_counts` do not establish physical truth or tower provenance; audit native ALLVARS and metadata before source decisions. To de-duplicate apparent humidity anomalies, classify `VPD_F < -1e-9` versus small roundoff and count its intersection with `RH_F>100`.

## JP-Tom HR/HH native chronology resolved at source-file boundaries

- Hourly `COREVARS_HR`: first `199901010000–199901010100`; last `200212312300–200301010000`.
- Half-hourly `COREVARS_HH`: first `200301010000–200301010030`; last `201312312330–201401010000`.
- These **two file-boundary intervals abut exactly without overlap or gap** in native timestamps. This is not proof of local-time-to-UTC mapping or full science-usable coverage; Stage04 found no intra-file time-axis issues.
- JP-Tgf source last interval `202212312330–202301010000`; filename `2002–2023` includes an ending boundary rather than 2023 measured starts.

## Stage05B — one-site-at-a-time no-Slurm forensic

[Stage05B raw JPF source/ERA/QC comparison](../scripts/stage05/05b_JPF_shared_timestamp_source_ERA_QC_READONLY.py) consumes the **existing full Stage04 JSON** to collect all its stored time-stamped JPF flagged samples from 5 stations. It then examines small **native-time windows ±60 min around their union** from `FLUXMET_HH`, printing the exact `TA_F`, `TA_F_MDS`, `TA_ERA`, `PA_F`, `PA_ERA`, `LW_IN_F`, `LW_IN_ERA` and available `*_QC` columns. It reads one double ZIP in bounded RAM per call, leaves sources unmodified, and **does not use Slurm**. This first forensic pass compares **same-file era-derived columns**, not a separately validated original ERA5_HH join; further independent source checks may follow if needed.

No stage05B IRIDIS execution has yet been reported. No corrected forcing or model case exists from these analyses.
