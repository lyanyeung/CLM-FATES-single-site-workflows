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

## Verified DK-Sor stage-29 results — 2026-10-24

The operator executed Stage 29 successfully, and reported `Status=OK`
with **2425/2425** unique archived annual `h0a` histories, no missing years,
a matching 4421 checkpoint, and an original-EC flux comparison with
340 matched months per metric.

Authoritative RFS result location (derived outputs, not inputs):

```text
/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_6/convergence_snapshots/20261024T100510Z_DK_Sor_2425_archive_snapshot/
```

| Carbon pool | Last 100y drift (%) | Last 250y drift (%) | Phase-aligned adjacent-cycle absolute mean change (%) |
|---|---:|---:|---:|
| TOTECOSYSC | +1.153824 | +2.819 | 0.365077 |
| TOTSOMC | +1.142844 | +2.880 | 0.364869 |
| TOTLITC | +1.645038 | +0.108 | 0.562725 |
| FATES_VEGC | -2.224546 | -1.853 | 2.066402 |
| FATES_STOREC | -1.104 | -0.437 | 2.106 |
| FATES_STRUCTC | -2.537 | -2.189 | 2.534 |

All shown metrics failed the project's exploratory 1% stage-27 convergence
screen. Soil carbon continues increasing, while vegetation carbon decreases.
**Classification: incomplete convergence by the selected project screen; the
2425-year spin-up must not be labeled fully equilibrated.**

| Original EC vs model (paired monthly, 1996–2024) | GPP | NEE |
|---|---:|---:|
| Valid paired months | 340 | 340 |
| Correlation R | 0.969 | 0.932 |
| Skill R2 = 1 - SSE/SST | 0.912177 | 0.790629 |
| RMSE (g C m^-2 d^-1) | 1.504133 | 1.309300 |
| Model − EC bias (g C m^-2 d^-1) | -0.604326 | +0.647671 |

The final dominant PFT is
`broadleaf_colddecid_extratrop_tree`, consistent at broad class level with
the tower's DBF biome. This does not validate PFT areal shares or site-level
land-surface fractions. High monthly flux skill alone does not imply soil or
whole-ecosystem carbon equilibrium. The listed scores apply to **model years
4374–4402 mapped onto original EC years 1996–2024**, not to the residual 18
model years after that cycle.

### Upload original derived figures, CSV, JSON and report to GitHub

A single-site publication script is provided at
[`30_publish_DK_Sor_2425_to_github.py`](../scripts/30_publish_DK_Sor_2425_to_github.py).
It validates all original Stage 29 output files and the exact 2425-year
metadata, creates SHA256 checksums, and uses a fresh checkout so a local
unmerged Git working tree is not modified. It copies **only** the four PNG
figures, generated CSV summaries, JSON metadata, and the generated Markdown
report into the repository's `figures/convergence_snapshots/` folder.

On IRIDIS6:

```bash
set -euo pipefail
cd ~/CLM-FATES-single-site-workflows
git fetch origin main
git show origin/main:examples/FLUXNET_MultiSite_6/scripts/30_publish_DK_Sor_2425_to_github.py > "$HOME/DK_Sor_2425_publisher.py"
"$HOME/.conda/envs/clm_fates_env/bin/python" -B "$HOME/DK_Sor_2425_publisher.py" --dry-run
"$HOME/.conda/envs/clm_fates_env/bin/python" -B "$HOME/DK_Sor_2425_publisher.py"
```

The source RFS outputs remain untouched. **Until the publisher reports
`GITHUB PUBLISH SUCCESS`, the original PNG/CSV/JSON files have not been
proven uploaded**. This documentation preserves the numerical results
independently of that publication step.
