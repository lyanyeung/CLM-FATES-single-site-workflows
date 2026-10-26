# Batch04 SYVH5 — actual operator 10/10 primary humidity numerical PASS; next seven-met NOLEAP Post-v5 Gate-0

**Source:** actual IRIDIS6 operator-returned stdout `Batch04_SYVH5_SOURCE_RH_VS_PRIMARY_FORCING_20261026T041121Z_e269ee`, 2026-10-26 04:11 UTC. Exact source site SHAs all verified; no source/model files changed. Final US-Syv SYVH3 SHA still `9299193bc12b06e37211d84d31c333e299f99cb0ed96ebc6ed224ef9eaaf02aa`.

## Verified result

- **10 / 10 sites `MODEL_NUMERICAL_HUMIDITY_PASS_WITH_EXPLICIT_VPD_ROUNDING`**, `NUMERIC_BLOCKERS {}` for every site, from SHA-selected `TA_F`, `VPD_F`, `PA_F`.
- Native VPD saturation quantisation-only exceptions: **US-Rpf 2008-02-06 07:00** (`T=-29.227°C; VPD=0.549hPa; es=0.5488405189hPa; excess 0.0001594811hPa`), **US-Rpf 2008-02-06 09:00** (`T=-29.244°C; VPD=0.548hPa; es=0.5479667749hPa; excess 0.0000332251hPa`), **US-Syv 2008-03-09 13:00** (`T=-6.234°C; VPD=3.842hPa; es=3.8419768033hPa; excess 0.0000231967hPa`). All below native 3-decimal VPD half-ulp **0.0005 hPa**. Retain source T/VPD/QC. These **3** raw records cannot be directly fed into unguarded `e=es−VPD` since it would yield a tiny negative vapor pressure; the future generated **MODEL QBOT** should have an explicit, provenance-recorded source-quantisation policy without silently adjusting original VPD.
- Derived QBOT preview ranges all within **0–0.041 kg/kg** (max **US-Ton `0.0406573731` kg/kg**). This is a numerical assessment, NOT a DATM forcing file.
- The auxiliary original source `RH` shows some very large differences from the **model internally derived** RH: e.g. **US-Seg 86.89pp; US-Ses 85.835pp; US-SP1 62.405pp; US-Uaf 43.233pp**. Many of the worst have QC1 provenance. **Do not overwrite source `RH`, `TA_F`, `VPD_F`**, or reinterpret independent original RH as erroneous on that basis. The model humidity precedence must be explicit.
- **Other nine site SHA pointers unchanged**. The operator retained the past manual SP1/SRG/Seg temperature source decisions separately; numerical humidity passing cannot supersede source/QC0 science holds.

## Existing checked technical precedent — NOT yet implemented for Batch04

The repo's **Batch01 Stage81** [`81_build_DATM_from_Stage80.py`](../../AmeriFlux_MultiSite_10/scripts/stage81/81_build_DATM_from_Stage80.py) defines all 7 annual DATM fields and uses `SHUM = QBOT`, with `RH` **derived** as a non-stream mapped cross-check field. The **Batch03 Stage11b** [`11b_three_site_postv5_gate0_audit.py`](../../AmeriFlux_MultiSite_10_Batch03/scripts/stage11/11b_three_site_postv5_gate0_audit.py) identifies the native sources `TA_F,VPD_F,PA_F,SW_IN_F,LW_IN_F,WS_F,P_F`, checks derived `TBOT,QBOT,PSRF,FSDS,FLDS,WIND,PRECTmms` and NOLEAP. In the native release `P_F` is **mm/30 minutes** (converted to `mm s−1` by division by **1800**). **Batch04 has not yet independently demonstrated the final actual site-specific DATM field map, ZBOT sensor height, time-centering or domain file**.

## Next actual action — SHA-selected Stage SYVH6 (research read-only, NOT YET RUN)

New independently source-pinned [`stage_syvh6_ten_site_postv5_gate0_all_meteorology_readonly.py`](../scripts/manual_review/stage_syvh6_ten_site_postv5_gate0_all_meteorology_readonly.py), GitHub revision **`65ee7d0715d5f6ed5dc857214ea98a58fdf4d6f7`**, uses the **same exact pinned revision** of the [SYVH5 helper](../scripts/manual_review/stage_syvh5_ten_site_vpd_driven_humidity_readiness_readonly.py) in the *same local directory*. It reviews all 7 native met fields, each full time source and every 29 February interval (365×48 expected per model year after exclusion), SHA, realistic wind/precipitation/shortwave/longwave/pressure bounds, small negative radiation/wind/rain rounded-source diagnostic, dry-air source rounding, and physically derived QBOT preview. It **does not create DATM/NetCDF or modify any original/derived source**.

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="65ee7d0715d5f6ed5dc857214ea98a58fdf4d6f7"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  FINAL="/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_US_Syv_stage_SYVH3_last_18_QC0_RH_closure_candidate_not_approved/candidate_20261026T034556Z_3372d66c"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/stage_syvh5_ten_site_vpd_driven_humidity_readiness_readonly.py" -o "$BASE/stage_syvh5_ten_site_vpd_driven_humidity_readiness_readonly.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/stage_syvh6_ten_site_postv5_gate0_all_meteorology_readonly.py" -o "$BASE/stage_syvh6_ten_site_postv5_gate0_all_meteorology_readonly.py"
  python3 -B -m py_compile "$BASE/stage_syvh5_ten_site_vpd_driven_humidity_readiness_readonly.py" "$BASE/stage_syvh6_ten_site_postv5_gate0_all_meteorology_readonly.py"
  python3 -u -B "$BASE/stage_syvh6_ten_site_postv5_gate0_all_meteorology_readonly.py" --manifest-dir "$FINAL" --report \
    2>&1 | tee "$BASE/Batch04_SYVH6_POSTV5_Gate0_SEVEN_MET_NOLEAP.log"
)
```

Expected: `SOURCE PIN VERIFIED FINAL SYVH3+9 OTHER SITES 10/10`, ten `SITE ... NUMERIC_BLOCKERS ... NONPRODUCTION_POLICIES` lines, `SYVH6 TEN SITE NATIVE SEVEN_MET NOLEAP GATE ...`, and a small JSON/TSV report under HOME. If all ten have empty blockers, a subsequent **technical conversion-preview** (not model submission) can derive an isolated `QBOT/SHUM` with an explicitly reviewed 3-halfhour source-precision rule, and validate 7 met + ZBOT/calendar inputs against the actual CIME configuration. Any source met numeric blocker gets returned with timestamps and QC/source evidence; no new human decision without a genuine source ambiguity.

**Production Post-v5 release, source-QC0 science, ZBOT heights, point-surface/PFT, DATM time-centering, actual CIME stream mapping and Slurm spinup** remain separate required decisions, NOT passed by Gate-0.
