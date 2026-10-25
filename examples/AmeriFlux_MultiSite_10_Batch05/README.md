# AmeriFlux MultiSite 10 — Batch 05

**Status (2026-10-25): Stage00 upload/checksum 10/10 verified; Stage01 extraction 10/10 verified; Stage02 complete original native time PASS 10/10, with metadata review US-UMB/US-Vcp and scientific review required for all ten. Stage03 read-only humidity QC / ERA5 clock scout executed successfully 10/10 (operator log); Stage04 full-event ERA provenance/paired-physics shadow executed 10/10, with 3,129 abnormal source timestamps fully matched to ERA printed labels; Stage05 original RH/QC/phase audit executed successfully 10/10 (3,541,632 HH; 47,267 RH differences >10pp; 503,174 RH missing); Stage06 RH disagreement episode/source-header audit completed 10/10 (6,782 continuous episodes, 47,267 severely discordant RH records); Stage07 QC/ERA/MDS inheritance audit complete 10/10 (50,287 event timestamps, 9,632/9,632 VPD-QC2 matches ERA, 9,018/9,018 TA-QC2 matches ERA); Stage08 all-row consolidated provenance and MDS alternatives PASS 10/10: 3,541,632 records, 0 inconsistent source-selection, 1,750 low-derived-RH screens (700 MDS-pair mathematically feasible, 1,050 nonphysical); Stage09 read-only low-RH triage completed 10/10 (1,750 records: 1,559 negative, 191 nonnegative <1%; 170 without ERA/tower-T physically feasible pairing); Stage10 SHA-verified report-only export DONE 10/10 (1,750 original humidity flags, 1,559 negative) at review_20261025T180413Z_682688; Stage11 existing Stage10 review ledger QA PASS 10/10 (229 mathematically feasible unapproved bracketed interpolation candidates, 1,510 lacking both QC0 anchors, 11 nonphysical interpolations, 170 overlapping ERA-pair holds, 27 negative measured-QC0/0 source events); Stage12 original native temporal context report COMPLETED 10/10 (382 unique priority records from 1,750 low RH flags, 4,966 original HH contextual rows, approved=0); Stage13 independent native-context QA DONE 10/10 (382 priority events/4,966 original HH, 229 bracketed interpolations reproduced, 27 measured negative RH discrepancies all <=0.2 percentage points, 0 forcing repairs); Stage14 science sensitivity report completed 10/10 (240 bracketed trials, 173 change >5 hPa; 27 source QC0/0 near-zero RH checked with Magnus/Buck/Tetens, only one nonnegative under Buck/Tetens; no forcing changes); Stage15 full 1750-event source-provenance/hold inventory PASS 10/10 (VPD QC0=119, QC1=965, QC2=666, negative=1559, original RH missing=1605, approved=0); Stage16 report-only source-pair study PASS 10/10 (MDS pair 700/1050 physical/nonphysical; ERA pair 1695/55; mixed TA_F+ERA VPD 1102/648; ERA vapor e+TA_F 1580/115 among 1695 valid ERA pairs; approved=0). Stage17 original native 1,750-HH source anomaly episode manifest COMPLETED 10/10 (522 continuous native episodes: P1 human review 39, P2 meteorological evidence needed 89, P3 remaining source-reference check 394; approved 0). FORCING HAS NOT BEEN MODIFIED. NO model-ready forcing has been approved.**

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


## Stage10 actual operator run: 10/10 review CSVs generated (2026-10-25)

[Stage10 original run log, exact 10-site row counts, and report semantics](docs/STAGE10_OPERATOR_MANUAL_REVIEW_REPORTS_2026-10-25.md). Operator output confirmed **SOURCE VERIFIED**, **SELF-TEST PASS**, and `STAGE10 SUMMARY sites=10/10 events=1750 negative=1559`. Report-only path:

```text
/home/ly3n24/ameriflux_batch05_stage10/review_20261025T180413Z_682688
```

