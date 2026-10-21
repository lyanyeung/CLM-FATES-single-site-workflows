# AmeriFlux MultiSite 10 — Batch 02

Stages 00 and 01 upload and extract the ten exact releases in [sites.tsv](sites.tsv):
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
