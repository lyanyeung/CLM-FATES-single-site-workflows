# AmeriFlux Batch02 — Stage61 PASSED; progress 5,133 non-Ho1 hard-humidity anomalies

24 October 2026. Stage61 figures are transcribed from the user's verified
IRIDIS6 terminal output. The original report CSV is still on IRIDIS6.

## Stage61 exact overlap result

Stage61 fixed Git blob `9d67aafa960c4c5e6e41d9c67f7f2eaf60f25d1d`
passed self-test, source checks and full AUDIT.
Report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage61_stage49_vs_stage60_full_hard_coverage_20261024T114810Z_fc209bf8`.

The original Stage49 source review had 26,432 unique flagged events,
including 26,332 original hard-physics records. Of those, 4,411
coincide exactly with source-verified Stage60 candidate patches
(**zero** extra patch timestamps outside the Stage49 review).
**21,921 original hard records lack Stage60 candidates**; **16,788**
belong to US-Ho1 and **5,133** belong to nine other sites.

| Site | Hard source records not yet Stage60-covered |
| --- | ---: |
| US-BZS | 86 |
| US-CMW | 42 |
| US-EML | 2,984 |
| US-GLE | 830 |
| US-Ha1 | 23 |
| US-Ho1 | 16,788 |
| US-Ho2 | 717 |
| US-Ho3 | 39 |
| US-ICh | 48 |
| US-ICt | 364 |
| **Total** | **21,921** |

All 917 US-Ho1 Stage58 provisional-UTC target rows are present in the
16,788 original Ho1 hard records. Do **not** mistakenly double count
them or assert only 917 Ho1 records need resolution.

Stage61 first 30 uncovered BZS records span cold weather and warm
spring; the original VPD exceeds saturation vapour pressure at
original EC tower air temperature, so implied water RH is negative.
This warrants a paired water-RH/VPD/QBOT replacement proposal based
on independent, time-aligned CDS ERA5; assigning RH=0 is not
physically justified. Raw source T/VPD/QC, independent metadata and
native half-hourly/hourly coordinates must remain traceable.

## Next Stage62 — avoid a separate approval for every low-quality RH

[Stage62 same-CDS ERA5 verifier/controlled fetch and candidate
constructor](../scripts/stage62/62_reuse_or_fetch_CDS_ERA5_for_5133_nonHo1_hard_humidity.py)
uses the existing Stage61 21,921-row exact residual file and pinned
Stage50 same-CDS methods (Git blob
`757452798582dc0aaf6d2c78f23999e653247469`).

- It verifies Stage61 source manifest and Stage49+Stage60
  SHA256, original primary files via Stage49 inventory, and exact
  the nine-site 5,133/Ho1 16,788 scope.
- For non-Ho1 only, it checks one original-release BIF file per
  site for `LOCATION_LAT, LOCATION_LONG, UTC_OFFSET`.
  Sites without matching BIF remain in an explicit provenance HOLD.
- Builds an exact site-year / CDS grid-year retrieval plan.
  Reuses checksum-validated CDS ERA5 independently retrieved
  t2m/d2m/sp NetCDF receipts from Stage15, Stage18 and Stage50
  or Stage62 verified cache. Missing grid-years are stated
  precisely. No use of FLUXNET ERA companions.
- In `--fetch`, downloads at most the explicitly
  requested number of new CDS grid-years, to an **isolated**
  Stage62 cache, with SHA256 receipt and original payload and
  full-year UTC calendar/time-series checks. No model source edits.
- In `--stage`, generates a separate 5,133-row
  per-event status ledger. For verified independent ERA5 rows,
  it retains **original EC TA_F and PA_F**, and selects the
  same-CSD ERA5 water RH + recalculated water VPD and QBOT when
  source EC T/PA are physical and abs(Tower T − ERA5 T2m) ≤8°C.
  QC1/QC2 does not alone force replacement of a plausible EC
  temperature. If original T is >8°C different from ERA5,
  **do not replace tower T automatically**; send those records
  to a separate cold-weather/neighbor-context check as before.
- 16,788 Ho1 source hard events are explicitly **not** processed
  with a guessed time offset. Even though the public site page
  confirms Howland main tower 1996–2023 FLUXNET v3-6, the
  same-release official BIF UTC_OFFSET still needs verification.
- The original 102 positive raw RH<1% items are a separate
  source review population, not automatically invalid and not
  included in the 5,133 hard-physics scope.

### Pinned IRIDIS6 command

Stage62 GitHub commit: `70aadc8831a0abd7a8cdfc6f03722fbe5a2ee216`.
Stage62 Git blob: **TO_BE_FILLED**.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  S50="$BASE/scripts/stage50/50_prepare_unified_CDS_ERA5_RH_zero_gt100.py"
  S62="$BASE/scripts/stage62/62_reuse_or_fetch_CDS_ERA5_for_5133_nonHo1_hard_humidity.py"
  COMMIT62="70aadc8831a0abd7a8cdfc6f03722fbe5a2ee216"
  EXPECTED62="TO_BE_FILLED"
  COMMIT50="RETRIEVE_PINNED_STAGE50_COMMIT"
  mkdir -p "$(dirname "$S50")" "$(dirname "$S62")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT62/$REL/scripts/stage62/62_reuse_or_fetch_CDS_ERA5_for_5133_nonHo1_hard_humidity.py" \
    -o "$TMP"
  test "$(git hash-object "$TMP")" = "$EXPECTED62"
  cp "$TMP" "$S62"
  test "$(git hash-object "$S50")" = "757452798582dc0aaf6d2c78f23999e653247469"
  "$PY" -m py_compile "$S62"
  "$PY" -B "$S62" --self-test
  "$PY" -B "$S62" --check
  "$PY" -B "$S62" --stage \
    2>&1 | tee "$HOME/Batch02_Stage62_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

When the printed verified independent grid-year census shows
missing CDS products, retrieve the needed subset with
`python -B SCRIPT --fetch --max-new 8`
and re-run `--stage`. Unverified station BIF
and US-Ho1 source metadata are hard provenance gates. Continue
the other sites independently.

The script is committed but **has not yet been executed on IRIDIS6**.
No model forcing changes are reported.
