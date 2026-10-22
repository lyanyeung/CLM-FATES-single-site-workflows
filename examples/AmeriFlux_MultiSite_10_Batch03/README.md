# AmeriFlux MultiSite 10 — Batch 03

This separate batch follows [Batch02](../AmeriFlux_MultiSite_10_Batch02/) for
the ten exact operator-supplied releases in [sites.tsv](sites.tsv).
Stages00–01 are ready for transfer and extraction. No live upload,
extraction, meteorological QC, DATM or model execution has been verified.

| Site | Exact package | Release year labels |
| --- | --- | --- |
| US-Kon | `AMF_US-Kon_FLUXNET_2004-2019_v1.3_r1` | 2004–2019 |
| US-Me2 | `AMF_US-Me2_FLUXNET_FULLSET_2002-2022_4-6` | 2002–2022 |
| US-Me6 | `AMF_US-Me6_FLUXNET_2010-2025_v1.3_r1` | 2010–2025 |
| US-MMS | `AMF_US-MMS_FLUXNET_1999-2023_v1.3_r1` | 1999–2023 |
| US-MOz | `AMF_US-MOz_FLUXNET_2004-2021_v1.3_r1` | 2004–2021 |
| US-Mpj | `AMF_US-Mpj_FLUXNET_2008-2025_v1.3_r1` | 2008–2025 |
| US-MtB | `AMF_US-MtB_FLUXNET_2009-2024_v1.3_r1` | 2009–2024 |
| US-NC2 | `AMF_US-NC2_FLUXNET_2005-2025_v1.3_r1` | 2005–2025 |
| US-NR1 | `AMF_US-NR1_FLUXNET_1998-2025_v1.3_r1` | 1998–2025 |
| US-NR3 | `AMF_US-NR3_FLUXNET_2007-2024_v1.3_r1` | 2007–2024 |

Release labels do not establish actual data coverage, native time step or
meteorological quality. US-Me2 retains its FULLSET format and original 4-6
suffix. Nine v1.3 packages and one FULLSET package are handled separately.

## Stage00: upload in the LOCAL WSL terminal

Local Windows source: `D:\Fluxes_Tower_Experiment\Ameriflux`.
WSL source: `/mnt/d/Fluxes_Tower_Experiment/Ameriflux`.
Each exact package must be directly contained as `<package>.zip` (ZIP
extension case insensitive) or a `<package>/` folder. ZIP takes priority
when both exist. Originals are copied without repacking.

Run in **LOCAL WSL**, not in an IRIDIS SSH terminal or native PowerShell.
From PowerShell, first run `wsl`, then paste:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/ameriflux_batch03_transfer"
  mkdir -p "$BASE/scripts/stage00"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage00/00_upload_ameriflux_batch03.sh"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage00/00_upload_ameriflux_batch03.sh" -o "$SCRIPT"
  bash -n "$SCRIPT"
  LOCAL_ROOT='/mnt/d/Fluxes_Tower_Experiment/Ameriflux' \
    bash "$SCRIPT" 2>&1 | tee "$BASE/upload_$(date +%Y%m%d_%H%M%S).log"
)
```

Requirements: Bash, curl, OpenSSH, rsync, sha256sum, find, awk, mktemp and
head. The script preflights all ten releases before connecting. It opens
one SSH master to `ly3n24@iridis6.soton.ac.uk`; enter a password once if
requested. Host-key confirmation and additional factors remain subject
to the SSH service. No password is stored in scripts or logs.

Every subsequent operation reuses a private socket in `/tmp`, uses batch
mode and cannot open a replacement network connection. If the connection
fails, the script stops without repeated password prompts. Rerun the same
command to connect once and resume; keep WSL and the network open during
transfer. The master closes automatically at exit.

Destination:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/packages/<PACKAGE>.zip
```

Folders use `packages/<PACKAGE>/`. `REMOTE` and `REMOTE_ROOT` may be
overridden. Existing files are preserved with `rsync --ignore-existing`;
partial transfers can resume. Every ZIP is SHA256 checked; folder transfers
receive a recursive checksum dry-run including extra remote files. A
same-named file with different content stops the run for inspection.
No source or destination package files are deleted.

Only the following line establishes upload success:

```text
UPLOAD VERIFIED: 10/10 (AmeriFlux Batch 03). Originals retained. No extraction or model jobs started.
```

## Stage01: extract and inventory on IRIDIS

