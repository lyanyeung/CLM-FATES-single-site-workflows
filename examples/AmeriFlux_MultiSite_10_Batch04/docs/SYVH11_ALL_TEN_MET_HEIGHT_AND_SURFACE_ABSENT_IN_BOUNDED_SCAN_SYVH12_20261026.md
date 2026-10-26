# Batch04 actual SYVH11 — all ten selected full met SHA PASS; point surface, CIME and measured ZBOT evidence not found in scanned paths

**Actual IRIDIS6 operator stdout, 2026-10-26 13:28 UTC.** Final selected SYVH9 full ten-site manifest SHA256 **`358816b1f93ce8014b8f166fce7c3d0b43d590254c78ef98d2357269f88d9562`**, `SYVH11 SOURCE PIN PASS`. No source/surface/domain/model writes.

For **all ten Batch04 stations**:
- Original SHA-verified Stage05/Stage08 FLUXNET BIF offers **no independently verified `VAR_INFO_HEIGHT` paired with `TA_F`, `WS_F` or `WIND`** under exact `VARIABLE_GROUP+GROUP_ID`: each site `BIF_TA_HEIGHTS=[]`, `BIF_WS_HEIGHTS=[]`, `BIF_WIND_HEIGHTS=[]`.
- No surface or domain NetCDF found in **bounded** ten-site directory scan used by SYVH11 (`SURFACE_DOMAIN_FILES=0` for each site).
- No CIME case directory name matching these station IDs in scanned immediate known case roots (`CASE_CANDIDATES=0` for each site).
- These are search-scope conclusions, **not** proof no source files exist in global scratch/inputdata, no published station sensor heights exist online, or original/site projects never had CIME cases.
- Canopy `HEIGHTC` is **not** a sensor measurement ZBOT. Exact canopy metadata: US-SP1 24.2m, US-SRG 0.5m, US-SRM 2.5m, US-Slt 9.52m, US-Syv 27.5m, US-Ton 4.449/4.61/9.16/10.64m; US-Rpf/Seg/Ses/Uaf no finite canopy record in the audited product. **NEVER** assign these to `ZBOT`, extrapolate TA or wind heights, or imply canopy observations determine height for atmosphere.
- **Met input science:** Ten exact complete source SHA, seven core met field physical/NOLEAP numeric `Gate-0 10/10 PASS`, verified independent ERA5-Land 12 target downwelling LW half-hours already applied and source-audited. There are only the 3 preserved source VPD 0.001-hPa quantisation edge cases. This status **does not** imply scientific source QC0 temperature holds or actual case field mapping approved.

Actual report:
```
/home/ly3n24/ameriflux_batch04_manual_review/Batch04_SYVH11_existing_surface_CIME_ZBOT_BIF_20261026T132815Z_07c18753.json
```
SHA256 `e1141218b9c9c518bf2e0f7777cab15529276e9173e2dae2400c8e06c7d8b286`.

## Fast path — build versioned, gridded 2000 point-surface *research candidates* while ZBOT scientific source evidence remains separate

Archived technical method already used for the original European cohort is [six-site `02_make_6_surfaces.sh`](../../FLUXNET_MultiSite_6/scripts/02_make_6_surfaces.sh). It uses original CTSM `tools/site_and_regional/subset_data point --create-surface --create-user-mods`, root `CTSM`, global `inputdata`, `default_data_2000.cfg`, `surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc`, `fv0.9x1.25_141008_ESMFmesh.nc` and `--surf-year 2000`. This is a **technical gridded baseline**, not a scientist-reviewed actual EC tower observed PFT/soil/surface.

New [`stage_syvh12_prepare_ten_point_surfaces_source_locked.py`](../scripts/manual_review/stage_syvh12_prepare_ten_point_surfaces_source_locked.py), pinned GitHub revision **`6426239e2737b6ab4918408c7f70fab03e51cbf3`**, checks:
1. Exact operator final SYVH9 manifest (source SHA for all ten files, actual SYVH9 12 LW receipt and 10/10 seven-met Gate-0 receipt), Stage05 original BIF source provenance (three sites) / Stage08 (seven sites).
2. Verified exact BIF lat/lon and UTC offsets, including the **pre-existing user-approved** US-Seg BIF group1495 point lat **34.3623**, lon **−106.7020**, elevation **1596m** (using the canonical original SHA-pinned [`coordinate_decisions.tsv`](../coordinate_decisions.tsv)).
3. Existing CTSM `subset_data` executable, global `inputdata` root and original `default_data_2000.cfg` against exactly the established six-site base configuration; stops rather than inventing another resolution/PFT baseline.
4. `--build` creates all ten **under a fresh, timestamped, uniquely named experiment-only output tree** `.../stage12_provisional_ctsm_point_surfaces_RESEARCH_ONLY/candidate_...`, creates a separate per-site CFG; no original `sites/MY_EC_SITE/<site>/subset_data`, original user_mods, weather CSVs, models/CIME cases, Slurm jobs are touched. Verifies each newly created NetCDF surface is a finite 1x1 point, records full SHA, actual grid-cell center vs original tower coordinate, and requires natural land/PFT fields. Retains new full source/CFG/run-log receipt per station.
5. `--preflight` does not write anything, and `--build` automatically repeats the preflight before touching its isolated directory. A missing global CTSM/inputdata/tool binary or changed grid base stops before build. A tool runtime error stops after leaving a **partial isolated candidate** for audit; it does not delete existing resources or silently approve the incomplete set.
6. Does not create actual domain/CIME configuration, **does not assign ZBOT**, alter source PFT/soil, or claim the CTSM gridded year-2000 PFT matches in situ station vegetation. Another science audit and domain/height field mapping decision are mandatory before use in CLM-FATES.

## One-shot IRIDIS6 source-pinned command

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="6426239e2737b6ab4918408c7f70fab03e51cbf3"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/coordinate_decisions.tsv" -o "$BASE/Batch04_approved_coordinate_decisions.tsv"
  SCRIPT="$BASE/stage_syvh12_prepare_ten_point_surfaces_source_locked.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/scripts/manual_review/stage_syvh12_prepare_ten_point_surfaces_source_locked.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --self-test
  python3 -u -B "$SCRIPT" --preflight 2>&1 | tee "$BASE/Batch04_SYVH12_surface_PRECHECK.log"
  python3 -u -B "$SCRIPT" --build 2>&1 | tee "$BASE/Batch04_SYVH12_point_surfaces_BUILD.log"
)
```

**Completion** requires actual terminal `SYVH12 TEN ISOLATED POINT SURFACE CANDIDATES CREATED 10/10` and full new per-site surface SHA/latlon logs. Even completion is **only provisional**, not DATM or model spinup approval. If the preflight fails, do not substitute arbitrary surface or run global recursive searches on the HPC filesystem: first verify the actual CTSM inputdata configured for this account.

**Parallel scientific uncertainty to resolve separately:** Original BIF contains no exact TA/wind instrument `VAR_INFO_HEIGHT`. Find actual source in station BASE/BADM portal documentation, site operator metadata, or external published station description; if truly unavailable, future met reference-height policy must be explicitly recorded for each site and not mislabeled as observed. No artificial `2m ZBOT` may be silently asserted; canopy `HEIGHTC` is never equivalent.
