# Claude handoff — US-Me6, AmeriFlux Batch03

**Assignment as of 2026-10-29:** Claude is requested to take over the difficult *remaining* US-Me6 humidity/temperature source evidence, after completing its US-MtB independent workstream. This is a **handoff document**, not an automatic transmission to Claude. **US-NR3 is reserved for a separate advanced model; US-NR1 is Claude's second new site; ChatGPT/operator handles US-Mpj.** No other site should be changed.

## The exact existing station, no fresh start

- Source release: `AMF_US-Me6_FLUXNET_2010-2025_v1.3_r1`, 2010–2025, **280320 NOLEAP native 30-minute model rows**; exact original primary FLUXMET and paired companion ERA are in the *signed Stage07 manifest*, not guessed path names.
- Verified last signed research-shadow missing count **45 VPD_USE/QBOT halfhours**, comprising **19 exact winter 2014-12-31 23:30–2015-01-01 08:30** cold episode and **26 other distinct source holds**. Not 45 independent invalid tower QC0 observations and not necessarily 45 whole missing meteorological time rows. Preserve every prior explicit approved amendment.
- Signed Stage13S actual user-approved 2015 source QC1 repairs: **12 of 18 complete source runs; 235 source-native HH; 214 new paired VPD/QBOT numeric changes; 18 former NaNs corrected**. Preserve exactly; do not globally override 2015 source QC1. Source-only Stage12AC original July 2017 five HH, Stage13AA, 13AD, 13AF, 13AI approved derivative chain also preserved. Exact latest recommended source shadow/Stage13AI must be selected by original SHA and actual operator report, not narrative.
- There are six long and/or awkward held runs: old Stage13U 782 native QC1 source HH audited; 768 old paired ERA-RH physical pass but 14 fail because tower/ERA T discrepancy >8°C; 2017 four long QC1 runs meet **original source VPD QC2 on both directly neighbouring boundaries** and may cause >4 hPa transitions. This wider 782HH source scope is **not identical** to latest 45 missing forcing HH. No blind repair of 761 unapproved QC1 neighbours.

## Prior science is extensive; DO NOT repeat the same calibration sweeps

2014-12-31 23:30–2015-01-01 08:30 **19 halfhours**: source original VPD_F QC2 equals paired companion VPD_ERA, but at −16 to −18°C selected tower temperature exceeds liquid-water saturation -> impossible negative implied e. Original left 2014-12-31 23:00 T QC2 = −7.538°C, new left first −17.295°C T QC1 (−9.757°C/30min), no true dual T/VPD QC0 analogue pairs at that left transition. Right 2015-01-01 08:30 T=−16.630°C to 09:00 T=−13.870°C both QC0, but right VPD QC2 ERA-derived. Existing ERA-RH correction hypothesis 19HH VPD ≈0.329–0.406 hPa, QBOT ≈0.000766–0.000876 kg/kg, physics may pass; not true measured RH. Right border calibrated hypothesis would change actual vapour e by +0.367398 hPa. Original source measured QC0 strict 11 analogue pairs/11 dates/8 years gave superficially favourable bounds, yet broader independent whole-day/year tests were not robust: **moderate date-weighted percentile 96.15%, year-weighted percentile 100%, 13/13 leave-year-out checks outside**; broad and temperature-only also unsupportive. **NO 19-hour candidate approved to overwrite even the research shadow.** Stage13AR actual signed report at `reports/stage13ar_Me6_right_QC0_day_year_clock_source_READONLY_20261029T024720Z_1bbd4fcf`. Do not repeat post-hoc search for favourable tuning thresholds.

Other **26** current missing HH are distinct source/event classes. Keep separate original QC1 long runs, 2015 Nov and 2017 QC2-outer events; don't assume the 19HH method is transferable. Baseline source `TA_F_QC`, `VPD_F_QC` QC0=measured, QC1=gapfill, QC2=ERA-downscaled; QC2 VPD is not independent tower humidity.

## Assigned work with clear finite scope

1. **Reconcile actual current 45** selected missing timestamps from latest signed shadow and map them to original raw source/QC and parent provenance. Verify that 19+26 exact partition remains correct. Check all full-site non-humidity variables, source native timestamps, PSRF and data dependency only as needed.
2. **Focus on genuinely new evidence** not additional reanalysis tuning: site BIF UTC−8, sensor height and the available original AMF BASE/BADM real RH/TA sensor channels, and if necessary near-site independent measurement. ERA5-Land T2m/D2m/SP and FLUXNET companion ERA are ERA-linked, not independent tower truth. If no independent 19HH humidity evidence, retain HOLD in scientific version. Any isolated numeric sensitivity must explicitly be low confidence and separate from accepted-source state.
3. **Batch adjudicate remaining 26** with signed original source context, quality and physical consistency (water/ice saturation, VPD/QBOT, adjacent real QC0 e/deltaVPD), not arbitrary centre-only interpolation; classify each original episode as MEASURED_SUPPORTED, ERA_RH_SENSITIVITY_ONLY, PHYSICS_CONFLICT_HOLD, EVIDENCE_INSUFFICIENT_HOLD. Compute counts per class and exactly what evidence would change remaining decision.
4. **Audit source-time/PFT model-readiness** only after genuine humidity science, no automatic Post-v5/DATM/AD400/Slurm.

## Handoff pointers and paths

Experiment root `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03`.
- Signed source manifest `qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json`.
- [US-Me6 actual full manual 19HH and 45HH source disposition](MANUAL_HOLD_TRIAGE_AND_TEN_SITE_STATUS_20261029.md).
- [Actual source 2015 complete QC1 runs / 2017 four QC2 boundaries](STAGE13U_ME6_SIX_REMAINING_QC1_HOLD_EPISODES_BATCH_SOURCE_TRIAGE_READONLY_20261027.md), [physical 14 holds](STAGE13W_ME6_FOURTEEN_PHYSICAL_HOLDS_2017_QC2_BATCH_EVIDENCE_20261027.md).
- [Stage13S original 235HH operator-approved shadow](STAGE13S_ME6_USER_APPROVED_TWELVE_2015_QC1_RUNS_235HH_MOBILE_20261027.md).
- [Stage13AR original QC0 actual independent source/year tests](../scripts/stage13/13ar_Me6_QC0_paired_day_year_native_clock_robustness_READONLY.py).
- [Original US-MtB Claude high-level lessons](US_MTB_CLAUDE_HANDBACK_20261029.md) — but do not transplant methods from a mountain station across distinct climate and sensors.

**Deliver exactly:** one current 45-row event ledger (19 vs 26), direct original source + optional BASE/BADM independent evidence, ONE classed human decision matrix, uncertainty and exact proposed separately versioned source approaches. **Do not create another open-ended Stage13AX chain**, silently change source QC0, or use a fitted donor result as validation truth. Any data output is research-only unless user separately authorizes release.
