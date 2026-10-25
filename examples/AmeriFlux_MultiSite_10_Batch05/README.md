# AmeriFlux MultiSite 10 — Batch 05

**Status (2026-10-25): Stage00 upload/checksum verification completed 10/10, as reported in the operator log. Stage01 extraction/structure completed 10/10 from the operator log. Stage02 metadata/full native time/basic meteorology audit locally tested and ready; IRIDIS6 execution pending.**

Fifth independent ten-site AmeriFlux campaign, following [Batch04](../AmeriFlux_MultiSite_10_Batch04/). Current scope is transfer, CSV extraction and structural inventory. Raw data are not committed to GitHub.

## Exact ten-site release manifest

| Site | Expected original archive | Release-year labels |
| --- | --- | --- |
| US-UiD | `AMF_US-UiD_FLUXNET_2008-2024_v1.3_r1.zip` | 2008–2024 |
| US-UMB | `AMF_US-UMB_FLUXNET_FULLSET_2007-2021_3-5.zip` | 2007–2021 |
| US-UMd | `AMF_US-UMd_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-Var | `AMF_US-Var_FLUXNET_2000-2025_v1.3_r1.zip` | 2000–2025 |
| US-Vcm | `AMF_US-Vcm_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-Vcp | `AMF_US-Vcp_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-WCr | `AMF_US-WCr_FLUXNET_1999-2025_v1.3_r1.zip` | 1999–2025 |
| US-Whs | `AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-Wjs | `AMF_US-Wjs_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-Wkg | `AMF_US-Wkg_FLUXNET_2004-2025_v1.3_r1.zip` | 2004–2025 |

Machine-readable source: [sites.tsv](sites.tsv). Names and years are supplied by the operator, not independently verified temporal coverage, cadence, QC or PFT classification. **US-UMB deliberately retains the distinct `FLUXNET_FULLSET_2007-2021_3-5` release name.** Its content/schema will be inspected separately after transfer. US-UiD and US-UMd remain distinct, with case preserved.

## Stage00 — run in LOCAL WSL

Windows source: `D:\Fluxes_Tower_Experiment\Ameriflux`; WSL mount: `/mnt/d/Fluxes_Tower_Experiment/Ameriflux`. Run the following in local WSL, not on IRIDIS or native PowerShell:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch05'
  BASE="$HOME/ameriflux_batch05_transfer"
  mkdir -p "$BASE/scripts/stage00"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage00/00_upload_ameriflux_batch05.sh"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage00/00_upload_ameriflux_batch05.sh" -o "$SCRIPT"
  bash -n "$SCRIPT"
  LOCAL_ROOT='/mnt/d/Fluxes_Tower_Experiment/Ameriflux' \
    bash "$SCRIPT" 2>&1 | tee "$BASE/upload_$(date +%Y%m%d_%H%M%S).log"
)
```

Requires Bash, curl, ssh, rsync, sha256sum, find, awk, mktemp and head. [Transfer script](scripts/stage00/00_upload_ameriflux_batch05.sh) follows Batch04's implementation with only batch labels/socket prefix changed.

The full ten-site source preflight finishes before SSH connects. Each source must be an exact `<package>.zip` (case-insensitive match) or an exact same-named release directory. A ZIP takes priority if both are present. Missing or ambiguous sources stop execution; packages are never renamed or repacked.

One SSH master connection to `ly3n24@iridis6.soton.ac.uk` handles all transfers and checks. Authentication normally occurs once; a lost master stops the script rather than opening another password session. Logs remain in `$HOME/ameriflux_batch05_transfer/` on WSL. Rerun the same command to resume.

Remote layout:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/packages/<EXACT-PACKAGE>.zip
```

Same-named source directories go under `packages/<EXACT-PACKAGE>/`. Existing final destination files are preserved with `rsync --ignore-existing`; a different checksum is a hard stop, not permission to replace data. Interrupted uploads use rsync partial files. ZIPs receive local/remote SHA256 checks; directories receive recursive checksum comparison, including detection of unexpected remote files (`--delete` is dry-run only). Local originals are retained.

Only a complete run may print:

```text
UPLOAD VERIFIED: 10/10 (AmeriFlux Batch 05). Originals retained. No extraction or model jobs started.
```

Publication of these scripts is **not** evidence that transfer succeeded. Record actual sizes/checksums and operator output after the run. No extraction, forcing repair, DATM, surface generation or Slurm submission occurs in Stage00.

## Stage00 operator result — 10/10 VERIFIED

The operator supplied the final successful upload line on 2026-10-25. See the [transfer evidence ledger](docs/STAGE00_TRANSFER_VERIFIED_2026-10-25.md). The visible excerpt contains sizes and SHA256 for the last four sites; no hashes for the first six are invented. Stage01 records the SHA256 of each source ZIP in its own new inventory report.

## Stage01 — run on IRIDIS6

[Extraction script](scripts/stage01/01_extract_ameriflux_batch05.py), adapted from Batch04. It requires only Python 3's standard library, validates the exact ten-site release manifest, extracts CSV products (including nested ZIPs), checks destination size/CRC, skips identical existing outputs and refuses to overwrite different CSVs. Original packages remain intact.

US-UMB is explicitly inventoried as FULLSET, separately from FLUXMET. Missing BIF or separate ERA5 companions for FULLSET are reported as metadata/source gaps for subsequent investigation. Both HH and HR products are preserved; filenames are not proof of actual cadence. This stage checks headers and the first row only; full time continuity, variable units, source QC, metadata and meteorological science remain later work.

Execute on IRIDIS6, after the successful Stage00 upload:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch05'
  BASE="$HOME/ameriflux_batch05_stage01"

  mkdir -p "$BASE/scripts/stage01"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"

  SCRIPT="$BASE/scripts/stage01/01_extract_ameriflux_batch05.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage01/01_extract_ameriflux_batch05.py" -o "$SCRIPT"

  python3 -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 |
    tee "$BASE/stage01_$(date +%Y%m%d_%H%M%S).log"
)
```

