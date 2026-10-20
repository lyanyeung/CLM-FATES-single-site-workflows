<!-- IRIDIS_LIVE_20261020_LATEST_START -->
## Latest IRIDIS6 run snapshot — 20 October 2026 (11 sites)

| Site | Archived years / target | Remaining model years | Latest coordinated checkpoint | `RESUBMIT` | Slurm snapshot | Job IDs (as reported) |
| --- | ---: | ---: | --- | ---: | --- | --- |
| BE-Bra | 1000 / 1000 | 0 | `2996-01-01-00000` | 0 | **COMPLETE** | — |
| FR-Fon | 1000 / 1000 | 0 | `3005-01-01-00000` | 0 | **COMPLETE** | — |
| GL-ZaH | 1000 / 1000 | 0 | `3000-01-01-00000` | 0 | **COMPLETE** | — |
| IT-Noe | 5 / 1000 | 995 | `2009-01-01-00000` | 198 | **IDLE** | — |
| AT-Neu | 1000 / 1000 | 0 | `3002-01-01-00000` | 0 | **COMPLETE** | — |
| FI-Sod | 1000 / 1000 | 0 | `3001-01-01-00000` | 0 | **COMPLETE** | — |
| CH-Aws | unknown / 1000 | unknown | `NO_ARCHIVE` | 199 | **IDLE** | — |
| CH-Cha | 1000 / 1000 | 0 | `3005-01-01-00000` | 0 | **COMPLETE** | — |
| CH-Fru | 1000 / 1000 | 0 | `3005-01-01-00000` | 0 | **COMPLETE** | — |
| CH-Lae | 1000 / 1000 | 0 | `3004-01-01-00000` | 0 | **COMPLETE** | — |
| CZ-Stn | 1000 / 1000 | 0 | `3010-01-01-00000` | 0 | **COMPLETE** | — |

**Summary:** **9 COMPLETE** at 1000 archived model years, **2 IDLE and unfinished**. IT-Noe has an intact-looking latest restart at **5/1000** (`2009-01-01-00000`) but no current job; `RESUBMIT=198` is only a stored CIME setting, **not** evidence of an active resubmission chain. CH-Aws has **NO_ARCHIVE**, so its elapsed model years **cannot be verified from this report**; treat as unresolved, not as a proven zero-year simulation. The published 9/11 completion is operational restart evidence, **not convergence or scientific validation**.

Source: operator-provided, read-only IRIDIS6 `check_four_spinups.py` report on **20 October 2026**. The report shows the newest archived, minimally validated three-component CIME restart and the Slurm queue at that instant, **not the current model timestep**. This page is not live telemetry. `RUNNING`/`PENDING` do not prove the next five-year segment has completed; `COMPLETE` means a target-year restart was observed, not that all history has been rechecked or that carbon pools/FATES demography have converged. No submissions, restart edits, or Slurm actions were performed in this README update.
<!-- IRIDIS_LIVE_20261020_LATEST_END -->

## 20 October 2026 — Nine completed 1000-year cases and Git inode maintenance

A later **read-only IRIDIS6 progress snapshot** supersedes the earlier 15 October operational status for these nine cases. BE-Bra, FR-Fon, GL-ZaH, AT-Neu, FI-Sod, CH-Cha, CH-Fru, CH-Lae and CZ-Stn each showed 1000 archived annual history files, continuous model years, a final restart, `RESUBMIT=0`, and `st_archive success`. IT-Noe remained at 5 model years and CH-Aws at 0 verified model years. This is a **run-completeness observation, not evidence of ecological equilibrium**.

For the protected per-case Git object packing workflow, see [nine-site maintenance script](../../maintenance/cime_git_cleanup/pack_11site_nine_1000yr.sh) and [maintenance README](../../maintenance/cime_git_cleanup/README.md). The script defaults to read-only audit and cannot include the two unfinished sites. Git compaction and any subsequent 1000→3000-year continuation are separate activities; verify restart-chain integrity and continuation settings first. No Git maintenance execution result is claimed in this repository update.

# Eleven long-term FLUXNET sites: source-aware forcing QC and site-specific review trials

