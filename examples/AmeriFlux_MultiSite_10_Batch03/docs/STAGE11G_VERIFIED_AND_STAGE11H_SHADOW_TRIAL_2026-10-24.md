# Batch03 — Stage11g VERIFIED 62-decision science method audit (24 October 2026)

**Evidence:** operator-provided IRIDIS6 `--self-test`, `--check` and `--run` all **PASS**. The source input SHA/Stage07 lineage and VPD/QBOT consistency were independently rechecked at all 62 exact native source times. No sources or forcing were modified by Stage11g.

**Sealed Stage11g report on IRIDIS6:**
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage11g_user62_ERA5_method_validation_20261024T082933Z_fcaf26d1/`

### Original human-choice census

| Site | Keep Stage07 TA | ERA5-based VPD method selected | Keep Stage07 VPD | Total unique |
| --- | ---: | ---: | ---: | ---: |
| US-MOz | 1 | 0 | 0 | 1 |
| US-Mpj | 1 | 4 | 1 | 6 |
| US-NC2 | 4 | 49 | 2 | 55 |
| **Total** | **6** | **53** | **3** | **62** |

All three "keep existing Stage07 VPD" choices retained exact user-specific existing candidates:

| Site / original native time | Stage07 VPD (hPa) | Stage07 RH over water (%) | Stage07 QBOT (kg/kg) |
| --- | ---: | ---: | ---: |
| US-Mpj / 2014-10-21 08:30 | 2.103106 | 81.078718 | 0.007181 |
| US-NC2 / 2025-03-22 01:30 | 2.949241 | 58.707942 | 0.002581 |
| US-NC2 / 2025-03-27 07:30 | 1.927236 | 79.775808 | 0.004648 |

## ERA5 VPD versus ERA RH transferred to tower T

Both comparison methods use the **source release's exact-time FLUXNET site-downscaled ERA5 companion** `TA_ERA` and `VPD_ERA`. They have **NOT** validated an independently downloaded ERA5-Land grid `T2m`/`Td2m` product.

| Method at the 53 user-chosen events | Numeric physical pass | Numeric physical fail | Science status |
| --- | ---: | ---: | --- |
| Directly assign source companion `VPD_ERA` while retaining Stage07 site `TA_USE` | **46 / 53** | **7 / 53** | Not accepted as production method |
| Infer source ERA water-relative RH and transfer that RH fraction to retained Stage07 `TA_USE`, then compute `VPD_USE` and `QBOT` using Stage07 `PSRF` | **53 / 53** | **0 / 53** | Numeric-screen success only, pending scientific/source accuracy review |

The numeric comparison alone **does not demonstrate** that the site-downscaled ERA humidity is closer to tower measurements, or that the source native clock, grid elevation and tower measurement height agree. Direct VPD cannot be assumed to correspond to a different retained temperature; the seven direct-copy physical failures demonstrate this in the selected 53 records.

A precise expression for the **research candidate RH transfer** (not official approval):

`RHfrac = (es_water(TA_ERA) - VPD_ERA) / es_water(TA_ERA)`, with `0 < RHfrac <= 1`;

`VPD_trial = es_water(TA_stage07) * (1 - RHfrac)`;

`QBOT_trial = 0.622 * ea_trial_Pa / (PSRF_stage07 - 0.378*ea_trial_Pa)`, where `ea_trial_Pa = 100 * es_water(TA_stage07) * RHfrac`.

No automatic RH clipping or 1% floor. Never mix grid and source native timestamps by row number.

## Stage11h: isolated, explicitly UNAPPROVED research forcing trial

[Stage11h source code](../scripts/stage11/11h_isolated_ERA_RH_three_site_science_trial.py) has been committed but is **NOT YET RUN ON IRIDIS6**. It uses Stage11g's SHA-sealed per-event mathematical preview, the final GitHub 62-event decision ledger and SHA-sealed Stage07 processed_v5 forcing to create **three standalone shadow CSVs** under a new `science_trials/stage11h_companion_ERA_RH_shadow_*/` location. This is an intentionally isolated research comparison rather than the official `processed_v5` or an accepted `Post-v5` forcing product.

Safety checks and contents:
- Reverify Stage11g receipt and every output file SHA, source Stage07 input/forcing hashes, original NO_LEAP 30-minute timeline, 998,640 combined site rows, 62 unique decision IDs and 6/53/3 event class counts.
- Retain the **six original QC0 air-temperature interpolations** and **three existing Stage07 VPD candidates** exactly.
- At only the selected **53 VPD event IDs**, compute companion ERA RH transferred to the retained site TA, and recompute QBOT with retained Stage07 pressure; **ALL other meteorological values/times unchanged numerically**.
- Report how many among the 53 VPD values actually differ from Stage07, absolute VPD/QBOT impacts, maximum adjacent VPD jump, minimum RH, and full-site numerical QA.
- `--check` is read-only. `--run` writes only **new shadow trial** files, places `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` **before** writing CSVs, emits a per-event diff and an output SHA receipt, and never clears the Stage07 hold.
- Not a final Post-v5 acceptance; **no model job, site PFT, CO2 or DATM output is authorized** by Stage11g/11h.

## Scientific next decisions after Stage11h

Compare the isolated trial to Stage07 for all three sites, including yearwise means and RH/VPD/QBOT distributions; scrutinize the 7 cases where directly copying companion VPD was inconsistent and any VPD boundary discontinuities from the RH-transfer shadow trial. Confirm tower/source clock metadata and height/elevation, assess bias and independent observations, and review non-target Stage07 changes before final acceptance. These issues are separate from the **1,924 other source humidity blockers** in the remaining seven Batch03 stations.

**Status as of this record:** 62/62 *user method directions* recorded; 53/53 ERA-RH transfer **numerically feasible**, **0/53 formally scientifically accepted**, 0 Post-v5 approvals, 0 DATM-ready sites, 0 spinup authorizations. Source Stage07/11f and SHA reports stay unchanged.
