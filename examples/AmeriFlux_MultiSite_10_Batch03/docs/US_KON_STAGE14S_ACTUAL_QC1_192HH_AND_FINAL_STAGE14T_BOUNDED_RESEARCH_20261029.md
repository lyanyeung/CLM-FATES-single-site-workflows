# US-Kon actual Stage14S 2011-May26 original T source evidence and final Stage14T bounded ERA5-Land research proposal

## ACTUAL operator Stage14S read-only science output (2026-10-29)

**Last remaining US-Kon Stage14R protected VPD/QBOT NaN is exactly original local 2011-05-26 11:00.** Original selected source 280320 30min NOLEAP 2004–2019 unchanged.

The ACTUAL original source `TA_F_QC==1` continuous run containing the artificial 02:00–02:30 join spans **2011-05-22 11:00 through 2011-05-26 10:30**, exactly **192 HH (96 h)**. This is a long tower *missing/gapfilled* T episode, **NOT 192 true measurements**. 02:00 original TA_F17.521°C/QC1 and 02:30 TA_F17.520°C/QC1. Initial Stage14R proposed replacing only from 02:30 with original SHA-verified ERA5-Land T2m13.114°C, left 02:00 original QC1 source17.521°C, creating a wholly artificial **4.407°C** join and one correctly protected HOLD.

Nearest TRUE original tower temperature QC0 **before May26 02:00** is **2011-04-27 08:00**, 7.365°C, distant **690 h**. Nearest after is **2011-05-26 11:00**, 16.777°C (next 11:30 QC0 17.311°C), distance 9h. This is too long to interpolate a measured-QC0 tower temperature across the whole run.

### Before, during, after and original ERA comparisons

| Native local source time | Original TA_F °C | Original TA_F QC | Original paired TA_ERA °C | Verified ERA5-Land T2m °C |
|---|---:|---:|---:|---:|
| May25 00:00 | 17.319 | 1 | 15.773 | 17.695 |
| May25 02:00 | 17.390 | 1 | 15.253 | 15.811 |
| May25 09:00 | 17.195 | 1 | 16.356 | 18.243 |
| May26 00:00 | 17.522 | 1 | 12.016 | 13.020 |
| May26 02:00 | 17.521 | 1 | 12.294 | 13.126 |
| May26 02:30 | 17.520 | 1 | 12.407 | 13.114 |
| May26 06:00 | 19.919 | 1 | 11.040 | 12.022 |
| May26 09:30 | 25.909 | 1 | 14.279 | 15.954 |
| May26 10:30 | 22.709 | 1 | 16.318 | 17.188 |
| **May26 11:00** | **16.777** | **0** | 16.803 | 17.756 |
| May26 11:30 | 17.311 | 0 | 17.285 | 18.278 |
| May27 02:00 | 11.014 | 0 | 13.254 | 12.644 |
| May27 09:00 | 12.395 | 0 | 14.156 | 17.319 |

All numbers above **actual user-provided** original Stage14S source audit, not generic synthetic approximations. Site source local UTC−6/interval midpoint +15m, ERA5-Land 2011 ZIP SHA source separately independently verified and original source FLUXMET/paired ERA SHAs signed.

**Interpretation.** Two ERA products coherently indicate the May26 early/morning original TA_F QC1 warm bias (up to ~10°C), and the returning tower true QC0 at 11:00 matches companion ERA within 0.026°C. Previous day May25 original QC1 T and ERA5-Land often agree to ~2°C; May27 original T QC0 differs from ERA5-Land increasingly during morning by up to >5°C. Therefore it is **NOT** scientifically justified to replace all 192 source QC1 T entries or declare ERA5-Land equivalent to measured tower T everywhere. Original source RH during this event is also QC1; reanalysis is a low-confidence candidate, not original measured tower humidity.

## Stage14T one-pass *isolated research-only* bounded last one HOLD experiment (unexecuted)

[Stage14T source-controlled script](../scripts/stage14/14t_US_Kon_May26_last_QC1_plateau_ERA5_bounded_research.py), Git commit `7207430364610eef44d3bb2d95a39632a308d5f3`, Git blob `e6f8aff083858930544bdee71f3bcc3093e8464a`. **Committed but not yet run on IRIDIS6.**

This operates only on original **Stage14R actual signed 1-HOLD research tape** at `science_trials/US_Kon_14R_last_two_reanalysis_source_RESEARCH_ONLY_20261029T071709Z_37710989`. Requires the existing original SHA-verified Stage14O local ERA5 loader, `$HOME/US_Kon_nine_tower_ERA5Land_pm2h.py`, exact Git blob `dabc868924ec46a5a2905ad3505a100fd1974e52`; no new data downloads.

The scientifically narrowly justified probe starts at May26 09:00, progressively moves its left edge **only when that external source 30-minute contact fails** and **only through original T QC1 and VPD QC1/QC2**, with absolute left limit **May25 00:00**. This avoids any false 02:00 original QC1/02:30 ERA5-Land mix. The earliest time selected is whichever 30-minute source transition passes all science constraints with the **smallest number of additional source edits**. The group must have valid original 2011 paired FLUXNET companion ERA RH and verified ERA5-Land RH difference ≤15pp for every candidate halfhour; full T, VPD, RHwater, QBOT, water/ice saturation and all halfhour internal/both external joins must satisfy unchanged original fixed criteria: dT≤4°C, dVPD≤4 hPa, dRH≤20pp, dQBOT≤0.003 kg/kg. The genuine observed 11:00 and later T QC0 **cannot** be modified; all previous Stage14R signed Sep29 and earlier independently researched events untouched. On failure the complete one source NaN stays protected. A new isolated research-only CSV/receipt is written by `--run`, no model inputs/CIME/Slurm.

**Important:** if Stage14T yields `remaining_HOLD_count=0`, this is only 280320-row numerical research humidity completeness, not independent measured source RH, not whole-site global QA, and NOT Postv5, DATM or AD400 spin-up approval.

```bash
(
  set -euo pipefail
  SCRIPT="$HOME/US_Kon_final_May_QC1_ERA5.py"
  READER="$HOME/US_Kon_nine_tower_ERA5Land_pm2h.py"
  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/30c4f7d3acdfe3df642ec83af756c67ebc547874/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14o_US_Kon_FINAL_nine_original_tower_ERA5Land_pm2h_READONLY.py" -o "$READER"
  test "$(git hash-object "$READER")" = "dabc868924ec46a5a2905ad3505a100fd1974e52"
  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/7207430364610eef44d3bb2d95a39632a308d5f3/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14t_US_Kon_May26_last_QC1_plateau_ERA5_bounded_research.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "e6f8aff083858930544bdee71f3bcc3093e8464a"
  python3 -B -c 'import pathlib,sys;p=pathlib.Path(sys.argv[1]);compile(p.read_text(),str(p),"exec");print("SYNTAX PASS")' "$SCRIPT"
  python3 -B "$SCRIPT" --run 2>&1 | tee "$HOME/US_Kon_final_May_QC1_ERA5.log"
)
```
