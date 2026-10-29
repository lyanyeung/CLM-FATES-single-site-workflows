# US-Kon — Stage14K ACTUAL operator result and Stage14L QC-constrained next action (2026-10-29)

## Stage14K was successfully executed on IRIDIS6

Operator reported **SYNTAX PASS**, exact source receipt validation and **68/68 ERA-RH-transferred VPD_USE/QBOT research candidate source native HH inserted** into a *new independent, research-only* 280320-row selected model-tape CSV. Stage12AY original had 77 missing native VPD/QBOT pairs; new research tape has **exactly 9 missing science-protected pairs**. All original non-68 fields/source and 9 protected original native keys unchanged. All newly rebuilt 68 water/QBOT/TBOT physical closure pass, and 0 existing selected complete-source thermodynamic numerical failures under program checks.

Actual Stage14K isolated output:
\`\`\`
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/US_Kon_68_ERA_RH_9HARD_HOLD_SCENARIO_20261029T044949Z_ebbfd739
\`\`\`

Signed parent Stage12AY source SHA256 \`c13c1f91caca0f2323df08f5075b69b3aff6e60083913e9456d95cbdfc808b31\`. Stage14J 77-row original source/QC ledger SHA256 \`1de96fd47ebddcd16b86b71741c4e7127ae50bfca0249412821a3d2689b43e3d\`.

## Why numerical completion is not scientifically finished

Out of **112** original source-episode 30-minute joins, the new Stage14K source had **62 flagged transitions**, including **43 VPD delta>4 hPa**, **18 RHwater delta>20 percentage points**, and **8 QBOT delta>0.003 kg/kg**. These overlap; the totals are NOT 69 distinct source hours. Nine protected missing original scientific source holds explain some of the 62 flagged edges but NOT all.

Examples:
- 2012-08-04 09:00–09:30 / 09:30–10:00: **23.53 / 23.25 hPa** VPD jumps; RH +32.8–34.4pp; QBOT 0.00465–0.00534.
- 2015-09-06 17:30–18:00 and 19:30–20:00: **16.78 / 11.00 hPa**, RH +42.97–44.73pp, QBOT 0.00612–0.00717.
- 2011-09-28 16:30–17:00: **12.08 hPa** VPD, 37.04pp RH, QBOT 0.005436.
- 2014-01-25 01:00–06:30 original 12HH block: only one VPD >4 hPa external edge (max 4.879982), all 12 centres numerically physical, but **not observed tower RH**.

Science: positive e and thermodynamic equation closure at a formerly missing centre DO NOT certify that the original adjacent QC1 MDS, QC2 ERA-derived, or mixed-source values are mutually consistent with the transplanted RH. The entire 68-rebuilt tape is **NOT approved** for Post-v5, DATM, AD400, Normal400 or Slurm. It must not be made "ready" by clipping/washing QC warnings to zero.

Protected original nine missing (strictly unchanged):
\`201102220830\`, \`201102220900\`, \`201102220930\`, \`201105261100\`, \`201109291830\`, \`201110150730\`, \`201110230730\`, \`201202251030\`, \`201208050900\`.

## Exact next ONE Stage14L research-only source/QC treatment

[Stage14L original-QC-aware connected neighbour ERA-RH *sensitivity* script](../scripts/stage14/14l_US_Kon_68_QC_neighbor_connected_ERA_RH_sensitivity.py), **not executed on IRIDIS6** as of this record. Input: signed actual Stage14K 68+9 tape, Stage14J source science ledger, immutable Stage12AY source and exact original published tower FLUXMET plus paired ERA.

It evaluates adjacent finite original source values only when their actual source \`VPD_F_QC\` is **1 or 2**, the selected value numerically still equals its published original \`VPD_F\` within 1e-5 hPa (guarding earlier historical pre-approved/numerically modified values), original paired ERA temperature and selected original tower T differ by no more than 5°C, physical water/ice T/e/VPD/QBOT all pass, and the substitute **strictly decreases the warning count at its immediate interface**. Extend toward 48 finite QC1/QC2 neighbours maximum per distinct original missing episode; do not cross original measured VPD QC0, hard HOLDs, unrelated missing, source-year time gaps, or prior source-modified values. No original TA/TBOT, pressure, radiation, precipitation or time field changes. Retain the original 68 research fills and all 9 source missing keys, and generate an additional independently versioned research *alternative*, not a promoted actual tower observation.

Reports **matched before/after warning counts at all 68 original candidate-contact joins**, plus all extended-edge warnings, actual QC names and each proposed original-finite neighbour replacement. If this method cannot improve source science without crossing QC0 or approved inputs, do not invent a temperature/humidity correction merely to pass thresholds. Reanalysis-to-reanalysis or derived-QC2 continuity is not independent validation.

**No automatic production approval**, no rewrite of previous successful source or model jobs. The user will review actual number of proposed neighbour edits, exact still-flagged groups and method limits, then decide whether to retain alternative or keep earlier Stage14K as uncertain research sensitivity.