After verified upload, run in an **IRIDIS terminal**:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage01"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage01/01_extract_ameriflux_batch03.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage01/01_extract_ameriflux_batch03.py" -o "$SCRIPT"
  python3 -B "$SCRIPT" \
    2>&1 | tee "$HOME/AmeriFlux_Batch03_stage01_$(date +%Y%m%d_%H%M%S).log"
)
```

No `git pull` is needed. Standard-library-only extraction supports Python3.9+.
The script preflights all selected packages, recursively reads nested ZIPs
(up to eight levels), flattens CSV basenames and skips `toc.csv`/`!toc.csv`.
It checks size/CRC32, skips identical existing CSVs and refuses to replace
different CSVs or conflicting basenames. Source packages remain intact.
An interrupted extraction may leave a `.partial`; inspect it before retrying.

Raw output and separate batch report:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/raw/<PACKAGE>/*.csv
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage01_extraction_<UTC>_<ID>.json
```

Nine v1.3 releases require a site-specific BIF and FLUXMET_HH or FLUXMET_HR.
US-Me2 FULLSET requires a site-specific FULLSET_HH or FULLSET_HR; absent BIF
is a metadata follow-up. Separate ERA5 HH/HR products are inventoried.
Native hourly products are retained without resampling. The inventory
records headers and the first timestamp pair; it does not validate full
coverage or meteorological values.

Successful extraction summary:

```text
BATCH03 SUMMARY: 10/10 PASS (extraction/structure only); failures: none
```

Read-only recheck after extraction:

```bash
python3 -B "$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage01/01_extract_ameriflux_batch03.py" --audit-only
```

`--sites US-Me2`, `--sites-root`, `--incoming-dir` and `--reports-dir`
are available. Audit-only creates no report or raw files.

## Stage02: read-only metadata and source-interval preflight on IRIDIS

After Stage01 finishes with `BATCH03 SUMMARY: 10/10 PASS`, run this in an
**IRIDIS terminal** (no `git pull` required):

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage02"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  curl -fLsS --retry 3 "$RAW/$REL/metadata_fallbacks.tsv" -o "$BASE/metadata_fallbacks.tsv"
  curl -fLsS --retry 3 "$RAW/$REL/coordinate_decisions.tsv" -o "$BASE/coordinate_decisions.tsv"
  SCRIPT="$BASE/scripts/stage02/02_check_batch03_metadata.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage02/02_check_batch03_metadata.py" -o "$SCRIPT"
  python3 -B "$SCRIPT" 2>&1 | tee "$HOME/AmeriFlux_Batch03_stage02_$(date +%Y%m%d_%H%M%S).log"
)
```

Stage02 reads BIF coordinates/IGBP/height records for nine releases, honors\nexplicit GROUP_ID-paired site coordinate decisions in coordinate_decisions.tsv\nfor US-Mpj and US-MtB (preserving their source BIF), and reads
the explicit official AmeriFlux site-page fallback for US-Me2 (the FULLSET
without BIF), and verifies only the *first* HH/HR source interval. It
does not write site data, surfaces, forcing, model cases or Slurm jobs.
Expected summary is `STAGE02 SUMMARY: 10/10 coordinate + first-interval checks PASS; failures: none`
if the actual data match the checks.

**Scientific hold:** US-Me2's official site page reports the 20 August
2020 Green Ridge Fire, 2021 salvage logging and later tower changes;
the current ENF label is not proof of a stationary ENF land cover
through 2002–2022. Surface/PFT choices need an explicit disturbance
history review. Its site-page coordinates (44.4526, -121.5589) are an
external metadata fallback, not coordinates read from the FULLSET release.
US-MMS has native hourly meteorology; preserve HR in later workflows.
Do not use BIF height records as a final ZBOT decision; compare the
curated BASE_MeasurementHeight reference and site-specific evidence.

## Stage03: isolated CTSM year-2000 reference point surfaces

After Stage02 passes 10/10, fetch the Stage03 driver and its exact metadata
dependencies to IRIDIS. Run `--check` first; `--run` only after the preflight
passes. The script is adapted from Batch02 and creates outputs exclusively in
`sites/MY_EC_SITE/<SITE>/subset_data_batch03_surf2000/` with a SHA256 receipt
for each station. It uses `CTSM/tools/site_and_regional/subset_data point`
with `--surf-year 2000 --create-surface --create-user-mods --lon-type 180`
and **does not** use `--dompft`. It retains the documented ctsm5.3.0
surfdata/mesh reference settings. Site metadata and the explicit selected BIF
GROUP_ID for US-Mpj/US-MtB are read and rechecked on every attempt.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage02" "$BASE/scripts/stage03"
  for FILE in sites.tsv metadata_fallbacks.tsv coordinate_decisions.tsv \
    scripts/stage02/02_check_batch03_metadata.py \
    scripts/stage03/03_make_batch03_surfaces.py
  do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  "$PYTHON_BIN" -B "$BASE/scripts/stage03/03_make_batch03_surfaces.py" --check \
    2>&1 | tee "$HOME/AmeriFlux_Batch03_stage03_check.log"
)
```

