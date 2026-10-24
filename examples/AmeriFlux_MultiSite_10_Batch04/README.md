# AmeriFlux MultiSite 10 — Batch 04

> **Operational status (2026-10-24): STAGE00 + STAGE01 VERIFIED (10/10 sites each) from operator logs.** SHA256-protected original ZIPs are documented in the [Stage00 integrity ledger](docs/STAGE00_TRANSFER_VERIFIED_2026-10-24.md); all ten release packages extracted 16 CSVs each with 0 structural failures in the [Stage01 results](docs/STAGE01_EXTRACTION_VERIFIED_2026-10-24.md). **Stage02 post-approval 10/10 PASS verified on IRIDIS6; US-Seg approved BIF GROUP_ID 1495 coordinates/elevation validated.** See [final Stage02 results](docs/STAGE02_POST_APPROVAL_VERIFIED_2026-10-24.md). See [Stage02 evidence](docs/STAGE02_METADATA_PREFLIGHT_2026-10-24.md). [Stage02B US-Seg diagnostic](scripts/stage02/02b_diagnose_US_Seg_coordinate_conflicts.py) has been executed. Paired BIF GROUP_ID 1479 vs 1495 evidence is documented in the [Stage02B ledger](docs/STAGE02B_US_SEG_PROVENANCE_VERIFIED_2026-10-24.md); The [human-approved decision](docs/STAGE02_US_SEG_GROUP1495_USER_APPROVAL_2026-10-24.md) is latitude 34.3623, longitude -106.7020 and elevation 1596 m. Stage02C full-HH timestamp audit **completed 10/10 PASS**, with scientific QC concerns preserved in the [Stage02C report](docs/STAGE02C_FULL_HH_TIME_QC_AUDIT_2026-10-24.md). No scientific forcing repairs, DATM inputs, surface/PFT decisions, CIME cases or spin-ups are approved.

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

## Stage01 — Extraction and structure inventory (Stage00 has now passed)

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

## Stage02 — APPROVED AND REVERIFIED (10/10 PASS)

Batch04 Stage02 follows the Batch03 metadata preflight, with one **explicit user-approved coordinate exception** in [coordinate_decisions.tsv](coordinate_decisions.tsv): **US-Seg original BIF GROUP_ID 1495, latitude 34.3623, longitude -106.7020, elevation 1596 m, LOCATION_DATE_START 200701010000**. Script verifies the exact BIF group pairing and elevation/date before accepting. The other nine sites still require unambiguous original BIF locations; no general fallback or silent coordinate guessing. IGBP and FATES PFT/height selections remain independently unapproved.

On the **IRIDIS6 login terminal**, run:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch04'
  BASE="$HOME/ameriflux_batch04_stage02"
  mkdir -p "$BASE/scripts/stage02"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  curl -fLsS --retry 3 "$RAW/$REL/coordinate_decisions.tsv" -o "$BASE/coordinate_decisions.tsv"
  SCRIPT="$BASE/scripts/stage02/02_check_batch04_metadata.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage02/02_check_batch04_metadata.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage02_$(date +%Y%m%d_%H%M%S).log"
)
```

This script **does not write any output** itself. The shell `tee` saves an external operator log. The operator **reran the revised checker** successfully: `STAGE02 SUMMARY: 10/10 coordinate + first-interval checks PASS; failures: none`. Final execution details are in [Stage02 post-approval verification](docs/STAGE02_POST_APPROVAL_VERIFIED_2026-10-24.md). The historical 9/10 before approval remains in the [original evidence](docs/STAGE02_METADATA_PREFLIGHT_2026-10-24.md). Investigate exclusions (WET/CRO/WAT), non-forest PFT applicability, sensor-to-TA mapping and time continuity in later independent scientific stages.

## Stage02B — US-Seg coordinate provenance (completed; approval recorded)

The original US-Seg BIF contains latitude `34.3623`, longitude candidates `-106.7020` and `-106.7019`. These longitudes are only about 9.18 m apart, but the currently published AmeriFlux site point is `34.3603, -106.7003`, roughly 267–272 m from these BIF candidates. The [research team site](https://www.litvaklab.org/grassland---us-seg.html) lists `34.3623, -106.7019`. The source mismatch has been investigated; the operator has now **explicitly selected original BIF GROUP_ID 1495**. The decision is recorded in [the approval ledger](docs/STAGE02_US_SEG_GROUP1495_USER_APPROVAL_2026-10-24.md). Other reference points are retained only for provenance and are not used in the approved site location.

Run **on IRIDIS6** after Stage02; the diagnostic is read-only:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage02"
  mkdir -p "$BASE/scripts/stage02"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage02/02b_diagnose_US_Seg_coordinate_conflicts.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage02/02b_diagnose_US_Seg_coordinate_conflicts.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage02b_US_Seg_$(date +%Y%m%d_%H%M%S).log"
)
```

