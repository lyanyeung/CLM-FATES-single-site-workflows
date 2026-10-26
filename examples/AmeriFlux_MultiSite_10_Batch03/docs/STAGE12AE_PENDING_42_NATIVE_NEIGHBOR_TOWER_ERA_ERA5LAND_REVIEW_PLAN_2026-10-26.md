# Stage12ae — 42 pending original-tower vs paired-ERA vs ERA5-Land before/after source review

The user requests the **actual original native half-hours before and after every still-unapproved event**, including original measured tower air temperature and published source VPD and QC, original matched companion FLUXNET `TA_ERA/VPD_ERA`, gridded SHA-verified ERA5-Land T2M/dewpoint/RH, and existing Stage12g forcing output.

## Current exact review population

- **34 US-Kon** `HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA` original source events in 2011–2012.
- **3 US-NR1** similar jumps: 2022-09-10 original times 06:00, 07:00, 08:30.
- **4 US-MtB** `HOLD_ICE_SUPERSATURATION`: 2024-02-11 05:00/05:30/06:00/06:30; operator conditional permission only IF installed CLM-FATES branch explicitly accepts forcing water-RH plus ice supersaturation without numerical fault. No model compatibility verified; hold until confirmed.
- **1 US-Kon 2008-09-26 05:30** original published VPD QC0 protected; do not replace without independent original observation/QC review.
- **33 US-Me6** previous Stage12g candidate jump events: user has already approved the general **original paired ERA-RH at fixed measured tower T/P** replacement approach, but these 33 are **NOT yet all applied**; they are not part of pending human decision count and should be shown for source provenance audit.

## Pinned direct source procedure

[Stage12ae exact 42 pending event triplets with optional ±2 source context, plus 33 Me6 previously approved event audits](../scripts/stage12/12ae_review_all_42_pending_before_after_tower_ERA_ERA5Land_READONLY.py), Git commit **`b5d5c9cadbb506deac1909049b97dc73b76e5a89`**, Git blob **`1cc3da4e9644bb44276caf35b69669d84b813d66`**.

The script checks original Stage12g SHA receipt/75 event ledger/verified gridded yearly-source manifest; original Stage07 FLUXNET tower and native paired ERA inputs/manifest SHA; existing operator-applied Stage12ac original US-Me6 separate source SHA; pinned Stage10b gridded time/UTC midpoint/position interpolation module Git blob. For each native time, it samples exactly previous 2, previous 1, original center, next 1, next 2 native half-hours (5 × 75 = 375 provenance rows), printing previous/current/next for **all 42 still-unapproved** original centers, a 42-line center summary and a separate 33-line US-Me6 already-approved policy source summary. The new script intentionally labels raw `VPD_F` with its native original QC: `QC=0` direct measurement, `QC=1` MDS fill, `QC=2` ERA-derived source; not all original VPD values are measured.

The gridded ERA5-Land RH is reconstructed separately from T2M/dewpoint using source UTC-midpoint interpolation at the **unapproved** original published station BIF time offset hypothesis. The local clock remains unchanged. The original site-downscaled FLUXNET companion ERA `TA_ERA,VPD_ERA` and the gridded ERA5-Land RH **MUST NOT be conflated**. For central reviewed events, Stage12ae verifies newly reconstructed gridded ERA5-Land T2M/RH exactly match the original SHA-signed Stage12g rejection ledger values. The Stage12ac Me6 overlay is read independently as current selected source (not replacing or overwriting original sealed Stage12g).

`--self-test`: synthetic mathematical checks; zero writes. `--check`: complete source and provenance table in terminal, zero writes. `--run`: same full review + **new isolated read-only-derived report only**, includes 75 × 5 context rows, source neighbor-jump summary, verified gridded year source receipts, SHA file manifest, original science HOLD unchanged. No source, forcing, PFT, DATM, Slurm or CLM-FATES spinup changes. **GitHub committed but NOT yet executed on user's IRIDIS6**; no assertion that the neighbor data was remotely read from their HPC.

Data NOT shown by prior 75-row output: original VPD and Stage12g values at the immediate neighboring native half-hours, original companion ERA at neighbors, and verified ERA5-Land interpolation at neighbors. Prior center-only rejection metadata must not be presented as if these adjacent observations have already been seen.