If it prints `PREFLIGHT: 10 ready + 0 verified existing = 10/10`
(or ten total across ready and verified), generate the reference surfaces:

```bash
PYTHON_BIN="$CONDA_PREFIX/bin/python"
"$PYTHON_BIN" -B \
  "$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage03/03_make_batch03_surfaces.py" --run \
  2>&1 | tee "$HOME/AmeriFlux_Batch03_stage03_run_$(date +%Y%m%d_%H%M%S).log"
```

Successful fresh generation prints `STAGE03 SUMMARY: created=10
skipped_verified=0 total=10/10`. Any existing incomplete output is retained
and blocks unsafe automatic overwrite. These are **exploratory reference**
surfaces, not scientifically approved PFT configurations or model input.
Stage04a should subsequently audit actual landunit and PFT fractions;
specifically review US-Kon/US-NR3 grassland, US-Mpj mixed IGBP and US-Me2
disturbance history. No DATM, case or Slurm jobs are created.

## Stage04a: audit generated landunits and natural PFTs

The operator's Stage03 log confirms `created=10 skipped_verified=0 total=10/10`.
Run the independent [Stage04a surface audit](scripts/stage04/04a_audit_batch03_surfaces.py)
on IRIDIS. It verifies Stage03 file inventories/SHA256 receipts, NetCDF
structure, landunit sums, and natural CLM PFT fractions. It reports separate
`pct_of_natural` and `pct_of_grid` values without replacing natural PFTs
or asserting a FATES parameter mapping. US-Mpj is reviewed against the
current WSA listing while retaining all original ENF/OSH/WSA BIF labels.
US-Me2 disturbance and the US-Kon/US-NR3 grassland sites are explicit
science-review flags. Site-level review remains required even if all
structural checks pass.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  "$PYTHON_BIN" -c 'import numpy; from netCDF4 import Dataset'
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage04"
  SCRIPT="$BASE/scripts/stage04/04a_audit_batch03_surfaces.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage04/04a_audit_batch03_surfaces.py" -o "$SCRIPT"
  "$PYTHON_BIN" -B "$SCRIPT" \
    2>&1 | tee "$HOME/AmeriFlux_Batch03_stage04a_$(date +%Y%m%d_%H%M%S).log"
)
```

The report contains `surface_summary.csv`, `natural_pft_detail.csv`
and `surface_summary.json`, saved to
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage04a_surface_<UTC>_<ID>/`.
A complete structural run prints `STAGE04A SUMMARY: 10/10 structural passes; 0 structural failures`.
This **does not** approve the ecological representativeness of gridded PFT
fractions or establish time-invariant post-disturbance conditions.
No surface, DATM, forcing, case or Slurm job is modified.

## Stage04b: full native source meteorology and paired ERA5 screening

The operator's Stage04a log confirms **10/10 surface structural passes**.
Scientific vegetation representation remains unapproved, especially US-MOz,
US-MtB, US-Me2/US-Me6, US-Mpj and US-NR1. This does not block separate
meteorological source screening.

[Stage04b](scripts/stage04/04b_audit_batch03_met_sources.py) audits the
seven primary meteorological variables and the matching ERA5 products
for the exact Batch03 release windows. US-MMS is native **HR (60 min)**;
all other Batch03 primary series are **HH (30 min)**.
No source repairs, interpolation, DATM or model jobs occur.
The review bounds and liquid-water RH reconstruction are exploratory,
not scientific acceptance. Time conventions still require verification.

Run on IRIDIS, first with `--check`:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  "$PYTHON_BIN" -c 'import numpy, pandas'
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage04"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage04/04b_audit_batch03_met_sources.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage04/04b_audit_batch03_met_sources.py" -o "$SCRIPT"
  "$PYTHON_BIN" -B "$SCRIPT" --check
)
```

Only after `SOURCE PREFLIGHT: 20/20 sources; 0 failures`, run:

```bash
PYTHON_BIN="$CONDA_PREFIX/bin/python"
"$PYTHON_BIN" -B \
  "$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage04/04b_audit_batch03_met_sources.py" \
  2>&1 | tee "$HOME/AmeriFlux_Batch03_stage04b_$(date +%Y%m%d_%H%M%S).log"
