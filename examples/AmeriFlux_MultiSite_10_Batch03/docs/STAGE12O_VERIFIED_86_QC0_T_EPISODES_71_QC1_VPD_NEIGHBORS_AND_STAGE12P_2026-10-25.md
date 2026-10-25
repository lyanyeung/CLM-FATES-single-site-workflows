# Stage12o VERIFIED — QC0 original tower temperature discrepancies persist; QC1 VPD edges require provenance analysis

**2026-10-25 09:04 UTC, IRIDIS6**: Git blob pinned Stage12o passed Python syntax, synthetic source test, source-SHA chained `--check`, and report-only `--run`. Its **new, isolated, SHA-receipted read-only report**:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12o_original_QC0_T_episodes_and_QC1_VPD_edges_20261025T090451Z_a15453b8/`

All **86** original source-native Stage12g holds (48 station/grid temperature discrepancy >5C; 38 VPD new-candidate neighbor jump >4 hPa) remain protected, as do the original 233 earlier physical source holds, all raw tower `TA_F`, pressure, original VPD QC, calendar and new research-shadow trial values. No source data, Post-v5, DATM, CIME, Slurm or spinup modification.

## Measured original station air-temperature persistence

The original Stage12n audit confirmed `TA_F_QC=0` for all 86 held source event times. Stage12o compared original native `TA_F` with original paired `TA_ERA` in full years 2015/2017/2022, NOT using the Stage12g ERA5-Land source grid as the temperature episode definition. A stage-relative temperature event was defined as **QC0 tower TA_F minus matched TA_ERA <= -5C** continuously for original consecutive half-hour periods.

| Group of previously temperature-held event times | N | Within cold QC0 native TA_F-vs-TA_ERA episode | At least 4 consecutive half-hours | At least 12 consecutive half-hours (6h) | Median overlapping run length for all held source events | Median source QC0 30-minute T jumps before/after |
|---|---:|---:|---:|---:|---:|---|
| US-Me6 2015 | 19 | 19 | **19** | **18** | 19 HH (9.5h) | 0.10 / 0.10 C |
| US-Me6 2017 | 10 | 6 | 6 | 6 | 16 HH (8h) | 0.295 / 0.400 C |
| US-NR1 2022 | 19 | 16 | 16 | **0** | 11 HH (5.5h) | 0.12 / 0.11 C |
| **Total** | **48** | **41** | **41** | **24** | — | — |

**Important:** the runs are counted as event-aligned held native half-hours, NOT as 24 distinct independent episodes. Source QC0 labels and smooth time steps plus multi-hour cold disparities argue against classifying these 48 as independent isolated single-timestamp sensor spikes. However sustained sensor offsets, native/paired source time uncertainty, mountain microclimates, and gridded representativeness have not been independently resolved: **no tower T replacement is authorised**.

Across full original years, QC0 tower minus native TA_ERA <=-5C occurred at **740/17,520** valid half-hours for US-Me6 2015, **1,005/17,482** for US-Me6 2017, and **1,648/17,507** for US-NR1 2022. Their full-year QC0 mean station-minus-TA_ERA discrepancies are near zero (+0.118, +0.062 and -0.014 C), so the temperature extremes are not evidence of a persistent whole-year offset.

## 76 distinct *sides*, 38 VPD-jump HOLD time events

| Source station | Original `VPD_F_QC=0` neighboring sides | Original `VPD_F_QC=1` neighboring sides | QC1 sides numerically equal to Stage12e VPD |
|---|---:|---:|---:|
| US-Me6 | 5 | **65** | **35/65** |
| US-NR1 | 0 | **6** | **4/6** |
| **Total** | **5** | **71** | **39/71** |

The **32/71 remaining QC1 sides do not numerically match original `VPD_F` and preserved Stage12e VPD**. A nonmatch *might* reflect finite differing values **or missing original/Stage12e values**; don't label the 32 as 32 proven erroneous readings, model-ready repairs or independent event counts. For the QC0 neighbors, all five original `VPD_F` and Stage12e values agree. Among 71 QC1 sides, **65** have finite final Stage12g neighbor VPD. Because Stage12g can mask jointly rejected neighbors, the final shadow is not a complete pre-rejection VPD chronology.

## Stage12p: classifying source provenance differences without changing the jump gate

The [Stage12p original QC1 neighboring VPD reference source-of-value classification](../scripts/stage12/12p_NR1_Me6_QC1_neighbor_provenance_at_jump_edges_READONLY.py) is **committed to GitHub but not yet run on IRIDIS6**. It verifies the exact Stage12o source report receipt **and each original SHA-sealed output file**, re-verifies the Stage12n source report, joins **76 uniquely keyed original source-native neighbor sides** across the two signed reports, and identifies five possible states:

- Original FLUXMET `VPD_F` and earlier Stage12e VPD both finite and equal
- Both finite but different
- Only original FLUXMET VPD finite
- Only preserved Stage12e VPD finite
- Both VPD values missing

The script then reports the originally rejected Stage12g candidate discrepancy against **three distinct references**: raw original `VPD_F`, older Stage12e VPD and final Stage12g VPD. It also distinguishes reference *sides* from original held events and reused neighboring timestamps. This diagnoses provenance only; it cannot prove a changed Stage12e VPD is wrong, prove a new ERA5-Land source VPD is correct or reconstruct all masked intermediate candidate transitions.

`--check` produces zero writes, and `--run` may create only a separate SHA-receipted source report. **All original 48 temperature/38 VPD holds and existing 14 Me6 RH research candidates stay unchanged; no original source forcing edits, threshold relaxation or model release.** Further US-NR1 year-source downloads remain paused pending source diagnosis.
