# Batch03 Stage11l VERIFIED: +11 US-NC2 RH-only additions; event-boundary science HOLD

**Verified on IRIDIS6 2026-10-24:** user-provided terminal output includes SHA-pinned source download, Python syntax PASS, Stage11l self-test PASS, `--check` PASS and `--run` PASS. A single new unapproved research shadow forcing was generated; no original Stage07/Stage11h, CIME, DATM or Slurm changes occurred.

**Exact Stage11l isolated science trial directory:**
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage11l_US-NC2_humidity_only_20261024T100319Z_31a4697e/`

**Only US-NC2 was regenerated.** US-MOz and US-Mpj refer to unchanged SHA-verified Stage11h original shadow CSVs.

## Event-level outcomes

| Item | Verified Stage11l outcome |
| --- | --- |
| Original Stage11f user selections | 62/62 retained |
| Previous selected ERA-RH replacement targets | 53/53 preserved |
| Newly selected US-NC2 neighbour targets | 11/11 recomputed at exact source-native half-hour timestamps |
| Cumulative distinct ERA-RH target times | **64** |
| Actually changed US-NC2 VPD values relative to Stage11h among new targets | **11/11** |
| Temperature `TA_USE` and `TBOT` | **unchanged at all 367,920 US-NC2 half-hours** |
| Site pressure, radiation, wind and precipitation | Unchanged |
| Modified new-record fields | `VPD_USE` and derived `QBOT` only |
| Formal scientific acceptance / Post-v5 / DATM / spinup | 0 / 0 / 0 / 0 |

The source companion **ERA5 `TA_ERA` and `VPD_ERA` are used solely to infer an ERA5 relative humidity fraction**. Humidity `VPD` and `QBOT` are then reconstructed at the retained **EC tower `TA_USE`** and existing site `PSRF`. **ERA5 air temperature does not replace EC tower temperature**. The source is site-downscaled release-paired ERA5, *not independently validated ERA5-Land gridded dewpoint*.

## Changes from Stage11h, exactly 11 native US-NC2 events

| Source-native time | Source original VPD QC | Source original RH (%) | Companion ERA RH (%) | Previous Stage11h VPD (hPa) | New Stage11l VPD (hPa) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2025-03-18 18:30 | 2 | 1.439602 | 29.610616 | 12.900000 | 9.212859 |
| 2025-03-18 19:30 | 2 | 9.885344 | 38.456384 | 9.496000 | 6.485273 |
| 2025-03-23 13:00 | 1 | 4.008103 | 46.663477 | 20.621000 | 11.457763 |
| 2025-03-23 13:30 | 1 | 4.260106 | 45.411435 | 20.779000 | 11.847682 |
| 2025-03-23 14:00 | 1 | 2.957143 | 44.241710 | 21.585000 | 12.402177 |
| 2025-03-23 14:30 | 1 | 2.269952 | 43.243128 | 20.785000 | 12.070920 |
| 2025-03-23 15:00 | 1 | 8.209256 | 42.272878 | 18.501000 | 11.635263 |
| 2025-03-25 08:00 | 1 | 9.424788 | 64.015516 | 15.227000 | 6.049511 |
| 2025-03-25 08:30 | 1 | 8.143003 | 56.206412 | 16.424000 | 7.830279 |
| 2025-03-25 09:30 | 1 | 6.697019 | 40.455124 | 17.982000 | 11.475903 |
| 2025-03-25 10:00 | 1 | 3.868047 | 33.056177 | 19.128000 | 13.320248 |

## Remaining high-impact adjacent half-hour jumps: review BEFORE approval

The previously large Stage11h jumps of 2025-03-23 12:30→13:00 (**9.761→0.598 hPa**) and 2025-03-25 09:00→09:30 (**8.651→2.145 hPa**) improved significantly in the new candidate, but other discontinuities remain or were introduced.

| Source-native half-hour boundary | Stage11h absolute VPD jump (hPa) | Stage11l absolute jump (hPa) | New minus old (hPa) | Interpretation |
| --- | ---: | ---: | ---: | --- |
| **2025-03-23 08:30→09:00** | **9.467392** | **9.467392** | 0 | Pre-existing high jump; Stage11l made no change at this boundary |
| **2025-03-25 10:00→10:30** | **0.051500** | **5.859252** | **+5.807752** | Newly introduced large jump; 10:30 has a previously Stage07-corrected candidate VPD; do not silently change it |
| **2025-03-18 18:00→18:30** | **1.310000** | **4.997141** | **+3.687141** | Newly increased event start jump |
| **2025-03-23 15:00→15:30** | **2.053000** | **4.812737** | **+2.759737** | Newly increased event end jump |

The original source VPD can be numerically positive yet imply *nonpositive actual water vapour pressure*, so compare `e_s(T)-VPD` and RH as well as VPD itself at each boundary endpoint. The significance of these jumps cannot be judged by smoothness alone: the paired ERA downscaling, instrument QC, native timestamp and tower-vs-grid height/elevation remain unverified independent science concerns.

Stage11l's reported **six outer event boundaries** include a 2025-03-25 event ending at 10:30; thus its `AFTER` check concerns 10:30→11:00 and **does not replace separate scrutiny of the changed 10:00→10:30 transition**. The output `11_new_target_adjacent_jump_changes.csv` does surface this +5.807752 hPa introduced jump.

## Full-year effect of 11 added records only (US-NC2, 2025)

`half_hours=17,520`, `yearly_mean_VPD_change_hPa=-0.004546`, `yearly_mean_RH_change_percentage_points=+0.024114`, `yearly_mean_QBOT_change_kgkg≈+0.000003` compared with the Stage11h candidate. Small annual shifts are NOT evidence that all half-hour humidity episodes and transitions are scientifically accurate.

## Next: Stage11m SHA-protected four-boundary context audit

Audit the **four boundary transitions**, jointly inspect their raw source `TA_F/VPD_F` and QC, original implied water RH, companion `TA_ERA/VPD_ERA` RH and existing Stage07/Stage11h/Stage11l VPD (and unchanged EC tower TA) in **native ±2-hour context**. Determine whether the boundary endpoint was already Stage07-corrected or Stage11h/11l-changed, and whether a physical issue remains. Do not authorize any further time-step repair automatically.

The existing Stage07 and Stage11h files and receipts and new Stage11l output must remain SHA-protected and `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marked. Full Post-v5 and model authorization remain zero. The seven other Batch03 sites and their separate humidity science blockers are unaffected.
