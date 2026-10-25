# Batch02 — Stage70 verified original VPD processing lineage; Stage71 independent CDS ERA5 coverage shadow

Operator log on Sunday 25 October 2026: Stage70 pinned script Git blob `89075f1774c4b84308e5f5a53cf0db5f49239837` had `SELF-TEST PASS`, `CHECK PASS`, and `AUDIT PASS`. Stage70 report: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage70_Ho1_BZS_original_VPD_product_lineage_20261025T082409Z_59c37277`.

## Scientifically grounded Stage70 findings

| Site | FLUXNET consolidated VPD QC | Original source | Events | Exact original source field match | VPD_F physically valid with source TA_ERA | Invalid even with TA_ERA |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| US-Ho1 | 2 | original VPD_ERA downscaled product | 16,738 | 16,738 | 15,679 | **1,059** |
| US-Ho1 | 1 | original VPD_F_MDS gapfill | 50 | 50 | 47 | **3** |
| US-BZS | 2 | original VPD_ERA downscaled product | 68 | 68 | 68 | **0** |
| US-BZS | 1 | original VPD_F_MDS gapfill | 18 | 18 | 13 | **5** |

All 16,874 original HALF-HOURLY `VPD_F` records match exactly the expected same-release FLUXNET source product by QC flag, including original FLUXNET primary source SHA256 and physical CSV line identity. This proves lineage; it is not yet independent meteorological validation.

- **99.60%** of all anomalies are QC2 downscaled-ERA VPD, rather than direct VPD measurements. The remaining QC1 are MDS gapfills.
- US-Ho1 QC2 median original `TA_F-TA_ERA` is often around `-12` to `-15 °C` in problematic cold years, so pairing VPD from processed/ERA temperatures with colder measured tower temperature often makes `VPD > es(Ttower)`.
- The **1,059 Ho1 QC2** cases that still fail at the original FLUXNET `TA_ERA` cannot be explained solely by the TA_F/TA_ERA pairing; in 1997–2007 many failing records even have `TA_F-TA_ERA=0`. Other source-processing and/or time mismatch hypotheses require independent evidence.
- BZS 68 QC2 pass at TA_ERA but source TA_F and TA_ERA differ strongly, including a 2012 median `-13.1045 °C` among anomalous QC2 events.
- This confirms **do not rewrite original tower temperatures to TA_ERA just to make processed VPD plausible**; keep original data immutable.

Original source primary SHA256 recorded by Stage70: US-Ho1 `519a3376161fc58ff0d9534de0b1f92a2460a8a2069b45cfb2254bb8f3b7655f`, US-BZS `281db855a6c334b63ae72748ee4bf1587265cc9c48cb4c31b658e91c1cfc89da`.

## Stage71 independent CDS reuse, no new downloads

[Stage71 script](../scripts/stage71/71_reuse_independent_CDS_Ho1_BZS_16874_shadow.py) reads Stage70's SHA-pinned original exact-row ledger and the user-supplied official 2026 site BIF offset evidence. It computes exact quarter-degree grids from published coordinates (Ho1 45.25, −68.75; BZS 64.75, −148.25), searches already existing Stage15/18/50/62 grid-year receipts, and passes every reused receipt through the original Stage50 SHA256+NetCDF+UTC calendar verifier.

For receipt-confirmed years only, Stage71 interpolates independently downloaded CDS ERA5 **water RH** calculated from ERA5 2m T/dewpoint, calculates prospective VPD/QBOT with unchanged original TA_F and PA, checks source tower TA_F_QC0 and abs(tower–independent ERA5 T) <=8C, and emits a **provisional, non-approved shadow** along with year-level source coverage. For missing/invalid receipts, the file explicitly lists `HOLD_NO_VERIFIED_CDS_GRIDYEAR` and failed source checks; Stage71 does not fetch, overwrite, or fabricate independent observations.

Original FULLSET `VPD_ERA` and `TA_ERA` are not independent source proof and are never used as a substitute for a CDS receipt. User-provided official BIF records state nominal UTC_OFFSET −5 and −9 but do not supply historical effective date. Even a numerical Stage71 candidate remains on **historical time / forcing HOLD**. The existing Stage64 9,389 independent numeric candidates stay unchanged; none were applied to DATM forcing.

Stage71 fixed-script commit: `e3abc8dd209384fcf4f159e8923f6167c3547817`.
Stage71 verified Git blob: `b1ce47dedf3da4c931cac3b8a6d4822090870a81`.

## Pinned IRIDIS6 command

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage71/71_reuse_independent_CDS_Ho1_BZS_16874_shadow.py"
  COMMIT="e3abc8dd209384fcf4f159e8923f6167c3547817"
  EXPECTED="b1ce47dedf3da4c931cac3b8a6d4822090870a81"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage71/71_reuse_independent_CDS_Ho1_BZS_16874_shadow.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage71.log"
)
```

Expected completion: `STAGE71 AUDIT PASS | independent CDS Ho1/BZS coverage and source-physics shadow inventoried`.

Stage71 is GitHub-committed and structurally checked but has not been run on IRIDIS6. All input/source hashes are gates. No original EC, independent CDS, Stage64-70, NetCDF forcing, DATM/CIME or Slurm data will be changed by the script.
