# AmeriFlux MultiSite 10 — Batch 01

**Current checkpoint (operator-reported 22 October 2026):** all ten Batch 01 pinned releases extracted; point surfaces created; original QC v5 candidate forcing generated (nine stations via Stage18, US-Bar in isolated Stage20); 10/10 independent numerical audits PASS (Stage21); Stage22 read-only extreme/source QC completed. **Science approval, ZBOT, PFT/footprint verification, DATM and spin-up are still pending.** GitHub records operator results but cannot independently inspect live HPC outputs.


## Current post-QCv5 status — 22 October 2026

**Source of status:** operator-provided IRIDIS6 Stage18/20/21/22 logs. These are historical snapshots, not live telemetry. No HPC data or CIME cases were changed by the GitHub documentation update.

- Official AmeriFlux `FLUXMET_HH` `*_F` already incorporates release-provided gap-filling (QC0 measured, QC1 MDS, QC2 downscaled reanalysis). Our *additional* QC v5 follows the original [8-site QC v5 engine](../FLUXNET_MultiSite_8/scripts/03_prepare_eight_site_forcing_v5.py): physics checks, short isolated-gap interpolation (2 half-hours SW, 4 most other variables), ERA5_HH fallback for longer gaps, humidity reconciliation and review ledgers.
- [Stage18 pinned adapter](scripts/stage18/18_run_original_qcv5_for_ten_pinned_sites.py) produced nine candidates in `qcv5_trial_20261021T232839Z`. That historical run was **9/10 with US-Bar FAIL**, so its `INCOMPLETE` marker must **not** be removed merely because the site was separately recovered. The original eight-site engine SHA256 was `61be3c46b69ee77739019fab499c94dd1fc1f66a77b1c830815e33baf5351a35`.
- [Stage20 US-Bar isolated QC v5 sensitivity](scripts/stage20/20_us_bar_scoped_qcv5_sensitivity.py) generated a tenth **numerical candidate**, independently stored under `usbar_scoped_trial_20261021T234357Z`. The three QC2 records on 2004-01-14 08:00, 08:30, and 09:00 used the historical code's RH 1% floor after a narrowly scoped extra negative-RH allowance. Both source FLUXMET and ERA5 shared the anomaly; **independent observational validation is absent**.
- [Stage21 ten-site numerical/provenance auditor](scripts/stage21/21_verify_ten_qcv5_candidates.py) reported **10/10 numerical PASS, 1,292 logged variable-time edits, 528 manual-review records, 518 changes carrying official QC0 flags, 0 residual RH<=0, and 27 positive RH<1%**. PASS is *not* science approval.
- [Stage22 extreme/source-continuity auditor](scripts/stage22/22_post_qcv5_extremes_source_switches.py) (verified build `20261022_stage22_end_year_fix_v2`) reported **894 candidate half-hour TA jumps >8°C (0 new jumps introduced by QCv5), 2,306 candidate TA differences from ERA5 >15°C, 518 official QC0 edits and 0 nonpositive RH**. These are **review flags**, not proof that observations are wrong.
- Example QC0 distributions from Stage21: CA-LP1 400; CA-Man 97; CA-Ca3 10; US-Aud 11. CA-LP1 alone has 1,943 post-QCv5 TA–ERA differences >15°C; investigate time/source, footprint and physical plausibility, not blind reanalysis replacement. All BIF-derived ZBOT, grid/footprint PFT representativeness, dynamic DATM time records and FATES spin-up remain to do.

### Single post-v5 audit entry point (stages 21 and 22)

[Stage23 post-QCv5 runner](scripts/stage23/23_run_post_qcv5_science_gates.sh) is a **reproducible read-only launcher**, not a new QC algorithm. It fetches an explicitly pinned revision of stages 21/22 into a temporary directory, runs preflight, then optionally writes only timestamped QC report CSVs. It **does not** rerun stages 18/20 or alter either historical candidate, source ZIP, DATM, surface, or spin-up. Run on IRIDIS6 with **direct GitHub download instead of git pull**:

```bash
BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
mkdir -p "$BASE/scripts/stage23"
curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10/scripts/stage23/23_run_post_qcv5_science_gates.sh" \
  -o "$BASE/scripts/stage23/23_run_post_qcv5_science_gates.sh"
bash -n "$BASE/scripts/stage23/23_run_post_qcv5_science_gates.sh"
bash "$BASE/scripts/stage23/23_run_post_qcv5_science_gates.sh" check
# Re-run the already completed audits ONLY when needed:
# bash "$BASE/scripts/stage23/23_run_post_qcv5_science_gates.sh" audit
```

