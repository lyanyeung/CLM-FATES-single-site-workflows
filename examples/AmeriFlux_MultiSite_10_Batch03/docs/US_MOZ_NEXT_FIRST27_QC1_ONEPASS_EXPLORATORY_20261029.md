# US-MOz: next single-run first 27 Jan-2005 QC1 source-event *isolated research* derivative

**Operator continuation (2026-10-29):** US-NC2 Stage14E actual PASS: Stage11Q sealed 367920 native HH no numerical missing and four original QC1 March2025 VPD boundaries now all <4hPa. See [NC2 final real operator result](US_NC2_STAGE14E_ACTUAL_367920_ONEPASS_MANUAL_DECISION_20261029.md). Next closest Batch03 scientific site is US-MOz (2004–2021, native 315360 halfhours), numeric full but **first Jan05/06 2005 27 QC1 T/VPD release anomaly** still unreviewed scientifically. This document is a saved plan **not an actual new IRIDIS6 run**.

## Already existing SIGNED evidence and user-approved 40 source replacements

The **second 40 HH** 2005-01-06 14:00–2005-01-07 09:30 was actually applied to one immutable research-only `Stage13L` shadow, with original CDS ERA5-Land independent extracted source and 29 original measured QC0 analogues (not adjacent), official BIF fixed UTC−6. Actual 40/40 source/QC/physics checks passed. **Do not modify it again.**

Original Stage13K source-ledger already contains all 67 tested native source records, nearest real measured QC0 and the aligned Jan03–Jan11 2005 CDS ERA5-Land T/d2m/SP. Both first 27 and second 40 lack true original measured T+VPD QC0 *within six hours* on both sides, despite original 29 QC0 analogues overall. First 27 were explicitly **not included in the earlier Stage13L 40-only operator authorization**. Old Jan09 conflicting negative tower/grid temperatures separately preserved. The existing CDS source is reanalysis, not a true tower observation.

## The one-pass user-requested experimental option, with exact scope

[Stage14F first27 native QC1 isolated sensitivity code](../scripts/stage14/14f_US_MOz_27QC1_onepass_isolated_ERA5Land_sensitivity.py). The NEW algorithm is one independent what-if forcing derivative of the **actual Stage13L signed parent** only:

- Exact original source-native **27** contiguous halfhours `2005-01-05 20:00`–`2005-01-06 09:00`, confirmed both original `TA_F_QC=1` and `VPD_F_QC=1`. Use already SHA-signed `Stage13K` CDS T2m and dewpoint VPD, reconstruct `TA_USE,T​BOT,VPD_USE,QBOT` at original site pressure (PSRF unchanged). All signed original sources and old approved 40 source rows are re-verified and left untouched.
- Whole exact 315360 NOLEAP 18-year `TA_USE/TBOT/VPD_USE/QBOT` (all fields finite) physical closure, 27-only native differential, original 40 exact preservation, existing 29 source QC0 analogues from prior signed reports. No download, no Slurm, no modified old dataset, no PFT/ZBOT alteration.
- Print the exact original-vs-reanalysis T/VPD and both 27-episode outer half-hour T/VPD jumps. If >4 °C/hPa, tag as warnings for human classification; boundary smoothness is diagnostic, **not independent validation**. Write CSV, exact 27-row method ledger, boundary comparison, SHA receipt, prominent `NOT_APPROVED_POSTV5_DATM_AD400` marker in a NEW `science_trials` directory only.
- **THIS IS NOT SCIENTIFIC ADMISSION:** it is an exploratory alternative method for the *first 27 previously unapproved QC1 source records*, not an extension of the prior 40-only source science approval. Original Jan09 event, case PFT/ZBOT, official BIF UTC−6 and model path remain unchanged.

## Exact command (pin SHA after final GitHub code commit)

```bash
(
 set -euo pipefail
 F="$HOME/US_MOz_first27_research.py"
 curl -fLsS --retry 3    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/dc87dd0b4cc31d30ab93f1ff40eb5dede777f3f7/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14f_US_MOz_27QC1_onepass_isolated_ERA5Land_sensitivity.py" -o "$F"
 test "$(git hash-object "$F")" = "4e6b902aaefa7983a687a1cba865173957df9dde"
 python3 -B "$F" --run 2>&1 | tee "$HOME/US_MOz_first27_research.log"
)
```

The source was code-reviewed/pinned through GitHub, not executed on IRIDIS6. If actual source/receipt or case physics differs, it will STOP without modifying existing datasets. Wait for exact new operator report before claiming the first 27 have actually been numerically reconstructed or that output is model ready.
