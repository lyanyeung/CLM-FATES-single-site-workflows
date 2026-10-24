# AmeriFlux MultiSite 10 — Batch 04

> **Operational status (2026-10-24): Stage00–02 structural metadata 10/10 PASS, Stage02C HH continuity 10/10 PASS; Stage04 3/3 targeted diagnostics PASS; Stage05/06 3-site candidate and physical audits PASS; Stage07 3 full derived CSVs WRITTEN (376 exact-time ERA5 VPD replacements, 1,566 US-Ton QC0 native readings protected); Stage08 7/7 full derived CSVs VERIFIED (416 patch rows / 696 HOLD); 10/10 complete candidate FLUXMET files generated; Stage09 zero repairs VERIFIED; Stage10 689/689 ERA5-Land fixes SUCCESS; Stage11 latest-ten manifest VERIFIED 10/10; Stage12 155 non-US-Syv science holds and 2 SP1 jump exceptions ready, not yet run.** SHA256-protected original ZIPs are documented in the [Stage00 integrity ledger](docs/STAGE00_TRANSFER_VERIFIED_2026-10-24.md); all ten release packages extracted 16 CSVs each with 0 structural failures in the [Stage01 results](docs/STAGE01_EXTRACTION_VERIFIED_2026-10-24.md). **Stage02 post-approval 10/10 PASS verified on IRIDIS6; US-Seg approved BIF GROUP_ID 1495 coordinates/elevation validated.** See [final Stage02 results](docs/STAGE02_POST_APPROVAL_VERIFIED_2026-10-24.md). See [Stage02 evidence](docs/STAGE02_METADATA_PREFLIGHT_2026-10-24.md). [Stage02B US-Seg diagnostic](scripts/stage02/02b_diagnose_US_Seg_coordinate_conflicts.py) has been executed. Paired BIF GROUP_ID 1479 vs 1495 evidence is documented in the [Stage02B ledger](docs/STAGE02B_US_SEG_PROVENANCE_VERIFIED_2026-10-24.md); The [human-approved decision](docs/STAGE02_US_SEG_GROUP1495_USER_APPROVAL_2026-10-24.md) is latitude 34.3623, longitude -106.7020 and elevation 1596 m. Stage02C full-HH timestamp audit **completed 10/10 PASS**, with scientific QC concerns preserved in the [Stage02C report](docs/STAGE02C_FULL_HH_TIME_QC_AUDIT_2026-10-24.md). No scientific forcing repairs, DATM inputs, surface/PFT decisions, CIME cases or spin-ups are approved.

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

