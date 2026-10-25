# AmeriFlux Batch04 — US-SP1 six Oct-2007 day-specific ERA residual temperature corrections, verified

**Status 2026-10-25: OPERATOR EXECUTED; SIX DAYS 137 NATIVE HALF-HOUR TRIAL REPLACEMENTS CREATED; ROW-BY-ROW 368,208-ROW SELF-AUDIT PASS. NO ADDITIONAL MANUAL REVIEW OF THIS SIX-DAY ALTERNATIVE NECESSARY.** Existing FLUXNET, Stage14, Stage15, prior three-point trial and model inputs were not rewritten. This user-approved research alternative is **not** an official AmeriFlux observation correction, nor a Post-v5/CLM-FATES production approval.

## Final exact IRIDIS6 trial artifact

```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_sp1_six_day_bias_adjusted_research_not_approved/candidate_20261025T231828Z_ed7de7ac
```

**US-SP1 entire final candidate CSV SHA256:**

```text
357a0c89892365e41e1b932663953fcff33487a2cbf6171ba3b9347b7482a9b0
```

This output **extends** the already full-CSV-verified previous three-point case: original US-SP1 October 2000 **2-HH independently ERA5-Land-sourced trial** retained unchanged, and the other **US-SRG 2019-03-19 12:00** one-HH ERA-flank interpolation remains unchanged in the 10-site research manifest. The earlier parent site CSV SHA `96d8c6ad2a082bb243160ee91c2aee0d2fcd3dc0a862515519c34dab2fa664d3` remains intact.

## Exact six manual daily rules and observed boundary checks

For each calendar day the researcher defined abnormal `TA_F` periods and computed the **mean original QC0 `TA_F - TA_ERA` of all other same-day normal half-hours**, using original FLUXNET processed `TA_ERA` (NOT independent ERA5-Land T2m). In each invalid HH, `TA_F_trial=TA_ERA_native+that day's mean` and `TA_F_QC_trial=2` (ERA-derived experimental provenance).

| Day Oct 2007 | Replaced local-standard HH | Valid same-day original QC0 calibrators | Same-day mean tower−ERA °C | Number of replacements | Onset discontinuity after trial °C | 18:00 transition °C |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 15 | 06:30–17:30 | 25 | −2.832680000 | 23 | +0.6363 | +0.1337 |
| 16 | 06:30–17:30 | 25 | −2.472120000 | 23 | +0.2279 | −0.5839 |
| 17 | 06:30–17:30 | 25 | −2.251880000 | 23 | −0.3629 | −0.3511 |
| 18 | 06:30–17:30 | 25 | −1.555640000 | 23 | +0.9914 | +0.3256 |
| 22 | 06:30–17:30 | 25 | −3.633480000 | 23 | +1.5625 | +1.2445 |
| 23 | 07:00–17:30 | 26 | −2.844576923 | 22 | −0.0796 | −0.8864 |
| **Total** | | **151** | Six distinct daily calibrations | **137** | **all absolute differences <2°C** | **all <2°C** |

The pre-run source verification confirms original `368208` rows and SHA `d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963`; exactly **288 source HH (six complete days) and 137 target HH**.

### Conservative source humidity lineage

The `RH` column is the **Stage14 parent candidate**. Existing Stage14 VPD-only source corrections were retained, not replaced by older original FLUXMET invalid humidity. Three cases per target: existing finite 0–100% RH, missing RH with physically valid parent VPD, or (hard-stop) invalid RH/VPD. The observed result split:

| Target subset | Count | Result |
| --- | ---: | --- |
| Valid Stage14 RH | **40** | Recalculate VPD for new trial TA, preserve source RH |
| Missing Stage14 RH but retained VPD physically valid | **97** | **Leave parent VPD and its QC unchanged**; do not invent RH |
| Original FLUXMET target VPD QC1 | **40** | Source audit provenance; candidate 0 QC1→QC2 because parent Stage14 VPD-only updates already carry QC2 |
| New TA values and TA provenance changes | **137 each** | `TA_F` and `TA_F_QC` changed |

Thus changed **field-cell count = 137 TA_F + 137 TA_F_QC + 40 VPD_F = 314**; **no VPD_F_QC fields changed in this v3 trial**. This matches the returned full-file audit.

## Source-verified operator terminal receipt

```text
SP1 DAILY ERA OFFSET SELF TEST PASS: six exact days, source anchors, 137 HH, no source overwrite
ORIGINAL SIX DAY SOURCE SHA VERIFIED d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963 all_rows 368208 original_HH_288 new_targets 137 target_original_VPD_QC1 40
REPAIR PLAN PASSED 137 new_halfhours source_QC1_VPD 40 VPD_recomputed_from_valid_RH 40 VPD_original_retained_when_RH_missing 97 VPD_QC1_to_QC2_only_if_recomputed 0
HUMIDITY PHYSICS: ALL 137 VPD NONNEGATIVE AND <= SATURATION AT NEW TA
INDEPENDENT FULL AUDIT PASS all_rows 368208 new_HH 137 modified_field_cells 314 original_2000_SP1_prior_2HH_unchanged True
SIX-DAY RESEARCH CANDIDATE CREATED AND INDEPENDENTLY AUDITED /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_sp1_six_day_bias_adjusted_research_not_approved/candidate_20261025T231828Z_ed7de7ac
US-SP1 NEW FULL CSV SHA256 357a0c89892365e41e1b932663953fcff33487a2cbf6171ba3b9347b7482a9b0
SIX DAYS 6 NEW HH 137 CHANGED FIELD CELLS 314
OTHER NINE SITE MANIFEST SOURCES UNCHANGED INCLUDING US-SRG 2019 MANUAL TRIAL
NO ORIGINAL/STAGE14/STAGE15/PREVIOUS THREE-POINT TRIAL WRITES
SCIENCE 8 T SOURCE HOLDS PLUS US-Syv 606+10 REMAIN; NO Post-v5 DATM CIME SLURM SPINUP RELEASE
```

### What is still awaiting scientific decisions?

**For this six-day Oct 2007 manual research alternative: no more local/manual observation scrutiny is required before treating the *candidate file* as technically audited.** The researcher supplied the intended daily-offset rule and verified exact output. The original official eight temperature science HOLDs are still present, even though *separate reproducible research alternatives* now address four original source episode locations: US-SP1 Oct 2000 two HH, US-SRG Mar 2019 one HH and US-SP1 Oct 2007 six intervals (covering Oct 15 17:30). Remaining **four original HOLD timestamps without these selected temperature alternatives**: US-SP1 **2008-01-16 08:00, 08:30; 2008-02-03 08:00** and US-Seg **2016-12-27 18:00**. These need **independent separate judgments**: Jan/Feb 2008 source TA is long smooth nocturnal cold relative to ERA rather than a few isolated time jumps, and the US-Seg 2016 overnight cooling persisted many hours. Avoid automatically applying the Oct 2007 daytime 06:30–17:30 correction heuristic to distinct 2008 or US-Seg evidence.

Original **US-Syv 606 inherited science holds + 10 missing ERA edges** remain separately deferred. The ten-site research manifest is not production DATM/CIME or a running spinup. Use scientific approval/release gates separately from file-integrity checks.

[RH-safe v3 source code](../scripts/manual_review/apply_sp1_six_oct2007_daily_era_offset_rh_safe_v3.py) (pinned execution commit `4ca2346496cd166ba5805f5f9b381eebf3dd22f4`). [Three-point earlier fully verified research alternative](MANUAL_THREE_T_FULL_SOURCE_AUDIT_VERIFIED_2026-10-25.md).