> **15 October 2026 status supersedes the older prospective sections below.** Stage15 produced **238/238 structurally audited, provisional** annual DATM files. Stage17 prepared cases; Stage18 initiated **1000-model-year CIME/Slurm resubmission workflows** for the eleven-site campaign. Multiple sites have been observed `RUNNING`, but **no complete 1000-year outcome or convergence has been established here**. IT-Noe has a dependency-error indication requiring separate investigation. **CH-Aws remains unresolved following three unsuccessful first segments** (`4286717`, `4286891`, `4286954`). For complete operational and scientific incident records, see [Stage17–18 1000-year spin-up status](docs/SPINUP_1000YEAR_STAGE17_18_2026-10-15.md) and [CH-Aws failed runs and meteorological investigations](docs/CH_Aws_HUMIDITY_FAILURES_2026-10-15.md). A [read-only status command](scripts/operations/01_readonly_spinup_status.sh) inspects running cases without resubmission.


**Recorded state: 14 October 2026 · Candidate forcing only · NOT scientifically approved for DATM or spin-up.**

This example documents the *executed* multisource meteorological consolidation and investigation of eleven long-running eddy-covariance sites for CTSM/CLM-FATES on IRIDIS6. It extends the scientific method and provenance principles of [eight-site QC v5](../FLUXNET_MultiSite_8/docs/QC_and_DATM_decisions.md); **it does not claim that the eight-site v5 Python script was directly run for these eleven sites**. Here, Stage03 is a distinct, source-aware merger, followed by narrowly scoped, independently versioned QC *trials* in Stages07, 08 and 11.

## Status snapshot — understand the acceptance level

| Status | Interpretation |
| --- | --- |
| **11/11 candidate files have passed the specific basic numerical and temporal trial checks** | Based on the separate last-run status reports; not yet a fresh end-to-end independent audit of all *final selected* versions. |
| `CANDIDATE_NUMERIC_OK_SCIENCE_REVIEW` | No rejected/missing values under the implemented numerical screens; **not** a scientific validity certificate. |
| `NOT_APPROVED_FOR_DATM_OR_SPINUP` | Final meteorological evaluation, landcover/PFT assessment, BIF height/ZBOT and independent DATM audit are outstanding. |

**Use different candidate tags per site; do not use Stage03 `v07a` indiscriminately for all eleven.**

| Site | Years (NO_LEAP, half-hourly) | Selected latest candidate tag (for further review only) | Specific record/change |
| --- | --- | --- | --- |
| BE-Bra | 1996–2025 | `v07a` | Multisource merge; 21 fallback humidity triplets require provenance review |
| FR-Fon | 2005–2025 | `v07a` | Multisource FLX/ICOS/ERA |
| GL-ZaH | 2000–2025 | `v07a` | Historical gap supported by ICOS ERA5, investigate source fractions |
| IT-Noe | 2004–2025 | `v07a` | 9 fallback triplets |
| AT-Neu | 2002–2020 | `v07a` | 19 fallback triplets |
| FI-Sod | 2001–2025 | `v07a` | Prior **PA conversion error** diagnosed; see below; early/middle/late products |
| CH-Aws | 2006–2024 | `landrh11a` | **559 VPD candidates** based on ERA5-Land-derived RH; 33 two-model disagreements >15 pp; **all 559 require science review** |
| CH-Cha | 2005–2024 | `v07a` | No unresolved basic numerical issues in recorded audit |
| CH-Fru | 2005–2024 | `pressure07a` | 6 erroneous ERA-sourced PA records, local bounded interpolation trial |
| CH-Lae | 2004–2024 | `pressurelw08a` | 3 PA + 2 LW_IN candidate repairs; older `pressure07a` is still `BLOCKED_MISSING` |
| CZ-Stn | 2010–2024 | `pressure07a` | 3 PA records (not only the one below hard absolute limit) |

Do **not** interpret the fact that a PFT dimension has 15 elements instead of 16 as a surface-generation failure: Stage03's historical PFT auditor expected 16 and incorrectly raised `ERROR` for all sites. Corrected read-only auditor: `scripts/stage04/00_reaudit_surface.py`. Its `STRUCTURE_OK_SCIENCE_REVIEW` designation is not proof of canopy/landcover representativeness. Some point surfaces include unexpectedly high crop fractions (e.g. BE-Bra ~37.4%, FR-Fon ~50.8%, CZ-Stn ~47.8%) relative to the site IGBP landcover; review before FATES experiments.