**Prepared and executed for 3/10 priority stations; remaining seven not executed.** The [Stage03 script](scripts/stage03/03_audit_batch04_extreme_met_and_ERA5.py) reports every station's counts and top-eight most extreme timestamped examples per category for `TA_F < -80 °C`, `TA_F > 60 °C`, `PA_F <= 0`, `PA_F < 50 kPa`, `PA_F > 115 kPa`, `RH < 1%`, `1% <= RH < 5%`, `RH > 100%` and `VPD_F < 0`. It prints native values, available original native QC columns, derived `RH(TA_F,VPD_F)` for valid tower values, and **only exact raw string timestamp-label matched** ERA5 HH variables if present. It never changes inputs, makes UTC assumptions, adopts external station coordinates or combines unrelated-source ERA variables to produce humidity/forcing.

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
  python3 -B "$SCRIPT" --sites US-SP1 US-Syv US-Ton
    2>&1 | tee "$BASE/stage03_priority_$(date +%Y%m%d_%H%M%S).log"
)
```

For all ten sites later, omit the `--sites` argument. The Stage03 output is a **read-only scientific screening, not a repair ledger or production approval**. Exact raw timestamp-label matches do not by themselves establish time-zone equivalence, forcing units, or a permitted replacement. Review events manually before any ERA5 repairs.

## Stage03 priority execution — 3/3 site science HOLD (2026-10-24)

The operator executed the initial Stage03 diagnostic for `US-SP1 US-Syv US-Ton`: `flagged=US-SP1,US-Syv,US-Ton none_of_selected_flags=none failed=none`. Actual event counts, timestamps and source values are documented in the [Stage03 priority ledger](docs/STAGE03_PRIORITY_MET_ERA_DIAG_2026-10-24.md).

**Important correction:** packaged `ERA5_HH` columns `TA_ERA` and `PA_ERA` should not be assumed to be physically independent unadjusted ERA5 reanalysis. The standard FLUXNET naming system denotes `*_ERA` as **downscaled/calibrated ERA-derived products**, while `*_F` consolidates tower and ERA-derived values. For example `PA_F_QC=2` denotes an ERA-downscaled fallback (see [FLUXNET variable codes](https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/)). v1.3 has updated ONEFlux processing, so further details must be verified from its own BIFVARINFO metadata. `PA_F=PA_ERA` can thus reflect product lineage rather than independent confirmation. Anomalous `TA_ERA` values of -243 to -271 °C at flagged rows make blind replacement scientifically unsafe.

The Stage03 script also supports `--sites US-Rpf US-Seg US-Ses US-Slt US-SRG US-SRM US-Uaf` for the remaining seven stations. **No repair policy is approved**.

## Stage04 — focused source lineage and neighbour checks (READ ONLY; not executed)

New script: [04_trace_batch04_meteorology_ERA_neighbours.py](scripts/stage04/04_trace_batch04_meteorology_ERA_neighbours.py).

Stage04 inspects exactly selected extreme time windows with two original half-hours on each side for US-SP1, US-Syv and US-Ton. It reports native `TA`, `TA_F_MDS`, `TA_F`, `TA_ERA`, `PA`, `PA_F`, `PA_ERA`, `VPD`, `VPD_F`, `VPD_ERA`, `RH` and available QC columns alongside **time-label matching** packaged ERA5 variables. It flags exact equality but never considers equality independent validation.

Run on IRIDIS6:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage04"
  mkdir -p "$BASE/scripts/stage04"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage04/04_trace_batch04_meteorology_ERA_neighbours.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage04/04_trace_batch04_meteorology_ERA_neighbours.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage04_neighbours_$(date +%Y%m%d_%H%M%S).log"
)
```

No original file, forcing, temperature, vapor or pressure values are modified. An external, independently retrieved ERA5/ERA5-Land meteorology source with independently validated units, times and spatial interpolation must be reviewed before authorizing per-timestamp substitutions.

## Stage04 operator verified / Stage05 QCv5 candidate repair builder

The operator ran Stage04 self-test and checked all three priority sites: `STAGE04 SUMMARY: examined=3/3 failed=none`. See [Stage04 evidence, previous QCv5 policy and explicit user repair instruction](docs/STAGE04_VERIFIED_AND_STAGE05_QCV5_APPROVED_METHOD_2026-10-24.md).

The user explicitly selected the historical QCv5 short-gap interpolation for obvious `TA_F`/`PA_F` outliers and ERA-based humidity reconstruction for problematic `RH`. We therefore published an **isolated candidate builder**, [Stage05](scripts/stage05/05_build_batch04_qcv5_repair_candidates.py) (prepared, not yet executed on IRIDIS6). It is strictly scoped to `US-SP1 US-Syv US-Ton`, uses only the original exact FLUXMET and packaged ERA5 products, and follows the historic `TA_F/PA_F/VPD_F` 4-HH (2-hour) **complete-run** interpolation cap. The 2004 and 2016 multi-row pressure pulses are detected as `PA_F<65 kPa` so the 49–51 kPa shoulders are not silently preserved. A single `TA_F=0,VPD_F=6.110,RH=0` joint anomaly is separately identified. With a physically valid **same-source** `TA_ERA,VPD_ERA,PA_ERA` pair and `|TA_tower-TA_ERA|<=8°C`, suspect `RH<5%` or `RH>100%` is estimated from ERA source humidity **at preserved tower temperature**, with corresponding `VPD_F` changed consistently.

This is NOT a blanket RH replacement: isolated low-RH values can be physically plausible, subzero humidity phase definitions require review, and the packaged ERA-derived products contain documented absurd values in some windows. Invalid ERA cases are routed to `unresolved_hold.csv`, not patched. Missing raw RH alone is not an error if consolidated TA/VPD/PA are usable. No native CSV, archived source, existing case or DATM is altered.

