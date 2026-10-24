# Batch03 Stage11M verified — US-NC2 four residual VPD boundaries

**Date:** 2026-10-24. **Evidence:** operator-provided IRIDIS6 full terminal output of SHA-pinned Stage11M. Both `--self-test` and `--check` succeeded, followed by `--run`, which created only a new standalone report directory.

**Observed results:**
```
STAGE11M SELF-TEST PASS: source RH, 4 native 30min boundaries, strict no-write hold
STAGE11M SUMMARY: source_site_rows=367920 new_Stage11l_events=11 four_residual_jump_boundaries=4 contexts=40 unchanged_EC_tower_T=True new_human_repair_approvals=0 Postv5_approved=0 DATM_ready=0 spinup=0
STAGE11M REVIEW REPORT DIR: /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage11m_stage11l_four_boundary_context_20261024T101118Z_53f2dfc3
NO STAGE07, STAGE11H, STAGE11L, DATM, CIME OR SLURM MODIFIED.
```

## Boundary evidence (source-native half-hours, hPa)

| ID | Source-native time pair | Stage11h jump | Stage11l jump | Increase | Scientific gate |
| --- | --- | ---: | ---: | ---: | --- |
| MAR18_NEW_START | 2025-03-18 18:00→18:30 | 1.310000 | **4.997141** | **+3.687141** | HOLD |
| MAR23_OLD_START | 2025-03-23 08:30→09:00 | **9.467392** | **9.467392** | 0 | HOLD; inherited Stage11h |
| MAR23_NEW_END | 2025-03-23 15:00→15:30 | 2.053000 | **4.812737** | **+2.759737** | HOLD |
| MAR25_NEW_END | 2025-03-25 10:00→10:30 | 0.051500 | **5.859252** | **+5.807752** | HOLD; largest introduced |

**Relevant original + site-downscaled companion rows:**

- MAR18 18:00: original `TA_F=13.899, VPD_F=14.210` => implied RH **10.456946%**; companion ERA RH **26.548804%**. At 18:30, original `TA_F=10.966,VPD_F=12.900` => RH **1.439602%**, companion RH **29.610616%**, Stage11l VPD **9.212859**; significant candidate boundary change but no independent tower evidence to declare it invalid.
- MAR23 08:30: source `VPD_F=14.315`, implied RH **4.026715%**; Stage11l VPD **14.315**. At 09:00 original `VPD_F=19.544` implied RH **−23.804519%** (nonphysical), and Stage11h/11l candidate `VPD=4.847608` yields companion **69.292073%**. The 9.467392 hPa jump existed before the 11-event Stage11l addition.
- MAR23 15:00: source VPD **18.501**, implied RH **8.209256%**, companion ERA RH **42.272878%**, Stage11l VPD **11.635263**. At 15:30: original and preserved VPD **16.448**, implied RH **19.351527%**, companion ERA RH **42.310841%**. Different provenance at adjacent half-hours likely contributes to the boundary contrast; not proof of an incorrect correction.
- MAR25 10:00: original VPD **19.128**, implied RH **3.868047%**, companion ERA RH **33.056177%**, Stage11l VPD **13.320248**. At 10:30 original VPD **20.786** implies **−0.333730% RH** (physically invalid), while existing Stage07/11h/11l VPD **19.179500** implies **7.420823% RH** versus ERA source **29.781172%**. The operator did NOT approve replacing this 10:30 Stage07-corrected value, and it is NOT one of the 11 newly selected timestamps.

**Interpretation:** Four residual VPD jumps do not independently prove Stage11l should be reversed or further smoothed. There are 3 introduced and 1 inherited boundary. Existing Stage07 QC choices and 11 added Stage11l user-approved trial method choices must be preserved pending science review. Underlying source instrument / source QC, dated clock metadata, tower-vs-grid humidity source provenance, and phase-consistent RH need further evidence. At minimum, distinguish true discontinuities from hybrid provenance transitions and inspect whether 2025 independent gridded ERA5-Land T/Td/P exists for US-NC2 and whether its time alignment is validated.

**Status:** numerical Stage11m inspection VERIFIED; **no new scientific repair approvals**; **Post-v5, DATM and spinup all zero**. Preserve SHA receipts and original Stage07/Stage11h/Stage11l output unchanged. The existing Stage11m result is **not** a need to rerun Stage11l or a signal to update the 11-event user decision ledger.
