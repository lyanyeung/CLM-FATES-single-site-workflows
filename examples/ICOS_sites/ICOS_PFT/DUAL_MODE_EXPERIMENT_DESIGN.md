# Dual-mode FATES vegetation experiment design (draft; NOT submitted)

Date: 2026-10-23. Scope: four existing FLUXNET multi-site batches; 22 sites having numerical literature leads in `38_site_PFT_evidence.csv`, and remaining 16 investigated separately.

## Scientific questions

* **FULL**: how does fully dynamic FATES competition and demography evolve under unchanged tower climate, CO2, soil and site conditions? Tower vegetation proportions are **validation targets**, not guaranteed prescribed initial PFT coverage.
* **FIXNC**: how do carbon uptake, pools and vegetation dynamics behave under an explicitly prescribed fixed PFT biogeography and no *inter-PFT* area competition? Within-PFT demographic growth and mortality may remain dynamic.
* Direct interpretation as 'effect of competition alone' is invalid unless all other configuration and biogeography differences are controlled; report the exact contrast and physical mechanisms. A third COMP_FIXEDBIO experiment may eventually help isolate competition from biogeography.

## Exactly two primary arms

| Item | FULL | FIXNC |
|---|---|---|
| Proposed suffix | `_OBSPFT_FULL26` | `_OBSPFT_FIXNC26` |
| Inter-PFT competition | enabled | disabled |
| Prescribed PFT area distribution | **No** | **Yes**, but only where tower-area evidence is vetted |
| Start | independent cold start/spin-up | independent cold start/spin-up |
| Meteorology, CO2 | same pinned original per-site forcing and concentration | identical to FULL |
| Soil/topography/hydrology, other landunits | preserve original | preserve original |
| PFT candidate definitions | explicitly inspect active FATES JSON and executable | same validated parameter lineage, separate build if mode requires it |
| Outputs | isolated directories | isolated directories |

**Do not modify the existing 38 cases.** Never point a new case to existing `RUNDIR`, `DOUT_S_ROOT`, `EXEROOT` or restart without checking whether shared resources are safe. New unique output roots and short names are mandatory. Existing case executable is not automatically compatible with changed `use_fates_nocomp` / `use_fates_fixed_biogeog` flags. Build a new executable when these choices are build-time; do not use `--keepexe` across incompatible FATES modes.

## Why 22 numerical leads are NOT 22 ready-to-run prescribed fractions

Only measured horizontal area fractions with a suitable tower footprint / land-unit denominator are suitable as direct targets. Species number, stem volume, basal area, biomass carbon share, canopy cover, or percent conditional on vegetated area require separate interpretation. PFTs on a FATES natural vegetation landunit may require normalization to the natural landunit, not the full grid. `PCT_NAT_PFT` is a CLM host-model vector and must not be assumed to prescribe FATES PFT fractions. Identify the parameter and actual input data controlling fixed biogeography in the checked-out FATES revision before any write.

**Readiness:**
* **AREA_CANDIDATE**: NL-Loo reported 500-m ground proportions, ES-LJu ground cover (need plant type mapping and bare-soil handling), DE-Tha conifer/deciduous footprint cover (source/functional mapping review).
* **STAND_CONDITIONAL**: tree inventory proportions for CZ-BK1, IT-Ren, CH-Dav, etc. Can support alternative scenarios only with explicitly justified area-conversion assumptions.
* **HOLD**: FR-Hes (temporal), FI-Hyy (conflict), CH-Lae (conflict), FR-FBn (basal area), FR-Fon (basal area), IT-Noe (vegetated-only), CH-Fru (total cover), or any incomplete coverage; do not fabricate remaining percentages.

## Required preflight and promotion gates

1. Run existing read-only `scripts/01_preflight_observed22.py` (requires the 38-site CSV co-located one directory above the script). Inspect original baseline case per site; reject historical branch/sensitivity clones.
2. Inspect actual CIME/CTSM/FATES git revisions, `CaseDocs/lnd_in`, `fates_paramfile` and `fates_hlm_pft_map`; verify compatible PFT names/traits, and source code handling of FATES fixed biogeography and no competition for *this* executable/revision. Treat missing runtime flags as unknown, not false.
3. Obtain measured land-unit and PFT-area fractions with survey date, percentage denominator, tower footprint and uncertainty. Map deciduous needleleaf **Larix** separately from ENF; keep woody shrubs/grass distinct.
4. Prepare candidate one-point surface copies *only after* verifying required NetCDF variables, dimensions, closure, crop vs natural vs other landunits, and valid ranges. Keep lakes, soil, glacier, wetlands, crop, urban, bare area intact unless independently justified. Never modify the original surface in place.
5. Build isolated FULL and FIXNC configurations; check compile-time flags/namelist and do not reuse binaries blindly. `preview_namelists` plus `check_input_data`, and manually inspect outputs. Guard against differences in physics/phenology settings.
6. Submit **one 1–5 year smoke-test per arm** in isolated directories after explicit readiness review; inspect model logs, histories and actual per-PFT coverage; fail fast if FIXNC does not hold fractions and if FULL unintentionally has fixed PFT areas.
7. Stage long spinups (initial target **1000 years**, subject to convergence and local resource budget), monitoring in blocks. Do not claim 1000y proves convergence. Compare yearly C pools, 50/100y trend and carbon flux vs EC GPP/NEE; analyze repeated meteorological cycles and observation periods consistently.
8. Only scale beyond initially validated sites after smoke test and no inode/quota conflict. Record Git SHA, FATES git SHA, params SHA256, surface SHA256, DATM checksums, CO2 setting, compilers, case XML, Slurm options, checkpoint chain.

## Site cohort

`38_site_PFT_evidence.csv` defines the **22-candidate observational cohort**, not 22 approved FIXNC configurations. `scripts/02_make_dual_mode_plan.py` emits all candidate case names and conservative per-site readiness flags.

## No-action guarantee

Preparation today is documentation and read-only planning only. No IRIDIS case creation, CIME setup, compilation, NetCDF changes or Slurm submission. Do not call any legacy `09_submit_...` script as a shortcut.