**IRIDIS6 command — first inspect, then write isolated sparse candidate and hold ledgers:**

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage05"
  mkdir -p "$BASE/scripts/stage05"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage05/05_build_batch04_qcv5_repair_candidates.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage05/05_build_batch04_qcv5_repair_candidates.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage05_preview_$(date +%Y%m%d_%H%M%S).log"
  python3 -B "$SCRIPT" --build-candidates \
    2>&1 | tee "$BASE/stage05_build_$(date +%Y%m%d_%H%M%S).log"
)
```

By default the **build** creates a new, never-overwritten directory under `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage05_candidates/`, containing sparse `candidate_patch.csv` and `unresolved_hold.csv` plus SHA256-pinned `report.json`. The script is NOT a complete processed forcing dataset; a separately audited patch materialisation and Post-v5 gate are required before model forcing may use the overlay. Continue full Stage03 review on the other seven sites.

## Stage05 — QCv5 research candidates actually built (2026-10-24)

Stage05 **self-test PASS; preview PASS; `--build-candidates` PASS on IRIDIS6**, priority **3/3** stations (US-SP1, US-Syv, US-Ton), no runtime failures and no original file edits. **5,336 variable-level candidate patch entries** consist of **16 local TA/PA interpolation/joint-zero entries** and **2,660 humidity times × 2 RH+VPD fields = 5,320 entries**. **754 HOLD rows** remain (US-SP1 147, US-Syv 606, US-Ton 1). Original FLUXMET HH rows scanned in this targeted pass total **1,244,784**. Exact counts, science caveats and the source output location are in [Stage05 operator-verified execution record](docs/STAGE05_VERIFIED_3_SITE_QCV5_CANDIDATE_BUILD_2026-10-24.md).

**Created operator output on IRIDIS6:**
```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage05_candidates/candidate_20261024T103113Z/
```

Stage05 generated *sparse repairs*, not `processed_v5` model forcing; the files are `candidate_patch.csv`, `unresolved_hold.csv`, `report.json` and `README.txt`. The 754 unresolved cases are predominantly US-Syv ERA humidity pair/temperature-screen failures. They are **not** silently replaced from invalid `*_ERA` values. The FLUXNET source and all other site files remain immutable. **Post-v5, DATM and spin-up remain unapproved.**

## Stage06 — source SHA, paired humidity physics and new VPD jump audit (READY, NOT EXECUTED)

[06_audit_batch04_qcv5_candidate_effects.py](scripts/stage06/06_audit_batch04_qcv5_candidate_effects.py) reads exactly the previously generated Stage05 candidate version, checks `report.json` origin SHA256, confirms per-site 87/534/4715 patch rows and 147/606/1 holds, independently reconciles each sparse candidate with original native source half-hours and ERA-RH/VPD thermodynamics at **retained site temperature**, counts cold temperature/source-QC0 changes, and flags **new VPD half-hour jumps greater than 4 hPa or increasing by more than 2 hPa**. The thresholds are *review flags*, not invalidity proofs and never trigger automatic smoothing. Failures halt without modifying candidates.

On IRIDIS6 first run `--check`, and then optionally `--run` for **new reports only**:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage06"
  mkdir -p "$BASE/scripts/stage06"
  SCRIPT="$BASE/scripts/stage06/06_audit_batch04_qcv5_candidate_effects.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage06/06_audit_batch04_qcv5_candidate_effects.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --check 2>&1 | tee "$BASE/stage06_check.log"
  python3 -B "$SCRIPT" --run 2>&1 | tee "$BASE/stage06_report.log"
)
```

Stage06 reports go into a new `reports/stage06_qcv5_candidate_effects_*` folder with SHA receipts and a boundary review list, without editing original or Stage05 files. **No production sparse-patch merge before the 754 HOLDs and boundary/physical QC have been resolved and seven remaining Batch04 sites have completed appropriate scientific screening.**

## Stage11 operator VERIFIED / Stage12 active non-Syv fixes (2026-10-25)

