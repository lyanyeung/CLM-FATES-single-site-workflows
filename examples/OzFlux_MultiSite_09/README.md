# OzFlux MultiSite 09 — source-preserving IRIDIS6 transfer and L6 scientific intake

**Status (2026-11-01): PREPARED, NOT EXECUTED.** This cohort contains **9 station IDs and 10 original NetCDF files**. The Windows D: file locations were supplied by the experiment operator; neither local files nor remote files have been opened by this repository change. Scripts are published, but **no upload, byte verification, NetCDF assessment, forcing conversion, CIME case or Slurm run is yet claimed**.

This is a *new cohort* parallel to [JapanFlux MultiSite 11](../JapanFlux_MultiSite_11/), [AmeriFlux Batch03](../AmeriFlux_MultiSite_10_Batch03/) and the existing, previously run [OzFlux AU-How](../OzFlux_AU-How/). Keep scientific settings and decisions independent of those campaigns.

## 1. Exact source file manifest

Root on Windows: `D:\Fluxes_Tower_Experiment\Ozflux`; root in a typical Windows WSL shell: `/mnt/d/Fluxes_Tower_Experiment/Ozflux`.

The machine-readable `sites.tsv` stores the exact original basenames; do **not** rename filenames to match site codes or assume every NetCDF uses the same internal variable names.

| Site | Exact Windows source path |
| --- | --- |
| AU-ASM | `D:\Fluxes_Tower_Experiment\Ozflux\AU-ASM\AliceSpringsMulga1_20100903T0000_to_20230308T0900_L6.nc` |
| AU-ASM | `D:\Fluxes_Tower_Experiment\Ozflux\AU-ASM\AliceSpringsMulga2_20240821T0700_to_20260423T0000_L6.nc` |
| AU-Cow | `D:\Fluxes_Tower_Experiment\Ozflux\AU-Cow\CowBay_20090101T0900_to_20260423T0000_L6.nc` |
| AU-Cpr | `D:\Fluxes_Tower_Experiment\Ozflux\AU-Cpr\Calperum_L6.nc` |
| AU-DaS | `D:\Fluxes_Tower_Experiment\Ozflux\AU-DaS\DalyUncleared_20080101T0000_to_20260423T0000_L6.nc` |
| AU-Dry | `D:\Fluxes_Tower_Experiment\Ozflux\AU-Dry\DryRiver_L6.nc` |
| AU-Gin | `D:\Fluxes_Tower_Experiment\Ozflux\AU-Gin\Gingin_L6.nc` |
| AU-How | `D:\Fluxes_Tower_Experiment\Ozflux\AU-How\HowardSprings_L6.nc` |
| AU-Stp | `D:\Fluxes_Tower_Experiment\Ozflux\AU-Stp\SturtPlains_L6.nc` |
| AU-Tum | `D:\Fluxes_Tower_Experiment\Ozflux\AU-Tum\Tumbarumba1_L6.nc` |

**AU-ASM special case:** Mulga1 and Mulga2 are **two separate files and apparent acquisition periods**. The filenames suggest a discontinuity between March 2023 and August 2024, but actual chronology, timezone, sampling conventions, station geometry, instrument changes and eligibility for any later harmonisation must be verified from the original metadata. **Never concatenate or fill this gap automatically.**

File timestamps are release-label hints, not scientifically verified continuous observations. Other sites may contain multiple time periods, gaps or different measurement/derived-variable schemas despite the common L6 extension.

## 2. Stage00: batch transfer from local Windows PC (run in WSL/Ubuntu)

Run the following in **your own PC's Ubuntu/WSL**, not an IRIDIS login terminal. Requires `git`, `ssh`, `rsync`, `sha256sum`, `awk`, `mktemp`, and `head`.

```bash
# Keep the interactive WSL shell open if a preflight command reports an error.
ls -ld /mnt/d/Fluxes_Tower_Experiment/Ozflux
command -v git ssh rsync sha256sum

if [[ -d "$HOME/CLM-FATES-OzFlux-upload/.git" ]]; then
  git -C "$HOME/CLM-FATES-OzFlux-upload" pull --ff-only
else
  git clone --depth 1 https://github.com/lyanyeung/CLM-FATES-single-site-workflows.git \
    "$HOME/CLM-FATES-OzFlux-upload"
fi

UPLOADER="$HOME/CLM-FATES-OzFlux-upload/examples/OzFlux_MultiSite_09/scripts/stage00/00_upload_ozflux.sh"

# First: local complete 10-file preflight, checksum only; no network transfer.
bash "$UPLOADER" --preflight-only

# Then: transfer originals and independently verify IRIDIS-side SHA256.
bash "$UPLOADER" 2>&1 | tee "$HOME/ozflux_stage00_upload.log"
```

Default destination for every source file:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<AU-SITE>/forcing/raw/<ORIGINAL_FILENAME>.nc
```

For example, the two AU-ASM sources are stored *separately*:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/AU-ASM/forcing/raw/AliceSpringsMulga1_20100903T0000_to_20230308T0900_L6.nc
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/AU-ASM/forcing/raw/AliceSpringsMulga2_20240821T0700_to_20260423T0000_L6.nc
```

The script internally uses `set -euo pipefail`; do not enable `set -e` in your interactive WSL terminal. If a source preflight fails, the script stops but WSL stays open. The uploader checks **all 10 local files before connecting**, uses a single SSH authentication for the batch, never rewrites an existing destination, permits rerun after an interrupted transfer, and verifies every original file against the IRIDIS-side SHA256. If an existing file (particularly AU-How) has a different hash, transfer **stops** and preserves it for manual review. Source files are never deleted or moved.