## Why these four stations needed exceptional treatment

| Case | Evidence | Candidate response; NOT a modification to observations |
| --- | --- | --- |
| **CH-Fru / CZ-Stn / CH-Lae pressure** | Era-derived `PA_F_QC=2` produced implausible 0, 14–55 kPa values and, at some times, companion ERA temperatures near −250 °C. Confirmed short corrupted blocks with reasonable uncorrupted pressure at both boundaries. | Stage07 interpolates **PA only** at 6/3/3 half-hours (12 total) in independent `pressure07a` directories, preserving TA/VPD and original QC/provenance. Never blindly copy the same broken ERA pressure. |
| **CH-Lae longwave** | On 2004-12-04 06:00 and 06:30, `LW_IN_F=42.34 W m⁻²`, `_QC=2`, rejected by `LW_IN>=60` screen; the `_ERA` value was identical. 05:30=271.581 and 07:00=277.980 W m⁻². | Stage08 interpolates to **273.714 and 275.847 W m⁻²**, in a second new tag `pressurelw08a`; 3 previous PA trial flags retained. |
| **CH-Aws winter humidity** | 559 negative reconstructed RH time steps, in 43 winter episodes, with minimum RH about −66.39%; original TA/VPD/PA are identical in FLUXMET and companion ERA5, all QC=2. Thus `_ERA` is **not independent confirmation**. | Stage09 fetches Open-Meteo-served historical ERA5 and ERA5-Land **T2m and Td2m**, using local standard time **UTC+1 without DST**. Stage10 compares RH estimates against tower valid QC=0/1 observations; **no winter valid RH tower points**. Stage11 uses ERA5-Land RH transferred to original site TA for **all 559** `VPD_F` trial values, while ERA5 remains comparison. 526 events differ by <=15 percentage points between models; 33 differ by >15 pp. **These counts are screening/uncertainty classes, not statistical certification or independent verification.** |
| **FI-Sod prior humidity alarm** | Historical script converted `PA_F` (kPa) using `×100` rather than `×1000`, incorrectly flagging **49,331** RH/QBOT records; after correcting PA units, **0 of those records** remained humidity-invalid. | Source-aware Stage03 uses `PA[kPa]→PSRF[Pa]` via ×1000. This is an error in an earlier *derived* script, **not 49,331 changes to the original source observations**. |

Full event provenance, exact values and scientific caveats: **[docs/QC_v5_extension_and_site_decisions.md](docs/QC_v5_extension_and_site_decisions.md)**.

## What is committed here

* All original Python scripts as used for **Stage02–Stage11** (including initial failed-check historical PFT auditor, isolated under `scripts/historical_DO_NOT_USE/`). File names and original behavior are preserved; stage folders merely group them.
* A documented stage-by-stage reproduction plan and version selection.
* Source-control protections: no downloaded tower ZIP/CSV, no hourly reanalysis JSONs, no large NetCDF, no logs or private paths containing tokens. Respect FLUXNET/ICOS/EUF/Open-Meteo data terms.

**Not included:** raw/downloaded data, candidate forcing CSVs, SHA-checkable originals, correction-ledger CSVs, `raw_openmeteo` cache, Surface or DATM NetCDFs, model archives, credentials. Validation of repository scripts on the original site packages requires obtaining data under their original permissions. The experiment snapshot includes original SHA256 *as metadata strings only* in the documentation; see provenance.

## Reproduce or inspect on IRIDIS6

The recorded scripts were executed from `~/FLUXNET_MultiSite_11_stageXX/` with `conda activate clm_fates_env` and site data under `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE`. GitHub's grouped scripts have the same file bodies and may be called from a checkout path.

**Read-only validation of the final selected candidate versions** (added to this repository package):

```bash
conda activate clm_fates_env
python examples/FLUXNET_MultiSite_11/scripts/12_verify_selected_trial_manifest.py
```

Do **not** rerun the Stage07/08/11 `--write...` actions against existing directories; each refuses overwrite. If you need to regenerate candidates from licensed raw data, use **new version tags**, preserve parent SHA256 and related reference reports, and explicitly review all site-specific stage prerequisites. Stage09 `fetch` relies on the external historical archive's continuing availability and must not be assumed bit-identical to this 2026 snapshot.

