# Batch05 Stage57 — US-Wjs 2018-03-11/12 30 original source-native HH science HOLD

## Confirmed previous step

Actual user IRIDIS6 Stage56 result (28 October 2026): two US-UMB 2009 and six US-Wjs 2021 RH interpolation candidates succeeded; Stage24 166-row overlay source and original SHA verified; combined **versioned 174-row** overlay written and all ten new local boundaries had zero jumps above 2 hPa. The original 2018 US-Wjs 30-HH source HOLD was preserved; no original AmeriFlux source, existing 166, DATM/CIME or Slurm changes.

Stage56 output:
`/home/ly3n24/ameriflux_batch05_stage56/eight_user_approved_interpolations_20261028T193428Z_4078597`.

## Why Stage57 targets a fresh March 2018 reference

The Stage33 ten actual downloads included one US-Wjs original high-risk event pilot, but it is NOT established that the March 2018 E0079 30-HH humidity problem was included. Do not infer this coverage from the existing nine matched Wjs pilot half-hours. US-Wjs March 2018 has original observed-source QC0 RH 100% at native 2018-03-11 19:00 and RH 92.127% at 2018-03-12 10:30. Native original VPD QC1 from 19:30 to 10:00 has RH missing and includes sustained 5.3 hPa then invalid negative-derived RH, so a naive 15h linear RH interpolation is unapproved.

Stage57 requests **one** point timeseries `reanalysis-era5-land-timeseries` at the Stage33 verified Wjs coordinates 34.4258° N, -105.8617° E (longitude −105.8617°), dates UTC `2018-03-11/2018-03-13`, hourly `2m_temperature` and `2m_dewpoint_temperature`, format NetCDF. Original source half-hour local-standard time → UTC uses the Stage29 BIF offset **−7 hours**, with missing BIF UTC_OFFSET_DATE_END, explicitly provisional and without DST shifts.

The script SHA-validates Stage56 174, Stage53 original events, Stage52 source inventory, independently validates the original Wjs raw FLUXMET source SHA and exact 30 QC1 missing RH half hours. Imports the existing Stage31 proven ZIP/NetCDF T/Td interpreter using its immutable SHA. If requested, downloads one genuine dataset to a newly named research folder and produces exact 34-HH (30 HOLD + 2 QC0 anchors + 2 extra outside) tables of original tower T/VPD/RH versus source processed ERA RH and actual downloaded ERA5-Land RH, two distinct moisture-to-tower-T VPD transfer hypotheses, T bias and clock alignment. It **never** approves new science repairs or modifies official input data.

GitHub:
- [Stage57 source](../scripts/stage57/57_Wjs_2018_30HH_targeted_CDS_ERA5Land_reference.py) at commit `e7fad3d234dd988140adb7dc1c0fbe96146e5cd6` (blob `bbcee36196150aa4df5c288257f1fb01aaf3c7c5`).
- [Stage57 launcher](../scripts/stage57/run_stage57_iridis6.sh) at commit `120e8c829d87a21431a5db33fba2f7e7d7eefdc5`; launcher hash is verified by fetching its GitHub file.

Expected outputs: `stage57_34_NATIVE_HH_TOWER_VS_REAL_ERA5L_30HH_HOLD.csv`, `STAGE57_WJS_2018_REAL_ERA5LAND_TOWER_COMPARISON.md`, and `stage57_manifest.json` alongside original CDS payload. Operator execution is required; no actual March 2018 ERA5-Land values are asserted by this document.

## Stage57 operator compile/self-test PASS then parser-hash failure (28 October 2026)

Actual operator log:
```
STAGE57 TWO SOURCE SCRIPTS SHA VERIFIED
STAGE57 SELF-TEST PASS | 30 exact held HH and four original neighbor HH, -7h provisional UTC, no forcing writes
ValueError: Stage31 original NetCDF interpreter SHA drift
```