```

Outputs are isolated under
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage04b_met_<UTC>_<ID>/`.
The target summary is 20/20 source audits with no source failures;
REVIEW flags are expected to need further evidence and site-specific decisions.

## Stage05: paired review of exact Stage04b anomalies

Operator results confirmed `STAGE04B SUMMARY: 20/20 sources audited;
0 source failures; 292 REVIEW source-years; 83082 flagged native records`.
The exact input directory is:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage04b_met_20261022T022701Z_d845a292
```

[Stage05](scripts/stage05/05_review_batch03_source_events.py) classifies the
83,082 flagged native source records into mutually exclusive priorities,
reconciles Stage04b annual and event counts, compares primary to paired
ERA5 on exact original site timestamps, checks raw source-row values and
hashes, and records source QC. US-MMS keeps its native hourly step. A
numerically clear counterpart is never automatic evidence for replacement.

On IRIDIS, download Stage04b helper and Stage05 script. Run `--check`
first; it verifies manifest/source identities and reconciles counts without
writing outputs. Full Stage05 writes a separate timestamped report.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage04" "$BASE/scripts/stage05"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  for FILE in scripts/stage04/04b_audit_batch03_met_sources.py \
              scripts/stage05/05_review_batch03_source_events.py; do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  REPORT='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage04b_met_20261022T022701Z_d845a292'
  SCRIPT="$BASE/scripts/stage05/05_review_batch03_source_events.py"
  "$PYTHON_BIN" -B "$SCRIPT" --source-report "$REPORT" --check
)
```

If Stage05 preflight passes, run the same downloaded script without
`--check`:

```bash
PYTHON_BIN="$CONDA_PREFIX/bin/python"
REPORT='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage04b_met_20261022T022701Z_d845a292'
SCRIPT="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage05/05_review_batch03_source_events.py"
"$PYTHON_BIN" -B "$SCRIPT" --source-report "$REPORT" \
  2>&1 | tee "$HOME/AmeriFlux_Batch03_stage05_$(date +%Y%m%d_%H%M%S).log"
```

A valid run should show `STAGE05 SUMMARY: events=83082` and
`ledger_mismatches=0`; complete success still requires examining
the event-priority/status reports. No source, surface, forcing, DATM,
case or Slurm job is changed.

## Stage06: primary repair-scope diagnosis (no edits)

Operator Stage05 verified all **83,082/83,082** flagged source rows with
**zero ledger mismatches**, grouped into 16,820 episodes. Its exact report
is `stage05_event_review_20261022T023135Z_32b20d9c`, paired with
`stage04b_met_20261022T022701Z_d845a292` (both in the Batch03
experiment `reports/` directory). Of the 83,082 source records,
42,892 are primary product records and 40,190 are companion ERA5 records.

[Stage06](scripts/stage06/06_diagnose_batch03_repair_scope.py)
cross-validates the Stage04b/Stage05 report snapshots and isolates **primary**
meteorological issues: numeric/humidity predicates, same-timestamp source
comparison, original source QC, contiguous episodes and missing-data
durations. Flags and companion screening are review evidence only, **not**
an automatic ERA5 replacement or candidate approval. An independent QCv5
candidate and Post-v5 science gate remain mandatory before DATM.

Run on IRIDIS:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage06"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage06/06_diagnose_batch03_repair_scope.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage06/06_diagnose_batch03_repair_scope.py" -o "$SCRIPT"
  REPORT_ROOT='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports'
  SOURCE="$REPORT_ROOT/stage04b_met_20261022T022701Z_d845a292"
  REVIEW="$REPORT_ROOT/stage05_event_review_20261022T023135Z_32b20d9c"
  "$PYTHON_BIN" -B "$SCRIPT" --source-report "$SOURCE" --review-report "$REVIEW" --check
)
```

After the check passes, execute the same script without `--check`:

```bash
PYTHON_BIN="$CONDA_PREFIX/bin/python"
REPORT_ROOT='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports'
SCRIPT="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage06/06_diagnose_batch03_repair_scope.py"
"$PYTHON_BIN" -B "$SCRIPT" \
  --source-report "$REPORT_ROOT/stage04b_met_20261022T022701Z_d845a292" \
  --review-report "$REPORT_ROOT/stage05_event_review_20261022T023135Z_32b20d9c" \
  2>&1 | tee "$HOME/AmeriFlux_Batch03_stage06_$(date +%Y%m%d_%H%M%S).log"
