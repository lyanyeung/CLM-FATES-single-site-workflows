# AmeriFlux MultiSite 10 — Batch 02

Stages 00–10 prepare reference surfaces, build native-resolution QC candidates and perform Post-v5 gates for the ten exact releases in [sites.tsv](sites.tsv):
US-BZS, US-CMW, US-EML, US-GLE, US-Ha1, US-Ho1, US-Ho2, US-Ho3,
US-ICh and US-ICt. First-batch scripts and manifests are unchanged.

## Current operational checkpoint — 22 October 2026

This is the separate Batch02 case under `main/examples/`. Stages00–10 and
the exact manifests are published here. Transfer, extraction, metadata and
isolated reference-surface generation have completed for all ten releases;
source and surface audits remain scientific evidence, not model approval.

The latest operator Stage07 run produced **five independently reconciled
numeric candidates and five failed sites**, with all inputs unchanged.

| Site | Native step | Stage07 result | Changed variable records | QC0 changes | Unresolved humidity records |
| --- | --- | --- | ---: | ---: | ---: |
| US-BZS | 30 min | Numeric candidate; review required | 87 | 1 | 0 |
| US-CMW | 30 min | Numeric candidate; review required | 44 | 2 | 0 |
| US-EML | 30 min | Blocked | — | — | 1,327 |
| US-GLE | 30 min | Blocked | — | — | 295 |
| US-Ha1 | 60 min | Numeric candidate; review required | 30 | 2 | 0 |
| US-Ho1 | 30 min | Blocked | — | — | 937 |
| US-Ho2 | 30 min | Numeric candidate; review required | 757 | 19 | 0 |
| US-Ho3 | 30 min | Numeric candidate; review required | 45 | 0 | 0 |
| US-ICh | 30 min | Blocked | — | — | 169 |
| US-ICt | 30 min | Blocked | — | — | 2,176 |

The five blocked sites total **4,904 unresolved humidity pairs**. Their
site-downscaled ERA5 support did not satisfy the inherited QC-v5 final
humidity rule. Their raw products contain `RH`, but its usability at these
exact rows has not yet been established. The [Stage08 same-release-RH
sensitivity](#stage-08-same-release-rh-sensitivity-for-stage07-blockers)
is published with synthetic validation; live IRIDIS execution is pending.
After Stage08 completes a ten-site selection, follow the
[Post-v5 gates and pipeline](#stages-0910-post-v5-gates-and-pipeline)
below. Candidate construction alone does not complete Post-v5.

Preserve the existing Stage07 trial, its five successful candidates and its
incomplete marker:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/qcv5_native_trial_20261022T010124Z_dfae01c2
```

No Batch02 DATM, CIME case or model job has been created. ZBOT and surface/PFT
representation still need site-specific review. Download links below use
the canonical `main` branch; previously supplied commit-pinned commands and
the development branch remain valid historical references.

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
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  "$PYTHON_BIN" -c 'import sys, numpy; print("Python:", sys.executable, "NumPy:", numpy.__version__)'
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ameriflux-batch02-transfer'
  REL='examples/AmeriFlux_MultiSite_10_Batch02'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage02" "$BASE/scripts/stage03"
  for FILE in sites.tsv metadata_fallbacks.tsv scripts/stage02/02_check_batch02_metadata.py scripts/stage03/03_make_batch02_surfaces.py; do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  SCRIPT="$BASE/scripts/stage03/03_make_batch02_surfaces.py"
  "$PYTHON_BIN" -B "$SCRIPT" --check
  "$PYTHON_BIN" -B "$SCRIPT" --run \
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

### Interpreter preflight and config-only recovery

The first live US-BZS attempt failed during CTSM import with
`ModuleNotFoundError: No module named 'numpy'`. The driver had invoked
`subset_data` as an executable, allowing its shebang to choose Python.
The shell's `(clm_fates_env)` prompt by itself did not establish which
interpreter that child used. The log alone also cannot rule out a missing
dependency in the intended environment.

The corrected driver explicitly invokes `[sys.executable, '-B', subset_data, ...]`
and first runs `point --help` with the same interpreter to test CTSM imports,
before creating or moving output directories. It prints the interpreter
and Conda environment. Use `$CONDA_PREFIX/bin/python` after activating
`clm_fates_env`; no automatic package installation or environment changes
are performed by the Python driver.

For the failed attempt above, after downloading the corrected script:

```bash
PYTHON_BIN="$CONDA_PREFIX/bin/python"
SCRIPT="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage03/03_make_batch02_surfaces.py"
"$PYTHON_BIN" -B "$SCRIPT" --check --recover-config-only
"$PYTHON_BIN" -B "$SCRIPT" --run --recover-config-only
```

Recovery is permitted only when an incomplete output directory contains
exactly the unchanged, expected `<SITE>_data.cfg`, with no other files or
directories. `--check` only describes that plan. `--run` rechecks and renames
the old directory to `subset_data_batch02_surf2000.incomplete_<UTC>_<ID>`
before creating a fresh output directory. It does not delete the old attempt
or adopt unverified NetCDF files. Any additional entry or config difference
blocks recovery for inspection. No other surface or source directory is moved.

Regression checks additionally exercised an unusable tool shebang, dependency
failure before any output creation/move, read-only recovery checks, exact
config-only preservation and retry, and rejection of an additional output file.

## Stage 04a: audit actual surface landunits and CLM natural PFTs

Operator output confirms Stage 03 completed all ten sites:
`created=10 skipped_verified=0 total=10/10`. Next run
[Stage 04a](scripts/stage04/04a_audit_batch02_surfaces.py) against each exact
`subset_data_batch02_surf2000/` directory. It reads generated inputs and
writes only small, timestamped CSV/JSON reports under:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage04a_surface_<UTC>_<ID>/
    surface_summary.csv
    natural_pft_detail.csv
    surface_summary.json
```

Checks include Stage 03 completion receipts and generated file inventories /
SHA256 values; one surface/config/user_mods set per site; landunit percentage
ranges and sums; single-point natural-PFT dimensions, ranges and sums; and
surface coordinates. Longitude comparisons account for 0–360 versus
-180–180 representations. A point/grid coordinate difference over 0.05 degrees
is an exploratory review note, not a site-coordinate replacement.

Reports explicitly distinguish `pct_of_natural` from `pct_of_grid`, with
`pct_of_grid = PCT_NATVEG * pct_of_natural / 100`. Tree/shrub/grass/bare totals
use the standard CLM natural PFT indices 0–14, not FATES parameter indices.
A 16th slot is labelled `extra_index_needs_review`, kept in the inventory and
excluded from assumed vegetation groups. A nonstandard explicit natpft
coordinate is rejected before assigning group names.

US-EML, US-ICh and US-ICt are always flagged for OSH/tundra representation
review. The script does not impose a majority-shrub requirement, change
PFTs, select FATES shrub parameters, or automatically exclude sites. Forest
subtype fractions below 50%, crop over 20%, natural vegetation under 50%, and
nonzero lake/wetland fractions are exploratory review screens, not official
acceptance thresholds. Percentage sum tolerance is 0.5 percentage points;
this checks numerical structure and does not establish ecological validity.
The HH/HR identity from Stage 03 remains in the report, including hourly Ha1.

Run on IRIDIS with the explicit environment interpreter:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  "$PYTHON_BIN" -c 'import numpy; from netCDF4 import Dataset'
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ameriflux-batch02-transfer'
  REL='examples/AmeriFlux_MultiSite_10_Batch02'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage04"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage04/04a_audit_batch02_surfaces.py" -o "$BASE/scripts/stage04/04a_audit_batch02_surfaces.py"
  "$PYTHON_BIN" -B "$BASE/scripts/stage04/04a_audit_batch02_surfaces.py" \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_stage04a_$(date +%Y%m%d_%H%M%S).log"
)
```

The final summary is `STAGE04A SUMMARY: N/10 structural passes; M structural
failures`. Review every printed warning and the report tables even when all
ten pass. No raw meteorology, existing surfaces, forcing/DATM, model cases
or Slurm jobs are changed. Full meteorological coverage/quality auditing is
still the next source-data task; no repairs or model runs occur here.

Options: `--root`, `--report-root`, and `--stdout-only` (no reports written).
The preferred backend is netCDF4; SciPy can read classic NetCDF fixtures if
netCDF4 is unavailable, but cannot read NetCDF4/HDF5 surfaces.
Validation passed compilation and six real classic-NetCDF fixture checks:
ten valid HH/HR and 15/16-PFT cases with correctly weighted grid fractions;
stdout-only with no report writes; changed file checksum rejection; invalid
natural-PFT sum rejection; fill-value handling without invalid JSON; and
rejection of nonstandard PFT index labels. Input hashes and modification
times stayed unchanged. The netCDF4/HDF5 backend and actual IRIDIS surface
values have not been exercised by this GitHub change.

## Stage 04b: full-release primary / ERA5 source screening

Operator-provided Stage 04a output confirms 10/10 structural surface passes.
Surface representativeness remains under review: US-CMW has 3.622% trees
within natural vegetation versus its DBF tower label; US-GLE has 36.139%
versus ENF. The three OSH sites also retain their vegetation review flags.
No PFT adjustment has been selected or applied.

[Stage 04b](scripts/stage04/04b_audit_batch02_met_sources.py) audits all seven
meteorological variables in each site's labelled release years, keeping
primary FLUXMET/FULLSET and same-package ERA5 separate. Expected inputs are
20 products: two FULLSET_HH primaries, seven FLUXMET_HH, US-Ha1 FLUXMET_HR,
and matching ERA5_HH/HR companions. ERA5 file names may span extra years
(e.g. 1981–2025); outside-window rows are counted separately, and only the
pinned release window enters annual variable screening.

Primary columns prefer `<VAR>_F`, using `<VAR>_F_MDS` only when the former
column is absent. Companion columns require `<VAR>_ERA`. There is no row-wise
fallback, combination of columns, interpolation or reanalysis replacement.
Every selected field, available QC column, file header and source SHA256 is
recorded in `source_inventory.json`. Missing required columns or ambiguous
files produce explicit source failures. QC values are counted literally;
absent QC columns are marked unavailable rather than interpreted as QC0.

The audit scans chunked input and uses native 30-minute / 60-minute expected
timestamps. It checks start/end interval length, off-grid and duplicate times,
nonincreasing source order, missing records/values, variable ranges and
TA/VPD/PA humidity consistency. Unique finite-value coverage cannot exceed
100% when duplicate rows exist. The annual expected counts are 17,520 for HH
and 8,760 for HR, after removing February 29 for prospective NO_LEAP analysis.
Original leap-day rows remain unchanged; their counts are in the inventory.
No time-zone conversion is made. Original site-local clock conventions still
need verification before generating DATM.

Variable units assumed from the source product convention are TA degC, VPD
hPa, PA kPa, SW_IN/LW_IN W m-2, WS m s-1 and P mm per native interval. The
same broad range limits as Batch 01 are exploratory screens. Liquid-water
saturation is used for reconstructed RH, including cold sites; flagged RH is
not automatically corrected or switched to an ice convention. RH <1%, <5%
and <10% counts overlap and must not be added together. Humidity infeasibility,
range flags and low RH are combined into a unique-per-source-record ledger.
Companion ERA5 is not assumed independent validation of gap-filled FLUXMET.

Outputs are isolated under:

```text
CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage04b_met_<UTC>_<ID>/
    annual_source_coverage_and_QC.csv
    physical_anomaly_records.csv
    timestamp_issues.csv
    missing_episodes.csv
    source_inventory.json
    source_failures.csv
```

The anomaly ledger includes source filename, original CSV row number,
timestamps, canonical variable values, original selected QC values and flag
names. Missing episodes describe expected-grid timestamp/value availability,
including unusable native intervals; timestamp and variable episodes can
overlap. This is an inventory, not a decision to fill every gap. Source-level
failures mean their annual audit is incomplete; any partial ledger entries
for a failed source must not be treated as a completed source QC result.

Run on IRIDIS:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  "$PYTHON_BIN" -c 'import numpy, pandas'
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ameriflux-batch02-transfer'
  REL='examples/AmeriFlux_MultiSite_10_Batch02'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage04/04b_audit_batch02_met_sources.py"
  mkdir -p "$BASE/scripts/stage04"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage04/04b_audit_batch02_met_sources.py" -o "$SCRIPT"
  "$PYTHON_BIN" -B "$SCRIPT" --check
  "$PYTHON_BIN" -B "$SCRIPT" \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_stage04b_$(date +%Y%m%d_%H%M%S).log"
)
```

`--check` reads headers only and writes nothing. A full run writes reports,
leaving all source CSVs, surfaces, forcing, cases and Slurm jobs unchanged.
Options include `--root`, `--report-root`, `--sites` and `--chunksize`.
A successful audit prints `20/20 sources audited; 0 source failures`; REVIEW
counts and anomaly ledgers still need inspection. `NO_FLAGS_IN_THIS_SCREEN`
is not scientific forcing approval. No short-gap interpolation, ERA5 or
ERA5-Land repair, forcing/DATM generation or spin-up has occurred in Batch02.

Validation passed compilation and synthetic HH/HR/FULLSET/ERA5 CSV tests with
chunk boundaries: source header pinning, read-only preflight, 8,760 / 17,520
expected counts, leap-day exclusion without source changes, cross-chunk
duplicates, missing values/timestamps, wrong intervals, off-grid times,
humidity and radiation flags, unique coverage capped at 100%, source-row
provenance, missing-episode ledgers and explicit missing-column failure.
Source hashes and modification times remained unchanged. Real IRIDIS source
values and complete release coverage have not yet been examined by this
GitHub change.

## Stage 05: one-pass event, gap, QC and counterpart review

Operator-provided Stage 04b output confirms 20/20 sources, zero source
failures, 430 source-years, 285 REVIEW source-years and 96,773 flagged native
source records. The count comprises 59,314 primary-product records and
37,459 companion ERA5 records; overlapping timestamps between sources and
hourly versus half-hourly records must not be treated as independent events
or equal duration. US-Ho1 primary has 22,167 and US-CMW primary 21,326 flags.
The terminal log does not yet identify their dominant variables or episodes.

[Stage 05](scripts/stage05/05_review_batch02_source_events.py) reads the exact
Stage04b report and checksum-verifies all twenty raw source products. It
reconciles annual, inventory and event counts; retrieves both sources at the
union of flagged site-local timestamps; verifies each ledger row against its
original CSV row and recomputes the same screen. No UTC/time-zone conversion
or independent clock alignment is inferred. Companion ERA5 is still not
independent ground truth.

Four mutually exclusive review priorities are used:

- P0: any numerical range or humidity-feasibility screen.
- P1: RH below 1%, without P0.
- P2: RH 1–5%, without higher priorities.
- P3: RH 5–10%, without higher priorities.

These are prioritization bins, not official repair rules. Low positive RH
can represent dry conditions. P2/P3 are never classified as high-priority
replacement review merely because ERA5 is wetter. Original relevant-variable
QC codes (including QC0) are retained and tabulated without universal
provenance assumptions. Exact episode lengths use native minutes and
NO_LEAP consecutiveness; duplicate timestamps are not counted twice within
an episode of one priority. Timestamp/variable missing episodes remain a
separate table and can overlap.

Paired statuses explicitly hold missing/duplicate counterparts, missing
variables, incompatible native intervals, flagged companions, or ledger
mismatches. A high-priority event with a numerically clear counterpart is
still labelled REVIEW, never approved or applied. Identical TA/VPD/PA is
reported as a potential source relationship, not validation. Every paired
row includes both sources' values/QC, original row IDs and review status.

Run on IRIDIS with the completed report pinned explicitly:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ameriflux-batch02-transfer'
  REL='examples/AmeriFlux_MultiSite_10_Batch02'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage04" "$BASE/scripts/stage05"
  for FILE in scripts/stage04/04b_audit_batch02_met_sources.py scripts/stage05/05_review_batch02_source_events.py; do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  "$PYTHON_BIN" -B "$BASE/scripts/stage05/05_review_batch02_source_events.py" \
    --source-report '/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage04b_met_20261021T233344Z_ff3b9f20' \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_stage05_$(date +%Y%m%d_%H%M%S).log"
)
```

Outputs go to a new sibling `stage05_event_review_<UTC>_<ID>/` directory:
`priority_summary.csv`, `flag_type_summary.csv`, `event_episodes.csv`,
`source_quality_summary.csv`, `missing_episode_summary.csv`,
`relevant_QC_summary.csv`, `paired_event_review.csv`,
`paired_review_summary.csv` and `review_summary.json`.
The console prints mutually exclusive priorities, paired status counts and
source-row verification totals. Any `ledger_mismatches` causes a nonzero exit;
a source checksum change blocks use of that source and requires a fresh audit.
No source file or earlier report is changed. No interpolation, ERA5/ERA5-Land
repair, edited forcing, DATM or model run has occurred in this batch.

Tests passed compilation and a synthetic end-to-end 20-source HH/HR/FULLSET
review, including all four priorities, counterpart flag/missing-time/duplicate/
bad-interval holds, QC0 retention, identical TA/VPD/PA detection and clear
counterpart review without automatic approval. Ledger value mismatch and raw
checksum changes were rejected. Source and Stage04b report hashes and
modification times stayed unchanged. Actual IRIDIS counterpart values and
category totals have not been evaluated by this GitHub change.

## Stage 06: primary-product repair scope diagnosis

The operator's Stage05 log reports 96,773 verified source rows, zero ledger
mismatches and 16,494 episodes. Its 30,718 high-priority/clear-counterpart
records mix both source directions and are not a primary repair count.
Primary-only totals from that log are 25,804 P0, 933 P1, 4,951 P2 and 27,626
P3 records (59,314 total). US-Ho1 has 16,717 primary P0 records; US-CMW has
20,444 primary P3 records. The log does not yet identify the P0 predicates
or justify altering dry conditions.

[Stage 06](scripts/stage06/06_diagnose_batch02_repair_scope.py) consumes the
explicit Stage04b and Stage05 snapshots. It verifies Stage04b input hashes
against Stage05, reconciles paired row keys/values/QC with the original
event ledger, checks verified counts/status totals and recomputes both
source screens. It does not rescan live raw files; Stage05 supplied the
raw-file verification for these report snapshots.

The report separates primary events from ERA5 backup issues and exposes
each range predicate and humidity predicate: nonpositive vapor pressure,
RH above 101%, invalid denominator and specific-humidity predicates.
Humidity causes can overlap and must not be summed as unique events.
These reproduce the exploratory liquid-water screen and do not establish
which of TA/VPD/PA should be changed. Each cause includes original QC,
values, counterpart evidence and its original paired status.

Comparison of a single range-flagged variable checks the corresponding
ERA5 variable. An unrelated ERA5 flag does not itself disqualify that
variable. Humidity comparison checks TA/VPD/PA jointly and RH at least
10%; native-time and row-identity holds still apply. All clear-comparison
labels mean REVIEW, not approval to replace data. P1 remains extreme-dryness
review; P2/P3 remain retained pending low-RH review, without replacement.

Primary missing episodes, descriptive duration bands, native HH/HR priority
episodes and timestamp/coverage summaries accompany the cause tables.
Duration bands are not interpolation thresholds. Missing-timestamp and
per-variable gap hours overlap and must not be added as outage hours.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ameriflux-batch02-transfer'
  REL='examples/AmeriFlux_MultiSite_10_Batch02'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage06"
  FILE='scripts/stage06/06_diagnose_batch02_repair_scope.py'
  curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  "$PYTHON_BIN" -B "$BASE/$FILE" \
    --source-report '/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage04b_met_20261021T233344Z_ff3b9f20' \
    --review-report '/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage05_event_review_20261021T234428Z_d4fa7426' \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_stage06_$(date +%Y%m%d_%H%M%S).log"
)
```