The Python exporter printed the resolved path under `/iridisfs/home/ly3n24/...`; the shell path was `/home/ly3n24/...`. Use `realpath` locally to confirm these address the same files. Exactly 10 `<SITE>_low_RH_review.csv` reports and `audit_summary.json` are expected under that directory. The source logs do not provide the actual per-site interpolation candidate counts, so do **not** invent how many are bracketed, or claim any interpolation is approved. Original data/forcing remained unchanged, and no model runs or jobs were started.

## Stage11 (READ ONLY): check report arithmetic and list human-review candidates

[Stage11 review CSV/JSON validator](scripts/stage11/11_audit_stage10_review_ledgers_readonly.py) reads only the existing Stage10 report directory: verifies row counts (1,750), negative (1,559), nonnegative <1% (191), original per-site summaries, native physical formula, source QC0/0 cases, interpolation math and 3h anchor bounds. It prints per-site diagnostic categories and priority examples; writes NOTHING. It is **not an automatic forcing repair**.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage11"
  COMMIT="5025119232ff2f3a5f66b0d4bbead831c61a972d"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/11_audit_stage10_review_ledgers_readonly.py"
  REPORTS="$HOME/ameriflux_batch05_stage10/review_20261025T180413Z_682688"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage11/11_audit_stage10_review_ledgers_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "905ba71593569d0ba9451a008eef1bf1bd9f1d69"
  echo "STAGE11 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  test -f "$REPORTS/audit_summary.json"
  python3 -B "$SCRIPT" --report-dir "$REPORTS" \
    2>&1 | tee "$BASE/stage11.log"
)
```

When the IRIDIS6 run genuinely succeeds, expect `STAGE11 SUMMARY sites=10/10 events=1750 negative=1559 nonnegative_below1=191 files_valid=10`. Stage11's GitHub blob was verified, but it has **not** been executed on the private IRIDIS6 reports. No original data/forcing writes, no time changes, no model or Slurm activity.


## Stage11 actual operator result — 10/10 PASS (2026-10-25)

[Stage11 source-grounded complete result](docs/STAGE11_REVIEW_LEDGER_VALIDATION_2026-10-25.md) confirms all ten Stage10 CSV ledgers agree with `audit_summary.json` and original math and bracket checks. The 1,750 cases split into:

- 229 interpolations with verified +/-3-hour QC0/0 anchor times and **mathematically feasible, not approved** interpolated VPD
- 1,510 without two qualifying QC0/0 observations within +/-3 h
- 11 interpolations whose numeric VPD candidate remains nonphysical (4 US-Vcm; 7 US-Wkg)
- 170 overlapping ERA-pair holds (115 hypothetical ERA implied vapor pressures inconsistent with tower TA, 55 ERA pair internally nonphysical under water formulation)
- 27 negative computed-RH source cases with measured TA/VPD (26 US-WCr, 1 US-Vcm)

**Do not equate formula-negative RH of around −0.1% in measured VPD with a defective tower sensor.** Original RH in 26 US-WCr measured-pair cases is 0%; this may be a saturation-equation / numerical-precision boundary issue. None of the event groups is model forcing ready.

## Stage12 — full original FLUXMET/FULLSET +/-3-hour temporal context for priority cases (NO REPAIRS)

[Stage12 original data context script](scripts/stage12/12_export_priority_low_RH_source_context_readonly.py) reads existing Stage10 event CSV, verifies source SHA256 again, and exports the native meteorology/QC/MDS/ERA values from 3 h before to 3 h after each unique priority event. Categories: 229 unapproved bracketed, 11 unphysical bracketed, 27 measured source negatives, and 170 ERA-pair holds (these overlap). Also validates source event-center values and both actual QC0 measured anchors for any bracketed case. Outputs **new** independent report CSV/JSON only — neither original sources, original Stage10 reports, forcing, model cases nor Slurm are touched.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage12"
  COMMIT="1afc927170d16919946982e7bfe2136d4d442960"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/12_export_priority_low_RH_source_context_readonly.py"
  REPORTS="$HOME/ameriflux_batch05_stage10/review_20261025T180413Z_682688"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage12/12_export_priority_low_RH_source_context_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "267753d59b23ee102bedeb2706c59cefb09b8b91"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/context_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --report-dir "$REPORTS" --output-dir "$OUT" \
    2>&1 | tee "$BASE/stage12.log"
  echo "STAGE12_REPORTS=$OUT"
)
```

