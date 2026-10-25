# AmeriFlux Batch02 Stage69 PASS; Stage70 exact original VPD_F source-lineage audit

25 Oct 2026 operator Stage69 pinned fixed Python passed SHA, syntax, self-test, check and audit.

Stage69 isolated report: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage69_16874_original_VPD_vs_water_es_source_diagnosis_20261025T080834Z_782347f2`.

## Exact science outcomes

- All 16,788 US-Ho1 + 86 US-BZS original source hard humidity anomalies have `VPD_F > es_water(TA_F)` and yield `e_actual=es_water - VPD_F<=0` and inferred RH<0. They are not actual independent RH measurements.
- **US-Ho1**: VPD_F_QC=2 16,738, QC=1 50, QC=0 **0**; TA_F_QC0 15,792. Original raw RH missing in 16,764.
- **US-BZS**: VPD_F_QC=2 68, QC=1 18, QC=0 **0**; TA_F_QC0 84. Original raw RH missing in all 86.
- Total VPD source QC2 (downscaled ERA) **16,806 = 99.597%**, QC1 (high-quality MDS gapfill) 68; zero originally measured VPD in this hard-source population.
- Ho1 winter abnormalities last days (longest 236 consecutive HH = 118 hours, 11–16 February 2015). Downscaled/filled VPD is not necessarily thermodynamically consistent with the *original* observed TA_F; this is a hypothesis to test, not yet proof.
- Stage69 `VPD_F / 10` and `/100` made these particular impossible combinations numerically admissible in the diagnostic, but there is no evidence of a factor-of-ten unit error. **Never authorize arbitrary rescaling.**

## Authoritative FLUXNET product meanings

The FLUXNET FULLSET definition specifies:

- `VPD_F` consolidated VPD, unit **hPa**. From VPD_F_MDS if source MDS QC 0/1, otherwise VPD_ERA.
- `VPD_F_QC` at half-hourly cadence: 0 measured, 1 high-quality gapfill, 2 downscaled ERA.
- `VPD_ERA` processed downscaled meteorological product derived from the FLUXNET product's ERA-driven processing, **NOT a new independent CDS ERA5 point/time observation**.
- `TA_F_QC`: 0 measured, 1 good gapfill, 2 ERA-downscaled.

References:

https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/
https://pmc.ncbi.nlm.nih.gov/articles/PMC7347557/

## Stage70: exact original row/source forensics, no forcing writes

[Source-pinned Stage70](../scripts/stage70/70_original_Ho1_BZS_VPD_F_ERA_MDS_source_lineage.py) uses exact Stage69 source event CSV and Stage61/Stage49 original FLUXNET input inventory. It checks original primary **SHA256**, exact physical CSV row, original tower timestamps, temperature, VPD and QC identities. It then reads original `VPD_F`, `VPD_ERA`, `VPD_F_MDS`, `TA_ERA`, and optional raw `VPD` from original site FULLSET_HH (columns missing in release are reported as absent). It tests whether processed QC2 VPD_F matches VPD_ERA, QC1 VPD_F matches VPD_F_MDS, and whether VPD_F is physically valid at *processed TA_ERA* despite being invalid at *original TA_F*. Per-year lineage, QC and saturation results are saved in an immutable new report.

Do not infer a VPD correction, standalone ERA5 validation, or automatic RH model input modification from this stage. A downstream independent CDS ERA5 data product assessment, official historical BIF source clock applicability and residual 69 temperature HOLDs remain separate.

Stage70 commit: `84caa3273118354bc55f388edeb6348edf2e5721`.
Stage70 Git blob: `89075f1774c4b84308e5f5a53cf0db5f49239837`.

## Pinned IRIDIS6 execution

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PY="$CONDA_PREFIX/bin/python"
  REL="examples/AmeriFlux_MultiSite_10_Batch02"
  SCRIPT="$HOME/CLM-FATES-single-site-workflows/$REL/scripts/stage70/70_original_Ho1_BZS_VPD_F_ERA_MDS_source_lineage.py"
  COMMIT="84caa3273118354bc55f388edeb6348edf2e5721"
  EXPECTED="89075f1774c4b84308e5f5a53cf0db5f49239837"
  mkdir -p "$(dirname "$SCRIPT")"
  TMP="$(mktemp)"
  trap 'rm -f "$TMP"' EXIT
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage70/70_original_Ho1_BZS_VPD_F_ERA_MDS_source_lineage.py" \
    -o "$TMP"
  echo "EXPECTED: $EXPECTED"
  echo "ACTUAL:   $(git hash-object "$TMP")"
  test "$(git hash-object "$TMP")" = "$EXPECTED"
  cp "$TMP" "$SCRIPT"
  "$PY" -m py_compile "$SCRIPT"
  "$PY" -B "$SCRIPT" --self-test
  "$PY" -B "$SCRIPT" --check
  "$PY" -B "$SCRIPT" --audit \
    2>&1 | tee "$HOME/Batch02_Stage70.log"
)
```

Expected completion: `STAGE70 AUDIT PASS | 16874 original VPD_F sources checked against same-release ERA/MDS companions`.

Published script statically verified against Git blob. Stage70 has not yet executed on IRIDIS6, no claimed source/model writes or independence approvals.
