# AmeriFlux MultiSite 10 — Batch 02

Stages 00–03 upload, extract, inspect metadata and prepare reference surfaces for the ten exact releases in [sites.tsv](sites.tsv):
US-BZS, US-CMW, US-EML, US-GLE, US-Ha1, US-Ho1, US-Ho2, US-Ho3,
US-ICh and US-ICt. First-batch scripts and manifests are unchanged.

The release names and year labels are supplied by the operator. US-BZS and
US-Ho1 retain their original `FLUXNET_FULLSET` names and version suffixes.
These labels do not establish actual data coverage or internal CSV structure.

## Upload from the local WSL terminal

The source is `D:\Fluxes_Tower_Experiment\Ameriflux`, accessible from WSL as
`/mnt/d/Fluxes_Tower_Experiment/Ameriflux`. Each package must be a directly
contained `<package>.zip` (ZIP extension matching is case insensitive), or
a directly contained `<package>/` folder. ZIP takes priority if both exist.
No repacking is performed. Required commands include `bash`, `ssh`, `rsync`,
`sha256sum`, `find`, `awk` and `mktemp`.

Download directly from GitHub; no `git pull` is needed. Run in **LOCAL WSL**,
not in an IRIDIS SSH terminal:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ameriflux-batch02-transfer'
  BASE="$HOME/ameriflux_batch02_transfer"
  mkdir -p "$BASE/scripts/stage00"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch02/sites.tsv" -o "$BASE/sites.tsv"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage00/00_upload_ameriflux_batch02.sh" -o "$BASE/scripts/stage00/00_upload_ameriflux_batch02.sh"
  bash -n "$BASE/scripts/stage00/00_upload_ameriflux_batch02.sh"
  LOCAL_ROOT='/mnt/d/Fluxes_Tower_Experiment/Ameriflux' \
    bash "$BASE/scripts/stage00/00_upload_ameriflux_batch02.sh" \
    2>&1 | tee "$BASE/upload_$(date +%Y%m%d_%H%M%S).log"
)
```

If the mounted directory actually uses the spelling `AmeriFlux`, change only
`LOCAL_ROOT` accordingly. Do not enter your password into a script or chat.

The script preflights all ten local sources before connecting. It opens one
SSH master to `ly3n24@iridis6.soton.ac.uk`; enter a password once at that
connection if requested. Host authenticity confirmation or an additional
factor may still be required by the SSH service. All subsequent commands
reuse the private socket in `/tmp`, use batch mode, and cannot fall back to
a new network connection. Keep the terminal and network connection open.
The master is closed automatically when the script exits.

Destination (same layout as Batch 01):

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/packages/<PACKAGE>.zip
```

For a source folder, the destination ends in `packages/<PACKAGE>/` instead.
`REMOTE` and `REMOTE_ROOT` may be overridden if needed.

Existing files are preserved via `rsync --ignore-existing`; interrupted
transfers retain partial data for a later retry. Every ZIP is SHA256 checked;
source folders receive a recursive checksum dry-run that also detects extra
remote files. A same-named conflicting destination causes failure rather than
replacement. The script never deletes source or destination package files.
An interrupted run stops without asking for passwords repeatedly; rerun the
same command to reconnect once and resume. Previously verified files are
checked again. A checksum conflict needs inspection before another retry.

Completion is reported only by:

```text
UPLOAD VERIFIED: 10/10 (AmeriFlux Batch 02). Originals retained. No extraction or model jobs started.
```

Operator-provided output confirms `UPLOAD VERIFIED: 10/10` for Stage 00.
This is evidence of transfer/checksum success, not extraction or source QC.
No simulation period, forcing cycle or spin-up duration has been chosen.

## Stage 01: recursive extraction on IRIDIS

Run the following in an **IRIDIS terminal**, after Stage 00. Download directly
from GitHub without `git pull`:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ameriflux-batch02-transfer'
  REL='examples/AmeriFlux_MultiSite_10_Batch02'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage01"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage01/01_extract_ameriflux_batch02.py" -o "$BASE/scripts/stage01/01_extract_ameriflux_batch02.py"
  python3 -m py_compile "$BASE/scripts/stage01/01_extract_ameriflux_batch02.py"
  python3 "$BASE/scripts/stage01/01_extract_ameriflux_batch02.py" \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_stage01_$(date +%Y%m%d_%H%M%S).log"
)
```

Outputs:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/raw/<PACKAGE>/*.csv
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage01_extraction_<UTC>_<ID>.json
```

The script preflights all selected source packages, recursively reads nested
ZIPs (up to eight levels), and extracts CSVs to the exact release directory.
CSV basenames are flattened; `toc.csv` and `!toc.csv` are excluded. Source
ZIPs, folders and non-CSV members remain intact in `forcing/packages`.
CSV size/CRC32 is checked before installation; identical existing CSVs are
skipped and different existing CSVs are rejected. Conflicting basenames in
nested folders are also rejected. Installation uses a hard link from a
temporary file in the same directory, so it cannot replace a concurrent
destination. An interrupted process may leave a `.partial`; inspect that
file before retrying rather than deleting existing raw files indiscriminately.

