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
