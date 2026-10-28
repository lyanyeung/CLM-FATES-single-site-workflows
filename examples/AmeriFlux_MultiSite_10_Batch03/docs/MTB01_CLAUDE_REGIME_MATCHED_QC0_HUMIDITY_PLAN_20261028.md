# US-MtB (Claude workstream) — MtB01: regime-matched QC0 humidity evidence, 2026-10-28

Read-only. This stage writes no repairs, makes no approvals, and does not touch US-Me6. The user makes every repair decision.

## What the earlier stages already show

| Stage | Humidity source tried | What stopped it at US-MtB |
| --- | --- | --- |
| 12d | Release-paired `TA_ERA`/`VPD_ERA` water RH applied at tower `TA_F` | Tower `TA_F` and `TA_ERA` differ by more than 5 °C: **2821** MtB rows |
| 12g | Independent ERA5-Land RH (3 downloaded years) | The same > 5 °C temperature rule, plus 4 ice cases. 1325 rows have no verified ERA5-Land year |
| 12j | Four ERA5-Land transfer methods | Every method failed the QC0 gate on all cold QC0 humidity (the > 2 hPa tail) |

The remaining gaps sit in one regime: the measured tower (`TA_F_QC=0`) is much colder than both reanalyses. That fits a cold-air pool or inversion at a mountain station. It would also fit a probe problem: the humidity sensor is missing at exactly these times, so `VPD_F` is gap-filled.

Stage12j validated on **all** cold QC0 data, and most of those records have a small tower−ERA difference. It did not test whether measured truth exists **in the target regime**.

## What MtB01 does

[Script](../scripts/mtb/MtB01_regime_matched_QC0_humidity_census_READONLY.py). It reads its inputs through the pinned Stage12g module (`sources()` re-verifies Stage12e/12f and returns every currently verified MtB ERA5-Land year). It also checks the Stage12g timeline folder named in the handoff (`…083234Z_e168f29f`) against its own receipt. The analysis covers the full release record, not only 2020/2022/2024. It has seven parts:

- **A. Census of every Stage12g MtB humidity gap.** The breakdown is by year, ledger reason, QC, hour, month, dT = `TA_F − TA_ERA` bin and gap length, with QC0 anchors within ± 2 h.
- **B. Measured truth by regime.** `VPD_F_QC=0` and `TA_F_QC=0`, counted per year × dT bin.
- **C. Four predeclared candidates, validated only on that truth.**
  - `COMPANION_RH` (the Stage12d formula)
  - `COMPANION_E`
  - `EMP_BIN_RH`: the QC0 mean RH in the same month, 3-hour block and dT cell, with the predicted time's 10-day block excluded
  - `EMP_ADJ_RH`: `COMPANION_RH` plus the block-excluded QC0 residual

  The gates are the Stage12j thresholds: N ≥ 50, valid fraction ≥ 0.60, MAE ≤ 1.5 hPa, |bias| ≤ 0.7 hPa, and at most 10 % of errors above 2 hPa. They are applied per year to cold QC0 data. There is also a new **REGIME gate**: pooled QC0 records with |dT| > 5 °C must meet the same thresholds. A method passes only if every year with N ≥ 50 passes, there are at least 3 such years, and the REGIME gate passes. All of this was fixed in code before any result.

  Error tails are reported by dT bin, tower T, month and measured VPD (descriptive only), together with runs of consecutive errors above 2 hPa.
- **D. Tower temperature plausibility.** Yearly extremes and episodes with `TA_F` < −25 °C, compared with `TA_ERA`. This includes the 2022 QC0 cluster near −39 °C. Nothing is deleted.
- **E. ± 2 h context tables** for the four 2024-02-11 frozen-phase events and the first ten extreme-cold episodes. The columns are:
  - tower values with their QC class
  - the companion ERA values
  - independent ERA5-Land T2m/D2m/SP where a verified year exists
  - RH relative to water and to ice, VPD and QBOT for each candidate
- **F. Installed model code.** The CTSM/CDEPS git HEADs, and the humidity lines in the installed DATM CLMNCEP mode, `lnd_import_export`, `atm2lndMod` and `QSatMod`. These are needed for the ice-supersaturation question.
- **G. ERA5-Land evidence files.** Which variables they contain. A geopotential field is needed for true grid orography.

## How the result decides the next step

- **B shows no or very little QC0 truth with |dT| > 5 °C.** No method can be validated in the target regime. The honest options are to keep the gaps on HOLD, or to fill them as a clearly labelled sensitivity input that is not validated.
- **REGIME truth exists and a method passes.** That method becomes a candidate for the user to decide on. The package states how many gaps it can cover and how many stay on HOLD.
- **REGIME truth exists but every method fails.** Look at the tails and at D: if the gaps line up with implausible tower temperatures, the problem is the temperature source, not the humidity method.
- **F decides the four frozen-phase points.** They are kept only if the installed code demonstrably passes QBOT through without a saturation cap or abort.
- **G has no geopotential.** A separate small CDS request for the ERA5-Land invariant geopotential (3 × 3 cells around the tower) is the next step for true grid height and grid selection.

## IRIDIS

```bash
cd ~ && conda activate clm_fates_env
REV=<commit>
M=~/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03/scripts/mtb/MtB01_regime_matched_QC0_humidity_census_READONLY.py
mkdir -p "$(dirname $M)"
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$REV/examples/AmeriFlux_MultiSite_10_Batch03/scripts/mtb/MtB01_regime_matched_QC0_humidity_census_READONLY.py" -o "$M"
python3 -B "$M" --self-test
python3 -B "$M" --check 2>&1 | tee ~/mtb01_check.txt
python3 -B "$M" --run   2>&1 | tee ~/mtb01_run.txt      # only after --check succeeds
```

## v1 fix (28 Oct, first IRIDIS `--check`)

The first `--check` stopped in Stage12h `evidence()` with `Expected exactly three validated US-MtB source years`. The Stage12g `sources()` catalog is built live from the Stage12f download status, and more MtB years have been verified since Stage12h/12i/12j ran. Those stages hard-code 2020/2022/2024, so they are historical snapshots, and their own `--check` would now refuse too. Nothing was written.

MtB01 now uses the pinned Stage12g module directly: Git blob `14eabe09`, the same pin as Stage12h. It uses all verified MtB years and takes `--stage12g` to name the timeline folder, which is receipt-checked.
