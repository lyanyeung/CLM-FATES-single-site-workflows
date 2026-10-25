# Stage82 PASS: Ho1 2000 VPD_F_QC2 is ERA-downscaled, not direct source-measured humidity — Stage83 native-source audit

Date: Sunday 25 October 2026. Actual IRIDIS6 operator log passed Stage82 pinned blob `cf4cbfcf80004548f9ce48af3edd1e1e5c5d3abb`, source hash and original schema checks, full isolated `AUDIT PASS`.

Original Stage82 immutable report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage82_Ho1_2000_full_year_bidirectional_native_T_VPD_source_QC_20261025T193617Z_ba9cfa2a`.

## Scientific source discovery — product-variable semantics are critical

The original year-2000 Ho1 FLUXNET half-hourly temperature `TA_F` was originally measured (TA_F_QC0) for 17,294/17,568 half-hourly records, but **every source `VPD_F_QC` record was 2/17,568**. According to FLUXNET2015 official FULLSET variable definitions, at the native HH resolution `VPD_F_QC=0` means measured, `=1` means good-quality gapfill and **`=2` means downscaled from ERA**. `VPD_F` is the consolidated source combining `VPD_F_MDS` and `VPD_ERA`, using MDS when its quality flag is 0 or 1, otherwise selecting downscaled ERA. `TA_ERA` is also a processed/downscaled temperature, not a second tower instrument.

Authoritative sources: https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/ ; https://fluxnet.org/wp-content/uploads/variable_codes_FULLSET_20161024.pdf ; https://fluxnet.org/data/fluxnet2015-dataset/variables-quick-start-guide/ . The source-product-specific interpretation is independent of generic QC flag conventions for other variables. VPD units are hPa; the diagnostic saturation vapor pressure used here is over water, and below-freezing saturation-over-ice science must be considered before declaring instrument failure.

**This changes the science question:** It may be expected for an ERA-downscaled `VPD_F` to be thermodynamically inconsistent with a collocated source-measured tower `TA_F` when those are not a physically paired T/humidity observation. It is not valid to accuse the original measured tower air temperature of failing merely because reanalysis-source VPD exceeds es(original tower T). Nor is it automatically valid to apply VPD_F unchanged with original TA_F into CLM-FATES. First establish original source pairing and reconcile forcing inputs conservatively.

## Actual Stage82 annual source population and evidence

| Native Ho1 2000 HH record population | Count |
| --- | ---: |
| Total original native source HH (leap year) | **17,568** |
| Native TA_F measured QC0 | **17,294** |
| Source-verified NOAA Bangor air T & native TA_F QC0 matched | **17,140** |
| Native source VPD_F_QC2 (ERA-downscaled classification) | **17,568** |
| Source Ho1 colder than Bangor NOAA by >8°C | **1,554** |
| Source Ho1 warmer than Bangor NOAA by >8°C | **2,518** |
| Source QC0 + NOAA difference within ±8°C | **13,068** |
| Both source air T and NOAA usable but source not-paired/non-QC0 | **428** |

The Stage82 original `TA_ERA` column had valid entries **17,568/17,568**; its ±3°C closeness to original tower TA_F or NOAA varies significantly and does not by itself identify true air temperature. Original NOAA−Ho1 temperature category transitions in 30 min: **521**, with **zero direct extreme warm↔cold switches** and **zero native T 30-minute jumps >8°C** among those category transitions. Slow or regional weather variation can produce large persistent differences; the transition screen does not prove original sensor good/bad.

Original VPD_F is **QC2 for all year**, so source VPD_QC0=0 and VPD_QC1=0 across every NOAA residual class; this source quality flag is not meaningful as measured humidity evidence for 2000. The Stage82 water-saturation screen flagged **1,068** original native T QC0 HH with VPD_F > es_water(T tower): 519 in NOAA-warmer-than-Ho1 (>8°C), 525 within ±8°C and 24 without the combined matched QC0+NOAA conditions. The year-2000 original hard VPD source census was 1,069, with one temperature-not-QC0 instance explaining the one-row difference. This screen indicates incompatibility with the assumed local T/humidity pair; it **does not establish which source, if any, is erroneous**.

Further full-year native T_ERA/source relative-to-airport distinctions from Stage82:

| Source native QC0 air-T discrepancy | Native HH | TA_ERA within 3°C of Ho1 original T | TA_ERA within 3°C of NOAA original T | TA_ERA not within 3°C of either |
| --- | ---: | ---: | ---: | ---: |
| Ho1 colder than Bangor NOAA by >8°C | 1,554 | 359 | 369 | 826 |
| Ho1 warmer than Bangor NOAA by >8°C | 2,518 | 536 | 523 | 1,459 |

The 'two-air-temperature-references' are **not independent local tower truth**. Source ERA and airport/ERA5 reanalysis may share station observations and site-calibration ancestry. NOAA Bangor airport is roughly 46 km from Ho1 forest tower; canopy, snow, exposure, synoptic regimes and nominal historical UTC± validity remain unresolved.

## Stage83: exact original source VPD_F/VPD_ERA provenance and source-T physics

[Stage83 read-only primary-source script](../scripts/stage83/83_Ho1_2000_QC2_ERA_VPD_native_source_provenance_audit.py) crosschecks the exact **Stage82 Git blob, all six finished Stage82 CSV SHA256 outputs and the original Stage49 FLUXNET HH primary file SHA256**. It matches original *physical CSV row number and timestamp* for all 17,568 native 2000 records, comparing direct raw original `TA_F`, `TA_F_QC`, `VPD_F`, `VPD_F_QC`, `TA_ERA` against the Stage82 source lineage data without modifying them.

Optional raw-product fields `VPD_ERA`, `VPD_F_MDS`, `VPD_F_MDS_QC`, `TA_F_MDS`, `TA_F_MDS_QC` are checked **only if actually present in the original primary source file**. Stage83 reports the number of exact numerical VPD_F–VPD_ERA agreements (±0.0001 hPa), optional MDS QC, water saturation es(TA_F_QC0) vs es(TA_ERA), native VPD_F > es under each T, and the number that become physically consistent if evaluated at TA_ERA. It **does not replace VPD, TA or apply a correction**. A case where raw VPD_F differs from raw VPD_ERA is flagged for further source-product investigation, not silently forced into equality.

Stage83 retains all original extreme VPD and complete source QC; never clips high original values to a fabricated physically plausible range. Outputs include per-native-HH T/VPD source audit, monthly source census, temperature-sign/VPD provenance group review and the 1,068 original QC0 T water-saturation mismatch event rows. Note that 1,068 is a provenance/physics diagnostic count, not permission for 1,068 source repairs. It leaves **15,199** Ho1/BZS humidity numerical shadows, **1,675** T science HOLDS, **16,874** source hard VPD HOLDS and Stage64 previous **9,389** additional candidates unchanged.

Stage83 script exact Git commit `53ba77f1e9d8e4f02f552b2f4bd3a9f72b263fa9`, SHA1 Git blob `8e2bdf99a404ba27dcb8832f734028bb084a8660`. Git source was lexically/structurally checked, **not yet run on IRIDIS6**.

## IRIDIS6 one-paste pinned script

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage83/83_Ho1_2000_QC2_ERA_VPD_native_source_provenance_audit.py"
  COMMIT="53ba77f1e9d8e4f02f552b2f4bd3a9f72b263fa9"
  EXPECTED="8e2bdf99a404ba27dcb8832f734028bb084a8660"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage83/83_Ho1_2000_QC2_ERA_VPD_native_source_provenance_audit.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  test ! -L "$SCRIPT"
  if test -e "$SCRIPT"; then
    test -f "$SCRIPT" && test "$(git hash-object "$SCRIPT")" = "$EXPECTED" || {
      echo "REFUSE: Stage83 local source differs, no overwrite" >&2; exit 1;
    }
  else
    cp "$TMP" "$SCRIPT"
  fi
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage83_Ho1_2000_VPD_F_QC2_ERA.log"
)
```

Expected completion only AFTER IRIDIS6 execution: `STAGE83 AUDIT PASS | independently checked 17568 raw source VPD_F_QC2 provenance and original/ERA air T physics; no model approval`.

No original tower, NOAA, CDS, formal NetCDF forcing, DATM, CIME or Slurm is modified. The main science decision should follow the *original-product provenance result* rather than a blanket assumption ERA5 T is better than measured TA_F.