Expected after actual IRIDIS6 success: `STAGE12 SUMMARY sites=10/10 original_events=1750 priority_unique=... context_rows=... approved=0 reports=...`. The number of **unique** priority events and rows of temporal context are not guessed from the overlapping categories and will be printed by the real run. Script created/pinned on GitHub, but user operator run and self-test are **pending**.


## Stage12 completed — real operator's source-context export (2026-10-25)

[Stage12 exact original 10-site operator counts and science evidence](docs/STAGE12_NATIVE_TEMPORAL_CONTEXT_2026-10-25.md).

- Original ten site files were SHA256 verified; source and Stage10 reports were left unchanged; no forcing, model cases, clocks or Slurm were touched.
- Original Stage10 input cohort = **1,750** low-derived-RH records; 4 scientific priority categories from Stage11 overlap, yielding **382 distinct priority target half-hours**.
- **4,966** original native contextual records extracted, exactly **13 half-hours per target** (±3 hours; duplicated context timestamps between overlapping target windows are intentional). No repair approved.
- Category membership counts remain **229 bracketed math-feasible but UNAPPROVED**, **11 bracketed still nonphysical**, **27 measured QC0/0 negative**, and **170 ERA/tower-T pairing holds**. Sum 437 memberships, 55 duplicates by category overlap. The other **1,368** low RH cases were not among selected Stage12 priorities and remain unresolved in Stage10.
- IRIDIS6 report folder:
  `$HOME/ameriflux_batch05_stage12/context_20261025T192426Z_1264512`.
  Three outputs: `stage12_priority_targets.csv`, `stage12_original_native_context.csv`, `stage12_summary.json`.

## Stage13 — full context and science-priority consistency screen (READ ONLY; operator run pending)

