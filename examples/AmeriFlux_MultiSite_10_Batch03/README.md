# AmeriFlux MultiSite 10 — Batch 03

> **Latest scientific status (2026-10-24):** Stage10k completed on IRIDIS6 for 1,924/1,924 residual cold-humidity events, including the two US-NR3 exceptions. There are **0 approved humidity repairs, 0 approved UTC offsets, and no Post-v5/DATM/spinup approval**. See [Stage10k science decision gate](docs/STAGE10K_SCIENTIFIC_DECISION_GATE_2026-10-24.md). Full SHA-pinned event reports remain on IRIDIS6; GitHub has scripts and operator-verified summaries.


This separate batch follows [Batch02](../AmeriFlux_MultiSite_10_Batch02/) for
the ten exact operator-supplied releases in [sites.tsv](sites.tsv).
The operator has completed and verified Stage00–10d diagnostic execution on IRIDIS6 as of 2026-10-24. All 10 packages were transferred and extracted; 3/10 Stage07 numeric QC-v5 trials completed, 7/10 remain humidity-blocked; all 32 required ERA5-Land year-site products are present; 1,924 residual humidity records passed Stage10d evidence triage. These are **scientific investigations, not approved forcing repairs**. No Post-v5 acceptance, DATM or CLM-FATES spin-up is authorized. Refer to the **[Stage00–10d scientific status and decision ledger](docs/SCIENTIFIC_REVIEW_STATUS_2026-10-24.md)** for verified operator results and limitations.

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

## Stage08: same-release RH sensitivity for seven humidity-blocked sites

The operator's Stage07 live candidate trial:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/qcv5_native_trial_20261022T024559Z_36c46e58`
completed **3/10** numeric candidates (US-MOz, US-Mpj, US-NC2);
seven failed with **2,273** unresolved humidity pairs (US-Kon 359,
US-Me2 4, US-Me6 1, US-MMS 22, US-MtB 15, US-NR1 173, US-NR3 1699).
The original trial and incomplete marker must remain untouched.

[Stage08 sensitivity driver](scripts/stage08/08_resolve_blockers_with_raw_rh.py)
uses the [separate RH engine](scripts/stage08/qcv5_raw_rh.py) to preserve
the three successful Stage07 candidates by SHA256 and rerun only seven
blocked sites. Only exact replicated humidity blocker rows may use
same-release `RH` to reconstruct VPD while preserving the candidate's TA
and PA. Valid RH does not establish independent measurement provenance;
all reconstructions require manual QC0/RH provenance review. The driver
never changes the Stage07 trial or primary sources.

On IRIDIS, **first run the read-only check**:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage07" "$BASE/scripts/stage08"
  for FILE in scripts/stage07/qcv5_native.py \
              scripts/stage07/07_build_batch03_qcv5_candidates.py \
              scripts/stage08/qcv5_raw_rh.py \
              scripts/stage08/08_resolve_blockers_with_raw_rh.py; do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  TRIAL='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/qcv5_native_trial_20261022T024559Z_36c46e58'
  "$PYTHON_BIN" -B "$BASE/scripts/stage08/08_resolve_blockers_with_raw_rh.py" \
    --stage07-root "$TRIAL" --check
)
```

Expected `STAGE08 PREFLIGHT: preserved=3 blocked=7 unresolved_records=2273`
if all original trial and script hashes match. After reviewing this
result, `--run` can build the separate sensitivity trial; if any site
remains blocked, the incomplete marker is retained and a further
scientific decision is needed. A complete selection is still not
Post-v5 accepted and is never sufficient to start DATM/spin-up.

## Stage08b: residual RH blocker classification (no candidate edits)

Stage08 ended `preserved=3 sensitivity_pass=0 failed=7 selected=3/10
inputs_unchanged=True`. Among 2,273 original unresolved humidity pairs,
349 met same-release RH numerical criteria but **none of the seven
sensitivity runs completed**; 1,924 remained unresolved. Same-release
`RH_QC` was unavailable for all 349 numerically eligible records.

[Stage08b](scripts/stage08/08b_diagnose_remaining_rh.py) verifies the
unchanged preserved Stage08 output and classifies the 1,924 remaining rows
by documented hold reason, missing/out-of-range RH, cold temperatures,
negative implied vapor pressure, and ERA RH screen status. These counts
may overlap and are **not** independent repair approvals. The output
is evidence only, not revised QCv5 or Post-v5 acceptance.

Run in IRIDIS:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage08"
  SCRIPT="$BASE/scripts/stage08/08b_diagnose_remaining_rh.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage08/08b_diagnose_remaining_rh.py" -o "$SCRIPT"
  TRIAL='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/raw_RH_sensitivity_20261022T025645Z_3c43eb8b'
  "$PYTHON_BIN" -B "$SCRIPT" --stage08-root "$TRIAL" --check
)
```

