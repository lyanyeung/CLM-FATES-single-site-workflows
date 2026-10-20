# Nine-site 1000-year plotting: executed Home → RFS → GitHub workflow

**Updated 20 October 2026 after successful plotting and transfer.** Nine successful cases: BE-Bra, FR-Fon, GL-ZaH, AT-Neu, FI-Sod, CH-Cha, CH-Fru, CH-Lae, CZ-Stn. IT-Noe and CH-Aws are excluded. Model completion does not establish carbon equilibrium or scientific agreement with eddy-covariance observations.

## Canonical code

- [19_plot_nine_site_spinup1000.py](../scripts/19_plot_nine_site_spinup1000.py) — reads archived h0a NetCDF and original HH EC tower releases under `forcing/raw*`; produces carbon convergence and monthly GPP/NEE figures.
- [20_submit_nine_site_plots_home.sh](../scripts/20_submit_nine_site_plots_home.sh) — Slurm submission, **writes only Home** on compute nodes.
- [21_transfer_nine_site_plots_to_rfs.sh](../scripts/21_transfer_nine_site_plots_to_rfs.sh) — login-node-only rsync transfer, full checksum comparison, retained verification receipt.
- [22_publish_nine_site_plots_github.sh](../scripts/22_publish_nine_site_plots_github.sh) — publish selected derived PNG/CSV/metadata and update README. **Home deletion requires `--cleanup-home-after-push`.**

The new scripts supplement the original Stage17/18 executed model code. They do not alter CIME cases, restart files, or source observation data.

## Verified storage environment

- User's RFS NFS mount on **login nodes**: `/research/xclimatetbm/ly3n24`.
- Completed results: `/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_11/spinup1000_final/`.
- Slurm 4490812 failed early on compute node red6066: `Permission denied: '/research'`; RFS was **not** accessible there. Do not direct compute-node stdout/stderr, Matplotlib cache, or TMPDIR to RFS.
- Slurm 4492378 successfully ran the 9-site plotter using a Home staging area. This produced 9 `Status=OK` rows, 27 PNG figures, 73 result files. The files were then transferred to RFS on the login node; rsync checksum comparison passed. The RFS summary's `Directory` column was corrected to the RFS destination.
- Source data in `/scratch` / `/iridisfs/scratch` are **READ ONLY**. Scratch may contain ongoing spin-ups, which are completely independent of this workflow.

## Repeat the workflow from a clean checkout on IRIDIS6

Use a separate clean Home checkout because the original `~/CLM-FATES-single-site-workflows` may have unrelated unresolved Git conflicts:

```bash
git clone https://github.com/lyanyeung/CLM-FATES-single-site-workflows.git "$HOME/CLM-FATES-11site-repro"
cd "$HOME/CLM-FATES-11site-repro"
bash examples/FLUXNET_MultiSite_11/scripts/20_submit_nine_site_plots_home.sh
```

Check the printed Slurm job ID and wait until `sacct -j <JOBID>` reports `COMPLETED 0:0`. The submission script creates `~/.plot11_1000_latest` pointing at the exact Home staging path. It refuses to overwrite an existing pointer.

On the **login node**, after Slurm completion:

```bash
cd "$HOME/CLM-FATES-11site-repro"
bash examples/FLUXNET_MultiSite_11/scripts/21_transfer_nine_site_plots_to_rfs.sh
bash examples/FLUXNET_MultiSite_11/scripts/22_publish_nine_site_plots_github.sh
```

By default, the publishing script **preserves** the Home staging results. Only after examining the transfer verification receipt and confirming GitHub visibility, optionally run:

```bash
bash examples/FLUXNET_MultiSite_11/scripts/22_publish_nine_site_plots_github.sh --cleanup-home-after-push
```

This removes the exact Home staging directory identified by the run pointer, not the clean Git checkout or any Scratch directory. The script requires a receipt, successful GitHub push and checksum identity for transferred files before allowing deletion.

## Published versus retained artifacts

RFS contains all nine per-site `carbon_annual_means.csv`, `monthly_FATES_vs_EC.csv` time series, `convergence_metrics.csv`, `monthly_metrics.csv`, 27 PNGs, per-site metadata and nine-site summary (73 result files), plus transfer records/logs.

GitHub contains only the selected derived 27 PNGs, site convergence and monthly skill metrics, per-site metadata, nine-site summary and code/README. **Never publish raw tower EC HH CSV, detailed paired time-series tables, NetCDF history/restart files, Slurm logs or credentials.**

Negative `R²` is possible and indicates poorer skill than the observation-mean baseline. Notable diagnostics include GL-ZaH GPP `R² ≈ -38.55` and NEE `R² ≈ -60.05`; further scientific investigation is required before conclusions are drawn.

## Historical instructions

Earlier versions of this document suggested direct plotting to RFS from Slurm compute nodes and a guessed Python executable location. **Those steps are obsolete on this verified IRIDIS6 setup.** Use scripts 20–22 above rather than attempting the older compute-node RFS configuration.
