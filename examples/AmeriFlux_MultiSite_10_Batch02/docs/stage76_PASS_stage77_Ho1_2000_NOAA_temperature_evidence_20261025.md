# Stage76 PASS: measured Ho2/Ho3 cross-tower science context → Stage77 Bangor NOAA year 2000

Date: 2026-10-25. The operator's pinned Stage76 Git source blob `bf4694181f2dd4625143a7397089aea2c2993832` passed self-test, Stage75 original provenance `--check` and final isolated `--audit`.

Stage76 verified original report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage76_1675_Ho1_BZS_original_cross_tower_QC0_context_20261025T092852Z_ceabe542`.

## Original SOURCE SHA validation

Stage76 verified exact FLUXNET original native source SHA before comparing real **TA_F_QC=0** records. Among the 1,619 US-Ho1 temperature HOLD native timestamps:

- US-Ho2 original FLUXMET_HH 1999–2025: **1,320** exact same-local-timestamp matches, but only **327** have valid original TA_F QC0; source SHA256 `b309740af7b6efb9c4faef8b8d9cded2a25bb8386efbd7ea72b00646bd2fbc3d`.
- US-Ho3 original FLUXMET_HH 2003–2021: **410** exact native timestamps, **408** TA_F QC0; source SHA256 `bcf15cc584a6fe6560fb5834c6bae3a9a56ab68f9222f30a41c5738f43061b54`.
- Ho2/Ho3 exact timestamp matching is **not historical offset equivalence certification**. Relative sensor heights, land cover and local gradients also remain unverified.

## Stage76 exhaustive temperature HOLD classification

| Original cohort | No neighbor QC0 at exact time | Neighbor supports Ho1 T (within 3°C) | Neighbor supports CDS T | Conflicting both | Matches neither | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| US-Ho1 original TA_F_QC1/2 | 605 | 15 | 256 | 104 | 16 | **996** |
| US-Ho1 original TA_F_QC0 but abs(Ttower - TCDS)>8C | 580 | 42 | **0** | **0** | 1 | **623** |
| US-BZS original T_QC1/2 or large delta | no site-relevant Ho2/Ho3 evidence | — | — | — | — | **56** |

Crucially **US-Ho1 2000 accounts for 505 of the 623 native measured QC0 versus independent CDS >8C holds**, and **all 505 have no original native QC0 Ho2/Ho3 observation at that timestamp**. This is lack of independent ground measurement, not an assertion of a sensor problem. All **36** US-Ho1 2008 native measured T discordant records have native QC0 neighbor evidence supporting original Ho1, not CDS. The remaining 42 Ho1 source-QC0-difference records supported by neighbors include these 36 in 2008 and 4 in 2013 etc.

Additional decision caution: the 'neighbor supports both' category for 104 QC1/QC2 Ho1 temperature cases means the set of native neighbor observations includes evidence near each comparator under exploratory ±3°C rule. It is not conclusive identification of a correct air-temperature source. QC0 itself only means recorded measured-source provenance in this product and does not demonstrate absolute instrument accuracy.

## Stage77: previously established independent NOAA Bangor (GHCNh) methodology extended to Ho1 2000

Older [Stage39 NOAA GHCNh source availability](../scripts/stage39/39_probe_NOAA_GHCNh_Bangor_history.py) and [Stage40 source-QC parser](../scripts/stage40/40_compare_NOAA_Bangor_QC_with_Ho1_CDS.py) used station `USW00014606` Bangor, original numeric NOAA hourly observations, observed source/origin and quality code whitelist, ±30-minute nearest UTC observation, and rejection of equidistant conflicting reports. However those original Stage39/40 evidence pulls covered **1998, 1999 and 2001**, not 2000, and did not preverify a SHA256 for 2000.

New [Stage77 script](../scripts/stage77/77_Ho1_2000_QC0_NOAA_Bangor_source_temperature_probe.py) verifies the exact Stage76 505 site-year original measured temperature cases and SHA-pins the original Stage40 parser (Git blob `8767dbcad2c3c6cd431b37968e867838eac01d87`). Stage77 `--check` is source only and offline. `--audit` makes a bounded HTTPS request for NOAA GHCNh year 2000 `GHCNh_USW00014606_2000.psv`, compares only formally accepted source-QC records at each provisional Ho1 local-UTC−5 time, and archives the **original unmodified first-acquired 2000 NOAA PSV bytes** in a new isolated Stage77 report with source SHA256, exact per-event pairings, counts of distinct NOAA physical reports versus reused half-hours, and descriptive temperature differences.

This NOAA source is **additional ground-station context**, not a replacement for local Ho1 tower sensor measurements. Bangor is an airport roughly 46 km from forest canopy; bad weather gradients/elevation, 30-minute pairing and historical time assumptions may limit applicability. **A NOAA comparison never automatically releases the 505 Ho1 Q0 T HOLDs or any historical BIF/forcing permissions.** US-BZS 56 temperature HOLDs need a separate local Alaska source; Bangor is geographically irrelevant.

Stage77 source commit `0f6ee696539a3088e803afb5d1392736261116a9`; Git blob `0211de8a12aba54827fd55bdfbe9890c21c14734`.

## IRIDIS6 pinned execution (one NOAA year, raw byte archive only in new report)

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL/scripts"
  SCRIPT="$BASE/stage77/77_Ho1_2000_QC0_NOAA_Bangor_source_temperature_probe.py"
  PRIOR="$BASE/stage40/40_compare_NOAA_Bangor_QC_with_Ho1_CDS.py"
  COMMIT="0f6ee696539a3088e803afb5d1392736261116a9"
  EXPECTED="0211de8a12aba54827fd55bdfbe9890c21c14734"
  EXPECTED_PRIOR="8767dbcad2c3c6cd431b37968e867838eac01d87"
  mkdir -p "$(dirname "$SCRIPT")" "$(dirname "$PRIOR")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT

  # Required Stage40 parser: Stage77 imports it in --self-test.
  # No Stage39 download is needed for the Stage77 parser functions.
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/$REL/scripts/stage40/40_compare_NOAA_Bangor_QC_with_Ho1_CDS.py" \
    -o "$TMP"
  echo "EXPECTED STAGE40: $EXPECTED_PRIOR"
  echo "ACTUAL   STAGE40: $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED_PRIOR"
  cp "$TMP" "$PRIOR"

  # Pinned original Stage77 remains unchanged.
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage77/77_Ho1_2000_QC0_NOAA_Bangor_source_temperature_probe.py" \
    -o "$TMP"
  echo "EXPECTED STAGE77: $EXPECTED"
  echo "ACTUAL   STAGE77: $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$PRIOR"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage77_Ho1_2000_NOAA.log"
)
```