**Scientific acceptance gates before DATM (all pending):**

1. **QC0 traceability:** Review all 518 flagged measured-value edits, retaining original, changed value, justification and affected variable. Do not interpret a QC0 source code as infallible or automatically overwrite it.
2. **Post-repair extreme/context events:** Audit 894 existing >8°C TA half-hour jumps, 2,306 TA-versus-ERA >15°C flags (overlapping events are allowed), local context and source changes; leverage ES-LJu's coupled TA/VPD protocol and IT-Noe's full-episode diagnostic. A difference from ERA is not proof of a bad tower measurement.
3. **Low RH and US-Bar:** Review all 27 positive RH<1% and the three specially scoped US-Bar QC2 winter events; CH-Aws showed that positive input QBOT alone does not guarantee CLM 2-m diagnosed RH never becomes negative.
4. **Forcing-to-DATM inputs:** Verify BIF time-varying ZBOT, station-local timestamps, noleap 30-minute alignment, units, full seven-variable coverage, independent humidity reconstruction and deterministic per-site source checksums.
5. **Surface ecology:** Site IGBP/PFT/landunits for CA-TP1/3/4 (gridded high cropland), CA-Cbo (grid cropping), US-Aud (grassland), and other stations require footprint-aware scientific approval. **Do not submit spin-up solely because numerical QC passes.**

### Stage24 science-review queue (not another repair)

[Stage24 decision-matrix script](scripts/stage24/24_build_post_qcv5_science_review_queue.py) consumes the **already completed** Stage21 and Stage22 report directories, checks their site totals, and writes prioritized site/episode/timestamp queues plus an explicit list of the 518 source-QC0 edits. It does **not** reread the entire original meteorology or modify any candidates. Historical pinned report paths are defaulted, and can be overridden with `--stage21-dir` / `--stage22-dir`.

Run via direct GitHub download (no `git pull`):

```bash
BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
mkdir -p "$BASE/scripts/stage24"
curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10/scripts/stage24/24_build_post_qcv5_science_review_queue.py" -o "$BASE/scripts/stage24/24_build_post_qcv5_science_review_queue.py"
python3 -m py_compile "$BASE/scripts/stage24/24_build_post_qcv5_science_review_queue.py"
python3 "$BASE/scripts/stage24/24_build_post_qcv5_science_review_queue.py" --check
python3 "$BASE/scripts/stage24/24_build_post_qcv5_science_review_queue.py" --run
```

**Next gate:** human decisions about flagged QC0, temperature episodes, low RH and site ecological representation. No site has scientific approval or DATM yet.

### Data version policy

Never edit official release CSVs, the original shared QC-v5 engine, or previously generated numerical candidates in place. All site-specific remedies must create new versioned site-limited trial folders and replacement ledgers. The separate Stage20 US-Bar sensitivity is **not** a global change to QCv5 humidity thresholds. ERA5_HH used by the official FLUXNET release is **not** verified independent ERA5-Land; do not claim ERA5-Land replacement occurred. Do not delete or change the Stage18 incomplete marker to imply unified approval.

---

## The ten source releases

| Site | Original release archive stem | Labelled release window |
| --- | --- | --- |
| BR-Ma2 | `AMF_BR-Ma2_FLUXNET_1999-2016_v1.3_r1` | 1999–2016 |
| CA-Ca3 | `AMF_CA-Ca3_FLUXNET_2001-2024_v1.3_r1` | 2001–2024 |
| CA-Cbo | `AMF_CA-Cbo_FLUXNET_1996-2024_v1.3_r1` | 1996–2024 |
| CA-LP1 | `AMF_CA-LP1_FLUXNET_2007-2024_v1.3_r1` | 2007–2024 |
| CA-Man | `AMF_CA-Man_FLUXNET_1994-2008_v1.3_r1` | 1994–2008 |
| CA-TP1 | `AMF_CA-TP1_FLUXNET_2002-2023_v1.3_r1` | 2002–2023 |
| CA-TP3 | `AMF_CA-TP3_FLUXNET_2002-2023_v1.3_r1` | 2002–2023 |
| CA-TP4 | `AMF_CA-TP4_FLUXNET_2002-2023_v1.3_r1` | 2002–2023 |
| US-Aud | `AMF_US-Aud_FLUXNET_2002-2024_v1.3_r1` | 2002–2024 |
| US-Bar | `AMF_US-Bar_FLUXNET_2004-2023_v1.3_r1` | 2004–2023 |

