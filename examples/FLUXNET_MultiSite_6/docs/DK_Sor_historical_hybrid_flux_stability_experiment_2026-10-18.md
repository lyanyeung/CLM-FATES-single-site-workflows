# DK-Sor: 1000-year spin-up restart → historical hybrid pilot; flux stability experiment

**Record date:** 2026-10-18. **Status:** DK-Sor one-year hybrid case *prepared*, not yet submitted or scientifically verified. The 1000-year spin-up archive and 500/1000-year plots are complete for five sites (not DE-Hai).

## Scientific questions

1. **Can CLM-FATES reproduce observed GPP and NEE seasonality and interannual variability at EC towers?** Existing spin-up cycle comparisons are a useful baseline, but should not be confused with an independently initialized historical evaluation.
2. **Does a slowly drifting soil carbon pool matter for flux evaluation?** We must measure phase-aligned *model-model* differences in GPP, NEE, ecosystem respiration (RECO), and heterotrophic respiration (Rh) across the ~500- and ~1000-year checkpoints, alongside soil carbon trends. Similar EC R² scores alone do not establish flux stationarity.
3. **What changes when a real-calendar historical simulation starts from a spun-up state?** Compare a fixed-CO2 historical hybrid run with the same-year forcing from a spin-up cycle, then (separately) test documented transient historical CO2 and any other time-varying drivers.

## Existing spin-up setup and results

