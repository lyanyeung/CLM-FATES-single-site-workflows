# Stage79 operator PASS — US-Ho1 year-2000 505 QC0 cold episodes and Stage80 original transition diagnostics

**25 October 2026, after 18:12 UK local time.** The operator ran the original Stage79 exact Git blob `6c5de3a74de5a1b587648e0fa594369cfb461a1f`, with `SELF-TEST PASS`, full source SHA `CHECK PASS`, and isolated `AUDIT PASS`.

Stage79 verified report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage79_Ho1_2000_505_QC0_source_month_hour_episode_control_triage_20261025T181238Z_2b6cbd1f`.

## Original-source year-2000 findings

All **505** Ho1 original measured T QC0 / independent CDS ERA5 T difference >8°C cases are organized into **36 native 30-minute-consecutive episodes** (Stage79 console shows only the longest 35), of which **498** have a source-QC-screened NOAA Bangor comparison, **306** distinct NOAA physical reports. Original source case months: **Jan 300 (59.4%); Feb 73; Mar 115; Nov 8; Dec 9** — 488/505 (96.6%) in Jan–Mar. Stage79 kept native `TA_F_QC=0`, source timestamps and source lineages; the 505-case selection does not independently prove bad native sensor data.

All **505/505** event timestamps have at least one same-month original T QC0 non-hard-VPD control within **±7 days, ±1 hour same local clock**. Of these 505, only the previously confirmed **498** had a matched NOAA original station report at the event time; across them the signed event-minus-nearby-control median (NOAA−Ho1) is **+13.894°C**, with IQR **+10.241 to +17.906°C**. The background controls are not randomized and may reflect very different weather, canopy exposure and source selection, so these statistics remain descriptive.

### January original T discrepancy persists across night/day source strata

The 3-hour local-clock bin source-control signed NOAA−Ho1 temperature difference shows unusually large contrast in January:

| January native local bin | Held source HH | Same-month control source HH | Held median NOAA−Ho1 (°C) | Control median NOAA−Ho1 (°C) | Held minus control (°C) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 00–03 | 37 | 101 | +18.630 | −7.147 | **+25.777** |
| 03–06 | 48 | 93 | +17.415 | −8.565 | **+25.980** |
| 06–09 | 50 | 82 | +15.895 | −7.199 | **+23.094** |
| 09–12 | 52 | 90 | +12.555 | −7.7755 | **+20.3305** |
| 12–15 | 18 | 138 | +15.555 | +1.7495 | +13.8055 |
| 15–18 | 16 | 148 | +12.680 | +1.1350 | +11.5450 |
| 18–21 | 32 | 125 | +14.000 | −3.5300 | +17.5300 |
| 21–24 | 40 | 109 | +17.855 | −4.8450 | +22.7000 |

These are comparisons of **medians** from unequal original source cohorts within month/bin, not direct paired correction factors. The contrast occurs at night and daytime and cannot be resolved simply by modest clock offset changes (as Stage78 established). No new original source observation was created and no QC0 temperature is yet approved for replacement.

### Long original measured-QC0 cases worth inspection

| Source continuous native local time | Source HH | Duration | Signed NOAA−Ho1 median |
| --- | ---: | ---: | ---: |
| 2000-03-06 04:00 to 03-07 14:30 | 70 | **35 hours** | +12.835°C |
| 2000-02-22 11:30 to 02-23 11:00 | 48 | **24 hours** | +11.680°C |
| 2000-01-01 15:30 to 01-02 13:00 | 44 | **22 hours** | +18.825°C |
| 2000-01-02 17:00 to 01-03 14:00 | 43 | **21.5 hours** | +21.270°C |
| 2000-01-11 20:00 to 01-12 14:00 | 37 | 18.5 hours | +17.920°C |
| 2000-01-07 16:00 to 01-08 09:30 | 36 | 18 hours | +14.535°C |
| 2000-01-10 18:30 to 01-11 10:30 | 33 | 16.5 hours | +21.660°C |

Interpretation: the original reported source T appears to enter discrete, often multi-hour or multi-day regimes inconsistent with Bangor airport and nominal-clock ERA5 air temperatures, but still could involve complex microclimate, sensor installation, original QC lineage, temporal alignment, site-source provenance or release processing artifacts. The observations **must not** be automatically 'corrected' using airport or ERA5 T.

## Stage80: inspect each episode's true original leading and trailing edges

[Stage80 source script](../scripts/stage80/80_Ho1_2000_original_T_QC0_episode_boundary_and_NOAA_transition_audit.py) reads and SHA-checks the whole Stage79 result and original Stage78 Git code; imports Stage78's original Stage49 primary Ho1 FLUXNET file hash verifier and original 505 source row/temperature comparison. For all **36 episodes**, it builds per-native-HH windows covering **6 hours before + episode + 6 hours after** the flagged source-QC0 run, directly reading original `TA_F`/`TA_F_QC` and `VPD_F`/`VPD_F_QC` (and `TA_ERA` only if originally present). It matches exactly the original NOAA 2000 archival file with the pinned Stage40 source-QC selector at nominal shadow UTC−5, keeping historical effective-date approvals FALSE.

The episode summary prints original 30-minute temperature changes at entry/exit, plus previous 2h / first 2h / last 2h / next 2h original source T-QC0 and NOAA−Ho1 signed medians and NOAA independent report counts. Large ±8°C changes are **diagnostic threshold flags only, not scientifically approved sensor-failure criteria**. Windows can overlap, and repeated original HH/NOAA station reports are not independent. No historical site time offset validity is claimed from nominal BIF.

Stage80 corrected Git commit `e1c7e53c777ee457ed722691fb0b1a0e43819d69`; Git blob `945ca08b393d15fd8f710619d60a001dd9a1e9ad`.

### One-paste IRIDIS6 command

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage80/80_Ho1_2000_original_T_QC0_episode_boundary_and_NOAA_transition_audit.py"
  COMMIT="e1c7e53c777ee457ed722691fb0b1a0e43819d69"
  EXPECTED="945ca08b393d15fd8f710619d60a001dd9a1e9ad"
  OLD_EXPECTED="0aac181f03c20f4039b3031f28c41211fb67eca7"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage80/80_Ho1_2000_original_T_QC0_episode_boundary_and_NOAA_transition_audit.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  test ! -L "$SCRIPT"
  if test -e "$SCRIPT"; then
    test -f "$SCRIPT" || { echo "STOP: nonregular Stage80 destination" >&2; exit 1; }
    ACTUAL_LOCAL="$(git hash-object "$SCRIPT")"
    if test "$ACTUAL_LOCAL" = "$OLD_EXPECTED"; then
      cp "$TMP" "$SCRIPT"
    else
      test "$ACTUAL_LOCAL" = "$EXPECTED" || {
        echo "STOP: unexpected Stage80 destination blob; no overwrite" >&2; exit 1;
      }
    fi
  else
    cp "$TMP" "$SCRIPT"
  fi
  test "$(git hash-object "$SCRIPT")" = "$EXPECTED"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage80_Ho1_2000_QC0_boundaries.log"
)
```

