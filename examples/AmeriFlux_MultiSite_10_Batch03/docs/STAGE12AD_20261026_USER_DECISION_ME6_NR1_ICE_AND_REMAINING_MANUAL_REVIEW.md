# Stage12ad — operator decision and exhaustive pending triage after Stage12ac

**User statement (2026-10-26):** For US-Me6, extend the previously operator-approved humidity reconstruction from original-native paired ERA relative humidity at measured tower temperature; accept that faster drying during morning warming can be a plausible meteorological feature. User specifically asks whether US-NR1 near-saturation was produced after substituting ERA5 RH, or whether it represents original measured tower RH. For US-MtB, user authorizes retaining all 4 water-RH-derived ice-supersaturated records **ONLY IF their installed CLM-FATES model explicitly accepts them**. Preserve this condition: *physics plausibility is not proof of model acceptance*. User requests EVERY remaining manual-review category identified without repeated individual-event questions.

## Provenance / immutable source evidence

Stage12g checked 75 source-reviewed event rows in user-supplied IRIDIS6 log dated 2026-10-26. Grouped counts: US-Me6 `HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA` 33; US-Kon same 34; US-NR1 same 3; US-MtB `HOLD_ICE_SUPERSATURATION` 4; US-Kon `HOLD_ORIGINAL_QC_OR_SITE_T_P` 1. Original Stage12g receipt: `science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f/stage12g_research_only_sha_receipt.json`. These 75 originate **ERA5-Land gridded RH candidate screens**, distinct from the paired original FLUXNET `TA_ERA/VPD_ERA` humidity source employed at the already-applied five US-Me6 Stage12ac times.

**US-Me6 decision scope:** user accepts the same *approach* for all 33 Stage12g VPD-jump candidates; their grid source alone does not prove the availability, valid clock offset, matching humidity, QBOT, source QC, or physically valid original paired ERA candidate. Use original paired ERA-RH when present and checked, unchanged original tower QC0 T and PSRF, no QC0 VPD overwrites. Treat >4 hPa alone as no longer requiring new case-by-case user approval for this Me6 scope; verify same-source provenance and boundary integrity, don't silently apply gridded RH or extend approval to other stations. As of this document, **no new US-Me6 33-row derived applied output is claimed**.

**US-NR1** `202209100600` grid water RH 99.033191%, site tower measured temp 0.762°C, original `VPD_F_QC=1`; `202209100700` grid RH 96.536603%, tower T 1.720°C, original VPD QC1; `202209100830` grid RH 92.390442%, tower T 1.230°C, original VPD QC1. This is **ERA5-Land grid RH**, *not directly measured RH*. The source original VPD is quality-1 gapfilled, *not tower QC0 humidity*. Stage12g rejects at original existing-neighbour >4hPa, not solely because near saturation is unphysical. Three remain pending user science judgment.

**US-MtB** `202402110500`, `202402110530`, `202402110600`, `202402110630`, original measured tower T approx −8.39,−8.30,−8.50,−8.64°C; gridded ERA5-Land water RH 92.509627,94.483866,95.151813,94.478945%. Grid air T approx −3.64,−3.99,−4.23,−4.35°C. Derived water vapour pressure at colder tower T might exceed saturation over ice but remain less than saturation over liquid water. Atmospheric ice supersaturation can be physically plausible and CTSM accepts specific humidity QBOT forcing, but model docs alone do NOT establish that this particular installed branch's relative-humidity guard explicitly permits `RH_ice>100%`. Four-record conditional authorisation pending exact installed CTSM/CLM/FATES code path DATM QBOT-to-RH checks or non-model input physics preflight; no RH clipping or data repair yet.

**US-Kon original QC0 protected** `200809260530`, QC_VPD_F=0 (observed), tower 16.141°C vs grid 16.797°C, grid water RH 85.231541%. Stage12g `HOLD_ORIGINAL_QC_OR_SITE_T_P`; preserve the observed QC0 VPD unless independent source mismatch documented; no blanket ERA replacement.

## Remaining 34 US-Kon VPD-jump IDs — full user-review candidate list

