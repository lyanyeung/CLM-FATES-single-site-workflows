# Batch04 SP1 October 2007 six-day manual temperature replacement — missing Stage14 RH resolved by conservative humidity provenance logic

**2026-10-25 operator failure report:** Original six-day/288-row source and all six mean residual calibrations **PASS** on IRIDIS6; first v1 `--apply` **stopped before creating the new candidate**, with `ValueError: Stage14 RH missing/out of 0..100 for 200710150630`. This is **not** a failure of six daily source temperature bias estimates; it's the v1 assumption that valid RH is present at all 137 target records. **No original/parent research case or model data were changed** in that failed run.

## Revised science/data handling

Temperature intervention is **identical** to the user's manual decision and the [six-day 137-half-hour calibrated plan](SP1_SIX_DAY_OPERATOR_MANUAL_ERA_BIAS_REPAIR_READY_2026-10-25.md):

| Date Oct 2007 | Broken original TA interval (native local-standard time) | Mean normal-period original `TA_F − TA_ERA` °C | Targets |
| --- | --- | ---: | ---: |
| 15 | 06:30–17:30 | −2.832680 | 23 |
| 16 | 06:30–17:30 | −2.472120 | 23 |
| 17 | 06:30–17:30 | −2.251880 | 23 |
| 18 | 06:30–17:30 | −1.555640 | 23 |
| 22 | 06:30–17:30 | −3.633480 | 23 |
| 23 | 07:00–17:30 | −2.844576923 | 22 |
| **Total** | | | **137** |

`TA_new(t) = original FLUXNET TA_ERA(t) + mean(healthy daytime-excluded native QC0 TA_F−TA_ERA on same calendar day)`, with **research candidate `TA_F_QC=2`**. The input `TA_ERA` is **original processed FLUXNET ERA data, not independent ERA5-Land**.

The source `TA_F_MDS` and `TA_F_MDS_QC` fields are left intact, **including when they equal the original suspect temperatures**, to preserve original measured provenance. Downstream science users must choose **trial `TA_F`** explicitly, not mistakenly use `TA_F_MDS`.

Humidity/VPD treatment **is not a blanket VPD overwrite**:

1. **Stage14 RH finite and 0–100%:** recompute candidate `VPD_F` at `TA_new` using that original verified RH, and change candidate `VPD_F_QC` to **2** for derived ERA-origin provenance.
2. **Stage14 RH truly missing:** retain original `VPD_F` numeric value **and original `VPD_F_QC` unchanged**, **only** if `0 ≤ VPD_F ≤ es(TA_new)` and original VPD is QC1 or QC2. Do not invent a vapor-pressure/dew-point value and do not mistake unmodified original VPD for a freshly recalculated humidity product.
3. **Stage14 RH finite but outside 0–100%, or no original physically valid VPD:** hard-stop preflight **without creating any new research candidate**. This needs independent RH/VPD source evidence, not guessing.

The output provenance ledger explicitly records per-HH `humidity_method`, `original_RH_retained_pct` (nullable), trial/old TA and VPD and both QCs. Expected modification count: **exactly 137 HH**, **at least 274 field cells** (TA_F + TA_F_QC per HH), **at most 548 field cells** (VPD_F and VPD_F_QC might also change). **Do not claim the prior v1 expectation of exactly 451 changed cells for v2**, because RH-dependent VPD treatment is conditional. Original source VPD_QC1 count **40** is still verified, but those 40 entries are reclassified only if an RH-based VPD change actually occurs.

The earlier separate **3-point** source-pinned parent is preserved unchanged with original US-SP1 SHA `96d8c6ad2a082bb243160ee91c2aee0d2fcd3dc0a862515519c34dab2fa664d3` and US-SRG SHA `d65523022718819d7013d79f1015fe419958078a8d1fde4f062fa8470929933f`. The Stage14 original FLUXMET and all other 9 selected site input sources retain their original references. The new candidate is intended for research sensitivity only.

## Run RH-safe v2 on IRIDIS6

[RH-safe v2 script](../scripts/manual_review/apply_sp1_six_oct2007_daily_era_offset_rh_safe_v2.py) pinned GitHub commit **`cce12e0e6279f1d0acb1914dd309672573beec2b`**.

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="cce12e0e6279f1d0acb1914dd309672573beec2b"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  mkdir -p "$BASE"
  SCRIPT="$BASE/apply_sp1_six_oct2007_daily_era_offset_rh_safe_v2.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/apply_sp1_six_oct2007_daily_era_offset_rh_safe_v2.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --apply 2>&1 | tee "$BASE/SP1_six_day_RH_safe_v2_apply.log"
)
```

This first checks **all 137 source-target VPD/RH branches and both boundaries on all six days before writing**. When valid, it creates one **new isolated** full 368,208-row US-SP1 research CSV, new 10-site manifest, 137-row temperature/humidity provenance TSV, source-SHA receipt and a row-by-row full research-only audit. It does not run model jobs or write back to FLUXNET/Stage14/the existing 3-point case. User must return stdout including `REPAIR PLAN PASSED`, `INDEPENDENT FULL AUDIT PASS` and `SIX-DAY RESEARCH CANDIDATE CREATED AND INDEPENDENTLY AUDITED` to mark success.

**Scientific status:** user-directed **experimental ERA-origin temperature replacements** only. Original source-validity HOLDs, US-Syv **606+10** deferred and Post-v5/DATM/CIME/Slurm/spinup blockers persist. No new original-tower measurement has been proven valid by constructing an ERA-adjusted alternative.
