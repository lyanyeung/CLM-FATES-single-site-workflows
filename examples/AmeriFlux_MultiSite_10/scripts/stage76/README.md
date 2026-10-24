# Stage76 — 17 extreme RH cases and all 1–5% RH: ERA temperature/dewpoint and human review

> **SUPERSEDED BY THE LATEST HUMAN DECISION — 24 OCTOBER 2026.** The operator now explicitly directs **all 1,109 RH <5% records** (18 below 1%, including CA-Man, and 1,091 between 1% and 5%) to be recalculated using *actual native ERA5 T2m + 2m dewpoint + surface pressure*. The earlier Stage76 partial review and 'accept 1–5% as-is' classification are historical only. **Do not use Stage76 as the current release pipeline.** Use [Stage77](../stage77/README.md) instead. No actual native ERA5 recomputation has been reported complete yet.

**Scientific status: science review only, 0 meteorological replacements approved.** This stage follows the successful Stage75 ten-site numerical inventory and the CA-Man Stage74 operator-selected 18-row joint trial.

## Scope

- **17 unresolved RH <1% half-hours:** CA-Ca3 **7**, CA-Cbo **2**, US-Bar **8**. The CA-Man **one documented risk** remains separately retained, not included in these 17.
- **1,091 RH 1–5% half-hours** across the ten reviewed Batch01 candidates: CA-Ca3 **34**, CA-Cbo **26**, CA-Man **120**, CA-TP4 **6**, US-Aud **874**, US-Bar **31**. The other four sites have zero. These are *screening flags*, not 1,091 confirmed bad measurements; a persistently arid episode needs a different review than a single isolated low-RH spike.
- Classify contiguous half-hour RH1–5 episodes, maximum duration, entry/exit RH shifts, individual RH, VPD, temperature, and available FLUXMET `TA_F_QC` and `VPD_F_QC`. Produce per-event and per-episode **manual decision columns**.

## Crucial distinction: actual ERA5 dewpoint versus inferred dewpoint

**True native ERA5 comparison (preferred)** uses **ERA5** `2m_temperature`, `2m_dewpoint_temperature`, `surface_pressure` from **the same CDS product, nearest grid point and UTC hour**; convert K/K/Pa, interpolate temperature and **actual water vapour pressure** (from dewpoint) plus surface pressure to 30-minute intervals, and then calculate `RH`, `VPD`, `QBOT`. **Do not mix original tower Q/P with the new temperature**. Native hourly data may be obtained via [CDS ERA5 hourly time-series](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries).

For immediate offline comparison when native ERA5 has not been downloaded, Stage76 also reads co-timed raw **FLUXNET ERA5_HH** `TA_ERA + VPD_ERA + PA_ERA`; it estimates `e=e_sat(TA_ERA)-VPD_ERA` and **inverts this vapor pressure to an *inferred dewpoint***. FLUXNET ERA variables can be separately site-adjusted, so this column **IS NOT native ERA5 2m dewpoint**. Both alternatives remain distinct in the CSV and are never treated as interchangeable.

**Time discipline:** FLUXNET/AmeriFlux `TIMESTAMP_START` is local standard time with no daylight saving; ERA5 CDS `valid_time` is UTC. Stage76 accepts native matches **only** with `--utc-offsets-json`, e.g. a **provisional, site-metadata-dependent** JSON mapping the station to `UTC - forcing clock` in minutes. Verify it against site BADM and averaging semantics. No silent assumption that LST=UTC, and no clock/site-source approval is implied by a matched data row.

## How to run

Scripts:

- `76_batch01_low_RH_ERA_dewpoint_and_dry_review.py` — `--self-test`, `--check` (zero writes), `--audit` (new reports only). If a genuine native ERA5 input already exists, add both `--native-era5-csv PATH` and `--utc-offsets-json PATH`. The CSV schema is `site,valid_time_utc,t2m_K,d2m_K,sp_Pa,source_dataset`, where `source_dataset` must be `reanalysis-era5-single-levels`.
- `76b_download_native_ERA5_T2m_D2m_SP.py` — `--plan --events-csv PATH` prepares the exact 17-event site-year requests; `--download --events-csv PATH --outdir NEW_DIR` downloads the native ERA5 hourly time-series through **user-configured** `cdsapi` credentials. **Do not provide or commit your private CDS API token**.

Coordinates for CDS point requests are the published AmeriFlux locations CA-Ca3 (49.5346, −124.9004), CA-Cbo (44.3184, −79.9341), US-Bar (44.0646, −71.2881). ERA5 time-series picks the nearest 0.25-degree grid point; native ERA5 grid data are not identical to tower instruments.

The Stage76 audit creates:
- `17_RH_lt1_ERA_T_dewpoint_human_review.csv` — original RH, independent or inferred ERA RH/Td/VPD/QBOT, original QC0 neighbors and blank `decision` column.
- `1091_RH_1to5_human_review.csv` — each half-hour's RH/T/VPD, neighboring RH, FLUXMET quality evidence, source-derived ERA RH, episode ID and empty human decision field.
- `RH_1to5_consecutive_episodes.csv` — grouped dry-spell duration and isolated-vs-persistent risk.
- `10_site_low_RH_overview.csv` — site summaries.
- `native_ERA5_required_schema.csv`, `manifest.json` — import interface and SHA/provenance receipt.

**No automatic source replacement** even for RH below 1%: the ERA products are an alternative for **manual approval**. Especially for low RH, do not alter reliable QC0 observations or retain old tower humidity when swapping in ERA temperature. The root [mandatory same-source meteorology rule](../../../../README.md) and [CA-Man human-review precedent](../stage74/README.md) apply.

## Source references

- [AmeriFlux metadata site coordinates](https://ameriflux.lbl.gov/sites/site-search/)
- [FLUXNET product definitions, VPD_ERA and PA_ERA units](https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/)
- [CDS ERA5 hourly time series](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries)
- [AmeriFlux time-zone requirement](https://ameriflux.lbl.gov/data/aboutdata/data-variables/)
