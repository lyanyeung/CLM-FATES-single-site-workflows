# US-Syv — user-directed six ERA5-origin temperature intervals, 106 HH — execution and residual manual review

**User's explicit decision 2026-10-26:** "US-Syv这从2017-02-10/11， 2007-02-11/12， 17:30到7:00全部用ERA5代替。2003-04-27从11:30到19:30也全部用ERA5代替。另外三段也全部用ERA5代替，不需要提取了。然后告诉我别的需要人工审核的地方。"

**Interpretation strictly grounded in preceding US-Syv source audit:** The written **2017-02-10/11** is taken as **2007-02-10/11** because the six source-verified episodes being discussed were in February **2007** and April **2003**, not 2017. Both overnight 17:30-to-07:00 user instructions apply. The **Feb11 17:30→Feb12 07:00** interval is **28 HH**, which adds **8 new half-hours after Feb12 03:00** relative to the earlier 20-HH original Stage05 HOLD span. No 2017 or unspecified extra days added.

## Operator-authorized exact native local-standard-time windows

| Interval | Start | End, inclusive | HH |
| --- | --- | --- | ---: |
| Feb08 evening | 2007-02-08 17:30 | 2007-02-08 21:30 | 9 |
| Feb09 evening | 2007-02-09 17:30 | 2007-02-09 23:30 | 13 |
| Feb10 night | 2007-02-10 17:30 | 2007-02-11 07:00 | 28 |
| Feb11 night | 2007-02-11 17:30 | 2007-02-12 07:00 | 28 |
| Feb12 evening | 2007-02-12 17:30 | 2007-02-12 22:30 | 11 |
| Apr27 daytime | 2003-04-27 11:30 | 2003-04-27 19:30 | 17 |
| **Exact disjoint authorized total** | | | **106** |

**Temperature equation explicitly directed by the operator:** `TA_F_trial(t)=FLUXNET_packaged_TA_ERA(t)` at the **identical native half-hour timestamp** and `TA_F_QC_trial=2`. **No per-day calibration bias** in Syv, unlike the independent previously approved six-day US-SP1 Oct2007 137-HH decision. `TA_ERA` is the *processed packaged FLUXNET ERA5-derived* series and **is not separately downloaded independent ERA5-Land T2m**; preserve this provenance on every candidate sample.

**Input protection:** SHA-verified original AmeriFlux Syv 438288-HH full release, original paired ERA5 same-time source, Stage05+Stage07 source receipts, existing Stage07 Syv candidate SHA `5086cbc0f08f73b218d08fdcf34cf0643a6ae1ea95c05c200a98800452b5b32e`. The separate parent ten-site research manifest comes from previously **operator-PASS US-SP1 137-HH alternative**, with US-SP1 final full SHA `357a0c89892365e41e1b932663953fcff33487a2cbf6171ba3b9347b7482a9b0`, preserving all prior SP1/US-SRG/other sites unchanged.

**Humidity physics handling at those authorized T replacements:** Prefer packaged same-native `VPD_ERA` only when `0≤VPD_ERA≤es(TA_ERA)`; set trial VPD QC2 and compute new `RH=100(1−VPD/es(newT))`. If unusable, keep valid Stage07 VPD at new T and derive RH. If **both** VPD sources fail saturation, apply the *approved* T replacement, **do not fabricate VPD/RH**; preserve them and flag `HUMIDITY_UNRESOLVED` for later science review. QC0/1/2 original provenance is preserved in a per-HH ledger, the candidate has ERA-derived T QC2. This is a scientific **research alternative**, not a recoding of the official tower archive.

## IRIDIS6 execution — exact GitHub revision

