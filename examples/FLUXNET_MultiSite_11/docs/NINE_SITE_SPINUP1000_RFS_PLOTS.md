# Nine-site 1000-year spin-up plots — scratch-read-only workflow (2026-10-20)

The 11-site experiment has **nine archived 1000-year cases** (BE-Bra, FR-Fon, GL-ZaH, AT-Neu, FI-Sod, CH-Cha, CH-Fru, CH-Lae and CZ-Stn). IT-Noe and CH-Aws are excluded. Spin-up completion does **not** imply scientific equilibrium; forcing and land-cover QC remain provisional.

The plotting script is [scripts/19_plot_nine_site_spinup1000.py](../scripts/19_plot_nine_site_spinup1000.py), adapted from the six-site [1000-year diagnostics](../../FLUXNET_MultiSite_6/scripts/14_plot_five_site_spinup1000.py) and eight-site [seven-site plotting code](../../FLUXNET_MultiSite_8/scripts/18_plot_seven_site_spinup500.py). It reuses the six-site carbon-pool and EC functions, including aligned forcing cycles. The actual case naming is `<SITE>_FATES_SPINUP500_11P` (despite the 1000-year length).

**No Scratch writes are intended:** model inputs under `/scratch` and `/iridisfs/scratch` are opened for reading only. All NEW output, matplotlib cache, Python cache, temp files and scheduler logs must be on verified Research Filestore (RFS) or non-scratch home directories.

## 1. Establish the RFS path on IRIDIS6 (not guessed)

Use your **actual, existing** Research Filestore mount path; contact IRIDIS support if it is only available on another access host. Do not assume it is `/research` or `/mnt`. Example shell:

```bash
export REPO="$HOME/CLM-FATES-single-site-workflows"
export RFS_BASE="/ABSOLUTE/ACTUAL/RFS/PATH/accessible/from/IRIDIS6"
test -d "$RFS_BASE" || { echo "RFS is not mounted here"; exit 1; }
df -T "$RFS_BASE"
realpath "$RFS_BASE"
# Ensure the real target is NOT scratch, including symlinks:
case "$(realpath "$RFS_BASE")/" in /scratch/*|/iridisfs/scratch/*) echo "REFUSING SCRATCH"; exit 1;; esac
test -w "$RFS_BASE" || { echo "RFS not writable"; exit 1; }
export PLOTROOT="$RFS_BASE/CLM_FATES/FLUXNET_MultiSite_11/spinup1000_final"
```

Do not run `git pull` inside the existing IRIDIS clone until its unrelated unmerged files are resolved. Instead obtain this added plotting script using a separate clean clone under `$HOME` or transfer the script from GitHub; do not change the spin-up cases. If using a fresh clone:

```bash
git clone https://github.com/lyanyeung/CLM-FATES-single-site-workflows.git "$HOME/CLM-FATES-eleven-plotting"
export REPO="$HOME/CLM-FATES-eleven-plotting"
```

## 2. Check source files without writing output

```bash
conda activate clm_fates_env
export PYTHONDONTWRITEBYTECODE=1
python -B "$REPO/examples/FLUXNET_MultiSite_11/scripts/19_plot_nine_site_spinup1000.py" \
  --repo "$REPO" --output-root "$PLOTROOT" --preflight
```

The script demands **1000 consecutive annual h0a files** from each site's actual case name, checks the DATM forcing-cycle stream, and looks for EC HH data. Missing EC data/ambiguity is reported for review; use `--obs-csv SITE=/absolute/HH.csv` to resolve explicitly. No input files or case XML are rewritten.

## 3. Run on a compute node with caches/logs off Scratch

Create directories on verified RFS **only after the mount check above**. Avoid the standard Slurm default output file in the current working directory if that directory is on scratch:

