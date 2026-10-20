# Scratch figure/analysis archival → Research Filestore (6/8/11/13 batches)

This reusable tool follows the **login-node RFS pattern** successfully used by `FLUXNET_MultiSite_11/scripts/21_transfer_nine_site_plots_to_rfs.sh`, but adds independent receipts and a guarded **picture-only** cleanup.

[Implementation](../scripts/research_filestore/archive_scratch_analysis.py).

## Safety and scope

- Targets old **Scratch** figures (`png/jpg/jpeg/svg/pdf/webp/tif/tiff`) from `/iridisfs/scratch/ly3n24/CLM_FATES/experiments`, per-site `forcing/validation/analysis` areas, and non-live model-output `analysis/validation/plots/results/diagnostics` folders. Nearby analysis CSV/JSON/TSV/TXT are copied for reproducibility, but **never removed**.
- Conservative batch classification; skips ambiguous provenance, files changed in the past 24 hours, `run`, `hist`, `rest`, `archive`, case folders, raw forcing and model NetCDFs. **Does not promise to find every historical figure**: audit any other custom locations separately rather than expanding deletion scope blindly.
- Copying requires live `/research/xclimatetbm/ly3n24` to be an **NFS mount**, available on IRIDIS6 login nodes. Previous 11-site Slurm compute job could not access `/research`: do not submit RFS copy/prune as batch work.
- Destination: `/research/xclimatetbm/ly3n24/CLM_FATES/<BATCH>/scratch_analysis_archive/<original-relative-path>`; verified receipts at `.../_receipts/<UTC>_<id>.json`.
- Refuses to overwrite a different existing destination; files must match SHA256. No `rsync --delete`; no changes to Slurm jobs, case configs, DATM, restarts or archived model history. GitHub contains **source code and descriptions only**, not copied private analysis/results.
- The 11-site `spinup1000_final` at `/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_11/spinup1000_final/` is **already archived by its own script**. This new tool does not replace or delete that dataset.
- **Important**: do not remove still-referenced Scratch figures from downstream notebooks or scripts without updating their paths; archive path preserves original relative structure for future inspection.

## Execute on an IRIDIS6 login node

From a checkout of `CLM-FATES-single-site-workflows`:

```bash
cd ~/CLM-FATES-single-site-workflows
git pull --ff-only
SCRIPT=scripts/research_filestore/archive_scratch_analysis.py
python3 -B "$SCRIPT" audit --batch all
python3 -B "$SCRIPT" copy --batch all
```

The `copy` step prints a **different explicit receipt path for each batch** with files. For every receipt, independently check:

```bash
python3 -B "$SCRIPT" verify --receipt "/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_6/scratch_analysis_archive/_receipts/REPLACE_WITH_REAL_FILENAME.json"
```

Then—and **only** after inspecting the receipt and full copies—delete **only the verified original Scratch pictures** (never the nearby analysis tables or model files):

```bash
python3 -B "$SCRIPT" prune \
  --receipt "/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_6/scratch_analysis_archive/_receipts/REPLACE_WITH_REAL_FILENAME.json" \
  --confirm DELETE_VERIFIED_SCRATCH_IMAGES
myfiles
```

Repeat with the real receipt path for each batch. `audit` has no writes. `copy` creates only RFS files. `verify` is read-only. `prune` modifies only individually verified Scratch images.

Optional `--min-age-hours 72` further excludes recently modified results. This is **not** the same as model convergence assessment, and there is no guarantee that every old image is safe to remove from a scientific workflow. First check what audit finds.

## Other pre-existing results

- The older 6-, 8- and 11-site figures have already been published selectively in GitHub, and/or stored in Home or RFS. This tool **does not delete GitHub figures** or Home results. Its scope is Scratch only.
- To archive other previously produced Home figures, use the previously verified 11-site Home→RFS workflow or a separate Home-targeted copy. Do not assume all plots live in Scratch.
- Live case `lnd/hist/*.nc` and restarts need their own checkpoint-aware RFS archival procedure; never include them in a figure cleanup.
