# US-Me2 documented clock, 2026-10-26

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

## Four original event holds and next action

The historical **four** are four humidity-event records routed to `CLOCK_METADATA_HOLD`, **not four different missing metadata variables**. Their exact source row/time identities must be loaded from the sealed Stage11a report on IRIDIS6; they are not available in this local repository.

[Stage14a](../scripts/stage14/14a_US_Me2_documented_clock_READONLY.py) checks the cluster CSV bytes against the above original ZIP-member hashes and against the original Stage07 manifest, checks both full time axes, verifies the Stage11a event-table receipt and maps exactly four source row/time matches to UTC start/end/midpoint. `--check` writes nothing. `--run` writes one new report under `reports/stage14a_US_Me2_documented_clock_*`; it leaves all original sources, forcing, previous sealed reports, hold markers, model cases and queues unchanged.

Successful cluster output should end with:

```text
ME2 CLOCK SUMMARY CLUSTER_SOURCE_AND_FOUR_CLOCK_HOLDS_VERIFIED UTC_OFFSET=-8 DST=FALSE legacy_events=4 humidity_repairs=0 DATM=FALSE jobs=0
```

This cluster result has **not yet been observed**. The local source scan and clock logic have been executed. The remaining operator step is to run Stage14a on the already extracted cluster sources and retain the four-event receipt. If more than one Stage11a directory exists, select the exact historical report explicitly with `--stage11a /absolute/path`, rather than choosing by modification time.

After that check, the missing-clock-metadata gate can move to `RESOLVED_WITH_SITE_BADM_SUPPLEMENT`, and the four events can proceed to humidity-source/physics/continuity review using the documented UTC midpoints. This does not establish valid replacement VPD/QBOT or a complete forcing candidate. The 2020 fire, vegetation history, PFT/surface choices, humidity review and production forcing acceptance remain separate work.
