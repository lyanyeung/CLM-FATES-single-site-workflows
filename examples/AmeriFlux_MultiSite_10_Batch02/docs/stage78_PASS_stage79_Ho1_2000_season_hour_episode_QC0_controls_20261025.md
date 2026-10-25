# Stage78 PASS — original measured Ho1 year-2000 anomalous temperature: clock shifts do not resolve cold gap

25 October 2026, source: actual IRIDIS6 Stage78 stdout provided by the operator. SHA-pinned Stage78 blob `002b6fb491b1d9dd6e570feed31a3c041f0aae2a` passed Python self-test, source/provenance check and complete isolated `AUDIT PASS`. **No NOAA network call** was necessary; original Stage77 NOAA year-2000 raw source SHA `2d5756c1de9faa1bf4e59cddc24ab39556ae167d602d80859786309601bb3620` was reused unchanged.

Source-report path:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage78_Ho1_2000_measured_QC0_NOAA_controls_clock_sensitivity_20261025T180347Z_0a9449e9`.

## Stage78 exact source populations

- **505** native US-Ho1 year-2000 TA_F_QC0 measured-source temperatures had >8°C disagreement with separately downloaded, SHA-verified independent CDS ERA5 t2m. These were selected by original temperature/VPD science criteria, so comparisons are not randomly selected source observations.
- **6,006** same-year, same-calendar-month original TA_F_QC0 half-hours, excluding **all 1,069 original year-2000 hard-VPD event timestamps**, formed a **descriptive non-hard-VPD control** (not a guaranteed local temperature calibration control).
- Year 2000 original source includes **17,568** native HH (366 days × 48). Months containing the 505 original selected holds are **January, February, March, November and December**.
- At nominal local-minus-UTC −5: 505 events: **498 NOAA source-QC matches**, **306 distinct station source reports**, source-report-equal MAE **14.346°C**, median (NOAA–original Ho1) **+13.655°C**. Controls: 6,006 source-QC0 native HH, **5,945 NOAA paired HH**, **3,605 distinct station source reports**, report-equal MAE **6.698°C**, median (NOAA–Ho1) **−1.715°C**. Airport proximity/atmospheric serial correlation/NOAA reanalysis-assimilation lineage means these are not independent randomized validations.

## Tested clock shift, same 483 original Ho1 events across all five offsets

| Trial local-minus-UTC offset | Common original Ho1 native HH | Distinct NOAA source reports | Unique-report-equal mean | Median NOAA − Ho1 |
| --- | ---: | ---: | ---: | ---: |
| UTC−7 | 483 | 292 | 14.703°C | +14.04°C |
| UTC−6 | 483 | 293 | 14.532°C | +13.90°C |
| **UTC−5 nominal** | **483** | **293** | **14.336°C** | **+13.64°C** |
| UTC−4 | 483 | 295 | 14.077°C | +13.41°C |
| UTC−3 | 483 | 296 | 13.855°C | +13.28°C |

Shifting UTC−5 to UTC−3 reduces common-support source-report MAE by just **0.481°C** while still leaving **13.855°C MAE** and **+13.28°C median signed NOAA–Ho1**. Thus ±2h offsets are insufficient as a sole explanation. UTC−3's slight MAE advantage is **NOT** official site historical clock evidence. The original Stage77 nominal UTC−5 atmospheric era pairing was held fixed and not inappropriately compared at off-nominal trial clocks.

Original Stage78 control report-equal MAE by trial offset: UTC−7 6.749°C, −6 6.708°C, **−5 6.698°C**, −4 6.730°C, −3 6.795°C. The controls themselves have substantial spatial/time-variability error. Stage78 does not establish all 6,006 controls are sensor-correct or that every 505 selected event is sensor-wrong. Original native tower T, seasonal sampling, canopy site environment and Bangor airport distance (~46 km) remain scientific uncertainties.

## Stage79 next: source-only stratification, matched same-hour controls, run-level science review

[Stage79 script](../scripts/stage79/79_Ho1_2000_NOAA_season_hour_episode_matched_control_triage.py) reads exclusively the Stage78 immutable outputs (five full clock offsets with 505 original measured holds and 6,006 QC0 same-month non-hard controls each), verifies original report/output SHA256 and exact source cohorts, then analyzes:

1. **Month × local three-hour bin**: source-QC0 original observations, matched half-hours, number of unique NOAA original station reports, mean absolute error computed with distinct station report equally weighted, and signed NOAA−Ho1 T medians.
2. **Exploratory local matched control**: for each of the 505 Ho1 native held events, find same-year QC0 non-hard-VPD controls within **±7 calendar days and ±1 hour on local clock**, separately reporting available controls, distinct NOAA reports, and event-minus-control airport-versus-forest temperature bias. Days/month/clock similarity does not prove calibration or instrument accuracy.
3. **Contiguous 30-minute source-HOLD episodes**: first/last original tower timestamp, episode length and source-report counts, signed and absolute differences. Long runs and their start/end can guide a targeted instrument metadata/processing review.

**Stage79 is diagnostic only:** no raw NOAA/CDS/FLUXNET download, no reanalysis recomputation, no time offset approval, no station corrections, no DATM/NetCDF or Slurm changes. Stage74 15,199 numeric humidity shadows, 1,675 original tower T HOLDs and Stage64 prior 9,389 source candidates remain scientifically on HOLD.

Stage79 source commit `1d921fb2bd0b59948ec0c8995eb3bd07cc6e40ec`, Git blob `6c5de3a74de5a1b587648e0fa594369cfb461a1f`.

## IRIDIS6 pinned Stage79 execution

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage79/79_Ho1_2000_NOAA_season_hour_episode_matched_control_triage.py"
  COMMIT="1d921fb2bd0b59948ec0c8995eb3bd07cc6e40ec"
  EXPECTED="6c5de3a74de5a1b587648e0fa594369cfb461a1f"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage79/79_Ho1_2000_NOAA_season_hour_episode_matched_control_triage.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  test ! -L "$SCRIPT"
  if test -e "$SCRIPT"; then
    test -f "$SCRIPT" && test "$(git hash-object "$SCRIPT")" = "$EXPECTED" || {
      echo "STOP: Stage79 already exists with differing content" >&2; exit 1;
    }
  else
    cp "$TMP" "$SCRIPT"
  fi
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage79_Ho1_2000_T_QC0.log"
)
```

Expected operator confirmation (not yet run):
`STAGE79 AUDIT PASS | original Ho1 2000 505 QC0 source month/diurnal/episode/nearby-control evidence; no model approval`.

Script is GitHub committed, source syntax structure and Git SHA checked, **not yet executed on IRIDIS6**. If an implementation error arises, retain all original evidence and adjust only the Stage79 code/pinned new commit; do not bypass original source SHA or release scientific HOLDs.
