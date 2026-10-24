# Batch04 Stage04 operator verification and Stage05 QCv5 candidate repair policy

**Date:** 2026-10-24. **Evidence:** user-uploaded Stage04 terminal log; Stage04 self-test PASS, all three priority sites examined, `STAGE04 SUMMARY: examined=3/3 failed=none`. All original FLUXMET and packaged ERA5 releases unchanged.

## Stage04 scientific findings

1. **US-SP1, 2016-10-09 19:30/20:00/20:30:** `TA_F=-109.923/-243.686/-111.323 °C`, `TA_F_QC=2`, exactly equal to `TA_ERA`; `PA_F=51.184/1.499/51.258 kPa` also equals abnormal `PA_ERA`. Neighbouring tower QA values: `TA_F=23.84` at 19:00 and `TA_F=21.04` at 21:00. The earlier or later `TA_F_MDS` fields contain plausible ~23°C values but their QC class is 3, not automatically accepted as science replacement.
2. **US-SP1, 2004-12-04 00:30–01:30:** `PA_F=51.288/1.499/51.276` surrounded by ~101 kPa, while `PA_F_QC=2`. `TA_ERA=-243.686` at the minimum; native `TA_F` remains ~10°C.
3. **US-Syv, 2004-12-03 23:30–2004-12-04 00:30:** `PA_F=49.149/5.064/49.026` around ~93 kPa; `TA_ERA=-136.728/-271.171/-135.987°C` at anomalous times, while native `TA_F` is physically plausible near −2°C.
4. **US-Ton, 2004-12-03 21:30–22:30:** `PA_F=49.032/-1.185/49.034` around ~99 kPa, with `TA_ERA=-127.144/-257.363/-127.45°C`; tower `TA_F≈5.6–6.1°C` remains plausible.
5. **US-Ton, 2003-02-27:** repeated `RH=0.001%` and `VPD_F≈10.1 hPa` at tower `TA_F≈7°C`; companion `TA_ERA≈7–8°C` and `VPD_ERA≈1–2 hPa` imply much greater humidity. The source may be defective but the exact full event duration needs candidate audit.
6. **US-Ton, 2025-11-16:** `RH≈102.1–102.2%`, `VPD_F=0`; site-derived `RH(TA_F,VPD_F)=100%` while same-label packaged ERA variables suggest nonzero VPD.
7. **US-Syv, 2025-05-16 02:30:** isolated `TA_F=0`, `VPD_F=6.110`, `RH=0` between `TA_F≈8.15` and `8.14°C`. Should be audited as a joint temperature/VPD dropout rather than an authentic freezing event.

## User-authorised scientific approach

The user expressly requested reuse of previous QCv5 interpolation for obviously invalid records, and reconstruction of problem RH from ERA5. Historical code [Batch03 QCv5 engine](../../AmeriFlux_MultiSite_10_Batch03/scripts/stage07/qcv5_native.py) sets native half-hourly interpolation caps: `TA_F=4`, `VPD_F=4`, `PA_F=4`, `SW_IN_F=2`, `LW_IN_F=4`, `WS_F=4`, `P_F=0`. An isolated BAD run must have **two valid adjacent boundary observations** within the same calendar year; longer runs are **not partially interpolated**.

The new Batch04 [Stage05 candidate builder](../scripts/stage05/05_build_batch04_qcv5_repair_candidates.py) reuses the 4-HH rule for physically impossible `TA_F` and short triangular `PA_F` errors. For `PA_F`, the companion 49–51 kPa side lobes are included using a conservative **<65 kPa** pulse threshold when strong valid neighbours exist: this is a new, labelled local pulse extension rather than the historical absolute PA<50 threshold. A single `TA_F=0,VPD_F=6.110,RH≤1` surrounded by plausible ~8°C readings is a separately labelled joint-sensor extension.

For original site `RH<5%`, `RH>100%`, or physically invalid site `TA/VPD` pair, use physically screened **same-timestamp** companion `TA_ERA,VPD_ERA,PA_ERA` as a *QCv5 candidate estimate* only. Compute liquid-water `RH_ERA = 100 × [1 - VPD_ERA / e_s(TA_ERA)]`, then `VPD_candidate=e_s(TA_tower_candidate) × [1 - RH_ERA/100]`, preserving physically valid local TA and PA. ERA pair must have temperature -55 to 52°C, PA 65 to 110 kPa, VPD≥0 and physically valid 1–100% RH; site/ERA temperature difference must be ≤8°C. ERA columns in this package are **calibrated/downscaled FLUXNET derivatives, NOT a separately downloaded independent raw ERA5 measurement**. The event must not mix a corrupted ERA component with tower variables.

**Important scientific distinction:** missing native RH alone (e.g. ~50% on US-Syv) does not require mass ERA replacement when consolidated `TA_F,VPD_F,PA_F` are already valid; the eventual model humidity should be computed from reconciled valid variables. RH repairs also need to consider ice versus liquid water saturation at subzero temperatures, plus native QC/provenance.

## Materialisation and approval

Stage05 `--build-candidates` generates an **isolated sparse patch overlay** `candidate_patch.csv`, `unresolved_hold.csv`, and SHA256-pinned `report.json`. It does not overwrite original archives, native CSVs, the `ERA5_HH` CSVs, previously prepared forcing, site surfaces, or cases. A candidate overlay is *substantive numerical repair preparation*, **not yet a complete forcing CSV**. The user must first examine unresolved events and candidate QC logic, and a separate Post-v5 merge/integration gate is required before production forcing.

**No actual Stage05 operator run is yet observed.** Until its self-test, preview, candidate build and subsequent review pass, record `STAGE05_READY_NOT_EXECUTED`, **no production repair or spin-up approved**.
