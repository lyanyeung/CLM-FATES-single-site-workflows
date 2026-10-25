# Stage81 operator PASS — complete Ho1 year-2000 source-native T versus Bangor NOAA: bidirectional long residuals

25 October 2026, after 19:24 UK time. The operator supplied pinned Stage81 SHA-confirmed IRIDIS6 `SELF-TEST PASS`, `CHECK PASS` and `AUDIT PASS`. Original Git blob `6e584c3e446e6637e8dbdad3241a278d15c0f415`; original Stage81 source reports are unchanged.

Stage81 completed isolated report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage81_Ho1_2000_full_year_QC0_NOAA_temperature_regimes_20261025T192411Z_3f99abd7`.

## Original-source exact 2000 population and source limitations

| Stage81 full-year source evidence | Original 30min HH |
| --- | ---: |
| All original Ho1 2000 native HH (leap year) | **17,568** |
| Native measured-source `TA_F_QC=0` temperature valid | **17,294** |
| Native measured-source QC0 + screened Bangor NOAA station observation | **17,140** |
| Bangor NOAA **warmer** than original Ho1 by >8°C | **1,554** |
| Original Ho1 **warmer** than Bangor NOAA by >8°C | **2,518** |
| Matched measured-source temperatures within ±8°C of NOAA | **13,068** |
| Native original year-2000 VPD hard-physics anomaly timestamps | **1,069** |
| Earlier Ho1 QC0–independent ERA5 T difference >8°C source-HOLD records | **505** |

The 505 earlier ERA5-temperature discordance/HARD-VPD cases have **498** original NOAA source-QC matching HH from Stage77, and **465 of the 505** also meet the new >+8°C *NOAA-versus-Ho1* temperature threshold. These are different controls/threshold comparators and should never be assumed numerically identical.

Of all **1,554 NOAA-warmer-than-Ho1** matched records, **519** occur inside the original 1,069 hard-VPD cohort (Jan 318, Feb 60, Mar 124, Nov 8, Dec 9), while **1,035** are *outside* that cohort. The 2,518 opposite-sign Ho1-warmer-than-NOAA observations all occur in non-hard-VPD timestamps according to the Stage81 monthly stratification. The 4,072 two-sign differences are **scientific diagnostics** and not an inferred 4,072 faulty tower-temperature measurements.

Actual source temperature-residual continuous-run census: **122 original measured-QC0 cold relative to NOAA runs** and **167 original measured-QC0 warm relative to NOAA runs**. These are new temperature-threshold source runs, independent of the earlier 36 VPD-selected episodes. Real original measured-QC0 relative-to-airport differences can change SIGN across the same winter without an instrument automatically being wrong.

## Long actual T residual runs in the operator output

| Ho1 native local time | Source matched QC0 HH | Duration | Sign / median Bangor−Ho1 T | Overlap with original VPD-hard |
| --- | ---: | ---: | --- | ---: |
| 2000-01-10 10:30–01-12 22:30 | 121 | 60.5 h | **+16.580°C** (Ho1 colder) | 88 |
| 2000-03-06 00:00–03-08 01:00 | 99 | 49.5 h | **+12.800°C** (Ho1 colder) | 70 |
| 2000-10-26 10:30–10-27 22:30 | 73 | 36.5 h | **+11.225°C** (Ho1 colder) | 0 |
| 2000-01-17 03:30–01-20 23:00 | 184 | 92 h | **−18.314°C** (Ho1 warmer) | 0 |
| 2000-02-02 16:30–02-05 12:00 | 136 | 68 h | **−15.6725°C** (Ho1 warmer) | 0 |
| 2000-12-07 21:30–12-10 10:00 | 122 | 61 h | **−14.056°C** (Ho1 warmer) | 0 |

**Critical science caveat:** Bangor is an airport ground station about 46 km from the forest tower; wind, snow, stable nocturnal inversion, terrain/land cover, measurement height and canopy microclimate are potentially confounding. NOAA station and reanalysis can share assimilated observations; they are not automatically two statistically independent confirmations. FLUXNET `TA_F_QC=0` identifies a processing provenance, not an absolute guarantee of instrument accuracy. Original BIF nominal UTC−5 historical date applicability remains NOT APPROVED.

## Stage82: original FLUXNET temperature source lineage and native VPD physics by the signed NOAA discrepancy

[Stage82 source](../scripts/stage82/82_Ho1_2000_full_year_bidirectional_T_VPD_source_lineage_audit.py) pins **the completed Stage81 Git code and all six Stage81 output CSV SHA256 digests**, gates exact annual clock/source QC and 17,568/17,294/17,140/1,554/2,518 record counts and the 122+167 true source-residual runs, with the original 505/1,069 VPD/ERA selections retained only for provenance.

Stage82 reads the **original FLUXNET `TA_ERA` value if present** in the raw product (as Stage80 preserved under `original_TA_ERA_C`) but does NOT fabricate it if missing, and compares its exploratory ±3°C agreement separately with native measured Ho1 and original NOAA. `TA_ERA` is a processed/reanalysis product, not a second measured local instrument. It partitions the raw source `VPD_F` and native `VPD_F_QC` by the full-year cold/normal/warm source-temperature discrepancy, and recomputes saturated vapor pressure over water at original TA_F as a **diagnostic source-physics screen** (no automated VPD correction). It does not silently discard original extreme VPD magnitudes.

Source-level outputs: full 17,568-HH T/VPD/QC/NOAA provenance, monthly warm/cold/reference counts, separate original VPD QC0/1/2 frequencies, optional TA_ERA provenance, 289 long-run triage and all 30-minute native temperature-versus-NOAA state transitions. **No source-temperature repair, UTC time correction, VPD repair or formal forcing update is permitted.** The original 15,199 humidity numeric-only shadows and 1,675 temperature source-HOLD cases for Ho1/BZS, as well as the independent Stage64 9,389 rows, remain unchanged.

Stage82 Git source fixed commit `a94ed786ad3d084cde5e55c91eba663849c56d78`, Git blob `cf4cbfcf80004548f9ce48af3edd1e1e5c5d3abb`. Source code GitHub SHA and bracket/quote structure were checked, **NOT actual Python compilation/IRIDIS6 runtime**. The original NOAA/source temperature and QC confidence caveats remain in force.

## IRIDIS6 one-paste source-pinned command

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage82/82_Ho1_2000_full_year_bidirectional_T_VPD_source_lineage_audit.py"
  COMMIT="a94ed786ad3d084cde5e55c91eba663849c56d78"
  EXPECTED="cf4cbfcf80004548f9ce48af3edd1e1e5c5d3abb"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage82/82_Ho1_2000_full_year_bidirectional_T_VPD_source_lineage_audit.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  test ! -L "$SCRIPT"
  if test -e "$SCRIPT"; then
    test -f "$SCRIPT" && test "$(git hash-object "$SCRIPT")" = "$EXPECTED" || {
      echo "REFUSE: existing Stage82 script differs, no overwrite" >&2; exit 1;
    }
  else
    cp "$TMP" "$SCRIPT"
  fi
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage82_Ho1_2000_T_VPD_QC_NOAA.log"
)
```

Expected AFTER successful actual cluster run: `STAGE82 AUDIT PASS | 17568 original Ho1 2000 T/VPD/QC and source NOAA bidirectional science evidence; no forcing approval`. Do not assume source `TA_ERA` is available or infer any missing scientific measurements. All writes are a NEW isolated Stage82 report only.