Success ends with `BATCH05 SUMMARY: 10/10 PASS (extraction/structure only); failures: none` and a `REPORT:` path. Operator execution now passed 10/10; see the [Stage01 evidence ledger](docs/STAGE01_EXTRACTION_VERIFIED_2026-10-25.md).

Extracted CSVs: `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/raw/<EXACT-PACKAGE>/`.

New timestamped JSON inventory: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch05/reports/stage01_extraction_*.json`.

Optional CLI: `--audit-only` (no extraction/report writes), `--sites US-UMB`, `--sites-root PATH`, `--reports-dir PATH`. Self-test uses synthetic temporary archives only and checks nested ZIPs, FULLSET/FLUXMET, HH/HR labels, reruns, overwrite refusal and unchanged source ZIP SHA256s. No forcing, DATM, CIME or Slurm jobs are created in Stage01.

## Stage02 — original metadata, complete HH/HR chronology and basic met screen

[Stage02 read-only auditor](scripts/stage02/02_audit_batch05_metadata_time_met.py) is locally tested on all ten synthetic release layouts, including FULLSET without BIF and an hourly source. It has not yet executed against the actual IRIDIS6 source files.

It validates the exact Batch05 manifest; inventories original BIF coordinate/location groups, IGBP and height records; scans every native FLUXMET or FULLSET HH/HR record for malformed timestamps, durations, gaps, overlaps and missing values; records source CSV SHA256s, field names, source QC counts, extremes and up to three timestamped examples per flag. Conflicting coordinate candidates are retained for review; no coordinate is selected for model inputs. If BIF is absent (possible for FULLSET), it still scans the site's full meteorology series and marks metadata for follow-up. All available HH/HR files are scanned; none is automatically chosen as forcing.

Screening assumptions are explicitly TA in degC, VPD in hPa, PA in kPa and RH in percent. Derived RH uses a water-saturation formula only; subzero water/ice cases and release-specific units need later verification before repair. Source labels and original QC are reported, not treated as independent ERA validation. Threshold flags are evidence for later work, not automatic replacement decisions. Full native Gregorian chronology is preserved, including leap days; no NO_LEAP conversion or time-zone shift occurs. Label-year boundary differences are printed separately from internal continuity.

Run on IRIDIS6:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch05'
  BASE="$HOME/ameriflux_batch05_stage02"

  mkdir -p "$BASE/scripts/stage02"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"

  SCRIPT="$BASE/scripts/stage02/02_audit_batch05_metadata_time_met.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage02/02_audit_batch05_metadata_time_met.py" -o "$SCRIPT"

  printf '%s  %s\n' \
    'eb16d333f515cb85500aca0f1b384af0c2fa3204ec64bad02ec48d55cad6b199' "$BASE/sites.tsv" \
    'fc3caa5ca8589aae2369f5343efa25dd71e65ac0b3d7ae7db7c8d19343d20402' "$SCRIPT" |
    sha256sum -c -

  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 |
    tee "$BASE/stage02_$(date +%Y%m%d_%H%M%S).log"
)
```

The audit itself writes no files. Shell `tee` saves its output under `$HOME/ameriflux_batch05_stage02/`. A normal completion prints `STAGE02 SUMMARY` with separate time, metadata and science review lists. Review flags are findings; exceptions produce `failed=` entries and a nonzero exit. Time PASS is internal chronology only; compare the separately printed label-boundary screen. Missing coordinates, IGBP or physical anomalies do not silently become approved inputs. Use `--sites US-UMB` for a focused rerun. No meteorological repairs, downloaded reanalysis, surfaces, DATM, PFT/ZBOT choices or model jobs are produced.
