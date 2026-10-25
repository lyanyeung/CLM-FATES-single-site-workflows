# Batch03 Stage12q v2 VERIFIED: QC1 VPD provenance at 38 rejected source times

**IRIDIS6 operator result: 2026-10-25 09:35 UTC.** Pinned Stage12q v2 SHA and syntax, `--self-test`, `--check`, and `--run` PASS. The source-only SHA-receipted report is:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12q_76_original_VPD_edge_CDEG_lineage_20261025T093514Z_044390c3/`

The exact signed **76 immediate sides / 38 original native VPD-jump HOLD events** reproduce. Original 71 QC1 and 5 QC0 immediate sides are preserved, along with 48 additional tower/grid T HOLDs (86 in total), original 233 prior physics holds and all tower T/P/native clock.

## Stage12q v2 result, scientific interpretation

| Station | Original source-QC | Original RAW vs Stage12e | Provenance of retained Stage12e value | Sides |
| --- | --- | --- | --- | ---: |
| US-Me6 | QC0 | both finite match | Stage12c raw/companion baseline | 5 |
| US-Me6 | QC1 | both finite differ | **Stage12d matched companion ERA RH-only candidate** | **22** |
| US-Me6 | QC1 | both finite match | Stage12c raw/companion baseline | 35 |
| US-Me6 | QC1 | raw-only finite | Stage12e missing / no retained VPD | **8** |
| US-NR1 | QC1 | both finite differ | **Stage12d matched companion ERA RH-only candidate** | **2** |
| US-NR1 | QC1 | both finite match | Stage12c raw/companion baseline | 4 |

Exactly **24 original QC1 source sides** have different but finite candidate values introduced by Stage12d, NOT by Stage12e. The other **8 original raw-finite QC1 sides** are missing in Stage12e; this is a state, not evidence that Stage12e deleted a finite value. Stage12g has a finite final VPD for **2 of the 8** previously missing sides; the others remain final-shadow missing. Among the 24 different finite sides, comparison of the Stage12g-rejected hypothetical VPD to raw source exceeds 4 hPa at 23 sides, while comparison to preexisting Stage12e value exceeds 4 hPa at only 4 sides. Such alternative-reference sensitivity is diagnostic and cannot establish the correct reference or license threshold relaxation.

The 76 are **neighbor sides, not 76 independent source times**: 3 neighbor native timestamps were reused in the 76 sides. Numerical matches to a QC1 / ERA-derived product do not make that reference an independent observed-QC0 VPD.

## Next: Stage12r root-cause science audit

Examine each of the 32 original QC1 mismatch sides at original source times. Reconstruct **why Stage12c left its VPD missing** using *original published* FLUXMET VPD/TA and original companion TA_ERA/VPD_ERA, the unchanged Stage12c site TA/pressure, Stage12c hard bounds and water saturation/QBOT validity. Confirm the 24 later Stage12d numbers against the original paired companion-ERA RH transfer formula (matched native time, fixed site T/P); for the eight still missing at Stage12e, expose the exact signed Stage12d and Stage12e rejection reasons and distinguish any later Stage12g isolated research candidates.

No raw-source values may be altered or treated as ground truth simply because `VPD_F_QC=1`; no model/DATM/Post-v5/spinup approval, and keep original >4 hPa discontinuity and tower-grid >5 C guards. Stage12r must generate reports **only**; it is not yet executed on IRIDIS6.
