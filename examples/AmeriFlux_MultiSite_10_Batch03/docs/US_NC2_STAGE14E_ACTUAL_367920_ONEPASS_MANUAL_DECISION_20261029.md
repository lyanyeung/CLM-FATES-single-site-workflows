# US-NC2 Stage14E — actual signed full-site scientific screen & manual decision

**2026-10-29 04:10 UTC — ACTUAL IRIDIS6 SUCCESS** from user-pasted operator run of Git-blob-verified [Stage14E one-pass source auditor](../scripts/stage14/14e_US_NC2_next_onepass_site_march2025_QC_READONLY.py). No forcing, original release, PFT, DATM, case or Slurm edits.

## Exact source selected: stage11Q ACTUALLY APPLIED, not merely a proposal

Actual signed isolated research shadow:

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage11q_US-NC2_auto9_RH_only_20261024T112211Z_cd95c65a/US-NC2_humidity_only_auto9_shadow_NOLEAP.csv
```

Its receipt SHA256: `82420c80e41893fe6e5fc83439dd9d66eb0fc874353ec9fa2b56153711a85131`. Original tower SHA256: `0fcf835eb58889b942f73c4dd46f61fbf0b2cb7e25f2de67100b6ebca3b78c77`. Paired standalone ERA original SHA256: `408adb16af70c413672a619679f142430f1f1909dea434b892d243331ef8c4b0`. These were verified by the original one-pass program, which selected Stage11Q only after finding a valid SHA-receipted Stage11Q actual result. Earlier 2026-10-24 documents saying "Stage11Q not executed" are superseded.

Final read-only audit report:

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/us_nc2_2025_march_onepass_source_manual_20261029T041041Z_7d1ada0f
```

## Actual 2005–2025 367920 HH results

- **367,920** native 30-minute NOLEAP model rows, exactly 17,520 for each of 21 years.
- **0** missing meteorology; **0** water-based saturation/VPD/QBOT closure issues; **0** `TBOT=273.15+TA_USE` issues; **0** negative wind, precipitation, SW or LW radiation.
- **11** water RH below 5%, **all in 2025**; **1,003** subzero `RH_ice>100%` phase-caution rows (2005–2025).
- All four previously reported anomalous Stage11L March-2025 native VPD edges now below 4 hPa in actual Stage11Q:

| Native event boundary | Prior Stage11L 30min delta VPD hPa | Actual Stage11Q delta VPD hPa |
|---|---:|---:|
| 2025-03-18 18:00→18:30 | 4.997141 | **2.443450** |
| 2025-03-23 08:30→09:00 | 9.467392 | **0.851464** |
| 2025-03-23 15:00→15:30 | 4.812737 | **0.130257** |
| 2025-03-25 10:00→10:30 | 5.859252 | **1.226889** |

Exact source-native QC and original full-day classification: March18/23/25 original VPD QC0 **0** on all three dates; original water-implied negative RH **1/11/1** counts respectively; selected water physical failure **0** on all dates; actual selected VPD differs from original **5/20/7** source-native times. Reanalysis (companion ERA and ERA5-Land) can support an explicit research sensitivity but **not independent measured VPD validation**, even if native time edges are smooth.

## MANUAL FINAL VERDICT

**PASS and CLOSE US-NC2 numeric meteorology gap closure and the four Stage11L discontinuity defects.** Adopt actual signed Stage11Q as **the current independent research derivative for US-NC2**. Preserve all original source and Stage07/Stage11L/Stage11Q signed outputs, original Jan2019 operator-selected tower T, all official VPD QC and original BIF UTC−5 (no user-approved clock shift). Stage11Q added 9 RH-source candidate slots relative to Stage11L and preserves source T/P.

**Do not mass-replace the 11 water-RH<5% or the 1,003 ice RH>100% solely because thresholds flag them.** The first are low-water-RH provenance warnings rather than algebraic errors. The second involve liquid-water vs ice saturation formulations, not evidence each record is impossible. Underlying model water/ice clipping should be examined in one later exact DATM/case preflight if actually releasing this source.

This one-pass result is conclusive on **numeric completeness, water mass consistency, TBOT conversion and the four repaired native half-hour jumps**, **not** the whole original 13 VPD provenance review as independently verified measurements, original clock mapping, active PFT/surface, ZBOT or a model stress-test. It does not provide permission for production Post-v5, DATM, AD400, Normal400, Slurm. Do not create another stage merely to eliminate warnings.

**Next fastest remaining science site: US-MOz.** Actual Stage13L completed 40 original Jan2005 QC1 slots; first 27 Jan2005 source QC1 source-temperature anomaly remains unresolved scientifically despite zero numeric gaps, with Jan09 source exception separately retained. No new ERA5-Land download required: full Jan03–Jan11 2005 original source evidence is already signed on IRIDIS6. US-Me6/US-NR1 assigned to Claude; US-NR3 independently reserved.
