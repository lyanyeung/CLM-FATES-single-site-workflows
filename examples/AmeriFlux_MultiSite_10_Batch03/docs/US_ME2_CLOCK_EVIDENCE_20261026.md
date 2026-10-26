# US-Me2 documented clock, 2026-10-26

See the [docs README](README.md) for Chinese status and execution instructions. The complete runnable script is also archived [inside docs/code](code/14a_US_Me2_documented_clock_READONLY.py), identical to the maintained Stage14a script.

The missing UTC offset has now been recovered from the user's separately downloaded AmeriFlux site BADM. The selected FULLSET ZIP itself still contains no BIF. The new evidence supersedes the historical statement that UTC−8 has only solar/temperature diagnostic support.

## Evidence and interpretation

Read-only inspection of `AMF_US-Me2_BIF_20260527.xlsx` found exactly one `UTC_OFFSET` record in sheet `AMF-BIF`, Excel range **A767:E767**:

| SITE_ID | GROUP_ID | VARIABLE_GROUP | VARIABLE | DATAVALUE |
| --- | --- | --- | --- | --- |
| US-Me2 | 12976 | GRP_UTC_OFFSET | UTC_OFFSET | -8 |

Workbook SHA256: `adcd983cca9c9c8392e0581a43414c8c4382c10ffaba431022a7656c59ba4cd4`.
Local original: `D:/Fluxes_Tower_Experiment/Ameriflux/BADM/AMF_US-Me2_BIF_20260527.xlsx`.
The complete group contains only this record. The workbook has no alternative UTC offset or date-scoped clock change. This is a site-level BADM supplement downloaded separately in 2026, **not metadata bundled with the 2024 4-6 release**, and it does not independently document datalogger configuration for every historical year.