If the preflight passes, run the same command with `--run` in place of
`--check` to create a new isolated
`reports/stage08b_rh_cause_<timestamp>_<id>` report with
`site_hold_summary.csv`, `unresolved_rh_records.csv`, and
`unresolved_by_year_and_reason.csv`. No inputs are modified.

## Stage08c: ERA5 humidity rejections for 1,924 residual events

Stage08b confirmed that all **1,924** remaining Stage08 blockers have
`HOLD_RH_MISSING_OR_NONFINITE`. The next evidence-only audit,
[Stage08c](scripts/stage08/08c_diagnose_era_humidity_blockers.py),
classifies **why companion ERA5 humidity does not meet the existing
QCv5 numeric preconditions**, and compares water/ice saturation
formulations below freezing only as a sensitivity (not a repair).

IRIDIS read-only preflight:

```bash
(
  set -euo pipefail
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage08"
  SCRIPT="$BASE/scripts/stage08/08c_diagnose_era_humidity_blockers.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage08/08c_diagnose_era_humidity_blockers.py" -o "$SCRIPT"
  "$PYTHON_BIN" -B "$SCRIPT" --check
)
```

After a successful preflight, `"$PYTHON_BIN" -B "$SCRIPT" --run`
writes only isolated `reports/stage08c_era_humidity_...` files.
The prior Stage07 and Stage08 incomplete markers must remain in place;
no forcing, DATM, PFT/case changes or Slurm submissions are authorized.

## Stage08f: independent read-only MDS humidity-pair screen

Stage08e completed a SHA256-pinned inventory of all 1,924 residual humidity
blockers. It found both MDS TA and MDS VPD populated at 1,625 native
timestamps, while 299 lacked that pair. This is **availability only**,
not evidence of correct or independent humidity.

[Stage08f](scripts/stage08/08f_audit_mds_humidity_pairs.py) independently
checks physically consistent MDS TA/VPD pairing, the corresponding QC
fields, whether MDS VPD remains valid at retained TA, and numerical
similarity with the original F and ERA companions. It does not modify
forcing, prior trials, DATM, or jobs; a science review is still mandatory.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
  mkdir -p "$BASE/scripts/stage08"
  SCRIPT="$BASE/scripts/stage08/08f_audit_mds_humidity_pairs.py"
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage08/08f_audit_mds_humidity_pairs.py" \
    -o "$SCRIPT"
  "$CONDA_PREFIX/bin/python" -B "$SCRIPT" --check
)
```

After the read-only check, run `"$CONDA_PREFIX/bin/python" -B "$SCRIPT" --run`
for an isolated `reports/stage08f_mds_pairs_...` report. Successful
numerical screens are review cues, **not repair approvals**.

## Stage09a — external dewpoint evidence planning (read-only)

Stage08f finished: 1,535 physically valid MDS TA/VPD pairs (all QC2/3),
421 VPD values valid at retained TA, 90 physically inconsistent pairs
and 299 incomplete pairs. **None are approved substitutes.** The
[Stage09a plan script](scripts/stage09/09a_plan_external_dewpoint_evidence.py)
produces a 7-site/year CDS ERA5-Land hourly dewpoint/temperature/pressure
request manifest based on the 1,924 residual blockers. It also inventories
BIF `UTC_OFFSET` records and labels missing or inconsistent clock metadata
as unresolved, rather than assuming a timezone. It does not submit API
requests, interpolate, or change any forcing or model runs.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage09"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage09/09a_plan_external_dewpoint_evidence.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage09/09a_plan_external_dewpoint_evidence.py" -o "$SCRIPT"
  "$CONDA_PREFIX/bin/python" -B "$SCRIPT" --check
)
```

