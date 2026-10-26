# Batch04 — SYVH9 completed 10/10 full seven-met NOLEAP source audit; SYVH10 original BIF/surface/ZBOT/CIME Gate-1

Actual operator 2026-10-26 SYVH9 source verification and independent ERA5-Land longwave correction are permanently documented in [SYVH9 12-HH and Gate-0 operator evidence](SYVH9_INDEPENDENT_ERA5LAND_12_LONGWAVE_REPAIR_10SITE_GATE0_PASS_20261026.md). **Six independent CDS STRD source SHA receipts verified; exactly 12 native HH replaced in five sites; all 10 site seven met fields and full NOLEAP calendar pass numerical QA; only three documented raw VPD quantisation exceptions.**

**Final research source selector** (do not use older Stage11 / SYVH3 manifest):
```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_Batch04_SYVH9_12_low_LW_5sites_independent_ERA5Land_research_not_approved/candidate_20261026T121123Z_a8b8146f/RESEARCH_TEN_SITE_MANIFEST.tsv
```

## Why no DATM or model jobs yet

The seven numerical primary met fields available to a model converter are now checked: `TA_F [°C]`, `VPD_F [hPa]`, `PA_F [kPa]`, `SW_IN_F [W/m²]`, `LW_IN_F [W/m²]`, `WS_F [m/s]`, `P_F [mm/30min]`. Derivations for a controlled preview use `TBOT=TA+273.15`, `PSRF=PA*1000`, `FSDS=SW`, `FLDS=LW`, `WIND=WS`, `PRECTmms=P_F/1800`, vapor pressure `e=es(T)-VPD`, specific humidity `q=0.622e/(10PA - 0.378e)`, `SHUM=QBOT=q`. The three source VPD rounding-only oversaturations need documented **output-only** zero-vapour convention for a future NetCDF preview (no editing source `TA_F` or `VPD_F`). Exact time-centering is not established by mere continuity.

[Existing Batch01 Stage81 DATM script](../../AmeriFlux_MultiSite_10/scripts/stage81/81_build_DATM_from_Stage80.py) provides a technical preview precedent: model stream uses `SHUM` sourced from `QBOT`, `RH` reconstructed for checking, NOLEAP annual NetCDF and a template XML, but explicitly does **not** verify ZBOT, actual domain choice, CIME stream mapping, source time-centering, or site science approval. Its old Stage80 source manifest **must not be reused for Batch04**. Likewise, a tower canopy-height metadata variable is **not** a verified meteorological `ZBOT` measurement height.

## Next automatic no-write check — SYVH10

New [`stage_syvh10_postv5_site_metadata_and_DATM_gate1_readonly.py`](../scripts/manual_review/stage_syvh10_postv5_site_metadata_and_DATM_gate1_readonly.py), pinned commit **`657d7239421934eaa2ba4d8f4b09f64a32c6eb5f`**.

Verifies:
1. Actual SYVH9 final source repair receipt, 10-site manifest and 10 source SHA, all ten full seven-met Gate-0 result receipts, 5 corrected full source file pointers and 3 VPD rounding annotations.
2. Stage05 three original raw sources and Stage08 seven, independently SHA checked; each original FLUXNET BIF exact tower coordinate and native **UTC_OFFSET**, BIF SHA and relevant instrument-height metadata candidates **without assuming they equal ZBOT**.
3. Existing site `subset_data/surfdata*.nc` point-surface candidate count, SHA and `LONGXY/LATIXY`, comparing to tower BIF without automatically choosing a surface if ambiguous; domain-file candidate inventory without silently activating one.
4. Reports the exact still-unresolved **sensor-specific ZBOT, source interval/time centering, CIME/CDEPS active field mapping/domain, source science approval**. All source and model files untouched. Report JSON/TSV only under HOME.

Run on IRIDIS6:

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="657d7239421934eaa2ba4d8f4b09f64a32c6eb5f"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  FINAL="/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_Batch04_SYVH9_12_low_LW_5sites_independent_ERA5Land_research_not_approved/candidate_20261026T121123Z_a8b8146f"
  mkdir -p "$BASE"
  SCRIPT="$BASE/stage_syvh10_postv5_site_metadata_and_DATM_gate1_readonly.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/stage_syvh10_postv5_site_metadata_and_DATM_gate1_readonly.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --self-test
  python3 -u -B "$SCRIPT" --candidate-dir "$FINAL" --report \
    2>&1 | tee "$BASE/Batch04_SYVH10_Postv5_DATM_metadata_gate1.log"
)
```

Expected:
- `SYVH10 SELF-TEST PASS...`
- Ten `GATE1 SITE...` lines including BIF UTC offsets, height metadata candidates and point surface status
- `SYVH10 SOURCE PROVENANCE AND POSTV5 DATM METADATA GATE1 AUDIT COMPLETE`
- `DATM/CIME/SLURM/MODEL SPINUP NOT AUTHORISED`

**Next after real SYVH10 output:** inventory actual sensor measurement heights and configured CIME/DATM field mappings by site; isolate any real unresolved scientific conflict. Only then create a **versioned model technical preview**, not production/release. No operator manual judgement is needed **right now** for the 12 LW repairs or 10-site seven-met numerical data: they passed. The Gate-1 code is published, **not yet executed on IRIDIS6**; actual station height and surface status must be taken from its live output, not guessed.
