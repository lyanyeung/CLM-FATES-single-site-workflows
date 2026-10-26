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


## Stage18: original observed half-hour evidence pack for investigator decisions

The operator completed Stage17, identifying **522** native contiguous low-RH episodes from **1,750** original anomalous half-hours, with **39 P1 episodes** (US-Vcm 37, US-Vcp 1, US-WCr 1). The investigator requested all the actual original source numeric data for a human **KEEP / HOLD / REPLACE** decision. **None of the original source meteorology has yet been changed.**

[Stage18 read-only, SHA-pinned original met review exporter](scripts/stage18/18_export_p1_original_review_pack_readonly.py) reads the exact Stage16 selected anomaly ledger, Stage17 P1 episodes, and only the three original native source files needed for those P1 episodes. SHA256 is verified against the prior Stage12 originals. It exports:

- `stage18_39_episode_index.csv`: all P1 event source dates, half-hour counts and provenance.
- `stage18_all_p1_original_flagged_HH.csv`: all P1 anomalous original half-hours, exact original `TA_F`, `VPD_F`, `RH`, two quality codes, MDS and ERA companion values, and derived water RH.
- `stage18_all_p1_original_6hour_context.csv`: native raw time series surrounding each P1 episode (±6 hours), marked context-only when outside the flagged half-hours.
- `stage18_7_priority_review_cards.md`: seven concise native-time user decision tables (US-WCr August 2025, US-Vcm December 2007, January 2007, February 2008, November 2024, October 2025, US-Vcp January 2011), with all other P1 source abnormal HH at the end.
- `stage18_summary.json`: exact hashes and counts and zero repair approvals.