All exact names are in [sites.tsv](sites.tsv). The release-window labels are not independently checked data coverage; inspect BIF, meteorology, and missing years at the next stage. Do not assume a model-year spin-up target or a meteorological repeat cycle yet.

## Stage 00 — upload source archives (LOCAL WSL / VS Code)

The example assumes the ZIPs are in `/mnt/d/Fluxes_Tower_Experiment/AmeriFlux/`; override `LOCAL_ROOT` for your real folder. Files can be `<package>.zip` or extracted `<package>/` folders. All ten are preflight-checked before anything is uploaded. Existing remote ZIP files are not overwritten, and the transfer is checksum-verified.

```bash
# Execute on your LOCAL WSL terminal, not inside IRIDIS Remote SSH.
cd ~/CLM-FATES-single-site-workflows
# Download the required scripts directly from GitHub; avoid git pull with unresolved local conflicts
LOCAL_ROOT='/mnt/d/Fluxes_Tower_Experiment/AmeriFlux' \
  bash examples/AmeriFlux_MultiSite_10/scripts/stage00/00_upload_ameriflux_10.sh
```

Destination:
`/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/packages/<PACKAGE>.zip`.

If the remote file has the same name but differs from the local ZIP, the transfer stops at SHA256 verification; inspect manually rather than overwriting.

## Stage 01 — recursive extraction (IRIDIS6 / VS Code Remote SSH)

```bash
cd ~/CLM-FATES-single-site-workflows
# Download the required scripts directly from GitHub; avoid git pull with unresolved local conflicts
python3 examples/AmeriFlux_MultiSite_10/scripts/stage01/01_extract_ameriflux_10.py
```

The script looks in each site-specific `forcing/packages/` and `MY_EC_SITE/_incoming_zips/`. If ZIP files already exist somewhere else on IRIDIS, **skip Stage 00** and use:

```bash
python3 examples/AmeriFlux_MultiSite_10/scripts/stage01/01_extract_ameriflux_10.py \
  --incoming-dir /path/to/your/ameriflux_zip_folder
```

Single-site extraction and a later read-only validation are also supported:

```bash
python3 examples/AmeriFlux_MultiSite_10/scripts/stage01/01_extract_ameriflux_10.py --sites CA-Man US-Bar
python3 examples/AmeriFlux_MultiSite_10/scripts/stage01/01_extract_ameriflux_10.py --audit-only
```