**Stage11 operator result VERIFIED:** all 10 latest complete derived FLUXMET HH source files SHA-checked, full CSVs not duplicated, new `LATEST_10_SITES_FOR_POSTV5_INPUT.tsv` written:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage11_latest_ten_manifest/candidate_20261024T232100Z_1c6ef02a/LATEST_10_SITES_FOR_POSTV5_INPUT.tsv`.

Current source selection: Stage07 3 sites, Stage08 5 sites, Stage10 2 sites; 689/689 previous Rpf/SRM humidity faults are resolved. The old science HOLD ledger still has **761 entries**: **606 US-Syv deferred** and **155 other sites** (US-SP1 147; US-Seg 4; US-Uaf 2; US-SRG 1; US-Ton 1), plus up to 12 Stage07 skipped ERA jump-edge event timestamps which may overlap old HOLDs (2 SP1, 10 Syv).

**Next Stage12**: [source-repair script](scripts/stage12/12_repair_non_syv_science_holds.py) with [method and progress record](docs/STAGE11_VERIFIED_AND_STAGE12_NON_SYV_2026-10-25.md). It targets the 155 non-Syv old holds plus two SP1 missed jump-edge timestamps. It retains physically consistent original tower temperature/VPD wherever corroborated by trustworthy neighbouring native measurements and acquires **independent ERA5-Land** hourly T2m/dewpoint/surface pressure at precisely BIF located and local-standard UTC-offset-aligned years where source VPD is invalid or a high-jump edge was not repaired. It uses the pinned Stage10 helper to recover/download NetCDF. It creates new complete derived CSVs **only for actually modified sites**, a new latest-ten-site TSV, resolved/unresolved decision ledger and SHA receipt. US-Syv not touched. Any ambiguous original BIF holds only its site.

To run on IRIDIS6, download BOTH scripts beside each other (Stage12 imports Stage10 helper by filename):

```bash
(
  set -euo pipefail
  REPO="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  BASE="$HOME/ameriflux_batch04_stage12"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$REPO/c3a44684134a6a50e4086543301adc05e66365d9/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage12/12_repair_non_syv_science_holds.py" -o "$BASE/12_repair_non_syv_science_holds.py"
  curl -fLsS --retry 3 "$REPO/b8ff0c2aaf41683d70bb94e9d70715c25c5eea45/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage10/10_era5land_independent_humidity_fill.py" -o "$BASE/10_era5land_independent_humidity_fill.py"
  python3 -B -m py_compile "$BASE/12_repair_non_syv_science_holds.py"
  python3 -B "$BASE/12_repair_non_syv_science_holds.py" --self-test
  python3 -B "$BASE/12_repair_non_syv_science_holds.py" --run --max-downloads 3 2>&1 | tee "$BASE/stage12_run.log"
)
```

Stage12 is **committed but not yet executed**. Its actual science repair counts are to be established by the IRIDIS6 operator output; model-ready Post-v5, DATM and spinup remain unapproved.

## Batch04 Stage10 VERIFIED 689/689; Stage11 ten-site latest-source selection ready

Operator IRIDIS6 confirmed Stage10 successful **689/689 independent ERA5-Land source VPD repairs** (US-Rpf **688**, US-SRM **1**, remaining **0**). Original BIF station points/UTC_OFFSET were used, and source hourly T2m/D2m/SP was physically screened; the previously partial US-Rpf 2022 NetCDF was recovered and reused with a SHA receipt, while US-SRM 2023 was successfully downloaded from CDS.

**Latest complete independent ERA5-Land candidate files** (no original input overwrite):
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage10_independent_era5land/candidate_20261024T231424Z_d9967326`.

[Stage10 689/689 operator-verified result, receipts and remaining external gates](docs/STAGE10_VERIFIED_689_OF_689_ERA5LAND_REPAIR_2026-10-25.md).

**Stage11 (new executable, NOT run on IRIDIS6):** [11_register_latest_ten_derived_forcing_candidates.py](scripts/stage11/11_register_latest_ten_derived_forcing_candidates.py) builds **one precise 10-site data selection TSV**, SHA-checks the complete derived FLUXMET HH source files and selects the *latest* actual data:
- **3 from Stage07:** US-SP1, US-Syv, US-Ton
- **5 from Stage08:** US-Seg, US-Ses, US-Slt, US-SRG, US-Uaf
- **2 from Stage10:** US-Rpf, US-SRM

It does not duplicate millions of NetCDF/CSV source records or overwrite anything. It keeps remaining scientific decisions separate: **754 Stage05 original three-site HOLD entries + 7 Stage08 non-Rpf/SRM HOLD entries = 761**; **12 additional Stage07 skipped ERA jump endpoints may overlap** existing holds. These are *not* 689 newly unresolved Stage10 events, all of which were repaired. US-Syv remains deferred per explicit user instruction.