For context, see the [eight-site workflow README](../FLUXNET_MultiSite_8/README.md) and [eight-site human QC decisions](../FLUXNET_MultiSite_8/docs/QC_and_DATM_decisions.md).

## Remaining work before claiming model-ready

1. Independently review temperature discontinuities/flatlines, solar/longwave radiation, precipitation totals, winds and source switches **site-by-site**, with different ecoclimatic expectations and the original variable QC flags. Structural numeric checks alone are insufficient.
2. Assess CH-Aws ERA5-Land winter humidity uncertainty, mountain exposure, reference clocking, alternative RH formula/ice phase, interpolation/resolution limits and high-uncertainty 33-event sensitivity. No direct tower humidity evidence exists for the winter 559 events.
3. Examine surface landcover/PFT fractions relative to each EC footprint; identify crop contamination and whether FATES requires site-specific PFT adjustments.
4. Use dated BIF `TA_F`/wind observation heights for time-varying `ZBOT`; audit sensor-height mismatches and metadata gaps. No eleven-site DATM or spin-up is represented as completed by this directory.
5. Produce independently verified, non-overwriting final DATM and only then run subsequent model checks/spin-up and carbon convergence analysis.


## Update — 14 October 2026: 238/238 PROVISIONAL DATM validated

The eleven-site candidate forcing now has a **user-approved dated-BIF TA_F ZBOT policy**, with the earliest documented height held constant backwards only as an explicitly annotated assumption. This does not reconstruct actual early sensor heights. The Stage15 read-only DATM audit returned **238/238 annual NO_LEAP NetCDF files** structurally correct; all 11 site-specific `user_nl_clm` files are present. **No 500-year spin-up was submitted, and scientific approval is still open.**

Read the full scientific/methodological record: **[Dated BIF height and dynamic ZBOT, Stage13–15](docs/BIF_DYNAMIC_ZBOT_STAGE13_15.md)**. For exact executable scripts use `scripts/stage13b/`, `scripts/stage14/`, `scripts/stage15/`, and the Stage16 configuration-only inspection in `scripts/stage16/` after it has been published. The old sections below describing uncompleted BIF/DATM are preserved as a historical snapshot, superseded by this update.

**Outstanding:** independent driver science review; CH-Aws winter modeled humidity uncertainty; gridded crop/PFT vs tower footprint; site-specific stream/namelist/CO₂ choice and GF-Guy executable preflight; short model tests. **Do not submit spin-up yet.**

<!-- NINE_SITE_1000_FINAL_START -->
## Nine-site 1000-year spin-up: convergence and EC comparisons

Nine sites completed 1000 model years. IT-Noe and CH-Aws are excluded.
The figures show annual carbon pools (1000 years), final 250-year
carbon dynamics, and monthly GPP/NEE comparisons for the last
complete forcing cycle.

**Caution:** Model completion does not establish ecological convergence.
Negative R² indicates performance worse than the observation-mean baseline.
Some sites have incomplete EC observation periods.

| Site | GPP monthly R² | NEE monthly R² |
|---|---:|---:|
| BE-Bra | 0.469 | 0.194 |
| FR-Fon | 0.772 | 0.517 |
| GL-ZaH | -38.551 | -60.050 |
| AT-Neu | 0.847 | -0.650 |
| FI-Sod | 0.035 | -2.245 |
| CH-Cha | 0.465 | -1.785 |
| CH-Fru | 0.772 | -0.761 |
| CH-Lae | 0.850 | 0.535 |
| CZ-Stn | 0.499 | -0.082 |

[Nine-site summary CSV](figures/spinup1000_final/nine_site_spinup1000_summary.csv)

### BE-Bra

![BE-Bra carbon pools, 1000 years](figures/spinup1000_final/BE-Bra/BE-Bra_01_carbon_pools_annual_mean.png)

![BE-Bra carbon pools, final 250 years](figures/spinup1000_final/BE-Bra/BE-Bra_02_carbon_pools_last250years.png)

![BE-Bra monthly GPP and NEE](figures/spinup1000_final/BE-Bra/BE-Bra_GPP_NEE_monthly_overview.png)