Expected final line:

```text
UPLOAD VERIFIED: 10/10 NetCDF files across 9 OzFlux sites. No model jobs submitted.
```

This line confirms a byte-for-byte transfer, **not scientific validation**. Do not claim completion before seeing it in the actual WSL log.

## 3. Stage01: read-only NetCDF inventory on IRIDIS6

**Critical Python import safeguard:** Never download this inspector as `inspect.py`, because `inspect` is a Python standard-library module imported by `netCDF4`. A previous Stage01 command did that and caused `AttributeError: module 'inspect' has no attribute 'cleandoc'` for every site *before any NetCDF data were inspected*. This was a script-name error, not source corruption. Existing generated `$HOME/ozflux_stage01/inspect.py` must be moved aside before rerunning. The source-controlled script is named `01_inspect_ozflux_nc.py`.

After Stage00 has independently verified all ten file SHA256 hashes, log into **IRIDIS6**. Run the commands below **without enabling `set -e` in the interactive shell**:

```bash
conda activate clm_fates_env
DIR="$HOME/ozflux_stage01"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/OzFlux_MultiSite_09"
mkdir -p "$DIR/old"
# Move only the previously misnamed inspector; leave all source NetCDF untouched.
if [[ -f "$DIR/inspect.py" ]]; then
  mv -n "$DIR/inspect.py" "$DIR/old/inspect.py"
fi
curl -fLsS "$BASE/sites.tsv" -o "$DIR/sites.tsv" || exit 1
curl -fLsS "$BASE/scripts/stage01/01_inspect_ozflux_nc.py" -o "$DIR/ozflux_nc_metadata.py" || exit 1
python3 -c 'import inspect, netCDF4; print("inspect from", inspect.__file__); print("netCDF4", netCDF4.__version__)'
python3 -B "$DIR/ozflux_nc_metadata.py" --manifest "$DIR/sites.tsv" > "$DIR/inventory.json"
python3 - "$DIR/inventory.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
for s in x["files"]:
    print(s["site"], s["filename"], s["status"],
          "vars="+str(s.get("variable_count","?")),
          "time="+",".join(v["name"] for v in s.get("time_coordinates",[])))
    if "error" in s: print("  ERROR:", s["error"])
print("INVENTORIED", x["inventoried_count"], "/10")
PY
```

If `$DIR/old/inspect.py` already exists, manually choose an alternative name before moving the new one; do not overwrite previous logs or scripts. The Python `inspect.__file__` shown in the import test must point to the system/conda Python standard library, **not** to `$DIR/inspect.py`. Ignore a stale `__pycache__` subdirectory after the source has been moved.

This inspector reads original NetCDF headers, attributes and up to three scalar time samples per time coordinate. It does **not** modify site data, convert timezone, concatenate periods, produce forcing or submit jobs.

The published [OzFlux AU-How](../OzFlux_AU-How/) case is an **existing Howard Springs example**, not a generic permission to apply its 2003–2025, 23 m, zero-gap, 30-minute, NOLEAP, or DATM logic to every new site. In particular, its `05_make_datm.py` removes earlier matching output files and must **not** be executed on unreviewed source locations. No independently validated AU-Tum example currently exists under this repository's `examples/` tree.

Stage01 success requires `INVENTORIED 10 /10`. A successful metadata read alone does not approve meteorological physics or any forcing gap-filling decision.

## 4. Subsequent scientific stages (not implemented/authorised yet)

1. **Stage02 — source provenance/time QC:** verify actual temporal coverage, time coordinate convention (UTC vs local, interval start/end/centre), timestep, gaps/duplicates, fill values, QA/QC flags, lat/lon, instrument/source changes and especially the two AU-ASM periods. Keep each source immutable.
2. **Stage03 — meteorological physics and forcing candidate:** evaluate OzFlux variable mapping per station, compare native data and observation QC, assess radiation/humidity/precipitation and site-specific height. Existing AU-How uses `Ta→TBOT`, `SH→QBOT`, `ps→PSRF`, `Fsd→FSDS`, `Fld→FLDS`, `Ws→WIND`, `Precip→PRECTmms`; **do not assume units, gap-filling status or mapping are identical for these other L6 products**.
3. **Stage04 — site vegetation/soil/surface:** scientific approval of each site's PFT fractions, shrub/bare ground, soil texture and correct surface/mesh. No copy of an unrelated site's vegetation or forcing height.
4. **Stage05 — independent DATM and NOLEAP audit; model preflight:** validate chronology, water and radiation physics and all required forcing fields. Only after sign-off, prepare site-specific CIME/FATES cases and consider the established staged spinup (AD and Normal) approach. **Stage00 and Stage01 submit no Slurm jobs.**

## 5. Provenance and non-destructive rules

- File names, local paths and cohort selection: experiment operator, 2026-11-01.
- Layout and guarded batch-transfer workflow: [JapanFlux MultiSite 11](../JapanFlux_MultiSite_11/) and earlier AmeriFlux examples.
- Existing AU-How forward case and its nontrivial time convention: [README](../OzFlux_AU-How/README.md) and [KNOWN_ISSUES](../OzFlux_AU-How/KNOWN_ISSUES.md).
- Store only documentation, manifest and scripts on GitHub; **do not commit raw EC NetCDF files, generated DATM outputs or Slurm results**.
- Neither source files nor existing model experiments are modified by this new cohort's checked-in scripts.