Run Stage11 on IRIDIS6:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/d9b8a6f66c844514249b71c9daa27e6ede7c6c6a"
  BASE="$HOME/ameriflux_batch04_stage11"
  SCRIPT="$BASE/11_register_latest_ten_derived_forcing_candidates.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage11/11_register_latest_ten_derived_forcing_candidates.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --build 2>&1 | tee "$BASE/stage11_build.log"
)
```

The manifest output `qcv5_stage11_latest_ten_manifest/candidate_*/LATEST_10_SITES_FOR_POSTV5_INPUT.tsv` is a **version-pinned input selection, NOT Post-v5-approved production forcing**. The model/DATM transition requires separate validation and unresolved science-gate resolution.

## Stage10 BIF verified; three external site-years present; safely resume missing two (2026-10-24)

Stage10 reached its first CDS download after a successful self-test. Original BIF readings are unambiguous: US-Rpf **65.1198°N, -147.429°, UTC_OFFSET -9** and US-SRM **31.8214°N, -110.8661°, UTC_OFFSET -7**. The operator's 689 exact target HH timestamps fall into only **five site-years**: US-Rpf 2024 (390), 2008 (218), 2021 (69), 2022 (11), US-SRM 2023 (1). The first **three have existing SHA receipts**; US-Rpf 2022 has a saved `.download.partial`, and US-SRM 2023 needs a new retrieval.

The old `FileExistsError` is a safety guard that stopped a potential overwrite of US-Rpf 2022's earlier partial response. **No Stage10 derived repairs are confirmed yet.** [Fixed Stage10](scripts/stage10/10_era5land_independent_humidity_fill.py) first verifies and reuses a complete previous partial (or isolatedly preserves a failed one and retries); it never deletes original data, and only then obtains missing years and creates new **full native-length** source-derived CSVs.

Read the [Stage10 interrupted partial provenance and fix](docs/STAGE10_INTERRUPTED_CDS_PARTIAL_RESUME_2026-10-24.md). On IRIDIS6, re-download the pinned source from commit `b8ff0c2aaf41683d70bb94e9d70715c25c5eea45` and run `--run --max-downloads 2`. Existing 3 year receipts are preserved, and at most 2 new CDS requests are needed (or 1 if the pre-existing 2022 partial verifies).

## Stage09 VERIFIED (zero source repairs) / Stage10 independent ERA5-Land next

The operator completed Stage09 (`--self-test` and `--apply`) on IRIDIS6, generated two complete source-length derived CSVs, **0 new patches**, and preserved all **696 Stage08 HOLDs**. **US-Rpf 688/688** and **US-SRM 1/1** source-native VPD samples in the ERA-physics HOLDs are themselves physically invalid and cannot be safely rescued by max-four-HH original-tower interpolation. The repeated Stage09 source-CSV SHA256 matches Stage08 unchanged files.

[Stage09 VERIFIED and Stage10 CDS replacement method](docs/STAGE09_VERIFIED_ZERO_REPAIRS_AND_STAGE10_INDEPENDENT_ERA5LAND_2026-10-24.md).

**Next runnable Stage10 program:** [10_era5land_independent_humidity_fill.py](scripts/stage10/10_era5land_independent_humidity_fill.py), **not yet run on IRIDIS6**. It reads original BIF coordinates/UTC_OFFSET for US-Rpf and US-SRM (never hardcodes an invented location), groups the **689** exact blocked native timestamps by year, automatically retrieves at most **3 targeted CDS ERA5-Land point/year responses** per run, verifies each NetCDF time/units/physical data and SHA receipt, transfers gridded dewpoint-derived RH to retained tower temperature and directly creates **two new complete derived FLUXMET HH candidate CSVs** for all successfully repaired time points. Unavailable grid years or invalid source temperature/pressure remain HOLD. No production, DATM, CIME or Slurm operations.

Run after CDS credentials `~/.cdsapirc` and `cdsapi,numpy,netCDF4` are configured:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/b8ff0c2aaf41683d70bb94e9d70715c25c5eea45"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage10"
  SCRIPT="$BASE/scripts/stage10/10_era5land_independent_humidity_fill.py"
  mkdir -p "$(dirname "$SCRIPT")"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage10/10_era5land_independent_humidity_fill.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --run --max-downloads 3 2>&1 | tee "$BASE/stage10_run.log"
)
```

If some site-years remain after the first run, run the same `--run` again. Use `--apply-existing` to generate full derived files from already-verified grid evidence without more CDS requests. All Stage10 results remain incomplete research data until unresolved scientific issues are settled.

## Stage08 success and Stage09 next direct native-VPD fixes (2026-10-24)

