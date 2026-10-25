# Stage12n VERIFIED — raw tower TA_F_QC=0 at all 86 original US-Me6/US-NR1 RH holds

**2026-10-25 08:52 UTC on IRIDIS6:** Stage12n Python syntax, self-test, signed-source `--check` and report-only `--run` all PASSED. Full upstream Stage12m/Stage12g provenance and 86 original native held time IDs were preserved. Original SHA-receipted READ-ONLY report:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12n_NR1_Me6_original_T_VPD_QC_and_companion_TA_ERA_20261025T085220Z_39e37c1b/`

The prior Stage12g new-source RH proposal population remains **100 source event times**, **14 US-Me6 numerical research-only RH/QBOT candidates** and **86 science HOLDs** (US-Me6: 29 gridded-site T >5°C, 35 adjacent VPD >4hPa; US-NR1: 19 T, 3 VPD). The original Stage12b 233 science holds and all original source temperature, pressure, VPD, relative time, QC and code remain untouched. No Post-v5, DATM or spinup release.

## Observed temperature QC and paired-ERA comparison

**All 86 original held native events have raw FLUXMET `TA_F_QC=0`.** This is a high-quality source QC designation, NOT grounds to overwrite or simply reject measured tower T because reanalysis is warmer. For the 48 rejected due to raw tower-vs-ERA5-Land >5°C source T:

| Held site/year | N | Median raw tower TA_F minus original paired TA_ERA | Median raw tower TA_F minus gridded ERA5-Land T2m | Median gridded ERA5-Land minus native paired TA_ERA |
|---|---:|---:|---:|---:|
| US-Me6 2015 | 19 | **-9.472°C** | **-11.165°C** | +1.651°C |
| US-Me6 2017 | 10 | **-5.826°C** | **-5.601°C** | +0.961°C |
| US-NR1 2022 | 19 | **-5.563°C** | **-7.898°C** | +2.425°C |

Whole-year raw measured QC0 native source tower-versus-paired TA_ERA MAE is **2.331°C** (US-Me6 2015), **2.456°C** (Me6 2017), **3.136°C** (NR1 2022). These are YEAR-wide references, distinct from the subset medians above, and are not proof that original tower measurement is in error. `TA_ERA` and gridded ERA5-Land are not two independent EC tower sensors.

## Original VPD-neighbor QC0 vs QC1

Stage12n opened exactly two adjacent native half-hours for each **38 VPD jump HOLDs**. Among the **76 adjacent sides**:

| Site | VPD neighbor sides with original `VPD_F_QC=0` | Sides with `VPD_F_QC=1` |
|---|---:|---:|
| US-Me6 (35 holds × 2) | **5** | **65** |
| US-NR1 (3 holds × 2) | **0** | **6** |
| **Total** | **5** | **71** |

A *side* is not a unique time or independent measurement. FLUXMET `VPD_F_QC=1` indicates the source's filled/classified reference rather than verified QC0 measured VPD; it is important NOT to assume all such values are erroneous or to loosen Stage12g's >4hPa continuity HOLD. In the previously sealed final shadow, 38 original rejected source candidates still differed from at least one preserved finite neighbor by >4hPa; this supports conducting a source-quality/continuity audit, NOT immediate candidate acceptance.

## New Stage12o: temporal consistency and source-neighbor provenance only

The [Stage12o read-only signed QC0 tower temperature episode and QC1 VPD neighbor audit](../scripts/stage12/12o_NR1_Me6_QC0_cold_episodes_and_QC1_VPD_edges_READONLY.py) has been committed to GitHub, but **not yet run on IRIDIS6**. It SHA-verifies the exact Stage12n report receipt and six output tables, then reuses its original upstream Stage12m/Stage12g validated source metadata.

For the 48 original temperature HOLDs it reads original native half-hour `TA_F`, `TA_F_QC`, paired native `TA_ERA` for 2015/2017/2022 (no leap year). It checks whether tower temperature >5°C COLDER than paired native ERA persists for 1, >=4 or >=12 successive originally measured QC0 half-hours, and contextualizes the events with original 6-hour before/after window and **original QC0 tower temperature steps**. This can distinguish isolated sudden source temperatures from multi-hour local anomalies; neither category validates a clock shift or sensor defect. It does NOT change the Stage12g grid T difference rule or assign a new tower T.

For **76 original VPD neighbor sides**, it checks original FLUXMET `VPD_F_QC` and values against preserved Stage12e VPD and finite final Stage12g shadow. This clarifies whether **QC1** native-source reference and Stage12e prior scientific humidity are numerically the same, but cannot make QC1 an independent ground truth or prove the >4hPa rejected proposal was acceptable. **No humidity candidate generated**; all 86 original science HOLDs remain.

Stage12o `--check` no-write; `--run` creates only a new isolated SHA-receipted report. No source download, VPD/QBOT/TA/pressure clock edits, Post-v5/DATM/CLM/CIME/Slurm or spinup.
