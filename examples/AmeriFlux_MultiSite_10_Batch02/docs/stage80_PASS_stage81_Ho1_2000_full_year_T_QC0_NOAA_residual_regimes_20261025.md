# Stage80 PASS: 36 VPD-selected Ho1 2000 QC0 cold episodes; Stage81 full-year native T investigation

Date: 25 October 2026. IRIDIS6 operator verified pinned corrected Stage80 Git blob `945ca08b393d15fd8f710619d60a001dd9a1e9ad`; actual Python syntax/self-test, source SHA check and full audit **PASS**. Note the `Stage80 CHECK PASS` console line incorrectly says `35 episodes` from a stale print string, but the **science manifest, original CSV and final audit correctly verify all 36 original episodes summing to 505 HH**. The previous Stage79 `head(35)` had shown only the first 35 of those 36.

Immutable upstream report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage80_Ho1_2000_505_QC0_episode_boundary_original_NOAA_20261025T184904Z_7a1491db`.

## Actual native original source results

All 36 source-selected temperature-discrepancy episodes include exactly 505 original FLUXNET TA_F/QC0 half-hours and ±6 hours original native `TA_F`, `TA_F_QC`, `VPD_F`, `VPD_F_QC`, original `TA_ERA` when present, plus previously SHA-proven Bangor NOAA weather source-QC results. The audit writes two new source-science CSV reports and an evidence SHA manifest; original FLUXNET, NOAA, independently retrieved CDS ERA5, DATM, NetCDF forcing, CIME and Slurm files remain untouched.

**Key discovery: none of the 36 selected VPD-defined episode boundaries shows an 8°C-or-larger discontinuity in the before/start or end/after two-hour median Bangor-minus-Ho1 residual.** Stage80 printed `STAGE80 NOAA SOURCE BOUNDARY STRONGLY SHIFTED >8C: START 0 END 0`. This particular 8°C test refers to **change in median NOAA−Ho1 signed residual across two-hour windows**, not an instrument-failure certificate and not a claim every native 30-minute sensor jump is below 8°C.

| Selected VPD+T episode (Ho1 native local clock) | HH | Start native 30-min T jump (°C) | End native 30-min T jump (°C) | NOAA−Ho1 median 2h before | First 2h inside | Last 2h inside | First 2h after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2000-03-06 04:00 – 03-07 14:30 | 70 | −0.32 | +0.162 | +9.980 | +11.140 | +15.877 | +15.4575 |
| 2000-02-22 11:30 – 02-23 11:00 | 48 | +0.25 | +0.520 | +6.995 | +8.985 | +15.130 | +14.870 |
| 2000-01-01 15:30 – 01-02 13:00 | 44 | −1.46 | +0.290 | +11.335 | +14.775 | +17.385 | +15.770 |
| 2000-01-02 17:00 – 01-03 14:00 | 43 | −0.54 | +0.170 | +14.760 | +16.635 | +20.000 | +15.245 |

**Scientific implication:** many selected original VPD hard and >8°C independent CDS temperature comparison events are simply part of a *longer preexisting air-temperature divergence* that extends before/after their VPD-based selected windows. Thus interpreting the 36 VPD-selected event intervals as physical source-T drift onset/offset is incorrect. The next source-science check must investigate **all native Ho1 measured QC0 temperatures**, not only the selected 505 hard-VPD timestamps.

## Stage81: full-year native Ho1 measured T QC0 versus preserved NOAA Bangor observations

[Stage81 read-only script](../scripts/stage81/81_Ho1_2000_full_year_native_QC0_NOAA_cold_regimes_independent_VPD.py) uses exact Git-source-pinned Stage80 code and verifies the new Stage80 operator manifest plus **both** actual Stage80 CSV output SHA256 values. It reruns the same original Stage79/78/77/74, primary Stage49 FLUXNET and NOAA source hash/calendar integrity checks, then scans the complete **17,568 original 30-minute HH across leap year 2000**. It verifies the exact original 505 selected T-QC0 events and 1,069 original VPD hard timestamps but **does not filter to those events** when constructing full-year source T residual regimes.

All native TA_F(QC0) with physically plausible original temperatures and formally source-QC-screened Bangor NOAA source matches at provisional UTC−5 are kept. Stage81 records (NOAA airport T − Ho1 original measured T), computes monthly, daily, month/3-hour and original hard-VPD vs nonhard-stratified summaries, and creates two sets of **new continuous 30min source time series**: NOAA warmer than native Ho1 by >8°C, and NOAA colder by >8°C. Source periods break automatically where the native temperature is non-QC0, original NOAA report absent/failed QC or a 30min gap. It reports source-HH counts, distinct NOAA station reports, duration, original VPD hard/nonhard overlap and the fraction of the previous 505 temperature-HOLD records within each observed source-residual regime.

This isolates **source-air-temperature residual regimes regardless of VPD selection**, rather than mistaking VPD-derived 36-block boundaries for the actual temperature-bias edges. NOTE: >8°C remains an *exploratory source residual diagnostic*, NOT proof of a sensor fault. Bangor airport ~46 km from forest tower may be systematically warmer due to landscape/snow/inversions; ERA5 and NOAA may share assimilated information; long gaps or historical actual UTC offset remain scientific uncertainties. Do not auto-correct any of the 505 native QC0 T or any other original source T from this analysis.

Stage81 exact Git source commit `ad97b1c563e07863cdffe3a2b1f833f8b6541fae` and Git blob `6e584c3e446e6637e8dbdad3241a278d15c0f415`. The Stage80 original timestamp and SHA source gates are enforced unchanged.

## One-paste IRIDIS6 — offline, source-read-only, independent isolated report

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage81/81_Ho1_2000_full_year_native_QC0_NOAA_cold_regimes_independent_VPD.py"
  COMMIT="ad97b1c563e07863cdffe3a2b1f833f8b6541fae"
  EXPECTED="6e584c3e446e6637e8dbdad3241a278d15c0f415"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage81/81_Ho1_2000_full_year_native_QC0_NOAA_cold_regimes_independent_VPD.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  test ! -L "$SCRIPT"
  if test -e "$SCRIPT"; then
    test -f "$SCRIPT" && test "$(git hash-object "$SCRIPT")" = "$EXPECTED" || {
      echo "REFUSE: existing Stage81 source differs, no overwrite" >&2; exit 1;
    }
  else
    cp "$TMP" "$SCRIPT"
  fi
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage81_Ho1_2000_full_year_T_NOAA.log"
)
```

Expected success after HPC verification:
`STAGE81 AUDIT PASS | source-pinned full-year Ho1 2000 measured QC0 air-T and NOAA residual regimes independent of VPD selection`.

Stage81 has been GitHub committed and structure-checked, but **not yet executed on IRIDIS6**. All original 16,874 hard-VPD science source HOLDs, 15,199 humidity-only numerical shadows, 1,675 T-QC and tower/ERA T-science HOLDs and unrelated Batch02 Stage64 9,389 numeric proposals remain untouched. No model or forcing changes are permitted.