After successful check, use `"$CONDA_PREFIX/bin/python" -B "$SCRIPT" --run`
to produce an isolated `reports/stage09a_external_dewpoint_plan_...`
containing `era5land_request_plan.json`, `site_utc_offset_inventory.json`
and `request_summary.csv`. External series need actual time alignment
and source-evidence review before any further QCv5 candidate trials.

## Stage09b — one-site/year ERA5-Land pilot, not forcing

Stage09a returned 32 requested site-years spanning 7 sites and 1,924
source-event blockers. BIF UTC offsets are recorded for six stations but
require provenance validation; US-Me2 has no release BIF. The
[Stage09b pilot](scripts/stage09/09b_download_era5land_pilot.py) validates
the pinned Stage09a request receipt and offers one explicit CDS retrieval
(default **US-NR3 2022**) rather than automatically submitting all 32.
The US-NR3 2022 pilot returned 8,904 consecutive hourly observations per variable (2021-12-29 through 2023-01-03) using two date endpoints, so earlier concerns about two isolated dates were disproved. The verified CDS product for point hourly ERA5-Land is
`reanalysis-era5-land-timeseries`. Returned payload can be a NetCDF
or ZIP of NetCDF groups. The pilot preserves the raw response in isolated
`external_evidence/` storage, and SHA256-receipts both request and
response. No data are interpolated, aligned or used for any repair.

On IRIDIS6, first **read-only**:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage09"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage09/09b_download_era5land_pilot.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage09/09b_download_era5land_pilot.py" -o "$SCRIPT"
  "$CONDA_PREFIX/bin/python" -B "$SCRIPT" --site US-NR3 --year 2022 --check
)
```

The preflight reports whether `cdsapi` and credentials exist; it does not
print a token or initiate any API calls. Set up a Copernicus CDS account,
accept the dataset licence and configure `~/.cdsapirc` securely on the
cluster prior to explicitly selecting `--run`. Never commit the API token.
After confirming the request format on the live CDS dataset, a single
pilot can be run with `--site US-NR3 --year 2022 --run`. Inspect the
returned raw NetCDF/ZIP and UTC coverage before any expansion to the
remaining 31 requests. Six BIF clock offsets and the US-Me2 fallback
still need verified local-standard-time alignment before joining
downloaded evidence with the site series.

## Stage09c–d: verified US-NR3 2022 pilot and dewpoint evidence

Stage09c confirmed that the downloaded two-member ZIP contains exactly
8,904 hourly UTC values **per variable**, with `t2m`, `d2m`, `sp`,
each covering 2021-12-29 00:00 through 2023-01-03 23:00. The total
17,808 reported across two NetCDF time axes is **not** a count of
independent timestamps. Requested tower coordinates (40.052, −105.5864)
mapped to ERA5-Land grid (40.1, −105.6). The 2022 pilot does **not**
need redownloading. Date endpoints in Stage09a/09b were restored
to the empirically validated `["2021-12-29","2023-01-03"]` form.

The [Stage09d read-only comparison](scripts/stage09/09d_validate_nr3_2022_dewpoint.py)
confirms full unique UTC axes, grid coordinates, units and temperature/
dewpoint/pressure physical ranges and produces a **provisional** comparison
at the US-NR3 2022 blocked native timestamps, using the BIF local
standard UTC−7 offset only as a pending-verification assumption. This
does not authorize any source substitution.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  mkdir -p "$BASE/scripts/stage09"
  SCRIPT="$BASE/scripts/stage09/09d_validate_nr3_2022_dewpoint.py"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage09/09d_validate_nr3_2022_dewpoint.py" -o "$SCRIPT"
  "$CONDA_PREFIX/bin/python" -B "$SCRIPT" --check
)
```

