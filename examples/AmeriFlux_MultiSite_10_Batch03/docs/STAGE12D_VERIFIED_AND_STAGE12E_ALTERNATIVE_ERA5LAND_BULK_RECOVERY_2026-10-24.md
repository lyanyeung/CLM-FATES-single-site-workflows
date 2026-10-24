# Batch03 Stage12d VERIFIED; Stage12e second humidity source autonomous rescue

Stage12d **PASSED** IRIDIS6 Python syntax, self-test, read-only check, and isolated run on 2026-10-24. Sealed research-only successor:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage12d_six_site_companion_RH_gap_recovery_20261024T121810Z_f1fa4cee/`

The Stage12b **1687** numerical ERA5-Land grid-RH target events are unchanged; additional **3792** previously missing humidity events passed native time-paired companion ERA RH screening (EC tower `TA_USE` and `PSRF` unchanged). The original **233** water, phase, temperature and other physics holds are explicitly preserved as missing humidity, with no QC0 observed humidity overwritten, no source time shift, and no Post-v5/DATM/spinup approval.

## Remaining exact counts

| Site | Stage12d additional companion RH repairs | Extra humidity still held (excluding original 233) | Time rows missing any input |
|---|---:|---:|---:|
| US-NR3 | 1 | 455 | 627 |
| US-Kon | 551 | 717 | 719 |
| US-NR1 | 699 | 241 | 299 |
| US-MMS | 8 | 20 | 21 |
| US-MtB | 2353 | 2856 | 2857 |
| US-Me6 | 180 | 83 | 83 |
| **Total** | **3792** | **4372** | **4606** |

Root cause classification of **4372** residual extra humidity rows from the Stage12d source-paired ERA screen:
- Source ERA T versus preserved EC tower TA differs by >5C: **3442**, including **2821 at US-MtB**.
- Companion source RH physically invalid: **743**, including **451 at US-NR3**.
- Repaired VPD would create a new adjacent jump >4 hPa: **180**.
- FLUXMET source VPD QC0 or unknown: **7**.
The **original 233 physics holds**, **four US-Me2 clock holds**, and **one additional row missing a non-humidity input only** are separate. The 4606 rows with at least one missing input are *not* 4606 erroneous direct humidity measurements.

## Stage12e — autonomous but strictly guarded existing-year ERA5-Land source

[Stage12e six-site existing ERA5-Land relative humidity rescue](../scripts/stage12/12e_six_site_independent_ERA5Land_gap_rescue.py) is **GitHub committed, not yet run on IRIDIS6**.

It takes the SEALED Stage12d full native timelines, preserves all 1687 previous Stage12b and 3792 previous Stage12d VPD/QBOT, and runs the previously SHA-pinned Stage10b/Stage09f data verification to access 32 EXISTING and validated year/site gridded ERA5-Land sources.

- Only rows still without VPD/QBOT and NOT any of the 233 original Stage12b scientific conflicts are candidates.
- Requires original FLUXMET source VPD QC1 or QC2 (never auto-overwrites measured QC0/unknown), verified year-site ERA5-Land product, physically valid native-midpoint hourly interpolated T2m/D2m/SP, grid T within 5C of unchanged tower TA, grid pressure within 15000 Pa of existing PSRF, and subzero ice phase plausibility. It does not relax the 5C screen just to improve recovery numbers.
- Transfers **only gridded ERA5-Land RH** (from grid T2m and dewpoint) to original, unchanged EC tower TA_USE and PSRF, rebuilding only missing VPD_USE/QBOT. **ERA5-Land temperature is NEVER inserted into tower temperature forcing**.
- A proposed repair with a new adjacent VPD jump >4 hPa is rejected back to HOLD. Events in years outside the 32 verified sources are likewise held; no CDS downloads are triggered or extrapolated.
- `--check`: no new files; `--run`: ONE NEW `INCOMPLETE`-marked six-site research shadow directory plus candidate, hold, site status and SHA receipt. Neither mode changes original Stage07/11h/11l/11q, previous Stage12b/12c/12d outputs, DATM, CIME, Slurm, surface, PFT or spinup.
- Published site BIF UTC offsets used for **hypothetical native-to-UTC midpoint pairing only**; no station clock offset has been scientifically approved or changed. Gridded ERA5-Land is ERA5-driven, so agreement with source-paired ERA5 is NOT an independent tower-humidity measurement.

**Scientific hold:** No Post-v5, DATM or spinup release is permitted. Scientifically consequential temperature mismatch episodes, unknown tower clock/time calibration and source physics conflicts require dedicated follow-up even if newly generated RH appears smooth.