Outputs go to a new `stage06_repair_scope_<UTC>_<ID>/` directory:
`direction_summary.csv`, `primary_issue_details.csv`,
`primary_cause_summary.csv`, `primary_event_review_queue.csv`,
`primary_review_summary.csv`, `primary_missing_episodes.csv`,
`primary_gap_summary.csv`, `primary_source_quality.csv`,
`primary_priority_episodes.csv` and `repair_scope_summary.json`.
The terminal prints primary priorities, detailed P0 causes, review queues,
coverage, longest gaps and ERA5 events with a numerically clear primary.
Inputs are preserved; no interpolation, source replacement, surface changes,
forcing/DATM generation or model jobs occur.

Local validation used 3,004 numerical cases against Stage05 plus a complete
synthetic Stage04b/05/06 pipeline with twenty HH/HR/FULLSET sources. It
checked primary/ERA5 direction, overlapping humidity causes, variable-specific
counterpart comparisons with unrelated flags, time/duplicate holds, QC0
retention, low-RH retention and missing-episode outputs. Reruns created
separate reports. Modified paired values and changed pinned Stage04b reports
were rejected before output creation; source/prior-report hashes and
modification times were preserved. Live IRIDIS Stage06 results remain pending.

## Stage 07: isolated native HH/HR QC-v5 candidates

The operator's Stage06 log reports 59,314 primary events, 37,459 ERA5 events,
zero primary missing episodes and zero primary timestamp/interval defects.
There are 19,723 primary P0 records with screen-clear counterpart support
and 6,081 without such support. Most primary P0 predicates are nonpositive
vapor pressure and negative specific humidity from the same TA/VPD/PA
combination; these causes overlap. The companion also contains anomalies,
so Stage06 support counts do not establish how many repairs will succeed.

[Stage 07](scripts/stage07/07_build_batch02_qcv5_candidates.py) now builds
actual, separate candidate CSVs. It uses a
[native-resolution adaptation](scripts/stage07/qcv5_native.py) of the
historical eight-site QC-v5 engine, the same method used by AmeriFlux Batch01.
The historical source is
`examples/FLUXNET_MultiSite_8/scripts/03_prepare_eight_site_forcing_v5.py`,
Git blob `f82e43c7d379bfaea370a349e7fe9f842bdc93b3`.
This is a documented adaptation, not a claim of an unchanged algorithm or
independent scientific validation. The original eight-site script is untouched.

Before output creation, the driver verifies the Stage06-linked report hashes,
Stage05 verification totals, manifest year/release/native-interval selection
and all twenty raw SHA256 values against Stage04b. It prints available
primary RH column names, but retains the historical TA/VPD humidity method;
it does not silently substitute another RH field. The standalone ERA5
product has explicit precedence over embedded ERA columns, matching the
sources actually compared in Stages04b–06.

The candidate method retains the historical hard screens, corroborated
isolated-spike and joint-artifact checks, tiny-negative handling, short-gap
then ERA fallback, and final VPD reconciliation from ERA RH while preserving
otherwise plausible tower TA. Zero initial missing values does not remove
the interpolation step: flagged values can become gaps during secondary QC.
Positive low RH alone does not trigger replacement. The historical
strong-near-zero-vapor rule still requires corroborating ERA moisture and
temperature evidence; every such reconstruction remains reviewable.

The native adaptation explicitly handles:

- Native 30-minute data at nine sites and 60-minute data at US-Ha1, without
  hourly upsampling or duplicated records.
- Complete internal gaps up to 120 minutes for TA/VPD/PA/LW/WS and 60 minutes
  for SW. A longer gap is never partly interpolated. Both usable boundaries
  must be in the same year. Precipitation is not interpolated.
- At least 180 minutes for the historical joint plateau rule.
- Accumulated precipitation divided by 1800 seconds for HH or 3600 for HR.

The inherited final humidity rule allows ERA RH in [-2,100.05]% and clips
the RH used for reconstruction to [1,100]%. This can affect mildly negative
or positive-below-1% ERA RH when final reconciliation is needed. Every floor
adjustment is logged and counted explicitly; it is a research candidate,
not an observed humidity value or a model-stability guarantee. Severe
unsupported humidity still raises a site failure. No new blanket low-RH
floor is applied to otherwise retained source records.

After each successful site build, a separate audit checks full NO_LEAP
chronology, native precipitation units, seven forcing fields, independent
QBOT reconstruction, raw-to-candidate changes and one-to-one replacement
events, original source values and original QC codes. It counts actual
modified QC0 variable records, interpolation/ERA/reconstruction origins,
manual-review records, RH-floor changes and residual RH bins. Only bin-edge
classification uses a 1e-9 percentage-point tolerance; candidate data and
physical validity checks are not changed by that reporting tolerance.
All input hashes are checked again after the run.

Run both source preflight and candidate generation in one command:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/ameriflux-batch02-transfer'
  REL='examples/AmeriFlux_MultiSite_10_Batch02'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage07"
  for FILE in sites.tsv scripts/stage07/qcv5_native.py scripts/stage07/07_build_batch02_qcv5_candidates.py; do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  "$PYTHON_BIN" -B "$BASE/scripts/stage07/07_build_batch02_qcv5_candidates.py" \
    --run \
    --scope-report '/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage06_repair_scope_20261021T235441Z_edc8e9e8' \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_stage07_$(date +%Y%m%d_%H%M%S).log"
)
```

`--check` performs checksum preflight without creating outputs. `--run`
creates a fresh `qcv5_native_trial_<UTC>_<ID>/` under this batch's experiment
directory. Per-site candidate CSVs are under `SITE/forcing/processed_v5/`;
replacement, manual-review, low-RH, status and independent-audit files are
under `SITE/forcing/qc_v5/`. The root contains `exact_input_manifest.json`,
`candidate_run_summary.csv`, `input_preservation_check.json` and
`output_sha256.json`.

Any site failure retains `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP`, preserves
the other site candidates and exits nonzero. An all-site numeric pass writes
`COMPLETE_NUMERIC_CANDIDATES_REVIEW_REQUIRED`. Neither marker approves QC0
changes, RH floors, ZBOT, surface/PFT representation or model use. Existing
outputs are never overwritten; inputs, surfaces, cases and jobs are untouched.
Native ERA5-Land is not downloaded. DATM and model runs are not created.

Validation used complete synthetic years for all twenty source products,
including leap-year source data and the actual Stage04b/05/06 report chain.
HH candidate forcing, replacement events, manual-review and low-RH CSVs
matched the historical engine. Ten native candidates passed independent
audits; tests covered standalone precedence over conflicting embedded ERA,
HR precipitation rates, duration-limited whole-gap interpolation, retained
positive low RH, recorded QC0/floor changes, and unchanged source/report
hashes and modification times. Altered source-QC provenance, changed raw
hashes and existing output destinations were rejected. Severe unsupported
companion humidity blocked candidate emission; a failed site retained the
incomplete marker and the other candidates. These are synthetic validation
results; the operator's live Stage07 outcome is recorded in the current
operational checkpoint above.

## Stage 08: same-release RH sensitivity for Stage07 blockers

[Stage08](scripts/stage08/08_resolve_blockers_with_raw_rh.py) preserves the
five successful Stage07 candidates by path and checksum and reruns only the
five documented humidity-blocked sites. Its separate
[sensitivity engine](scripts/stage08/qcv5_raw_rh.py) reproduces the Stage07
failure counts and example rows. All other QC-v5 rules remain as in Stage07.
The original Stage07 script/engine and its incomplete marker remain intact.

Only the reproduced unresolved rows may use the raw primary-product `RH`
value at the same native timestamp. RH must be finite and in (0,100]%, with
plausible current TA/PA and a screened VPD/QBOT reconstruction:

```text
VPD_candidate = es(TA_after_prior_QC) * (1 - RH_raw / 100)
```

This fallback changes VPD only and preserves the TA/PA reached by prior QC.
It adds no RH floor or RH interpolation. Missing, zero, out-of-range RH or
failed reconstruction remains on HOLD and prevents that site's candidate
from being selected. RH may share sensor or processing provenance with VPD;
its source quality is not independently established. Original RH/RH_QC,
VPD/QC, source CSV row number, TA/PA, ERA evidence, proposed values and
decisions are recorded for every blocker, including rejected candidates.
All accepted reconstructions receive explicit manual-review entries.

The driver verifies the Stage07 raw/report/code and output hashes before
importing its reusable audit helper. It independently checks original RH
row/timestamp/value/QC, blocker scope, the reconstruction formula, retained
TA/PA, event scope and manual-review completeness. Successful candidate
files also pass the Stage07 full numeric/conversion/change-ledger audit.
Every input and all five preserved candidates are rehashed after execution.

Run on IRIDIS against the exact existing Stage07 trial:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch02'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage08"
  for FILE in scripts/stage08/qcv5_raw_rh.py scripts/stage08/08_resolve_blockers_with_raw_rh.py; do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  "$PYTHON_BIN" -B "$BASE/scripts/stage08/08_resolve_blockers_with_raw_rh.py" \
    --run \
    --stage07-root '/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/qcv5_native_trial_20261022T010124Z_dfae01c2' \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_stage08_$(date +%Y%m%d_%H%M%S).log"
)
```

Reuse the exact existing Stage07 helper, engine and manifest files; their
hashes were pinned by that trial. The Stage08 command downloads only its
two new files. `--check` verifies inputs without creating outputs.

`--run` creates a fresh `raw_RH_sensitivity_<UTC>_<ID>/` under this batch's
experiment directory. Per-site `qc_v5/*_native_RH_resolution_attempts.csv`
and `*_RH_provenance_audit.json` document attempted/rejected RH fallback.
Complete sites also have candidate forcing, event/manual-review ledgers and
independent audits. Root `raw_RH_run_summary.csv`,
`input_preservation_check.json`, `exact_input_manifest.json`,
`selected_candidates.json`/`.csv` and `output_sha256.json` describe the
selection without copying the five preserved Stage07 forcing CSVs.

Any failure retains `INCOMPLETE_SENSITIVITY_DO_NOT_USE_FOR_DATM`, excludes
that site from selection and exits nonzero. An all-site result creates
`COMPLETE_TEN_SELECTED_CANDIDATES_REVIEW_REQUIRED`: five preserved Stage07
candidates plus five raw-RH sensitivities. This is a numeric selection,
not scientific or DATM/model approval. The Stage07 incomplete marker is
always preserved. ZBOT, surface/PFT representation and all QC0/floor/RH
changes still require appropriate review.

Synthetic validation used the real Stage04b/05/06/07 report chain and ten
complete native-year sources with exactly five humidity-blocked sites.
It checked successful five-plus-five selection, blocker count/example
reproduction, raw-row/RH/QC evidence, VPD-only changes with retained TA/PA,
manual-review entries, and unchanged source/report/Stage07 candidate hashes
and modification times. Successful HH/HR CSVs matched Stage07 when the new
fallback was unnecessary. Tampered RH evidence and preserved forcing were
rejected. Missing, zero and out-of-range RH produced a four-plus-five partial
selection, an excluded failed site and a retained incomplete marker, with
no added RH floor. These tests do not predict how many of the actual 4,904
IRIDIS blockers have usable raw RH.

## Stages 09/10: Post-v5 gates and pipeline

Batch02 follows the uploaded Batch01 Post-v5 operation, with explicit native
HH/HR and candidate-selection adaptations:

| Batch01 operation | Batch02 equivalent |
| --- | --- |
| [Stage21 independent numeric/provenance audit](../AmeriFlux_MultiSite_10/scripts/stage21/21_verify_ten_qcv5_candidates.py) | Stage09 numeric, conversions and raw-to-event ledger audit |
| [Stage22 extreme meteorology / source switches](../AmeriFlux_MultiSite_10/scripts/stage22/22_post_qcv5_extremes_source_switches.py) | Stage09 extremes, source/QC switches and every QC0 modification |
| [Stage23 Post-v5 runner](../AmeriFlux_MultiSite_10/scripts/stage23/23_run_post_qcv5_science_gates.sh) | Stage10 Stage08-to-Post-v5 pipeline, with failure gating |

[Stage09](scripts/stage09/09_post_qcv5_batch02.py) reads only the exact
completed Stage08 selection: five preserved Stage07 candidates plus five
same-release-RH sensitivities. An incomplete selection is rejected before
report creation. Raw/report/code, selected forcing and event/manual/status
hashes are verified before and after the audit.

The first Post-v5 gate reuses the checksum-pinned independent numeric audit
helper, with its audit JSON writer redirected into the new report directory.
It rechecks full native NO_LEAP chronology, forcing ranges, native rainfall
conversion, independent QBOT, seven-variable source-to-candidate changes,
original values/QC and the complete replacement ledger. It never rewrites
the earlier independent-audit JSONs in either candidate trial.

The second gate reproduces Batch01's HH extreme screens and adds actual
candidate-source switches alongside original QC switches. It reports new
and retained temperature jumps, isolated spikes, temperature differences
from ERA, TA below -25 or above 45 C, VPD/pressure jumps, heavy rainfall,
low positive RH and all original-source QC0 edits. QC0 totals come from this
batch's independently reconciled events; Batch01's fixed 518 is not reused.
Low positive RH in the 1–5 and 5–10% bins is also counted. These are review
screens, not automatic edits or proof that cold/dry observations are wrong.

Rate thresholds retain the HH values and use their nominal hourly equivalent
for US-Ha1:

| Screen | HH / 30 min | HR / 60 min |
| --- | ---: | ---: |
| TA step | >8 C | >16 C |
| VPD step | >5 hPa | >10 hPa |
| Pressure step | >5000 Pa | >10000 Pa |
| Accumulated rain | >18 mm | >36 mm |

Hourly data cannot resolve within-hour extremes. Rate flags use the native
model-grid step; event context includes the actual source clock gap so
leap-day-removal boundaries can be reviewed separately. Episode grouping
uses the Batch01 two-hour separation. RH bin edges use the same 1e-9
percentage-point reporting tolerance as the Batch02 candidate audit.

[Stage10](scripts/stage10/10_run_batch02_qcv5_post.sh) provides these modes:

- `build-and-audit`: run Stage08 into a fresh, explicitly named directory;
  only if all ten selections pass, run both Stage09 Post-v5 gates.
- `audit SELECTION_ROOT`: re-audit an exact completed Stage08 selection
  without rebuilding candidates.
- `check SELECTION_ROOT`: verify selection and input hashes without new
  reports or candidates.