```bash
mkdir -p "$PLOTROOT" "$RFS_BASE/CLM_FATES/joblogs" "$RFS_BASE/CLM_FATES/cache/mpl" "$RFS_BASE/CLM_FATES/cache/xdg" "$RFS_BASE/CLM_FATES/tmp"
export MPLCONFIGDIR="$RFS_BASE/CLM_FATES/cache/mpl"
export XDG_CACHE_HOME="$RFS_BASE/CLM_FATES/cache/xdg"
export TMPDIR="$RFS_BASE/CLM_FATES/tmp"
export TMP="$TMPDIR" TEMP="$TMPDIR" PYTHONDONTWRITEBYTECODE=1
# Submit from HOME, explicitly redirect BOTH batch logs outside Scratch.
cd "$HOME"
sbatch --job-name=eleven9_plots --partition=batch --nodes=1 --ntasks=1 \
  --cpus-per-task=2 --mem=12G --time=08:00:00 \
  --output="$RFS_BASE/CLM_FATES/joblogs/eleven9_plots_%j.out" \
  --error="$RFS_BASE/CLM_FATES/joblogs/eleven9_plots_%j.err" \
  --wrap="export PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR='$MPLCONFIGDIR' XDG_CACHE_HOME='$XDG_CACHE_HOME' TMPDIR='$TMPDIR' TMP='$TMPDIR' TEMP='$TMPDIR'; source ~/.bashrc; '$HOME/miniconda3/envs/clm_fates_env/bin/python' -B '$REPO/examples/FLUXNET_MultiSite_11/scripts/19_plot_nine_site_spinup1000.py' --repo '$REPO' --output-root '$PLOTROOT'"
```

**Environment caveat:** the Python executable at `$HOME/miniconda3/envs/clm_fates_env/bin/python` is an example; verify `which python` after `conda activate clm_fates_env`, then substitute its exact absolute path. Do not run the job if the RFS mount is not accessible on compute nodes. RFS access and permitted workload must be confirmed with your local HPC support.

For an **interactive** test, run one site directly rather than submitting a job, with the same environment variables:

```bash
python -B "$REPO/examples/FLUXNET_MultiSite_11/scripts/19_plot_nine_site_spinup1000.py" --repo "$REPO" --output-root "$PLOTROOT" --sites BE-Bra
```

Each successful site generates two carbon-pool figures (1000 years and last 250 years) and one GPP/NEE monthly EC comparison, plus convergence/skill CSV and metadata JSON. Carbon/EC analysis uses last **complete** and correctly phase-aligned meteorological forcing cycle; `NEE_{model}=-FATES_NEP`, EC NEE=`NEE_VUT_REF`. Scientific caveats must accompany plots.

## 4. Review status before publishing

```bash
cat "$PLOTROOT/nine_site_spinup1000_summary.csv"
find "$PLOTROOT" -type f -name '*.png' | sort
```

If EC source files are missing or multiple plausible HH CSVs exist, review original FLUXNET/ICOS permissions and select the correct HH file with `--obs-csv`. Do not invent EC plots or treat carbon-only results as full success.

## 5. Publish only selected derivative files

**Never upload** raw tower CSVs, detailed paired monthly flux tables, original NetCDF archives, restarts, input forcing, RFS credentials, or private logs.

Prefer a **separate clean checkout under HOME/WSL**, because the original checkout may contain unrelated Git conflicts. After copying reviewed derivative plots and limited summary CSVs into:

`examples/FLUXNET_MultiSite_11/figures/spinup1000_final/<SITE>/`

run inside that clean clone:

```bash
git add -f examples/FLUXNET_MultiSite_11/figures/spinup1000_final/*/*_01_carbon_pools_annual_mean.png
git add -f examples/FLUXNET_MultiSite_11/figures/spinup1000_final/*/*_02_carbon_pools_last250years.png
git add -f examples/FLUXNET_MultiSite_11/figures/spinup1000_final/*/*_GPP_NEE_monthly_overview.png
git add -f examples/FLUXNET_MultiSite_11/figures/spinup1000_final/*/*_convergence_metrics.csv
git add -f examples/FLUXNET_MultiSite_11/figures/spinup1000_final/*/*_monthly_metrics.csv
git add -f examples/FLUXNET_MultiSite_11/figures/spinup1000_final/nine_site_spinup1000_summary.csv
git diff --cached --stat
git diff --cached --name-only
git commit -m "Publish nine-site 1000-year convergence and EC comparison"
git push origin main
```

The per-example `.gitignore` currently ignores PNG/CSV/JSON; `git add -f` must be restricted to the reviewed derivative file types above. The copy from RFS to the clean clone is intentionally NOT automated before review, and the above `git add` commands only succeed after those files have actually been copied. Add a dated README section with links after verifying files and values.

**Verified output status:** repository scripts/docs only. The RFS mount, real IRIDIS archive access and image generation cannot be executed through the GitHub connector. No claim is made here that nine RFS plot sets or their scientific results have been generated.