[SHA/provenance-pinned full source repair script](../scripts/manual_review/apply_US_Syv_six_operator_ERA_temperature_intervals_106HH_research_trial.py), GitHub commit **`110b32f3aac32c359c3b966e5c91b6605820a291`**.

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="110b32f3aac32c359c3b966e5c91b6605820a291"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  mkdir -p "$BASE"
  SCRIPT="$BASE/apply_US_Syv_six_operator_ERA_temperature_intervals_106HH_research_trial.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/apply_US_Syv_six_operator_ERA_temperature_intervals_106HH_research_trial.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --apply 2>&1 | tee "$BASE/US_Syv_106HH_ERA_T_apply.log"
)
```

Preflight ensures **all 106 exact time keys and valid ERA temperature**, outputs sample old/source/ERA pairs, counts original QC0/1/2, compares original source SHA and parent derived SHA, classifies candidate VPD physical status, and lists **up to 20 longest other contiguous original site-T-vs-ERA HOLD episodes** for user to review next. Only after preflight does `--apply` write a **brand-new immutable 438288-HH US-Syv trial CSV**, an updated research ten-site selected input manifest (same exact 9 other paths/SHAs), new 106-row source/ERA/QC/humidity provenance TSV and full 438288-row side-by-side audit, SHA256 receipts and humidity-hold list. No prior original, Stage14/Stage07, SP1/SRG research parent or model inputs changed.

**Execution status: code committed to GitHub, NOT YET run on IRIDIS6 in current conversation.** Successful completion requires terminal lines `OPERATOR ERA TEMPERATURE REPLACEMENT PREFLIGHT PASS exact_106_HH`, `INDEPENDENT FULL FILE SOURCE AUDIT PASS` and `US-SYV SIX INTERVALS SCIENCE CANDIDATE CREATED & VERIFIED`. Only the operator's result can establish the final SHA, humidity treatment counts, and remaining science invalid events.

## What else needs operator judgement after these 106 HH?

Before this selected intervention, original [verified Syv triage](US_SYV_616_UNIQUE_HOLDS_86_EPISODES_PRIORITY_MANUAL_DECISIONS_2026-10-26.md) found **616 distinct historical HOLD HH** (606 inherited +10 separate source ERA failures; zero overlap), **598 VPD saturation failures** and **86 contiguous episodes**. Six historical anomalous source intervals contributed **98 old HOLD timestamps**; the newly extended Feb11–12 period adds **8 more time stamps outside the old HOLD**. Therefore a preliminary **518 old HOLD unique time stamps** remain outside the six operator-directed temperature replacements, subject to the program's source list proof on IRIDIS6. Do not say 518 are all unrepairable. These 518 may be split between:

1. **Other temperature-discrepancy source HOLD episodes**, originally 183 HH of reason `SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID`, of which 98 old source HOLD HH are in the six addressed intervals. There may be **85 old T-source discrepancy HH** outside the six selected ranges (verify exact category/timestamp intersection in operator output). These require source-specific judgement about *retaining* or replacing original TA. Examples of other known episodes include **2003-05-08 11:30–14:00 (6 HH), 2002-05-22 19:30→May23 00:30 (11 HH), 2008-04-04 18:30–20:30 (5 HH), 2001-11-01 20:00–23:30 (8 HH)**; do not auto-apply a six-range correction to them.
2. **Humidity-source physical failures**, mostly low-temperature grid or observation near-continuity where original T tracks packaged `TA_ERA`. Examples source-verified: 2007-02-03→05 **85 HH**, 2019-01-30→31 **43 HH**, 2008-02-10 **27 HH**, 2004-01-28→29 **23 HH**. Original/Stage07 VPD exceeds `e_s(T)`. These need physically validated **VPD/RH-only** repair from reliable independent ERA5-Land dew point/RH, or independently verified paired-ERA humidity fraction; **do not blindly copy packaged `VPD_ERA`** when it also exceeds saturation.
3. **18 originally physics-valid historical HOLDs**. Not every one is necessarily outside the selected 106; exact overlap and historical reasons must be evaluated before science signoff. Preserving legacy HOLD provenance does not prevent documenting separately approved treatment.

**Do not mark any of these outstanding science gates as passed until the new candidate is actually generated and independently audited.** US-SP1 2008 retain original TA, US-Seg provisional retain T/Stage14 VPD, US-SP1/US-SRG earlier trial alternatives remain valid independently. No Post-v5/DATM/CIME/Slurm/spinup release.