For the last uploaded Stage07 result, run the combined next step on IRIDIS:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch02'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage08" "$BASE/scripts/stage09" "$BASE/scripts/stage10"
  for FILE in \
    scripts/stage08/qcv5_raw_rh.py \
    scripts/stage08/08_resolve_blockers_with_raw_rh.py \
    scripts/stage09/09_post_qcv5_batch02.py \
    scripts/stage10/10_run_batch02_qcv5_post.sh
  do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  PYTHON="$PYTHON_BIN" bash "$BASE/scripts/stage10/10_run_batch02_qcv5_post.sh" build-and-audit \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_QCv5_Postv5_$(date +%Y%m%d_%H%M%S).log"
)
```

Existing Stage07 helper/engine/manifest files stay in place because the
original trial pinned their hashes. The pipeline chooses and prints its
exact Stage08 output directory; it never searches for a latest trial.
If Stage08 still fails at unusable RH, execution stops before Post-v5.

Post-v5 creates only a fresh `reports/stage09_postqcv5_<UTC>_<ID>/`, containing
`numeric_audits/`, `numeric_and_ledger_summary.csv`,
`site_extremes_and_sources_summary.csv`, `timestamped_event_context.csv`,
`all_original_QC0_edits.csv`, `annual_extreme_counts.csv`,
`site_failures.csv`, `input_manifest.json`, `input_preservation_check.json`
and `postv5_summary.json`. Any numeric/ledger or input-preservation failure
returns nonzero. Science flags remain `REVIEW_PRE_DATM` even if numeric
checks pass; source/candidate files, surfaces, DATM, cases and jobs are not
modified by Post-v5. ZBOT, PFT representation and scientific changes remain
separate decisions before model setup.

Validation used the synthetic Stage04b–08 chain, completed ten-site selection
and both Post-v5 gates. All ten candidates passed; the actual fixture QC0
total was 55, demonstrating that no Batch01 total was hard-coded. All matching
HH screen counts agreed with fixed Batch01 Stage22. HR temperature/pressure
and rainfall threshold cases, full end-year tables, report-only JSON routing,
input/candidate hashes and modification times were checked. An incomplete
Stage08 selection blocked Post-v5 before report writes. Separate mocked
runner checks verified failure stopping, passing the exact fresh selection
path and auditing/checking an existing selection without rebuilding it.
Live Batch02 Stage08/Post-v5 outcomes remain pending operator execution.

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

## Stage11–31 cold-humidity scientific audit archive (24 October 2026)

The original Stage11–22 scripts were restored from the historical Stage22 commit. Stage23–30 inline analyses are archived as reproducible read-only entry points (not byte-identical copies); Stage31 is the next source-aware sensitivity gate. See [scientific audit report and IRIDIS6 instructions](docs/cold_humidity_scientific_review_20261024.md).

**SCIENCE HOLD:** 4,884 unresolved Stage08 records, 0 DATM-approved replacements; US-Ho1 time offset is still provisional. Avoid rerunning completed CDS downloads or overwriting preserved Stage07/08 candidates.

### Stage31 result and Stage32 source/phase audit (24 October 2026)

Stage31 passed on IRIDIS6 and classified all 4,884 held targets by original temperature provenance (QC0 **938**, QC2 **3,945**, other **1**). All RH-transfer candidates were numerically within water-phase bounds, but 431 dewpoint-transferred variants were negative (Ho1 425, GLE 6) and 2,782 ice-supersaturation cautions were flagged. **No approval.** Stage32 is a new read-only script comparing the source-stratified RH-transfer, dewpoint-transfer, and paired CDS-T/RH *numerical reference* with ice/temperature/timezone review flags. [See science report and GitHub-to-IRIDIS instructions](docs/cold_humidity_scientific_review_20261024.md).

### Stage32 result, Stage33 US-Ho1 clock alignment sensitivity

Stage32 completed on IRIDIS6: all 4,884 held records re-verified, 431 Td-transfer negative-water-VPD conflicts (Ho1 425, GLE 6), and 2,782 ERA5 ice-RH warnings. All remain SCIENTIFIC HOLD, no repairs approved. Stage33 uses already downloaded SHA-pinned ERA5 NetCDF grid-years to compare hypothetical local-minus-UTC offsets -7 to -3 against original observed QC0 temperature, separately for all covered years, winter and held targets. This is not independent timezone certification. See [science provenance and stage details](docs/cold_humidity_scientific_review_20261024.md).

**Stage33 v2 path-identity hotfix:** original Stage19 receipt ledger used unreconciled `/home` spelling; Stage33 originally resolved `/iridisfs/home` before ledger lookup. V2 compares aliases of the **same file** but strictly checks SHA256 against Stage19 and the verified NetCDF receipt. See [review notes](docs/cold_humidity_scientific_review_20261024.md). Do not run `set -e` unguarded on interactive HPC login shells during diagnosis.


### Stage33 checked; Stage34 QC2 temperature-provenance audit

Stage33 v2 passed: US-Ho1 nominal UTC-5 best matched 106,336 observed-T QC0 timestamps among tested offsets -7 to -3 (MAE 1.472 C), but the 425 negative dewpoint-transfer VPD cases persist regardless of offset (421-427). Missing original QC0 temperatures in multiple anomaly years demand a source-focused review. Stage34 is now the next read-only script; it checks the 425 negative-VPD QC2 timestamps against independently downloaded CDS ERA5 temperature/dewpoint and original FLUXNET temperature gapfill by year. See the science review in docs/cold_humidity_scientific_review_20261024.md. Zero repairs approved.


### Stage34 verified and Stage35 neighbouring Howland QC0 audit

Stage34 passed with 917 Ho1 held, 425/425 negative Td-transfer VPD events in QC2 temperatures, and large CDS vs FLUXNET temperature differences (median +11.7672C within the 425). Stage35 now checks original site-QC0 temperature from nearby Ho2 and Ho3, with pinned input SHA256 and no forcing or model changes. See docs/cold_humidity_scientific_review_20261024.md. No science approvals.

### Stage35 passed; Stage36 original-source independence audit

Stage35 verified all three original Howland tower SHA256 releases. In Ho1's 425 negative Td-transfer VPD cases, Ho2 QC0 overlaps **67**, Ho3 QC0 overlaps **106**, and **all 67 Ho2** records coincide with Ho3: only **106 unique** timestamps have neighbour QC0, with **319** lacking both. CDS ERA5 T is much closer to these QC0 sources than original Ho1 QC2 temperature; nevertheless, Ho3/Ho1 are suspiciously close (0.000°C mean difference in 85 held QC0 records in 2012). Stage36 tests for shared or duplicated original temperature source and does **not** approve any model forcing. See docs/cold_humidity_scientific_review_20261024.md for scientific limitations.


### Stage36 verified; Stage37 missing-independent-evidence audit (24 October 2026)

Stage36 found exceptionally long exact Ho1–Ho3 original QC0 temperature matching (~311.6 consecutive days in 2012), suggesting shared meteorological processing rather than independent instruments. At the 425 US-Ho1 negative dewpoint-transfer VPD events, only 106 unique timestamps have any neighbouring original QC0 (Ho2 67, Ho3 106, both 67); 319 timestamps have none (1998:64; 1999:25; 2001:230). The 67 simultaneous Ho2–Ho3 QC0 temperature records differ numerically (median abs difference 0.32°C), and both sources favour CDS ERA5 over Ho1 QC2 at these timestamps. The new [Stage37 read-only ERA provenance audit](scripts/stage37/37_audit_Howland_319_unanchored_ERA_provenance.py) focuses on the 319 unanchored observations without treating Ho2 ERA as independent verification. See [scientific review](docs/cold_humidity_scientific_review_20261024.md). **All 4,884 remain HOLD; approvals=0.**

### Stage37 verified; Stage38 historical measured-temperature source inventory

Stage37 successfully traced Ho1's 319 negative-Td-VPD records with no neighbouring QC0: 1998 64, 1999 25, 2001 230. In 1999/2001 Ho2 *ERA gapfill* follows CDS ERA5 within ~0.65°C median, while Ho1 QC2 gapfill differs by ~9.4–11.6°C, suggesting a Ho1-specific processing problem, not independent observation validation. Stage38 performs a **read-only local Ho1 BASE/BADM archive inventory** and prints exact date windows and modern NOAA GHCNh candidate station-year sources, with explicit unverified-coverage warnings. No new downloads or model changes; see [scientific audit](docs/cold_humidity_scientific_review_20261024.md). All 4,884 remain on HOLD.

### Stage38 verified; Stage39 memory-only NOAA GHCNh source probe

Stage38 identified the 319 Ho1 cases without neighbouring QC0 as 1998 64 (4 episodes), 1999 25 (3), 2001 230 (9) and found only the original FLUXNET FULLSET ZIP in its bounded local search (not proof BASE/BADM is unavailable elsewhere). Stage39 adds a standalone read-only NOAA GHCNh station-year availability script with --self-test, offline --check, and explicit optional network --probe. It does not write external data or declare NOAA station quality accepted. [See detailed science record](docs/cold_humidity_scientific_review_20261024.md). 4,884 HOLD / 0 approved forcing replacements.


### Stage39 v2 preflight bug fix (24 October 2026)

Initial Stage39 --self-test passed, and three original source checksums passed, but --check failed before NOAA network access due to invalid `.all()` calls on the scalar bool returned by `np.allclose()`. Stage39 v2 corrects both checks, retains SHA256 and strict numerical comparisons, and adds a synthetic regression case. **No NOAA probe was launched, no original data were changed, and no repair was approved.** See [scientific audit record](docs/cold_humidity_scientific_review_20261024.md).

### Stage39 v3 NOAA PSV STATION field fix

Stage39 v2 passed original data checks and reached NOAA for 1998, 1999 and 2001, but its `--probe` parser mistakenly required `station_id` rather than the actual NOAA `STATION` field. Stage39 v3 accepts the correct header, rejects station-ID mismatches, and adds an actual-header regression test. NOAA numeric-temperature availability/QC is **not verified until v3 runs on IRIDIS6**. Original forcing/model records remain untouched; science HOLD 4,884/4,884. See [audit log](docs/cold_humidity_scientific_review_20261024.md).


### Stage39 v3 verified; Stage40 source-specific NOAA temperature-QC comparison

Stage39 v3 retrieved ALL three Bangor GHCNh PSV station-years (1998/1999/2001) and found a raw numeric temperature report within +/-30 minutes for all 319 unanchored US-Ho1 negative-VPD events. Stage40, located at scripts/stage40/40_compare_NOAA_Bangor_QC_with_Ho1_CDS.py, reuses the pinned Stage39 source gate and exact NOAA PSV SHA256s, applies provisional legacy source-specific quality codes (223/1 or 335/5) with matching station provenance and then reports NOAA vs original Ho1 QC2 vs CDS ERA5 temperature comparison. It separately counts distinct NOAA reports to avoid half-hour pseudo-replication. Airport microclimate and Ho1 UTC offset remain unresolved, and NO forcing repairs are approved. See docs/cold_humidity_scientific_review_20261024.md.

### Stage40 passed; Stage41 distinct-NOAA-report and Ho1 QC0 control review

Stage40 verified 316/319 source-QC-screened Bangor temperature comparisons but only 197 distinct NOAA source reports. The 1998/1999/2001 airport-to-Ho1 original QC2 MAEs were 17.191/13.008/11.640 C, versus airport-to-CDS ERA5 MAEs of 1.057/1.109/1.520 C. Three equidistant conflicting 2001 matches were excluded. Stage41 (scripts/stage41/41_audit_NOAA_event_dependence_Ho1_QC0_calibration.py) analyzes independent source-report weighting and 16 episodes, plus 3,005 measured-coded Ho1 1999 QC0 temperatures as separate airport-to-forest calibration observations outside the February anomalies. The source QC and provisional UTC clock remain restricted. See [review details](docs/cold_humidity_scientific_review_20261024.md). Original 4,884 scientific HOLD and zero repairs approved.

### Stage41 completed; Stage42 1999 measured-QC0 site-airport comparison

Stage41 successfully reconfirmed **197 distinct** source-QC-screened NOAA reports across the 316 anomalous Ho1 timestamp pairs. Per unique report, overall Bangor-to-original Ho1 QC2 MAE was **12.881 C**, versus Bangor-to-CDS ERA5 MAE **1.274 C**. All 16 contiguous anomaly episodes favour CDS in episode-level MAE, with a less clear 2001 episode. Separately, 1999 original Ho1 QC0 temperatures (Oct-Dec only: 3,005 records) show Bangor-minus-Ho1 MAE **5.024 C** on 2,986 provisionally QC-screened pairs, exposing spatial/seasonal/time-alignment uncertainties. The new [Stage42 script](scripts/stage42/42_audit_Ho1_1999_QC0_Bangor_temporal_bias.py) tests hypothetical UTC offsets -7 to -3 on *common tower timestamps*, monthly/local-hour QC0 bias, and sustained differences, without replacing any forcing or asserting February representativeness. All 4,884 original records remain scientific HOLD, with zero approved repairs.

### Stage42 passed; Stage43 Ho1 original QC0 and TA_ERA source triangulation

Stage42 verified 1999 Ho1 October–December observed-coded QC0 temperatures (3,005 total): nominal −5 local-minus-UTC Bangor comparison has 2,986 provisionally NOAA QC-screened matches (1,498 unique reports), MAE **5.024°C**, with both positive and negative long deviations >10°C. Across the *same 2,942 QC0 timestamps*, trials −7 to −3 h yield MAE 5.075/5.020/5.002/5.010/5.039°C; −5 is the minimum but is not an official BADM time-zone certification. The February 1999 25 original Ho1 QC2 temperature anomalies remain 11.3–14.0°C from Bangor across tested offsets. [Stage43](scripts/stage43/43_audit_Ho1_1999_QC0_vs_two_ERA_Bangor.py) now audits original Ho1 QC0 and Ho1/Ho2 processed TA_ERA source temperatures against Bangor in the same 1999 fall timestamps and February failures. No forcing/model writes or science approvals; all 4,884 remain HOLD.

### Stage43 verified; Stage44 original ERA5 companion source-provenance review

Stage43 successfully traced 1999 Ho1 temperature discrepancies on exactly 2,986 measured-QC0/NOAA source-screened matches and 25 February QC2 failure timestamps. In the QC0 controls, Ho1 original `TA_ERA` versus Bangor MAE was **6.672 C**, while Ho2 original `TA_ERA` versus Bangor MAE was **1.377 C**; in the February QC2 failures Ho1 `TA_F` equalled its `TA_ERA` (0 C residual), and Bangor-versus-Ho1 gap MAE **13.008 C** versus Bangor-versus-Ho2 ERA **1.061 C**. Official FLUXNET metadata define `TA_ERA` as **site-regressed ERA air temperature**, not raw grid ERA5. New [Stage44](scripts/stage44/44_audit_Ho1_FLUXNET_ERA5_companion_provenance.py) performs a strictly read-only inventory and conditional native-timestamp comparison with `ERA5_HH` / `AUXMETEO` companions inside the original Ho1 FULLSET ZIP, checking ZIP-HH original SHA256 identity without extracting files. This tests whether companion ERA fields are another alias of processed data; it does not authorise forcing changes. All 4,884 original Batch02 targets remain scientific HOLD.

### Stage44 verified: ERA5_HH TA_ERA duplicates FULLSET; Stage45 AUXMETEO parameter audit

Stage44 successfully confirmed the original US-Ho1 FULLSET archive SHA256 and FULLSET_HH byte identity with Stage08, then found that companion `ERA5_HH` `TA_ERA` is **exactly equal** to the corresponding FULLSET `TA_ERA` on all **52,560** half-hours in 1998, 1999 and 2001, including **all 319** held source temperature/dewpoint cases. This is a distributed processed-field alias, not independent ERA verification. The accompanying original `AUXMETEO` is only 1,002 bytes with columns `ID, VARIABLE, PARAMETER, VALUE, TIMESTAMP`; its contents still need review. New [Stage45](scripts/stage45/45_audit_Ho1_AUXMETEO_metadata_provenance.py) pins all prior source SHA256s and the whole ZIP SHA256, prints the untouched AUXMETEO metadata rows read directly from ZIP in-memory and does not interpret unverified coefficients or change forcing. All 4,884 remain SCIENTIFIC HOLD and 0 repairs approved.

### Stage45 complete; Stage46 Ho1 AUXMETEO-vs-measured-QC0 empirical fit audit

Stage45 successfully read and SHA256-verified the **32** original US-Ho1 AUXMETEO processing parameters. Temperature `TA` has `ERA_SLOPE=1.00`, `ERA_INTERCEPT=-0.00`, `ERA_RMSE=4.66`, `ERA_CORRELATION=0.72` (`TIMESTAMP=-9999`). Official FLUXNET documents define these as site-downscaling regression parameters; numerical metadata values are printed to only two decimals and must not be mistaken for proof of a fallback or identical raw ERA input. New [Stage46](scripts/stage46/46_recompute_Ho1_QC0_vs_ERA_AUXMETEO_diagnostics.py) performs a strictly read-only, pinned-sha audit of observed-coded QC0 `TA_F` versus existing downscaled `TA_ERA` over all available original Ho1 years, details the 1999 observed October–December season and checks the 319 held anomalies. It reports an **empirical descriptive fit** without claiming to replicate the original pipeline's calibration data or raw ERA regression. All 4,884 remain on scientific HOLD, 0 approved repairs.

### Stage46 verified; Stage47 original MDS source/QC lineage review

Stage46 successfully validated all original source/ZIP/AUXMETEO hashes and the 319 held Ho1 QC2 cases. On 274,148 original measured-coded Ho1 `TA_F_QC=0` half-hours versus distributed `TA_ERA`, Pearson r **0.71944** matches the reported AUXMETEO ERA_CORRELATION **0.72**, but computed RMSE **7.7346°C** differs from AUXMETEO ERA_RMSE **4.66°C** (different/unknown original fit population; no provenance verdict). Empirical OLS slope measured-on-downscaled-ERA **1.00196**, intercept **-0.01508°C**. In 1999 Oct–Dec, QC0 n=3,005 had r **0.08069** and RMSE **7.0377°C**; 1998/2001 original observed QC0 records are absent. New [Stage47](scripts/stage47/47_audit_Ho1_MDS_QC0_vs_ERA_residual_concentration.py) checks original `TA_F_MDS_QC` against consolidated source flags and quantifies the heavy-tailed temperature residuals at 319 held events. All 4,884 original targets remain science HOLD, zero approved repairs.

### Stage47 completed; Stage48 ten-site VPD-negative / low-RH external-ERA policy

Stage47 successfully reconfirmed that all 274,148 original Ho1 consolidated measured-coded QC0 T equal their MDS measured-coded QC0 source exactly, and the 319 held Ho1 original QC2 T records all have poor-quality MDS QC=3 (MDS-vs-ERA temperature differences ~18.97°C in 1998, ~17.38°C in 1999 and ~2.53°C in 2001). Ho1 original QC0 versus site-downscaled ERA empirical RMSE is 7.7346°C, with >=10°C differences making up 64.159% of squared error. Stage48 adds new negative-VPD/negative-RH physical screens and a **conditional independently retrieved CDS ERA5/ERA5-Land humidity candidate** rule for the full 10-site batch; very low positive RH <1% is high-priority manual review rather than mandatory substitution. An exact source/UTC/elevation/air-T-QC gate prevents using in-package FLUXNET ERA and prevents humidity-only replacement at suspect Ho1 QC2 temperature. See [ten-site audit and rule policy](docs/batch02_ten_site_qc_and_era_repair_policy_20261024.md) and [Stage48 read-only scanner](scripts/stage48/48_audit_ten_site_vpd_rh_era_repair_rule.py). All 4,884 original held records remain unapproved, and five numeric Stage07 site candidates still need review. No model forcing files were changed.


### Stage48 IRIDIS6 verified and Stage49 original-source review ledger (24 October 2026)

Stage48 was executed on IRIDIS6 and its self-test, inventory preflight and
full ten-site read-only audit completed with the original SHA256 inputs
unchanged. Original source rows: **3,462,624** (3,460,200 future NO_LEAP);
**26,332** unique hard humidity screens, of which **25,890** have
nonpositive derived water RH; **39** raw RH=0, **405** raw RH>100,
**102** raw positive RH<1%; no negative raw VPD and no negative raw RH.
**21,551** hard-screen rows carry original TA_QC0 coding, which does not
prove T physical validity. Ho1 dominates (16,788 hard rows); EML 4,311
and ICt 2,570 also require priority review. These are NOT the 4,884 Stage08
scientific HOLD cohort, and no model repair has been approved.

The exact operator-reported per-site table, physical caveats, new Stage49
code link, and complete IRIDIS6 instructions are archived in
[Stage48 verified results and Stage49 instructions](docs/stage48_operator_result_and_stage49_20261024.md).
The new read-only [Stage49 row-level science ledger](scripts/stage49/49_build_ten_site_original_humidity_review_ledger.py)
pins the existing Stage48 Git blob, checks the source inventory and hashes
before/after scanning, classifies original hard-humidity and raw RH<1%
records with conservative manual science routes, and produces fresh
CSV/JSON reports without modifying source or prior candidates.
Stage49 was subsequently executed successfully on IRIDIS6, generating 26,432 unique original RH physics / extreme-dry review rows. The original source inputs remain unchanged.

**Science HOLD unchanged:** Stage08 cohort 4,884 rows; 0 approved
replacement/forcing/model jobs. Avoid making automatic ERA substitutions
from the in-package FLUXNET companions or from RH>100 near saturation;
external CDS ERA5/ERA5-Land and site time/temperature must first be validated.


### Stage50 external CDS ERA5 RH=0/>100 unified candidate policy (24 October 2026)

Operator Stage49 self-test, check, and audit **PASSED** on IRIDIS6,
with 3,462,624 immutable primary source rows and 26,432 unique original
hard-humidity/positive-RH<1 review rows. Original RH=0: **39** records;
original RH>100: **405** records, across exactly four sites:
US-Ha1 398, US-Ho2 7, US-ICh 9, US-ICt 30. These **444** candidate
replacements are a narrow subset of the raw original-source science task,
not the Stage08 4,884 held-cohort.

[Stage50 source-pinned script](scripts/stage50/50_prepare_unified_CDS_ERA5_RH_zero_gt100.py)
and [full methodology and IRIDIS6 commands](docs/stage50_unified_CDS_ERA5_RH_zero_gt100_20261024.md)
use one independent CDS **reanalysis-era5-single-levels-timeseries**
(t2m/d2m/sp) product. They verify native BIF site coordinates and
UTC offsets, reuse checksum-verified Stage15/18 grid-years if equivalent,
and plan/fetch only missing ERA5 grid-years before creating separate
timestamp-exact candidate RH/VPD/QBOT. They never use
in-package FLUXNET *_ERA as independently retrieved CDS, never mix
ERA5-Land, and never overwrite original, Stage07/08, DATM or Slurm files.

The scheme interpolates ERA5 **water RH** hourly to native local-standard
tower timestamps, then derives candidate VPD and QBOT using the retained
tower T and P. Original T QC2, T discrepancy >8 C or unverified source
prevents unconditional humidity-only application. The >100% original
RH group also carries phase/supersaturation review. **Stage50 has now
completed its IRIDIS6 build**: 10/10 verified external CDS ERA5 grid-years,
444 candidate RH values, 12 original-RH-zero retained-T proposals,
405 RH>100 phase-review proposals, and 27 joint-T/RH manual reviews.
All remain unapproved for model forcing. See the Stage50 operator log
summary and [Stage51 read-only joint-temperature review](docs/stage50_operator_success_and_stage51_review_20261024.md).


### Stage51 completed and Stage52 scientific review (24 October 2026)

Operator-reported Stage51 **AUDIT PASS** after the completed Stage50 build:
all **444** independent CDS ERA5 RH candidates reconciled and remain
scientifically **unapproved**. **12** original RH=0 rows can retain
tower T for a humidity-only candidate; **405** RH>100 rows require
supersaturation/phase review (**396 US-Ha1 and 9 US-ICh**); **27**
original RH=0 cases require T-quality review (**all US-ICt**).
All 27 original US-ICt T QC flags are nonzero, but none has
|Tsite - independent ERA5 T2m| >8 C. This does NOT prove the original
site T valid or justify automatic joint T replacement.

[Stage51 exact operator results and Stage52 run instructions](docs/stage51_operator_success_and_stage52_next_20261024.md)
and the new [Stage52 read-only RH/T QC audit](scripts/stage52/52_review_original_RH_supersaturation_and_ICt_temperature_QC.py)
retain the prior Stage50/51 SHA256 provenance. Stage52 will quantify the
405 RH exceedances and below-zero phase evidence, and show original
QC distributions and same-ERA5 alternative T/RH/VPD/QBOT for all
27 ICt events. **Stage52 has now passed on IRIDIS6; see the Stage52 completed results and Stage53 staging policy below.**

### Stage52 VERIFIED; Stage53 same-CDS-ERA5 RH-only staged-policy candidate (24 October 2026)

Operator Stage52 **AUDIT PASS**: 444 original RH defects comprise
39 zero-RH and 405 >100% events. Of 405 supersaturation events,
396 occur at US-Ha1 (102: 100–100.5%, 101: 100.5–101%,
181: 101–105%, 12: >105%, max 110.8%);
9 occur at US-ICh (all 100–100.5%, max 100.3%).
All 405 original source VPD values are near zero, and
229 RH>100 events are below freezing (Ha1 220; ICh 9).

The 27 US-ICt original RH=0 T-quality review events are
**14 original TA QC1 + 13 original TA QC2**; none has
abs(Tsite - independent CDS ERA5 T2m) >8 °C, maximum 5.193 °C.
Do not infer QC1/2 air temperature valid solely from the ERA5
temperature-difference screen.

**User-selected policy:** calculate and stage replacement RH for
**all 444/444 source RH=0 or RH>100 records from the same independently
downloaded CDS ERA5 t2m/d2m/sp source**, preserving EC tower T and
pressure and recomputing physically consistent candidate VPD and
QBOT. No unrequested TA substitution is performed; the 27
original-T QC1/QC2 cases retain a separate scientific gate, as
do all 405 phase/supersaturation events. This staging policy
does **not** mean the corrections have been written to DATM.
The unrelated Stage08 4,884-case HOLD remains in force.

[Stage52 verified numerical counts, Stage53 science policy,
full reproducible commands](docs/stage52_operator_success_and_stage53_RH_only_staging_20261024.md)
and [Stage53 isolated sparse patch script](scripts/stage53/53_stage_user_selected_444_external_ERA5_RH_only_patch.py)
are published in GitHub; Stage53 was subsequently executed successfully on IRIDIS6 and an isolated 444-row staging ledger now exists.

### Stage53 operator PASS; Stage54 exact 444 vs 4,884 collision audit (24 October 2026)

The operator's Stage53 `--self-test`, `--check`, and `--stage` **ALL PASSED** with pinned blob
`824f18c7868fa451274b1e359906ece2fd84a199`.
Real Stage53 output:
`reports/stage53_444_ERA5_RH_only_staging_20261024T100652Z_543ef3f1`.
Exactly 444 RH=0/>100 source rows have user-selected independent
CDS ERA5 humidity replacements and same-RH/tower-T/PA
physically consistent VPD and QBOT in an isolated sparse patch.
The 27 US-ICt original T QC1/2 uncertainties and 405 RH>100
phase questions retain explicit scientific review flags; **not
approved for DATM or spinup**. Original data and forcing unchanged.

Next, [Stage54 read-only exact-overlap script](scripts/stage54/54_crosswalk_444_ERA5_RH_stage11_4884_HOLD.py)
must reconcile `site+timestamp_start` against Stage11's
`site+time` for the separate 4,884 scientific HOLD
cohort, preventing accidentally applying two different decisions
to one original tower record. [Verified Stage53 result and Stage54
run instructions](docs/stage53_operator_pass_stage54_overlap_plan_20261024.md).
Stage54 has now **passed** in IRIDIS6 with **zero** exact same-site/original-tower-local-time collisions (444 Stage53 only; 4,884 Stage11 only). See [Stage54 operator-verified result](docs/stage54_operator_verified_zero_overlap_20261024.md). No model input was altered.


### Stage54 IRIDIS6 PASS: 444 and 4,884 have ZERO exact same-site/local-time overlap (24 October 2026)

Operator source check and full Stage54 AUDIT both passed using
Git blob `f74d004bf9277c0583309387ea1352703da76db7`.
Intersection = **0**; Stage53-only = **444**, Stage11-only
= **4,884**, 5,328 distinct *audited-target* timestamps across
the two cohorts. Exact Stage11 distribution: US-EML 1,327;
US-GLE 295; US-Ho1 917; US-ICh 169; US-ICt 2,176.
This does not mean all original Stage48 26,332 hard-physics records
are resolved and it does not remove the 4,884 science HOLD.
[Archived exact Stage54 result](docs/stage54_operator_verified_zero_overlap_20261024.md).

**Next:** [Stage55 read-only existing-ERA5 scientific triage](scripts/stage55/55_triage_existing_stage19_4884_ERA5_science_HOLD.py)
reuses the previous independently retrieved CDS ERA5 Stage19
4,884-row sensitivity report, verifying source SHA256 and source-local
timestamps before classification. It does not download new ERA5
or authorize any forcing/model writes. If the matching Stage19
report does not already exist, Stage55 explicitly stops and directs
the operator to generate Stage19's isolated report from verified
existing CDS data. [Stage55 reproducible IRIDIS6 instructions](docs/stage54_pass_stage55_existing_4884_ERA5_triage_20261024.md).
Stage55 has subsequently passed on IRIDIS6; see the verified checkpoint below.


### Stage55 AUDIT PASS: 4,884 existing ERA5 candidates numerically valid; science HOLD remains (2026-10-24)

IRIDIS6 Stage55 syntax, self-test, exact-source check and full audit
**PASSED**, using the existing Stage19 4,884-row external CDS ERA5
report. Stage54 zero-overlap with the 444 Stage53 RH proposals was
confirmed. Stage55 found **0 numeric-invalid** records; 4,884/4,884
are still science HOLD. Primary exclusive review groups:
- 3,245 original temperature-QC concern,
- 689 water/ice saturation review,
- 33 tower vs ERA5 air-temperature discrepancy >8 C,
- 917 US-Ho1 UTC−5 provisional alignment.

The exclusive routes are prioritization only. Across all records
the overlapping raw flags show **3,946** original TA QC not 0,
**4,884** original VPD QC not 0, **433** tower-minus-ERA5
T absolute differences >8 C, and **4,884** water/ice cautions.
None was automatically released for forcing/model runs.
The 444 Stage53 RH choices are still isolated staging records,
not actual DATM writes.

[Detailed verified Stage55 operator checkpoint and remaining science gates](docs/stage55_operator_PASS_checkpoint_20261024.md).
Further action: scientifically adjudicate the 4,884 Stage11 HOLD
records and US-Ho1 UTC offset; then audit combined independent
stage revisions against the broader Stage48 original hard-physics
census before a new forcing build. The source 26,332 hard cases
are NOT automatically covered by the 5,328 distinct Stage53+Stage11
targets. No model spinup has begun for this Batch02 workflow.


### Stage56 original-EC-temperature retention policy (≤8 °C compared with verified ERA5) — 24 October 2026

The operator selected a specific temperature QC rule for the **4,884
distinct Stage11 HOLD records**: **retain ORIGINAL FLUXNET TA_F**, even
if TA_F_QC is QC1/QC2, when it is numerically valid and the absolute
difference to the same independent CDS ERA5 T2m is **≤8.0 °C**.
Do not use the Stage11 retained T as a substitute without checking its
equality to original TA_F. Invalid original T/ERA5 T or >8 C site/ERA5
differences remain explicit temperature HOLD; unusual or missing QC
codes are flagged, but QC by itself never forces T replacement. No automatic replacement
of tower T is authorized. **US-Ho1 stays provisional for all 917
records** until site metadata/UTC_OFFSET is independently confirmed.

[Published Stage56 script](scripts/stage56/56_keep_original_tower_T_when_ERA5_within_8C.py)
uses the previously verified Stage19 ERA5 RH to recompute consistent
candidate VPD/QBOT against original TA_F and original PA_F where
safe. [Stage56 complete policy, safeguards and pinned IRIDIS6
commands](docs/stage56_user_policy_keep_original_T_within_8C_20261024.md).
All cold-water/ice humidity review flags remain attached and **none
of the 4,884 are auto-approved as model forcing**; Stage53 444
independent RH candidates remain unchanged. Stage56 published on
GitHub but not yet executed on IRIDIS6.


### Stage57: investigate exact 63 TA_F vs independent ERA5 temperature discrepancies >8 C (24 October 2026)

Stage56 operator check and full audit **PASSED**: 3,904
Stage11 source tower TA_F values are numerically valid and within
8 C of independent CDS ERA5 T2m and are retained in isolated
RH/VPD/QBOT candidates. Remaining discrepancy cases: **US-EML 27,
US-GLE 6, US-ICt 30** (63 total). All 917 US-Ho1 site-time-offset
records remain separate HOLD. No source or DATM writes made.

For the exact 63, new
[Stage57 original-source-and-neighbourhood audit](scripts/stage57/57_manual_review_63_tower_T_vs_ERA5.py)
verifies Stage56 provenance plus the immutable original tower
primary SHA256, then prints original TA_F/QA, same-source independent
ERA5 T2m, temperature difference sign/magnitude, ±30/60/120-minute
original tower neighbors with their QC, nearest QC0 observation,
day median and temporal clustering. It does NOT automatically
claim EC tower errors or replace TA_F with ERA5. **All 63 remain
science HOLD pending manual inspection of actual row-level evidence.**
[Stage57 pinned instructions and science review rubric](docs/stage57_manual_review_63_ec_tower_temperature_gt8C_20261024.md).
Stage57 is published on GitHub but has not yet run on IRIDIS6.


### Stage57 human review: 63 extreme-cold original tower temperatures approved; Stage58 temperature-only integration (24 October 2026)

After inspecting the **actual 63** Stage57 read-only rows, the operator
explicitly approved retaining original tower **TA_F** in all cases:
US-EML 27 (TA QC0), US-GLE 6 (TA QC0), US-ICt 30 (TA QC2). Every
original temperature is **below freezing**, warmer than ERA5 by
8.01–11.63 °C, continuous with adjacent tower observations within
3 °C, and none flagged as an isolated tower spike. This is a
**temperature** acceptance, not an automated release of
RH/VPD/QBOT or forcing.

[Stage58 independent-source-rechecked temperature sign-off](scripts/stage58/58_accept_63_manual_extreme_cold_tower_temperatures.py)
pins original Stage57 source and Stage56/19/11 provenance, joins
the 63 human decisions with the earlier 3,904 retained EC
temperatures, and stages **3,967 original EC temperatures kept**;
**917 US-Ho1** entries retain provisional UTC-offset HOLD.
Candidate ERA5 RH-coupled VPD/QBOT values for 3,967 are recomputed
using original EC TA_F and PA_F but retain full **water/ice-phase
humidity scientific HOLD** and no model/forcing approval.
[63-row evidence, Stage58 reproducible commands and next physical
checks](docs/stage57_manual_approval_and_stage58_temperature_integration_20261024.md).
The Stage57 pasted evidence ends in `STAGE57 CHECK PASS`,
not Stage57 AUDIT; Stage58 regenerates and pins original evidence
rather than relying on an unverified Stage57 report folder.
**Stage58 has been published but not yet executed on IRIDIS6.**


### Stage58 live PASS and Stage59 isolated water/ice humidity review (24 October 2026)

Operator verified pinned Stage58 script and passed syntax/self-test/source
check/audit. Actual report:
`reports/stage58_63_manual_T_approved_3967_T_total_20261024T110141Z_e65bde6c`.
Original EC TA_F is accepted in **3,967 of 4,884** Stage11 records:
3,904 within 8 C of independently acquired CDS ERA5 T2m plus 63
user-reviewed extreme cold readings. The remaining **917 US-Ho1
rows** stay HOLD pending site release UTC_OFFSET validation. All
3,967 have numerically consistent same-CDS water RH / tower-TA_F and
original-PA_F VPD/QBOT candidate values. None are forcing-approved.
[Verified Stage58 output](docs/stage58_operator_PASS_3967_temperature_retained_20261024.md).

**Next Stage59:** [Script for 3,967 water-vs-ice humidity diagnostics
and US-Ho1 source BIF inventory](scripts/stage59/59_review_water_vs_ice_RH_for_3967.py).
It verifies the completed Stage58 report SHA256; converts the
source-pinned ERA5 water RH + original EC TA_F to equivalent
RH with respect to ice and VPD over ice without clipping; quantifies
ice supersaturation and negative ice VPD; separately inventories
source-adjacent US-Ho1 BIF UTC_OFFSET candidates. These are **science
review flags, not automatic defects or original data edits**.
All RH/VPD/QBOT, original Stage11/53, DATM and model forcing remain
under existing HOLD. Stage59 has not yet been run on IRIDIS6.


### Stage59 live PASS; Stage60 4,411 independent ERA5 water-humidity policy staging (24 October 2026)

Operator Stage59 downloaded verified pinned blob and completed syntax,
self-test, source check and AUDIT PASS. Actual report:
`reports/stage59_water_ice_review_3967_20261024T110624Z_2dc93fb4`.
Of 3,967 accepted original-EC-temperature humidity candidates,
2,257 are subzero without ice RH supersaturation,
687 have ice RH 100–105%, 1,013 have ice RH >105%, and
10 have original TA_F >=0 C. **These 1,700 water-to-ice phase
oversaturations are not 1,700 invalid water-RH/QBOT data**:
CLM-FATES forcing needs consistent QBOT, original EC T/PA,
and an explicitly defined water vapour reference; over-ice RH
and ice VPD are diagnostic-only, not inputs.

The user delegated a physical-rule-based correction rather
than manual review of these 3,967 ice-supersaturation flags.
New [Stage60 source-verified 4,411-row automated unified
humidity-policy script](scripts/stage60/60_stage_unified_4411_ERA5_water_humidity_and_hold_Ho1.py)
stages **3,967 Stage58/59 + 444 Stage53** unique EC site/local
times with independent CDS ERA5 water-reference RH and paired
water VPD/QBOT calculated at original EC temperature/pressure.
It confirms original Stage54 no-overlap, provenance SHA256,
same underlying ERA5 product, per-site counts and thermodynamic
identities. **No forcing/model edits or DATM approval**: source
Stage48/07/08 full hard-physics coverage and 10-site native
NO_LEAP forcing validation remain outstanding.

US-Ho1 917 cases **remain UTC-offset HOLD**: the source-release
folder contains no adjacent matching BIF metadata, so the
published AmeriFlux site profile is not sufficient proof
of release UTC_OFFSET. The decision is to retrieve and
authenticate same-product (FLUXNET 3-6) official BADM/BIF
rather than guess from nearby station/timezone.
[Stage59 operator PASS, Stage60 pinned IRIDIS6 command,
physical policy and remaining gates](docs/stage59_operator_PASS_and_stage60_auto_4411_water_humidity_20261024.md).
Stage60 has not yet been run on IRIDIS6.


### Stage60 IRIDIS6 PASS: 4,411 SHA-pinned independent CDS ERA5 water-humidity choices; Stage61 original-source hard-physics coverage (24 October 2026)

Operator ran pinned Stage60 Git blob `7affb6854f479eb008fd566c2f0e5320320a092f`
and passed Python syntax, self-test, source check and isolated STAGING.
Exact Stage60 report:
`reports/stage60_4411_ERA5_water_RH_VPD_QBOT_unified_20261024T112137Z_950f7adf`.
The complete 4,411-row candidate set contains 3,967 accepted
tower-TA/PA humidity replacement cases and 444 original RH=0/>100
cases, with **zero** duplicated (site, tower-local-time), **zero**
candidate water-RH>100 and **zero** negative candidate water-VPD.
Ice RH>100 occurs in 1,700 diagnostic records and is **not**
used as a basis for automatically clipping water RH. These are
**isolated proposals, not yet applied to DATM or model spinup**.

The original 10-site Stage48/49 source data have **26,332 hard
humidity physics anomaly times** among **26,432 original-review
records**. **Do not subtract 4,411 from 26,332** without joining
the actual source identities: the Stage60 population is different.
New [Stage61 original source vs selected Stage60 exact-identity
coverage code](scripts/stage61/61_exact_original_humidity_hard_screen_vs_4411_repair_coverage.py)
reuses Stage49 source-reported original RH/VPD QC and Stage58/
Stage60 SHA-pinned reports; writes only isolated coverage outputs
and the exact per-site/year/time still-uncovered source records.
The 917 original US-Ho1 UTC-offset HOLDs stay separate from this
forcing-ready science policy and no forcing is modified.

[Stage60 PASS and complete Stage61 pinned IRIDIS6 instructions](docs/stage60_operator_PASS_and_stage61_full_original_hard_coverage_20261024.md).
Stage61 published on GitHub; **not yet run on IRIDIS6**.


### Stage61 IRIDIS6 AUDIT PASS: 21,921 original hard humidity events remain after Stage60; Stage62 automatic non-Ho1 data completion (24 October 2026)

Operator Stage61 fixed Git blob `9d67aafa960c4c5e6e41d9c67f7f2eaf60f25d1d`
passed self-test, source check, and full isolated audit. The exact
Stage49 review census contained 26,332 original hard-physics events
plus 100 additional positive-RH-under-1%-only events, and **all
4,411** Stage60 selected independent ERA5 water-humidity patch
times coincide with the Stage49 hard set. Exact same-site/native
timestamp source join identifies **21,921 hard original events not
yet covered by Stage60**. Of those, **16,788** are US-Ho1 source
hard events, including **all 917** earlier Stage58 provisional-UTC
HOLD target records. **5,133** are spread over nine other sites:
BZS 86, CMW 42, EML 2,984, GLE 830, Ha1 23, Ho2 717,
Ho3 39, ICh 48, ICt 364. No forcing was changed.

New [Stage62 fast source-verified independent CDS ERA5 reuse,
bounded retrieval and original-TA/PA humidity correction script](scripts/stage62/62_reuse_or_fetch_CDS_ERA5_for_5133_nonHo1_hard_humidity.py)
continues the nine-site 5,133 exactly from Stage61, using only
checksum-pinned Stage50 t2m/d2m/sp CDS ERA5 receipt methodology.
It automatically reuses Stage15/18/Stage50 verified independent
ERA5 grid-years and explicitly reports missing grid-years and
missing original-release BIF metadata. With `--fetch`
it downloads a bounded subset of missing authenticated grid-years
into a new isolated Stage62 cache; with `--stage` it
creates separate candidate/hold rows where CDS is available and
original tower T vs ERA5 agrees to <=8 C. No guessing original
Ho1 UTC_OFFSET, no automatic changing of original tower T if
>8 C, no use of in-package companion *_ERA, and no source/DATM
writes. The distinct 102 positive original RH<1% cases remain a
separate scientific review, not compulsory ERA repair.

[Stage61 verified live stdout and Stage62 complete IRIDIS6
instructions](docs/stage61_PASS_stage62_5133_CDSEra_auto_reuse_fetch_20261024.md).
Stage62 committed but not yet run on IRIDIS6.


### Stage62 IRIDIS6 STAGING PASS; new automatic verified-CDS continuation for 22 missing grid-years (24 October 2026)

The original Stage62 exact-source audit and isolated staging **PASSED**,
producing `reports/stage62_nonHo1_5133_verified_CDS_stage_20261024T120055Z_3489543f`.
Of the 5,133 previously uncovered **non-Ho1** original VPD/RH hard
events: **2,911** have valid independent ERA5 water-humidity corrections
at original tower T/PA; **1,970** still need 22 independent CDS ERA5
grid-years; **166** have original tower vs ERA5 T2m discrepancy >8 C
and retain temperature science HOLD; **86 US-BZS** lack verified
same-release BIF UTC_OFFSET and stay provenance HOLD.
The 16,788 separate US-Ho1 original source hard cases remain held.
No original, Stage60, forcing or model files were touched.

An updated [Stage62 automatic batch completion script](scripts/stage62/62_reuse_or_fetch_CDS_ERA5_for_5133_nonHo1_hard_humidity.py)
has `--auto --max-new 8` to fetch all 22 missing exact
independent CDS grid-years in validated, resumable batches,
then automatically rebuild the full 5,133 event status ledger.
It preserves original EC TA/PA, never guesses station UTC_OFFSET,
never implicitly approves >8 C tower temperature deviations,
and never overwrites original inputs/NetCDF/DATM.
[Verified Stage62 output, precise BIF/T blockers and pinned one-shot
IRIDIS6 Stage62 --auto command](docs/stage62_operator_pass_next_auto_CDS_20261024.md).
Stage62 `--auto` published on GitHub but not yet
executed on IRIDIS6.


### Stage62 --auto interrupted by existing verified_receipt.json; checksum-safe resumable fix (24 October 2026)

The operator's Stage62 `--auto` run downloaded
and verified an initial batch of **8 CDS grid-years**, then verified
one 2013 grid-year. The following 2014 CDS request completed,
but creating
`.../ERA5_2014_lat+031.75_lon-0110.25/verified_receipt.json`
raised `FileExistsError` because the file already existed
before exclusive receipt creation. Its source/hash validity is
**unknown until independently verified**. No Stage62 automatic final
5,133-candidate restaging or forcing writes occurred in that
interrupted run. Previously verified grid-years can be reused.

A revised Stage62 Git blob
`4438a236ac8b0a9f4d8562ea0fae9612f979ffed`
(under commit `ad8919d90cbaf2f60b4ac6c11b7455b6c79deac9`)
adds a CDS-cache POSIX exclusive lock and validates existing
receipts or file-creation races using the SHA256-pinned source,
NETCDF t2m/d2m/sp and complete expected grid/year UTC calendar.
It **never deletes or overwrites** existing receipts or source
files; invalid/conflicting receipts remain a hard STOP.
Re-run `--auto --max-new 8` from the cache rather
than discarding previous CDS downloads.

[Interruption diagnostics, scientific boundaries and pinned
restart command](docs/stage62_operator_pass_next_auto_CDS_20261024.md).
The race-safe retry script has been committed, but it has not
yet run on the operator's cluster.


### Stage62 original CDS source SHA256 mismatch at US-CMW 2014, isolated immutable rescue (24 October 2026)

The resumed Stage62 preflight showed a concrete source
`CDS source SHA256 mismatch` for
`ERA5_2014_lat+031.75_lon-0110.25/original_CDS_payload`.
The existing verified receipt and payload must **not** be overwritten
or deleted. A new Stage62 Git blob
`0b68fa14a7e008bd7fb1b19153024e215f67c2bf`
adds an isolated recovery cache and a narrow SHA conflict-only gate:
it re-downloads just this grid/year under a different directory,
builds an independently verified receipt, reuses all other verified
Stage15/18/50/62 CDS grid-years and then continues `--auto`
towards the original 5,133-row candidate/hold census.
Any other CDS integrity mismatch still stops without changing source.
No EC original, previous stage, DATM, NetCDF forcing or model writes.
[Confirmed failure, recovery provenance and exact pinned IRIDIS6
restart command](docs/stage62_operator_pass_next_auto_CDS_20261024.md).
The new rescue path is published on GitHub but has not yet been
executed on IRIDIS6.


### Stage62 50/50 verified independent CDS grid-years PASS; Stage63 automated original-T evidence and BIF discovery (24 Oct 2026)

The operator ran Stage62 pinned Git blob
`0b68fa14a7e008bd7fb1b19153024e215f67c2bf` successfully.
All **50** original-BIF-verified independent CDS ERA5 grid-years
are SHA/calendar-verified, with **0** missing. The 5,133
Stage61 non-Ho1 hard anomalies are fully categorized in
`reports/stage62_nonHo1_5133_verified_CDS_stage_20261024T225848Z_db032320`:
**4,801** physically numeric ERA5 water-RH/VPD/QBOT candidates
with original EC T/PA, **246** EC T vs ERA5 discrepancies >8 C,
and **86 US-BZS** site original-BIF time-alignment HOLD.
Combined with Stage60's 4,411, **9,212** candidates are selected,
but none have been applied to model forcing.
All 16,788 original US-Ho1 hard source events, including its
917 previously checked provisional-UTC subset, remain separate.

New [Stage63 automated original EC temperature time-neighbor
and QC gate, 246 rows](scripts/stage63/63_automatic_246_temperature_neighbor_and_metadata_triage.py)
verifies original source file SHA256 and exact CSV native-time/row
identity, checks local temperature stationarity/neighbor QC, and
conservatively accepts only strongly supported extreme-cold
tower temperatures without imposing a blanket ERA5-temperature
overwrite. Uncertain cases remain documented HOLD. It also
searches original US-BZS / US-Ho1 source-adjacent ZIP archives
for BIF and only labels metadata as exact-release candidates
when ZIP's original source CSV SHA256 matches the Stage49
primary exactly. No original/model input writes.
[Stage62 final operator PASS and Stage63 pinned one-paste
IRIDIS6 procedure](docs/stage62_operator_PASS_and_stage63_246_auto_T_neighbour_20261024.md).
Stage63 is committed, not yet run on IRIDIS6.


### Stage63 IRIDIS6 full PASS; 177 automatic original cold-T acceptances and Stage64 full source accounting (24 October 2026)

The user ran pinned Stage63, which passed syntax, self-test,
source check and AUDIT. Report:
`reports/stage63_246_temperature_auto_neighbor_QC_20261024T231206Z_b5fac2db`.
Of the 246 original EC tower temperatures >8°C from independently
verified ERA5 T2m, the exact original-source neighboring-T and QA
audit **automatically accepted 177 cold records** and
held **69**: 48 at/above freezing outside the conservative cold-only
automatic policy, 12 native tower temporal jump/nonstationarity,
9 lacking verified neighboring QC. No original T or forcing was
changed. Stage63 searched source-adjacent US-BZS and US-Ho1 ZIP
directories and found no matching same-release BIF.

[Stage64 source-pinned automatic candidate merger](scripts/stage64/64_merge_9389_verified_ERA5_humidity_candidates.py)
now reconciles **4,411 Stage60 + 4,801 Stage62 + 177 Stage63 =
9,389** unique (site, original tower timestamp) independent CDS
ERA5 water-humidity candidate replacements, with original accepted
EC air T and PA retained. All exact source identities, Stage61
original **26,332** hard-physics RH/VPD records, SHA256 and water
VPD/QBOT formulas must match. The residual source holds are
**16,788 US-Ho1 original metadata/time**, **86 US-BZS original
BIF/time**, and **69 Stage63 tower T** (16,943 total).
The additional 100 unique positive RH<1% original review-only
events stay separate. This is an isolated science-ledger integration,
not approval to overwrite DATM or run models.
[Stage63 IRIDIS6 results and Stage64 pinned command](docs/stage63_PASS_stage64_9389_consolidated_source_hard_20261024.md).
Stage64 GitHub-published but not yet executed on IRIDIS6.

### Stage64 9389 independent water humidity candidate reconciliation PASS; Stage65 wider original BIF XLSX metadata search (25 Oct 2026)

Operator Stage64 IRIDIS6 syntax, self-test, source check and full audit passed. Report: reports/stage64_9389_unique_ERA5_humidity_candidates_20261024T232045Z_c8678d94. Exactly 26332 original source hard RH/VPD event identities accounted: 4411 Stage60 candidates, 4801 Stage62 candidates and 177 Stage63 original-cold-temperature-confirmed candidates; **9389** unique independent CDS ERA5 water-RH/VPD/QBOT proposals; remaining **16943** hard source HOLD (US-Ho1 16788 original time offset, US-BZS 86 original release BIF, 69 Stage63 T evidence). All original files, netCDF, DATM and model jobs remain unmodified and scientific model input approval remains false.

Critical metadata format correction: official AmeriFlux BADM BIF is often published as .xlsx (site naming convention AMF_SITE_BIF_YYYYMMDD.xlsx), while prior Stage63 searched principally for *BIF*.csv. The new [Stage65 bounded source-pinned BIF CSV/XLSX/ZIP discovery and 69-T-HOLD inventory](scripts/stage65/65_find_official_release_BIF_xlsx_and_triage_69.py) supports XLSX without added third-party dependencies and only labels site UTC_OFFSET as exact-release evidence when the identical original primary CSV (SHA256) and unique valid SITE_ID BIF are present in one archive. It never silently equates site longitude with archived UTC_OFFSET.

[Stage64 exact operator results and Stage65 verified GitHub run details](docs/stage64_PASS_stage65_BIF_xlsx_original_release_and_69T_20261025.md). Stage65 not yet executed on IRIDIS6.

### Stage65 PASS: 26 source/BIF candidates, zero exact source-release matches; Stage66 global FLUXNET BIF lookup (25 October 2026)

Operator Stage65 passed self-test, source check and audit. The report at `reports/stage65_metadata_xlsx_BIF_and_69T_triage_20261024T233546Z_05d7f38e` found **13 local file/archive candidates and 10 BIF candidates per site** (US-BZS and US-Ho1), but **0 same-original-archive SHA-confirmed release BIF**. Its 69 original temperature HOLDs are classified as 37 warm-context, 18 source-neighbor/QC, 14 possible sensor plateau/bound; the 9,389 Stage64 independent ERA5 water-humidity candidate rows are preserved.

Scientific metadata discovery improvement: FLUXNET2015 metadata are also distributed **globally** as `FLX_AA-Flx_BIF_HH_<YYYYMMDD>.xlsx` (and other resolutions), not necessarily inside individual `US-xxx` files. Site `UTC_OFFSET` may include `UTC_OFFSET_DATE_START` and multiple `GROUP_ID` cohorts. New [Stage66 global AA-Flx BIF / UTC_OFFSET date-history audit](scripts/stage66/66_find_global_FLX_AA_Flx_BIF_and_UTC_offset_history.py) scans bounded source and ZIP folders, decodes site-specific rows from global XLSX BIFs, preserves GROUP_ID history, checks exact original-primary SHA in candidate ZIP, and reports whether release provenance is actually verified. It does not guess the clock offset or approve DATM. US-Ho1 16,788 and US-BZS 86 original hard events still HOLD until verified.

[Stage65 actual PASS and Stage66 pinned IRIDIS6 procedure](docs/stage65_PASS_stage66_global_FLX_AA_Flx_BIF_history_20261025.md). Stage66 code committed but has not yet run on IRIDIS6.

### Stage66 global FLUXNET BIF search PASS but no source UTC evidence; Stage67 exact parser-vs-absence diagnostic (25 October 2026)

Stage66's Git-verified operator run passed check and audit, scanned **11 original-package roots / 64 candidate files**, but found **0** US-Ho1 or US-BZS UTC_OFFSET site records and **0** original same-archive source matches. Its isolated report is `reports/stage66_AA_Flx_global_BIF_UTC_history_20261025T054649Z_2a6cae25`. No original input, ERA5 NetCDF, DATM, model or Slurm changes. Stage64's **9,389** source-verified humidity candidates and 16,943 original hard HOLDs remain unchanged.

Source-provenance nuance: officially published AmeriFlux BADM/BIF can be **separate** from original flux ZIP and need not have identical ZIP packaging; however, the downloadable BIF must have verifiable publisher/release evidence and time applicability before authorizing local-to-UTC alignment. Current absence of a same-ZIP BIF is not proof an official one does not exist.

New [Stage67 forensic of all 64 Stage66 parsed BIF objects / errors plus optional official standalone BIF XLSX/CSV import](scripts/stage67/67_forensic_64_BIF_sources_and_official_import.py) pin-verifies original Stage66 manifest, disambiguates **no site rows vs BIF parser misses/errors**, and inspects any unchanged publisher-sourced metadata already staged in `~/AmeriFlux_Batch02_official_BIF`. It reports independent candidate offsets and their GROUP_ID/date periods without auto-approving UTC_OFFSET or overwriting forcing. [Stage66 live log and pinned Stage67 instructions](docs/stage66_PASS_stage67_forensic_official_BIF_20261025.md). Stage67 committed, not yet run on IRIDIS6.

### Stage67 IRIDIS6 audit PASS — source BIF gap confirmed, official BADM acquisition needed (25 October 2026)

Operator Stage67 source-pinned audit passed; isolated report `reports/stage67_BIF_actual_source_forensic_and_official_staging_20261025T064106Z_91002c73`. It examined **64** candidate data archives/files, decoded **254,579 BIF rows** across **37** files, and found **no `SITE_ID` rows for US-Ho1 or US-BZS**. Four reported parse-limit errors were the stations' large FLUXNET FULLSET / ERA5 companion CSVs, not BIF metadata files. The local official BIF download/import folder is absent. This is now a metadata-access/source-provenance dependency, not a general parser issue. Stop re-running unchanged local BIF directory scans.

Official AmeriFlux publishes BADM/BIF separately, including site BIF XLSX or network `AMF_AA-Flx_BIF_*` and BASE-BADM ZIP. Access requires an account and applicable data use terms. The source release references are **US-Ho1 FLUXNET-1F 3-6 (1996–2023)** DOI `10.17190/AMF/2469453` and **US-BZS FLUXNET-1F 5-7 (2010–2024)** DOI `10.17190/AMF/1881572`. On obtaining publisher-proven official BIF, place its original XLSX/CSV/ZIP in `~/AmeriFlux_Batch02_official_BIF` and rerun Stage67 `--official-dir` to inspect group/date-specific UTC_OFFSET. This never by itself approves an offset without applicable timestamp/source provenance.

[Stage67 operator findings, official download paths, and targeted next dependency](docs/stage67_PASS_official_BIF_access_required_20261025.md). The Stage64 9,389 independent water-humidity candidates and 16,943 source HOLDs remain unchanged. No DATM forcing/model input changed.

### User-supplied official AmeriFlux BIF XLSX: US-Ho1 -5, US-BZS -9; Stage68 read-only original clock audit (25 October 2026)

Two original site-specific official BIF XLSX uploads were parsed directly in the conversation (not inferred from clocks/geography). Ho1 `AMF_US-Ho1_BIF_20260527.xlsx` SHA256 `24fd0a35cf5f39e49cb70fa63af6fb962cfc1bd71652aec51bd29843593ba6f1`, **426 rows**, `UTC_OFFSET=-5`, GROUP_ID 11463, location 45.2040 -68.7402, BASE DOI 10.17190/AMF/1246061. BZS `AMF_US-BZS_BIF_20260715.xlsx` SHA256 `9f7c46d81528505ef1586600fb68fb67fb87f88dc61cbbf04e8d0e4c17b48fac`, **62 rows**, `UTC_OFFSET=-9`, GROUP_ID 87183, location 64.6963 -148.3235; comment explicitly calls this Alaska Standard Time; BASE DOI 10.17190/AMF/1756434. Neither uploaded BIF contains `UTC_OFFSET_DATE_START` or multiple offset groups. The BIF publication/BASE version must not be misinterpreted as the corresponding historical FLUXNET source release version or full-period time applicability.

[Two-site source-derived BIF evidence JSON with exact XLSX SHA256](data/official_BIF_20261025/official_two_site_BIF_time_evidence.json) now committed to GitHub. **Original XLSX binary objects were supplied as conversation attachments, not committed to this repository; the JSON is extracted, attributed evidence.**

[Stage68 source-pinned 16,874 Ho1/BZS original-hard-event local-to-UTC SHADOW audit](scripts/stage68/68_original_BIF_Ho1_BZS_UTC_clock_history_shadow.py) and [operator procedure/source science caveats](docs/stage67_to_stage68_uploaded_official_BIF_20261025.md) are available. Stage68 does not overwrite or release 16,788 Ho1 and 86 BZS time HOLDs until full historical clock provenance and independent ERA5 coverage/physical QA are verified. Original EC CSV, Stage64 9,389 previously selected humidity candidates, DATM NetCDF, CIME, model and Slurm jobs are unchanged.

### Stage68 BIF nominal clock shadow AUDIT PASS; Stage69 Ho1/BZS original VPD saturation mechanism (25 October 2026)

Operator Stage68 ran successfully on IRIDIS6, isolated report `reports/stage68_official_uploaded_BIF_Ho1_BZS_UTC_shadow_20261025T075428Z_11c5b183`. Published site BIF values **US-Ho1 UTC_OFFSET −5** and **US-BZS UTC_OFFSET −9** were used only for a source-pinned, bijective **provisional** UTC crosswalk of **16,788 Ho1 + 86 BZS = 16,874** original hard humidity event timestamps. Historical offset applicability and independent ERA5 validation are not yet certified; the original XLSX SHA256 bytes were checked against the conversation-uploaded source artifacts, *not revalidated on IRIDIS6 in Stage68*.

Source science finding: ALL Ho1 16,788 and BZS 86 original hard events have `ACTUAL_VAPOR_NONPOSITIVE` and `RH_INFERRED_LT0`; Ho1 15,792 and BZS 84 retain original TA QC0. The Stage48 calculation is `e_actual=es_water(T_original)-VPD_original`. An impossible negative inferred RH is not a direct negative RH sensor observation and does not by itself indicate temperature should be replaced. It may reflect suspect VPD source, T source, data lineage or scale/units.

New [Stage69 original VPD/es_water QC, year/episode, units diagnostic](scripts/stage69/69_original_Ho1_BZS_vpd_saturation_failure_diagnosis.py) requires exact Stage68/64 SHA-pinned source ledgers, independently recalculates VPD/es(T), original T/VPD QC combinations, year distributions, consecutive native HH episodes and **unapproved** VPD /10, /100 scale hypotheses. This stage DOES NOT authorize units correction, historical time-offset release, independent CDS ERA5 claims, or DATM/model writes. [Stage68 operator PASS and one-paste Stage69 run](docs/stage68_PASS_stage69_16874_original_vpd_source_physics_20261025.md). Stage69 published on GitHub but not yet run on IRIDIS6.

### Stage69 original VPD mechanics audit: pandas `.flags` bug fixed (25 October 2026)

Operator Stage69 original Git blob `5edf6ca49a1bba1c6292b80322d7e306e1b08549` passed self-test but failed during source check: `AttributeError: 'Flags' object has no attribute 'astype'`. Cause: `a.flags` resolved the pandas DataFrame `.flags` property rather than the original Stage49/68 CSV column named `flags`. The [fixed Stage69 script](scripts/stage69/69_original_Ho1_BZS_vpd_saturation_failure_diagnosis.py) uses explicit `a["flags"]` and includes a regression self-test; pinned fixed blob `a5c678d57b8691a7bd6b37c8241711b828054223`. [One-paste IRIDIS6 recovery procedure](docs/stage69_pandas_flags_source_column_fix_20261025.md). Stage64/68 outputs remain unchanged; Stage69 `--check`/`--audit` still need operator verification.

### Stage69 original Ho1/BZS VPD saturation mechanism PASS; source QC2=downscaled ERA, Stage70 original-product lineage next (25 October 2026)

Operator Stage69 pinned fixed code passed syntax, self-test, full source `--check` and isolated `--audit` on IRIDIS6. Report: `reports/stage69_16874_original_VPD_vs_water_es_source_diagnosis_20261025T080834Z_782347f2`. All **16,788 US-Ho1 + 86 US-BZS** original hard humidity events have `VPD_F > es_water(TA_F)`, hence `e_actual = es_water - VPD_F <=0` and derived RH<0. This is a **processed VPD/TA consistency failure**, not measured negative RH. All events have **VPD_F_QC=1 or 2; ZERO QC0**. US-Ho1: VPD QC2 16,738, QC1 50; US-BZS: QC2 68, QC1 18. **Total 16,806/16,874 (99.60%)** are FLUXNET `VPD_F_QC=2`, officially meaning ERA-downscaled source values, not direct observations. `VPD_F_QC=1` is high-quality MDS gapfill. TA_F QC0 is 15,792 Ho1 + 84 BZS. Stage69's `/10`/`/100` numerical sensitivity is NOT unit error proof and is not an approved fix. Some Ho1 winter runs exceed 100 h consecutively.

Primary source definition: https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/ . The `VPD_ERA` column in the historical FULLSET is a product of prior ERA-driven FLUXNET processing, **NOT independent modern CDS ERA5**, so copying it cannot provide independent repair evidence.

[Stage70 exact site original PRIMARY source VPD_F vs VPD_ERA/VPD_F_MDS and TA_ERA lineage inspection](scripts/stage70/70_original_Ho1_BZS_VPD_F_ERA_MDS_source_lineage.py) uses Stage69 source event IDs and pinned Stage49 original-site file SHA; audits the exact original physical CSV row, timestamp, T, VPD, QC, compares VPD source to the appropriate ERA/MDS column, and evaluates VPD physical consistency against source paired TA_ERA. [Stage69 actual PASS and Stage70 pinned command](docs/stage69_PASS_stage70_original_VPD_ERA_MDS_source_forensics_20261025.md). This is READ ONLY. Stage70 has been committed, but not yet run on IRIDIS6. Stage64 9,389 earlier candidate patches and 16,874 Ho1/BZS original source HOLDs remain immutable; no DATM forcing approval.

### Stage70 original VPD_F source/QC exact-row provenance PASS; Stage71 independent CDS existing-gridyear inventory and provisional physics (25 Oct 2026)

Operator Stage70 self-test/source check/audit PASS. Report: `reports/stage70_Ho1_BZS_original_VPD_product_lineage_20261025T082409Z_59c37277`. All **16,874** original US-Ho1 (16,788) and US-BZS (86) nonphysical VPD_F records match the expected `VPD_ERA` (QC2=downscaled ERA) or `VPD_F_MDS` (QC1=MDS gapfill) value **exactly**, with zero original unmatched companion source rows and SHA-verified original FLUXNET source file/row/time identity. Source QC2 US-Ho1 16,738, US-BZS 68; source QC1 US-Ho1 50, US-BZS 18. **15,679/16,738 Ho1 QC2** and **68/68 BZS QC2** become physically possible when evaluated using processed `TA_ERA` in place of original `TA_F`. However **1,059 Ho1 QC2** remain inconsistent even with original-source paired `TA_ERA` (and 3 Ho1 QC1, 5 BZS QC1 remain invalid with `TA_ERA`). This rules out explaining every anomaly as a simple TA_F/TA_ERA mismatch. `VPD_ERA` embedded in FULLSET is NOT independent CDS ERA5. No source units fix or temperature replacement is approved.

New [Stage71 existing independently SHA+UTC/calendar verified CDS ERA5 receipt reuse, gridyear census and RH/VPD/QBOT source-TA shadow](scripts/stage71/71_reuse_independent_CDS_Ho1_BZS_16874_shadow.py) reuses Stage15/18/50/62 verified external CDS sources where available (Ho1 grid 45.25/−68.75, BZS 64.75/−148.25) and emits explicit missing-receipt and T/physics HOLD counts otherwise. **No download, no unproven historical UTC offset approval, no forcing edits**; the original Stage64 9,389 candidates remain untouched. [Stage70 verified science findings and pinned Stage71 IRIDIS6 instructions](docs/stage70_PASS_stage71_independent_CDS_coverage_shadow_20261025.md). Stage71 committed and static-checked, not yet tested on IRIDIS6.

### Stage71 actual independent CDS receipt SHADOW PASS (16/26), Stage72 exact ten-gridyear isolated recovery (25 October 2026)

Operator Stage71 pinned blob `b1ce47dedf3da4c931cac3b8a6d4822090870a81` passed self-test, full source `--check` and isolated `--audit`. Original Stage71 source report: `reports/stage71_Ho1_BZS_independent_CDS_verified_reuse_shadow_20261025T083319Z_8aef8c86` (actual absolute `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/...`). Exactly 16/26 target site grid-years have source/payload/NetCDF SHA256, grid/unit and buffered UTC calendar verification. In the 16,874 original Ho1/BZS hard-physics records: **7,695** have physical numeric RH/VPD/QBOT shadow candidates retaining original T/PA but historical BIF timestamp applicability remains HOLD; **8,115** are in ten grid-years without valid independent CDS receipt; **987** have nonzero original T QC and **77** original T differ >8°C from verified ERA5. All original 16,874 remain HOLD, Stage64 earlier 9,389 candidates unchanged; no model or forcing writes.

The ten grid-year missing cohorts, in descending impacted original-hard-event count: Ho1 2015 2,268; 2013 1,474; 2011 1,366; 2000 1,069; 2008 1,036; 2016 762; BZS 2012 79; Ho1 2021 46; Ho1 2023 8; BZS 2011 7. Several are **rejected old CDS receipts**, not wholly missing files (the Stage71 logs show 1–2 verification issues), so do not overwrite any existing payload or receipt.

New [Stage72 pinned 10-grid-year independent CDS ERA5 recovery and complete read-only time/physics shadow](scripts/stage72/72_rescue_missing_10_Ho1_BZS_independent_CDS_gridyears.py): `--plan` read-only classification, `--fetch --max-new 2` append-only downloads into a NEW isolated Stage72 cache (highest impact first, exclusive writer lock, receipt SHA256 and calendar proof), and `--audit` recompute whole 16,874 from pinned Stage71 logic with Stage72 cache prepended. [Full Stage71 audited science/status and pinned Stage72 IRIDIS6 procedure](docs/stage71_PASS_stage72_restore_missing_10_CDS_gridyears_20261025.md). Stage72 has been committed and code structurally checked; not yet run on IRIDIS6. Historical BIF clock and DATM forcing approval remain FALSE.

### Stage72 two independent CDS recoveries PASS; Stage73 same-grid cross-site immutable receipt source-bridge first (25 October 2026)

Operator Stage72 passed original SHA, self-test, 10-grid-year plan, two successful independent CDS fetches and complete source-verified audit. New **US-Ho1 2015 and 2013** CDS receipts were created under **new isolated Stage72 cache**, NetCDF SHA256 `a2a69b2fc309e8d4f7f8ab0e501ea0dd17123f89dd148fbd9d475559ad9a0d0c` and `c2905055a1b69bed4a7f5c41aed6b940cbb799620c17b6a85bfa07960a4ca2e9`; all old originals preserved. Stage72 report `reports/stage72_16874_original_independent_CDS_recovery_shadow_20261025T084352Z_01da7b3d`: **18/26 independent CDS grid-years verified**, **11,432/16,874 numeric-only original source RH/VPD/QBOT shadow candidates**, **4,373 missing independent-year records**, **987 TA QC nonzero**, **82 native T versus external ERA5 T >8 °C**; all original Ho1/BZS hard events remain HOLD and no model forcing edits.

**Important correction to prior Stage72 download rationale:** all six original-old CDS rejections for Ho1 2015, 2013, 2011, 2016, 2021 and 2023 reported **only** `Stage50 receipt site membership mismatch`, not an observed source SHA/NetCDF corruption. Stage50 metadata restricts old receipts to original requesting site, although other towers may occupy the exact same ERA5 quarter-degree grid. Do not redownload the remaining four Ho1 2011/2016/2021/2023 without verifying cross-site source provenance first.

New [Stage73 independently source-checksummed same-grid-year original CDS receipt bridge](scripts/stage73/73_same_grid_cross_site_original_CDS_receipts.py) uses pinned Stage50/71/72 QA. It revalidates the original CDS receipt against its **original recorded site membership**, exact gridyear, original request 0.25° grid, immutable payload/netcdf SHA, full UTC hourly buffered calendar and file units. Only a passing, nonconflicting source gets a NEW scoped Ho1 bridge receipt pointing to unchanged old NetCDF and original receipt SHA. [Stage72 PASS, membership correction and pinned Stage73 command](docs/stage72_PASS_stage73_original_CDS_same_grid_bridge_20261025.md). Four candidate same-grid years cover **2,182** anomalous source events. The other four Ho1 2000/2008 and BZS 2011/2012 have **2,191** records and no verified receipts in audited cache roots, so they are the next genuine download candidates. Stage73 published, not yet executed on IRIDIS6. No previously selected 9,389 Stage64 numerical candidates or forcing modified.

### Stage73 cross-site same ERA5 grid receipt bridges PASS; Stage74 four truly missing independent CDS gridyears (25 October 2026)

Stage73 operator run verified 4 original US-Ho1 external CDS receipts originally downloaded for US-Ho2/US-Ho3, for exact identical quarter-degree gridyears 2011 (1366 source hard), 2016 (762), 2021 (46), 2023 (8), by original receipt SHA, payload SHA256, NetCDF SHA256, source request lat/lon, full buffered UTC year, units and grid integrity. All old source receipts/CDS files remain unchanged; new create-only bridge receipts preserve original source path, SHA and original source members. Report: `reports/stage73_exact_grid_cross_site_verified_CDS_shadow_20261025T085440Z_4ca0e311`.

Updated full **16,874 original Ho1/BZS hard-event** independent CDS shadow: **13,606 numerical water-RH/VPD/QBOT source candidates**, **2,191 in 4 still absent CDS gridyears**, **995 original TA QC nonzero**, **82 tower TA vs external ERA5 >8 C**. Verified independent CDS gridyear coverage is **22/26**; all original hard source time/physics HOLDs remain in force (2026 official BIFs do not certify every historical UTC offset interval). Previous Stage64 9,389 independent numeric candidate rows remain untouched. No DATM forcing/model changes.

Now recover **only four genuinely missing independent CDS gridyears:** Ho1 2000 (1069), Ho1 2008 (1036), BZS 2012 (79), BZS 2011 (7) — 2,191 source events. [Stage74 pinned four-year isolated CDS fetch+scientific shadow](scripts/stage74/74_fetch_four_truly_missing_Ho1_BZS_CDS_gridyears.py) gates SHA-pinned Stage73 source evidence, keeps Stage73 bridges and all older CDN files immutable, and creates new verified CDS year receipts via the original Stage72 exclusive-lock create-only workflow. `--plan` read-only, `--fetch --max-new 4` true independent CDS only, `--audit` checks full 16,874 against SHA-pinned original source with refreshed coverage; no original forcing, DATM/CIME, or Slurm changes. [Stage73 PASS / Stage74 operator instructions](docs/stage73_PASS_stage74_four_missing_independent_CDS_20261025.md). Stage74 is committed/structurally verified but not yet run on IRIDIS6.

### Stage74 all independent CDS gridyears complete 26/26; Stage75 1675 original tower-T quality and context holds (25 October 2026)

Operator Stage74 pinned script self-test, read-only plan, four independent CDS fetches and final SHA+UTC calendar/physics audit PASS. The last source years are Ho1 2000 and 2008, BZS 2012 and 2011. New source files/receipts were written only in the separate Stage72 CDS rescue cache, with no previous source or formal model-input replacement. Stage74 final report `reports/stage74_four_missing_years_16874_Ho1_BZS_CDS_SHADOW_20261025T090751Z_d0953fbc` verifies **26 / 26** independent CDS ERA5 source-relevant gridyears. Exactly **zero** of 16,874 original Ho1+BZS hard humidity events remain blocked by absent external CDS.

After retrieving the last four CDS source-years: **15,199** numerical-only water humidity candidate events retaining original tower T/PA but with historical BIF clock and forcing science HOLD; **998** original native tower TA_F QC nonzero; **677** native QC0 TA_F with abs(tower T minus independent ERA5 t2m)>8°C. These are exhaustive, mutually exclusive (15199+998+677=16874). Relative to Stage73, 595 of the newly covered observations fall into >8°C T difference and 3 into original T QC hold; do not mistake new diagnostics for source files being corrupted. Earlier Stage64 9,389 numeric humidity candidates from the rest of Batch02 are unchanged. **NONE** are yet applied to formal forcing.

New [Stage75 source-immutable 1,675 native tower-temperature science-HOLD triage](scripts/stage75/75_full_26_gridyear_original_temperature_hold_science_triage.py) reads the SHA-pinned Stage74 source data, checks exact original event/clock status, and compares native FLUXNET TA_F/QA, FLUXNET processed TA_ERA, independently validated CDS ERA5 T2M, source VPD QC and annual/contiguous source-HOLD episodes. Treat reanalysis sources as contextual, not tower ground truth; **no blanket ERA5-T replacement**. [Stage74 verified 26/26 evidence, Stage75 executable pinned IRIDIS6 instructions](docs/stage74_PASS_stage75_remaining_1675_original_T_source_triage_20261025.md). Official FLUXNET original temporal convention is local standard (no DST) but 2026 site BADM lacks historical dated offset evidence, so time-source approvals remain FALSE; no DATM, NETCDF forcing, CIME, Slurm or model changes. Stage75 GitHub-committed; not yet run on IRIDIS6.

### Stage75 operator scientific audit PASS; Stage76 original Ho2/Ho3 measured-T independent-tower context (25 October 2026)

Stage75 actual IRIDIS6 `--self-test`, original SHA-pinned `--check` and final isolated `--audit` PASS. Original read-only source report `reports/stage75_1675_original_TA_QC_and_T_vs_CDS_science_triage_20261025T091912Z_27b0e442`; full 26/26 independently verified CDS ERA5 gridyears, 16,874 exact original Ho1/BZS nonphysical VPD source cases: **15,199 numeric-only independent RH/VPD/QBOT humidity shadows**, **998 original air temperature QC1/QC2 holds**, **677 measured QC0 tower T versus independent ERA5 T >8°C holds**. Original T_QC holds split Ho1 QC1=167, QC2=829, BZS QC1=2; native measured QC0 >8°C split Ho1=623, BZS=54. Stage75 found 505 of the QC0 T-difference cases in Ho1 year 2000, some continuous >30 hours and measured T ~13°C colder than CDS in those episodes. Do not automatically overwrite measured T or assume ERA5 T is local ground truth; neither original FLUXNET TA_ERA nor CDS ERA5 can independently corroborate the other's reanalysis ancestry.

New [Stage76 exact original US-Ho2/US-Ho3 QC0 tower T native-source evidence comparison](scripts/stage76/76_Ho1_Ho2_Ho3_original_QC0_temperature_cross_tower_audit.py): source-SHA-verifies original FLUXNET HH tower primary files from Stage49 inventory and the full Stage75 report, matches exact native Ho1 original local timestamps only, compares **genuinely measured QC0** Ho2/Ho3 air temperature (where available) to Ho1 and independent CDS ERA5 T with exploratory ±3°C categories. Neither Ho2/Ho3 tower metadata, time standard history, sensor heights, canopy microclimate nor support for BZS are assumed; BZS 56 T-HOLDs remain separate. A same-clock neighbor source is diagnostic, not scientifically-approved temperature/forcing replacement. [Stage75 validated data findings, Stage76 pinned operator command](docs/stage75_PASS_stage76_Ho1_neighbor_measured_T_QC0_20261025.md). Original Stage64 9,389 numeric candidates and all 16,874 source/clock HOLDs remain unchanged, no NETCDF/DATM/CIME/Slurm writes. Stage76 code published and statically structure-checked, not yet run on IRIDIS6.

### Stage76 exact original Ho2/Ho3 measured QC0 corroboration PASS; Stage77 NOAA Bangor ground-station audit of 505 Ho1-2000 gaps (25 Oct 2026)

Operator Stage76 pinned Git SHA, self-test, read-only original SHA/clock/primary-source `--check` and isolated `--audit` all PASS. Stage76 report `reports/stage76_1675_Ho1_BZS_original_cross_tower_QC0_context_20261025T092852Z_ceabe542`: among 1619 US-Ho1 original T science HOLDs, native Ho2 exact source T matches 1320 timestamps but only 327 valid original QC0; native Ho3 410 exact timestamps but 408 QC0. For the **623 Ho1 native measured QC0** source T-vs-CDS >8°C HOLDs, **580 have no original Ho2/Ho3 QC0 comparator**, **42 QC0 neighbor observations support original Ho1 T**, **1 matches neither**, **zero solely support CDS ERA5 T**. Critically, all **505 QC0 discrepancies from Ho1 year 2000 lack an independently QC0 measured Ho2/Ho3 same-timestamp comparison**. For **996 Ho1 originally non-QC0 temperatures**, 605 no QC0 neighbor, 256 QC0 neighbor nearer to CDS temperature, 15 nearer Ho1 original temperature, 104 conflicting source neighbor support, 16 match neither. US-BZS 56 T science HOLDs remain without geographically relevant local tower comparisons. Matching nominal local timestamps, nearby sensor heights and 2026 BIF effective historical offset are unverified and ALL source temperature HOLDs continue.

Previously available independent NOAA GHCNh Bangor (USW00014606, airport ~46km from Ho1) source-QC inspection Stage39/40 only included 1998, 1999 and 2001, not year 2000. New [Stage77 original NOAA Bangor 2000 QC source measured-T audit](scripts/stage77/77_Ho1_2000_QC0_NOAA_Bangor_source_temperature_probe.py) pins Stage76 report output SHA and Stage40 original source-code/QC parser Git blob; `--check` is offline/read-only, `--audit` fetches only the as-yet-unverified NOAA 2000 file over restricted NOAA HTTPS, archives raw original station bytes and SHA256 in a **NEW isolated report**, quality-/station-origin-screens hourly reports, joins each of the exact 505 Ho1 nominal BIF UTC−5 source hours within ±30min, and reports **distinct station observations** separately from paired half-hours so dependent observations are not overstated. Airport data are not Ho1 canopy ground truth and do not authorize a temperature/UTC/forcing patch. [Stage76 verified outputs, Stage77 pinned IRIDIS6 download+audit command](docs/stage76_PASS_stage77_Ho1_2000_NOAA_temperature_evidence_20261025.md). Stage77 code is GitHub-committed and structural checked, not yet run against NOAA on IRIDIS6.

### Stage77 NOAA Bangor 2000 original ground-source temperature comparison PASS; Stage78 native Ho1 QC0 controls and UTC sensitivity next (25 October 2026)

Operator Stage77 pinned original source self-test, Stage76 raw source `--check`, first-source NOAA HTTPS archive and full `--audit` PASS. Original raw NOAA GHCNh station `USW00014606` Bangor year-2000 PSV source is **10,119,935 bytes, SHA256 `2d5756c1de9faa1bf4e59cddc24ab39556ae167d602d80859786309601bb3620`** saved under `reports/stage77_Ho1_2000_505_QC0_NOAA_Bangor_external_T_context_20261025T094314Z_fa509a05`. Source year original 11,403 rows; 11,355 plausible T and 11,329 passing the Stage40 site/source quality-code whitelist. Of **505 Ho1 year-2000 original TA_F_QC0** anomalies with |Ho1−CDS ERA5|>8°C, **498** paired to source-QC-filtered independent-airport observation within ±30 min; these 498 half-hours correspond to only **306 distinct NOAA station reports** (not 498 independent measurements). **NOAA airport–original Ho1 MAE 14.322°C versus NOAA airport–CDS ERA5 MAE 1.516°C**, 490 paired HH NOAA more similar to CDS by >1°C, 6 closer to Ho1, 2 within 1°C; 4 no numeric source within 30min and 3 equidistant discordant reports excluded.

This is strong evidence for investigating the Ho1 **year-2000** measured-QC0 temperature source/time and instrument calibration, **not an approved automatic ERA5 temperature replacement**. Bangor airport ~46 km away cannot represent forest canopy local temperature without testing; hourly NOAA reuse and serial correlation matter, and near-site assimilation could make airport observations and ERA5 not statistically independent. User-supplied 2026 BIF Ho1 nominal UTC_OFFSET −5 remains historical applicability HOLD.

New [Stage78 SHA-pinned archived NOAA 2000 vs exact Ho1 505 QC0, same-month original measured QC0 non-hard-VPD controls and trial UTC offsets](scripts/stage78/78_Ho1_2000_NOAA_QC0_control_and_clock_sensitivity.py) uses the saved Stage77 NOAA original source bytes (no repeated NOAA download), the exact byte-pinned original Stage49 source Ho1 FULLSET primary and Stage74 list of 1,069 year-2000 hard-VPD rows; independent station-source matches use original Stage40 QC/tie logic. Trial UTC−7/−6/−5/−4/−3 is compared on common Ho1 native-event time support to distinguish potential clock shifts from a sustained original temperature bias; **never** compare fixed-UTC CDS temperature at alternative shifts or claim historical offset approval. The audit reports both paired HH and equal-distinct-NOAA-report summaries, with all source/HOLD flags retained. [Stage77 actual operator evidence, raw NOAA source SHA and pinned Stage78 IRIDIS6 commands](docs/stage77_PASS_stage78_Ho1_2000_NOAA_native_QC0_controls_clock_sensitivity_20261025.md). Stage78 code GitHub-committed and structurally checked, not yet run on IRIDIS6; no original FLUXNET, NOAA, CDS, netCDF forcing, DATM, CIME or Slurm changes. Stage74 15,199 numeric-only humidity candidates and Stage64 prior 9,389 candidate rows remain unchanged.

### Stage78 original Ho1 2000 QC0 source controls and clock sensitivity PASS; Stage79 monthly/hourly and source-episode diagnosis (25 Oct 2026)

Operator Stage78 pinned blob `002b6fb491b1d9dd6e570feed31a3c041f0aae2a` verified and full self-test, SHA read-only check, isolated audit PASS. Input source report: `reports/stage78_Ho1_2000_measured_QC0_NOAA_controls_clock_sensitivity_20261025T180347Z_0a9449e9`, reuses unchanged Stage77 raw NOAA Bangor 2000 PSV (`2d5756c1de9faa1bf4e59cddc24ab39556ae167d602d80859786309601bb3620`). The original FLUXNET Ho1 year-2000 population contains 17,568 30min HH source rows, with **505 measured TA_F_QC0** events held because Ho1–independent CDS ERA5 T >8°C, and **6,006 same-month original QC0 non-hard-VPD controls** across Jan/Feb/Mar/Nov/Dec. At nominal UTC−5, Ho1 505 event NOAA source QC matches: 498 HH, **306 distinct station reports**, equal-report MAE **14.346°C**, median NOAA−Ho1 **+13.655°C**. Controls: 5,945 matched HH, **3,605 unique NOAA reports**, equal-report MAE **6.698°C**, median NOAA−Ho1 **−1.715°C**. Controls also exhibit substantial airport-versus-forest variance and are not ground truth.

Strict same **483 Ho1 source timestamps** matched at all tested nominal/sensitivity offsets −7/−6/−5/−4/−3 yield NOAA-report-equal MAE **14.703/14.532/14.336/14.077/13.855°C** respectively, with median NOAA−Ho1 **+14.04/+13.90/+13.64/+13.41/+13.28°C**. The UTC−5 to UTC−3 trial improvement is only **0.481°C**, nowhere near explaining the ~14°C residual. Importantly this **does not approve a different historical UTC clock**; alternative NOAA timestamps must NOT be compared against fixed-UTC independent CDS temperatures. The selected event/control distribution does not alone identify a sensor error or justify replacing measured QC0 Ho1 with ERA5.

New [Stage79 original measured-source Ho1 2000 month × three-hour, source 30min episode and ±7 day/±1 local-clock hour non-hard-QC0 control diagnostics](scripts/stage79/79_Ho1_2000_NOAA_season_hour_episode_matched_control_triage.py) is a source-HOLD-preserving **offline read-only** audit of Stage78's original 32,555 five-offset rows with output SHA verification. It generates isolated per-month/hour counts, unique-NOAA-report-weighted differences, native source episode lengths, and exploratory nearby control differences, without source/download/network activity or forcing changes. [Stage78 actual operator PASS, evidence limitations and pinned Stage79 IRIDIS6 command](docs/stage78_PASS_stage79_Ho1_2000_season_hour_episode_QC0_controls_20261025.md). Stage79 script committed and statically checked, not yet executed on IRIDIS6. Original 16,874 Ho1/BZS source humidity anomalies, **15,199 humidity numeric shadows**, **1,675 temperature-review HOLDs** and other Stage64 **9,389** candidates remain SCIENCE HOLD with **zero formal NETCDF/DATM/CIME changes**.

### Stage79 Ho1-2000 original QC0 seasonal/diurnal/36 native cold-episode science audit PASS; Stage80 corrected source transition windows (25 Oct 2026)

User-provided operator Stage79 pinned blob `6c5de3a74de5a1b587648e0fa594369cfb461a1f` self-test/source SHA check and independent offline isolated `--audit` PASS. Original report `reports/stage79_Ho1_2000_505_QC0_source_month_hour_episode_control_triage_20261025T181238Z_2b6cbd1f` identifies **505 measured native TA_F_QC0** original year-2000 Ho1 temperature discrepancies into **36 continuous 30min episodes** (Stage79 stdout printed only 35 longest; 504 HH shown + 1 additional singleton = 505 HH); month counts **Jan 300, Feb 73, Mar 115, Nov 8, Dec 9** (488/505 Jan–Mar). All **505** have at least one original QC0 same-month, same-local-time ±1h, ±7d non-hard-VPD comparison, but original NOAA source-QC actual matches remain **498/505**. Event minus local control signed NOAA−Ho1 difference in the 498 NOAA-matched records has median **+13.894°C**, IQR **+10.241 to +17.906°C**. Jan early-night 00–06: event vs same-month/hour-bin signed medians differ by ~25.8–26.0°C; original source QC0 without physical tower verification is not calibration proof.

Among the longest source episodes: **70 HH (35h)** 2000-03-06 04:00→03-07 14:30 (median NOAA−Ho1 +12.835°C); **48 HH (24h)** 2000-02-22 11:30→23 11:00 (+11.680°C); **44 HH (22h)** 2000-01-01 15:30→02 13:00 (+18.825°C); **43 HH (21.5h)** 2000-01-02 17:00→03 14:00 (+21.270°C). Source-selection effects, airport-versus-canopy spatial difference and uncertain historical BIF UTC offset still preclude any approved T replacement. The previous Stage78 ±2h clock test did **not** eliminate the ~14°C NOAA-airport versus source Ho1 temperature discrepancy.

New [Stage80 SHA-pinned original Ho1 2000 native QC0 36-episode +/-6h source edge check](scripts/stage80/80_Ho1_2000_original_T_QC0_episode_boundary_and_NOAA_transition_audit.py) uses immutable Stage79 report/checksums, original Stage78 source retrieval logic, verified byte-identical primary native FLUXNET 2000 HH `TA_F`/`TA_F_QC`, `VPD_F`/`VPD_F_QC` and optional native `TA_ERA`, and the original archived SHA-verified 2000 NOAA GHCNh station file. It outputs per-HH full original source context ±6h around **all 36 episodes**, and 2h-before/start/end/after source T and NOAA−Ho1 comparisons and original 30-minute temperature jumps. All flags are diagnostic only; timestamps/source T are not modified. [Stage79 operator PASS, episode table, Stage80 pinned IRIDIS6 command](docs/stage79_PASS_stage80_Ho1_2000_35_QC0_episode_boundaries_20261025.md). Original Stage80 **failed** operator --check because it mistook Stage79 printed `head(35)` for full CSV (actually **36** rows, 505 HH). Corrected Stage80 source Git commit `e1c7e53c777ee457ed722691fb0b1a0e43819d69`, blob `945ca08b393d15fd8f710619d60a001dd9a1e9ad`. Original SHA-proven Stage79 output unchanged, Stage80 correction not yet tested on IRIDIS6. Full original humidity 16,874 source HOLDs, 15,199 numeric humidity shadows, 1,675 temp review HOLDs and other 9,389 Stage64 numeric candidates remain immutable. No original FLUXNET/NOAA/CDS or NetCDF/DATM/CIME/Slurm modifications.

### Stage80 operator PASS 36/36 selected original Ho1 QC0 source episodes; Stage81 full-year NOAA temperature residuals independent of VPD selection (25 Oct 2026)

Stage80 corrected Git blob `945ca08b393d15fd8f710619d60a001dd9a1e9ad` passed IRIDIS6 self-test, SHA-verified Stage79→Stage49 and archived NOAA source `--check`, and isolated **`AUDIT PASS`**, report `reports/stage80_Ho1_2000_505_QC0_episode_boundary_original_NOAA_20261025T184904Z_7a1491db`. Minor stale `--check` print says `35 episodes` but source report and audit confirm **36 full native source episodes**, original **505 native TA_F QC0** half-hours, all source/NOAA data unchanged. The Stage79 console showed only `head(35)` episodes; the 36th was a 1-HH singleton.

**Key original-source science result:** Source-QC NOAA Bangor-minus-Ho1 original measured T remains strongly positive **before and after most VPD-selected cold episodes**. Across 36 episodes, the two-hour before/start or end/after signed-residual median changed by more than 8°C for **0 starts, 0 ends**. For 2000-03-06→03-07 35h episode, median NOAA−Ho1 T before/start/end/after = **+9.980 / +11.140 / +15.877 / +15.4575°C**; actual source-native 30min boundary T changes were **−0.32 / +0.162°C**. For the 2000-02-22→23 24h episode the corresponding signed residuals were **+6.995 / +8.985 / +15.130 / +14.870°C**, native T jumps +0.25/+0.52°C. Therefore the **36 selected source humidity-hard + independent-CDS-temperature >8°C runs cannot be interpreted as true instrument-temperature residual regime onset/offset**. Median source-residual boundary threshold is only diagnostic; 0 flagged source-residual boundaries is NOT direct proof of sensor health or that *all* raw source temperature jumps are small.

New [Stage81 source SHA-verified full-year Ho1 2000 native TA_F QC0 versus NOAA Bangor residual-regime analysis](scripts/stage81/81_Ho1_2000_full_year_native_QC0_NOAA_cold_regimes_independent_VPD.py) imports pinned verified Stage80, independently checks Stage80 audited report/outputs SHA, entire original 17,568 HH (2000 leap year), native QC0 and source-QC NOAA within ±30min, maps the previous 505 native original cases and 1069 VPD hard-HH only as **context flags**. It computes original source half-hour NOAA−Ho1 residuals, seasonal/hourly/daily source census split original VPD hard vs nonhard, and **new contiguous >+8°C and <-8°C QC0 residual runs across the complete year**, without VPD-based episode selection. Fully offline, new isolated report only, no source/NOAA re-download, no air-temperature replacement or forcing edits. [Verified Stage80 operator source evidence and pinned Stage81 IRIDIS6 code](docs/stage80_PASS_stage81_Ho1_2000_full_year_T_QC0_NOAA_residual_regimes_20261025.md). Stage81 GitHub code SHA/structure checked, awaiting IRIDIS6 real run.

**Unchanged scientific HOLDs:** 16,874 original Ho1/BZS humidity-hard events, 15,199 independent CDS numeric-only humidity shadows awaiting historical BIF UTC and final science approval, 1,675 original source T quality/delta holds, and prior separate Stage64 9,389 proposals. Neither an airport temperature reference nor ERA5 automatically validates original tower QC0 or licenses model forcing modification. Original FLUXNET, NOAA, CDS, CIME, DATM and Slurm unchanged.

### Stage81 full original Ho1 2000 measured QC0 NOAA temperature-regime audit PASS; Stage82 bidirectional source TA_ERA/VPD lineage (25 Oct 2026)

Actual IRIDIS6 operator Stage81 pinned Git blob `6e584c3e446e6637e8dbdad3241a278d15c0f415` self-test, source SHA check and new isolated `AUDIT PASS`. Original report `reports/stage81_Ho1_2000_full_year_QC0_NOAA_temperature_regimes_20261025T192411Z_3f99abd7` reconstructs **17,568** native source HH across leap year 2000, **17,294** valid original TA_F_QC0 temperatures, **17,140** original QC0 half-hours source-QC-matched with the SHA-archived Bangor NOAA GHCNh 2000 airport temperature. Original annual native measured Ho1 source temperature relative to NOAA: **1,554 HH NOAA warmer than Ho1 by >8°C**, **2,518 HH Ho1 warmer than NOAA by >8°C**, **13,068 matched HH within ±8°C**; the 4,072 extreme differences are scientific comparisons with a ~46km-distant airport, **not** proven sensor faults. Unmatched/non-QC0 original 428 HH excluded from measured/QC0 and NOAA paired residual comparisons.

Original 505 VPD-hard-selected QC0-versus-separate CDS temperature flags represent only a subset: **498** had NOAA source-QC station matches and **465/505** have NOAA more than 8°C warmer than Ho1; of ALL 1,554 NOAA warmer-than-Ho1 events, **519 are within the original 1,069 VPD-hard source population, 1,035 outside**. All 2,518 opposite-sign Ho1 warmer-than-NOAA cases are source-nonhard-VPD under Stage81's monthly decomposition. These bidirectional differences form **122** full-year QC0 cold-relative-to-NOAA runs and **167** warm-relative-to-NOAA runs independently of the earlier 36 VPD-selected original source blocks.

Notable source measured-QC0 residual examples: **2000-01-10 10:30→Jan12 22:30, 60.5 h, median NOAA−Ho1 +16.580°C, 88 VPD-hard HH**; **2000-01-17 03:30→Jan20 23:00, 92 h, median NOAA−Ho1 −18.314°C, 0 VPD-hard HH**; **2000-10-26 10:30→Oct27 22:30, 36.5h NOAA−Ho1 +11.225°C and ZERO VPD-hard HH**. Strong, opposite-sign source/airport differences in a single winter invalidate any assumed universal native T calibration correction. NOAA/ERA5 can share assimilated observations; local canopy, weather, instrument provenance and historical site clocks remain unresolved. No native measured T or VPD correction approved.

New [Stage82 SHA-pinned original Ho1 2000 full-year **native TA_F, optional TA_ERA, VPD_F / VPD_F_QC** versus screened archived NOAA signed-temperature source triage](scripts/stage82/82_Ho1_2000_full_year_bidirectional_T_VPD_source_lineage_audit.py) gates all original Stage81 output SHA256, source calendar/census and 289 source residual runs, records VPD source QC0/1/2 association with both temperature difference directions, source native FLUXNET `TA_ERA` if present (processed/reanalysis, NOT independent measured tower truth), full native VPD extremal values plus water-saturation exploratory physics and original 30min temperature state transitions. All 17568 original HH retained, only a newly created evidence-only Stage82 report. [Actual Stage81 science findings, scope, caveats and IRIDIS6 Stage82 SHA-pinned run command](docs/stage81_PASS_stage82_Ho1_2000_bidirectional_original_T_VPD_QC_20261025.md). Stage82 GitHub source committed and statically checked, **not yet run on IRIDIS6**.

Unchanged previous science HOLDs: full **16,874 original Ho1/BZS humidity hard events**, **15,199** numerical humidity shadow candidates without approved historical BIF effective UTC/source T/forcing QA, **1,675** original temperature-QC/CDS delta HOLDs, separate Stage64 **9,389** numeric source candidates. No native tower, NOAA, CDS, forcing NetCDF, DATM, CIME or Slurm edits.

### Stage82 FULL YEAR Ho1 2000 original TA_F-QC0 vs NOAA/VPD QC2 source result PASS; Stage83 verify native VPD_F is ERA-downscaled per FLUXNET official definition (25 Oct 2026)

Operator ran pinned Stage82 Git source blob `cf4cbfcf80004548f9ce48af3edd1e1e5c5d3abb` and reports SHA/`SELF-TEST PASS`, original source/output `CHECK PASS`, isolated `AUDIT PASS`. Original report `reports/stage82_Ho1_2000_full_year_bidirectional_native_T_VPD_source_QC_20261025T193617Z_ba9cfa2a`: **17,568** original Ho1 year-2000 HH, **17,294** TA_F measured-source QC0, **17,140** matched source-QC NOAA Bangor station. Of source-matched original TA_F_QC0: **1,554 NOAA warmer than Ho1 >8°C, 2,518 Ho1 warmer than NOAA >8°C, 13,068 within ±8°C**; 428 original hours not combined source-paired/QC0. Stage82 finds **all 17,568 original `VPD_F_QC=2`**, **all 17,568 original `TA_ERA` available**, 521 30min NOAA−Ho1 temperature regime-state transitions and zero directly extreme-cold-to-extreme-warm in 30min and zero native T 30min >8°C jumps among these transitions.

**Authoritative FLUXNET2015 FULLSET semantics:** At native HH resolution, `VPD_F_QC=0` measured, `1` high-quality MDS fill, **`2` ERA-downscaled source**; `VPD_F` is consolidated from `VPD_F_MDS` and `VPD_ERA` (MDS used only for MDS QC0/1). Source docs: https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/ and https://fluxnet.org/wp-content/uploads/variable_codes_FULLSET_20161024.pdf . Thus the year-2000 Ho1 `VPD_F` is **not originally measured humidity**, despite most source tower `TA_F` entries being observed QC0. The reported original source physical mismatch VPD_F>eswater(T measured QC0) for **1,068** native HH is logically compatible with ERA-derived humidity versus a distinct local tower air-temperature source and cannot identify the erroneous variable by itself. No automatic NOAA/ERA5 T replacement or forcing is justified. Native processed `TA_ERA` is not independent ground-truth T.

New [Stage83 exact original FLUXNET HH year-2000 VPD_F_QC2 primary SHA/source-row provenance and VPD_ERA/TA_ERA water-saturation cross-check](scripts/stage83/83_Ho1_2000_QC2_ERA_VPD_native_source_provenance_audit.py) verifies exact Stage82 code and six archived output SHA, independently revalidates original Stage49 primary CSV SHA and **all 17,568 original physical line+timestamp+raw temperature/VPD/QC observations**, inspects optional native `VPD_ERA`, MDS + QC fields when present, checks VPD_F≃VPD_ERA source values directly, and evaluates VPD_F vs eswater(original measured TA_F) and vs eswater(native original processed TA_ERA), preserving all original extreme VPD values. It creates only a separately hashed science-report folder, with no DATM/CIME/forcing edits. [Stage82 actual operator PASS and official FLUXNET QC2 reference, pinned Stage83 IRIDIS6 instructions](docs/stage82_PASS_stage83_Ho1_2000_QC2_ERA_VPD_source_provenance_20261025.md). Stage83 GitHub-committed/source structurally checked; not yet run on IRIDIS6.

Unchanged original science HOLD: **16,874** original Ho1/BZS source hard VPD rows; **15,199** humidity numerical shadow candidates not yet approved due original historical BIF/T/VPD forcing issues; **1,675** source temperature-review HOLD rows; the separate Stage64 **9,389** proposed numeric humidity sources. All approvals remain false.

### Stage83 PASS: original Ho1 2000 VPD_F is exactly original VPD_ERA 17568/17568, source-T mismatch explains all 1068 QC0 physics flags; Stage84 inspect 32 ERA-self Jan exceptions (25 Oct 2026)

Operator Stage83 pinned Git blob `8e2bdf99a404ba27dcb8832f734028bb084a8660` source SHA, self-test, completed Stage82/original FLUXNET SHA and original physical HH row QC check and isolated **AUDIT PASS**. Original full-year FULLSET_HH source SHA256 `519a3376161fc58ff0d9534de0b1f92a2460a8a2069b45cfb2254bb8f3b7655f`, report `reports/stage83_Ho1_2000_original_VPD_QC2_ERA_T_context_20261025T224055Z_24b5df95`. Direct original **17,568/17,568** source HH all have `VPD_F_QC2`, and each source `VPD_F` exactly equals its **original `VPD_ERA`** (max abs diff=0 hPa). Original tower TA_F remains measured-source QC0 for **17,294** HH, but **VPD_F is never directly measured** in this 2000 product; FLUXNET2015 FULLSET standard `VPD_F_QC=2` means ERA-downscaled. Original `VPD_F_MDS`, `VPD_F_MDS_QC`, `TA_F_MDS` columns available, with **zero MDS VPD QC0/1** for this year. Relevant official FLUXNET variable docs: https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/ and https://fluxnet.org/wp-content/uploads/variable_codes_FULLSET_20161024.pdf .

Original native source `VPD_F > eswater(TA_F_QC0)` for **1,068 HH** — all **1,068 are consistent with companion source processed `TA_ERA`** (`VPD_F ≤ eswater(TA_ERA)`). This strongly supports incompatible air-temperature versus humidity *source pairing* as the dominant driver of earlier native tower-T humidity physics holds; it does NOT prove an originally measured tower T is erroneous. A **separate** group of **32 HH** has original `VPD_ERA > eswater(TA_ERA)` (ALL January 2000), with **zero overlap** with the 1,068 tower-T mismatch group. These 32 require independent ERA product field/time/convention scrutiny and may reflect numerical/downscaling or other mismatch; neither implies a measured RH observation nor an approved humidity/air-T correction.

New [Stage84 source-immutable original Ho1 2000 32 January ERA-VPD versus source ERA-T saturation exceedance diagnostic](scripts/stage84/84_Ho1_2000_32_native_ERA_VPD_T_own_source_physics_hold_audit.py): verifies exact Stage83 source Git blob, all 5 Stage83 finished report SHA256 outputs, complete 17,568 source HH identities and 32/1,068 disjoint physics cases, recalculates saturation-over-water and below-freezing ice sensitivity, derived implied RH (NOT original RH observation), prints exact 32 native timestamps/excess magnitudes/days and +/-6h source context, creates new isolated SHA-marked report only. Full source `VPD_F`, raw `VPD_ERA`, TA_F and processed TA_ERA retained byte-unchanged. [Stage83 actual science results and Stage84 pinned IRIDIS6 one-paste instructions](docs/stage83_PASS_stage84_Ho1_2000_32_original_ERA_VPD_T_self_physics_20261025.md). Stage84 GitHub committed/lexically checked, **not yet run on IRIDIS6**.

Unchanged entire original Ho1+BZS source humidity hard/HOLD **16,874**, numerical-only independent ERA5 candidate humidity shadows **15,199**, original temperature-source HOLDs **1,675**, separate Stage64 candidate source records **9,389**. The no-historical-UTC-approval, no-replacement and no-DATM/CIME/NetCDF/Slurm changes continue. No original measured tower TA_F automatically replaced by NOAA or ERA5.

### Manual science DECISION: Ho1 2000 KEEP tower-original TA_F; Stage85 humidity-only candidate created by one operator command (25 October 2026)

The operator explicitly approved **keeping native US-Ho1 2000 TA_F**, ending further tower T vs ERA/NOAA tests. Decision is scoped to the **17,294 source-measured TA_F_QC0** HH (including the 505 previously >8°C vs ERA5 and both original Stage84 Jan 24–25 intervals); retain all 17,568 original TA_F source fields byte-unchanged, leaving **274 source T QC!=0** as separate unapproved provenance HOLD. This override applies only to Ho1 2000 and does not change existing other site/year approvals.

**Stage85 new humidity-only candidate logic**: Native FLUXNET VPD_F_QC=2 ERA VPD source equals VPD_ERA all 17,568 original 2000 HH. In measured QC0 rows, KEEP original VPD as-is wherever 0≤VPD≤eswater(original native tower TA_F), including the **32 original ERA self-inconsistent January records** that are compatible with measured tower temperature. In the **exact 1,068 measured-QC0 source HH** where original VPD>eswater(native tower T), preserve ERA fractional saturation deficit `D=VPD_ERA/eswater(TA_ERA)` and set `VPD_new=eswater(native TA_F)*D`, `RH_new=100*(1-D)` so native tower air T is NEVER changed. Pressure-matched near-surface specific humidity `QBOT` is computed only where original source PA_F or PA_ERA exists; pressure missing is clearly flagged, never fabricated. The other **274 original non-QC0 tower T source HH** remain a science HOLD with no new approved humidity. Only new isolated candidate CSVs and source/decision SHA manifest created, **not** an overwrite of original forcing or a Slurm submission.

Committed operator command and details: [Stage85 approved keep-tower-T/manual decision and source-pinned direct builder](docs/stage84_manual_decision_APPROVED_stage85_preserve_tower_T_humidity_candidate_20261025.md), [Stage85 script](scripts/stage85/85_apply_manual_Ho1_2000_keep_tower_T_repair_humidity_candidate.py). Source commit `982e1e8919b5b9bb9ce3998f067c577bd74ad40d`, Git blob `e09676acaf05b21fa10eff3aace38cdd47880e41`. GitHub commit was performed here; actual original IRIDIS6 files are not accessible via GitHub and operator must execute the one command once to generate the site-local output. Existing source 16,874 humidity-hard historical records, 15,199 original numeric-only shadows, 1,675 original T-HOLD historical record and separate Stage64 9,389 candidates all remain as immutable historical provenance; this manual tower-T decision is separately documented and does not grant blanket forcing approval.

### Stage85 operator PASS — manual Ho1-2000 tower-T QC0 retained; scoped humidity-only source candidate; Batch02 DATM still not generated (25 Oct 2026, 23:55 UTC)

Operator ran exact Stage85 pinned Git blob `e09676acaf05b21fa10eff3aace38cdd47880e41` on IRIDIS6 and printed `STAGE85 MANUAL DECISION APPLIED` and `STAGE85 CANDIDATE CREATED`, report `reports/stage85_Ho1_2000_MANUAL_KEEP_TOWER_T_humidity_candidate_20261025T235555Z_12086954`. **Original Ho1 2000 tower TA_F unchanged 17,568/17,568**, 17,294 original measured TA_F_QC0 retained, humidity-only source-ERA saturation-fraction transformed for 1,068 original physically inconsistent source-QC0 HH, 32 original Stage84 ERA-self January cases retained with original VPD, 274 TA_F_QC≠0 held separate, **QBOT available 17,294/17,294 original QC0 source HH, missing 0**. No existing forcing DATM NetCDF/CIME/Slurm modifications; new manifest + candidate CSVs under separate report only. No further manual review of the previously approved original 505 QC0 large contextual temperature differences or 32 Stage84 original tower-T records is required.

**Next gates before full ten-site Batch02 DATM:** (a) choose QC-provenance policy for 274 nonQC0 Ho1 2000 source temperature rows and others; (b) link Stage85 candidate into complete station/all-year selected forcing without losing exact original timestamps, independently run Post-v5 numerical/physical/QC event audits and ensure ten-site full coverage; (c) decide/check historical local clock, NOLEAP 30min/60min and interval-centering; (d) generate year-by-year CF NetCDF and stream *templates* as TECHNICAL_PREVIEW_ONLY (Batch01's verified Stage81 NC builder is reference software, not reusable Batch02 site-selection source), then real case domain/CIME DATM-vs-CDEPS/ZBOT and smoke-test. Site vegetation/PFT representation remains a separate model acceptance gate. Prior Stage64 9,389 and historical Stage74 15,199/1,675 are immutable science-provenance rows, **not** newly approved or mutually additive Stage85 edits. The user does not need to re-audit 1,068 or 32 original Ho1 year-2000 cases.

[Stage85 PASS evidence and scoped pre-DATM blocking decisions](docs/stage85_PASS_preDATM_remaining_actions_20261025.md).

### Stage86 current ten-site Stage08/Post-v5 inventory after manual Ho1 year-2000 Stage85 (26 Oct 2026)

**Do not assume other 9 Batch02 stations are DATM-ready.** Earliest documented Stage07 selected BZS, CMW, Ha1, Ho2, Ho3 numeric candidates, while EML, GLE, Ho1, ICh, ICt had humidity blockers. Later QC and CDS science audits do not establish a completed ten-site Stage08+Stage09 final source selection. Newly GitHub-published [Stage86 read-only actual on-cluster inventory](scripts/stage86/86_batch02_ten_site_and_Stage85_preDATM_inventory_readonly.py) SHA-verifies exact Stage85 operator PASS outputs (17,294 QC0 original tower T, 1,068 humidity-only remaps, 32 unchanged VPD, 274 nonQC0 source T hold), inventories each existing Stage08 selected candidate root/site/forcing SHA and corresponding Stage09 Post-v5 reports, and prints the missing integration gate. [Pinned operator command and data-conservative next steps](docs/stage85_PASS_stage86_ten_site_integration_readonly_preDATM_20261026.md). Stage86 script Git commit `a74667fe1757ec0123838657fea4a57219627664`, Git blob `0d88ba00946a70288d88b484f650dc213a5b40a8`, structurally checked but **not yet executed on IRIDIS6**. Stage08/09 selection or old Stage10 runner cannot be presumed to incorporate later Stage85 Ho1-2000 manual decision; first overlay selected source candidate in a separate new copy before DATM NetCDF technical build.

### Stage86 operator inventory PASS: 0 complete ten-site Stage08, 0 Post-v5 — Stage87 starts technical NetCDF for 5 numerically complete sites (26 Oct 2026)

Stage86 IRIDIS6 run independently SHA-verified the completed US-Ho1 2000 Stage85 manual source result and found one *incomplete* Stage08 sensitivity directory `raw_RH_sensitivity_20261022T013805Z_aadaffee` with references only to Stage07's five numeric candidates. **NO** ten-site candidate set and **NO** Post-v5 report exists on this experiment root. Remaining Stage07 humidity-blocked sites are US-EML, US-GLE, US-Ho1, US-ICh, US-ICt; do not claim the other nine sites have all passed. New [Stage87 five-site native HH/HR NOLEAP NetCDF technical-preview builder](scripts/stage87/87_build_five_verified_Stage07_DATM_noleap_technical_preview.py) SHA-proves the original five numerically verified Stage07 selected CSV forcing and existing Batch02 point surfaces, directly builds 117 annual NetCDF4_CLASSIC technical previews expected for BZS(15), CMW(21), Ha1(35, hourly), Ho2(27), Ho3(19), makes five **unactivated** stream templates, and does not alter Ho1 Stage85 or any existing source/case/Slurm. Git source commit `e3c7ab2e57e2796ad88187f4ef7b7ea1164abc3b`, Git blob `4f188cd785f31812bd8ec002b05dafda09e884b2`. This only accelerates TECHNICAL NetCDF creation; old Stage07 QC0 changes, site clock/ZBOT/PFT and Post-v5 science are not automatically approved. [Actual Stage86 checkpoint and Stage87 pinned IRIDIS6 execution](docs/stage86_PASS_stage87_five_preexisting_batch02_DATM_netcdf_preview_20261026.md). Stage87 committed/Git hash checked but not yet run on IRIDIS6.
