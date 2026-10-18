# DK-Sor: fixed vs historical atmospheric CO₂ in CLM-FATES

**Experiment record: 18 October 2026.** This is a planned controlled comparison, not a publication of final modeled CO₂ effects. **The NOAA historical case was submitted and its first annual run was observed running; complete 1996–2024 output and active CO₂ ingestion are not yet verified.**

[Parent six-site experiment](../../README.md) · [Read-only status tool](scripts/01_status_readonly.sh) · [Comparison and plotting code](scripts/02_compare_historical_fluxes.py) · [Existing initialization design](../../docs/DK_Sor_historical_hybrid_flux_stability_experiment_2026-10-18.md)

## Scientific question

**Does replacing fixed atmospheric CO₂ with observed global historical CO₂ alter the ability of CLM-FATES to reproduce eddy-covariance GPP and NEE at DK-Sor during 1996–2024?**

We will examine changes in seasonal variability, annual mean, interannual variability and systematic bias, as well as the difference between the two simulations. This is a CO₂-forcing sensitivity test, *not* evidence that any model–EC difference is caused only by CO₂ unless all other configuration inputs and initialization are demonstrated identical.

## Why DK-Sor and why this comparison?

DK-Sor has a long ICOS FLUXNET flux and meteorological record covering 1996–2024. The existing site workflow ran 1000 model years with the 29-year meteorological forcing repeated and CO₂ fixed at 361.93 ppm. The archived 1000-year state is the shared initialization source for the historical experiments. Slow soil carbon pools continue drifting; similar 500/1000-year EC flux skill does not independently establish carbon or flux equilibrium.

One-year fixed historical hybrid pilot **completed** (Slurm 4396583 run; 4396584 archive) and its 1996 annual h0a output and 1997-01-01 restart were observed present.

## Experimental design

| Comparison | Fixed historical control | NOAA historical atmospheric CO₂ |
|---|---|---|
| Case | `DK-Sor_FATES_HIST1996_2024_TEST` | `DK-Sor_FATES_HIST1996_2024_NOAA_CO2` |
| Initial vegetation/soil state | 1000-year DK-Sor spin-up restart, model 2996-01-01 | Same original DK-Sor spin-up restart, model 2996-01-01 |
| Historical chronology | 1996–2024, once | 1996–2024, once |
| Meteorology | DK-Sor 1996–2024 (existing CLM_USRDAT) | Same, independently verify stream |
| Atmospheric CO₂ | 361.93 ppm constant | NOAA GML globally averaged marine-surface *monthly* CO₂ |
| CLM_CO2_TYPE | `constant` | `diagnostic` |
| CCSM_BGC | `none` | `CO2A` |
| DATM_CO2_TSERIES | `none` | `cmip6_20tr` plus case-local NOAA stream override |
| Timing | First year (1996) verified complete; rest NOT verified | First job 4397132 submitted and model started; remaining chain NOT verified |

The NOAA source is `https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_gl.csv`. The generated candidate NetCDF covers **1995–2025** for edge interpolation but the model experiment covers **1996–2024** only. Download audit showed January 1996 = 362.14 ppm, December 2024 = 425.20 ppm. These are input series values, **not yet independently verified values in model history**.

The historical case's CDEPS CO₂ stream requires `CO2 Sa_co2diag`. The installed CDEPS accepted `DATM_CO2_TSERIES=cmip6_20tr` (not the older token `20tr`). Its `user_nl_datm_streams` comments must begin with `!` rather than `#`. Only the NOAA case's own namelist overrides and generated CIME files were modified; no changes to other sites, global CTSM source or shared executable.

**Interpretation caveat:** `CCSM_BGC=CO2A` and `CLM_CO2_TYPE=diagnostic` need runtime verification. In particular, check whether the coupler/executable routes `Sa_co2diag` to the land component correctly, inspect emitted stream / log metadata, and confirm dynamic CO₂ is actually used by FATES. A completed job alone does not prove this.

## Planned evaluation

