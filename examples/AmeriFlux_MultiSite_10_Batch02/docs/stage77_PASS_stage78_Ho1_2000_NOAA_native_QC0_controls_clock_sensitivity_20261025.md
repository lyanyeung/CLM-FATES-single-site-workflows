# AmeriFlux Batch02 — Stage77 operator PASS, archived NOAA 2000 source; Stage78 native QC0 controls and time-shift sensitivity

**25 October 2026, verified from the user's IRIDIS6 log.**

Stage77 `--self-test`, `--check` and final `--audit` all PASS after the GitHub-pinned Stage40 NOAA QC parser was installed. The Stage77 original source code remains Git blob `0211de8a12aba54827fd55bdfbe9890c21c14734`; upstream Stage40 parser blob `8767dbcad2c3c6cd431b37968e867838eac01d87`.

Isolated **Stage77 successfully completed report**:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage77_Ho1_2000_505_QC0_NOAA_Bangor_external_T_context_20261025T094314Z_fa509a05`.

## Actual source result — NOT a temperature-repair approval

| Stage77 verified original evidence | Count / diagnostic |
| --- | --- |
| Original US-Ho1 2000 QC0 T values, |Ttower − independent CDS T| >8 °C | **505** |
| NOAA Bangor year-2000 source GHCNh PSV bytes | **10,119,935** |
| Source PSV rows / plausible numeric / passing Stage40 source-code and QC whitelist | **11,403 / 11,355 / 11,329** |
| Source-QC matched Ho1 original HH records within 30 minutes | **498** |
| Physically distinct NOAA source reports contributing to matched HH | **306** |
| No numeric NOAA report within 30 minutes | 4 |
| Equidistant conflicting NOAA reports rejected | 3 |
| MAE Bangor − Ho1 original QC0 | **14.322 °C** |
| MAE Bangor − nominal-clock independent CDS ERA5 T | **1.516 °C** |
| Bangor closer to CDS by more than 1 °C / closer to Ho1 by more than 1 °C / within 1 °C | **490 / 6 / 2 HH** |
| Maximum native half-hours paired to one original NOAA report | **2** |

NOAA original 2000 source raw SHA256 (not guessed):
`2d5756c1de9faa1bf4e59cddc24ab39556ae167d602d80859786309601bb3620`.

NOAA source/QC whitelist inherited from Stage40: `(source 335, quality 5, originating station 726088-14606)` and `(source 223, quality 1, ICAO-KBGR)`, empty measurement code, with ±30-minute nearest-report matching and conflicting equidistant reports rejected. This is a **legacy diagnostic whitelist**, not a general guarantee of instrument accuracy.

**Interpretation:** The source-QC-screened Bangor airport temperature is strongly closer to the separately downloaded ERA5 T2M than to the apparently measured Ho1 2000 original T values in these selected anomalous records. This is strong evidence warranting a science/instrument/time investigation, **not** proof Ho1 original measured QC0 is wrong. Both spatial representativeness (airport ~46km from forest, different canopy/height/exposure), serially reused NOAA reports, source clock convention and selection on Ho1-vs-ERA disagreement constrain inference. NOAA meteorological station observations and a reanalysis may also share assimilated information, so don't claim statistically independent corroboration without checking reanalysis assimilation lineage.

## Stage78 scope

[Stage78 original Ho1 2000 QC0 and NOAA time-shift/source controls](../scripts/stage78/78_Ho1_2000_NOAA_QC0_control_and_clock_sensitivity.py) does **not** request NOAA again. It verifies SHA256 of the **archived original 2000 NOAA PSV and original Stage77 505-event report**, 26/26 original Stage74 independent CDS/HOLD source census and the original byte-SHA-verified Ho1 FULLSET_HH source from Stage49 primary inventory.

Stage78 constructs **source-observed Ho1 TA_F_QC0 control half-hours** from the original year-2000 product that are NOT among any of the **1,069 original Ho1 2000 hard-VPD event timestamps**; controls are restricted to the calendar months containing the 505 original measured temperature-disagreement events. This is not a scientifically guaranteed matched-control case design: time of day and microclimate remain sources of confounding and must be assessed from stratified evidence.

It compares the unchanged 505 native Ho1 events and same-month QC0 controls against the byte-pinned NOAA source using nominal local-minus-UTC −5 and nearby sensitivity offsets −7, −6, −4 and −3 hours; the time-offset sensitivity of the same 505 event timestamps is reported on **strict identical supported timestamps** across all offsets. Off-nominal NOAA matches are NOT compared with the fixed nominal-UTC CDS ERA5 series. Report both per-native-halfhour and **equal-per-distinct-NOAA-report** MAE, source reuse and per-month summary.

No Stage78 result is a historical official BADM/UTC offset certification, automatic temperature replacement, forcing approval or statistically independent sensor truth. The full 16,874 Ho1+BZS original hard source time HOLDS remain; Stage74 15,199 numeric-only humidity shadows and other Batch02 Stage64 9,389 candidates remain immutable. Stage77 and existing NOAA/CDS/FLUXNET source files are never rewritten.

Stage78 commit: `bba8ac7b358550bcc34f40001266566f9e2f0c1f`; exact source blob: `002b6fb491b1d9dd6e570feed31a3c041f0aae2a`.

## IRIDIS6 exact source-pinned offline next step

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage78/78_Ho1_2000_NOAA_QC0_control_and_clock_sensitivity.py"
  COMMIT="bba8ac7b358550bcc34f40001266566f9e2f0c1f"
  EXPECTED="002b6fb491b1d9dd6e570feed31a3c041f0aae2a"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage78/78_Ho1_2000_NOAA_QC0_control_and_clock_sensitivity.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  test ! -L "$SCRIPT"
  if test -e "$SCRIPT"; then
    test -f "$SCRIPT" && test "$(git hash-object "$SCRIPT")" = "$EXPECTED" || {
      echo "REFUSE: existing Stage78 script has different SHA" >&2; exit 1;
    }
  else
    cp "$TMP" "$SCRIPT"
  fi
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage78_Ho1_2000_NOAA.log"
)
```

Expected completion: `STAGE78 AUDIT PASS | Ho1 2000 505 original measured QC0 source-airport controls and clock sensitivity audited`.

Stage78 is committed and source structure checked, but **has not been run on IRIDIS6**; first execution may reveal source-schema issues, in which case preserve upstream original and fix only Stage78. The `--check` mode accesses only source files and manifests, no Internet; `--audit` does not download NOAA or change original files. Data quality, local representativeness and original time/source scientific HOLDs remain unresolved.

Stage78 was hardened to convert the pandas nullable string timestamp mask to an ordinary NumPy boolean array before retrieving physical primary-source CSV row numbers; its pinned self-test checks this. No Stage77 or input-file content changed.
