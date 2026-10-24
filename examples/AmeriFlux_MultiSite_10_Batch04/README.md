# AmeriFlux MultiSite 10 — Batch 04

> **Operational status (2026-10-24): PREPARED, NOT YET VERIFIED ON IRIDIS6.** Stage00 and Stage01 code is published; this is not evidence that any original data have been uploaded or extracted. The operator must run the WSL command below and retain its output. No forcing modification, QC repair, DATM input, surface modification, CIME case or spin-up is approved by this preparation.

Fourth independent ten-site AmeriFlux campaign following [Batch03](../AmeriFlux_MultiSite_10_Batch03/), [Batch02](../AmeriFlux_MultiSite_10_Batch02/) and [Batch01](../AmeriFlux_MultiSite_10/). This directory contains the exact release manifest and reproducible scripts. Never commit raw tower ZIPs or derived large files to GitHub.

## Exact 10-site release manifest

| Site | Original archive name (expected) | Release-year labels |
| --- | --- | --- |
| US-Rpf | `AMF_US-Rpf_FLUXNET_2008-2024_v1.3_r1.zip` | 2008–2024 |
| US-Seg | `AMF_US-Seg_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-Ses | `AMF_US-Ses_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-Slt | `AMF_US-Slt_FLUXNET_2005-2022_v1.3_r1.zip` | 2005–2022 |
| US-SP1 | `AMF_US-SP1_FLUXNET_2000-2020_v1.3_r1.zip` | 2000–2020 |
| US-SRG | `AMF_US-SRG_FLUXNET_2008-2025_v1.3_r1.zip` | 2008–2025 |
| US-SRM | `AMF_US-SRM_FLUXNET_2004-2025_v1.3_r1.zip` | 2004–2025 |
| US-Syv | `AMF_US-Syv_FLUXNET_2001-2025_v1.3_r1.zip` | 2001–2025 |
| US-Ton | `AMF_US-Ton_FLUXNET_2001-2025_v1.3_r1.zip` | 2001–2025 |
| US-Uaf | `AMF_US-Uaf_FLUXNET_2003-2025_v1.3_r1.zip` | 2003–2025 |

Machine-readable manifest: [sites.tsv](sites.tsv). Year labels and FLUXNET release names are operator-provided identifiers, **not** independently verified station coverage, native cadence, measurement quality or land-cover/PFT assignment. Accept only an exact `<package>.zip` archive (case-insensitive extension) or an exact same-named release directory in the Windows source folder. ZIP takes priority when both exist. No renaming, repacking or altered year-range substitutions.

## Stage00 — Copy and SHA256-verify all original packages

**Run in your LOCAL WSL terminal, not on IRIDIS and not in native PowerShell.** Windows source: `D:\Fluxes_Tower_Experiment\Ameriflux`; WSL mount: `/mnt/d/Fluxes_Tower_Experiment/Ameriflux`.

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch04'
  BASE="$HOME/ameriflux_batch04_transfer"
  mkdir -p "$BASE/scripts/stage00"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage00/00_upload_ameriflux_batch04.sh"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage00/00_upload_ameriflux_batch04.sh" -o "$SCRIPT"
  bash -n "$SCRIPT"
  LOCAL_ROOT='/mnt/d/Fluxes_Tower_Experiment/Ameriflux' \
    bash "$SCRIPT" 2>&1 | tee "$BASE/upload_$(date +%Y%m%d_%H%M%S).log"
)
```

Requirements: Bash, `curl`, `ssh`, `rsync`, `sha256sum`, `find`, `awk`, `mktemp` and `head`. The script first preflights the **entire ten-site manifest** and refuses to connect if any source is missing. It then establishes **one SSH master session** to `ly3n24@iridis6.soton.ac.uk`; normal authentication may be required once. Later operations reuse only the master (batch mode, no fallback connection). Run again to resume an interrupted transfer. It neither changes nor deletes local originals.

Expected destination for each ZIP:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<US-SITE>/forcing/packages/<EXACT-PACKAGE>.zip
```

Same-named release directories, if provided instead of ZIP, go under `packages/<EXACT-PACKAGE>/`. Existing completed destination archives are preserved (`rsync --ignore-existing`); an existing different SHA256 is a **hard stop** rather than being replaced. ZIPs are verified end-to-end by local/remote SHA256; folders are checked with checksum-based `rsync --dry-run` including unexpected remote files. Source and destination package files are never deleted; any cleanup of temporary transfer files is managed by rsync.

**Do not report success unless the full output contains:**

```text
UPLOAD VERIFIED: 10/10 (AmeriFlux Batch 04). Originals retained. No extraction or model jobs started.
```

Store the WSL upload log outside GitHub; it contains actual sizes, SHA256 digests, SSH errors (if any) and the verified site tally. Confirm remote disk/inode quotas if transfers fail.

## Stage01 — Extraction and structure inventory (only AFTER Stage00 passes)

Stage01 script is ready at [scripts/stage01/01_extract_ameriflux_batch04.py](scripts/stage01/01_extract_ameriflux_batch04.py), adapted from Batch03. It extracts CSV products without altering original archives; recursively handles nested ZIPs; checks output CRC/size and inventory structure; records a timestamped JSON report. It does **not** approve site meteorology, produce forcing or submit model jobs.

To run only after a verified 10/10 upload, execute **on IRIDIS6**:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch04'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage01"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage01/01_extract_ameriflux_batch04.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage01/01_extract_ameriflux_batch04.py" -o "$SCRIPT"
  python3 -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" 2>&1 | tee "$HOME/AmeriFlux_Batch04_stage01_$(date +%Y%m%d_%H%M%S).log"
)
```

The Stage01 CLI also supports `--audit-only`, `--sites US-Rpf`, `--sites-root` and `--reports-dir`. Stage01 runs no Slurm jobs. Default output inventory location: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/reports/`.

## Scientific gates after extraction (not yet executed)

1. Inventory each site's actual BIF, FLUXMET, FLUXES and companion products and native HH versus HR cadence, time zone, timestamp continuity and actual year coverage.
2. Audit tower-specific coordinates, vegetation/PFT evidence and instrument/measurement heights. Do not assign tower vegetation or ZBOT from coarse IGBP or unverified sensor layers.
3. Evaluate native sensor QC, implausible TA/VPD/RH/QBOT and wind/radiation records; any ERA5-Land replacements require source-level evidence, a repair ledger and explicit approval.
4. Perform the separately versioned QCv5 and Post-v5 verification gates before building DATM or submitting CLM-FATES spin-ups.

**Provenance:** the transfer script and extraction script are Batch04 adaptations of the Batch03 scripts, maintaining the same independent per-site package directory and dry-run/no-overwrite safeguards. Do not copy scientific acceptance outcomes from earlier batches to these ten new sites.
