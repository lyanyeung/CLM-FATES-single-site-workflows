# AmeriFlux MultiSite 10 — Batch 05

**Status (2026-10-25): Stage00 upload/checksum 10/10 verified; Stage01 extraction 10/10 verified; Stage02 complete original native time PASS 10/10, with metadata review US-UMB/US-Vcp and scientific review required for all ten. Stage03 read-only humidity QC / ERA5 clock scout executed successfully 10/10 (operator log); Stage04 full-event ERA provenance/paired-physics shadow executed 10/10, with 3,129 abnormal source timestamps fully matched to ERA printed labels; Stage05 original RH/QC/phase audit executed successfully 10/10 (3,541,632 HH; 47,267 RH differences >10pp; 503,174 RH missing); Stage06 RH disagreement episode/source-header audit completed 10/10 (6,782 continuous episodes, 47,267 severely discordant RH records); Stage07 QC/ERA/MDS inheritance audit complete 10/10 (50,287 event timestamps, 9,632/9,632 VPD-QC2 matches ERA, 9,018/9,018 TA-QC2 matches ERA); Stage08 all-row consolidated provenance and MDS alternatives PASS 10/10: 3,541,632 records, 0 inconsistent source-selection, 1,750 low-derived-RH screens (700 MDS-pair mathematically feasible, 1,050 nonphysical); Stage09 read-only low-RH triage completed 10/10 (1,750 records: 1,559 negative, 191 nonnegative <1%; 170 without ERA/tower-T physically feasible pairing); Stage10 SHA-verified report-only human review CSV exporter published, operator execution pending. NO model-ready forcing has been approved.**

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

[Stage02 read-only auditor](scripts/stage02/02_audit_batch05_metadata_time_met.py) was locally tested on all ten synthetic release layouts (including FULLSET without BIF and an hourly source) and has now been run on all ten actual IRIDIS6 source files by the operator; see the Stage02 results below.

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


## Stage02 actual IRIDIS6 result — PASS 10/10 for native chronology

The operator's complete Stage02 output on 2026-10-25 is recorded in the [Stage02 evidence ledger](docs/STAGE02_FULL_NATIVE_AUDIT_2026-10-25.md). Every site reports `TIME PASS` and `LABEL_BOUNDARY_SCREEN FULL_LABEL_YEARS`. Metadata review: **US-UMB** (no BIF in FULLSET) and **US-Vcp** (two coordinate/elevation candidates). Derived water RH is negative at a total of **1,559 half-hour records** across the batch; counts are screen diagnostics (TA degC / VPD hPa assumption), not certified repairs. All ten sites need scientific QC. Stage02 performed no writes to the extracted source files.

## Stage03 — humidity-event source QC + original ERA5 companion/clock scout (read-only)

[Stage03 source](scripts/stage03/03_review_humidity_qc_and_era5_clock.py) inventories native TA/VPD/RH abnormal events with their original QC, per-year distributions and sample timestamps; separately inspects the matching original ERA5 CSV's header/schema, time span and available variables. It computes TA agreement diagnostics across **integer-hour offset hypotheses −12..+12** using a limited set of QC0 source-TA anchors. It **does not select an offset** or declare any ERA5 record scientifically valid. Sub-hour offset requirements and units must be checked before any replacement. If the ERA5 candidate does not contain a recognizable TA column, this is reported without inventing one.

Run on IRIDIS6 (main branch script is downloaded; verify filename, syntax and self-test before full scan):

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage03"
  SCRIPT="$BASE/03_review_humidity_qc_and_era5_clock.py"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage03/03_review_humidity_qc_and_era5_clock.py" \
    -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage03_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Output includes `ORIGINAL_AUDIT`, `ERA_SCOUT`, `SITE_AUDIT_DONE` and `STAGE03 SUMMARY: audited=10/10 failed=none` on successful data scans. The program writes **nothing to the source**; only the command's `tee` creates a local log. Interpretation of the source and ERA5 clock, replacement decisions, ZBOT, PFT, and all forcing/model modifications remain pending.


## Stage03 operator result — executed 10/10 (2026-10-25)