Expected script-only completion (not yet independently run on IRIDIS6):
`STAGE77 AUDIT PASS | immutable NOAA 2000 raw and exact 505 Ho1 QC0 T source context; no forcing approval`.

NOAA network/source availability and QC coverage for **2000 have not yet been demonstrated**. The 2000 raw SHA is acquired at first operator run, not invented. `STAGE77 SELF-TEST PASS` and `STAGE77 CHECK PASS` are prerequisites, not proof of station measurement representativeness. No original EC, CDS, NetCDF forcing, DATM, CIME, Slurm or previous report is mutated.

## Stage77 dependency recovery — original operator failure

The operator's original Stage77 Git blob verified but `--self-test` stopped with `ValueError: Pinned Stage40 original QC parser absent/symlinked`. This is a **missing local prerequisite**, not a failed Stage76 source science audit or NOAA source failure. Exact upstream Stage40 file is `scripts/stage40/40_compare_NOAA_Bangor_QC_with_Ho1_CDS.py` with Git blob `8767dbcad2c3c6cd431b37968e867838eac01d87`, matching Stage77's `PRIOR_BLOB`. The command above installs this exact verified file before invoking Stage77 self-test/check/audit, without altering Stage40 science logic or Stage77's original pinned source. Stage40's NOAA parser `parse_psv` / `select` / `selftest` are self-contained for this use; its older Stage39 prereq is only used in a separate Stage40 analysis entrypoint, not Stage77. Do not assume Stage77 NOAA year-2000 download has succeeded yet.