As with earlier stages, this does not invent a UTC offset, infer a source instrument or modify any source/forcing/CIME/Slurm settings.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage18"
  COMMIT="cf6fb9fe7a8c8ea9905757b0086a05c9a1d486ec"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/18_export_p1_original_review_pack_readonly.py"
  STAGE16="$HOME/ameriflux_batch05_stage16/source_pairs_20261025T225516Z_1291407"
  STAGE17="$HOME/ameriflux_batch05_stage17/episode_manifest_20261025T230607Z_1291407"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage18/18_export_p1_original_review_pack_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "e58205016cda48d42d4732261ebc238fd7941ee7"
  echo "STAGE18 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/original_review_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage16-dir "$STAGE16" \
    --stage17-dir "$STAGE17" --output-dir "$OUT" \
    2>&1 | tee "$BASE/stage18.log"
  echo "STAGE18_REPORTS=$OUT"
)
```

After success, show the actual reviewer decision cards with `cat "$OUT/stage18_7_priority_review_cards.md"` **inside the same shell**, or upload that `.md` and the flagged HH CSV to ChatGPT to conduct an evidence-based KEEP/HOLD/REPLACE review. This script is committed and SHA-verified on GitHub but has **not been executed on IRIDIS6**. All proposals remain `HOLD_NOT_APPROVED`.


## Stage19: P1 original-before-and-after user review tables

The operator completed Stage18: original P1 met from three SHA256-pinned native sources, **39 P1 episodes = 176 flagged original HH, 775 unique HH context rows**, with original Stage18 evidence at `$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929`.

User requested both the **before and after** meteorology and ERA5 data, by problem, so they can decide now. The Stage18 pasted terminal output showed P1-flagged hours but not all 775 surrounding HH values; Stage19 provides exact existing CSV data without fabricating missing rows.

[Stage19 report-only before/during/after source tables](scripts/stage19/19_make_before_during_after_decision_tables_readonly.py) reads only Stage18 reports and writes:
- `stage19_SEVEN_priority_original_before_after.md`, one full copy/paste-ready file combining the seven core review groups with original surrounding meteorology;
- `seven_priority_groups/G01...G07.md`, individual full before/P1/between/after table per top group;
- `all_39_episodes/US-...E....md`, individual exact original episode ±6h source context; neighboring abnormal P1 half-hours separately labeled;
- `stage19_all_episode_before_during_after_long.csv`, machine-readable audit rows for all 39 P1 episodes including source value QC, MDS alternatives, processed ERA counterparts, source RH and water-Magnus RH;
- `stage19_summary.json`.

**Critical data provenance:** the original source columns `TA_F` and `VPD_F` are not necessarily measured *tower* values: QC0=measured, QC1=MDS, QC2=source-supplied processed ERA. `TA_ERA` and `VPD_ERA` are source supplied downscaled ERA/reference counterparts; their exact reanalysis version has not been independently verified as **ERA5/ERA5-Land**. This script does not independently download ERA5/ERA5-Land. No source meteorology, QC, DATM forcing, CIME or Slurm changes.

```bash
(
 set -euo pipefail
 BASE="$HOME/ameriflux_batch05_stage19"
 COMMIT="b5081d1ebc18ab6d4622b1ac6d0ad4379072b92e"
 RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
 SCRIPT="$BASE/19_make_before_during_after_decision_tables_readonly.py"
 STAGE18="$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929"
 mkdir -p "$BASE"
 curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage19/19_make_before_during_after_decision_tables_readonly.py" -o "$SCRIPT"
 test "$(git hash-object "$SCRIPT")" = "47a9fb0e683ff32ba87993725856ab88998fe788"
 echo "SOURCE VERIFIED"
 python3 -B -m py_compile "$SCRIPT"
 python3 -B "$SCRIPT" --self-test
 OUT="$BASE/original_before_after_$(date -u +%Y%m%dT%H%M%SZ)_$$"
 python3 -B "$SCRIPT" --stage18-dir "$STAGE18" --output-dir "$OUT" \
   2>&1 | tee "$BASE/stage19.log"
 echo "HUMAN_REVIEW_FILE=$OUT/stage19_SEVEN_priority_original_before_after.md"
)
```

After success, `cat "$OUT/stage19_SEVEN_priority_original_before_after.md"` to copy into the chat, or transfer and attach the `.md`. **Stage19 has been committed to GitHub and hash checked, but operator has not yet executed it on IRIDIS6.** All 176 flagged original HH remain HOLD, nothing automatically approved.


## Stage20 user-approved RH source reconstruction candidates (2026-10-26; operator run pending)

[User source humidity decisions and exact evidence](docs/STAGE20_USER_HUMIDITY_DECISIONS_2026-10-26.md).
[Stage20 report-only original 117-candidate decision overlay script](scripts/stage20/20_make_investigator_decision_candidate_overlay_readonly.py).

The investigator decided:
- G01 WCr 2025-08-25 13:00 to 2025-08-26 01:30: 26 original low-RH measured HH → use original *processed ERA-pair RH* with tower T unchanged, rederive VPD coherently.
- G03 Vcm 2007-01-16 22:00 to 2007-01-17 14:30: all 34 original native RH values, **including transitions** (10 P1 + 24 surrounding) → rederive VPD coherently from each selected native T and original RH.
- G05 Vcm 2024-11-21–22: 26 P1 source QC0 low-RH records use processed ERA-derived RH with unchanged original tower T and rederived coherent VPD; nearby unapproved non-P1 source RH<5% is untouched.
- G06 Vcm 2025-10-13/14: 23 P1 measured low-RH records use processed ERA-derived RH with unchanged tower T and rederived coherent VPD. Another eight source-native RH≈0.3% appear during QC1/1 periods, but those original selected MDS VPD values already imply physical 66–83% RH, so hold separate source-RH-only field provenance and **do not rewrite good QC1 VPD without additional confirmation**.
- G02 Vcm 2007-12-15/16 original RH is missing all 19 P1 and original processed ERA RH itself becomes negative (as low as -12.21%).
- G04 Vcm 2008-02-06 original RH missing all 38 context HH; 11/12 P1 ERA RH negative.
- G07 Vcp 2011-01-01 original RH missing all three P1; processed ERA RH -6.00% to -6.42%; original tower measured RH resumes at 09:30 68.05% and 11:00 49.83%, not at 07:00–08:00.

At this stage **nothing has been written to forcing, original QC, CIME, or Slurm**. To create a **strictly NEW diagnostic candidate-only CSV/JSON** and examine exact proposed humidity/VPD values before preparing a production forcing update, run on IRIDIS6:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage20"
  COMMIT="801e16fd5df76d4b88183690766ebf937d1ce050"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/20_make_investigator_decision_candidate_overlay_readonly.py"
  STAGE18="$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage20/20_make_investigator_decision_candidate_overlay_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "e5ffc43fef13e79034e160058be478a819f5ad92"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/decision_candidates_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage18-dir "$STAGE18" --output-dir "$OUT" \
    2>&1 | tee "$BASE/stage20.log"
  echo "STAGE20_REPORTS=$OUT"
)
```

Expected **G01 26 + G03 34 + G05 26 + G06 31 = 117 candidate half-hours** (including G06 eight QC1 raw-low-RH entries with separate provenance). G02 19 + G04 12 + G07 3 = **34 separate missing-RH holds**. Two native source comparisons are essential: `RH_ERA` is diagnostic source-downscaled ERA RH, **not newly downloaded ERA5/ERA5-Land RH**; and the VPD must be `es(original TA_F)*(1 - chosen RH/100)`, never unmodified `VPD_ERA` combined with tower T. User has approved this candidate direction, but no source or production forcing changes have yet been run or verified.


## Stage22 user-approved NON-HOLD overlay (2026-10-26)

**Latest status supersedes any earlier Stage20 Stage21 instructions to keep all candidates on hold.** User: “hold我人工审核，其他的按照你的决定修改。” Stage21 was successfully run by operator (source verified) and categorized 57 remaining original P1 HH into A=44, B=11, C=2.

