# Stage83 PASS — native US-Ho1 2000 original VPD_F is exactly VPD_ERA; Stage84 32 residual ERA-self inconsistency events

Date: 2026-10-25. Operator Stage83 Git blob `8e2bdf99a404ba27dcb8832f734028bb084a8660` passed actual IRIDIS6 SHA, self-test, original source physical line+timestamp/Stage82 output checksum checks and final isolated `AUDIT PASS`.

Original completed Stage83 report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage83_Ho1_2000_original_VPD_QC2_ERA_T_context_20261025T224055Z_24b5df95`.

## Verified Stage83 original FLUXNET FULLSET_HH source lineage

Original source SHA256: `519a3376161fc58ff0d9534de0b1f92a2460a8a2069b45cfb2254bb8f3b7655f`.

| Direct source evidence | Number |
| --- | ---: |
| Native 2000 HH records (366×48) | **17,568** |
| Original `VPD_F_QC=2` (downscaled ERA source) | **17,568 / 17,568** |
| Original `VPD_F` exactly equals raw `VPD_ERA` numerically | **17,568 / 17,568** |
| Original measured-provenance `TA_F_QC=0` | **17,294 / 17,568** |
| `VPD_F > eswater(TA_F)` among original TA_F_QC0 | **1,068** |
| Of these 1,068 mathematically within eswater(TA_ERA) | **1,068 / 1,068** |
| **Different** records with `VPD_F > eswater(TA_ERA)` | **32**, all January |
| Inconsistent with both `eswater(TA_F QC0)` and `eswater(TA_ERA)` | **0** |

Of the 32 unmatched ERA-T exceedance records, Stage83 grouped **12** with NOAA colder than original Ho1 by >8°C, **18** within ±8°C, and **2** without combined native QC0 + independently screened NOAA match. No 32-record observation is in the 1,068 original TA_F QC0 self-incompatibility group.

Source HH included original `VPD_ERA`, `VPD_F_MDS`, `VPD_F_MDS_QC`, `TA_F_MDS`, and `TA_ERA` fields (source presence confirmed by Stage83). Source `VPD_F_MDS_QC` was not QC0 or QC1 for any original source HH, so the FULLSET `VPD_F` consolidated source relies exclusively on ERA downscaling. This was previously not obvious from comparing an ERA humidity product against measured tower TA_F.

Official FLUXNET FULLSET source conventions: https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/ and https://fluxnet.org/wp-content/uploads/variable_codes_FULLSET_20161024.pdf . The source QC2 flag is **not** a generic error flag and does not itself establish that ERA product VPD is wrong.

**Scientific consequence:** A VPD downscaled from ERA reanalysis is not a native humidity sensor paired to `TA_F_QC0`. Testing `VPD_ERA` against a distinct original tower air temperature can expose source mismatch, not sensor failure. All 1,068 source inconsistency records are mathematically compatible with the companion processed ERA temperature. This is not an endorsement of replacing original measured tower TA_F in the model, and it does not prove the ERA VPD/TA_ERA weather values are local ground truth or appropriate CLM-FATES forcing without further consistency testing.

## Stage84: only the 32 original ERA-VPD vs ERA-temperature water-saturation exceedances

[Stage84 source](../scripts/stage84/84_Ho1_2000_32_native_ERA_VPD_T_own_source_physics_hold_audit.py) verifies the completed exact Stage83 Git source and ALL five Stage83 original CSV output SHA256 digests, the original Stage83 raw FLUXNET full-year 17,568 original timestamp and physical row IDs, independent source `VPD_F`=`VPD_ERA` equality, the exact 1,068 source measured-T incompatibilities and the separate **32** native `VPD_F > eswater(original TA_ERA)` source cases.

Stage84 recomputes original `eswater(TA_ERA)`, extra VPD in hPa and the **implied** RH=100×(1−VPD/eswater) for mathematical context, with below-freezing `esice` sensitivity strictly as a separate diagnostic. Negative implied RH is **not a measured RH observation**. Original ERA-downscaled products' effective T and VPD inputs, source interpolation and subfreezing conventions must be investigated before claiming the 32 are 'bad' ERA values. The 32 exact original January half-hours, dates, native T/TQC, original VPD and QC, optional MDS, daily counts, 30min-contiguous episodes and full ±6h source HH context are printed and saved. Raw extreme values are never clipped, originals never altered. No official historical BIF UTC/source/forcing approval granted.

Stage84 Git commit `4de795b63add3fe29b6278d4481f3abafc32c703`, Git blob `9118b2a8a7e93d5fa7e78762de5beb14f0dd23f2`. Its source bracket/quote structural consistency was checked after GitHub creation, **not yet actual Python compiled or executed on IRIDIS6**.

## IRIDIS6 pinned single command — offline, immutable science

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage84/84_Ho1_2000_32_native_ERA_VPD_T_own_source_physics_hold_audit.py"
  COMMIT="4de795b63add3fe29b6278d4481f3abafc32c703"
  EXPECTED="9118b2a8a7e93d5fa7e78762de5beb14f0dd23f2"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage84/84_Ho1_2000_32_native_ERA_VPD_T_own_source_physics_hold_audit.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  test ! -L "$SCRIPT"
  if test -e "$SCRIPT"; then
    test -f "$SCRIPT" && test "$(git hash-object "$SCRIPT")" = "$EXPECTED" || {
      echo "REFUSE: Stage84 existing source changed, no overwrite" >&2; exit 1;
    }
  else
    cp "$TMP" "$SCRIPT"
  fi
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage84_Ho1_2000_32_ERA_self_physics.log"
)
```

Expected **only if** full on-cluster audit succeeds: `STAGE84 AUDIT PASS | 32 exact Ho1 January 2000 ERA VPD > eswater(ERA T) original cases, no source repair`. Output is a new isolated Stage84 report and SHA manifest. The original 16,874 source hard-VPD events, 15,199 numerical-only humidity shadow candidates, 1,675 temperature science holds and other Stage64 9,389 proposals remain unchanged; no original FLUXNET, NOAA, CDS, forcing NetCDF, DATM, CIME or Slurm writes.
