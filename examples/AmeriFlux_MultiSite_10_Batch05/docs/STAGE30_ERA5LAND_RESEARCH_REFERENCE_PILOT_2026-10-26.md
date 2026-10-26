# AmeriFlux Batch05 — Stage29 succeeded, Stage30 research-only ERA5-Land reference pilot

## Stage29 completed on IRIDIS6 (2026-10-26, operator output)

```text
STAGE29 SELF-TEST PASS | BIF GROUP_ID dates + end-month leap day + UTC from LST; original source never written
STAGE29 SUCCESS | original BIF GROUP_ID dates checked, 27 native windows compared; NO ERA5_LAND DOWNLOAD
STAGE29 SITE US-Vcp OFFSETS -7.0 GROUPS 2 CLOSED_DATED 0 ZIP_STATUS BIF_READ_PASS
STAGE29 SITE US-Wjs OFFSETS -7.0 GROUPS 1 CLOSED_DATED 0 ZIP_STATUS BIF_READ_PASS
STAGE29 SITE US-Vcm OFFSETS -7.0 GROUPS 2 CLOSED_DATED 0 ZIP_STATUS BIF_READ_PASS
STAGE29 SITE US-WCr OFFSETS -6.0 GROUPS 1 CLOSED_DATED 0 ZIP_STATUS BIF_READ_PASS
STAGE29 WINDOW_COVERAGE ONLY_UNDATED_OR_END_ONLY_GROUP_REVIEW 1
STAGE29 WINDOW_COVERAGE OPEN_ENDED_START_DATED_REVIEW 26
STAGE29_REPORTS=/home/ly3n24/ameriflux_batch05_stage29/bif_UTC_20261026T112153Z_2957771
```

### Original BIF groups, actual evidence

| Site | Source BIF GROUP_ID | UTC_OFFSET h | UTC_OFFSET_DATE_START | UTC_OFFSET_DATE_END | Science gate |
|---|---|---:|---|---|---|
| US-Vcp | 4791 | −7 | absent | absent | undated metadata |
| US-Vcp | 4799 | −7 | 2007-01-01 00:00 | absent | open-ended |
| US-Wjs | 1493 | −7 | 2007-05-04 13:30 | absent | open-ended |
| US-Vcm | 1266 | −7 | absent | absent | undated metadata |
| US-Vcm | 1274 | −7 | 2007-01-01 00:00 | absent | open-ended |
| US-WCr | 3522 | −6 | absent | absent | undated metadata |

