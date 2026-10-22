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

Only Stages00–02 are implemented here. Later stages will use the actual
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