| Original date | Native HH timestamps |
|---|---|
| 2011-02-21 | 11:00 |
| 2011-02-22 | 09:00 |
| 2011-03-15 | 10:00 |
| 2011-03-24 | 13:00, 14:00 |
| 2011-03-27 | 11:00, 12:00 |
| 2011-03-30 | 09:00, 10:00 |
| 2011-03-31 | 16:00 |
| 2011-04-01 | 11:00 |
| 2011-04-05 | 10:00 |
| 2011-04-07 | 15:00 |
| 2011-05-26 | 11:00, 12:30 |
| 2011-09-29 | 18:30 (original VPD QC2) |
| 2011-10-15 | 07:30 |
| 2011-10-17 | 08:00, 16:30 |
| 2011-10-18 | 02:30, 05:00, 06:00, 21:00, 22:00 |
| 2011-10-19 | 01:00, 02:00, 06:00, 07:00, 11:00, 12:00 |
| 2011-10-23 | 07:30 |
| 2012-02-25 | 10:30 |
| 2012-03-05 | 08:00 |
| 2012-08-05 | 09:00 |

All US-Kon remaining jump targets are original VPD QC1 except `201109291830` original VPD QC2. The table of 75 **does not contain original/raw/ERA/Stage12g values at the immediate neighbor time**, so no science approval can be inferred yet from this listing alone.

## Full six-site remaining humidity inventory, after successful user-approved Stage12ac output selection

| Site | Missing VPD_USE / QBOT |
|---|---:|
| US-NR3 | 238 |
| US-Kon | 367 |
| US-NR1 | 237 |
| US-MMS | 16 |
| US-MtB | 2840 |
| US-Me6 | 65 |
| TOTAL | 3763 |

US-NR1 additionally has one other-variable missing row = 3764 rows with ANY missing. Stage12g earlier holds reasons sum **2670** *distinct pending source-year IDs*, including 70 jump holds, 4 ice holds, 1 QC0/T/P protective hold, 1119 ERA5-Land vs measured tower air temperature mismatch >5°C, and 1476 missing verified ERA5-Land site-year source. The **remaining 1093 humidity-missing records are outside this particular 2670-row Stage12g source-year hold ledger**, not free to use. Earlier **233 immutable science physics holds** are among this legacy protected space; all other historical holds need their own exact classification. User-approved Me6 33 and US-MtB conditional 4 must not be called executed or source-ready.

1119 Stage12g `HOLD_SITE_GRID_T_DIFF_GT5C` by site/year: US-Kon 2011 16, 2012 24; US-Me6 2015 19, 2017 10; US-MtB 2020 300, 2022 328, 2024 403; US-NR1 2022 19. This is a systematic representativeness/source-clock problem requiring a group-level scientific policy, NOT automatically replace measured tower T with gridded air T. 1476 `MISSING_VERIFIED_STAGE12F_SOURCE_YEAR`: US-Kon 2004 3, 2007 8, 2009 1, 2010 3; US-MMS 2000 6, 2014 5, 2019 4; US-Me6 2020 2; US-MtB 2010 127, 2011 242, 2012 116, 2013 183, 2015 56, 2016 107, 2017 87, 2018 285, 2023 122; US-NR1 2001 17, 2002 1, 2004 3, 2008 3, 2010 6, 2011 1, 2012 5, 2013 5, 2017 10, 2018 14, 2019 9, 2020 9, 2021 17, 2023 9, 2024 4; US-NR3 2011 6. These 1476 are missing-source operational tasks, not requests for record-wise operator votes.

Still need classify 1093 existing other Stage12g missing records (including old 233 physics science holds), and conduct other 4 Batch03 sites readiness separate. No Post-v5, DATM or model approval.

## Explicit next steps

1. Apply user's Me6 humidity-source **policy** to the 33 enumerated event timestamps as a separate strictly scoped, SHA-pinned full-year corrected derivative once native paired ERA-RH evidence/QBOT and original source QC/timing verified; do NOT confuse grid ERA5-Land with same-native companion ERA-RH. The previously sealed Stage12ac already fixed five different earlier original native half-hours.
2. Verify exact installed CLM/CTSM/FATES code and coupled runtime handling of ice relative humidity at specific humidity forcing before releasing four MtB conditional records. Preserve water-phase RH and record ice RH separately, and do not invent compatibility.
3. Produce exact original neighbor and candidate triple for 34 Kon + 3 NR1, retain US-Kon QC0 protective row. Ask for *one cluster-level* human choice, never 37 individual repetitive choices.
4. Batch triage 1119 grid-air vs tower-air T mismatch and 1476 verified-source-year holes; classify other 1093 original held records with prior protected 233.