- **Scientific approval for a new reconstructed RH+VPD native-time overlay: 162 HH** = 117 original Stage20 candidate HH + 34 non-2015 US-Vcm QC0 extreme-low source RH records reconstructed using processed source ERA RH with observed tower TA + 11 QC2 records reconstructed using available original source RH and selected TA.
- **46 original P1 HH specifically HOLD for user's manual review** = 34 Stage20 native original RH missing events (G02 19, G04 12, G07 3), 10 A-class 2015-12-06 source extreme-low RH (source ERA T differs strongly and processed ERA RH can be <10%), plus 2 2008-12-27 C-class missing source RH events.
- **3 specific QC0 transition boundary HH not modified:** WCr 2025-08-25 12:30, WCr 2025-08-26 02:00, Vcm 2025-10-14 11:30, until user's explicit per-time replacement decision.
- Original 176 P1 HH = 130 approved P1 + 46 held P1; the 162-overlay row total additionally includes 32 Stage20 non-P1 transition / original source RH QC1 records. No double count.

[Stage22 operator-ready script](scripts/stage22/22_apply_decisions_to_versioned_native_overlay.py) and [decision provenance documentation](docs/STAGE22_APPROVED_NONHOLD_RECONSTRUCTION_2026-10-26.md).

**No IRIDIS6 Stage22 execution yet.** The script creates ONLY NEW output reports `stage22_VERSIONED_APPROVED_RH_VPD_native_overlay.csv` (162), `stage22_46_MANUAL_HOLD_P1_untouched.csv` (46), boundary QC table, manifest, and short operator review. It does NOT alter original source CSV/QC, existing DATM forcing, CLM-FATES cases, Slurm, or previous Stage18/20/21 files. Source `TA_ERA/VPD_ERA` were NOT independently verified as ERA5-Land; these values are processed source ERA and must carry reconstruction provenance.

Run the pinned one-call command in the Stage22 decision documentation; after checking exact results, manually review the 46 HOLD and source native edge discontinuities. Model-ready forcing creation remains blocked until full Batch05 1,750-HH QC/P2/P3 review, Post-v5 technical checks and remaining source-specific holds are resolved.


## Stage24 four explicitly approved edge-half-hour RH/VPD reconstructions (2026-10-26)

**Most recent investigator science decision** (supersedes earlier Stage23 manual EDGE HOLD *for precisely four named timestamps*): replace processed-source ERA-derived RH while **retaining original measured tower `TA_F`**, reconstruct physically coherent VPD; **do not expand interval**.

- E01 US-Vcm 2014-08-19 **08:30**, ERA-derived RH 56.194173% (previous source RH 17.18377%).
- E02 US-Vcm 2025-10-14 **11:30**, ERA-derived RH 75.805596% (previous source RH 37.98483%). Afterward 12:00–13:30 source RH≈99.46% is **unapproved plateau review**.
- E03 US-WCr 2025-08-25 **12:30**, ERA-derived RH 65.093868% (previous source RH 33.68535%). Preceding original 09:30–12:00 source RH=100% is **unapproved plateau review**.
- E04 US-WCr 2025-08-26 **02:00**, ERA-derived RH 91.924097% (previous source RH 32.35776%).

**Outputs after operator runs Stage24:** Stage22 existing 162 changed rows + exactly 4 approved edges = **166 versioned RH/VPD overlay half hours**; 46 original P1 human HOLD entries **byte-identical and unchanged**; original 176 P1=130 already approved + 46 held; 10 unapproved near-saturation plateau HH identified separately. All original FLUXMET, native source QC, DATM, CIME/Slurm remain unmodified; neither processed source `TA_ERA/VPD_ERA` nor derived `ERA_RH` has been independently verified as ERA5-Land.

[Stage24 pinned source script](scripts/stage24/24_merge_four_approved_edge_RH_to_versioned_overlay.py) and [Stage24 exact decisions, operation and provenance](docs/STAGE24_EXACT_FOUR_EDGE_APPROVALS_2026-10-26.md). **Script committed to GitHub; operator execution still pending.** Do not advertise a finished forcing: 46 P1 RH HOLD and P2/P3 source-science QC remain unresolved.


## Stage25 exact original 1750 anomaly crosswalk to Stage24 executed 166 approved rows

**Verified operator Stage24 SUCCESS 2026-10-26:** exactly 166 versioned approved RH/VPD overlay HH and 46 manual P1 HOLD with unchanged original FLUXMET/DATM/CIME/Slurm. Three previously identified large edge jumps fixed, **one remains**: WCr 2025-08-25 **12:00→12:30** jumps +6.032576601 hPa because source RH=100% at 12:00; do **not** auto-replace the earlier RH 100% plateau. WCr 2025-08-25 09:30–12:00 (six HH) and Vcm 2025-10-14 12:00–13:30 (four HH) source near-saturation platforms remain **unapproved science-review only**.

[Stage25 exact 1750/522 original source-to-overlay crosswalk](scripts/stage25/25_crosswalk_1750_source_anomalies_with_166_approved_readonly.py) and [Stage24 operator completion, Stage25 pinned execution instructions and science cautions](docs/STAGE25_ORIGINAL_1750_EXACT_CROSSWALK_AND_P2P3_QC_2026-10-26.md).