**Root cause: code-only integrity comparison mismatch.** The Stage57 launcher successfully verified `git hash-object` of the exact Stage31 parser against `a28bde14dadcaf87abaaa2d52f2eaa785e16c89f` (Git blob SHA-1). The Stage57 Python then erroneously compared `hashlib.sha256(file)` (raw-file SHA256) against that 40-character SHA-1. This was guaranteed to fail regardless of file correctness. It happened **before any CDS download and before the new output directory was created**. It was not a data-quality failure.

Fixed Stage57 source: commit `75c558020ec650f1eeeeca8ba72c156c5eb8c2f3`, Git blob `1f1d747277109853448d33f21127de985f268a23`. It now computes actual Git blob SHA-1 (prefix `blob <byte-size>\0` + file bytes) against the original pinned Git blob, and independently records raw-file SHA256 in the manifest. No meteorological logic or source scientific approvals changed.

Fixed Stage57 launcher: commit `cfd20d17563c01709c254ec8026361bd261b4080`, blob `fe841e658a21145daeed2c0cfc79e27cee2e1a88`. Use the corrected one-line command:

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/cfd20d17563c01709c254ec8026361bd261b4080/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage57/run_stage57_iridis6.sh" -o "$HOME/run_stage57.sh" && test "$(git hash-object "$HOME/run_stage57.sh")" = "fe841e658a21145daeed2c0cfc79e27cee2e1a88" && bash "$HOME/run_stage57.sh"
```

Status of corrected version: GitHub source and pinned blob checks verified by the assistant. **IRIDIS6 actual corrected execution and real March 2018 CDS retrieval pending**. Previously approved Stage56 174-row overlay and 2018 30-HH HOLD remain unchanged.

## Confirmed actual IRIDIS6 Stage57 execution (2026-10-28 19:51 UTC)

```
STAGE57 TWO SOURCE SCRIPTS SHA VERIFIED
STAGE57 SELF-TEST PASS
STAGE57 SOURCE PASS | Stage56 original 174 approved rows SHA checked, US-Wjs 2018 30-HH HOLD unchanged
CDS request 43503174-f95c-4c30-b634-9a2833950c4c: successful
STAGE57 SUCCESS | 34 original HH, 30 Wjs-2018 HOLD, 2 QC0 anchors; 1 actual CDS ERA5-Land download
```

Actual result:
`/home/ly3n24/ameriflux_batch05_stage57/wjs2018_actual_ERA5Land_20261028T195055Z_4119241`.

| Native source timestamp | Original tower VPD hPa | Tower RH % | source ERA RH (derived) % | independent-downloaded ERA5-Land RH % | ERA5-Land RH to tower temperature VPD hPa |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2018-03-11 19:00 (QC0) | 0 | 100 | 73.528964 | 66.762685 | 2.02307736 |
| 2018-03-11 19:30 (QC1) | 5.398 | missing | 76.288720 | 68.078134 | 1.89501702 |
| 2018-03-12 06:00 (QC1) | 5.322 | missing | 86.577430 | 79.748184 | 1.21339554 |
| 2018-03-12 09:00 (QC1) | 7.709 | missing | 79.887949 | 67.135164 | 2.08517419 |
| 2018-03-12 10:00 (QC1) | 8.069 | missing | 75.890788 | 61.273691 | 3.01646413 |
| 2018-03-12 10:30 (QC0) | 0.672 | 92.127 | 72.618856 | 58.221250 | 3.56227871 |

At the two verified tower RH QC0 anchors, ERA5-Land grid RH is **33.237315 and 33.905750 percentage points lower** than original source tower RH, respectively; source processed ERA RH is also much lower. Direct ERA5-Land RH at original tower TA yields VPD 2.023 hPa at the left anchor versus original measured 0 hPa, and 3.562 hPa at the right anchor versus original measured 0.672 hPa. These are substantive boundary and tower/grid-representativeness disagreements; blindly assigning grid RH to original tower T is NOT science-approved.

Only the grid ERA5-Land data are freshly downloaded; the AmeriFlux products' `TA_ERA` and `VPD_ERA` remain processed reanalysis companion data. Gridded observations are not independent in-situ tower humidity measurements.

**Stage57 user-verified PASS; 30-HH 2018 science HOLD unchanged.** Next Stage58 is a reproducible side-by-side *read-only comparison*, not an automated approval.