After preflight, `--run` creates isolated diagnostic CSV/JSON
under `reports/stage09d_nr3_2022_dewpoint_...`, leaving the
original ZIP, tower data, candidate forcing, and model cases unchanged.

## Stage09e: external dewpoint at retained tower TA (evidence only)

Stage09d confirmed all **8,904 hourly UTC samples per variable** for
the US-NR3 2022 ERA5-Land pilot. The 295 blocked native records in 2022
have externally derived grid RH **47.10–84.60%** under provisional
UTC−7 alignment. This establishes usable comparison evidence, **not a
validated forcing replacement**.

[Stage09e](scripts/stage09/09e_nr3_dewpoint_tower_consistency.py)
compares two explicitly separate **sensitivities**: (A) external
dewpoint-derived vapor pressure combined with retained tower TA and
pressure; (B) transfer of the external grid RH to tower TA/pressure.
It evaluates relative tower/grid temperatures and pressures, includes
native-interval midpoint timing and ±1-hour time-offset sensitivity,
and reports previously screened MDS alternatives. UTC offset approval
and site/grid elevation differences remain open scientific checks.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  SCRIPT="$BASE/scripts/stage09/09e_nr3_dewpoint_tower_consistency.py"
  mkdir -p "$BASE/scripts/stage09"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage09/09e_nr3_dewpoint_tower_consistency.py" -o "$SCRIPT"
  "$CONDA_PREFIX/bin/python" -B "$SCRIPT" --check
)
```

After preflight `--run` creates an isolated
`reports/stage09e_nr3_2022_tower_dewpoint_...` science-evidence
report, not a revised forcing. **Do not** remove existing
`INCOMPLETE` markers, edit sources, or start DATM/Spin-up.

## Stage09f: checkpointed, capped external dewpoint downloads

Following Stage09e's 295 US-NR3 2022 comparisons, preserve both
humidity-transfer sensitivities as evidence only: absolute vapor pressure
passed 278/295, RH transfer passed 295/295. Neither passes independent
scientific validation or authorizes forcing edits.

[Stage09f](scripts/stage09/09f_incremental_dewpoint_queue.py) audits
all existing ERA5-Land receipts, ZIP CRCs, full hourly UTC time axes,
units, gridded coordinates and T2m/D2m/SP numeric coverage before
choosing at most **three new site-years per invocation**. US-NR3 2022
is reused and not redownloaded. `--check` is strictly read-only;
`--run --max-new 1` downloads just one selected year, with a second
validation afterward. Keep the Stage09b file beside Stage09f.
Missing credentials or absent CDS resources stop execution rather
than bypassing the strict checks.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
  mkdir -p "$BASE/scripts/stage09"
  for name in 09b_download_era5land_pilot.py 09f_incremental_dewpoint_queue.py; do
    curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage09/$name" -o "$BASE/scripts/stage09/$name"
  done
  "$CONDA_PREFIX/bin/python" -B "$BASE/scripts/stage09/09f_incremental_dewpoint_queue.py" --check --max-new 1
)
```

The next optional command is `--run --max-new 1` (not automatic).
This does not approve UTC conversion, site-elevation adjustments,
RH or VPD replacement, DATM, or spin-up.

## Stage09g: one-command finish of remaining ERA5-Land evidence

After Stage09f successfully verified **20/32** site-years (1,868/1,924
blocked native timestamps covered by external evidence), the
[Stage09g runner](scripts/stage09/09g_download_all_remaining.py)
can finish **all 12 remaining** without repeated manual submissions.
It invokes the existing pinned Stage09f and Stage09b scripts in
**serial, ≤3-request batches**, re-checks all existing SHA256 receipts,
hourly UTC axes, NetCDF variables and grids before and after each
batch, refuses overwrites, and stops on the first failed download.
It does NOT modify QCv5, DATM, cases, or submit Slurm jobs.