[Convergence metrics](figures/spinup1000_final/BE-Bra/BE-Bra_convergence_metrics.csv) · [EC metrics](figures/spinup1000_final/BE-Bra/BE-Bra_monthly_metrics.csv) · [Metadata](figures/spinup1000_final/BE-Bra/BE-Bra_metadata.json)

### FR-Fon

![FR-Fon carbon pools, 1000 years](figures/spinup1000_final/FR-Fon/FR-Fon_01_carbon_pools_annual_mean.png)

![FR-Fon carbon pools, final 250 years](figures/spinup1000_final/FR-Fon/FR-Fon_02_carbon_pools_last250years.png)

![FR-Fon monthly GPP and NEE](figures/spinup1000_final/FR-Fon/FR-Fon_GPP_NEE_monthly_overview.png)

[Convergence metrics](figures/spinup1000_final/FR-Fon/FR-Fon_convergence_metrics.csv) · [EC metrics](figures/spinup1000_final/FR-Fon/FR-Fon_monthly_metrics.csv) · [Metadata](figures/spinup1000_final/FR-Fon/FR-Fon_metadata.json)

### GL-ZaH

![GL-ZaH carbon pools, 1000 years](figures/spinup1000_final/GL-ZaH/GL-ZaH_01_carbon_pools_annual_mean.png)

![GL-ZaH carbon pools, final 250 years](figures/spinup1000_final/GL-ZaH/GL-ZaH_02_carbon_pools_last250years.png)

![GL-ZaH monthly GPP and NEE](figures/spinup1000_final/GL-ZaH/GL-ZaH_GPP_NEE_monthly_overview.png)

[Convergence metrics](figures/spinup1000_final/GL-ZaH/GL-ZaH_convergence_metrics.csv) · [EC metrics](figures/spinup1000_final/GL-ZaH/GL-ZaH_monthly_metrics.csv) · [Metadata](figures/spinup1000_final/GL-ZaH/GL-ZaH_metadata.json)

### AT-Neu

![AT-Neu carbon pools, 1000 years](figures/spinup1000_final/AT-Neu/AT-Neu_01_carbon_pools_annual_mean.png)

![AT-Neu carbon pools, final 250 years](figures/spinup1000_final/AT-Neu/AT-Neu_02_carbon_pools_last250years.png)

![AT-Neu monthly GPP and NEE](figures/spinup1000_final/AT-Neu/AT-Neu_GPP_NEE_monthly_overview.png)

[Convergence metrics](figures/spinup1000_final/AT-Neu/AT-Neu_convergence_metrics.csv) · [EC metrics](figures/spinup1000_final/AT-Neu/AT-Neu_monthly_metrics.csv) · [Metadata](figures/spinup1000_final/AT-Neu/AT-Neu_metadata.json)

### FI-Sod

![FI-Sod carbon pools, 1000 years](figures/spinup1000_final/FI-Sod/FI-Sod_01_carbon_pools_annual_mean.png)

![FI-Sod carbon pools, final 250 years](figures/spinup1000_final/FI-Sod/FI-Sod_02_carbon_pools_last250years.png)

![FI-Sod monthly GPP and NEE](figures/spinup1000_final/FI-Sod/FI-Sod_GPP_NEE_monthly_overview.png)

[Convergence metrics](figures/spinup1000_final/FI-Sod/FI-Sod_convergence_metrics.csv) · [EC metrics](figures/spinup1000_final/FI-Sod/FI-Sod_monthly_metrics.csv) · [Metadata](figures/spinup1000_final/FI-Sod/FI-Sod_metadata.json)

### CH-Cha

![CH-Cha carbon pools, 1000 years](figures/spinup1000_final/CH-Cha/CH-Cha_01_carbon_pools_annual_mean.png)

![CH-Cha carbon pools, final 250 years](figures/spinup1000_final/CH-Cha/CH-Cha_02_carbon_pools_last250years.png)

![CH-Cha monthly GPP and NEE](figures/spinup1000_final/CH-Cha/CH-Cha_GPP_NEE_monthly_overview.png)

[Convergence metrics](figures/spinup1000_final/CH-Cha/CH-Cha_convergence_metrics.csv) · [EC metrics](figures/spinup1000_final/CH-Cha/CH-Cha_monthly_metrics.csv) · [Metadata](figures/spinup1000_final/CH-Cha/CH-Cha_metadata.json)