CSV output: `MY_EC_SITE/<SITE>/forcing/raw/<PACKAGE>/*.csv`. The script expands nested ZIPs, validates size/CRC32, skips byte-identical existing CSVs, rejects conflicting existing CSVs, and checks BIF + FLUXMET_HH existence. Missing ERA5_HH is only a **warning**. All source ZIPs remain intact. A JSON inventory stays on IRIDIS at:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports/stage01_extraction_summary.json`

No model files are deleted or relocated. The next work item is a **scientific source audit**: actual temporal coverage, variable headers/QC, meteorological gaps, BIF tower-height metadata, land cover and FATES PFT decisions, followed by forcing/DATM development. `CA-Man`'s 1994–2008 label is relatively short and warrants specific coverage review.


## Stage 02: AmeriFlux BIF geolocation preflight (read-only)

Stage 01 extraction and structural inventory succeeded at all 10 sites according to operator-provided IRIDIS output (16 CSV files per site, including one BIF, one FLUXMET_HH and one ERA5_HH). This **does not validate meteorological forcing, PFT or temporal coverage**. Before following the older ICOS surface-generation example, inspect every station's BIF coordinates using the [Stage 02 read-only preflight](scripts/stage02/02_check_10_bif_coordinates.py).

```bash
BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10"
REPO="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
mkdir -p "$BASE/scripts/stage02"
curl -fL "$REPO/examples/AmeriFlux_MultiSite_10/scripts/stage02/02_check_10_bif_coordinates.py" -o "$BASE/scripts/stage02/02_check_10_bif_coordinates.py"
curl -fL "$REPO/examples/AmeriFlux_MultiSite_10/sites.tsv" -o "$BASE/sites.tsv"
python3 "$BASE/scripts/stage02/02_check_10_bif_coordinates.py" | tee "$HOME/AmeriFlux_10_stage02_bif.log"
```

The script does not create CTSM surfaces, modify ZIP/CSV input, or submit any Slurm jobs. It verifies that each release's BIF supplies one valid latitude/longitude pair, prints available IGBP labels, and highlights ambiguous metadata. Surface files should only be generated after coordinate and vegetation-representation review. CTSM year-2000 surface gridding does not establish EC footprint representativeness.

## Stage 03 — CTSM point surfaces (reference year 2000)

**Observed prerequisite:** user-provided 21 October 2026 IRIDIS6 logs show **10/10 Stage 01 extraction and Stage 02 BIF geolocation checks PASS**. The BIF classes are six ENF sites (CA-Ca3, CA-LP1, CA-Man, CA-TP1, CA-TP3, CA-TP4), two DBF (CA-Cbo, US-Bar), one EBF (BR-Ma2) and one GRA (US-Aud).

[Stage 03 guarded surface generation](scripts/stage03/03_make_10_surfaces.sh) adapts the existing [13-site surface script](../FLUXNET_MultiSite_13/scripts/stage02/02_make_13_surfaces.sh) for exactly the ten AmeriFlux source releases. It reads BIF `LOCATION_LAT` and `LOCATION_LONG` afresh and uses CTSM `tools/site_and_regional/subset_data point --surf-year 2000 --create-surface --create-user-mods`. The same default_data_2000.cfg edits as the four prior ICOS experiments are retained for comparability.

**Safety:** `--check` (default) is read-only and checks all 10 coordinates, exact release paths, CTSM tools/inputdata, and any existing output. `--run` must be requested explicitly; it never overwrites a different or partial surface/configuration and preflights all 10 sites before writing anything. Completed existing outputs are skipped. A failed generation may leave a partial site output, which is intentionally blocked from automatic overwrite/retry until investigated.

Use **direct GitHub downloads** on IRIDIS6; do not use `git pull`:

```bash
BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
mkdir -p "$BASE/scripts/stage03"
curl -fL --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10/sites.tsv" -o "$BASE/sites.tsv"
curl -fL --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10/scripts/stage03/03_make_10_surfaces.sh" -o "$BASE/scripts/stage03/03_make_10_surfaces.sh"
bash -n "$BASE/scripts/stage03/03_make_10_surfaces.sh"
bash "$BASE/scripts/stage03/03_make_10_surfaces.sh" --check
# When all ten have passed the dry-run and outputs have been reviewed:
bash "$BASE/scripts/stage03/03_make_10_surfaces.sh" --run
```

Expected output for each site: `<SITE>/subset_data/surfdata*.nc`, `<SITE>/subset_data/user_mods/`, and `<SITE>/<SITE>_data.cfg`. These are **not** meteorological forcing or spin-up runs.

**Scientific warning:** a coarse-grid year-2000 CTSM surface is not automatically representative of the tower EC footprint or of the BIF IGBP classification. **US-Aud is a grassland (GRA)** and requires particular scrutiny if using forest-focused FATES parameterization; the BIF vegetation label by itself does not validate a CLM-FATES natural-PFT configuration. Similarly, CA-TP1/CA-TP3/CA-TP4 are geographically close but physically distinct tower sites. Surface crop/natural-vegetation fractions, land cover, and selected FATES PFTs need a separate scientific audit before forcing/CIME. Source FLUXMET/ERA5 coverage and meteorological QC are still pending.

## Stage 04 — read-only surface/PFT and FLUXMET/ERA5 source quality audits

**Prerequisites confirmed by operator on 21 October 2026:** Stage 01 extraction 10/10; Stage 02 BIF coordinates 10/10; Stage 03 CTSM point surfaces created 10/10 (year-2000 reference, no `--dompft`). These are structural/operational achievements; they are **not proof of valid FATES vegetation representation or approved meteorological forcing**.

- [Stage 04a surface auditor](scripts/stage04/04a_audit_10_surfaces.py): read-only checks `surfdata*.nc`, required files, landunit fractions, `PCT_NAT_PFT` length (15 or 16, with caution for index 15), and CLM natural tree/grass/shrub percentages. It flags gridded cropland and BIF forest/grass mismatches **for review**, without assuming `--dompft` should be set. Particularly inspect US-Aud GRA and the CA-TP1/TP3/TP4 sites.
- [Stage 04b source meteorology auditor](scripts/stage04/04b_audit_10_met_sources.py): reads **only the exact pinned FLUXMET_HH/ERA5_HH** files from each release, chunk by chunk; checks annual NO_LEAP half-hourly timestamps, duplicates, `TA/VPD/PA/SW_IN/LW_IN/WS/P` completeness, numerical limits, original QC code counts, and the humidity feasibility reconstructed from TA (°C), VPD (hPa), PA (kPa). ERA companion products are **not assumed independent ground truth**. Original source files are never changed.

**Execution on IRIDIS6 with direct GitHub downloads (no git pull)**:

```bash
BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
mkdir -p "$BASE/scripts/stage04"
curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10/sites.tsv" -o "$BASE/sites.tsv"
curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10/scripts/stage04/04a_audit_10_surfaces.py" -o "$BASE/scripts/stage04/04a_audit_10_surfaces.py"
curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10/scripts/stage04/04b_audit_10_met_sources.py" -o "$BASE/scripts/stage04/04b_audit_10_met_sources.py"
python3 -m py_compile "$BASE/scripts/stage04/"*.py
python3 "$BASE/scripts/stage04/04a_audit_10_surfaces.py"
python3 "$BASE/scripts/stage04/04b_audit_10_met_sources.py"
```

Small timestamped CSV/JSON reports are kept on IRIDIS under `CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports/stage04[a,b]_*`; no tower CSV, NetCDF, or report is committed to GitHub. The scripts do not create or submit CIME/Slurm jobs. **Do not interpret Stage 04 structural PASS as permission to start spin-up.** Next: inspect individual flagged source-year events, tower measurement heights/ZBOT, PFT/soil/landunit representativeness, and only then prepare an isolated provisional forcing candidate and DATM.

## Stage 06–09: Event-level QC provenance and humidity diagnostics (21 October 2026)

**Evidence from operator-provided IRIDIS6 reports, not live execution by GitHub:**

- Stage 06 reconstructed **1,744 flagged source/site/half-hour records** and 12 groups with at least three stations sharing the same **local** clock timestamp; **0 differences** relative to Stage 04 source-year anomaly counts.
- Stage 07 paired **all 1,744** source records with the other source at the same site-local time. **1,672** flagged records had a counterpart not triggering the same physical check; **72** had a counterpart triggering the same physical flag. These categories are **not** an authorization to overwrite FLUXMET with ERA5.
- Stage 08 identified **1,708 unique site-local timestamps**, with **36 timestamps** flagged in both sources (72 source records). Among the 1,672 source-specific rows, **1,665** received a high-priority humidity physical flag and **7** a hard-range flag. The same site/source/calendar-day/clock-time pattern did **not** recur in both 2004 and 2016 under the strict Stage 08 matching rule; this does not establish independence of the source data.
- Particularly high source-event counts: **CA-LP1 869**, **CA-Man 578**. Stage08 leaves **every record on HOLD**. A matching ERA5_HH timestamp or a numerically plausible companion is not independent validation. Where FLUXMET QC=2 the release may already rely on ERA-derived meteorology.

**[Stage 09: diagnose humidity severity and episodes](scripts/stage09/09_diagnose_humidity_severity.py)** operates solely on Stage 07's `paired_anomaly_events.csv`. It categorizes RH <= 0, RH > 101/102/105, specific-humidity anomalies, hard-range violations, source QA/QC provenance for affected variables, identical TA/VPD/PA values, and consecutive 30-minute anomaly episodes. Liquid-water RH conventions are retained for comparability, with no automatic switch to ice saturation or inferred replacement values.

IRIDIS6 execution: **download directly from GitHub rather than using `git pull`**:

```bash
BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10"
RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
mkdir -p "$BASE/scripts/stage09"
curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10/scripts/stage09/09_diagnose_humidity_severity.py" -o "$BASE/scripts/stage09/09_diagnose_humidity_severity.py"
python3 -m py_compile "$BASE/scripts/stage09/09_diagnose_humidity_severity.py"
python3 "$BASE/scripts/stage09/09_diagnose_humidity_severity.py" | tee "$HOME/AmeriFlux_10_stage09.log"
```

Reports are isolated on IRIDIS in timestamped `stage09_humidity_severity_*` directories. **Nothing is changed in raw tower/ERA data, generated surfaces, DATM, CIME cases or Slurm jobs.** Do not infer ecological equilibrium or validated spin-up readiness from numerical completeness. Separate landcover/PFT review is still required for CA-TP1/3/4, CA-Cbo and US-Aud.