On IRIDIS6, download the three versioned scripts to the established
Stage09 folder (do not `git pull` into a conflicted checkout).
First run `09g_download_all_remaining.py --check` for a
read-only audit, then explicitly run `--run` to finish the
queue. A persistent advisory lock prevents two Stage09g instances
from draining the same queue simultaneously. A failed or interrupted
CDS retrieval may retain a `.download.partial` file, which requires
manual inspection before retry; existing verified ZIP/receipt pairs
are never changed. Successful completion is `VERIFIED=32/32`.

This is **external evidence coverage only**, not scientific acceptance
of replacement RH, QBOT, or forcing. UTC offset and grid/site elevation
checks remain required before Post-v5 and spin-up.

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

Stages00–10d now have repository scripts and operator-reported IRIDIS results. The updated [science status report](docs/SCIENTIFIC_REVIEW_STATUS_2026-10-24.md) supersedes earlier interim progress numbers in this historical README. All remaining 1,924 events require science review, and PFT/forcing/DATM/spin-up approval has not been granted. No forcing cycle, CO2 setting or spin-up length is selected.

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
authenticate to IRIDIS. They are historical pre-deployment tests, **not** substitutes for the separately reported live IRIDIS6 Stage00–10d validations.
The [scientific decision ledger](docs/SCIENTIFIC_REVIEW_STATUS_2026-10-24.md) records subsequent operator results, including SHA-pinned reports and outstanding QC/clock/forcing holds.


## Current run status (2026-10-24): Stage09h–10d

The scripts for these additional stages are available in
[stage09](scripts/stage09) and [stage10](scripts/stage10): Stage09h BIF/time-axis
audit, Stage09i temperature-based offset sensitivity, Stage10a solar-radiation
clock cross-check, Stage10b 1,924-event two-transfer humidity sensitivity,
Stage10c independent water/ice thermodynamic verification, and Stage10d
SHA-pinned 183-episode manual review prioritization.

**Latest live IRIDIS6 results:** 32/32 ERA5-Land year-site products verified;
7/7 affected towers pass native timestamp checks; 6 published BIF UTC offsets
and US-Me2 UTC−8 hypothetical only; 1,924/1,924 humidity records audited.
Absolute-vapor-pressure transfer passed 1,897/1,924 water-physics screens;
grid-RH transfer passed 1,924/1,924. Stage10c found 27 absolute-transfer
water-physics failures, 170 A and 78 B ice-supersaturation cautions; Stage10d
identified 150 tower/grid temperature-difference cautions, 183 event clusters,
and 31 priority-P0 entries (27 failure events plus four US-Me2 clock holds).
**All repair approvals remain zero.**

Read the [full science and provenance status report](docs/SCIENTIFIC_REVIEW_STATUS_2026-10-24.md)
for exact existing IRIDIS directories, per-site breakdowns, decision gates,
recheck commands, and the distinction between scripts committed on GitHub and
full raw numerical evidence retained on IRIDIS. No new forcing, Post-v5,
DATM/CIME case or Slurm job has been created or approved by these stages.


## Latest observation-provenance audit (Stage10e–10h, 2026-10-24)

See the [Stage10e–10g verified quality evidence ledger](docs/STAGE10E_TO_10G_QC_EVIDENCE_2026-10-24.md) for
89 P0/P1 events in 19 clusters, corrected dual TA+VPD QC0 definitions,
6h/24h/72h/7d observation availability, and annual QC0 coverage.
US-NR3 showed zero source-labeled measured TA_F and VPD_F records in
2017, 2018 and 2023, despite nearly complete numeric meteorology.
The [Stage10h provenance script](scripts/stage10/10h_original_qc_source_provenance.py)
is the historical v1 attempt; it incorrectly required identical whole-file
source/ERA coverage and stopped without reports. The [Stage10h-v2 timestamp-keyed audit](scripts/stage10/10h_v2_timestamp_keyed_qc_provenance.py)
**completed on IRIDIS6**: 1,924/1,924 exact event matches, 1,866 VPD QC2
ERA-downscaled, 58 VPD QC1 gapfilled, zero VPD QC0; 100% of the selected
primary timestamps match the broader companion ERA native timeline.
The [Stage10i source ERA VPD saturation audit](scripts/stage10/10i_source_ERA_vpd_saturation_audit.py)
has since **passed** the actual IRIDIS6 `--check` and `--run`. See the current
Stage10i–j section below. No humidity, time-offset, Post-v5 or spinup approval has been granted.


