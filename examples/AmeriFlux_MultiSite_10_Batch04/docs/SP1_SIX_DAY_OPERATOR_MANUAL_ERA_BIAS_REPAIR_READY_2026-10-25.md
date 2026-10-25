# Batch04 — operator-directed 6 × daily bias-corrected source TA repair, 137 half-hours — SCRIPT READY

**2026-10-25, user decision:** For original US-SP1 2007-10-15–18 and 2007-10-22–23, flag the clearly wrong *daytime* temperature intervals and replace research-candidate `TA_F` using a **daily arithmetic mean tower-minus-original-FLUXNET-`TA_ERA` bias** computed from the **normal parts of that SAME calendar day**. These replacements are from `TA_ERA` (a **processed FLUXNET ERA product**, **not** the separately downloaded ERA5-Land file). Label ERA-derived replacements **trial QC2**. This decision is a manual alternative scenario; it does not amend official raw tower QC0 evidence.

## Source-verified full 24h original six-day operator data

The operator uploaded complete **288 native 30-minute source rows**, 48 per date; every `TA_F_QC=0`. [Original full-day extractor](../scripts/manual_review/inspect_sp1_six_october_days_full_24h_original_T_ERA_QC.py) pins source SHA `d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963`. Direct visual inspection identifies abrupt QC0 drop at **06:30** for Oct 15, 16, 17, 18 and 22, or **07:00** for Oct 23; QC0 values recover abruptly at **18:00** on all six dates.

**Scientific method:**

```text
daily_offset[d] = mean( original_TA_F(t) - original_TA_ERA(t) )
                  for all original QC0 HH on date d:
                       t < anomaly_start[d] OR t >= 18:00

new_TA_F(t) = original_TA_ERA(t) + daily_offset[d]
                  for anomaly_start[d] <= t <= 17:30
```

| Original date | Abnormal native local-standard HH | Original QC0 normal calibration HH | Daily mean original TA_F−TA_ERA °C | New HH |
| --- | --- | ---: | ---: | ---: |
| 2007-10-15 | 06:30–17:30 | 25 | **−2.832680000** | 23 |
| 2007-10-16 | 06:30–17:30 | 25 | **−2.472120000** | 23 |
| 2007-10-17 | 06:30–17:30 | 25 | **−2.251880000** | 23 |
| 2007-10-18 | 06:30–17:30 | 25 | **−1.555640000** | 23 |
| 2007-10-22 | 06:30–17:30 | 25 | **−3.633480000** | 23 |
| 2007-10-23 | 07:00–17:30 | 26 | **−2.844576923** | 22 |
| **Total** | **137 replacement HH** | **151 original QC0 anchors left untouched** | six separate daily means | **137** |

These means are computed directly from the user-uploaded original 288-HH report (`TA_F` and `TA_ERA` both shown with 0.001°C precision). All source values must be SHA-verified and the six computed daily means cross-checked again on IRIDIS6 before any candidate write. **No blanket whole-day ERA overwrite.**

### Example new TA_F (°C) from daily arithmetic means

| Day | 06:30 / 07:00 new TA | Noon new TA | 17:30 new TA |
| --- | ---: | ---: | ---: |
| Oct 15 | **15.186** | **24.016** | **23.086** |
| Oct 16 | **17.838** | **24.320** | **23.804** |
| Oct 17 | **17.587** | **24.895** | **24.061** |
| Oct 18 | **18.971** | **27.003** | **25.914** |
| Oct 22 | **19.273** | **23.909** | **22.146** |
| Oct 23 | **19.170** (07:00) | **25.685** | **26.456** |

Check the critical newly repaired boundaries against the original untouched QC0 flanks: **all six** source-derived new start and end transitions are **<2°C**, verified by the science script before writing. For each of the 137 new `TA_F` values, the new trial `TA_F_QC=2`; recompute `VPD_F = e_s(T_{new})*(1-RH_{Stage14}/100)` from retained Stage14 RH and set `VPD_F_QC=2` to flag ERA-origin computed humidity physics. **RH is NOT changed.** The old original `TA_F_MDS` and its metadata remain unchanged as the original product lineage. This is a **research trial** not official original-source recoding.

For these 137 targets original `VPD_F_QC` is QC2 at **97 HH** and QC1 at **40 HH**, with **no QC0 VPD overwritten**. Expected independent full-CSV comparison from the previous 3-point research trial is **137 modified HH; 451 changed field cells** (every new HH changes `TA_F,TA_F_QC,VPD_F`, and the 40 original VPD QC1 become new trial VPD QC2). The original source data, previous 3-point research trial, existing original eight tower-temperature source science holds and US-Syv 606+10 deferred events are retained.

## Execute (IRIDIS6, a single separate research candidate)

[Source- and parent-trial-pinned executable script](../scripts/manual_review/apply_sp1_six_oct2007_daily_era_offset_research_candidate.py), commit **`e0694f481a5f5950343851bbc552bf32179f36d3`**.

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="e0694f481a5f5950343851bbc552bf32179f36d3"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  mkdir -p "$BASE"
  SCRIPT="$BASE/apply_sp1_six_oct2007_daily_era_offset_research_candidate.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/apply_sp1_six_oct2007_daily_era_offset_research_candidate.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --apply 2>&1 | tee "$BASE/SP1_six_day_137_HH_manual_trial.log"
)
```

`--apply` rechecks all exact six-day original local-standard 48-HH sources, six user-selected baseline means, original `368208`-row release SHA, parent full-source **US-SP1 research trial SHA `96d8c6ad2a082bb243160ee91c2aee0d2fcd3dc0a862515519c34dab2fa664d3`** and **US-SRG parent SHA `d65523022718819d7013d79f1015fe419958078a8d1fde4f062fa8470929933f`**. All 137 site-specific candidate RH values must be physically valid, and all twelve abnormal start/end corrected temperature transition gaps must be less than 2°C. Then `--apply` creates a **new, uniquely named research-only directory** holding one full modified US-SP1 CSV, a 10-site manifest reusing other nine unchanged entries including US-SRG's previous single-point repair, 137-HH provenance TSV, metadata receipt and **full side-by-side 368208-row verification**. It stops instead of silently emitting unchecked results if any contract fails.

**Critical status:** script committed to GitHub, **NOT yet executed on IRIDIS6** in available logs. No assertion that a new 137-HH repair file exists. The user has requested applying the alternative; the execution must be run on IRIDIS6 because the files live under `/iridisfs`. No Post-v5/DATM/CIME/Slurm/CLM-FATES spinup approval and no original source edits.

## Scientific caveat

Using same-day bias from normal tower periods significantly reduces discontinuities and retains site-specific offsets, but does **not** prove processed `TA_ERA` reproduces unobserved local microclimate during excluded daytime hours. Preserve alternatives and provenance; compare independent site BASE/neighbor towers for source-side evidence before using the series in formal spinup/flux evaluation. Do not retrospectively mark native QC0 source values as physically impossible without supporting observation evidence.