Inventory recognizes the two formats separately:

- Eight v1.3 releases: require site-specific BIF and a FLUXMET_HH or FLUXMET_HR
  CSV; report HH and HR variants of ERA5 and FLUXES separately. Missing a
  separate ERA5 HH/HR product is a note. US-Ha1 supplies FLUXMET_HR and ERA5_HR
  according to the operator's extraction log; the earlier HH-only condition
  incorrectly failed its structural inventory after successful extraction.
  HR is accepted and explicitly recorded without resampling or renaming.
- US-BZS and US-Ho1 FULLSET releases: require a site-specific FULLSET_HH or
  FULLSET_HR CSV. Missing BIF is a metadata follow-up, not an extraction
  failure. Hourly data and missing separate ERA5 products are reported.
- Meteorological headers must contain TIMESTAMP_START/TIMESTAMP_END and one
  structurally valid first data row. Columns and the first timestamp pair
  and native product resolution labels are written to the inventory; this
  does not scan or validate the time series. Later forcing must account for
  the hourly source rather than assuming all ten sites are half-hourly.

The summary reports `BATCH02 SUMMARY: 10/10 PASS (extraction/structure only)`
only when all ten complete. Each extraction run writes its own JSON report,
including source ZIP SHA256 values and per-site failures. Successful sites
remain intact if another site fails. No meteorological CSV values, existing
forcing/DATM, surfaces, CIME cases or Slurm jobs are modified. In particular,
US-Ha1 uses only the exact release's raw output directory.

For a read-only inventory after extraction:

```bash
python3 "$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage01/01_extract_ameriflux_batch02.py" --audit-only
```

`--sites US-BZS US-Ho1`, `--sites-root`, `--incoming-dir` and `--reports-dir`
are available. Audit-only writes no report or raw output. Next inspect BIF
or FULLSET metadata, actual coverage and meteorological QC before preparing
surfaces, forcing or model experiments.

## Stage 02: read-only metadata and coordinate preflight

Operator output now confirms `BATCH02 SUMMARY: 10/10 PASS` after the hourly
inventory fix. Next inspect metadata before preparing CTSM point surfaces.

[Stage 02](scripts/stage02/02_check_batch02_metadata.py) reads the exact
release directories. Eight v1.3 sites use their release BIF. The two FULLSET
sites without BIF use [metadata_fallbacks.tsv](metadata_fallbacks.tsv):

| Site | Latitude | Longitude | IGBP | Source |
| --- | --- | --- | --- | --- |
| US-BZS | 64.6963 | -148.3235 | ENF | [AmeriFlux site page](https://ameriflux.lbl.gov/sites/siteinfo/US-BZS) |
| US-Ho1 | 45.2040 | -68.7402 | ENF | [AmeriFlux site page](https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1) |

These are official site-page search extracts retrieved on 21 October 2026;
direct page opens were blocked by HTTP 403. They are current site metadata,
not embedded release-specific BIF. Provenance, exact package names and this
limitation are preserved in the fallback table. Do not borrow Ho2/Ho3
coordinates for Ho1. BZS is described as black spruce on a permafrost peat
plateau; its ENF label alone does not validate soil or footprint representation.

The script prints unique valid coordinates, original IGBP labels, coordinate
provenance, available height metadata, and the first HH/HR timestamp interval.
It checks 30 minutes for HH and 60 minutes for HR, retaining US-Ha1's hourly
identity. It does not inspect full time-series completeness or choose ZBOT,
PFT fractions, spin-up periods, or replacement meteorology. Non-forest and
study-inclusion classes are flagged for review without excluding sites.
Missing height information is reported for follow-up.

Run on IRIDIS, with direct GitHub downloads and no `git pull`:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ameriflux-batch02-transfer'
  REL='examples/AmeriFlux_MultiSite_10_Batch02'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage02"
  for FILE in sites.tsv metadata_fallbacks.tsv scripts/stage02/02_check_batch02_metadata.py; do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  python3 -m py_compile "$BASE/scripts/stage02/02_check_batch02_metadata.py"
  python3 "$BASE/scripts/stage02/02_check_batch02_metadata.py" \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_stage02_$(date +%Y%m%d_%H%M%S).log"
)
```

Expected summary, if real input checks pass:
`STAGE02 SUMMARY: 10/10 coordinate + first-interval checks PASS; failures: none`.
The script writes no files; the shell saves its output log. No source data,
forcing, surfaces, cases or Slurm jobs are changed. Inspect the printed table
and review notes before the next surface-generation stage. A coordinate PASS
is not approval of vegetation representation or meteorological forcing.

Stage 02 passed Python compilation and six synthetic-input checks: eight BIF
plus two fallback sites with native HH/HR intervals; ambiguous coordinate
rejection; missing-value coordinate rejection; no silent fallback for a
missing v1.3 BIF; rejection of HR/first-interval mismatch; and study-inclusion
flagging without automatic exclusion. Input file hashes and modification
times stayed unchanged in every check. Live IRIDIS Stage 02 has not been run
by the GitHub change.

## Stage 03: isolated CTSM reference point surfaces (year 2000)

Operator-provided Stage 02 output confirms 10/10 coordinate and first-interval
checks. IGBP labels are five ENF (US-BZS, US-GLE, US-Ho1/2/3), two DBF
(US-CMW, US-Ha1), and three OSH (US-EML, US-ICh, US-ICt). US-Ha1 is hourly.
These observations do not establish FATES PFT fractions or forcing quality.

[Stage 03](scripts/stage03/03_make_batch02_surfaces.py) imports the Stage 02
metadata reader, rechecks all ten sources and preserves the explicit FULLSET
coordinate provenance. It uses the same reference settings as Batch 01:
CTSM `subset_data point --surf-year 2000 --create-surface --create-user-mods`,
`--lon-type 180`, and **no `--dompft`**. The template's surfdata directory is
changed from ctsm5.4.0 to ctsm5.3.0, the 16-PFT file is
`surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc`, and the mesh is
`fv0.9x1.25_141008_ESMFmesh.nc`, as in the preceding experiments.

Batch-specific output is isolated from the existing single-site US-Ha1
experiment and all ordinary `subset_data/` directories:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/subset_data_batch02_surf2000/
    <SITE>_data.cfg
    surfdata*.nc
    user_mods/
    batch02_surface_receipt.json
```

