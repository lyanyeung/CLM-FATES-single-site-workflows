# Stage71 operator PASS → Stage72 isolated recovery of ten independent CDS ERA5 grid-years

Date: 25 October 2026. The user's IRIDIS6 Stage71 output verified source Git blob `b1ce47dedf3da4c931cac3b8a6d4822090870a81` and showed SELF-TEST, CHECK and final AUDIT PASS.

Stage71 isolated report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage71_Ho1_BZS_independent_CDS_verified_reuse_shadow_20261025T083319Z_8aef8c86`.

## Source-verified status

All 16,874 original source-hard events are separately accounted for:

| Stage71 status | Events | Next action |
| --- | ---: | --- |
| independent CDS verified, original T/PA numerical candidates, historical BIF time still HOLD | **7,695** | preserve, don't modify forcing |
| CDS independent verified receipt/grid-year missing or fails proof | **8,115** | recover ten grid-years in isolated Stage72 cache |
| source original TA_F quality not QC0 | **987** | defer source-neighbor T quality science check |
| original TA_F differs >8°C from independent ERA5 2m T | **77** | defer original temperature and elevation/context audit |
| **original source anomalous population** | **16,874** | entire site/time provenance still under science HOLD |

Existing original verified independent ERA5 receipt grid-years **16 of 26**, missing **10 of 26**, counted as exactly **8,115** hard source events.

### Exact missing grid-year cohorts (from operator Stage71)

| Site | Year | Original hard events | Stage71 existing local-source errors |
| --- | --- | ---: | ---: |
| US-Ho1 | 2015 | 2,268 | 1 |
| US-Ho1 | 2013 | 1,474 | 1 |
| US-Ho1 | 2011 | 1,366 | 1 |
| US-Ho1 | 2000 | 1,069 | 0 |
| US-Ho1 | 2008 | 1,036 | 0 |
| US-Ho1 | 2016 | 762 | 2 |
| US-BZS | 2012 | 79 | 0 |
| US-Ho1 | 2021 | 46 | 1 |
| US-Ho1 | 2023 | 8 | 1 |
| US-BZS | 2011 | 7 | 0 |

**Do not call all ten entirely absent:** five/six year cohorts have old candidate receipts but an error; this is often a failed SHA or metadata/calendar check, and the exact reason should come from a new read-only Stage72 `--plan`. Never overwrite the existing receipt/source payload or NetCDF to 'repair' it.

## Stage72

[Stage72 source](../scripts/stage72/72_rescue_missing_10_Ho1_BZS_independent_CDS_gridyears.py) SHA-verifies the Stage71 report outputs, the old Stage71 computation script and the Stage50 independent CDS `t2m/d2m/sp` reader. It classifies the ten missing grid-year receipts; `--plan` is entirely read-only.

Stage72 `--fetch --max-new N` requests at most N **independent CDS ERA5** grid-years, highest-impact cohorts first (US-Ho1 2015, then 2013). All new files go under a new `~/AmeriFlux_Batch02_Stage72_independent_CDS_ERA5_rescue/ERA5_YYYY_lat..._lon.../` cache. A nonblocking exclusive `flock` prevents concurrent writers. Original Stage15/18/50/62 receipts, payloads and NetCDF are never deleted, moved or overwritten, including invalid old receipts. Successfully verified new `original_CDS_payload`, `era5_dewpoint_hourly_UTC.nc` and `verified_receipt.json` are created there with SHA256 and exact buffered UTC-hourly calendar, units, range and quarter-degree coordinate validation. The new receipt is emitted only after full independent-source checks. If CDS credentials are unavailable or an interrupted payload fails validation, Stage72 stops without touching the original sources.

Stage72 `--audit` reruns the source-pinned Stage71 full 16,874-event calculation with only the new immutable Stage72 cache **prepended** to earlier receipt roots. It writes a new isolated full source-event shadow (original tower T/PA, water RH/VPD/QBOT), year/coverage manifest, and preserves original time-approval HOLD and all 9,389 Stage64 earlier numeric candidates. No official historical effective-date proof is silently inferred from uploaded 2026 BIF, and no DATM/forcing changes are made.

New script pinned commit: `d22c7cfdbb84cb4d0c6068590868d4a05820f642`.
New script Git blob: `3326c317fcf5fada71f15370828245355852948f`.

## One-paste Stage72 IRIDIS6, safe first two CDS recovery requests

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage72/72_rescue_missing_10_Ho1_BZS_independent_CDS_gridyears.py"
  COMMIT="d22c7cfdbb84cb4d0c6068590868d4a05820f642"
  EXPECTED="3326c317fcf5fada71f15370828245355852948f"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage72/72_rescue_missing_10_Ho1_BZS_independent_CDS_gridyears.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --plan
  "$PY" -B "$SCRIPT" --fetch --max-new 2 \
    2>&1 | tee "$HOME/Batch02_Stage72_fetch2.log"
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage72_audit.log"
)
```

Successful fetch prints `STAGE72 VERIFIED NEW INDEPENDENT CDS...` and `STAGE72 FETCH PASS`. A successful refreshed isolated science census prints `STAGE72 AUDIT PASS | refreshed 16874 original Ho1/BZS independent CDS coverage SHADOW; no forcing approval`.

To fill the remaining independent-source gaps, repeat `--fetch --max-new 2` or `--fetch --max-new 10` (each run verifies and skips previously completed Stage72 grid-years), then `--audit`. Any CDS service failure is an upstream source/retrieval issue, not science approval.

Stage72 script was committed and checked structurally. It has NOT been successfully run on IRIDIS6 yet. Full Python syntax is checked by the user-side `py_compile` before any fetch. No source/model writes were requested in this chat.
