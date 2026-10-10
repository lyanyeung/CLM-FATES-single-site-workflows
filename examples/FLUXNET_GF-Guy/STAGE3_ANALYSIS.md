# GF-Guy Stage 3: 300-year convergence and final-cycle EC comparison

This package adds **analysis-only code** after the GF-Guy Stage 1 surface/CO2
setup and Stage 2 300-year spin-up. It does not submit, modify, or restart a
CTSM/FATES case. No raw EC files, model NetCDFs, or generated graphics are
committed to GitHub.

## Verified simulation provenance (from IRIDIS logs)

- Case: `GF-Guy_FATES_SPINUP300_CO2405`
- Starting model year: 2017; final simulated year: 2316 (restart at 2317-01-01)
- `CLM_CO2_TYPE=constant`, `CCSM_CO2_PPMV=405.0`
- 2017-2021 no-leap DATM meteorology, `taxmode=cycle`, repeated 60 times
- 300 annual `*.clm2.h0a.*.nc` history files archived
- Last CIME archive completed successfully; `RESUBMIT=0`

## One command on IRIDIS6

After copying this entire Stage 3 folder into an existing checkout of the
repository on IRIDIS, with the Stage 1 `scripts/00_config.sh` in place:

```bash
conda activate clm_fates_env
cd /path/to/CLM-FATES-single-site-workflows/examples/FLUXNET_GF-Guy
bash scripts/15_run_stage3_analysis.sh
```

Alternatively run each Python script independently:

```bash
HIST=/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive/GF-Guy_FATES_SPINUP300_CO2405/lnd/hist
SITE=/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/GF-Guy

python scripts/13_plot_spinup300_convergence.py \
  --archive "$HIST" \
  --output "$SITE/spinup300_diagnostics"

python scripts/14_compare_final_cycle_ec.py \
  --hist "$HIST" \
  --obs "$SITE/forcing/raw/ICOSETC_GF-Guy_ARCHIVE_L2/ICOSETC_GF-Guy_FLUXNET_HH_L2.csv" \
  --out "$SITE/spinup300_diagnostics/EC_final_cycle"
```

The **HH file is explicit**, avoiding ambiguity with the DD, MM, WW, and YY
exports from the same `ICOSETC_GF-Guy_ARCHIVE_L2` archive.

## Outputs

Generated below `$SITE/spinup300_diagnostics/`:

- `01_carbon_pools_annual_mean.png` — annual means of three carbon pools
- `02_annual_pct_change.png` — ordinary adjacent-model-year changes
- `03_same_forcing_5yr_pct_change.png` — compare with identical forcing phase, 5 model years earlier
- `04_annual_GPP_NEE.png` — annual mean daily-rate GPP and NEE
- `05_last_30_years_drift.png` — late-stage carbon stock drift
- `GF-Guy_annual_spinup300.csv` — all 300 annual means and relative changes
- `GF-Guy_5yr_cycle_means.csv` — means from each 5-year forcing cycle
- `GF-Guy_final_convergence_summary.csv` — last-cycle % change and absolute trend diagnostics

In `EC_final_cycle/`:

- `GF-Guy_GPP_monthly_EC2017-2021_FATES2312-2316.png`
- `GF-Guy_NEE_monthly_EC2017-2021_FATES2312-2316.png`
- `GF-Guy_final_cycle_daily_FATES_vs_EC.csv`
- `GF-Guy_final_cycle_monthly_FATES_vs_EC.csv`
- `GF-Guy_final_cycle_FATES_vs_EC_metrics.csv`

## Research interpretation

### Convergence

`TOTECOSYSC` and `TOTSOMC` history variables are in `g C m-2`.
`FATES_VEGC` is in `kg C m-2`; the script multiplies it by 1000 to compare
stocks in `g C m-2`. `FATES_GPP` and `FATES_NEP` are in
`kg C m-2 s-1`; multiplying by `1000 * 86400` produces
`g C m-2 day-1`. Atmospheric CO2 remains fixed at **405 ppm**.

The diagnostic compares annual history *means*. A difference between two
5-year cycle means divided by 5 gives an approximate drift per model year.
The same-forcing-year percentage change compares a model year with five
model years earlier. Adjacent-year percentage differences mix meteorological
variation and changing ecological state, so they are less direct indicators
of equilibrium. The last 30 years contain six complete forcing cycles.

**No automatic pass/fail is imposed.** FATES can have demographic variability,
so low drift in bulk pools is not sufficient evidence of demographic steady
state. End-of-cycle restart states may be needed for a stricter test.

### EC GPP/NEE validation, matching ES-LJu 09 style

Model years 2312-2316 map onto EC observation years 2017-2021:

| Model year | Observed forcing/EC year |
|---|---|
| 2312 | 2017 |
| 2313 | 2018 |
| 2314 | 2019 |
| 2315 | 2020 |
| 2316 | 2021 |

For leap year **2020**, omit Feb 29 from the EC observations: the model uses
`NO_LEAP` and has 365 daily records. Model daily timestamps are checked using
CF time bounds when present (or start-of-interval obtained from end times),
so an `h0a` filename dated Jan 2 does not cause a one-day mismatch.

Variable choices:

- FATES GPP: `FATES_GPP`
- FATES NEE: `-FATES_NEP`
- EC GPP: prefer `GPP_DT_VUT_REF`; use `GPP_NT_VUT_REF` **only when DT is absent**
- EC NEE: `NEE_VUT_REF`

EC conversion assumes EC NEE/GPP input units `µmol CO2 m-2 s-1`:
`86400 * 12.0107e-6` to `g C m-2 day-1`.

Daily EC aggregates require at least **40 valid half-hour records**. Monthly
model/EC paired averages require **20 matched daily values**, independently
for GPP and NEE. Models and observations both use **solid lines**; only the
NEE zero reference is dashed. NEE uptake (negative) follows tower convention.

The metrics include daily and monthly `N`, Pearson `R`, model efficiency
`R2 = 1 - sum((model-observation)^2) / sum((observation-mean_obs)^2)`,
`RMSE`, `MAE`, and `Bias` (FATES minus EC). **`R2` is not `R**2`**, matching
`examples/ICOS_ES-LJu/scripts/09_compare_fates_ec.py`.

## Testing and restrictions

```bash
python -m unittest discover -s tests -v
bash -n scripts/15_run_stage3_analysis.sh
```

Tests use synthetic data only. This Stage 3 implementation passes tests for
no-leap date mapping, 30-min EC aggregation, HH source selection, and the R2
definition; the 300-year convergence routine was also exercised against 300
synthetic annual history files. **IRIDIS real-data results need a fresh run
and scientific review before calling the analysis validated.**

No command in these scripts calls `case.setup`, `case.submit`, `xmlchange`,
`case.build`, or removes archived NetCDF/restart files.
