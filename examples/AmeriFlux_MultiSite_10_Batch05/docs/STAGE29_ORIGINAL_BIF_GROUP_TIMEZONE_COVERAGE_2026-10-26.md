# Batch05 Stage28 operator success and Stage29 original BIF group UTC-offset validation

## Stage28 real operator result — 2026-10-26

```text
SOURCE VERIFIED
STAGE28 SELF-TEST PASS
STAGE28 SUCCESS | 3 official site locations, 483 original P2P3 episodes reviewed,
top 20 pilot episodes selected
STAGE28 P1_MANUAL_HOLD 46 HH / 5 events; RH_SATURATION_PLATEAUS 2; unchanged
STAGE28 SITE US-Vcp lat 35.8641 lon -106.5965 elev_m 2501 ZIP ZIP_READ_ONLY_PASS METADATA_UTC_OFFSET_LINES True UTC_VERIFIED NO
STAGE28 SITE US-Wjs lat 34.4258 lon -105.8617 elev_m 1931 ZIP ZIP_READ_ONLY_PASS METADATA_UTC_OFFSET_LINES True UTC_VERIFIED NO
STAGE28 SITE US-Vcm lat 35.8885 lon -106.5322 elev_m 3043 ZIP ZIP_READ_ONLY_PASS METADATA_UTC_OFFSET_LINES True UTC_VERIFIED NO
STAGE28 PILOT_NATIVE_WINDOWS 27 P2P3_HALF_HOURS 264
STAGE28_REPORTS=/home/ly3n24/ameriflux_batch05_stage28/reference_preflight_20261026T043201Z_1748291
```

The Stage28 original package BIF lines **actually found** were:

| Site | Group(s) shown in BIF snippets | UTC_OFFSET | Dated metadata evidence |
|---|---|---:|---|
| US-Vcp | 4791, 4799 | -7 | GROUP_ID=4799 has `UTC_OFFSET_DATE_START=200701010000` |
| US-Wjs | 1493 | -7 | GROUP_ID=1493 has `UTC_OFFSET_DATE_START=200705041330` |
| US-Vcm | 1266, 1274 | -7 | GROUP_ID=1274 has `UTC_OFFSET_DATE_START=200701010000` |

**Do not infer that DATE_END is absent** — Stage28 sampled only selected textual matches (first 30), not full grouped metadata. Stage29 retrieves the full BIF group and checks all `UTC_OFFSET_DATE_END` rows explicitly. A BIF variable group is five columns: `SITE_ID,GROUP_ID,VARIABLE_GROUP,VARIABLE,DATAVALUE`; every variable grouped under the same GROUP_ID belongs to that instance. [Official AmeriFlux BADM Data Product](https://ameriflux.lbl.gov/data/aboutdata/badm-data-product/).

Prior Stage28 code emitted harmless `SyntaxWarning: invalid escape sequence '\\`'` when producing Markdown; that line is patched in GitHub Stage28 commit `ae92f1e28c1258b7e87cc3a2ac9de8117a2bb880` (no science/input changes; rerun not required).

US-WCr's separate RH=100% plateau is in Wisconsin, not near the three New Mexico sites. Official site location **45.8058° N, -90.0795° E, 520 m** from https://ameriflux.lbl.gov/sites/siteinfo/US-WCr. **US-WCr UTC_OFFSET must be read from its OWN BIF**, never inherited from the New Mexico `-7`.

## Stage29 original grouped timezone preflight

[Stage29 source code](../scripts/stage29/29_verify_bif_utc_offset_groups_and_convert_pilot_windows.py)

Pinned script commit `f97e0492926487e8d73fc38fd3b90f1fa065b9d4`, Git blob SHA `754901706e84c8a69655049c6d403d6b6ce6ac66`.

The script:
1. Opens each original AmeriFlux FLUXNET ZIP **read-only** (US-Vcp, US-Wjs, US-Vcm, US-WCr).
2. Parses the actual BIF five-column schema and groups `UTC_OFFSET`, `UTC_OFFSET_DATE_START`, `UTC_OFFSET_DATE_END` *by GROUP_ID*, verifies offsets are physically permissible and date ranges consistent.
3. Checks whether each of the 27 Stage28 **native event ±6h windows** falls within a same-BIF-group fully documented date range.
4. Writes **candidate** LST→UTC times using the BIF offset, without DST or changing original stage data. If BIF group dates are missing/open-ended, labels the window `REVIEW`; if groups contradict, labels `CONFLICT`, no conversion.
5. Does **not download ERA5-Land, set scientific approval, update original tower FLUXMET, alter Stage24's 166 approved RH/VPD overlay, clear the 46 manual P1 HOLD, modify DATM forcing or submit Slurm jobs**.
6. Even closed-dated groups remain `PENDING_SCIENTIST_METADATA_AND_LICENSE_REVIEW` for external ERA5-Land requests. This prevents a typo or changed original source release from silently creating downloads at wrong UTC times.

### Run on IRIDIS6

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage29"
  COMMIT="f97e0492926487e8d73fc38fd3b90f1fa065b9d4"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/29_verify_bif_utc_offset_groups_and_convert_pilot_windows.py"
  D28="$HOME/ameriflux_batch05_stage28/reference_preflight_20261026T043201Z_1748291"
  ROOT="/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage29/29_verify_bif_utc_offset_groups_and_convert_pilot_windows.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "754901706e84c8a69655049c6d403d6b6ce6ac66"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/bif_UTC_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage28-dir "$D28" \
    --site-root "$ROOT" --out "$OUT" 2>&1 | tee "$BASE/stage29.log"
  echo "STAGE29_REPORTS=$OUT"
  cat "$OUT/stage29_FOUR_SITE_BIF_METADATA_GATE.csv"
  cat "$OUT/stage29_ORIGINAL_BIF_UTC_OFFSET_ALL_GROUPS.csv"
  cat "$OUT/STAGE29_UTC_SOURCE_GROUP_AUDIT_AND_REQUEST_GATES.md"
)
```

Expected three new evidence CSVs, Markdown and JSON. User should share the command output so the relevant GROUP_ID and date-start/date-end metadata can be confirmed.

### External reference after Stage29 source verification

ECMWF/Copernicus Climate Data Store offers [ERA5-Land hourly **time-series**](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries) of 2m temperature and dewpoint, with hourly temporal coverage and CSV/NetCDF output. The time-series product uses a nearest ERA5-Land grid point for each requested location; nearest grid elevation and site elevation difference must be investigated. Do not request before site-specific timestamp mapping is verified and the user agrees to the licensed CDS account workflow. Do not treat ERA5-Land as an in-situ observed station or independent physical proof. Remember the climatological distinction between preserving source ERA RH vs preserving the source ERA actual vapor pressure across large tower/reanalysis temperature mismatch.

**Status of Stage29:** GitHub source and docs committed; IRIDIS6 script run pending.