### Stage10i verified and Stage10j next (2026-10-24)

[Stage10i](scripts/stage10/10i_source_ERA_vpd_saturation_audit.py) passed IRIDIS6
self-test/check/run: 1,924/1,924 event rows had original paired
`VPD_ERA > es_water(TA_ERA)`, corresponding to negative *implied* liquid-water
vapour pressure within the exact-release paired ERA source fields. The largest
site median overage was US-MtB (0.257 hPa); US-NR3 covered 1,484 records.
This **does not** establish that actual atmospheric water vapour pressure
was negative, or identify which upstream ERA/downscaling step is at fault.

[Stage10j — verified on IRIDIS6](scripts/stage10/10j_source_vs_grid_humidity_counterfactuals.py)
compared existing source ERA and ERA5-Land meteorology at the same 1,924 event
identities. A numerical VPD-only swap made implied vapour pressure nonnegative
in 1,922 events (99.90%), versus 188 under a temperature-only swap. The 2
VPD-only exceptions were both US-NR3. The swap is **not** a scientifically
approved correction and does not constitute independent validation.

[Stage10k — VERIFIED on IRIDIS6](scripts/stage10/10k_exception_provenance_science_gate.py)
passed self-test, read-only check and full report generation: the two US-NR3
exceptions are 2018-02-21 09:30/10:00 local native time, source rows
195333 and 195334, both VPD QC2. The audited Stage10j reconciliation remains
1,922/1,924 VPD-only algebraic sign changes and 188/1,924 temperature-only;
**these are not approved forcing replacements**. Full evidence and the formal
[Stage10k scientific decision gate](docs/STAGE10K_SCIENTIFIC_DECISION_GATE_2026-10-24.md)
are recorded with exact IRIDIS report location and proposed source/physics
acceptance criteria.
**All humidity and clock approvals remain zero; no Post-v5 or model runs.**


### Stage11a — VERIFIED scientific review matrix (2026-10-24)

The [Stage11a source-pinned review script](scripts/stage11/11a_science_decision_matrix.py)
uses SHA-receipted Stage10d event flags, Stage10h exact-source QC origins,
Stage10k exception classifications, Stage10g QC-window evidence, and the
Stage07 original input manifest. It **passed IRIDIS6 self-test/check/run**, recording 1,687 evidence-insufficient holds, 233 physical/temperature-conflict holds and 4 US-Me2 clock holds (1,924/1,924).

It is designed to create `1924_source_event_science_review.csv`,
`32_site_year_science_decision_matrix.csv`, and
`10_site_post_v5_readiness.csv` in a new isolated report folder; its
`--self-test` / `--check` modes do not write analysis reports. Event routing
distinguishes US-Me2 clock metadata holds, flagged humidity/temperature
physics conflicts and remaining absence of independent measurement evidence.
All repair/clock/Post-v5 approvals remain **FALSE**. The three Stage07 numeric
candidate sites are **not** Post-v5 certified; the other seven remain blocked.

Do **not** use the Stage11a review route or a source/grid counterfactual
pass percentage to start DATM, modify forcing, or submit a spinup. Scientific
signoff is a separately documented human review decision.

### Stage11b — three numeric candidates, Post-v5 Gate-0 (code committed)

[Stage11b script](scripts/stage11/11b_three_site_postv5_gate0_audit.py)
has **passed IRIDIS6 self-test, check and full report run**. It rechecks
the original SHA-pinned FLUXMET/ERA source and Stage07 `processed_v5` candidates
for **US-MOz, US-Mpj and US-NC2**, including complete NO_LEAP native
time steps, TBOT/QBOT/PSRF/PRECTmms physics and conversions, raw-to-v5
change ledger, changed original QC0 records, manual review and ERA-RH floor
counts. A successful Gate-0 is **numeric/provenance-only**, never official
Post-v5 approval; `--check` writes nothing, `--run` creates one isolated
read-only review report. The Stage07 INCOMPLETE marker is retained, no DATM
or spinup authorised.


