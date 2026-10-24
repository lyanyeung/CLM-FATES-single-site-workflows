# Batch03 Stage11l — 11 explicit US-NC2 new RH method decisions and isolated humidity-only successor

**Decision date:** 24 October 2026. User explicitly approved the **11 previously unrepaired US-NC2 neighbour VPD source-native timestamps** for the same release-paired companion **ERA5 relative-humidity transfer** as the Stage11h research shadow. The user also explicitly directed **EC tower air temperature not to change**, and to modify **humidity only**. This instruction is distinct from the already retained six Stage07 TA selections: Stage11l starts from Stage11h, retaining `TA_USE` and `TBOT` at **every native half-hour**, not restoring or changing any Stage07 predecessor temperature.

## Machine-readable user-selected 11 new targets

[STAGE11L_USER_APPROVED_11_US_NC2_NEIGHBOUR_RH_ADDITIONS_2026-10-24.csv](STAGE11L_USER_APPROVED_11_US_NC2_NEIGHBOUR_RH_ADDITIONS_2026-10-24.csv)

| Native source date | Exact original timestamp set | Count | Source VPD QC |
| --- | --- | ---: | --- |
| 2025-03-18 | 18:30, 19:30 | 2 | 2 |
| 2025-03-23 | 13:00, 13:30, 14:00, 14:30, 15:00 | 5 | 1 |
| 2025-03-25 | 08:00, 08:30, 09:30, 10:00 | 4 | 1 |
| **Total** | **11 unique native half-hours** | **11** | 2 QC2 + 9 QC1 |

The 11 original VPD values were **unchanged in Stage07 and Stage11h**. Stage11k v2 successfully verified the earlier 52 source context entries had exactly 25 source/companion ERA RH discrepancy cases: 11 untouched, 3 Stage07-only corrections, 7 other Stage11h modifications and 4 Stage11h central hotspot corrections. The new 11 do not overlap the previously approved 62 event IDs.

**Original 62-event human choices remain unchanged:** 6 existing Stage07 TA candidates retained, 53 original ERA5 humidity target times, 3 existing Stage07 VPD retained. Stage11l cumulative candidate ERA-RH target mask: **53+11=64 unique humidity timestamps**. Count of *actually different* VPD values in Stage11l is not known until its IRIDIS calculation; Stage11h had 43 actual changes.

## Exactly what "change humidity only" means

The paired FLUXNET site-downscaled ERA5 companion source provides `TA_ERA` and `VPD_ERA` at the original exact native timestamp. These are used only to reconstruct **source companion fractional RH over water**:

`RH_ERA = (es_water(TA_ERA) - VPD_ERA) / es_water(TA_ERA)`

At the existing Stage11h tower candidate temperature (`TA_USE`) and site pressure (`PSRF`) the new humidity is

`VPD_new = es_water(TA_USE) * (1 - RH_ERA)`

`e_a_new(Pa) = 100 * es_water(TA_USE) * RH_ERA`

`QBOT_new = 0.622 * e_a_new / (PSRF - 0.378 * e_a_new)`

`TA_USE`, `TBOT`, `PSRF`, all other meteorological columns, native timestamps and all nontarget VPD/QBOT rows must be unchanged compared with the sealed Stage11h research shadow. **ERA temperature is NEVER substituted for the EC tower/site air temperature.**

No 1% RH floor, no silently copied ERA VPD at a different tower temperature, no arbitrary interpolation, no unapproved change of 3 Stage11f retained VPD events. This is **not independent gridded ERA5-Land T2m/dewpoint verification**.

## Script and mode

[11l_us_nc2_11_neighbour_humidity_only_shadow.py](../scripts/stage11/11l_us_nc2_11_neighbour_humidity_only_shadow.py) has been committed to GitHub, **not yet run on IRIDIS6**.

- `--self-test`: synthetic formula/negative-humidity/11-target census checks, no original inputs
- `--check`: **completely read-only** source and SHA preflight; imports the exact SHA-pinned Stage11h and Stage11k-v2 verification modules; independently calculates all 11 replacements in memory and prints data and boundary evidence, without output writes
- `--run`: after the same checks, writes exactly **one new US-NC2 full-year NO_LEAP shadow CSV** in a **new** `science_trials/stage11l_US-NC2_humidity_only_*` folder with:
  - exactly 11 source-native event replacement details
  - all 11 point-level original vs successor neighbour VPD jumps
  - **six outer boundaries** (before + after) of the three extended events
  - yearly VPD/RH/QBOT changes relative to Stage11h
  - an SHA file-reference JSON for the unchanged Stage11h US-MOz and US-Mpj files, without copying them (avoid unnecessary files/inodes)
  - SHA receipt, source provenance, an `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker written **before** any shadow forcing CSV, and scientific hold instructions

The script rejects any modification of `TA_USE` or `TBOT` in all 367,920 US-NC2 half-hour rows, rejects all unselected variable/time changes, requires the 11 source-native IDs and verified source QC/RH evidence, and checks whole-year physical humidity/QBOT closure.

**The six boundaries** include both ends of Mar 18 18:30–19:30, Mar 23 09:00–15:00 (including previously Stage11h-corrected rows), and Mar 25 08:00–10:30 (includes already Stage07-corrected row). Compare absolute and ADDED jumps; do not infer observational truth from smoothness alone.

## Scientific status

**Decision accounting:** 62 original reviewed records + 11 new candidate repair choices = **73 distinct human-reviewed source event IDs**, of which **64 are ERA-humidity-targeted IDs**, six are KEEP TA and three are KEEP VPD. The additional 11 are *human approved as a trial repair method* only, **not formally approved as physically correct observations or Post-v5**.

Existing Stage07, Stage11h and Stage11j source/receipts remain SHA-locked and unchanged. Other seven Batch03 sites retain 1,924 independent humidity blockers. Post-v5 accepted sites=0; DATM ready sites=0; spinup authorised=0.

Do not remove any `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker or launch model jobs based on Stage11l without later independent source/science gate acceptance.
