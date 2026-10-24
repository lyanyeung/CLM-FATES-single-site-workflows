# AmeriFlux Batch02 — Stage59 operator PASS; automatic Stage60 water-humidity staging policy

Date: 2026-10-24. Stage59 results below from operator-provided
IRIDIS6 terminal output. This GitHub page does not represent an
independent upload of the operator's Stage59 CSVs.

## Actual Stage59 PASS and zero need for manual phase-by-phase edits

Pinned Git blob verified on IRIDIS6:
`c9e9efcb374100eed9bfbb7f750df3527de61e68`.
Python syntax, self-test, source check, isolated full audit PASS.
Report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage59_water_ice_review_3967_20261024T110624Z_2dc93fb4`.

Stage59's 3,967 original-EC-temperature-accepted Stage58
meteorological records (same independent CDS ERA5 humidity, original
site air temperature and pressure) break down as:

| Water/ice review route | Count |
| --- | ---: |
| Subzero and no numerical supersaturation over ice | 2257 |
| RH over ice 100–105% | 687 |
| RH over ice >105% | 1013 |
| Tower air temperature >=0 C | 10 |
| **Total** | **3967** |

Counts of over-ice RH>100: EML **636**, GLE **175**,
ICh **48**, ICt **841**. These 1,700 ice supersaturation
diagnostics must not be mistaken for 1,700 automatically invalid
water-reference RH records. Examples reach RH_ice 131.61%;
negative **ice-reference** VPD of ~−0.08 hPa at cold temperatures
is not the same as negative **water-reference** VPD.
Water/ice saturation reference must be stated explicitly.

All Stage59 3,967 records reproduce the same independently
downloaded ERA5 water-RH, original EC TA_F/PA_F water-VPD and
specific humidity (QBOT) to numerical tolerance.

Stage59 searched the original US-Ho1 1996–2023 release (ver. 3-6)
directory; **no adjacent *_BIF_*.csv** was present.
**917 US-Ho1** records remain original-release UTC offset HOLD.
Official station overview, not proof of original tower-local UTC offset:
https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1

## User-delegated automatic physical-science policy

1. **Preserve original EC tower air temperature and pressure**
   for the already source-approved Stage58 **3,967** records.
   Never replace EC TA_F with coarser ERA5 T2m merely because
   historical native TA_QC is QC1/QC2.
2. **Select independent CDS ERA5 water-reference RH** for the
   3,967 humidity anomalies, and calculate VPD_water and QBOT
   from this same humidity with original tower T and PA.
   Keep over-ice RH and ice-reference VPD diagnostic only:
   do **not** use negative ice VPD as a CLM-FATES forcing input.
   No forced clipping of water RH or QBOT for cases that are
   supersaturated over ice.
3. **Include exactly 444** previously source-verified Stage53
   original RH=0/>100 substitutions using the same independent
   CDS ERA5 product, original EC T/PA and paired water-VPD/QBOT.
   Stage54 verified intersection of Stage53 and Stage11 identities
   to be zero. Thus **3,967 + 444 = 4,411** exact site-local
   unique timestamps.
4. Validate every source report manifest and SHA256, expected
   per-site totals, source timestamp non-overlap and
   water-reference thermodynamic calculations before creating
   one separate **Stage60 candidate patch**.
5. **Do not** apply these sparse corrections to pre-existing
   model forcing or assert ten-site forcing ready. Earlier
   source Stage48 >26,000 other physical anomaly source events,
   all upstream Stage07/08 QC cohorts and complete ten-site
   NO_LEAP forcing still require full source/coverage QA. If
   any negative *water-reference* VPD appears, count/report it,
   and defer that event's forcing use until the dedicated
   forcing eligibility check. Do not automatically clip
   or silently omit its source time.
6. **Do not auto-release US-Ho1's 917**. Obtain the ver. 3-6
   same-release FLUXNET BADM/BIF UTC_OFFSET from the official
   AmeriFlux data portal. UTC−5 based on geographical context
   or ERA5 similarity alone is not sufficient provenance for
   a complete 1996–2023 tower time-series.

## Stage60 script and pinned IRIDIS6 commands

[Stage60 Python source](../scripts/stage60/60_stage_unified_4411_ERA5_water_humidity_and_hold_Ho1.py)

GitHub commit: `bee64690e05ffeb26b894f8b5affed7bfb53b0c2`

Git blob SHA: `7affb6854f479eb008fd566c2f0e5320320a092f`

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage60/60_stage_unified_4411_ERA5_water_humidity_and_hold_Ho1.py"
  COMMIT="bee64690e05ffeb26b894f8b5affed7bfb53b0c2"
  EXPECTED="7affb6854f479eb008fd566c2f0e5320320a092f"
  mkdir -p "$BASE/scripts/stage60"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage60/60_stage_unified_4411_ERA5_water_humidity_and_hold_Ho1.py" \
    -o "$TMP"
  ACTUAL="$(git hash-object "$TMP")"
  printf 'EXPECTED: %s\nACTUAL:   %s\n' "$EXPECTED" "$ACTUAL"
  test "$ACTUAL" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --stage \
    2>&1 | tee "$HOME/AmeriFlux_Batch02_Stage60_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected successful audit:
`STAGE60 STAGING PASS | 4411 source-unique ERA5 water-humidity replacements`

No original, archived candidate, NetCDF forcing, DATM, CIME, Slurm
or run state is modified by Stage60. Successful execution produces
one new SHA-pinned 4,411-event sparse candidate ledger, including
science decision, source, water thermodynamics and ice-phase
caution fields, and a site summary. **Stage60 has not yet been
executed on IRIDIS6** when this documentation was published.