**Stage25 script already published to GitHub, operator still needs to run it.** Do not assume all 1574 original P2/P3 abnormal HH remain unapproved: Stage24's 166 approved overlay half-hours include 36 outside the original P1 tier and an **exact site+native-HH join** is needed to establish which coincide with original P2/P3 flags versus unflagged transition/edge rows. Stage25 reports per-original-event approved/HOLD/unapproved counts and per-episode/workstream evidence strategies. NO new automatic P2/P3 changes, no independent reanalysis downloaded, no final forcing or model jobs.


## Stage26 P2/P3 per-native-HH science candidate feasibility (2026-10-26)

Stage25 **successfully executed by IRIDIS6 operator** (not merely published):
- Original 1,750 abnormal native half-hours / 522 events exactly mapped.
- Current Stage24 **166 approved versioned overlay HH** consist of original anomaly P1 **130** and **36 out-of-original-screen transition/edge HH**.
- Original P1=176 consists of **130 candidate-approved** and **46 unchanged manual HOLD**.
- All **1,574 P2/P3 native flagged HH are still unapproved**; none overlaps the 166 approved overlay.
- Site breakdown remaining: US-Vcp 626, US-Wjs 401, US-Vcm 362, US-Var 62, US-WCr 62, US-UMB 23, US-Wkg 22, US-UMd 15, US-Whs 1, US-UiD 0.
- Stage25 first-match evidence groups **924 unresolved provenance**, **607 source processed ERA pair physically valid**, **38 MDS pair physically valid**, **5 original RH present**. These four groups are strictly mutually exclusive as implemented in Stage25, but they do *not* exhaust possible overlap of physically feasible source alternatives.

[Stage26 1,574 native-hour MDS/ERA/ERA-e/native-RH research-only candidates](scripts/stage26/26_reconstruct_p2p3_physics_candidates_research_only.py) and [operator command / scientific decision guide](docs/STAGE26_ALL1574_P2P3_SCIENCE_OPTIONS_2026-10-26.md).

Stage26 **pending operator execution**. It generates four mathematically distinct candidate hypotheses, records original source QC and source-vs-tower TA discrepancies, and partitions all 1,574 P2/P3 HH into *scientific evidence* subgroups. **No P2/P3 changes are approved by this step**; original FLUXMET, Stage24 approved 166, P1 HOLD 46, DATM and Slurm remain unmodified. This is intended to reduce human review to data-source/physics method decisions instead of 1,574 independent timestamps. Independent T/dewpoint meteorology is needed for unsupportable source alternatives and scientific corroboration. No actual full forcing or Post-v5 yet.


## Stage27 operator P2/P3 RH-source comparison, source risk and 483 episode priority (2026-10-26)

The Stage26 source audit has **executed successfully** on IRIDIS6. **All 1,574 original P2/P3 half-hours remain unapproved**, although all 1,574 have a mathematically feasible *processed source ERA-pair RH* candidate; options exist for 551 MDS pairs, 1,459 source ERA actual-vapor-pressure shadows, and 5 native source RH. These candidate counts overlap; 546 HH have both MDS and processed ERA RH alternatives. Original selected TA differs from source processed ERA TA by >5°C in **372 HH**, so unconditional source ERA pairing is scientifically unjustified. No independent ERA5/ERA5-Land downloaded.

[Stage27 native-HH MDS-vs-source-ERA RH disagreement, processed ERA assumption and 483 original P2/P3 episode risk screener](scripts/stage27/27_compare_p2p3_mds_era_and_temperature_risk_readonly.py); [Stage26 actual operator output and pinned Stage27 executable instructions](docs/STAGE27_P2P3_SOURCE_AGREEMENT_DISAGREEMENT_AND_RISK_2026-10-26.md). **Stage27 published; operator run pending.** It partitions by native RH present, MDS–ERA RH concordance, disagreement, ERA-only cases; flags temperature discrepancy and large VPD sensitivity, ranks original P2/P3 episodes and produces zero new forcing approvals.

The **166 Stage24 approved overlay** remains separate from 46 manual P1 HOLD and 10 unapproved saturated RH plateau HH. No original FLUXMET, production DATM, source QC or Slurm changes.


## Stage28 independent reference meteorology pilot and source UTC-offset gates (2026-10-26)

**Stage27 has been EXECUTED by operator (read-only):** all 1,574 original P2/P3 native HH remain SCIENCE-UNAPPROVED, across 483 original episodes. Stage27 source MDS and processed-source ERA humidity comparator outcomes were 23 pairs agreeing within 5 RH percentage points, 115 disagreeing 5–20 pp, **408 disagreeing >20 pp** (339 US-Vcp); **1,023 only processed-source ERA RH**, 5 original source RH available. Across all P2/P3, original selected-T minus processed-source ERA-T >5°C 372 HH, source ERA RH-conserving versus its actual vapor-pressure-conserving VPD difference >2 hPa 66 HH, and resulting candidate versus source original VPD >5 hPa 715 HH. Those flags overlap, and do not make any candidate scientifically approved.