**Verified from the complete supplied Stage03 log:** `audited=10/10 failed=none`. All ten source and original release-bundled ERA5_HH companions are available; no ERA companion RH column was detected. There are **1,559** derived water-RH-negative half-hours, **1,750** derived water-RH<1% half-hours, **1,296** native RH>100 records, and **201** native RH<1 records; these sets overlap. The complete source-derived tables and source/ERA examples are recorded in [Stage03 evidence and scientific interpretation](docs/STAGE03_HUMIDITY_ERA_PROVENANCE_2026-10-25.md).

**Critical discovery:** US-Vcm has abnormal native TA/VPD examples identical to bundled ERA values; US-Vcp and US-Wjs have abnormal VPD values identical to ERA but much colder native TA. **Blindly replacing abnormal VPD with the bundled VPD_ERA would not resolve those records.** Stage03 offset rankings from sparse temperature samples do not authorize shifting any timestamps.

## Stage04 — complete event-level original / ERA humidity provenance (READ ONLY)

[Stage04 script](scripts/stage04/04_full_native_era_humidity_provenance.py) performs an exact-label comparison of **every** flagged native humidity record (not just Stage03's 12 per-site examples). It separates inherited ERA VPD from temperature incompatibility, evaluates ERA-internal vapour-pressure nonnegativity and computes a provisional physically constrained native-T+ERA-vapour-pressure candidate without writing it. Exact-label comparison is purely diagnostic; clock alignment, grid/height corrections, ice-phase physics, independent ERA5-Land science and model readiness remain **unapproved**.

Execute on IRIDIS6:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage04"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  SCRIPT="$BASE/04_full_native_era_humidity_provenance.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage04/04_full_native_era_humidity_provenance.py" \
    -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage04_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected successful final line: `STAGE04 SUMMARY audited=10/10 failed=none`. The source itself writes nothing; `tee` writes a shell log. Operator output will determine the next evidence-gated repair design. There is **no** forcing overwrite, timestamp shift, ERA adoption, DATM construction or Slurm model job.


## Stage04 actual IRIDIS6 run — complete 10/10 (2026-10-25)

The operator's full console output reports `STAGE04 SUMMARY audited=10/10 failed=none`; full site table and scientific caution are in [Stage04 evidence ledger](docs/STAGE04_FULL_EVENT_ERA_PAIR_SCREEN_2026-10-25.md). Of **3,129** distinct flagged half-hours, **2,336** have a mathematically feasible ERA-vapour-pressure / tower-temperature pairing, **738** do not, and **55** have ERA-internal physically inconsistent humidity under the stage's water-saturation assumption (US-Vcm 52, US-Vcp 3). **762** event rows have native VPD numerically identical to the bundled ERA VPD. None of these is a completed repair, and same-label joins do not establish UTC alignment.

## Stage05 — original RH provenance and frozen-temperature sensitivity (READ ONLY)

Published: [`scripts/stage05/05_native_RH_provenance_phase_screen.py`](scripts/stage05/05_native_RH_provenance_phase_screen.py). It re-audits all native rows, fingerprints each original source against the exact SHA256 logged in Stage04, compares the original RH field to the independent *calculation* from TA/VPD, tabulates near-identity and large disagreements by original TA/VPD QC, and separates water/ice saturation formula results below 0C. **This statistical comparison does not establish whether the original RH field is independently observed or an intermediate processed variable.** It writes no source files.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage05"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  SCRIPT="$BASE/05_native_RH_provenance_phase_screen.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage05/05_native_RH_provenance_phase_screen.py" \
    -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage05_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected on a successful operator run: `STAGE05 SUMMARY audited=10/10 failed=none`. This is an expectation, not a claimed run. Stage05 **does not** change timestamps, forcing, CIME, DATM, surface files or Slurm queues.


## Stage05 operator result — completed 10/10 (2026-10-25)

The operator's Stage05 source SHA fingerprints and self-test passed at IRIDIS6; `STAGE05 SUMMARY audited=10/10 failed=none`. Across 3,541,632 native HH records, 503,174 original RH values are missing; 47,267 populated-RH cases disagree by more than 10 percentage points with the RH calculated from original `TA_F` and `VPD_F` using water saturation. The major sites are US-Vcm (16,065), US-Vcp (10,509), US-WCr (12,425). All severe discrepancies occur under TA/VPD QC1/1 (38,278), QC2/2 (8,981), or QC1/2 (8); none occur under QC0/0. For 503 subfreezing low-derived-RH records, substitution of the Stage05 ice formula leaves all 503 below 1% RH. These are screening counts, not proof of independently measured RH or of the QC categories' processing meaning. See the full [Stage05 evidence ledger](docs/STAGE05_NATIVE_RH_PROVENANCE_2026-10-25.md).

## Stage06 — source-lineage candidates and contiguous severe-RH discrepancy episodes (READ ONLY)

[Stage06 auditor](scripts/stage06/06_rh_disagreement_lineage_and_episodes.py) scans all 10 original native CSVs, validates the operator-reported Stage05 SHA256 for each, reports any **actually present** unsuffixed TA/VPD columns and their equality with processed TA_F/VPD_F, quantifies original-RH vs derived-RH discrepancies by original QC pair, and reports the longest contiguous >10 percentage-point mismatch episodes. RH remains a *candidate with unverified provenance*, not an adopted input. No original CSV/forcing write, timestamp shift, ERA5 adoption or Slurm submission occurs.

Run on IRIDIS6:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage06"
  COMMIT="a6d0db95e575f8159c8cecbe8561615ccc1f7e1e"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/06_rh_disagreement_lineage_and_episodes.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage06/06_rh_disagreement_lineage_and_episodes.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "31d9db0179fc9743b8058f90119dbfb734f8426b"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage06_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

On a successful operator run, the script prints `STAGE06 SUMMARY audited=10/10 failed=none`. Stage06 has been published but **not yet run** on the user's full IRIDIS6 dataset.


## Stage06 actual IRIDIS6 operator run (2026-10-25) — PASS 10/10

[Complete Stage06 result, 10-site episode table, and QC documentation](docs/STAGE06_SEVERE_RH_EPISODES_AND_QC_PROVENANCE_2026-10-25.md): 3,541,632 original HH records scanned; 47,267 source-RH differences >10 pp in 6,782 distinct contiguous episodes. The longest is US-Vcm 297 half-hours (148.5 h) spanning 2023-03-04 05:00 to 2023-03-10 09:00 (printed source timestamps, local-standard convention). No independent unsuffixed TA/VPD columns were found in the ten **selected** native FLUXMET/FULLSET files; other source packages have NOT been excluded.

**Official FLUXNET meanings** for `TA_F_QC` and `VPD_F_QC`: 0 = measured; 1 = good-quality gapfill (MDS); 2 = downscaled ERA. See https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/ and https://fluxnet.org/data/fluxnet2015-dataset/variables-quick-start-guide/. QC2 inherited ERA values must **not** be replaced with the very same companion ERA values. The official dataset time convention is *local standard time without DST* (https://fluxnet.org/data/fluxnet2015-dataset/); do **not** adopt Stage03 correlation-based shifts. Source-release and site-specific metadata still require verification.

## Stage07 — verify actual gapfill lineage, MDS availability, and QC2 ERA value inheritance (READ ONLY)

[Stage07 script](scripts/stage07/07_verify_fluxnet_qc_lineage_and_era_inheritance.py) scans all native HH rows for physical humidity alarms or disagreement; checks original hashes against Stage06; inventories optional `TA_F_MDS/VPD_F_MDS` columns without inventing them; and joins flagged native records to original release-bundled `ERA5_HH` by **printed source timestamp** solely to audit QC2 inheritance. This is NOT a source repair; `RH` is not assumed to be independent or measured.

On IRIDIS6:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage07"
  COMMIT="c04ae1454a4ee506588092cd08c01773c5885e84"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/07_verify_fluxnet_qc_lineage_and_era_inheritance.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage07/07_verify_fluxnet_qc_lineage_and_era_inheritance.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "184fe85ce0756ce22b069d8cd26bf8b9cfee816e"
  echo "STAGE07 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage07_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

On a successful run, expect `STAGE07 SUMMARY audited=10/10 failed=none`. The code has been committed and hash-verified on GitHub but its operator self-test and real IRIDIS6 run are **pending**. The script does not overwrite source files, build forcing, change clocks or submit jobs.


## Stage07 — actual IRIDIS6 source-lineage result 10/10 (2026-10-25)

Stage07 passed original SHA fingerprints and `STAGE07 SUMMARY audited=10/10 failed=none`. All 50,287 screened source-flagged timestamps have an exact printed-label release `ERA5_HH` companion record. Among **only those flagged rows**, QC2 `TA_F` matches `TA_ERA` for 9,018/9,018, and QC2 `VPD_F` matches `VPD_ERA` for 9,632/9,632. Likewise 41,269/41,269 flagged QC0/1 TA and 40,655/40,655 flagged QC0/1 VPD agree with available `*_F_MDS`. **These are a confirmed consolidation/source-lineage relationship, not independent source agreement or model forcing approval.**

Of those Stage07 anomalous rows, 346 had an ERA TA/VPD pair that violates the present water-saturation assumption (US-Vcm 343; US-Vcp 3); this larger sample includes Stage04's 55 cases. Ten selected native FLUXMET/FULLSET files have `TA_F_MDS`, `VPD_F_MDS`, their MDS QC and `TA_ERA/VPD_ERA`, but no unsuffixed `TA`/`VPD` or `RH_QC`. See [Stage07 evidence ledger](docs/STAGE07_LINEAGE_AUDIT_2026-10-25.md). The difference between consolidated `*_F_QC` codes (0 measured, 1 good MDS, 2 ERA) and MDS `*_F_MDS_QC` codes (0 measured, 1 good, 2 medium, 3 poor) is essential; never auto-promote MDS QC2/3.

## Stage08 — all-row original source-selection and MDS alternative quality screen (READ ONLY)

Published: [Stage08 full 10-site original CSV check](scripts/stage08/08_full_consolidation_QC_and_MDS_alternatives_readonly.py). It scans **every** native half-hour, not just Stage07's 50,287 flagged points, comparing `*_F` with `*_F_MDS` at consolidated QC0/1, with `*_ERA` at consolidated QC2, and inventories `*_F_MDS_QC` 0–3 at QC2 events. It additionally counts any violations of the published F-variable source-selection convention and tests whether lower-quality MDS intermediate TA/VPD combinations are physically plausible — **never approving or writing an alternative**. Stage08 operator run is pending.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage08"
  COMMIT="803b725ece37472ddfde339aa4034a6bd51ae262"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/08_full_consolidation_QC_and_MDS_alternatives_readonly.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage08/08_full_consolidation_QC_and_MDS_alternatives_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "3eaf03109e8e80ae97aaa3fb0e1eb0d328bc03ca"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage08_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected when the real operator run succeeds: `STAGE08 SUMMARY audited=10/10 failed=none`. Stage08 has been committed and file hash checked on GitHub, but has **not** been executed on IRIDIS6. **NO original overwrite, RH adoption, fallback forcing, timestamp conversion, CIME case, or SLURM job.**


## Stage08 — actual operator run 10/10 (2026-10-25)

Full results: [Stage08 complete original row QC, provenance and MDS alternative science report](docs/STAGE08_FULL_CONSOLIDATION_AND_LOW_RH_2026-10-25.md).

**3,541,632** original half-hour rows scanned, all ten original SHA256 fingerprints matched: `STAGE08 SUMMARY audited=10/10 failed=none`. Source choice was fully consistent with the FLUXNET consolidation rules, across the entire series: **3,119,032/3,119,032** TA QC0/1 matched TA_F_MDS; **422,600/422,600** TA QC2 matched TA_ERA; **3,097,311/3,097,311** VPD QC0/1 matched VPD_F_MDS; **444,321/444,321** VPD QC2 matched VPD_ERA.

For the **1,750** `RH_water(TA_F,VPD_F)<1%` original source rows (**1,559** negative and **191** nonnegative), pairing original MDS TA and MDS VPD is *mathematically plausible* for **700** and nonphysical for **1,050**. **666** low-RH records inherit VPD_ERA (F_QC2); all have lower-quality VPD_F_MDS_QC2/3, so none can be indiscriminately promoted to MDS. **119** low-RH records have `TA_F_QC/VPD_F_QC=0/0`, requiring tower-observation review. Mathematical plausibility is not validation; source `RH` has no independently verified provenance.

## Stage09 — low derived-RH event triage (READ ONLY, operator run pending)

[Stage09 script](scripts/stage09/09_low_RH_source_resolution_readonly.py) scans the exact 10 original SHA-verified source files, splits `RH_water <0` (physically impossible under the stated water formula) from `0<=RH_water<1%` (extreme but not categorically impossible), and classifies each low-RH event by consolidated QC, MDS-QC, original RH availability, MDS-pair physics, ERA-pair physics, and the *hypothetical* pairing of ERA implied vapour pressure with original tower temperature. It prints only summaries, representative examples and longest contiguous low-RH episodes; writes no source/forcing.

IRIDIS6 commands:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage09"
  COMMIT="e1d5a0d5326d3f1187800588a65283c06a5fd90e"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/09_low_RH_source_resolution_readonly.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage09/09_low_RH_source_resolution_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "96b969a6e6dd8f9c1f29cddda91c98a522c3d642"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage09_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected on operator success: `STAGE09 SUMMARY audited=10/10 failed=none`. This has **not** been run on the operator's IRIDIS6 data; the script has been published and reviewed but not executed in this session. No output forcing has been authorised.


## Stage09 — actual operator PASS 10/10, scientific triage (2026-10-25)

Full results: [Stage09 exact 1,750 original-source low-RH inventory and QC breakdown](docs/STAGE09_1750_LOW_RH_TRIAGE_2026-10-25.md). `STAGE09 SUMMARY audited=10/10 failed=none` and ten original SHA256 checks verified. Water-derived RH<1% at **1,750** original HH records, of which **1,559 strictly negative** and **191 nonnegative**. **1,605** original RH values missing, with 145 populated RH values of still-undetermined independent provenance. Original QC of the 1,750: 119 measured/measured, 961 measured/good-MDS, 479 measured/ERA, 4 good-MDS/good-MDS, 128 good-MDS/ERA, 59 ERA/ERA. Exactly 666 original anomalous VPD values are ERA-derived, and their alternative `VPD_F_MDS` has medium/poor QC2/3; never auto-promote.

Using the hypothetical ERA vapour pressure (ERA water saturation minus ERA VPD) with tower TA is mathematically possible for 1,580, not possible for 115 more, and ERA itself is internally nonphysical under this water formula in 55 records. **Mathematical feasibility is never approval for source replacement.** The 119 measured-pair records should have separate original measurement review; **27** are negative (26 US-WCr, 1 US-Vcm), **92** are nonnegative below 1% (US-Vcm). No forcing modifications have been approved or written.

## Stage10 — manual review report export, with strict no-model-write guard

[Stage10 original SHA256-verified event CSV exporter](scripts/stage10/10_export_low_RH_manual_review_ledger.py) writes **only new review reports** to an explicit, previously nonexistent `--output-dir`. It lists all 1,750 source-flagged HH and original TA/VPD/RH, consolidated/MDS QC, ERA/MDS physical feasibility, and a purely exploratory interpolated VPD if two measured physically coherent TA/VPD anchors exist within 3 hours on each side of the event. **It does not adopt the interpolation, modify original FLUXMET/ERA sources, create forcing, alter timestamps, edit CIME, or submit Slurm.** No output directory may overlap the source root or exist already.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage10"
  COMMIT="3d1630c7f2930acbeaa693c4bb77ffd7cbced382"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/10_export_low_RH_manual_review_ledger.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage10/10_export_low_RH_manual_review_ledger.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "b33e85901c7c0502f68985ead116fc1cae187a72"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/review_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --output-dir "$OUT" 2>&1 | tee "$BASE/stage10.log"
  echo "STAGE10_REPORTS=$OUT"
)
```

On success the operator should observe `STAGE10 SUMMARY sites=10/10 events=1750 negative=1559`, plus 10 event CSVs and `audit_summary.json`. The script is published but still needs execution and its self-test on IRIDIS6. **Reports are diagnostic artefacts, NOT replacements or model-ready forcing.**