**Stage08 VERIFIED 7/7:** `US-Rpf, US-Seg, US-Ses, US-Slt, US-SRG, US-SRM, US-Uaf` have complete derived FLUXMET_HH CSVs. 2,384,448 original native half-hours were copied; exactly 208 half-hours in five sites received 416 RH/VPD variable-level patches. US-Rpf and US-Slt had no modified source values. Stage08 has **696 HOLD** records (US-Rpf 688, US-Seg 4, US-SRG 1, US-SRM 1, US-Uaf 2; US-Ses and US-Slt zero). See [Stage08 verified SHA receipt summary](docs/STAGE08_VERIFIED_SEVEN_SITE_DERIVED_CSVS_2026-10-24.md).

**Actual Stage08 output:** `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage08_remaining_seven_candidates/candidate_20261024T120137Z/`.

**10/10 Batch04 site candidates now exist**, combining three Stage07 and seven Stage08 complete derived CSVs. They are NOT yet Post-v5 approved forcing.

**Stage09 (ready, NOT run):** target **689** invalid paired ERA humidity HOLDs, including **688 US-Rpf + 1 US-SRM**, without touching the deferred US-Syv or any other site. Apply actual physically admissible short original tower VPD interpolations (maximum four half-hours, trustworthy original QC0/QC1 flank records) and derive RH when original VPD is already valid but separate RH is invalid. Long runs and physically implausible interpolations remain HOLD. The command creates **two new full derived source CSVs** (not merely a diagnostic report), retains all original/Stage08 file SHA receipts and never overwrites previous candidate directories.

[Stage09 code](scripts/stage09/09_repair_ERA_invalid_native_humidity_short_gaps.py) | [Stage09 approved approach and run](docs/STAGE09_US_RPF_SRM_DIRECT_NATIVE_HUMIDITY_REPAIR_2026-10-24.md).

Run on IRIDIS6:
```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/c794f403bac063092d17030d1939121fae3b94a9"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage09"
  SCRIPT="$BASE/scripts/stage09/09_repair_ERA_invalid_native_humidity_short_gaps.py"
  mkdir -p "$(dirname "$SCRIPT")"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage09/09_repair_ERA_invalid_native_humidity_short_gaps.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --apply 2>&1 | tee "$BASE/stage09_apply.log"
)
```

The 754 Stage05 inherited HOLDs at the three original priority sites (plus 12 Stage07 invalid direct ERA edge targets, possibly overlapping) remain separate. The Stage08 696 HOLD entries and any Stage09 survivors must not be silently ignored in future model forcing.

## Latest verified: Stage07 three complete site candidates DONE; Stage08 remaining seven prepared

**Stage07 IRIDIS6 execution verified on 2026-10-24.** Three complete native-length derived FLUXMET_HH files were written, with original Stage05/Stage06 inputs SHA-pinned and unchanged:

- **US-SP1:** 368,208 source rows; 32 direct same-time ERA5 VPD replacements; 62 actual rows changed; SHA256 `9390f88948eaf621b4e697682da701675f08330b268f3661d5a98cd130364b28`
- **US-Syv:** 438,288 rows; 12 direct ERA5 VPD replacements; 270 actual rows changed; SHA256 `5086cbc0f08f73b218d08fdcf34cf0643a6ae1ea95c05c200a98800452b5b32e`
- **US-Ton:** 438,288 rows; 332 direct ERA5 VPD replacements; 961 actual rows changed; SHA256 `4ca4467a7f6180136ef06c8595bb36d2f25ae5413c91cd357c5c0d84a99d5646`