Public AmeriFlux tower locations verified against official AmeriFlux pages: **US-Vcp (35.8641, −106.5965, 2501 m)**, **US-Wjs (34.4258, −105.8617, 1931 m)** and **US-Vcm (35.8885, −106.5322, 3043 m)**. The FLUXNET timestamp convention is local standard time without DST; release- and site-specific **BADM UTC_OFFSET has not yet been verified**.

[Stage28 high-risk native-hour pilot, official coordinates and source-ZIP/BADM UTC offset evidence preflight](scripts/stage28/28_independent_reference_metadata_and_priority_windows_readonly.py) and [operator instructions and time-metadata science cautions](docs/STAGE28_EXTERNAL_MET_REFERENCE_PILOT_CLOCK_GATE_2026-10-26.md). Code is on GitHub; operator Stage28 run is **PENDING**. Stage28 generates top 20 risk episodes (original timestamp windows), five P1 HOLD event reference windows and two RH platform windows plus original-site ZIP metadata evidence. It neither guesses timezone nor downloads ERA5-Land, modifies the original FLUXMET, existing approved 166, human HOLD 46, forcing or Slurm. Only after BADM UTC_OFFSET is verified can an independently downloaded ERA5-Land T/dewpoint pilot be joined correctly to the original tower clock for scientific decision-making.

This stage is designed to **break the audit-only loop** and prepare verifiable new observational/reanalysis evidence before deciding P2/P3 repair. Stage24's single residual WCr saturation-edge jump and the ten unapproved RH saturation-platform HH remain separately held for review.


## Stage29 original BIF grouped UTC_OFFSET evidence and conditional external meteorology request timestamps

**Stage28 successfully executed on IRIDIS6** (read-only). All three New Mexico priority-site original release ZIPs contain BIF `UTC_OFFSET=-7` evidence: US-Vcp GROUP_ID 4791/4799 (4799 DATE_START=200701010000), US-Wjs GROUP_ID 1493 (DATE_START=200705041330), US-Vcm GROUP_ID 1266/1274 (1274 DATE_START=200701010000). The previous Stage28 code's harmless `SyntaxWarning` about escaped Markdown backticks is fixed in GitHub; Stage28 rerun is not needed. The first Stage28 source review pilot comprises **20 high-risk P2/P3 episodes / 264 original anomalous HH**, 5 manual P1 HOLD windows containing **46 HH**, 2 unapproved saturated RH platforms; total **27 native event windows**. Source FLUXMET/DATM/Stage24 approved 166 rows/HOLD 46 unchanged.

[Stage29 verified BIF GROUP_ID UTC_OFFSET/date-range source scanner and exact 27 native-to-UTC conditional conversion](scripts/stage29/29_verify_bif_utc_offset_groups_and_convert_pilot_windows.py) and [Stage28 operator evidence, pinned Stage29 command and original BIF/ERA5-Land science prerequisites](docs/STAGE29_ORIGINAL_BIF_GROUP_TIMEZONE_COVERAGE_2026-10-26.md). Stage29 parses all native `UTC_OFFSET`, `UTC_OFFSET_DATE_START`, `UTC_OFFSET_DATE_END` under each GROUP_ID, checking full effective-dated intervals; it includes **US-WCr in Wisconsin** as a *separate source ZIP and timezone*, since WCr's saturation plateau cannot inherit the New Mexico -7 shift. No UTC conversion is authorized for external data requests if original grouped date ranges are ambiguous.

**Stage29 is on GitHub but operator execution pending**. Even after group verification, it does not make an ERA5-Land network request; the next step is a time-verified independent external 2 m T/dewpoint pilot, preserving provenance, dataset timezone, altitude discrepancies and original QC. No automatic P2/P3 repairs or model jobs.


## Stage30 Stage29-confirmed BIF offsets and research-only ERA5-Land pilot data requests

**Stage29 executed successfully on IRIDIS6.** All four original release BIF ZIPs parsed without conflict: original source UTC_OFFSET -7 h for **US-Vcp, US-Wjs, US-Vcm**, and -6 h for **US-WCr**. Actual SOURCE GROUP_ID: Vcp 4791 (undated), 4799 (start 2007-01-01 00:00); Wjs 1493 (start 2007-05-04 13:30); Vcm 1266 (undated), 1274 (start 2007-01-01 00:00); WCr 3522 (undated). All six groups lack END_DATE. Original 27 Stage28 pilot event windows had source coverage 26 `OPEN_ENDED_START_DATED_REVIEW`, 1 `ONLY_UNDATED_OR_END_ONLY_GROUP_REVIEW`; **no CLOSED_DATED complete source groups**. Candidate native LST to UTC conversion is +7h for 3 NM sites, +6h for Wisconsin WCr, without DST. The missing BIF end dates remain explicitly unverified; no alternate timezone inferred.

