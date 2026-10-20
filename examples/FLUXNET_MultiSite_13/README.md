# FLUXNET MultiSite 13: QC v5 forcing and exploratory meteorological repairs

<!-- IRIDIS_LIVE_20261020_LATEST_START -->
## Latest IRIDIS6 run snapshot — 20 October 2026 (13 sites)

This is newer than the Stage37 recovery publication below. All reported cases are the existing `_FATES_SPINUP1000_S30SHARED` cases, **not** the superseded `S30EXCL` cases.

| Site | Archived years / target | Remaining model years | Latest coordinated checkpoint | `RESUBMIT` | Slurm snapshot | Job IDs (as reported) |
| --- | ---: | ---: | --- | ---: | --- | --- |
| DE-Lnf | 650 / 1000 | 350 | `2652-01-01-00000` | 69 | **PENDING** | 4490359:PENDING |
| DE-Obe | 455 / 1000 | 545 | `2463-01-01-00000` | 108 | **RUNNING** | 4490688:RUNNING, 4490690:PENDING |
| ES-Agu | 460 / 1000 | 540 | `2466-01-01-00000` | 107 | **PENDING** | 4489459:PENDING |
| ES-LJu | 470 / 1000 | 530 | `2474-01-01-00000` | 105 | **PENDING** | 4490127:PENDING |
| IT-Col | 465 / 1000 | 535 | `2461-01-01-00000` | 106 | **PENDING** | 4490463:PENDING |
| DE-Gri | 510 / 1000 | 490 | `2514-01-01-00000` | 97 | **RUNNING** | 4490687:RUNNING, 4490689:PENDING |
| DE-RuR | 505 / 1000 | 495 | `2516-01-01-00000` | 98 | **PENDING** | 4490358:PENDING |
| FI-Hyy | 500 / 1000 | 500 | `2497-01-01-00000` | 99 | **PENDING** | 4490465:PENDING |
| FI-Let | 495 / 1000 | 505 | `2505-01-01-00000` | 100 | **PENDING** | 4491686:PENDING, 4491687:PENDING |
| FR-Pue | 465 / 1000 | 535 | `2465-01-01-00000` | 106 | **PENDING** | 4490129:PENDING |
| GF-Guy | 465 / 1000 | 535 | `2469-01-01-00000` | 106 | **PENDING** | 4491521:PENDING, 4491522:PENDING |
| IT-MBo | 485 / 1000 | 515 | `2488-01-01-00000` | 102 | **PENDING** | 4490834:PENDING, 4490835:PENDING |
| IT-Tor | 435 / 1000 | 565 | `2443-01-01-00000` | 112 | **PENDING** | 4490130:PENDING |

**Summary:** **2 RUNNING** (DE-Obe, DE-Gri) and **11 PENDING**; none is archived at 1000 years in this snapshot. The 13 archived checkpoints total **6,360 of 13,000 target model-years**, with **6,640 remaining**. This establishes post-recovery queued/running jobs and advanced checkpoints relative to historical incidents, but does not independently verify each next CIME segment or confirm final 1000-year completion.

Source: operator-provided, read-only IRIDIS6 `check_four_spinups.py` report on **20 October 2026**. The report shows the newest archived, minimally validated three-component CIME restart and the Slurm queue at that instant, **not the current model timestep**. This page is not live telemetry. `RUNNING`/`PENDING` do not prove the next five-year segment has completed; `COMPLETE` means a target-year restart was observed, not that all history has been rechecked or that carbon pools/FATES demography have converged. No submissions, restart edits, or Slurm actions were performed in this README update.
<!-- IRIDIS_LIVE_20261020_LATEST_END -->

<!-- FLUXNET13_STAGE37_QUOTA_RECOVERY -->
## Stage 37 — Recover interrupted 1000-year spin-ups after Scratch file-count quota failure (20 October 2026)

**Status: recovery code and runbook published; actual successful resumption NOT YET VERIFIED.** Following the October 18–19 IRIDIS6 Scratch inode/file-count exhaustion (614,400/614,400 files), CESM/ParallelIO reported `Disk quota exceeded`, and many dependent CIME `st_archive` jobs remained `DependencyNeverSatisfied`. That queue state does not distinguish a first-segment failure from a later interruption. Consult site-specific `CaseStatus`, `sacct` and restart inventory before deciding how far a station ran.

