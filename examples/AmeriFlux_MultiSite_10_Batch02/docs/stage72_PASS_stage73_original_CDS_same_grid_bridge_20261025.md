# Batch02 Stage72 PASS — correct cross-site source receipt false HOLD, no redundant downloads

Operator Stage72 IRIDIS6 evidence (25 October 2026): original pinned Git blob `3326c317fcf5fada71f15370828245355852948f` verified; `--self-test`, `--plan`, two independent CDS fetches, and refreshed `--audit` all PASS.

Original successful Stage72 report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage72_16874_original_independent_CDS_recovery_shadow_20261025T084352Z_01da7b3d`.

## Source and numeric status

- Two new independent CDS verified grid-years: US-Ho1 2015 (NetCDF SHA256 `a2a69b2fc309e8d4f7f8ab0e501ea0dd17123f89dd148fbd9d475559ad9a0d0c`) and 2013 (NetCDF SHA256 `c2905055a1b69bed4a7f5c41aed6b940cbb799620c17b6a85bfa07960a4ca2e9`). These were saved in **new isolated Stage72 cache**, prior original CDS files/receipts remain unchanged.
- Complete independent year coverage **18/26**, increased from 16/26.
- Original hard events 16,874: **11,432** standalone independent ERA5 RH/VPD/QBOT numeric shadow candidates, **4,373** lacking a verified independent source; **987** native TA QC nonzero, **82** native TA vs independent ERA5 T differing over 8 °C. These counts close exactly and **all records remain historical source-time HOLD**. Existing unrelated Stage64 9,389 numeric candidates remain unchanged.
- New numerically viable rows from two downloaded years **3,737** = 2,267 (2015) + 1,470 (2013).

## Critical discovery: mismatch is the receipt's site list, NOT evidence of corrupt CDS bytes

Stage72 `--plan` classified SIX original receipts as rejected exclusively for `ValueError Stage50 receipt site membership mismatch` (US-Ho1 2015, 2013, 2011, 2016, 2021, 2023). This old **Stage50 schema intentionally binds receipts to the original requesting site**, even when another tower shares the same ERA5 0.25° grid. That reason alone **does not establish a faulty or corrupted CDS payload**. In hindsight the 2015/2013 fresh independent downloads were scientifically conservative but may have been redundant; there is no source corruption evidence in this log.

At present four unresolved site/year cohorts show membership-only rejection, involving **2,182 original hard events**: Ho1 2011 (1,366), Ho1 2016 (762), Ho1 2021 (46), Ho1 2023 (8). The other four cohorts (Ho1 2000/2008 and BZS 2011/2012) have **2,191 original hard events** and no receipts in the sources searched by Stage71, so they are the genuine download priorities if no other source cache exists.

## Stage73 source-preserving same-grid bridge

[Stage73 script](../scripts/stage73/73_same_grid_cross_site_original_CDS_receipts.py) ensures cross-site reuse is evidence-based. It dynamically checks the exact older 4 grid-year receipt paths and historical original listed source sites. It reruns Stage50's original source receipt validator **with the original recorded member sites**, which checks the original independent CDS payload SHA256, NetCDF SHA256, dataset, 0.25° grid, full buffered hourly UTC calendar, coordinates, physics and units. In addition, it requires the original CDS request lat/lon to map exactly to Ho1's quarter-degree grid, and requires matching netcdf/payload hashes if two original validated receipts exist (for example 2016). Inconsistent valid sources remain HOLD; no automatic source choice.

Only if all provenance checks pass does Stage73 create a **new** source-specific scoped receipt, under `~/AmeriFlux_Batch02_Stage73_same_grid_original_CDS_bridge/ERA5_YEAR_lat.../verified_receipt.json`, including the original receipt file SHA and original source sites. The new receipt points to **unchanged original** CDS payload+NetCDF files; old receipts and CDS sources are not moved, edited, replaced or deleted. `--audit` reuses the exact Stage71 original source ledger and methods with the bridge and prior Stage72 cache, recalculates 16,874 original event shadows, and explicitly keeps official BADM historical clock and DATM approvals false. Do not claim a released time offset just because current official site BADM reports −5 or −9.

Stage73 pinned source commit `a1ebfe61332d22d848081bc9f3c8b7728777d18d`.
Stage73 verified Git blob `66af1ae518ff56ff55165c58f26afb5863b6688b`.

## One-paste IRIDIS6

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage73/73_same_grid_cross_site_original_CDS_receipts.py"
  COMMIT="a1ebfe61332d22d848081bc9f3c8b7728777d18d"
  EXPECTED="66af1ae518ff56ff55165c58f26afb5863b6688b"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage73/73_same_grid_cross_site_original_CDS_receipts.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --plan
  "$PY" -B "$SCRIPT" --bridge
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage73.log"
)
```

Expected `STAGE73 AUDIT PASS | full 16874 source-cohort same-grid CDS shadow, original HOLD retained`.

**Do not run Stage72 --fetch again for the membership-only years** before checking Stage73. Stage72 did not distinguish other-site same-grid receipt lineage. For the genuinely missing site grid-years after Stage73, recover with a new specifically targeted create-only download to avoid overwriting or needlessly repeating these old shared data files.

Stage73 code committed and locally lexically inspected against the original Git blob; not yet executed on IRIDIS6. Any old receipt found with valid source but incompatible lat/lon/grid or different source sha remains HOLD. Neither Stage64's existing 9,389 source-verified water candidate rows nor original 16,874 source-hard HOLD population has been altered.