```

Stage06 creates only timestamped reports in `reports/stage06_repair_scope_...`;
no source files, surfaces, forcing, cases or Slurm jobs are modified.

## Stage07: checksum-gated native QCv5 candidate trial (NOT DATM-ready)

The operator Stage06 report `stage06_repair_scope_20261022T023738Z_0a4d314f`
confirms 42,892 primary and 40,190 paired-ERA source events,
10,469 primary P0 numeric-screen events, 31,732 P2/P3 low-positive-RH
events, and no missing primary source timestamps/variable gaps. These
screens do not establish which values are genuine sensor errors.

[Stage07 driver](scripts/stage07/07_build_batch03_qcv5_candidates.py)
and [historical native engine](scripts/stage07/qcv5_native.py) adapt the
Batch02 isolated trial. The former verifies pinned Stage06 report hashes,
manifest years, primary/ERA file hashes, and native HH/HR source identity.
US-MMS remains hourly, US-Me2 uses FULLSET_HH, and every other site uses
FLUXMET_HH. Run `--check` before any candidate construction.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage07"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  for FILE in scripts/stage07/qcv5_native.py \
              scripts/stage07/07_build_batch03_qcv5_candidates.py; do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  SCOPE='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage06_repair_scope_20261022T023738Z_0a4d314f'
  "$PYTHON_BIN" -B "$BASE/scripts/stage07/07_build_batch03_qcv5_candidates.py" \
    --scope-report "$SCOPE" --check
)
```

A successful preflight prints `PREFLIGHT: 10/10 exact releases, 20/20 raw
SHA256 verified` and `CHECK ONLY: no outputs created`. Do not use any
trial for DATM or spin-up until a full post-QCv5 independent science review
passes. For trial build, explicitly run the same driver with `--run`
instead of `--check`, after reviewing the preflight. A trial writes
only into a fresh `qcv5_native_trial_...` directory; no raw products,
original surfaces, cases or Slurm jobs are modified. The engine retains
the historical QCv5 treatment, including logged humidity reconstruction
and 1% ERA-RH floor events requiring manual review. It is **not** a
claim that the historical rules are optimal for arid Batch03 sites;
particularly inspect US-MtB, US-Mpj and US-NR3 outcomes.

## Next stages and scientific review

Continue from the actual Stage01 inventory, using Batch03-specific manifests
and outputs. Batch02 paths, coordinates, year selections and site-specific
humidity decisions must not be copied as Batch03 evidence.

1. Inspect BIF or official FULLSET metadata, coordinates, height and native
   coverage. Resolve missing US-Me2 metadata explicitly if necessary.
2. Generate isolated reference surfaces and inspect actual landunit/PFT
   fractions; review study inclusion and tower-footprint representation.
3. Audit all native source meteorology, paired ERA support and anomaly
   episodes before choosing repair scope.
4. Build isolated QCv5 candidates with original data, source QC and complete
   modification ledgers preserved.
5. Perform a separate **Post-QCv5** audit: reconcile QBOT and modifications,
   review QC0 changes, RH extremes, TA/PA jumps, ERA differences and hashes.
   Apply only justified site-specific revisions to new candidates and
   complete final acceptance. A numerical pass alone is not acceptance.
6. Establish ZBOT/PFT and forcing-loop settings, then generate DATM and
   prepare spin-up cases after those checks.

Stages00–04a are implemented here; PFT science review and meteorological QC remain pending. Later stages will use the actual
Batch03 results. No forcing cycle, CO2 setting or spin-up length is selected.

## Implementation and validation

Stage00 and Stage01 are Batch02 adaptations with batch identifiers changed;
transfer, extraction and inventory behavior is retained. Source Git blobs:
`ba0f68310dd0f63be2a5f2a6eb67b23d7035cf89` (upload) and
`7942c235b0b2cc35d08284c94352ae5375c99ca1` (extraction).

Local validation passed Bash/Python syntax and isolated integration checks:

- Ten exact mixed ZIP/folder uploads with mock SSH, real local rsync and
  checksums, one master connection and an unchanged identical rerun.
- Conflicting remote ZIP preservation/rejection, missing-source preflight
  before SSH, and disconnection without a replacement connection.
- Ten nested synthetic releases, US-Me2 FULLSET without BIF, native HH/HR
  identity, exact output paths, unchanged packages and identical rerun.
- Read-only audit without writes, conflicting raw CSV preservation/rejection,
  and missing-source preflight without raw output creation.

These mocks and synthetic packages do not access the operator's D drive or
authenticate to IRIDIS. Live upload/extraction remains pending operator
execution. Local validation does not establish actual source coverage or QC.