**Recovery target:** the 13 existing `<SITE>_FATES_SPINUP1000_S30SHARED` cases, not the superseded `S30EXCL` cases. Target 1000 cumulative model years (200 × 5-year segments); preserve site-specific surface, DATM, fixed CO2 and executable. Avoid rerunning Stage31–36 initial submission scripts or resetting the automatic resubmission counter to 199.

The new [Stage37 guarded recovery implementation](scripts/stage37/37_recover_13site_spinup1000_after_inode_quota.py) separates `inspect` (read-only), `prepare SITE` (back up interrupted output and stage a verified coordinated archived restart), and `submit SESSION` (a separate one-shot `case.submit` after revalidation). A site is blocked if the latest recoverable checkpoint, restart components, `RESUBMIT`, case history or Slurm state are ambiguous. Cases with no completed five-year restart are not automatically restarted. No GitHub model NetCDF/restart data are uploaded.

- [**Incident details, case safeguards, documented recovery procedure and IRIDIS6 commands**](docs/SPINUP1000_INODE_QUOTA_RECOVERY_2026-10-20.md).
- [**Stage31–36 original CIME and Slurm chronology**](docs/SPINUP1000_CIME_SLURM_STAGE31_36_STATUS.md).

```bash
cd ~/CLM-FATES-single-site-workflows
git pull --ff-only origin main
myfiles
python3 examples/FLUXNET_MultiSite_13/scripts/stage37/37_recover_13site_spinup1000_after_inode_quota.py inspect
```

**Do not claim 13/13 restarts, completed 1000 model years, or carbon-pool convergence until independently validated after resumed CIME/Slurm execution.**
<!-- END FLUXNET13_STAGE37_QUOTA_RECOVERY -->

<!-- FLUXNET13_20261018_FULLSYNC_START -->
## October 18, 2026 checkpoint: 13-site MET, BIF/ZBOT, DATM, surface and spin-up source

**Current status: 13/13 scientifically PROVISIONAL annual DATM inputs available; 271 annual files verified; 13/13 site point-surface NetCDF files detected.** Stage 28 numerical QC is **13/13 PASS**, but all underlying scientific forcing/height/PFT decisions remain subject to review. **1000-year spin-up completion and convergence are NOT established here.** Historical Stage00–22 notes below remain part of the experiment's decision history; they do not supersede this checkpoint.

### Detailed method documents

- [**MET Stage20–28: selected versions, unusual weather, source/QC caveats and unresolved MDS blocks**](docs/MET_STAGE20_28_METHOD_AND_OPEN_ISSUES.md).
- [**BIF TA/WS sensor heights, dated ZBOT changes, early extrapolation, DE-Lnf and IT-Col literature references, Stage29b/30 DATM manifests**](docs/BIF_HEIGHT_ZBOT_DATM_STAGE23_30.md).
- [**1000-year case configuration, Slurm shared-CPU-core policy, and the Stage31–36 recovery/failed-attempt timeline**](docs/SPINUP1000_CIME_SLURM_STAGE31_36_STATUS.md).
- [Source inventory and SHA256 ledger](docs/CODE_SOURCES_SHA256_20261018.tsv) (generated during publication).

### Data production status