1. Verify archive completion for both historical cases and a continuous series of 29 annual h0a files, 1996–2024; monitor any failed resubmissions.
2. Validate NOAA stream timing and CO₂ levels at model runtime, and check for hybrid initialization shock after remapping restart time from 2996 to 1996.
3. Read `FATES_GPP` and `FATES_NEP` from annual land history with units checked, using `FATES_NEE = -FATES_NEP` (positive NEE denotes ecosystem carbon loss). Convert kg C m⁻² s⁻¹ to g C m⁻² d⁻¹.
4. Compare daily and monthly FATES GPP/NEE to ICOS FLUXNET observations using the **same sample mask** and observation product for both runs. Report sample count, R² (1 - SSE/SST), R, RMSE, MAE and bias. Add GPP and NEE seasonal plots and annual sums; respiration, LAI and soil pools where available.
5. Quantify direct model-model differences `NOAA - Fixed` for monthly GPP/NEE, as well as whether NOAA changes EC agreement. Do not assume improvement without calculated outcomes.
6. Optional extension: compare 500- and 1000-year **phase-aligned** spin-up outputs, and separately test quality-reviewed tower CO₂. DK-Sor tower `CO2_F_MDS` QC audit passed 302/348 months under conservative daytime QC0 criteria; tower data are not interchangeable with NOAA atmospheric background CO₂.

**Critical comparator limitation:** The fixed-control case has **only 1996 confirmed completed** as of this record. Do *not* interpret a 29-year NOAA run versus a one-year control as a full paired 29-year experiment. The fixed-control must first finish the remaining 1997–2024 years without altering its 1996 historical initialization.

## Read-only code

Both repository scripts **never submit/cancel jobs, modify CIME cases, rebuild the shared `cesm.exe`, or edit historical forcing**.

```bash
conda activate clm_fates_env
cd ~/CLM-FATES-single-site-workflows
git pull --ff-only origin main

# Read-only: queue, archived model years, latest checkpoints, CaseStatus
bash examples/FLUXNET_MultiSite_6/experiments/DK-Sor_CO2_sensitivity/scripts/01_status_readonly.sh

# Interim diagnostic: minimum one COMPLETE common archived year
python examples/FLUXNET_MultiSite_6/experiments/DK-Sor_CO2_sensitivity/scripts/02_compare_historical_fluxes.py --min-years 1

# Final 29-year comparison; intentionally fails if the control is incomplete
python examples/FLUXNET_MultiSite_6/experiments/DK-Sor_CO2_sensitivity/scripts/02_compare_historical_fluxes.py --min-years 29
```

The plotting script imports the existing `scripts/10_compare_six_site_latest_complete_cycle.py` helper; it does not re-implement NetCDF timebounds, GPP/NEE flux sign or units. It writes generated plots and a local paired model/EC monthly table to the local `DK-Sor/validation/historical_fixed_vs_NOAA/` directory, **not to GitHub**. Inspect quality criteria and source data licensing before publishing any underlying EC observations.

## IRIDIS6 history and safety

- Original 1000-year spin-up: `DK-Sor_FATES_SPINUP500` (case name retained after continuation). Leave it untouched; other fixed-CO₂ sites and separate 3000-year spin-up chains may be active.
- Fixed control: `DK-Sor_FATES_HIST1996_2024_TEST` — 1996 successful; additional 28 years not reported.
- NOAA historical case: `DK-Sor_FATES_HIST1996_2024_NOAA_CO2`; initial `case.run` Slurm job 4397132, `case.st_archive` job 4397133. At last seen queue, 4397132 was in `CG` (completing), which is not a proven success.
- These experiments are isolated CIME cases with distinct RUN/DOUT paths. Do not rerun preparation/recovery scripts or submit active cases blindly.
- No raw tower data, model histories, restarts, forcing NetCDF, credentials or individual EC time series are stored in this public repository.

## Output plan

After both runs finish and are audited, publish plots of monthly GPP/NEE (EC, fixed, NOAA) and a concise aggregated-skill table, with metrics and clear data provenance. Until then, **there are no published CO₂-treatment effects**.