### Stage11b verified and Stage11c change-level review (2026-10-24)

The [Stage11b numeric-only Post-v5 Gate-0 audit](scripts/stage11/11b_three_site_postv5_gate0_audit.py)
**passed on IRIDIS6** for US-MOz, US-Mpj and US-NC2. The three candidate
forcing CSVs cover 998,640 NO_LEAP native half-hour records combined, with
105 original-to-candidate variable changes, **6 changes to original QC0 values**,
18 manual-review rows, zero ERA RH clipping/floor records and **38 ERA-source
variable replacements at US-NC2**. The minimum water-relative RH was 2.2064%,
0.4392% and 0.0773% for US-MOz, US-Mpj and US-NC2 respectively. The full
[verified Stage11b scientific evidence record](docs/STAGE11B_GATE0_VERIFIED_2026-10-24.md)
includes exact IRIDIS report locations and outstanding Post-v5 holds.

The next source-event [Stage11c audit script](scripts/stage11/11c_qc0_manual_era_change_review.py)
has now **passed the IRIDIS6 self-test, check and report run**. It
reconciles all 105 source QC/ERA/processed-v5 changes by native source key,
extracts 6 measured-QC0 changes, preserves 18 manual review entries, and
audits RH<1% records. The script is evidence-only, not a repair generator.

**All humidity, clock, PFT/CO2 protocol, Post-v5, DATM and spinup gates remain
unapproved.** No original forcing, processed_v5 data, Stage07 incomplete marker,
CIME case or Slurm job may be changed based on these audit results.


### Stage11c verified and Stage11d evidence packet (2026-10-24)

[Stage11c](scripts/stage11/11c_qc0_manual_era_change_review.py) **passed**
on IRIDIS6 with 105 exact source-to-v5 variable changes, 6 originally
QC0-coded measured air-temperature modifications, 18 manual-review entries
(including 4 without final variable changes), 38 US-NC2
`secondary_era_replacement` variables and 5 preserved RH values
between 0 and 1%. Stage11c reported no originally missing values among
the 105 modified source records; the 38 later ERA-source replacements
therefore require an explicit `event_reason` analysis, not a claim of
original input missingness.

The six modified QC0 values all have
`isolated_spike_ERA_confirmed|short_gap_interpolated` event reason.
[Verified Stage11c data interpretation and event list](docs/STAGE11C_VERIFIED_QC0_MANUAL_REVIEW_2026-10-24.md).

[Stage11d](scripts/stage11/11d_priority_change_context_review.py) has now
**passed IRIDIS6 --self-test, --check and --run**. Its 62 distinct review
cases (US-MOz 1, US-Mpj 6, US-NC2 55) have 558 source-native +/-2h
context records. The 38 US-NC2 VPD source values were original
`VPD_F_QC=1` numerical gapfill values, and all carry reason
`TA_VPD_inconsistent_VPD_only|remaining_gap_filled_ERA` before secondary
ERA replacement. Six source QC0 air-temperature spikes, five RH<1% cases,
and four unchanged manual-review rows remain on science hold. See
[Stage11d verified source evidence](docs/STAGE11D_VERIFIED_PRIORITY_SOURCE_REVIEW_2026-10-24.md).

[Stage11e-v1](scripts/stage11/11e_priority_scientific_triage.py) **failed synthetic self-test before IRIDIS file checks**: a one-event simulation encountered an erroneously hardcoded 62-event join requirement. The historical v1 is preserved for auditing.

[Stage11e-v2 repaired source-physics triage](scripts/stage11/11e_v2_priority_scientific_triage.py)
is **committed but not yet run on IRIDIS6**. Synthetic tests now explicitly request one event and verify that production still requires 62 unique joined records; an unmatched event identity also fails. It will use the sealed 62-target
Stage11d report to independently classify original VPD/T water thermodynamics,
check six QC0 edits against native neighbours and report 38 QC1 VPD
inconsistencies. The output is a scientific review queue, not permission to
write new forcing. All Post-v5/DATM/CIME/Slurm approvals remain zero.