| Data product / experiment | Recorded result | Remaining issue |
|---|---|---|
| 13-site MET Stage28 selection | 13/13 numerical hard-QC PASS | **Scientifically provisional.** Original MDS gaps and suspicious extreme rain remain |
| BIF TA reference heights, 11 stations | 5 time-varying dated BIF; 6 single documented BIF TA height | First-known-height extrapolation and TA/WS height mismatch require disclosure |
| **DE-Lnf** | **44 m static**, published **air-temperature sensor height** ([Jürgensen et al., 2021](https://doi.org/10.3390/f12121693)) | No proof it remained at 44 m across **all** 2002–2024 |
| **IT-Col** | **32 m static**, published **site measurement-height proxy** ([Keenan et al., 2009](https://doi.org/10.5194/bg-6-1423-2009)) | **NOT confirmed `TA_F` sensor height**; sensitivity/metadata confirmation needed |
| Stage29b / Stage30 DATM | 229 + 42 = **271** yearly 30-min `NO_LEAP` NetCDFs; earlier 229 SHA256-verified unchanged | Research-only provisional forcing; full manifest lives on IRIDIS |
| Surface data | 13/13 single-site point-surface NetCDFs found | Vegetation PFT / footprint / soil representation not independently certified |
| Spin-up setup | Intended **1000 model years per site**, 5-year jobs × 200, `RESUBMIT=199` | Slurm launch corrections; model completion and equilibrium not established |

**Special MET and BIF points:** DE-Gri and FI-Let retain **49 + 20 = 69** original MDS flagged blocks in the Stage28 decision ledger. ES-LJu has a suspicious strong-rainfall concentration at **23:00**; do **not** automatically re-time or redistribute precipitation without instrument/record evidence. FI-Hyy has **122,640 half-hour records** with TA/WS height difference >3 m in the BIF audit; wind speed was not vertically adjusted. Site heights may change at times not on the 30-minute grid, so Stage29b retains the original effective instant and maps height at the next eligible model timestamp, with early extrapolation explicitly flagged.

### Workflow and source code

`Surface: scripts/stage02/` → `MET: scripts/stage20–stage28/` → `BIF audit: scripts/stage23–stage24/` → `dynamic/static ZBOT and annual DATM: scripts/stage29b/` → `published/proxy static height completion: scripts/stage30/` → `CIME spin-up history: scripts/stage31–stage36/`.

**Warning on spin-up scripts:** `stage31` first submitted 13 cases using **incorrect whole-node `--exclusive`**, `stage34` stopped after preparation, and `stage35` hit a submission-state ambiguity. Those scripts are **audit history and superseded experiments**, not a recommended fresh spin-up recipe. Existing successful 8-/11-site references use **1 CPU / 8 GB per Slurm job, no `--exclusive`, PMIx `srun`**, with batch resources regenerated from CIME XML. The outcome of Stage36 needs its actual running log; do not assert it succeeded or double-submit uncertain cases.

The final Stage30 manifest lives under:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_13_ZBOT_DATM_STAGE30_20261018_055940_1008203/reports/04_consolidated_13site_271_DATM_SHA256_manifest.csv`

**Reproducibility vs redistribution:** the repository contains source code, scientific limitations and non-sensitive summaries. It intentionally excludes raw FLUXNET/ICOS/EUF packages, licensed BIF/EC observations, ERA caches, derived MET CSV, ZBOT/DATM NetCDF, active CIME case directories, restarts, spin-up output, private credentials and internal per-record manifests. Original files and hashes are retained on IRIDIS only.
<!-- FLUXNET13_20261018_FULLSYNC_END -->

**Historical checkpoint, 15 October 2026 (prior to the 18 October Stage28–30 completions).** This folder preserves 13-site baseline preparation, the correctly adapted QC v5 code, and every subsequent meteorological QC experiment through Stage 22. **The forcing is a numerical trial, not scientifically approved for BIF, DATM or spin-up.** No FLUXNET/ICOS or ERA source files are redistributed here.

## Sites and release windows

| Site | Source | Selected years |
|---|---|---|
| DE-Lnf | EUF FLUXNET v1.3 r1 | 2002–2024 |
| DE-Obe | EUF FLUXNET v1.3 r1 | 2008–2025 |
| ES-Agu | EUF FLUXNET v1.3 r1 | 2006–2024 |
| ES-LJu | EUF FLUXNET v1.3 r1 | 2004–2024 |
| IT-Col | FLUXNET2015 FULLSET HH + ERAI HH | 1996–2014 |
| DE-Gri | ICOS FLUXNET v1.3 r1 | 2004–2025 |
| DE-RuR | ICOS FLUXNET v1.3 r1 | 2011–2025 |
| FI-Hyy | ICOS FLUXNET v1.3 r1 | 1997–2025 |
| FI-Let | ICOS FLUXNET v1.3 r1 | 2010–2025 |
| FR-Pue | ICOS FLUXNET v1.3 r1 | 2000–2025 |
| GF-Guy | ICOS FLUXNET v1.3 r1 | 2004–2025 |
| IT-MBo | ICOS FLUXNET v1.3 r1 | 2003–2025 |
| IT-Tor | ICOS FLUXNET v1.3 r1 | 2008–2025 |

The precise, pinned releases are specified in [Stage 03](scripts/stage03/03_prepare_13_site_forcing_v5_candidate.py). **IT-Col's companion is ERA-Interim (ERAI_HH), not ERA5.**

## Proven working QC v5 baseline

Stage 03 does **not** invent a new meteorological QC algorithm. It imports the pre-existing **eight-site v5** implementation [`03_prepare_eight_site_forcing_v5.py`](../FLUXNET_MultiSite_8/scripts/03_prepare_eight_site_forcing_v5.py) and adapts only station/year selections and source-file lookup to the 13 explicit FLUXNET/ICOS releases. It requires the original reference module. Source products, old processed_v5 files, DATM and simulations remain unmodified.

Using a checkout on IRIDIS6 (after preparing licensed raw files), for example:

```bash
conda activate clm_fates_env
python examples/FLUXNET_MultiSite_13/scripts/stage03/03_prepare_13_site_forcing_v5_candidate.py --check --base-script examples/FLUXNET_MultiSite_8/scripts/03_prepare_eight_site_forcing_v5.py
python examples/FLUXNET_MultiSite_13/scripts/stage03/03_prepare_13_site_forcing_v5_candidate.py --run --base-script examples/FLUXNET_MultiSite_8/scripts/03_prepare_eight_site_forcing_v5.py
```

The corrected v5 audit is [Stage04 `*_fixed.py`](scripts/stage04/04_audit_13_site_qc_v5_fixed.py). The earlier Stage04 and Stage12 variants are retained **only as development history**; do not mistake original failed/buggy variants for the recommended method. Every isolated trial requires a **new output directory**; never delete an existing result to clear a collision.

## Chronological experiment log

| Stage | Activity and observation | Scientific interpretation |
|---|---|---|
| 00–04 | Source transfer/extraction; 13-site v5 candidate forcing and corrected audit | 13 numerical candidates, not independent scientific validation |
| 05–10 | VPD/QC0 and ES-LJu severe 2023 temperature tests; v6, paired TA/VPD legacy v7 experiments | Some originally QC=0 values also appeared physically implausible; experimental alternatives preserved separately |
| 11–15 | Read-only residual audits; targeted revisions | Stage12: 4 ES-Agu, 1 ES-LJu, 1 DE-Lnf records; Stage15: 4 ES-Agu, 3 FR-Pue. Total **13 modified half-hours across four sites** in the selected Stage15 parent chain |
| 16 | DE-Gri/FI-Let multiyear MDS audit | **465 suspect half-hours**, **82 flagged blocks**, not 465 independently proven errors |
| 17 | ERA5 and ERA5-Land crosscheck (30 requested model/year files) | Stage17 used an overly strict combined T/Td/RH/pressure validity gate, wrongly rejecting valid ERA5-Land temperature when its API pressure was missing |
| 17b | Independent temperature/air-moisture/pressure gates | **247/465** temperature dual-model-screened candidates |
| 18 | QC0 tower-based meteorology review including RH | **242/465** combined T/RH candidates; 13 complete flagged blocks screen positive |
| 19 | Both-reanalysis boundary preview on 13 fully screened blocks (114 HH) | Several local replacements make edge jumps worse, so no blanket substitution |
| 20 | Conservative 13-site revision and numeric QC | **58 additional candidate edits**, **11 DE-Gri + 47 FI-Let**, across 8 blocks. All 13 sites: **zero numeric hard failures** |
| 21 | Conservative additional changes and complete QC | **0 new edits**; Stage20 58 unchanged. **74 MDS blocks still unresolved**; **21 temperature steps >12 °C/30min**; **14 rain events >40 mm/30min** retained for review |
| 22 | Whole contiguous QC1 TA/VPD envelope strategy | **Not completed.** Refused overwrite of already-existing Stage22 output directory (`FileExistsError`). This path collision is NOT a scientific result |

Stage21 rejection *decision rows*: 45 `NO_STAGE18_SUPPORTED_UNTOUCHED_QC1_SUBSEGMENTS`, 33 `BOUNDARY_OR_INTERNAL_CONTINUITY_HOLD`, 2 `QC0_OR_UNSUPPORTED_SOURCE_KEEP`, and 2 `SEGMENT_LONGER_THAN_CONFIGURED_MAX`. Decision rows need not equal distinct blocks. The key insight: using only selected points inside a longer continuous QC1 fill period often introduces artificial discontinuities, motivating the unexecuted Stage22 whole-envelope experiment.

## Historical Stage21 science decisions before the later BIF implementation

1. Review the **74 pending** DE-Gri/FI-Let MDS flagged blocks using original measured QC0 anchors, whole fill periods and model disagreement; ERA5 and ERA5-Land are not independent ground truth.
2. Examine **21** remaining large half-hour TA steps and original source/QC transitions across sites. Do not automatically rewrite QC0.
3. Check **14** very heavy rainfall events (>40 mm/30min) plus wider thresholds, particularly GF-Guy, FR-Pue, ES-LJu. Check time-of-accumulation (including apparent daily rainfall around 23:00), units and source provenance; never blanket-clip plausible downpours.
4. Verify site-local-standard-time interpretation from site metadata (no automatic timezone choice from correlation), humidity/QBOT physical consistency, and instrument heights before BIF/ZBOT and DATM.
5. Stage22 output path already exists; inspect it before any rerun, or explicitly select a **new** `--out` version. Its script is archived as exploratory code, not a completed successful run.

## IRIDIS handoff paths

```text
Last completed Stage21 selected manifest:
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_meteorology_stage21_trial_v1_20261015/reports/stage21_selected_13site_meteorology_manifest.csv

Stage20 selected manifest (58 candidate changes):
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_meteorology_stage20_trial_v1_20261015/reports/stage20_selected_13site_meteorology_manifest.csv

Stage21 QC and decision reports:
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_meteorology_stage21_trial_v1_20261015/reports/
```

Source code [all stages](scripts) and the associated [ES-LJu v7 methodology](docs/ES-LJu_site_specific_QC_v7_METHOD.md) are in this folder. Code files were archived as supplied; actual numerical runs occurred on IRIDIS6, not inside GitHub.

**Do not commit licensed raw FLUXNET/ICOS data, ERA JSON caches, derived met forcing, NetCDF, access tokens, site credentials or model archives.** Preserve original and per-trial SHA256 ledgers on IRIDIS. **Historical Stage21 BIF gate: CLOSED_PENDING_SCIENTIFIC_MET_QC.** The later Stage29b/30 research-only BIF/ZBOT/DATM products are described above; scientific approval remains open.


## Scratch image and analysis archival to Research Filestore

All new Scratch-based diagnostic figures can be inventoried, SHA256-verified and copied to the shared Research Filestore using the repository-wide [cross-batch archival script](../../scripts/research_filestore/archive_scratch_analysis.py) and [step-by-step runbook](../../docs/SCRATCH_ANALYSIS_TO_RFS.md).

**Batch:** `FLUXNET_MultiSite_13`. On an **IRIDIS6 login node** (not Slurm compute node):

```bash
cd ~/CLM-FATES-single-site-workflows
python3 -B scripts/research_filestore/archive_scratch_analysis.py audit --batch FLUXNET_MultiSite_13
python3 -B scripts/research_filestore/archive_scratch_analysis.py copy --batch FLUXNET_MultiSite_13
```

Copy receipts are written to `/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_13/scratch_analysis_archive/_receipts/`. Independently `verify --receipt <actual-RFS-receipt.json>` before optionally running `prune --receipt <actual-RFS-receipt.json> --confirm DELETE_VERIFIED_SCRATCH_IMAGES`. Only precisely verified **Scratch images** are removed; related analysis CSV/JSON, model history/restarts, raw forcing, CIME cases, GitHub figures and Home files are never deleted by this tool. The script skips uncertain locations, so audit actual results and use the established Home→RFS workflow where appropriate.

**Status:** Documentation and reusable code published; no Scratch→RFS copy or deletion is claimed to have run on IRIDIS6 from this GitHub update.

### Home analysis archives (supplementary)

Historical Home-based derived figures and companion statistical tables may be archived using [`archive_home_analyses.py`](../../scripts/research_filestore/archive_home_analyses.py) and its [no-clone IRIDIS6 runbook](../../docs/HOME_ANALYSIS_TO_RFS.md). Use `audit --batch FLUXNET_MultiSite_13` then `copy --batch FLUXNET_MultiSite_13` on a login node. Results go to Research Filestore under `FLUXNET_MultiSite_13/home_analysis_archive/` with SHA256 receipts; original Home files are **never deleted**. This link records available procedures, **not** confirmation that the Home transfer has executed.
