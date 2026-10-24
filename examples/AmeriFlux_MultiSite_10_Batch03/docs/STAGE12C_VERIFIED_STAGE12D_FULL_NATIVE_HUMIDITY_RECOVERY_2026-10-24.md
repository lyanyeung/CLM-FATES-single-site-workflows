# Batch03 Stage12c VERIFIED; Stage12d six-site companion humidity recovery

**2026-10-24 IRIDIS6 operator log:** Stage12c passed Python syntax, `--self-test`, full read-only `--check`, and isolated `--run`. Six time-complete native NO_LEAP files were generated in:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage12c_six_site_noleap_hold_shadows_20261024T120618Z_f369a05e/`

**Exact important distinction:** Stage12c's 8,398 rows with at least one missing/held value comprise **233** previous specific Stage12b scientific humidity holds and **8,164** other newly encountered missing/invalid source humidity rows; together these cover 8,397 distinct humidity rows. **One more row** lacks a non-humidity field only. Seven rows in total lack some non-humidity forcing field, of which six overlap already-held humidity rows. There is therefore no valid scientific claim that all 8,398 are newly observed sensor errors. The extra humidity gaps arise from rebuilding from raw FLUXMET without the earlier Stage07 engine's full correction sequence.

| Site | NO_LEAP half-hours | Stage12b RH patches retained | Original Stage12b physical science holds | Additional Stage12c humidity holes | Any missing/held variable rows | Pre-existing Stage12c boundary jumps >4hPa |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| US-NR3 | 315,360 | 1,312 | 172 | 456 | 628 | 0 |
| US-Kon | 280,320 | 227 | 2 | 1,268 | 1,270 | 1 |
| US-NR1 | 490,560 | 116 | 57 | 940 | 998 | 0 |
| US-MMS | 219,000 | 17 | 1 | 28 | 29 | 0 |
| US-MtB | 280,320 | 14 | 1 | 5,209 | 5,210 | 0 |
| US-Me6 | 280,320 | 1 | 0 | 263 | 263 | 0 |
| **Total** | **1,865,880** | **1,687** | **233** | **8,164** | **8,398** | **1** |

The source chronology is complete, but the six files are intentionally NOT model-ready forcing. Stage07 originally completed **only US-MOz, US-Mpj, US-NC2**; the other seven failed the humidity numerical trial, so there is **no valid complete Stage07 six-site forcing file** to patch.

## Stage12d: automatic guarded RH recovery, no further event-by-event decisions

[Stage12d source-native companion ERA humidity gap rescue](../scripts/stage12/12d_native_companion_RH_bulk_gap_rescue.py), committed to GitHub, **not yet executed on IRIDIS6**.

- SHA verifies the original Stage07 source manifest, original 12b selected RH ledger and preserved holds, and EVERY 12c six-site shadow CSV/receipt.
- Reads the original exact-release FLUXMET and paired exact native-timestamp ERA `TA_ERA` + `VPD_ERA` for each site. This **does not use any guessed tower-to-UTC offset**, CDS files or source time shift.
- Builds companion ERA water RH from `TA_ERA` and `VPD_ERA`, transfers only this RH to **unchanged Stage12c EC tower `TA_USE` and site `PSRF`**, reconstructing `VPD_USE` and `QBOT` for previously missing *additional* humidity rows only.
- Selects only original source VPD QC1/QC2; holds QC0 or missing QC metadata (never silently replace measured tower humidity). Strictly requires physically valid companion vapour pressure, 0–100% RH without clipping, original site T/pressure, site–ERA T difference ≤5 °C, subzero ice saturation consistency, valid new specific humidity, and native half-hour/hour no-clock-shift source alignment. A newly filled time point creating an adjacent jump >4 hPa is returned to unresolved status, rather than smoothing a neighbour.
- **Preserves all 233 pre-existing original Stage12b physics and temperature science holds as NaN VPD/QBOT**. Also preserves every already valid VPD/QBOT value and all OTHER columns/clock/TBOT/TA_USE/PSRF exactly as in Stage12c. Explicitly reports the count, source QC and reason for all remaining unrepaired extra holes.
- `--check`: in memory, absolutely no report/forcing writes.
- `--run`: creates **six NEW science-only NO_LEAP successors** under an `INCOMPLETE`-marked `science_trials/stage12d_*` folder, with per-target provenance, remaining hold summary and SHA receipt. It never touches Stage12c or original/Stage07 source.

**Scientific scope:** This is automatic NUMERICAL research shadow repair, not validation of tower humidity observations and not approval of historical tower clock metadata. The companion ERA5 source may be downscaled/regressed and imperfect. Stage12c's original US-Kon one >4 hPa and three added >2 hPa edge jumps remain separate previously noted review flags; Stage12d's new jump guard does not retroactively validate them. No Post-v5, DATM, CIME, Slurm or spinup approvals. US-Me2's four separate unverified-clock source events remain held entirely outside this six-site workflow.