The default `--check` is read-only. `--run` preflights all ten sites before
creating any output. Existing batch outputs are skipped only if their request
(including coordinates, package, year, config and subset tool hash) and file
checksums agree with the completion receipt. Missing or changed receipts,
incomplete directories and changed outputs stop the run without overwriting.
A failed CTSM call may leave a partial directory; inspect it before retrying.
No raw data, old surface/configuration, forcing/DATM, cases or Slurm jobs are
modified. `CLM_FATES_ROOT` or `--clm-root` can override the installation root.

Run on IRIDIS in the existing `clm_fates_env`, directly downloading from GitHub:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ameriflux-batch02-transfer'
  REL='examples/AmeriFlux_MultiSite_10_Batch02'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage02" "$BASE/scripts/stage03"
  for FILE in sites.tsv metadata_fallbacks.tsv scripts/stage02/02_check_batch02_metadata.py scripts/stage03/03_make_batch02_surfaces.py; do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  SCRIPT="$BASE/scripts/stage03/03_make_batch02_surfaces.py"
  python3 -B "$SCRIPT" --check
  python3 -B "$SCRIPT" --run \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_stage03_$(date +%Y%m%d_%H%M%S).log"
)
```

Successful first-run summary:
`STAGE03 SUMMARY: created=10 skipped_verified=0 total=10/10`.
The next stage audits actual NetCDF landunit and natural-PFT fractions,
especially at the three OSH sites, and then audits full source meteorology.
The year-2000 grid sample is not a validated tower footprint or an automatic
mapping of OSH to FATES shrub parameters. No spin-up is launched here.

Validation: Python compilation plus five lifecycle checks with a mock CTSM
executable: read-only preflight, batch-wide rejection of a final site's
partial output before any new writes, ten isolated outputs, checksum-verified
rerun without writes, and preservation/rejection of a changed surface.
US-Ha1's original surface fixture stayed unchanged and its hourly provenance
remained in the receipt. These checks test orchestration, not real CTSM
execution or scientific NetCDF correctness; live generation is performed by
the operator on IRIDIS.

## Validation boundary

Validation passed: Bash syntax and six isolated integration checks with mock
SSH control and real local rsync/checksums: mixed ZIP/directory transfer,
identical rerun, missing source, conflicting ZIP, extra destination folder
file, and master disconnection. The mock checks one master launch and the
batch-only options on subsequent operations. Live SSH authentication and
multiplexing have not been tested here. No check authenticates to IRIDIS,
accesses the operator's D drive, or establishes a real upload.

Stage 01 passed Python compilation and seven synthetic-data checks: missing
package preflight with no raw writes; nested extraction of ten releases,
including two FULLSET releases without BIF; identical rerun; audit-only with
no file writes; conflicting existing CSV preservation; corrupt ZIP failure;
and wrong-site meteorology rejection. Source ZIP hashes remained unchanged,
TOC files were skipped and traversal-shaped names stayed inside the raw
directory. These tests are not live extraction or scientific validation of
the operator's IRIDIS packages. Standard-library-only code supports Python 3.9.

The hourly-source correction was verified with US-Ha1-like FLUXMET_HR and
ERA5_HR fixtures alongside the other nine HH/FULLSET releases, a repeat
read-only inventory with no raw writes, and rejection of an hourly release
missing BIF. The extraction code and original source data are unchanged.
After downloading the corrected script, run `--audit-only` to recheck all
ten already-extracted sites; no upload or extraction is required.
