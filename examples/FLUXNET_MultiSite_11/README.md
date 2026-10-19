
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