Expected operator success after actual HPC run: `STAGE80 AUDIT PASS | 36 Ho1 2000 measured QC0 episode boundaries with SHA-verified original NOAA, no forcing approval`.

Stage80 has been committed and code structure/Git blob SHA validated, **not yet tested against IRIDIS6 Stage79 source files**. All 15,199 independent CDS humidity numeric shadow candidates, 1,675 temp science HOLDs, full 16,874 original humidity source HOLDs and unrelated Stage64 9,389 candidates remain unmodified. Original FLUXNET, NOAA, ERA5, forcing NetCDF, DATM, CIME and Slurm are never changed.

## Stage80 35-versus-36 regression correction (operator failure)

The original Stage80 `--self-test` passed but `--check` failed at `old_report()` with `Stage79 original 35 episode/505 HH source census changed`. This does **not** implicate corruption in Stage79. The published Stage79 Python code uses `out.head(35)` when printing episode rows; those 35 rows contain **504** original half-hours, while its actual immutable CSV includes a **36th singleton**, closing exactly **505**. The original Stage80 error came from `EXPECTED_EPISODES=35`, a mistaken interpretation of *displayed* rows as *all* rows.

Fixed only the Stage80 script: expected **36 full episodes**, preserve original source SHA and exact 505 timestamp check, strengthen self-test with the 35 displayed durations (sum 504) + one unprinted singleton. Nothing in the Stage79 CSV, original FLUXNET, NOAA, CDS or formal forcing was changed. Run the **corrected pinned command above**: it only overwrites local Stage80 if its blob is precisely the previous `0aac181f...` or reuses the new blob, refusing any unexpected operator modification. The corrected Stage80 has not yet passed IRIDIS6 `--check`/`--audit`.