[Stage13 original-context QA Python script](scripts/stage13/13_check_native_context_science_readonly.py) consumes the three Stage12 outputs **without modifying them**; independently checks every target's exact 13 native HH timestamps/offsets, reproduces original derived water RH, reconstructs original QC0 observed anchor brackets for all **229** mathematical interpolation hypotheses, separates nonphysical brackets from physically plausible ones, and prints all **27** measured QC0/0 formula-negative original RH comparisons. Produces no replacement candidate forcing and makes no science approval.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage13"
  COMMIT="1a4774d39691d13de8fad1397f26491b94c651b2"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/13_check_native_context_science_readonly.py"
  REPORTS="$HOME/ameriflux_batch05_stage12/context_20261025T192426Z_1264512"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage13/13_check_native_context_science_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "5966fecb0940e3db640c9340b23e158d4fb65a3c"
  echo "STAGE13 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --stage12-dir "$REPORTS" \
    2>&1 | tee "$BASE/stage13.log"
)
```

Expected only when actual IRIDIS6 operation succeeds: `STAGE13 SUMMARY sites=10/10 priority=382 context=4966 interpolations_reverified=229 approved=0`. Stage13 is uploaded/hash-verified but **has not been executed on IRIDIS6**. The next science decision is whether further external independent weather observations and station metadata provide acceptable corrections, **not automatic substitution of ERA or a mathematically possible interpolation**.


## Stage13 actual operator science-context verification (2026-10-25)

[Stage13 original native context verified science report](docs/STAGE13_ORIGINAL_CONTEXT_REVIEW_2026-10-25.md). Real run output: `STAGE13 SUMMARY sites=10/10 priority=382 context=4966 interpolations_reverified=229 approved=0`.

- All original 13-HH contexts and original measured bracketing anchors independently reproduced for 229 (strictly unapproved) math-feasible interpolation candidates; the 11 other bracketed candidates remained physically inconsistent.
- The 27 negative water-formula RH values with consolidated measured TA/VPD `QC0/0` (26 US-WCr, 1 US-Vcm) **all** differed from the original populated `RH` by **<0.2 percentage points**. Absolute discrepancies 0.084182–0.108221 percentage points across the 27. Formula variation may materially affect their status near RH=0; native saturation formula and independence of original RH remain unverified.
- Large mathematically feasible interpolation changes: US-Var `201908190600` native VPD 21.747 hPa, straight bracket interpolation 0.11271 hPa (change **−21.63429 hPa**); this must not be applied without independent evidence.
- Neither RH nor VPD source was modified; no output forcing, model runs, time shifts or Slurm submissions.

## Stage14 scientific screen — report-only saturation formula sensitivity and 240 bracketed candidate magnitudes

[Stage14 script](scripts/stage14/14_compare_saturation_formulas_and_interpolation_risk_readonly.py) uses the **already generated** Stage12 CSV/JSON files; does not re-read entire 3.5M HH sources. For all 27 original `QC0/0` slightly formula-negative RH records, compares three explicitly hypothetical water saturation formulas (Magnus, Buck and Tetens) against original RH. For the 229 physically feasible + 11 nonphysical bracketed interpolation trials, verifies source QC0 anchors again and stratifies **absolute VPD changes** into <=1, >1–5, >5–10, >10 hPa. These are *scientific sensitivity screens*, not assertions about FLUXNET native calculation methods. All remain `HOLD_NOT_APPROVED`. New files are **review-only** CSV/JSON in a new directory, never original, Stage10, Stage12, forcing or CIME.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage14"
  COMMIT="82dd7ff57950401d7fbd18c01dc9309da4863f97"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/14_compare_saturation_formulas_and_interpolation_risk_readonly.py"
  REPORTS="$HOME/ameriflux_batch05_stage12/context_20261025T192426Z_1264512"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage14/14_compare_saturation_formulas_and_interpolation_risk_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "78bccf052b6bce94d6eb4cfc682e1e2caf068e15"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/science_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage12-dir "$REPORTS" --output-dir "$OUT" \
    2>&1 | tee "$BASE/stage14.log"
  echo "STAGE14_REPORTS=$OUT"
)
```

Operator expected success only after actual run: `STAGE14 SUMMARY sites=10/10 priority=382 context=4966 bracketed=229 nonphysical_bracketed=11 measured=27 approved=0`. Outputs: `stage14_all_240_bracketed_risk.csv`, `stage14_27_measured_saturation_formulas.csv`, `stage14_summary.json`. The current GitHub code is committed/verified and has not been executed against the private IRIDIS6 Stage12 CSVs.


## Stage14 actual operator execution (2026-10-25): PASS 10/10, 0 science approvals

[Stage14 complete source-derived science audit](docs/STAGE14_FORMULA_SENSITIVITY_AND_VPD_INTERPOLATION_RISK_2026-10-25.md). Source script hash, syntax and self-test passed; original Stage12 context examined without source or forcing changes. Operator reported `STAGE14 SUMMARY sites=10/10 priority=382 context=4966 bracketed=229 nonphysical_bracketed=11 measured=27 approved=0`.

All **240** bracketing results include **229** math-feasible but unapproved proposals and **11** nonphysical proposals. Absolute changes from source `VPD_F`: **25 <=1 hPa; 42 >1 to 5 hPa; 122 >5 to 10 hPa; 51 >10 hPa**; overall **173/240 (72.1%) >5 hPa**. No change magnitude provides scientific approval. In 27 measured QC0/0 near-zero source-RH cases, zero are RH>=0 under Magnus; only one (US-Vcm) is RH>=0 under Buck, and one under Tetens. All **26 US-WCr records remain slightly formula-negative under all 3 water curves**; native `RH` is approximately 0%, so source zero-floor/precision and native VPD calculation method remain unresolved. This **does not prove** that US-WCr is faulty or that formula choice can fix it.

