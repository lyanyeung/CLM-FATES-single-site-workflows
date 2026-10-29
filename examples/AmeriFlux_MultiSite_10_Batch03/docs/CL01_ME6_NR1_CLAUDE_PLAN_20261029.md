# US-Me6 and US-NR1: Claude workstream plan (CL01, 2026-10-29)

This responds to [the US-Me6 handoff](US_ME6_CLAUDE_DIFFICULT_SITE_HANDOFF_20261029.md) and [the US-NR1 handoff](US_NR1_CLAUDE_DIFFICULT_SITE_HANDOFF_20261029.md). The work is read-only: no shadow, forcing, Post-v5, DATM or Slurm change, and every prior approved edit is protected.

**Lesson from US-MtB.** The independent evidence came from the station's own BASE multi-sensor channels, not from further reanalysis tuning.

**Channels in the BASE height table (`BASE_MeasurementHeight_20260908`):**

| Site | BASE version | Temperature | Humidity | Other |
| --- | --- | --- | --- | --- |
| US-Me6 | 21-5 | `TA_1_1_1` (14.2 m), `TA_1_1_2`/`TA_1_1_3` (14 m) | `RH` (14 m) | `T_SONIC`; IRGA `H2O` at 14.2 m (LI-7500 open path, then LI-7200 closed path from 2014-10) |
| US-NR1 | 26-5 | three levels: 21.5, 8 and 2 m (HMP-35D/45D) | three levels: 21.5, 8 and 2 m | `VPD_PI` per level, plus any EC `H2O` |

For US-Me6, an IRGA water-vapour mole fraction is independent of the RH probe. This is the candidate new evidence for the 19 HH winter event, and the closed-path instrument works at −17 °C.

**[CL01](../scripts/claude/CL01_Me6_NR1_gap_ledger_BASE_evidence_decision_matrix_READONLY.py)** makes one pass per site and covers the handoff deliverables:

| Part | Content |
| --- | --- |
| A. Ledger | Every missing VPD_USE/QBOT HH in the latest signed shadow (Me6 Stage13AI: 45; NR1 Stage13P: 234; the run stops if the count differs), with original QC, companion ERA, episode and anchors. |
| B. BASE sources | RH and IRGA H2O at each gap. |
| C. Validation | Each source is checked against FLUXMET QC0 truth: Stage12j gates per year and pooled, with a cold subset and a \|dT\| > 5 °C subset. |
| D. Classification | One per HH, using the handoff classes MEASURED_SUPPORTED, ERA_RH_SENSITIVITY_ONLY, PHYSICS_CONFLICT_HOLD and EVIDENCE_INSUFFICIENT_HOLD. A temperature-source flag is added where the gap-filled TA_F disagrees with a BASE measured temperature by more than 3 °C. |
| E. Root cause | Breakdown by year, which covers NR1 2001/2018/2021. |
| Episodes | Each episode lists the evidence that would change its decision. |

Without the BASE file, CL01 still produces the ledger and reanalysis-only classes. BASE files are required at:
- `sites/MY_EC_SITE/US-Me6/forcing/raw/AMF_US-Me6_BASE_HH_21-5.csv`
- `sites/MY_EC_SITE/US-NR1/forcing/raw/AMF_US-NR1_BASE_HH_26-5.csv`

`--base` can point elsewhere.

## First IRIDIS `--check`, v1 (2026-10-29 04:17)

| Site | MEASURED_SUPPORTED | ERA_RH_SENSITIVITY_ONLY | PHYSICS_CONFLICT_HOLD | Total gaps |
| --- | --- | --- | --- | --- |
| US-Me6 | 0 | 27 | 18 (13 of the 19 HH winter event) | 45 |
| US-NR1 | 65 (8 m RH 50, 2 m RH 15) | 81 | 88 (1998: 43, 2009: 28) | 234 |

**US-Me6.** BASE RH passes validation (MAE 0.22 hPa, 16/16 years), but it is present at none of the 45 gaps. IRGA H2O passes pooled but only 9/13 years, and it is present at only 3 gaps (1 of the 19 HH).

**v2 change.** v2 adds `ERA:COMPANION_E` and `ERA:COMPANION_RH` to the validation table, so that reanalysis-only rows carry each site's own QC0 error. They are never classed as measured. v2 also prints the HOLD rows with the BASE and sonic temperatures.