The original Stage02 result was 9/10; the explicit location approval is now documented, but **the revised read-only Stage02 checker has now passed 10/10 on IRIDIS6**. External points remain historical references only, not selected coordinates.

## Stage02C — full HH time-series and basic scientific flags (READ ONLY)

[Stage02C script](scripts/stage02/02c_audit_batch04_HH_time_coverage.py) **was executed by the operator: time_pass=10, review=none, failed=none**. See [full HH results and QC HOLD report](docs/STAGE02C_FULL_HH_TIME_QC_AUDIT_2026-10-24.md). It checks all 10 original `FLUXMET_HH` series for full chronological continuity, malformed timestamps, non-30-minute intervals, gaps and overlaps, plus missing/available counts for basic named meteorological fields and review-only negative VPD/RH/PA/wind/precipitation diagnostics. Variables not present under the explicit names are marked `NOT_FOUND`, not silently inferred. **It does not approve or apply repairs**, shift UTC, choose US-Seg coordinates or create model jobs.

On IRIDIS6, run:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage02"
  mkdir -p "$BASE/scripts/stage02"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage02/02c_audit_batch04_HH_time_coverage.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage02/02c_audit_batch04_HH_time_coverage.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage02c_HH_$(date +%Y%m%d_%H%M%S).log"
)
```

For a smaller audit use `python3 -B "$SCRIPT" --sites US-Rpf US-Seg`. The `STAGE02C SUMMARY` indicates timestamp gates, **not** full scientific QC. No file writes occur inside the Python audit; shell `tee` creates only an operator log.

## Stage03 — timestamped extreme meteorology and same-label ERA5 comparison (READ ONLY)

**Prepared, not executed.** The [Stage03 script](scripts/stage03/03_audit_batch04_extreme_met_and_ERA5.py) reports every station's counts and top-eight most extreme timestamped examples per category for `TA_F < -80 °C`, `TA_F > 60 °C`, `PA_F <= 0`, `PA_F < 50 kPa`, `PA_F > 115 kPa`, `RH < 1%`, `1% <= RH < 5%`, `RH > 100%` and `VPD_F < 0`. It prints native values, available original native QC columns, derived `RH(TA_F,VPD_F)` for valid tower values, and **only exact raw string timestamp-label matched** ERA5 HH variables if present. It never changes inputs, makes UTC assumptions, adopts external station coordinates or combines unrelated-source ERA variables to produce humidity/forcing.

For a first targeted audit on US-SP1, US-Syv and US-Ton, run on **IRIDIS6**:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage03"
  mkdir -p "$BASE/scripts/stage03"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage03/03_audit_batch04_extreme_met_and_ERA5.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage03/03_audit_batch04_extreme_met_and_ERA5.py" -o "$SCRIPT"
  python3 -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --sites US-SP1 US-Syv US-Ton \\
    2>&1 | tee "$BASE/stage03_priority_$(date +%Y%m%d_%H%M%S).log"
)
```

For all ten sites later, omit the `--sites` argument. The Stage03 output is a **read-only scientific screening, not a repair ledger or production approval**. Exact raw timestamp-label matches do not by themselves establish time-zone equivalence, forcing units, or a permitted replacement. Review events manually before any ERA5 repairs.

## Scientific gates outstanding after structural/timestamp preflight

1. Inventory each site's actual BIF, FLUXMET, FLUXES and companion products and native HH versus HR cadence, time zone, timestamp continuity and actual year coverage.
2. Audit tower-specific coordinates, vegetation/PFT evidence and instrument/measurement heights. Do not assign tower vegetation or ZBOT from coarse IGBP or unverified sensor layers.
3. Evaluate native sensor QC, implausible TA/VPD/RH/QBOT and wind/radiation records; any ERA5-Land replacements require source-level evidence, a repair ledger and explicit approval.
4. Perform the separately versioned QCv5 and Post-v5 verification gates before building DATM or submitting CLM-FATES spin-ups.

**Provenance:** the transfer script and extraction script are Batch04 adaptations of the Batch03 scripts, maintaining the same independent per-site package directory and dry-run/no-overwrite safeguards. Do not copy scientific acceptance outcomes from earlier batches to these ten new sites.
