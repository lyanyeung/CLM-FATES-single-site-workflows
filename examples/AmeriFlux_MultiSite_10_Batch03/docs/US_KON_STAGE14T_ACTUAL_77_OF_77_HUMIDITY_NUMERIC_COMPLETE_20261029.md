# US-Kon Stage14T — ACTUAL final isolated research source NUMERIC COMPLETE (2026-10-29 07:36 UTC)

## Real operator run (not projected)

The operator executed the original SHA-pinned [Stage14T May26 last-QC1 source group trial](../scripts/stage14/14t_US_Kon_May26_last_QC1_plateau_ERA5_bounded_research.py). The uploaded source terminal log states `US-Kon 14T TWO FINAL SOURCE EVENTS SELF-TEST PASS` (legacy self-test label retained despite the script operating on ONE remaining May event), `US-Kon Stage14T SOURCE GROUP MAY26_ERA5_RH PASS True N 31`, and final `remaining_HOLD_count: 0`. **All 77/77 historical Stage14J remaining VPD/QBOT source missing half-hours have now been numerically reconstructed across Stage14K 68 + Stage14P 5 + Stage14Q 2 + Stage14R 1 + Stage14T 1.** This does not mean all raw QC1/QC2 finite source meteorology was scientifically validated.

Actual Stage14T new isolated science output:
```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/US_Kon_14T_last_May26_ERA5_research_only_20261029T073611Z_8d42d243
```
Actual signed Stage14R input source SHA256 `b2bb53727126ac820bb2986b04d62e14424c26548534064ee811306fd6ee52e5`, original primary tower `f228c7be096f5b79462d5281c80a15a0768c3ef6264853af93753889882777c0`, companion FLUXNET ERA `3aacd53fae73f18e4c7ea305195a246d977969d4548cd0e461aa64bb461c25c9`. Independent downloaded original ERA5-Land 2011 ZIP `external_evidence/era5land_timeseries_stage12f_missing_years/US-Kon/2011/ERA5Land_US-Kon_2011_stage12f_t2m_d2m_sp.zip` was SHA verified.

| Item | Actual result |
|---|---|
| Full selected original site timeline | 280,320 native 30-min NOLEAP HH, 2004–2019 |
| Group | `MAY26_ERA5_RH`, **PASS** |
| Connected native source scope | **2011-05-25 20:00 through 2011-05-26 11:00**, 31 HH |
| Last original source humidity hold actually filled | **2011-05-26 11:00**, original TA_F=16.777°C **QC0** and original VPD_F=20.573 hPa **QC1** (nonphysical at selected T); revised VPD=**9.69487 hPa**, QBOT=**0.00608 kg/kg**; measured tower T QC0 unchanged |
| Other finite native source QC1 VPD/QBOT revised | **30 HH** |
| Original source QC1 T revised | **30 HH** using native SHA-verified ERA5-Land T2m |
| Original tower T/VPD QC0 revised | **zero**, signed original tower source unchanged |
| Final original held missing VPD/QBOT count | **0** |
| All local native interface checks | **PASS**, 0 flagged edges across the 32 exterior/interior contacts |
| Max 30-min ΔVPD | 2.936509 hPa (gate 4) |
| Max 30-min ΔRHwater | 9.741434 pp (gate 20) |
| Max 30-min ΔQBOT | 0.000950772 kg/kg (gate 0.003) |
| Max 30-min ΔT | 3.868391°C (gate 4) |
| Scientific operator approval / DATM / Post-v5 / AD400 / Slurm | **NOT approved, none submitted** |

### Why the original failure was solved

Actual Stage14S original source established that continuous May22 11:00 to May26 10:30 `TA_F_QC=1` had **192 HH with no independently observed T**, and that real T QC0 resumed May26 11:00. Stage14R failed because it replaced 02:30 onward T using ERA5-Land but left original 02:00 QC1 T≈17.521°C, creating a false 4.407°C jump. Stage14T checked candidate left boundaries successively, selected the **latest admissible** original QC1 left boundary **May25 20:00** instead of expanding to the entire 192HH source outage. At May25 19:30 → 20:00, maximum local ΔT is now **3.868391°C**, VPD 2.936509 hPa, RH 9.741434 pp, QBOT 0.000950772 kg/kg; all below predeclared physical screening gates. May26 02:00→02:30 candidate T jump **0.01248°C**, rather than 4.407°C. May26 10:30→11:00 T jump **0.41078°C**, protecting original 11:00 tower QC0.

Original May25 20:00 proposed TA_USE=13.57561°C (original T QC1=17.475°C), VPD 3.53849 hPa. May26 11:00 tower T QC0=16.777°C unchanged; inferred ERA5-Land RH 49.21833%, independent paired FLUXNET ERA RH 50.03353% reasonably agree at center but **neither is independent observed original tower RH at 11:00**. The new site source remains an explicitly marked, separately saved low-confidence research candidate.

## Batch03 ten-site numerical checkpoint

Historical zero-NaN research-source evidence: US-MMS Stage14C; US-MOz Stage14I; US-Mpj Stage14D; US-MtB Claude MTB04; US-NC2 Stage14E; US-Me6 and US-NR1 Claude CL03; US-NR3 Claude NR3_09 MAIN (238/238 original gaps reconstructed, independently verified); and NOW **US-Kon Stage14T**. **9/10 numerically complete selected research shadows, not 9/10 production scientific approval**.

**US-Me2** has Claude CL07 ledger values for 365 problematic original humidity halfhours (122 leave-one-year-out QC0 climatology and 243 site-calibrated companion ERA; still 1 original QC0 nonphysical source HOLD unchanged), but latest [Claude CL04–07 report](US_ME2_CL04_FOUR_EVENT_DECISION_20261029.md) explicitly says **no full US-Me2 signed research forcing shadow exists yet**, and Me2 fire/salvage/tower-move and whole-source QC selection remain open. Do not claim Batch03 complete until a newer actual Me2 shadow/independent verifier appears.

## Scientific interpretation

**Actual confirmed: US-Kon selected research-source meteorology is NUMERICALLY COMPLETE for the previously held humidity source fields; all 280320 original halfhours retained.** Also: no original actual measured TA/VPD QC0 changed. It does **not** prove that unrelated remaining historical QC1/QC2 finite source VPD/T and all other prognostic/downstream forcing are scientifically representative, nor PFT, case clock, DATM saturated over-ice processing, Post-v5 or 400-year model spin-up readiness. Keep `NOT_APPROVED_FOR_DATM_OR_AD400` marker. A separate whole-site read-only scan and provenance receipt check are required before any production promotion.