**Totals:** 376 successful physical ERA5 VPD substitutions among 388 distinct Stage06 jump-endpoint times; 12 unsuccessful exact-source cases remain skipped/HOLD. **1,566** physically plausible native US-Ton QC0 samples preserved against other Stage05 proposed overrides. 1,293 unique native rows changed in derived full CSVs. 754 Stage05 HOLD entries carried forward and may overlap the 12 new skip entries. Verified output:

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage07_applied/candidate_20261024T114538Z_6a6b36ba
```

[Stage07 verified output and SHA record](docs/STAGE07_VERIFIED_THREE_FULL_DERIVED_CSVS_2026-10-24.md). **This is a derived research candidate, not approved Post-v5/CIME/DATM spinup forcing.**

**Stage08 VERIFIED on IRIDIS6:** the [remaining seven-site script](scripts/stage08/08_build_remaining_seven_qcv5_candidates.py) was executed successfully for US-Rpf, US-Seg, US-Ses, US-Slt, US-SRG, US-SRM, US-Uaf. It extends the established Stage05 QCv5 max4-HH interpolation + physically screened same-time ERA RH method, but **protects physically plausible native VPD QC0 readings** and **does not treat positive RH<5% alone as an ERA replacement requirement**. It does not invent the US-Syv one-off joint-zero TA fix for other sites. A source RH column is optional if missing in a particular FLUXMET release. It writes a new independent seven-site **complete derived FLUXMET_HH CSV per site** plus sparse candidates and HOLD ledger, original source SHA receipts, **no original or existing model edits**. The seven-site pipeline can advance without reopening the successful three-site Stage07 derived runs.

Execute:
```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/33770619bbc68e9030a70190ffe3c901beb2187f"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage08"
  SCRIPT="$BASE/scripts/stage08/08_build_remaining_seven_qcv5_candidates.py"
  mkdir -p "$(dirname "$SCRIPT")"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage08/08_build_remaining_seven_qcv5_candidates.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --build-candidates 2>&1 | tee "$BASE/stage08_build.log"
)
```
Output: new `qcv5_stage08_remaining_seven_candidates/candidate_*` folder with **seven complete derived FLUXMET_HH CSVs**, exact site source SHA256 + `candidate_patch.csv`, `unresolved_hold.csv`, `report.json` and INCOMPLETE research-candidate marker. Scientific warning: packaged ERA5 comes from the FLUXNET release and is not independent gridded ERA5-Land truth.

## Stage06 VERIFIED; Stage07 new full derived ERA5 VPD repair ready (2026-10-24)

Stage06 user execution: full original SHA checks, 5,336 Stage05 candidate variable patches and 754 holds VERIFIED; 210 flagged VPD jump edges (19 US-SP1; 12 US-Syv; 179 US-Ton), plus 2,259 original US-Ton QC0 VPD values potentially overwritten. Operator report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/reports/stage06_qcv5_candidate_effects_20261024T105030Z_8cc1f59c`.

**New user direction:** directly replace both endpoints of **these 210 flagged VPD jump edges** with **same-exact-native-timestamp packaged ERA5 `VPD_ERA`**, compute physically consistent derived RH at **retained EC tower temperature**, and create actual **three full-length derived FLUXMET HH CSVs** in a new isolated Stage07 version. Any nonphysical ERA VPD/pair is recorded as a skipped new HOLD; original native site VPD and stage05 source remain unchanged. **Outside the flagged edges**, protect original physically admissible US-Ton VPD QC0 and drop its previous Stage05 humidity overwrite. Defer the 419 bad US-Syv ERA pair cases.

[Stage07 script](scripts/stage07/07_apply_jump_ERA5_vpd_three_sites.py) | [Science method and executable shell command](docs/STAGE07_USER_APPROVED_DIRECT_ERA5_VPD_REPAIR_2026-10-24.md). The Stage07 Python code is **published but has not yet been run on IRIDIS6**. Only its user execution can confirm counts of valid vs invalid same-time ERA endpoints.

The paired FLUXNET `ERA5_HH` fields are downscaled ERA-derived data **not independently downloaded ERA5-Land**. Original ZIP/CSV, prior Stage05/06 results, `processed_v5`, DATM, CIME and Slurm jobs are not touched. Post-v5 model authorization remains withheld pending remaining scientific holds.

## Scientific gates outstanding after structural/timestamp preflight

1. Inventory each site's actual BIF, FLUXMET, FLUXES and companion products and native HH versus HR cadence, time zone, timestamp continuity and actual year coverage.
2. Audit tower-specific coordinates, vegetation/PFT evidence and instrument/measurement heights. Do not assign tower vegetation or ZBOT from coarse IGBP or unverified sensor layers.
3. Evaluate native sensor QC, implausible TA/VPD/RH/QBOT and wind/radiation records; any ERA5-Land replacements require source-level evidence, a repair ledger and explicit approval.
4. Perform the separately versioned QCv5 and Post-v5 verification gates before building DATM or submitting CLM-FATES spin-ups.

**Provenance:** the transfer script and extraction script are Batch04 adaptations of the Batch03 scripts, maintaining the same independent per-site package directory and dry-run/no-overwrite safeguards. Do not copy scientific acceptance outcomes from earlier batches to these ten new sites.