### CH-Fru

![CH-Fru carbon pools, 1000 years](figures/spinup1000_final/CH-Fru/CH-Fru_01_carbon_pools_annual_mean.png)

![CH-Fru carbon pools, final 250 years](figures/spinup1000_final/CH-Fru/CH-Fru_02_carbon_pools_last250years.png)

![CH-Fru monthly GPP and NEE](figures/spinup1000_final/CH-Fru/CH-Fru_GPP_NEE_monthly_overview.png)

[Convergence metrics](figures/spinup1000_final/CH-Fru/CH-Fru_convergence_metrics.csv) · [EC metrics](figures/spinup1000_final/CH-Fru/CH-Fru_monthly_metrics.csv) · [Metadata](figures/spinup1000_final/CH-Fru/CH-Fru_metadata.json)

### CH-Lae

![CH-Lae carbon pools, 1000 years](figures/spinup1000_final/CH-Lae/CH-Lae_01_carbon_pools_annual_mean.png)

![CH-Lae carbon pools, final 250 years](figures/spinup1000_final/CH-Lae/CH-Lae_02_carbon_pools_last250years.png)

![CH-Lae monthly GPP and NEE](figures/spinup1000_final/CH-Lae/CH-Lae_GPP_NEE_monthly_overview.png)

[Convergence metrics](figures/spinup1000_final/CH-Lae/CH-Lae_convergence_metrics.csv) · [EC metrics](figures/spinup1000_final/CH-Lae/CH-Lae_monthly_metrics.csv) · [Metadata](figures/spinup1000_final/CH-Lae/CH-Lae_metadata.json)

### CZ-Stn

![CZ-Stn carbon pools, 1000 years](figures/spinup1000_final/CZ-Stn/CZ-Stn_01_carbon_pools_annual_mean.png)

![CZ-Stn carbon pools, final 250 years](figures/spinup1000_final/CZ-Stn/CZ-Stn_02_carbon_pools_last250years.png)

![CZ-Stn monthly GPP and NEE](figures/spinup1000_final/CZ-Stn/CZ-Stn_GPP_NEE_monthly_overview.png)

[Convergence metrics](figures/spinup1000_final/CZ-Stn/CZ-Stn_convergence_metrics.csv) · [EC metrics](figures/spinup1000_final/CZ-Stn/CZ-Stn_monthly_metrics.csv) · [Metadata](figures/spinup1000_final/CZ-Stn/CZ-Stn_metadata.json)

Original EC CSV files, model NetCDF archives and restart files
are not published to GitHub.

<!-- NINE_SITE_1000_FINAL_END -->


## Scratch image and analysis archival to Research Filestore

All new Scratch-based diagnostic figures can be inventoried, SHA256-verified and copied to the shared Research Filestore using the repository-wide [cross-batch archival script](../../scripts/research_filestore/archive_scratch_analysis.py) and [step-by-step runbook](../../docs/SCRATCH_ANALYSIS_TO_RFS.md).

**Batch:** `FLUXNET_MultiSite_11`. On an **IRIDIS6 login node** (not Slurm compute node):

```bash
cd ~/CLM-FATES-single-site-workflows
python3 -B scripts/research_filestore/archive_scratch_analysis.py audit --batch FLUXNET_MultiSite_11
python3 -B scripts/research_filestore/archive_scratch_analysis.py copy --batch FLUXNET_MultiSite_11
```

Copy receipts are written to `/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_11/scratch_analysis_archive/_receipts/`. Independently `verify --receipt <actual-RFS-receipt.json>` before optionally running `prune --receipt <actual-RFS-receipt.json> --confirm DELETE_VERIFIED_SCRATCH_IMAGES`. Only precisely verified **Scratch images** are removed; related analysis CSV/JSON, model history/restarts, raw forcing, CIME cases, GitHub figures and Home files are never deleted by this tool. The script skips uncertain locations, so audit actual results and use the established Home→RFS workflow where appropriate.

**Status:** Documentation and reusable code published; no Scratch→RFS copy or deletion is claimed to have run on IRIDIS6 from this GitHub update.