[Stage30 original source-preserving CDS ERA5-Land point time-series API request planner with explicit optional one-file research fetch](scripts/stage30/30_build_and_optionally_fetch_ERA5Land_reference_pilot.py) and [Stage29 operator original source evidence + pinned Stage30 commands](docs/STAGE30_ERA5LAND_RESEARCH_REFERENCE_PILOT_2026-10-26.md). The Stage30 script builds site+UTC-month T/dewpoint request manifests for the 27 original pilot event windows (20 original high-risk P2/P3 episodes, 5 P1 HOLD event ranges, 2 unapproved RH-saturation platforms), SHA-verifies Stage28/29 source reports, and outputs both per-event UTC candidates and CDS request JSON. Default **no network and no download**. Optional `--fetch --acknowledge-provisional-bif-offsets --max-fetch 1` requires operator-supplied CDS credentials and licence consent; it retrieves only one research reference payload to a new separate output path, not forcing.

**Stage30 script is committed but the IRIDIS6 operator has not run it.** Stage24 approved 166 versioned RH/VPD half-hours remain untouched; 46 P1 manual HOLD and original P2/P3 1574 unapproved. No full DATM forcing production, no model job submissions.


## Stage30 operator PASS — 11 research-only CDS plans, corrected time-series API dates

**Stage30 EXECUTED successfully on IRIDIS6 2026-10-26** (not a CDS download): 27 original native pilot windows grouped into **11 site/month reference acquisition requests**, `DOWNLOADS 0`. Sites selected by top-20 high-risk original episodes and manual holds/plateaus: **US-Vcm six**, **US-Vcp four**, **US-WCr one**, **US-Wjs zero** (Wjs 401 original P2/P3 anomalies are not represented by these particular 20 top-ranked episodes; a later balanced pilot must add Wjs). Prior Stage24 overlay 166, P1 manual HOLD 46, original P2/P3 unapproved 1574, native FLUXMET/DATM unchanged.

**CRITICAL POST-RUN CDS API request bug fix:** original Stage30 planner emitted `date` as a two-element list. ERA5-Land time-series API expects an ISO slash-separated date range string (`YYYY-MM-DD/YYYY-MM-DD`), not the standard ERA5-Land `year/month/day/time` request form. Patched Stage30 [script](scripts/stage30/30_build_and_optionally_fetch_ERA5Land_reference_pilot.py) commit `14d976fb4fb6e8d0514d677b0aa9ee5055a48a6b`, Git blob `3b5446297834ee4a4d587e668038d5eb0143a2c1`. **Do not use the old script for `--fetch`**. This patch changes only API request serialization and actual-request self-test, not original site times or scientific decisions.

[Stage30 operator PASS, limitations, corrected script and optional ONE research-only downloaded reference command](docs/STAGE30_ERA5LAND_RESEARCH_REFERENCE_PILOT_2026-10-26.md). First priority `ERA5L_US_Vcm_200712` (four-day H01 source RH missing P1 reference window), with user-configured CDS license/API. Original grouped BIF time zones have open-ended/undated effective-date metadata (Vcm/Vcp/Wjs UTC−7, WCr UTC−6): **UTC date candidates, not complete independently validated clock metadata**. ERA5-Land remains model reanalysis rather than an independent in-situ tower sensor. External data must be unit/time/grid-validated before any RH/VPD science approval.


## Stage31 real ERA5-Land first payload validated against H01 native HOLD (script ready, operator pending)

**Real first CDS request SUCCESS 2026-10-26 ~11:46 UTC** (user-provided log): `reanalysis-era5-land-timeseries` source **US-Vcm Dec 14–17, 2007**, original download ID `ERA5L_US_Vcm_200712`; source `ERA5L_US_Vcm_200712.cds_download` **20,935 bytes**, verified user-reported SHA256 `abda0a706aef79dc0eb7a8b50db1b66ed427c8a756b81965d9bb3dba2e315646`. Stage30 CSV/JSON plans still 11 site/month requests, 27 original study windows; **one actually fetched source**. This is NOT an approved humidity replacement. The BIF offset remains -7 LST (DATE_END missing).

[Stage31 exact first downloaded CDS file ZIP/NetCDF inspection plus 19 half-hour US-Vcm H01 P1 original RH manual-HOLD comparison](scripts/stage31/31_validate_first_ERA5Land_CDS_payload_and_Vcm_H01_readonly.py) and [operator-pinned command and provenance](docs/STAGE31_FIRST_CDS_PAYLOAD_H01_READONLY_REFERENCE_2026-10-26.md). Stage31 verifies actual downloaded file bytes and internal hourly UTC T/Td with xarray, compares to SHA-pinned original Stage18 tower source observations and Stage24's 46 unchanged manual P1 HOLD events, computes gridded ERA5-Land RH and research-only alternate tower-relative VPD hypotheses (fixed RH vs fixed actual water vapour pressure) with source-clock candidates. The first external download may be a **ZIP containing separate NetCDF parameter groups** (per official CDS ERA5-Land time-series PUG); the Stage31 script detects the format before opening.

