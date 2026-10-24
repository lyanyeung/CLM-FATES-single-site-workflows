# Stage50 — One external CDS ERA5 rule for all original RH=0 / RH>100

Date: 24 October 2026.
**Status: scripts published on GitHub; live Stage50 not yet run on IRIDIS6.**
Inputs: verified Stage49 ten-site original-source ledger, exact Stage04b
source SHA256 inventory, original same-release BIF site coordinates and
UTC_OFFSET metadata, verified CDS ERA5 point-timeseries NetCDF receipts.

## Exact replacement scope from Stage48/49

| Tower | original RH=0 | original RH>100% | total |
| --- | ---: | ---: | ---: |
| US-Ha1 | 2 | 396 | 398 |
| US-Ho2 | 7 | 0 | 7 |
| US-ICh | 0 | 9 | 9 |
| US-ICt | 30 | 0 | 30 |
| **Total** | **39** | **405** | **444** |

No other records are replaced by this policy. Original positive RH<1%,
negative inferred RH, and the Stage08 cohort of 4,884 remain **separate**
scientific tasks. Those target sets overlap and must not be added.

## One ERA5 product, one numerical method

- The **only** source for these RH replacements is **independently downloaded
  CDS reanalysis-era5-single-levels-timeseries**, fields
  2m_temperature (t2m, K), 2m_dewpoint_temperature (d2m, K),
  and surface_pressure (sp, Pa). The point is selected from the nearest
  0.25-degree ERA5 grid cell to the *exact release BIF tower coordinate*.
- Do not silently mix ERA5 with ERA5-Land, Ho1's processed FLUXNET
  companion ERA5_HH, FLUXMET VPD_ERA or TA_ERA. Such companions may be
  site-regressed or numerically duplicated and are not verified CDS sources.
- The BIF local-minus-UTC offset is checked per tower and the tower
  **TIMESTAMP_START** mapped to the ERA5 hourly UTC series. These are
  local standard time source rules, not automatic daylight-saving conversion.
  The BIF UTC_OFFSET is a release provenance check; verify exact field
  interpretation before promoting any row to final forcing.
- The same Magnus water-basis saturation formula is used for all four sites:
  es(T_C) = 6.112 * exp[17.67 T_C/(T_C+243.5)] hPa.
  First form ERA5 hourly RH (%) = 100*es(Td2m_C)/es(T2m_C),
  then linearly interpolate this **hourly RH** to the native tower timestamp.
  Preserve original 60-minute US-Ha1 and 30-minute Ho2/ICh/ICt timestamps.
- For the *retained tower air temperature* (Tsite) and tower pressure (Psite),
  candidate VPD = es(Tsite)*(1-RHera/100) hPa.
  Candidate actual water vapour e = es(Tsite)*RHera/100 hPa.
  Candidate QBOT = 0.622*(100e)/(Psite - 0.378*(100e)), Psite in Pa.
  Use this identical VPD/QBOT reconstruction for every valid candidate;
  no mix of tower RH from different variables or packages.
- ERA5 interpolated RH must be finite, >0 and <=100.05%;
  Tsite and Psite must be plausible. Even then, the script marks
  original temperature QC2, missing/other QC, or |Tsite - TERA|>8C for
  **JOINT temperature/humidity review**, not unilateral humidity-only forcing.
  Cold RH>100 can reflect measurement/supersaturation or water/ice phase
  definitions. Record these flags rather than declaring true measurement error.

## Source reuse and missing coverage

The earlier Stage15/18 scientific audits already downloaded **some** verified
external CDS ERA5 years for ICh and ICt. Stage50 can checksum-verify and reuse
their actual source payload/NetCDF, but does not claim they cover every
RH=0/RH>100 year. Ha1 and Ho2 have no proven full source-year coverage
in those earlier five-site downloads.

Stage50 first reports every unique required grid/year. If a source is missing,
the explicit '--fetch' mode downloads precisely the same CDS product, variables,
hourly UTC time-series and +/-3 day year boundary buffer as Stage15/18.
A shared ICh/ICt grid/year may be verified and retrieved once, rather than
downloaded twice. All original payloads and NetCDF SHA256 receipts are
retained, with recovery from pre-existing complete payloads on interrupted
requests. No automatic retrieval occurs under '--plan' or '--build'.

## Reproducible operator commands, IRIDIS6

The Stage50 script is located at:

[scripts/stage50/50_prepare_unified_CDS_ERA5_RH_zero_gt100.py](../scripts/stage50/50_prepare_unified_CDS_ERA5_RH_zero_gt100.py)

~~~bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage50/50_prepare_unified_CDS_ERA5_RH_zero_gt100.py"
  mkdir -p "$BASE/scripts/stage50"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage50/50_prepare_unified_CDS_ERA5_RH_zero_gt100.py" -o "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --plan
)
~~~

After checking the BIF UTC and geographic evidence from the printed
'STATION' and 'GRID-YEAR' lines and ensuring the authorized CDS API account
and required dataset access exist, retrieve missing verified grid-years,
in small batches (e.g. at most 2 new downloads at a time):

~~~bash
conda activate clm_fates_env
PY="$CONDA_PREFIX/bin/python"
SCRIPT="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage50/50_prepare_unified_CDS_ERA5_RH_zero_gt100.py"
"$PY" -B "$SCRIPT" --fetch --max-new 2
"$PY" -B "$SCRIPT" --plan
~~~

Repeat '--fetch' until '--plan' prints 'missing grid-years 0'. Then:

~~~bash
"$PY" -B "$SCRIPT" --build \
  2>&1 | tee "$HOME/AmeriFlux_Batch02_Stage50_build_$(date -u +%Y%m%dT%H%M%SZ).log"
~~~

Build output: fresh isolated
'stage50_unified_external_ERA5_RH_<UTC>_<ID>/' under the experiment
reports directory, containing:

- RH_zero_gt100_444_ERA5_candidate_patch.csv — exactly 444 original
  time-targeted sparse row candidates, with source/ERA5 SHA256,
  original RH/T/VPD/pressure/QC, computed ERA5 RH and matching VPD/QBOT,
  and an explicit science review status.
- candidate_provenance.json — source inventory, BIF and NetCDF receipt
  identities and per-status counts.
- INCOMPLETE_DO_NOT_USE is left for interrupted runs.

This is an actual **candidate replacement calculation**, not a final
rewrite of original CSVs or historical Stage07/08 candidate forcing.
No model input or original data are edited. The candidate is sparse
because the 4,884 Stage08 HOLD records and 24 QC0 edits across five
numeric sites still need separate treatment; DO NOT apply these 444
rows in isolation to an otherwise unapproved model forcing.

## How to interpret outputs

- 'STAGE50 SELF-TEST PASS': algorithm's offline mini-test.
- 'STAGE50 PLAN PASS': 444 matching exact-source records and a list of
  verified or missing CDS grid-years. This does **not** mean 444 repaired.
- 'STAGE50 VERIFIED CDS': a new independent CDS retrieval was SHA256
  checked and audited. Additional years may still be missing.
- 'STAGE50 BUILD PASS': all 444 original RH events have an externally
  computed, source-linked **candidate RH**; each associated VPD/QBOT is
  present only where original T/P passes the independent numerical gate.
  Science approval remains zero, with any joint-T decisions unresolved.