The [official AmeriFlux processing instructions](https://ameriflux.lbl.gov/data/tips-ameriflux-flux-met-data-processing-pipeline/) specify local standard time without daylight saving, matching the registered site `UTC_OFFSET`. The [FLUXNET time convention](https://fluxnet.org/data/fluxnet2015-dataset/) likewise specifies local standard time. [FULLSET variable definitions](https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/) define `TIMESTAMP_START` and `TIMESTAMP_END` as the start and end of the averaging interval. The [site page](https://ameriflux.lbl.gov/sites/siteinfo/US-Me2) identifies the 2002–2022 FLUXNET product as version 4-6, DOI [10.17190/AMF/1854368](https://doi.org/10.17190/AMF/1854368).

Together, this supports **fixed UTC_OFFSET=−8 for the selected release**, with no DST adjustment:

```text
UTC_START = TIMESTAMP_START + 8 hours
UTC_END = TIMESTAMP_END + 8 hours
UTC_MIDPOINT = (TIMESTAMP_START + TIMESTAMP_END)/2 + 8 hours
```

For local `2002-01-01 00:00–00:30`, the UTC interval is `08:00–08:30`, midpoint `08:15`. The same +8 h applies in July. Do not use the DST-varying `America/Los_Angeles` timezone to localize these already-standard-time timestamps. A raw interval-start label must not be treated as the midpoint.

## Complete original-release scan performed locally

The user's original `AMF_US-Me2_FLUXNET_FULLSET_2002-2022_4-6.zip` was read without extracting or changing it. ZIP SHA256: `b0e213f42d01eabb8f3531b5728685d5823af164926006e7eee7fe31f009680a`.

| Original ZIP member | Rows | First start / last end in LST | Leap-day rows | SHA256 |
| --- | ---: | --- | ---: | --- |
| `AMF_US-Me2_FLUXNET_FULLSET_HH_2002-2022_4-6.csv` | 368160 | 2002-01-01 00:00 / 2023-01-01 00:00 | 240 | `5b29b04da37960a1640c19b75fc2a8ffbffd703ada89ba6c36689d86f834ae3e` |
| `AMF_US-Me2_FLUXNET_ERA5_HH_1981-2023_4-6.csv` | 753840 | 1981-01-01 00:00 / 2024-01-01 00:00 | 480 | `ad0ce6a1d934bb965d939375c1c8588ed643f3513c3ac7e31afed6ca993d3115` |

Both complete time axes exactly equal the expected Gregorian 30-minute grid. Every averaging interval is 1800 s, with zero missing, duplicate, reversed or off-grid timestamps. These checks support structural consistency, not proof of a correctly configured physical datalogger. Leap days are retained for this source audit. Later UTC/NOLEAP DATM preparation must treat leap-day removal and year-boundary coverage explicitly.

## Stage14a cluster verification completed, 2026-10-26 19:35 UTC

The historical **four** are four humidity-event records routed to `CLOCK_METADATA_HOLD`, **not four different missing metadata variables**. The operator executed the pinned Stage14a script on `login6003` in `clm_fates_env` and supplied the successful terminal output. Source SHA256/time checks, original Stage07 identity and exactly four sealed Stage11a source row/time matches all passed. Script SHA256: `5ea8ee372c733edb123e6cc029be2442a090e9bed1d252757fb831eeca4cbc89`, from commit `88b75ed01e823cdf722aca4c5a846b39bb901e9b`.

Actual new cluster report directory:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage14a_US_Me2_documented_clock_20261026T193531Z_985d2919
```

| Original CSV row | Local standard-time interval | UTC interval | UTC midpoint |
| ---: | --- | --- | --- |
| 227899 | 2014-12-31 20:30–21:00 | 2015-01-01 04:30–05:00 | 2015-01-01 04:45 |
| 227900 | 2014-12-31 21:00–21:30 | 2015-01-01 05:00–05:30 | 2015-01-01 05:15 |
| 227901 | 2014-12-31 21:30–22:00 | 2015-01-01 05:30–06:00 | 2015-01-01 05:45 |
| 227902 | 2014-12-31 22:00–22:30 | 2015-01-01 06:00–06:30 | 2015-01-01 06:15 |

The year boundary matters: these are **2014 local-source rows but 2015 UTC external-evidence times**. Keep source-row/year identity while selecting external hourly evidence by UTC timestamps, including appropriate neighboring UTC hours. Do not join a 2014-only UTC product or silently clamp outside its time axis.

[Stage14a](../scripts/stage14/14a_US_Me2_documented_clock_READONLY.py) checks the cluster CSV bytes against the above original ZIP-member hashes and against the original Stage07 manifest, checks both full time axes, verifies the Stage11a event-table receipt and maps exactly four source row/time matches to UTC start/end/midpoint. `--check` writes nothing. `--run` writes one new report under `reports/stage14a_US_Me2_documented_clock_*`; it leaves all original sources, forcing, previous sealed reports, hold markers, model cases and queues unchanged.

The actual operator-supplied summary was:

```text
ME2 CLOCK SUMMARY CLUSTER_SOURCE_AND_FOUR_CLOCK_HOLDS_VERIFIED UTC_OFFSET=-8 DST=FALSE legacy_events=4 humidity_repairs=0 DATM=FALSE jobs=0
```

The executed local source receipt and this cluster confirmation are separate evidence records. [Operator-reported cluster result](US_ME2_CLOCK_CLUSTER_OPERATOR_RESULT_20261026.json) transcribes the supplied output, not a direct download of the cluster report JSON. Its report-file SHA256 has not been supplied and is not invented. No repeat Stage14a run is required on the basis of this successful output.

The missing-clock-metadata gate is now `RESOLVED_WITH_SITE_BADM_SUPPLEMENT`. All four events have the new route `CLOCK_DOCUMENTED_HUMIDITY_SCIENCE_REVIEW_PENDING`; each printed `humidity_repair_approved=false`. Next inspect original tower TA/VPD/RH/pressure and QC, paired ERA and existing ERA5-Land coverage around UTC 2015-01-01 04:45–06:15, followed by physical consistency and adjacent-event continuity before proposing any humidity derivative. Clock resolution does not establish valid replacement VPD/QBOT or a complete forcing candidate. The 2020 fire, vegetation history, PFT/surface choices, humidity review and production forcing acceptance remain separate work. Stage14a changed no source timestamps or forcing, submitted no jobs, and reported `humidity_repairs=0 DATM=FALSE jobs=0`.