Original Stage14 report directory:
`$HOME/ameriflux_batch05_stage14/science_20261025T194317Z_1261521`. Outputs are `stage14_all_240_bracketed_risk.csv`, `stage14_27_measured_saturation_formulas.csv`, and `stage14_summary.json` (data stays on IRIDIS6).

## Stage15: consolidate EVERY 1,750 original low-RH source event, not only 382 priority events

[Stage15 full 1750-event scientific provenance inventory](scripts/stage15/15_full_1750_provenance_triage_readonly.py) reads **only existing Stage10 and Stage14 report files**. It independently rechecks all 1,750 native event TA/VPD and low-RH formula, every original source `F_QC`, the exact 240 Stage14 interpolation candidates and the 27 Stage14 original measured-RH sensitivity cases. All records receive a single *mutually exclusive VPD-source provenance* — 119 measured `VPD_F_QC0`, 965 good MDS `VPD_F_QC1`, 666 ERA `VPD_F_QC2` — plus traceable overlay risk tags and evidence follow-up needs. **None is accepted as a correction**. It verifies the exact 382 focus-event union across the existing reports and preserves 1,368 not previously in Stage12 focus.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage15"
  COMMIT="8fa013e2ae1677222581ab7913dc6a6d215f1cb2"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/15_full_1750_provenance_triage_readonly.py"
  STAGE10="$HOME/ameriflux_batch05_stage10/review_20261025T180413Z_682688"
  STAGE14="$HOME/ameriflux_batch05_stage14/science_20261025T194317Z_1261521"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage15/15_full_1750_provenance_triage_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "14bc20e15c6bd0e784827955e4bbd514a2a4c96c"
  echo "STAGE15 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/triage_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage10-dir "$STAGE10" --stage14-dir "$STAGE14" \
    --output-dir "$OUT" 2>&1 | tee "$BASE/stage15.log"
  echo "STAGE15_REPORTS=$OUT"
)
```

Only if actual IRIDIS6 reports pass all validations will it print `STAGE15 SUMMARY sites=10/10 reviewed=1750 negative=1559 measured=119 good_MDS=965 ERA=666 approved=0`. The script generates **only a new review CSV and JSON**, never changes native data, existing Stage10/14 reports, forcing or model jobs. Stage15 is currently **published but NOT executed** against the IRIDIS6 reports.


## Stage15 operator PASS 10/10 — original source provenance consolidated (2026-10-25 22:42 UTC)

[Stage15 actual operator audit and ten-site evidence](docs/STAGE15_ALL_1750_SOURCE_PROVENANCE_2026-10-25.md). All 1,750 low-RH source records were cross-checked against the Stage10 source-ledger and Stage14 science trials; 1,559 are strictly water-formula-negative, 191 nonnegative under 1%. Selected VPD source provenance: QC0 measured 119, QC1 good MDS 965, QC2 ERA 666. Original RH missing 1,605. Stage12 exact priority native temporal contexts cover 382 events, leaving 1,368 without that special context review. All `science_status=HOLD_NOT_APPROVED`.

The mutually exclusive Stage15 priority ranks were: measured QC0/0 negative 27, original ERA pair internally nonphysical 55, measured QC0/0 extreme low RH 92, interpolated change >10 hPa 51, ERA implied vapor pressure incompatible with tower TA 94, MDS good-QC1 humidity followup 822, ERA-QC2 humidity followup 609. These rank counts sum to 1,750 and are not independent physical event category counts. Original forcing unchanged, no Slurm.

Original Stage15 report folder on IRIDIS6:
`$HOME/ameriflux_batch05_stage15/triage_20261025T224213Z_1292191` (which resolves to `/iridisfs/home/ly3n24/...`).

## Stage16: scientifically distinguish tower/MDS/ERA source pairs across all 1,750 (report-only)

[Stage16 Python source-pair diagnostic](scripts/stage16/16_audit_all_1750_source_pairs_readonly.py) uses only the **existing Stage10 and Stage15 reports**. It joins every original timestamp from both sources, re-verifies all selected QC0/QC1/QC2 provenance and original values, and independently assesses:

- `(TA_F,VPD_F)`: originally selected, already flagged;
- `(TA_F_MDS,VPD_F_MDS)`: alternative native MDS source pair, with its QC0/1/2/3 retained;
- `(TA_ERA,VPD_ERA)`: internally paired original downscaled ERA variables;
- `(TA_F,VPD_ERA)`: **direct VPD mix**, which differs from conserving ERA-specific actual vapor pressure;
- ERA-implied `e_ERA=e_sat(TA_ERA)-VPD_ERA` paired with `TA_F`: an **independent hypothetical shadow**, not a validated replacement.

It reports site-level QC and physics counts, estimates selected TA vs ERA TA and VPD vs ERA VPD differences, and exports all 1,750 events to a **new** CSV/JSON folder. **No inference of scientific validity from a physical bound alone. No source/forcing writes.**

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage16"
  COMMIT="c3057bfbf6c2aa4a3556de857bc9e9d0faa527f7"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/16_audit_all_1750_source_pairs_readonly.py"
  STAGE10="$HOME/ameriflux_batch05_stage10/review_20261025T180413Z_682688"
  STAGE15="$HOME/ameriflux_batch05_stage15/triage_20261025T224213Z_1292191"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage16/16_audit_all_1750_source_pairs_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "e7c1eeca9021a1d900516c0bb3db523d1d72ec83"
  echo "STAGE16 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/source_pairs_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage10-dir "$STAGE10" --stage15-dir "$STAGE15" \
    --output-dir "$OUT" 2>&1 | tee "$BASE/stage16.log"
  echo "STAGE16_REPORTS=$OUT"
)
```

