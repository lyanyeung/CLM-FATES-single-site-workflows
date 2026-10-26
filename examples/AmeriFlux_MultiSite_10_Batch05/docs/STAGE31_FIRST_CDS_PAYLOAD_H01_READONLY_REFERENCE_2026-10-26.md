# AmeriFlux Batch05 — first successful real ERA5-Land download and Stage31 H01 external meteorological comparison

## Stage30 first CDS download actually succeeded (operator report, 2026-10-26 11:46 UTC)

```text
UPDATED SOURCE VERIFIED
STAGE30 SELF-TEST PASS | actual CDS ISO date interval construction
CDSAPI IMPORT PASS
CDS Request ID 1542ef1e-d0a8-4165-9c69-cd3192725e36
CDS status: accepted -> running -> successful
STAGE30 FETCH_SUCCESS ERA5L_US_Vcm_200712 BYTES 20935
SHA256 abda0a706aef79dc0eb7a8b50db1b66ed427c8a756b81965d9bb3dba2e315646
STAGE30 SUCCESS | 27 windows; CDS site-month plans 11 DOWNLOADS 1 RESEARCH_ONLY
STAGE30_FETCH_DIR=/home/ly3n24/ameriflux_batch05_stage30/one_reference_fetch_20261026T114508Z_3061960
```

Original file:
`/home/ly3n24/ameriflux_batch05_stage30/one_reference_fetch_20261026T114508Z_3061960/ERA5L_US_Vcm_200712.cds_download`.

This is real external CDS-provided ERA5-Land gridded meteorology, **not yet inspected**, and **not an independent field measurement**. The scientific meaning of source-downscaled ERA and CDS ERA5-Land still requires separate evaluation.

**Official ERA5-Land time-series product guide** says multiple requested variables can be delivered as a ZIP containing multiple NetCDF groups; one must not assume a `.cds_download` filename indicates a single NetCDF. Source: https://confluence.ecmwf.int/pages/viewpage.action?pageId=576394628 ; data product https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries .

## Stage31: inspect actual payload and join precisely 19 source H01 held records

[Stage31 exact first-payload and H01-only researcher assessment script](../scripts/stage31/31_validate_first_ERA5Land_CDS_payload_and_Vcm_H01_readonly.py)

Pinned script commit: `0ec0e2158a4f755325bb40d59c73a95517623dc2`; Git blob SHA: `a28bde14dadcaf87abaaa2d52f2eaa785e16c89f`.

This script:
1. SHA256-checks the **actual first downloaded 20,935-byte file** against the operator log AND Stage30 download manifest (refuses any mismatched source).
2. Inspects the file magic; treats actual ZIP members as individual NetCDF groups, temporarily extracts files without modifying the original. Also accepts directly returned NetCDF. Fails on unknown archive formats/ambiguous variables or duplicates.
3. Opens the scientific data with `xarray` (and `numpy`/`pandas` with a NetCDF backend). Requires actual **air-temperature** and **dewpoint-temperature**, explicit **Kelvin** units, no missing values, distinct hourly monotonic UTC timestamps. For the requested 2007-12-14 through 2007-12-17 inclusive expects exactly 96 UTC hourly records per variable. Validates nearest-grid metadata if coordinates are in the source.
4. Reads the original Stage18 **775** native source review/context rows and Stage24 **46** original unchanged P1 manual HOLD rows; joins exactly H01 original **US-Vcm 2007-12-15 21:00 through 2007-12-16 06:00 native local standard time**, 19 half-hours. The source RH should be missing for each one.
5. Uses provisional original BIF source group `UTC_OFFSET = -7`, native-to-UTC = +7 h, NO daylight saving. **Original BIF DATE_END is missing**, so conversion remains provisional and requires independent metadata confidence.
6. Linearly interpolates actual hourly ERA5-Land **T and Td in Kelvin** to half-hour UTC timestamps, with exact hourly matches unchanged. Converts to Celsius.
7. Computes `RH=100*es_water(Td)/es_water(T)`, gridded ERA5-Land VPD, and **two distinct unapproved hypothetical VPD calculations** using the original tower TA: preserving gridded RH or preserving actual water-vapour pressure from gridded Td. Neither strategy is claimed to correct height or elevation differences.
8. Outputs original source processed ERA RH/T/VPD next to the **newly downloaded** gridded ERA5-Land T/Td/RH, original tower TA/QC, candidate-grid-vs-tower T difference, and time-matching provenance.
9. Writes **only NEW Stage31 research report files**. Preserves original Stage24 166 approved overlay, 46 manual P1 HOLD, 1,574 original P2/P3 unapproved, source QC, original FLUXMET CSV/ZIP, DATM, CIME and Slurm.

Outputs: `stage31_H01_19_HH_EXTERNAL_ERA5L_T_TD_RH_VPD_RESEARCH_ONLY.csv`, `stage31_summary.json`, `STAGE31_H01_INDEPENDENT_REFERENCE_ASSESSMENT.md`.

### IRIDIS6 one-call command

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage31"
  COMMIT="0ec0e2158a4f755325bb40d59c73a95517623dc2"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/31_validate_first_ERA5Land_CDS_payload_and_Vcm_H01_readonly.py"
  D30="$HOME/ameriflux_batch05_stage30/one_reference_fetch_20261026T114508Z_3061960"
  D18="$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929"
  D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage31/31_validate_first_ERA5Land_CDS_payload_and_Vcm_H01_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "a28bde14dadcaf87abaaa2d52f2eaa785e16c89f"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 - <<'PY'
import xarray, numpy, pandas
print("XARRAY/NUMPY/PANDAS IMPORT PASS")
PY
  OUT="$BASE/H01_external_reference_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" \
     --stage30-fetch-dir "$D30" \
     --stage18-dir "$D18" \
     --stage24-dir "$D24" \
     --out "$OUT" 2>&1 | tee "$BASE/stage31.log"
  echo "STAGE31_REPORTS=$OUT"
  cat "$OUT/STAGE31_H01_INDEPENDENT_REFERENCE_ASSESSMENT.md"
)
```

If `xarray` or NetCDF engine modules are absent, install into the user's own `clm_fates_env` environment (without altering shared Python): `python3 -m pip install xarray pandas numpy netCDF4` or use an existing suitable Conda module. If a source NetCDF has unexpected coordinate/variable names, **stop and inspect actual output, do not invent data**.

**Stage31 script committed to GitHub; IRIDIS6 run pending.** This source is physically gridded and interpolated. Even after the new data are decoded, tower-relative VPD science repair is not approved automatically.