**Stage31 is published, but operator has not run it yet.** Original H01 19 records remain human HOLD; all Stage24 approved 166 unchanged, 46 total P1 HOLD and 1574 P2/P3 unapproved. No model DATM/Slurm/science automatic approvals.


## Stage32 real H01 winter external humidity phase and forcing-boundary science screening

**Stage31 verified operator SUCCESS 2026-10-26**: real SHA-verified CDS ERA5-Land 2007-12-14..17 UTC downloaded ZIP (one internal NetCDF, 96 hourly records). Exactly **19** original H01 US-Vcm native LST (2007-12-15 21:00 to 2007-12-16 06:00) RH-missing half-hours paired with external 2m T and dewpoint; ERA5-Land **RH_w=67.680542–78.046519%**, bundled original processed source ERA-derived RH **−12.214486 to −0.708978%**; ERA5-Land 2m T **2.4203–6.002364°C colder** than original tower TA. Original source and model/DATM remain unchanged; grid RH does not prove actual tower RH. The original BIF -7 offset DATE_END absent; temporal and elevation sensitivity remain.

[Stage32 source-SHA-verified H01 ice/water phase, dewpoint water-vapour pressure reconstruction and pre/post boundary trial audit](scripts/stage32/32_Vcm_H01_19HH_ice_water_phase_and_boundary_sensitivity_readonly.py) and [operator instructions and technical science distinction](docs/STAGE32_VCM_H01_ICE_WATER_PHASE_BOUNDARY_REVIEW_2026-10-26.md).

**Critical physics:** ECMWF ERA5/ERA5-Land *dewpoint* is defined relative to water: derive actual e using `es_water(Td)`, then compute `RH_water=100e/es_water(T)` or `RH_ice=100e/es_ice(T)`. Do not use ice saturation at dewpoint as if it were an observed frost point. Stage32 keeps four distinct *unapproved* tower-VPD choices (grid RH or grid e retained, reference saturation over water or over ice); computes 19-row phase comparison, ±30min reference RH variability, two existing-source-boundary × four candidate checks. No scientific approval or automatic clipping of possible ice supersaturation. **Stage32 published, operator run PENDING.** Stage24 approved 166, original P1 HOLD 46 (H01 19), P2/P3 unapproved 1574, 10 prior RH plateau suspect HH remain preserved. Source FLUXMET/DATM/CIME/Slurm untouched.


## Stage33 original H01 humidity neighboring source gate and 10 extra independent reference pilots

**Stage32 EXECUTED successfully by operator (26 October 2026):** original Vcm H01 19 manually held RH-native HH are supported by actual independently retrieved ERA5-Land temperature/dewpoint reference; derived grid RH over water 67.68–78.05%, over ice 78.80–92.83% (water/ice difference up to 14.79 percentage points). Grid temperature 2.42–6.00°C colder than measured tower air temperature. Four alternate tower-temperature VPD sensitivities cause **no 30-min boundary jump >4 hPa** against immediately neighboring unchanged source original data, but the unchanged neighbors have original VPD **2.581 hPa (20:30 LST 15 Dec 2007)** and **2.588 hPa (06:30 LST 16 Dec 2007)**, suspicious near water saturation vapor pressure at ~−12°C. Source QC/original implied RH must be checked rather than treating artificial smoothness as a repair validation. No science approval was made; 46 P1 HOLD preserved.

[Stage33 exact original neighboring RH and QC audit, plus 10 optional real ERA5-Land gridded reference acquisitions](scripts/stage33/33_H01_neighbor_QC_and_prioritized_independent_ERA5Land_batch.py) and [pinned IRIDIS6 command and H01 human-review decision gate](docs/STAGE33_H01_NEIGHBORS_AND_OTHER_TEN_EXTERNAL_REFERENCES_2026-10-26.md).

Stage33 reuses the Stage30 corrected point time-series CDS request specs and sequentially fetches with explicit opt-in six original P1-HOLD / RH-platform targets (Vcm H02/H03/H04, Vcp H05, Vcm 2025 saturation, WCr 2025 saturation), three Vcp original high-risk P2P3 conflict months (2008 Apr–Jun), **and the first previously omitted US-Wjs high-risk Stage27 P2P3 episode**. Default is PLAN ONLY; `--fetch --acknowledge-provisional-bif-offsets --max-fetch 10` downloads all 10 to a **NEW research reference folder**, preserving filenames and SHA256. It does not overwrite the successful original Stage30 first H01 CDS file or any source/forcing/data assimilation. All original BIF UTC_OFFSET_DATE_END still missing, so scientific clock conversion remains provisional. **Stage33 published to GitHub; operator execution pending.**


## Stage34 10 actual ERA5-Land gridded reference files vs remaining QC source

**Stage33 successfully executed and downloaded all 10 CDS ERA5-Land research references** on 26 Oct 2026, including 4 remaining P1 HOLD original events (H02/H03/H04/H05), two RH saturation platforms (Vcm Oct 2025, WCr Aug 2025), three Vcp 2008 high-risk months and one first Wjs original P2/P3 high-risk episode. Together with Stage30 first H01 file, this is **11 externally downloaded gridded references**, not 11 scientifically approved RH/VPD replacements. All files have source size and SHA256 reported by the operator, retained in [Stage34 source-based documentation](docs/STAGE34_ACTUAL_TEN_ERA5LAND_FILES_HOLD_P2P3_EVIDENCE_2026-10-26.md).