For the original cases named \`<SITE>_FATES_SPINUP500\`, forcing is site-specific, **authentic dated EC/ERA-based meteorology repeated cyclically** using \`CLM_USRDAT.UNSET:taxmode = cycle\` with first/last/align equal to the observed window. Atmospheric CO2 is fixed at the *first* forcing year's approximate global mean concentration. Spin-up accumulated 1000 model years, not 1000 distinct climate years.

The final 1000-year diagnostics are in [figures/spinup1000_final](../figures/spinup1000_final/). Five sites have 1000 complete annual land history files. DE-Hai is excluded from these five-site end-point results.

| Site | Forcing years | CO2 in spin-up (ppm) | Last complete 1000-year cycle | GPP monthly R² | NEE monthly R² |
|---|---|---:|---|---:|---:|
| RU-Fyo | 1998–2025 | 365.70 | 2950–2977 | 0.918 | −1.508 |
| DE-Tha | 1996–2025 | 361.93 | 2956–2985 | 0.729 | −1.365 |
| DK-Sor | 1996–2024 | 361.93 | 2953–2981 | 0.910 | 0.794 |
| NL-Loo | 1997–2025 | 363.04 | 2954–2982 | −0.023 | −1.710 |
| IL-Yat | 2000–2024 | 368.96 | 2975–2999 | −2.451 | −7.466 |

Recent \`TOTSOMC\` slopes remain positive (approximately 5.9–14.4 g C m⁻² model-year⁻¹ across five sites). This alone cannot establish that the instantaneous/monthly GPP and NEE flux responses are unstable. Conversely a low flux-model difference cannot justify claims of soil carbon equilibrium or long-term NEE carbon-budget fidelity.

**Carbon accounting caveat:** The published annual outputs satisfy \`TOTECOSYSC ≈ TOTSOMC + TOTLITC\` but record \`FATES_VEGC\` separately. Before applying total ecosystem C drift thresholds or inferring a net C balance, verify the FATES-specific accounting/units and avoid double counting.

**IL-Yat caveat:** \`FATES_STRUCTC\` is zero from model year 132 onward in the published annual means. Diagnose PFT/cohort representation and recruitment/mortality before using that result as a forest benchmark. This is a warning signal, not a concluded cause.

## Experiment design

### A. Flux-stability control (highest-priority scientific test)

Read **annual h0a model outputs** around the 500- and 1000-year checkpoints; recover daily/monthly fluxes with the verified mappings from \`scripts/10_compare_six_site_latest_complete_cycle.py\`. Pair only **identical forcing-year phases**; do *not* compare arbitrary terminal years, which have different meteorology.

For each site, compare the last complete forcing cycle at or before 500 elapsed years with the last at or before 1000:

- RU-Fyo: 449–476 vs 953–980 elapsed model years (1998–2025 forcing phase)
- DE-Tha: 451–480 vs 961–990 (1996–2025)
- DK-Sor: 465–493 vs 958–986 (1996–2024)
- NL-Loo: 465–493 vs 958–986 (1997–2025)
- IL-Yat: 476–500 vs 976–1000 (2000–2024)

These pairs are **phase-aligned** but separated by different amounts of elapsed spin-up time. Use (a) month-by-month model-model RMSE and bias; (b) annual mean and seasonal-cycle changes; (c) paired GPP and NEE EC skill differences; (d) Rh, Ra, and RECO if corresponding history fields are available; (e) LAI, FATES vegetation carbon/structure, soil moisture; (f) drift/cycle change in soil, litter, vegetation C. Negative NEE R² is possible; do not use near-zero mean NEE as a percentage-change denominator.

Pre-register practical *flux-tolerance* thresholds based on EC uncertainty/seasonal amplitude. Mark sites as flux-stable only if paired model fluxes and respiration are demonstrably insensitive to checkpoint (not only their R²). Report SOC drift separately.

### B. DK-Sor one-year historical hybrid pilot (technical feasibility)

**Original CIME case:** \`/iridisfs/scratch/ly3n24/CLM_FATES/cases/DK-Sor_FATES_SPINUP500\`

**Isolated pilot:** \`/iridisfs/scratch/ly3n24/CLM_FATES/cases/DK-Sor_FATES_HIST1996_2024_TEST\`

**Restart archive:** \`/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive/DK-Sor_FATES_SPINUP500/rest/2996-01-01-00000/\`

All five 1000-year restart sets were observed present on IRIDIS6, with CLM, coupler, DATM restart files plus dated rpointer files. The DK-Sor pilot was cloned using \`create_clone --keepexe\`; the existing working shared executable is \`/scratch/ly3n24/CTSM_FATES_OUTPUTS/GF-Guy_FATES_SURF2000_CO2405_1PT/bld/cesm.exe\`.

| Key | Prepared value |
|---|---|
| RUN_TYPE | hybrid |
| CONTINUE_RUN | FALSE |
| RUN_REFCASE | DK-Sor_FATES_SPINUP500 |
| RUN_REFDATE / RUN_REFTOD | 2996-01-01 / 00000 |
| RUN_STARTDATE | 1996-01-01 |
| GET_REFCASE | FALSE (reference state already staged manually) |
| STOP_OPTION / STOP_N | nyears / 1 |
| REST_OPTION / REST_N | nyears / 1 |
| RESUBMIT | 0 |
| CALENDAR / ATM_NCPL | NO_LEAP / 48 |
| CLM_CO2_TYPE / CCSM_CO2_PPMV | constant / 361.93 |
| DATM year_first / year_last / year_align | 1996 / 2024 / 1996 |
| MPI_RUN_COMMAND | srun --mpi=pmix --ntasks=1 --cpus-per-task=1 --cpu-bind=cores |

The prepared land namelist contains:
\`finidat = 'DK-Sor_FATES_SPINUP500.clm2.r.2996-01-01-00000.nc'\`,
and the **DK-Sor** surface NetCDF (\`surfdata_DK-Sor_hist_2000_16pfts_c261011.nc\`), not the GF-Guy surface.

The preparation run emitted \`PREPARATION COMPLETE — NOT SUBMITTED\`, and \`preview_run\` showed one node/one task. **The last observed \`BUILD_COMPLETE\` was \`FALSE\`**, after \`case.setup --reset\`. No successful pilot simulation has been reported. Independently verify shared build lineage/executable before marking this clone ready; do not rebuild the shared executable or edit original spin-up.

**Caution:** Restart model time is 2996-01-01, which is *not* a 29-year meteorological cycle boundary (the old state follows the preceding cycle phase). Starting the new model calendar at 1996-01-01 can abruptly change meteorological forcing. Review first-year flux, soil moisture, and cohort trajectories for initialization shock. An existing DATM/coupler restart must not be assumed to transfer cleanly to the rewound model calendar simply because CLM \`finidat\` resolves. For a hybrid pilot, inspect model-specific DATA/time alignment and restart semantics; if necessary, initialize DATM fresh while keeping the land restart, without overwriting the original archive.

**Historical preparation script:** [17_prepare_DK_Sor_historical_pilot.sh](../scripts/17_prepare_DK_Sor_historical_pilot.sh), archived to reproduce the original preparation logic. It is not an instruction to re-run against an already existing case.

**Non-mutating preflight:** [18_audit_DK_Sor_historical_pilot.sh](../scripts/18_audit_DK_Sor_historical_pilot.sh), checks metadata, build state, staged restart files and DATM/site inputs. A pass is **not** evidence of runtime success.

### C. Controlled historical comparisons (after successful one-year pilot)

1. Extend DK-Sor to historical 1996–2024 once the one-year hybrid pilot is checked (no accidental 29-year forcing recycling beyond the observation window).
2. Compare historical **fixed-CO2** (same 361.93 ppm) against the 1000-year spin-up's **phase-aligned** 1996–2024 forcing cycle. This isolates calendar reset/restart effects and quantifies any restart shock.
3. Separately enable true **historical-varying CO2** using a documented time-varying input/stream; do not equate \`CLM_CO2_TYPE=diagnostic\` by itself with a verified CO2 trajectory. Differences then measure the CO2-forcing intervention.
4. Quantify daily/monthly EC skill, GPP, NEE, RECO/Rh (where available), LAI and vegetation structure. Use identical overlap/quality filters across comparisons.
5. Only after DK-Sor is validated expand to RU-Fyo, DE-Tha and NL-Loo. Keep IL-Yat on hold pending FATES structural-C diagnosis. Do not alter \`<SITE>_FATES_SPINUP500\` originals.

## Safety / provenance

- No Slurm jobs submitted by either repository script; no model success claimed.
- \`BUILD_COMPLETE=FALSE\` is a **known blocker**, not permission to unconditionally bypass build integrity checks.
- Do not upload restricted EC time series, DATM NetCDF, CIME restarts, site-specific private data, raw forcing/QC packages, passwords/keys or large model archives to this public repository.
- Model and EC comparison plots, aggregated scores and clearly documented reproducible code may be published when verified for redistribution.
- Current record describes an experimental proposal and observed setup output, not a completed transient evaluation.
