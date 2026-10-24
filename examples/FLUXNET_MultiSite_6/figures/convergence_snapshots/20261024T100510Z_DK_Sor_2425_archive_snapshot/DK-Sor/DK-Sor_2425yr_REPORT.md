# DK-Sor — 2425-year spin-up diagnostics

Generated from original stage-27 repository analysis on archived annual h0a NetCDF.
No model or EC source data modified.

- Elapsed spin-up: 2425 years; annual model histories: 1996-4420
- Latest available coordinated three-component Scratch checkpoint: 4421
- Last **complete** 29-year forcing cycle: model 4374-4402, mapped onto original EC years 1996-2024
- Incomplete tail excluded from EC comparison: model 4403-4420
- Model flux definitions: GPP = FATES_GPP; NEE = -FATES_NEP
- EC definitions: GPP_DT_VUT_REF; NEE_VUT_REF
- EC comparison unit: g C m^-2 d^-1; model vs EC matched monthly mean values

## Carbon-pool trends and phase-aligned convergence

| Variable | Last 100y trend (%) | Last 250y trend (%) | Adjacent-cycle mean absolute change (%) | Stage-27 1% exploratory screen |
|---|---:|---:|---:|---|
| TOTECOSYSC | 1.154 | 2.819 | 0.365 | NOT_LOW_OR_UNDETERMINED |
| TOTSOMC | 1.143 | 2.880 | 0.365 | NOT_LOW_OR_UNDETERMINED |
| TOTLITC | 1.645 | 0.108 | 0.563 | NOT_LOW_OR_UNDETERMINED |
| FATES_VEGC | -2.225 | -1.853 | 2.066 | NOT_LOW_OR_UNDETERMINED |
| FATES_STOREC | -1.104 | -0.437 | 2.106 | NOT_LOW_OR_UNDETERMINED |
| FATES_STRUCTC | -2.537 | -2.189 | 2.534 | NOT_LOW_OR_UNDETERMINED |

Stage-27 thresholds are project-specific screening criteria, not a scientific certificate of full ecosystem equilibrium. Always inspect the trajectories.

## Last full cycle vs original EC tower

| Flux | Matched months | Correlation (R) | Skill R2 | RMSE | Model minus EC bias |
|---|---:|---:|---:|---:|---:|
| GPP | 340 | 0.969 | 0.912 | 1.504 | -0.604 |
| NEE | 340 | 0.932 | 0.791 | 1.309 | 0.648 |

RMSE and bias are in g C m^-2 d^-1. R2 = 1 - SSE/SST (not R squared).
Results reflect the original dynamic-competition Full FATES configuration; a good flux fit does not independently establish realistic PFT, soil or carbon-pool equilibrium.

## Figures

- DK-Sor_01_carbon_pools_annual_mean.png
- DK-Sor_02_carbon_pools_last250years.png
- DK-Sor_04_FATES_PFT_VEGC_evolution.png
- DK-Sor_GPP_NEE_monthly_overview.png

Full source provenance and quantitative tables are in the companion metadata.json and CSV files.
