# Eight-site QC, human decisions, and DATM audit (2026-10-12)

This page records **candidate** forcing decisions, not certification of every tower observation. The pipeline mirrors `../FLUXNET_MultiSite_6/`, preserving `raw/`, network provenance, QC v5 replacement logs, and dated BIF `TA_F` measurement heights.

## QC v5

| Site | Automated status | Changed site-variable records | Original review entries | Additional QC=0 changes |
| --- | --- | ---: | ---: | ---: |
| CZ-BK1 | REVIEW | 9 | 2 | 0 |
| IT-Ren | REVIEW | 121 | 8 | 0 |
| FR-Hes | REVIEW | 19 | 4 | 0 |
| FR-FBn | PASS | 0 | 0 | 0 |
| DE-Hzd | PASS | 0 | 0 | 0 |
| CH-Dav | PASS | 0 | 0 | 0 |
| BE-Vie | PASS | 6 | 0 | 0 |
| IT-Lav | PASS | 1 | 0 | 1 |

There are 14 original v5 review entries plus one additional review of an altered official-QC=0 measurement: **15 tracked event entries**. Reviewed entries can remain marked `REVIEW`; no automation should re-label them `PASS` merely because a human inspected them.

### Human decisions

- **IT-Lav 2003-03-11 11:00, LW_IN_F:** measured 474.507 W m^-2, anomalous relative to 10:30=277.889 and 11:30=265.957; correction 271.923 is their interpolation midpoint and ERA longwave was 255.362. User accepted the isolated-spike correction. Preserve provenance of QC=0 alteration.
- **CZ-BK1 2013-04-22 14:30 and 15:00:** `TA_F_QC=0` measured TA disagreed with `VPD_F_QC=2` ERA-sourced VPD, giving slightly negative implied humidity. Retain QC v5, preserve original TA. The 15:00 reconstructed RH is 0.355% (very low but positive), not independent ERA validation; user elected to retain and flag review.
- **IT-Ren eight and FR-Hes three early-period low-RH items:** original near-zero/impossible implied humidity in `VPD_F_QC=1` gap-filled data; retain QC v5 ERA-humidity candidate corrections, with provenance and review designation. Matching reconstructed RH to ERA is not independent measurement verification.
- **FR-Hes 2022-07-03 17:00, 18:00, 18:30:** three anomalously cold gap-filled `TA_F_QC=1` observations embedded in warmer ERA-derived intervals. User adopted paired `TA_ERA` and `VPD_ERA` at all three times, recalculating `TA_USE`, `VPD_USE`, `TBOT`, `QBOT`. Original QC v5 is retained under `processed_v5`; revised FR-Hes forcing under `processed_v5_manual_v1`, with ledger and checksums. The file `scripts/09_FRHes_manual_v1_rebuild_eight_datm.py` implements this versioned change; the DATM creation script is patched at runtime to read the revised FR-Hes forcing.
- **DE-Hzd precipitation:** the user elected to retain the officially provided `P_F`, despite 100% official ERA provenance and 2010–2025 annual sums around 2,134–4,136 mm, which are unusually high for the region. Not independently validated; potential hydrological sensitivity must be considered. Structural validation does not resolve this scientific issue.

## Dated BIF heights, DATM files

| Site | Dates in forcing | TA_F ZBOT history (m) | Annual files |
| --- | --- | --- | ---: |
| CZ-BK1 | 2004–2025 | 12 -> 17 -> 25 | 22 |
| IT-Ren | 1999–2025 | 15 -> 33.7 | 27 |
| FR-Hes | 1997–2025 | 17 -> 22 -> 35 -> 31.85 | 29 |
| FR-FBn | 2008–2024 | 16.2 -> 16.8 -> 16.9 | 17 |
| DE-Hzd | 2010–2025 | 5 -> 11 -> 16.75 | 16 |
| CH-Dav | 1997–2025 | 35 | 29 |
| BE-Vie | 1996–2025 | 21 -> 50 -> 50.8 -> 51.2 -> 51 | 30 |
| IT-Lav | 2003–2020 | 42 | 18 |

All **188/188** candidate annual DATM files passed independent structural verification (17,520 half-hour records/year, `NO_LEAP`), and the separate stage-06 DATM/surface audit also returned **188/188** with **STRUCTURE_OK_REVIEW** for all eight stations.

## Scientific caveats before production spin-up

- ERA-source proportions can be high, including DE-Hzd `PA_F` and `P_F` = 100%; keep source information, not just numeric QC pass/fail.
- The BIF `TA_F` heights are used for time-dependent `ZBOT`. Some early portions are extrapolated from the earliest height metadata; `WS_F` instrument height differs from TA by more than 3 m for long periods at several sites. WIND is not vertically normalized.
- CTSM gridded surface natural-PFT and crop percentages are not an independently verified representation of a flux-tower footprint or the FATES plant-functional-type parameterization. Gridded crop fractions reach 37.3% at DE-Hzd; many stations have substantial natural-landunit grass fractions.
- **No model spin-up is claimed for these eight stations.** The repository currently documents transfer, QC, provisional DATM creation and structural/surface audit.
