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

## CL02 `--run` results (2026-10-29 04:33, commit 3776753)

Reports:
- `reports/cl02_US-Me6_alternatives_decision_20261029T043239Z_873b540f`
- `reports/cl02_US-NR1_alternatives_decision_20261029T043321Z_89ce56f5`

Methods:
- CEC: COMPANION_E capped at DATM saturation.
- EMP: block-excluded QC0 RH climatology.
- SAT: DATM saturation.
- MEAS: validated BASE level transfer.

**QC0 validation by tower-T bin** (MAE in hPa; ✓ means the bin passes all five gates with N ≥ 100):

| T bin | Me6 CEC | Me6 EMP | NR1 CEC | NR1 EMP |
| --- | --- | --- | --- | --- |
| ≤ −15 | 0.45 ✓ | 0.05 ✓ | 0.79 ✗ | 0.14 ✓ |
| −15:−10 | 0.47 ✓ | 0.12 ✓ | 0.78 ✗ | 0.28 ✓ |
| −10:−5 | 0.54 ✓ | 0.24 ✓ | 0.79 ✗ | 0.53 ✓ |
| −5:0 | 0.69 ✓ | 0.51 ✓ | 0.76 ✓ | 0.88 ✓ |
| 0:5 | 0.69 ✓ | 0.81 ✓ | 0.81 ✓ | 1.06 ✗ |
| 5:15 | 0.92 ✓ | 1.39 ✗ | 1.19 ✗ | 1.81 ✗ |
| > 15 | 1.31 ✗ | 2.50 ✗ | 1.52 ✗ | 1.91 ✗ |

**Predeclared recommendation counts:**

| Site | MEAS | EMP | CEC | HOLD | Total |
| --- | --- | --- | --- | --- | --- |
| US-Me6 | 0 | 27 | 11 | 7 | 45 |
| US-NR1 | 65 | 83 | 70 | 16 | 234 |

**Me6.**
- The 19 HH winter event goes to EMP: VPD 0.28–0.32 hPa against ice saturation 0.24–0.25, so just below ice saturation.
- 2017-01-05 (4 HH) and 2017-12-23 (4 HH) also go to EMP. There CEC is far too dry: the companion is about 10 °C colder than the tower.
- The 7 HOLD rows are all isolated single HH in summer at 17.7–24.5 °C.

**NR1.**
- **1998.** Jan–Oct 1998 is 100 % ERA-filled for TA, VPD, SW and LW, and BASE has no data. November is 67 % measured and December is 100 % measured, so the tower started in Nov 1998. All 43 gaps in 1998 have reanalysis tower T.
- **2004-12-03 22:30–23:30 root cause.** The companion ERA record is corrupt: TA_ERA is −111.7, −216.8 and −111.8 °C, and PA_ERA = PA_F is 30.87, −8.20 and 30.86 kPa. VPD_F is QC0 (3.19–3.45 hPa), and the independent 2 m RH gives 3.28–3.53 hPa.
- **HOLD rows.** All 16 are 1–3 HH warm-season gaps in the 5:15 bin. They fall in 2001-06-15, 2002, 2010, 2012, 2017-06-30, 2018-05-20 and 2021-06-21.
