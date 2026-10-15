# Stage 17 — ERA5 / ERA5-Land external reference for DE-Gri and FI-Let

**Status:** proposal and reference-only workflow, 2026-10-14. No forcing repairs approved.

## Precedent from the user's repository

`examples/FLUXNET_MultiSite_11/scripts/stage09/01_CH_Aws_dewpoint_reference.py`: explicit archive requests `models=era5` and `models=era5_land`, original UTC hourly references, raw year/model JSON, checked timestamps, no unreviewed forcing modification.

`examples/FLUXNET_MultiSite_11/scripts/stage10/01_CH_Aws_reference_validation.py`: empirical comparison to QC=0/1 tower observations and separate scientific uncertainty.

`examples/FLUXNET_MultiSite_11/scripts/stage11/01_CH_Aws_ERA5Land_first_humidity_trial.py`: versioned derived-candidate workflow with unchanged parent data and SHA256 provenance. In the *current* work, **Stage17 is deliberately reference-only**; no Stage17 forcing exists until the evidence is examined.

## Problem

- DE-Gri: 2,352 QC=1 records; 264 above 8°C from the original FLUXNET `TA_ERA` baseline; 52 suspect blocks, 30 high-priority, 234 high-priority halfhours. Repeated identical paired TA/VPD across dates, and both warm and cold departures.
- FI-Let: 3,589 QC=1 records; 201 above 8°C; 30 suspect blocks, 19 high-priority, 190 high-priority halfhours. Some winter warm MDS gap fills disagree with reference by ~15°C while nearby QC=0 tower data agree much more closely.
- Stage16 flags are **review priority**, not confirmed source corruption. A strong grid/tower bias may be seasonal or local.
- Existing Stage15 selected-forcing manifest and all prior versions are untouched.

## Site coordinates and proposed clock convention

FLUXNET site information:

- DE-Gri, Grillenburg: 50.9500 N, 13.5126 E, site elevation ~385 m. Local standard clock UTC+1.
- FI-Let, Lettosuo: 60.6418 N, 23.9595 E, site elevation ~111 m. Local standard clock UTC+2.

Verify each supplied tower timestamp convention with BIF/product documentation before treating clock offsets as final; the script also generates ±1-hour clock sensitivity scores from true tower QC=0 records. Do not select DST based on correlation maxima alone.

## Reference retrieval

Open-Meteo archive endpoint: `https://archive-api.open-meteo.com/v1/archive`

Force **separate** `era5` and `era5_land` runs; never `best_match` or the blended `era5_seamless` product. Retrieve hourly `temperature_2m`, `dew_point_2m`, `relative_humidity_2m`, `surface_pressure`, with `timezone=GMT`. Each cache covers one relevant year plus 2-day margins and is kept immutable. Model years are discovered from Stage16's non-zero yearly QC1 anomaly counts (15 distinct site-years; 30 expected requests in this snapshot).

The API source is not a separate field observation: ERA5-Land is related to ERA5 through atmospheric driving. Data served through Open-Meteo may not be numerically identical to site-downscaled FLUXNET `TA_ERA`. Record provider, model, retrieval date, altitude, coordinates, source hashes and license.

## Validation

1. For both models, test native UTC offsets shifted into station-local **standard** time.
2. On each year, compare model 2-m temperature against *observed* FLUXNET `TA_F_QC=0` only, with RMSE/MAE/bias and correlation. This is observation-based QC in context, not enough to prove every flagged point.
3. For Stage16 QC=1 suspect timestamps, compute ±30-day local QC0 tower-model temperature bias for each model (min 48 valid records).
4. Classify screen-only: both references physically valid, model T difference ≤5°C, both QC0-bias-adjusted models differ from QC1 MDS by ≥8°C in the same direction. Record model RH and an *unapplied* paired TA/VPD proposal. The 5°C, 8°C and 48-record thresholds are prioritization choices, **not automatic repair or scientific approval**.
5. Compare cases with model disagreement, bias, topography, official timestamp convention, and QC source transitions. For cold conditions, document water vs ice saturation formula sensitivity before choosing VPD.
6. Only after review: create a **separate**, site-specific `--check`/`--run` *trial* modifying the confirmed QC1 intervals. Pair TA with reference-constrained RH-derived VPD and recompute QBOT from verified PSRF. Source flags in original files must remain unchanged; write separate provenance ledger and candidate QC flags. Document all measured QC0 decisions separately.
7. Run full-site meteorological and precip screens across the latest selected manifest before moving to BIF/ZBOT.

## Script and outputs

`17_DEGri_FILet_ERA5_ERA5Land_crosscheck.py`:

- `--mode preflight`: verify Stage16 reports, manifest and pinned original raw sources; no writes.
- `--mode fetch`: cache checked UTC hourly model JSON by site, model, year. Re-runnable; no overwrite of existing valid/invalid cache.
- `--mode assess`: create new `science_review_v1` report directory and return: `00_clock_offset_sensitivity_QC0.csv`, `01_measured_QC0_T_validation_by_year.csv`, `02_all_QC1_suspect_events_ERA5_ERA5Land.csv`, `03_Stage16_blocks_with_two_model_evidence_PENDING.csv`, `04_reference_provenance_sha256.json`.

**Never commit raw FLUXNET, meteorological source caches, derived observation CSV, user-specific paths, credentials, or large NetCDFs to public GitHub.** Publish only generic scripts, field definitions, methodology and anonymized summary counts consistent with data policy.

## Reference links

- https://github.com/lyanyeung/CLM-FATES-single-site-workflows/tree/main/examples/FLUXNET_MultiSite_11
- https://fluxnet.org/sites/siteinfo/DE-Gri
- https://fluxnet.org/sites/siteinfo/FI-Let
- https://open-meteo.com/en/docs/historical-weather-api