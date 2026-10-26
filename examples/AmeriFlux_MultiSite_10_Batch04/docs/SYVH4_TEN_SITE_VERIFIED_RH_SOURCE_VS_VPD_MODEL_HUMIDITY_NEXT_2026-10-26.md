# Batch04 ten-site SYVH4 actual operator PASS — resolve RH source semantics without tampering with tower T/VPD

**2026-10-26, operator-provided IRIDIS6 stdout.** Read-only batch audit complete for all 10 sites. This document distinguishes data integrity/primary physical humidity from auxiliary source RH observational-vs-reconstructed discrepancies. **No production input approved; no new source corrections have been run.**

## Verified complete-input and original-source integrity

- **10/10** final research selection complete-file SHA256 **PASS**. Final US-Syv SYVH3 SHA **`9299193bc12b06e37211d84d31c333e299f99cb0ed96ebc6ed224ef9eaaf02aa`**, operator-verified last 18 RH-only source corrections and full 438288 original native HH side-by-side provenance audit PASS.
- **10/10** sites: 30-minute native `TIMESTAMP_START/TIMESTAMP_END` continuity PASS, 0 bad step/END timestamps, no VPD outside `es_water(T)` beyond original three-decimal VPD precision. US-Rpf 2 and US-Syv 1 VPD source-precision-only exceptions.
- **10/10** sites: model-relevant T/VPD basic source saturation PASS (numerical, **not** a substitute for source sensor temperature science review). Full site data source manifest other nine site pointers unchanged.

### Raw source RH diagnostics (NOT independent confirmed bad FLUXMET VPD)

| Site | Native RH/VPD-derived difference flagged by provisional SYVH4 screen | RH source out of [0,100]% | RH source missing |
| --- | ---: | ---: | ---: |
| US-Rpf | 32,973 | 0 | 37,920 |
| US-SP1 | 2,040 | 0 | 52,320 |
| US-SRG | 118 | 263 | 7,514 |
| US-SRM | 1,003 | 0 | 3,926 |
| US-Seg | 11,021 | 0 | 7,949 |
| US-Ses | 8,796 | 0 | 6,430 |
| US-Slt | 1,200 | 0 | 9,055 |
| US-Syv | 7,054 | 0 | 219,653 |
| US-Ton | 544 | 1,559 | 10,679 |
| US-Uaf | 68,968 | 28 | 6,939 |
| **Totals** | **133,717** | **1,850** | **362,385** |

The provisional `RH_NOT_CLOSED_BEYOND_VPD_RESOLUTION` count is **not a count of defective source VPD or temperature**. `RH` in the assembled research source can be independently measured, processed by a different historical method, or present in only some years. It **cannot be silently replaced** with algebraically derived `RH=100×[1−VPD/e_s(T)]` while claiming raw RH remains an observation. Likewise, absent RH does not imply `VPD_F`, `TA_F`, `PA_F` absent.

**Correct separation:** For future CLM-FATES DATM forcing conversion, derive a consistent humidity state from the final selected native `TA_F`, `VPD_F`, and `PA_F` (where model humidity is computed from VPD rather than from independently sourced RH), and document input precision. Use `e=e_s(T)−VPD` in hPa and original `PA_F` in kPa, and `QBOT=0.622e/[10 PA_F−(1−0.622)e]` kg kg−1. Only permit this if complete source integrity, pressure and humidity physics support it. Preserve the original/source candidate `RH` column as separately traceable auxiliary material; never mutate original QC0 measured source RH or infer source RH failure from closure alone.

### Next action is AUTOMATED, not 133,717 manual decisions

A newly committed **read-only**, source- and SHA-locked [SYVH5 ten-site primary-humidity vs auxiliary-RH screening script](../scripts/manual_review/stage_syvh5_ten_site_vpd_driven_humidity_readiness_readonly.py), revision **`1d80fa04fc1faea690709a3e020bae89f7cc9a47`**, will independently stream the exact ten full selected native datasets from the operator's actual SYVH3 manifest and:

1. Confirm 10 source SHAs, final SYVH3 receipt, all nine other final research site selections unchanged.
2. Evaluate ability to calculate model-model-consistent **QBOT** from source `TA_F/VPD_F/PA_F`, with strict native local 30-minute timing, plausible 65–110 kPa pressure and 0–0.1 kg/kg specific humidity; explicitly enumerate source VPD quantisation exceptions without silently capping negative calculated vapour pressure.
3. Split **stored source `RH`** records into missing, outside 0–100, within precision closure, 0–1, 1–5, 5–20, >20 percentage point difference from source-derived RH. Print worst exact timestamps with QC fields, per-year counts and per-site SHA. This is a **diagnostic classification** and does **not** automatically rewrite QC0 native T/VPD/RH.
4. New optional tiny JSON and TSV audit under user HOME, only. No Post-v5 model files or Slurm jobs. **NOT RUN ON IRIDIS6** as of writing.

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="1d80fa04fc1faea690709a3e020bae89f7cc9a47"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  FINAL="/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_US_Syv_stage_SYVH3_last_18_QC0_RH_closure_candidate_not_approved/candidate_20261026T034556Z_3372d66c"
  mkdir -p "$BASE"
  SCRIPT="$BASE/stage_syvh5_ten_site_vpd_driven_humidity_readiness_readonly.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/stage_syvh5_ten_site_vpd_driven_humidity_readiness_readonly.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --manifest-dir "$FINAL" --report \
    2>&1 | tee "$BASE/Batch04_SYVH5_TEN_SITE_MODEL_HUMIDITY_VS_SOURCE_RH.log"
)
```

**Post-SYVH5 possible next work:** verify the actual planned Post-v5 DATM/CIME converter's meteorological field map and documented source precedence. If model requires `QBOT` or consistent RH derived from `TA_F/VPD_F/PA_F`, generate it in a **separate versioned forcing/NetCDF staging step** after source lineage QA. If a conversion consumes original `RH` as a forcing variable, it must be source-provenance-triaged and changed only in a new alternative, never in-place. Separately reconcile prior other-site raw sensor T scientific holds and operator decisions; don't confuse the RH source diagnostic with source T approval.

**Human decisions required right now:** None needed for 133,717 auxiliary RH discrepancies. Only source conflicting actual required forcing variables (from verified field map) or source T cases with no already approved alternative should be escalated. No model spinup yet.