A successful IRIDIS6 full report should end with `STAGE16 SUMMARY sites=10/10 events=1750 measured=119 MDS=965 ERA=666 approved=0`. The previously verified original source-pair physical bound counts expected for Stage16 are MDS feasible=700/nonphysical=1,050; internal ERA feasible=1,695/nonphysical=55; original ERA implied actual water vapor pressure paired with tower TA feasible=1,580/nonphysical=115. These are **shadow tests**: no original source changes or scientifically approved replacement follows merely from passing.

At 2026-10-25 the GitHub source file is committed and hash verified, but the operator Stage16 run/self-test on IRIDIS6 has not yet occurred.


## Stage16 executed and Stage17 ready (2026-10-25)

[Stage16 actual operator results](docs/STAGE16_FULL_1750_SOURCE_PAIR_AUDIT_2026-10-25.md): all 1,750 original low-RH source event rows were checked. Original VPD QC0=119, QC1=965, QC2=666. Source ERA pair was formula-physical in 1,695 but direct mixing source tower TA and source ERA VPD produced 648 formula-nonphysical pairs; preserving ERA's implied vapor pressure with tower TA yielded only 115 incompatible cases among 1,695 valid native ERA pairs. Large difference counts: 437 tower TA vs ERA TA >5°C, 629 source VPD vs ERA VPD >5 hPa. **This does not authorize changes.** Stage16 files on IRIDIS6: `$HOME/ameriflux_batch05_stage16/source_pairs_20261025T225516Z_1291407`.

