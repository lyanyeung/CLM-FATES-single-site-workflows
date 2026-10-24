# DK-Sor 2425-year analysis (24 October 2026)

## Evidence boundary

The user-provided IRIDIS6 monitor reported `DK-Sor_FATES_SPINUP500` at
**2425/3000 elapsed years**, with a coordinated checkpoint dated
`4421-01-01-00000` and no active continuation. This is an operator-reported
checkpoint, **not yet an independently executed 2425-year analysis**.
The GitHub plots previously released under
`carbon_flux_convergence_diagnostics/cases/DK-Sor/` used only **1715**
archived annual histories, so do not interpret those historical numbers as
the outcome after 2425 years.

## Correct forcing phase

- Case start year = 1996; completed model histories = 1996–4420 inclusive
  (2425 elapsed years).
- Original DATM and EC period = **1996–2024**, 29 years, `NO_LEAP`.
- 2425 = 83 complete 29-year forcing cycles + 18 additional model years.
- Last **complete** model cycle = 4374–4402, mapped one-to-one to original
  EC years 1996–2024.
- Previous complete cycle = 4345–4373 (for matched-phase diagnostics).
- The 18 model years 4403–4420 are included in carbon trajectory/drift
  analysis, but **excluded from the original-EC full-cycle comparison**.

## One-command workflow on IRIDIS6 (no `git pull` required)

The repository working tree might have unresolved merge conflicts. Fetch
and read the pinned GitHub entry point with `git show` instead of changing
the working tree.

```bash
set -euo pipefail
cd ~/CLM-FATES-single-site-workflows
git fetch origin main
SCRIPT="$HOME/DK_Sor_2425_analysis.py"
git show origin/main:examples/FLUXNET_MultiSite_6/scripts/29_plot_DK_Sor_2425yr.py > "$SCRIPT"
PY="$HOME/.conda/envs/clm_fates_env/bin/python"
"$PY" -B "$SCRIPT" --check-only
"$PY" -B "$SCRIPT" 2>&1 | tee "$HOME/DK_Sor_2425_analysis.log"
```

### Output and scientific methodology

This invokes the **unchanged** established
[`27_plot_six_site_latest_archived_convergence_to_RFS.py`](scripts/27_plot_six_site_latest_archived_convergence_to_RFS.py)
with `--sites DK-Sor`, using Git-pinned companion stage 14 and stage 10
helpers. The dedicated stage 29 entry verifies the exact archived annual
history coverage and reports an error rather than silently analysing an
incomplete 2425-year record. It warns if the three-component checkpoint
is no longer present on Scratch. Both source archives (Research Filestore
and Scratch) are searched.

Each run writes a new derived-only snapshot to:

```text
/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_6/convergence_snapshots/
  <UTCtimestamp>_DK_Sor_2425_archive_snapshot/
    DK-Sor/
      DK-Sor_01_carbon_pools_annual_mean.png
      DK-Sor_02_carbon_pools_last250years.png
      DK-Sor_04_FATES_PFT_VEGC_evolution.png
      DK-Sor_GPP_NEE_monthly_overview.png
      DK-Sor_carbon_annual_means.csv
      DK-Sor_convergence_metrics.csv
      DK-Sor_FATES_PFT_VEGC_annual_pct.csv
      DK-Sor_monthly_FATES_vs_EC.csv
      DK-Sor_monthly_metrics.csv
      DK-Sor_metadata.json
      DK-Sor_2425yr_REPORT.md
```

Science summary: all archived annual history years for the carbon pools,
latest 250 and 100 model-year linear drift checks, matched-phase changes
between adjacent 29-year forcing cycles, annual PFT vegetation-carbon shares,
and paired monthly GPP/NEE against the original FLUXNET EC data.

- Model GPP = `FATES_GPP`, model NEE = `-FATES_NEP`
- Original EC GPP = `GPP_DT_VUT_REF`; NEE = `NEE_VUT_REF`
- Units: `g C m^-2 d^-1`; paired monthly means require at least
  40 valid half-hours per day and 20 matched days per month.
- R2 is model skill `1 - SSE/SST`, not `corr^2`.
- Model-to-EC bias = model minus EC.
- The 1% drift criterion in stage 27 is **an exploratory screen**, not a
  universal ecosystem equilibrium criterion.

**Read-only sources:** No Slurm submissions, restart changes, model re-runs,
source NetCDF edits, surface changes or original-EC data edits. Only new
figures, tables and the report are written to Research Filestore.

The results **cannot be concluded** until the IRIDIS6 script has run and
the current snapshot CSVs have been inspected. The old 1715-year R2 and drift
metrics must not be reused as the 2425-year result.