No conflicting offset across the available site-specific BIF records, but **zero fully closed DATE_START/DATE_END metadata groups**. AmeriFlux BADM DATE variable guidance states when a DATE_START is recorded, a DATE_END is normally required, so missing DATE_END remains an explicit source metadata gap. [AmeriFlux DATE variables](https://ameriflux.lbl.gov/badm_resource/date-variables/). Local timestamps are FLUXNET local-standard time (no DST); provisional UTC candidate `UTC = local standard time − signed UTC_OFFSET` results in +7 h for the 3 New Mexico sites, +6 h for WCr. These are **candidate UTC mappings** not verified complete time metadata.

Stage29 source SHA256 is preserved in original Stage29 reports; no source files/forcing/slurm modified.

## Stage30: external meteorology to break the review-only loop

[Stage30 candidate UTC–CDS request planner and explicitly opt-in downloader](../scripts/stage30/30_build_and_optionally_fetch_ERA5Land_reference_pilot.py)

Script GitHub commit `907fd93a7f6a932586a20687224f7638baf01898`, Git blob SHA `ace3def89430b2677e97fea34008449020225453`.

CDS datasets:
- [ERA5-Land hourly time-series (ARCO, point/nearest 0.1° grid)](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries), dataset name `reanalysis-era5-land-timeseries`; 2 m temperature and 2 m dewpoint, units K, hourly UTC.
- [CDS API setup and licence instructions](https://cds.climate.copernicus.eu/how-to-api), minimum recent `cdsapi>=0.7.7`; **requires user to accept the dataset Terms of Use on the product page** and privately configure `~/.cdsapirc`.
- This time-series dataset can yield multiple NetCDFs in a bundle; inspect download file signature/contents and use valid UTC hourly axes before deriving RH/VPD. Product uses nearest 0.1° grid point; original tower altitude differences can be large; original bundled TA_ERA/VPD_ERA are not independently fetched data.
- The CDS dataset website/API may change; if a request schema is rejected, use dataset's **Show API request code** for the currently selected point and dates, without silently substituting a different scientific dataset.

The Stage30 planner reads original Stage29 27 *candidate* UTC windows and checks that each is reproduced exactly by original signed BIF offset, verifies all six BIF groups and site geolocations, then groups pilot windows into **site + UTC month** requests. Each request includes a one-day buffer beyond the event date boundaries, to avoid missing hourly points near 30-minute native timestamps. Files:
- `stage30_27_NATIVE_UTC_EVIDENCE_WINDOWS.csv`: native/UTC candidate per event, grouped BIF status.
- `stage30_CDS_ERA5L_SITE_MONTH_REQUEST_PLAN.csv`: each site-month date interval, true coordinates, dataset and JSON request.
- `stage30_CDS_REQUESTS_DRYRUN.json`: ready-to-review CDS API request specifications, zero execution on default path.
- `STAGE30_SOURCE_TIME_AND_CDS_PILOT.md`: concise operator summary.
- `stage30_summary.json`: all original report checksums, metadata uncertainty and whether any actual file was fetched.

### Stage30 PLAN — IRIDIS6 one-call command (NO external download)

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage30"
  COMMIT="907fd93a7f6a932586a20687224f7638baf01898"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/30_build_and_optionally_fetch_ERA5Land_reference_pilot.py"
  D29="$HOME/ameriflux_batch05_stage29/bif_UTC_20261026T112153Z_2957771"
  D28="$HOME/ameriflux_batch05_stage28/reference_preflight_20261026T043201Z_1748291"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage30/30_build_and_optionally_fetch_ERA5Land_reference_pilot.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "ace3def89430b2677e97fea34008449020225453"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/request_plan_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage29-dir "$D29" --stage28-dir "$D28" \
    --out "$OUT" 2>&1 | tee "$BASE/stage30_plan.log"
  echo "STAGE30_REPORTS=$OUT"
  cat "$OUT/STAGE30_SOURCE_TIME_AND_CDS_PILOT.md"
)
```

### OPTIONAL test of ONE external ERA5-Land data request — explicitly initiated by the operator

Once the user's CDS account and licence are configured, **optionally** repeat against a NEW output directory with flags, which explicitly acknowledge original BIF DATE_END is missing:

```bash
# Only on a network-permitted data-transfer node or workstation with
# cdsapi>=0.7.7 installed and your OWN ~/.cdsapirc / CDS licence accepted.
D29="$HOME/ameriflux_batch05_stage29/bif_UTC_20261026T112153Z_2957771"
D28="$HOME/ameriflux_batch05_stage28/reference_preflight_20261026T043201Z_1748291"
SCRIPT="$HOME/ameriflux_batch05_stage30/30_build_and_optionally_fetch_ERA5Land_reference_pilot.py"
OUT="$HOME/ameriflux_batch05_stage30/one_research_fetch_$(date -u +%Y%m%dT%H%M%SZ)_$$"
python3 -B "$SCRIPT" --stage29-dir "$D29" --stage28-dir "$D28" \
 --out "$OUT" --fetch --acknowledge-provisional-bif-offsets --max-fetch 1
```

**Important**: optional downloading is research-only. It has not been run, is not a new repair approval, and its outputs need a separate inspection of file format, actual grid location, UTC axis, T/dewpoint Kelvin units and site elevation before comparison. It is not valid yet to convert downloaded hourly reference RH into production DATM or assign original tower observation QC0. A single pilot file verifies API/format and time coverage; scale other 27 event windows only after inspection.

## Pending science

- Original Stage24 versioned overlay **166** approved half-hour pairs unchanged; original P1 human HOLD **46** unchanged; original P2/P3 **1,574** unapproved; 10 near-saturation plateau native records unapproved.
- Priority conflict US-Vcp original P2/P3 (339 MDS-vs-processed-ERA RH conflicts >20 percentage points); future external T/dewpoint reference compares source alternatives with explicitly chosen RH-based vs vapour-pressure-based temperature adjustment.
- No arbitrary timezone guessing or DST; continue to label BIF DATE_END as missing even if pilots align with expected climatology.
