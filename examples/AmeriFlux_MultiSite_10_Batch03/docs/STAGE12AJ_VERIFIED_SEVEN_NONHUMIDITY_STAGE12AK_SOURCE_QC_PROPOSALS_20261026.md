# Stage12aj verified 2026-10-26 03:06 UTC — Kon & NR1 PSRF/FLDS corrupt source values

**IRIDIS6 operator evidence:** pinned Stage12aj SHA/AST, self-test, --check, and --run all PASS. Read-only SHA-sealed report: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12aj_7_selected_nonhumidity_exact_native_source_QC_20261026T030647Z_344ecbba/`.

## Exact corrupt original source values

| Site | Native timestamp | Selected source field missing | Published native source value | Source QC |
|---|---|---|---:|---:|
| US-Kon | 2004-12-03 23:30 | PSRF (Pa) | PA_F=49.156 kPa | 2 |
| US-Kon | 2004-12-04 00:00 | PSRF (Pa) | PA_F=1.768 kPa | 2 |
| US-Kon | 2004-12-04 00:30 | PSRF (Pa) | PA_F=49.139 kPa | 2 |
| US-NR1 | 2004-12-03 22:00 | FLDS (W m-2) | LW_IN_F=22.869 W m-2 | 2 |
| US-NR1 | 2004-12-03 22:30 | PSRF (Pa) and FLDS (W m-2) | PA_F=30.871 kPa; LW_IN_F=22.869 W m-2 | 2 / 2 |
| US-NR1 | 2004-12-03 23:00 | PSRF (Pa) | PA_F=-8.200 kPa | 2 |
| US-NR1 | 2004-12-03 23:30 | PSRF (Pa) | PA_F=30.859 kPa | 2 |

**Strong evidence of contamination propagation:** US-Kon 49.156 kPa = (96.544 + 1.768)/2; 49.139 = (1.768 + 96.510)/2, exactly; NR1 30.871 = (69.942 + (-8.200))/2 and 30.859 is the 0.001 kPa rounded mean of -8.200 and 69.917. Hence each pressure outage consists of one physically impossible extreme negative/barely positive **QC2 ERA-filled** datum with adjacent corrupted averages. The source numeric QC2 indicator labels provenance, **not observed instrument QC0 validity**. Both longwave 22.869 are unrealistic versus original source valid previous 191.629 and subsequent 191.440 W/m2 during tower -2C conditions.

## Evidence-based short native time interpolations, proposal only

| Site | Native time | Field | Original invalid unit | Interpolated research candidate |
|---|---|---|---:|---:|
| US-Kon | 200412032330 | PSRF | 49.156 kPa | **96535.5 Pa** |
| US-Kon | 200412040000 | PSRF | 1.768 kPa | **96527 Pa** |
| US-Kon | 200412040030 | PSRF | 49.139 kPa | **96518.5 Pa** |
| US-NR1 | 200412032230 | PSRF | 30.871 kPa | **69935.75 Pa** |
| US-NR1 | 200412032300 | PSRF | -8.200 kPa | **69929.5 Pa** |
| US-NR1 | 200412032330 | PSRF | 30.859 kPa | **69923.25 Pa** |
| US-NR1 | 200412032200 | FLDS | 22.869 W/m2 | **191.566 W/m2** |
| US-NR1 | 200412032230 | FLDS | 22.869 W/m2 | **191.503 W/m2** |

US-Kon linear pressure anchors: 200412032300=96.544kPa, 200412040100=96.510kPa; original T fields retained. US-NR1 pressure anchors: 200412032200=69.942kPa, 200412040000=69.917kPa; downwelling LW anchors: 200412032130=191.629 and 200412032300=191.440 W/m2. Source-native 30-minute time unchanged. All anchors and corrupt interior native values verified against exact signed original Stage07 source on execution, not just the rounded values in this document.

### Status and next procedure

User has **NOT separately signed these eight non-humidity replacements**; only research candidates are allowed without that approval. [Stage12ak evidence-gated original source SHA-scoped script](../scripts/stage12/12ak_Kon_NR1_seven_nonhumidity_pressure_longwave_SCOPED_TRIAL.py) is committed at Git commit `151de58353def508780ca497723b6bd4c1ce62c7`, Git blob `6c91b342009b3308fabbb42ed75504f3162540db`; it was **not yet tested on operator's IRIDIS6** when written. `--check` revalidates original Stage12ai/12aj receipts, original immutable native Stage07 tower source SHA and exact QC2 source anchors, pressure and longwave physics, exact 8-variable/7-native-time masks, and unchanged QBOT/VPD. `--trial` additionally writes only two **INCOMPLETE / NOT OPERATOR APPROVED** research trial CSVs (Kon source successor to Stage12ah, NR1 to Stage12af) + event provenance and SHA receipt. This **does not overwrite** previously approved research shadows or create production forcing.

Original Stage12ai: six-site VPD/QBOT missing=3788, nine-site any-variable missing=3789. The seven non-humidity gaps include exactly one additional time row otherwise complete (NR1 200412032200). If and only if Stage12ak validates and the user subsequently approves science replacement, numerical nonhumidity gaps would become 0 Kon / 0 NR1; total nine-site rows with any source NaN would fall to 3788, while VPD/QBOT missing remain 3788. No Post-v5, DATM, CIME, spinup authorization. Further six-site VPD source HOLD and unresolved Me2 clock remain.