[Stage17 native half-hour episode and metadata evidence manifest](scripts/stage17/17_build_episode_evidence_manifest_readonly.py) groups all 1,750 events by site and contiguous native half-hour timestamps into review episodes. It writes only a NEW evidence request directory with three files: `stage17_episodes_evidence_requests.csv`, `stage17_site_metadata_gates.csv`, `stage17_summary.json`. It never downloads or substitutes ERA, creates UTC offsets, or approves humidity repair. Before independent verification using raw ERA5-Land 2m temperature/dewpoint, original source clock offset, coordinates/elevation, source algorithm and sensor provenance must be established.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage17"
  COMMIT="861509c28c955add7257b4217ad7dd6d2cb8a005"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/17_build_episode_evidence_manifest_readonly.py"
  STAGE16="$HOME/ameriflux_batch05_stage16/source_pairs_20261025T225516Z_1291407"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage17/17_build_episode_evidence_manifest_readonly.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "a9d50595899fff1623806d1c588a297f10d98d4e"
  echo "STAGE17 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/episode_manifest_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage16-dir "$STAGE16" --output-dir "$OUT" \
    2>&1 | tee "$BASE/stage17.log"
  echo "STAGE17_REPORTS=$OUT"
)
```

**Pending**: operator Stage17 run; then manually investigate prioritized episodes and request independent source/evidence at verified native timestamps before deciding any scientifically approved forcing repairs.


## Stage17 completed: 522 episodes, source-level human review is required before any data replacement

[Stage17 actual operator human-review gate and P1 examples](docs/STAGE17_EPISODE_HUMAN_REVIEW_GATE_2026-10-25.md).

```text
STAGE17 SUMMARY sites=10/10 original_HH=1750 episodes=522 approved=0
ONLY NEW EVIDENCE REQUEST CSV/JSON; NO ORIGINAL/OTHER_REPORTS/FORCING/MODEL/SLURM WRITES
```

Real IRIDIS6 reports:
`$HOME/ameriflux_batch05_stage17/episode_manifest_20261025T230607Z_1291407`; source long-term total 1,750 anomalous half-hours grouped into **522** contiguous native source-time episodes:

- **P1: 39 episodes** require priority human scrutiny (US-Vcm 37; US-Vcp 1; US-WCr 1). Includes original QC0 extreme-low observed RH, near-zero source RH and ERA source itself nonphysical. These should not be auto-overwritten.
- **P2: 89 episodes** need physically independent weather evidence and source processing metadata before selecting a replacement; these are not safe just because the alternative source pair passes water-saturation formula.
- **P3: 394 episodes** carry ordinary provenance and independent-reference checks. They are *not* automatically cleared or scientifically resolved.

**A requested conditional automatic forcing edit is NOT triggered**: scientific human review is nonzero and source/clock/metadata evidence still incomplete. Do not overwrite original/production forcing, clip negative RH, use the same source ERA as independent confirmation, or substitute poor MDS QC2/3. Stage17 did not approve any repair.

On IRIDIS6, print precisely the 39 P1 review episodes from the completed original manifest:

```bash
python3 - <<'PY'
from pathlib import Path
import csv
f=Path.home()/"ameriflux_batch05_stage17/episode_manifest_20261025T230607Z_1291407/stage17_episodes_evidence_requests.csv"
with f.open(newline="",encoding="utf-8") as fh:
    rows=list(csv.DictReader(fh))
p1=[r for r in rows if r["priority_tier"]=="P1_MEASURED_OR_ERA_INVALID"]
assert len(rows)==522 and len(p1)==39
for r in p1:
    print(r["episode_id"],r["native_start"],r["native_end"],r["half_hours"],
          "QC0="+r["qc0_measured_HH"],"ERA_INVALID="+r["ERA_internal_nonphysical_HH"])
PY
```

Next science gate: review original site sensor/RH/VPD formula for measured QC0 periods, and compare verified same-clock local meteorology with freshly acquired ERA5-Land 2m T and dewpoint **after site longitude/latitude/elevation and UTC conversion are verified**. These remain scientific checks not approvals to modify any forcing.