**Stage33 original immediate H01 neighbor QC2 evidence:** 2007-12-15 20:30 US-Vcm tower/source TA=-11.136°C VPD=2.581 hPa implies water-RH **1.513015%**; 2007-12-16 06:30 TA=-10.784°C VPD=2.588 hPa implies water-RH **3.973442%**. Both are QC2/QC2, **not measured in situ QC0**. Stage33's `SUSPECT False` was only because it used RH<1% as a narrow flag; these records remain scientifically questionable and UNMODIFIED, adjacent to original 19 H01 human HOLD entries. No approval for expanding H01 to neighbors or choosing source ERA replacement.

[Stage34 actual ten-file SHA/ZIP/NetCDF/UTC Kelvin meteorology validator and original P1/P2P3/RH-platform source join](scripts/stage34/34_assess_10_actual_CDS_references_against_all_P1_P2P3_and_platforms_readonly.py). This reuses the **proven Stage31 parser pinned by Git blob SHA**, rather than implementing another parsing stack. It compares gridded T/dewpoint/RH to original tower T/VPD/QC, source MDS and processed source ERA companion, covers all **27 remaining H02–H05 original P1 HOLD HH** and all **10 original unapproved RH platform HH**, as well as the source P2/P3 HH coinciding with the 4-site external reference windows. Every downloaded source file is required to match exact operator SHA, original UTC date interval, variable names/units and site grid. No scientific automatic source approval.

**Stage34 GitHub code and docs committed, operator execution pending**. No change to existing 166 approved Stage24 overlay, 46 P1 HOLD (including 19 H01), remaining 1574 original unapproved P2/P3, source FLUXMET or DATM/Slurm. Original BIF UTC_OFFSET_DATE_END absent and reference remains gridded reanalysis, not in-situ station observation.


## Stage35 externally reference-matched P1/P2P3/plateau science decisions and VPD trials

**Stage34 executed successfully on IRIDIS6**: 10/10 actual new CDS ERA5-Land ZIP/NetCDF downloads fully SHA/UTC/2m T/dewpoint/grid verified against previously untouched native tower QC. Matched exactly **429 unique original unapproved HH** = **27 non-H01 manual P1 HOLD** + **10 unapproved original RH saturation-platform HH** + **392 original P2/P3**. H01 original 19 manually held native HH were previously assessed using the initial separately downloaded first CDS reference. Existing Stage24 **166 approved native source RH/VPD overlay** unchanged. 46 original P1 HOLD and 1574 original P2/P3 still unapproved, no DATM production forcing or Slurm jobs. Stage34 summary path: `/home/ly3n24/ameriflux_batch05_stage34/reference_validation_20261026T131903Z_715715`.

Stage34 Vcp P2/P3 original 382 matched native HH: **323** have RH reference closer to processed source ERA than original MDS (margin >5 RH pp), **10** closer to MDS, remainder **49** equivocal; **280** differ from source MDS RH by >20pp, only **6** differ from source processed ERA by >20pp. Wjs first 9 HH are all closer to processed source ERA than MDS, but these are only 9/401 total Wjs original P2/P3. Source processed ERA and newly downloaded ERA5-Land are both reanalysis-related: **concordance is not independent observed truth**. Vcm/Vcp original P1 manual HOLDs 26/27 differ from source ERA RH by >20pp, while RH platforms show meaningful disagreement for some original source HH. These results need event-based science decisions, not blind replacement.

[Stage35 SHA-pinned original 429 matched HH ➜ physical original-tower-temperature VPD method trials, 6 source-science review lanes and original P2/P3 episode-level decision matrices](scripts/stage35/35_external_reference_to_tower_VPD_trial_and_episode_decision_matrix_readonly.py) and [Stage34 operator real numerical results, science limitations and Stage35 IRIDIS6 command](docs/STAGE35_REAL_ERA5LAND_EVENT_METHOD_TRIALS_2026-10-26.md). The code derives two tower water-saturation VPD trials (source-ERA RH transported vs fresh-grid ERA5-Land RH transported) alongside separately preserving external-grid actual vapour pressure as a third RESEARCH-only hypothesis. It explicitly flags fresh tower-grid T>5°C, source RH disagreement, native source VPD reconstruction shift, original source-HOLD and saturation platforms, and separately records **two H01 pre/post source QC2 neighbors** with implied RH water 1.513% and 3.973% (not automatically edited). `P2P3_REANALYSIS_ERA_CONCORDANT_LOW_T_DIFF` is a **screening lane**, not a scientific forcing approval.

**Stage35 code and docs committed to GitHub, operator execution pending.** No source originals, approved overlays, user manual holds, or forcing CIME/Slurm edits.
