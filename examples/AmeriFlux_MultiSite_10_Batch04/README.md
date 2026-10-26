# AmeriFlux MultiSite 10 — Batch 04

> **Operational status (2026-10-25): Stage00–02/C structural/native time checks 10/10 PASS; Stage07–11 ten SHA-verified research candidate sources; Stage12 non-Syv 148/156 targeted events resolved; Stage14 eight humidity-only numerical closures keeping original tower T; Stage15 two-point US-SP1 T sensitivity alternative executed; Stage16 VERIFIED PASS (368208 HH, two trial rows/three columns only); Stage17–19 VERIFIED PASS 6/6 each; Stage20 VERIFIED PASS 3/3 original BIF inventories; Stage21 **IRIDIS6 OPERATOR VERIFIED PASS: 3/3 original FLUXNET releases, 48/48 original CSV file headers inventoried, zero separately named sensor-level TA channel candidates identified**. **INTERNAL-ONLY T-QC SOURCE-AVAILABILITY ESCALATION CLOSED: request original site records / inspect distinct AmeriFlux BASE with independent provenance before further science decisions.** All **8/8 original QC0 T scientific HOLDs** remain; US-Syv **606 inherited HOLDs + 10 skipped Stage07 ERA edges** remain deferred. **Operator manual 3-point replacement `--assess` VERIFIED PASS (two US-SP1 exact ERA5-Land values and one US-SRG QC2-flank interpolation), `--trial` RUN SUCCESS (research-only candidate created, full-file independent read-only audit VERIFIED (2/2 entire site CSV, 3/3 HH, exactly 9 fields, SHA/RH/QC2/8-other-site manifest PASS)).** **US-SP1 original all-year 18:00 clock-step audit VERIFIED: 6 Oct 2007 dates in 2 clusters; US-SP2/US-SP3 adjacent tower BASE proposed for independent evidence.** **Operator requested six additional Oct 2007 day-interval replacements: daily healthy QC0 mean ERA residuals calculated for 137 HH; v1 RH stop superseded; RH-safe v3 `--apply` OPERATOR VERIFIED PASS: 137 HH, 314 cells, 40 rederived/97 VPD retained, SP1 full CSV SHA256 357a0c89892365e41e1b932663953fcff33487a2cbf6171ba3b9347b7482a9b0.** **NO approved Post-v5/DATM/CIME/Slurm/CLM-FATES spinup forcing**. See [Stage21 verified source inventory](docs/STAGE21_VERIFIED_ORIGINAL_TEMPERATURE_SOURCE_COVERAGE_2026-10-25.md) and [site contacts and drafted source requests](docs/STAGE21_SITE_OPERATOR_TEMPERATURE_REQUESTS_2026-10-25.md).

## SYVH3 OPERATOR VERIFIED: US-Syv 616 legacy science-HOLD treatments documented; ten-site input QA NEXT (2026-10-26)

**Latest actual operator-run US-Syv scientific research candidate is complete**: full 438,288 native HH, **297 ERA-source temperature substitutions** preserved, **415 independently ERA5-Land derived humidity repairs** preserved, **18 source-QC0 T and VPD retained with derived RH recomputed**, independent full source diff PASS. The one 2008-03-09 13:00 VPD excess of **0.0000232hPa** is smaller than native three-decimal source VPD precision (no value clipped). **Final derived Syv SHA256 `9299193bc12b06e37211d84d31c333e299f99cb0ed96ebc6ed224ef9eaaf02aa`**, parent directory `manual_US_Syv_stage_SYVH3_last_18_QC0_RH_closure_candidate_not_approved/candidate_20261026T034556Z_3372d66c`. Earlier SYVH1/SYVH2 **READY** notes below are historical steps, not current unresolved Syv science tasks. Original historical holds are preserved for provenance; candidate-only numerical treatments are complete.

**NEXT: Batch04 exact ten-site selected forcing SHA/physical QA, no model jobs.** [Final full ten-site selected manifest read-only audit](scripts/manual_review/stage_syvh4_final_ten_site_manifest_readonly_gate.py) pinned revision `5f58e37be6026e9db647d78e7df95bdac8acd361`. Checks all ten complete full-site FLUXMET files selected by the actual final SYVH3 `RESEARCH_TEN_SITE_MANIFEST.tsv`, each SHA, half-hour time coverage, VPD saturation, RH closure, source QA and non-Syv unchanged references. [Operator output and one-command next step](docs/US_SYV_SYVH3_OPERATOR_PASS_FINAL_AND_TEN_SITE_QA_2026-10-26.md). **Script published; not yet run on IRIDIS6.** Prior historical README states about eight non-Syv source-T science holds refer to earlier research stages and must be reconciled with subsequent operator approvals; do not silently mark those sites production-ready. **Post-v5 / DATM / CIME / Slurm / spinup not yet authorised.**

## SYVH2 VERIFIED: US-Syv 415 independent ERA5-Land VPD corrections PASS, final 18 QC0 RH-only reconciliations READY (2026-10-26)

Operator-run newest full US-Syv source candidate **438288 HH**, **SHA256 `265d92fc7d3cc8c3d3dff6b93067d9fc380969131ab044c08bd192c1ceb9b1cc`**; all **11** applicable independent ERA5-Land yearly receipts SHA checked, **415 original physically invalid source VPD corrected**, 297 previously user-approved T replacements preserved, all other nine site source selections unchanged. Actual final 18 historical source ERA grid-humidity HOLD HH in 2021 have `TA_F_QC=0`, `VPD_F_QC=0`, valid native T/VPD but **derived RH not physically closed** (by 0.787–1.497 RH percentage points). A separate global T/VPD screen flagged exactly **one VPD=3.842hPa at T=−6.234°C on 2008-03-09 13:00**, only **0.0000232hPa** above `es_water`, well within native three-decimal VPD input quantization. Do **not** replace/cap raw VPD for this rounding-only discrepancy.

**New research-only Stage SYVH3**, committed but **not yet run**: [last 18 original QC0 source RH-only closure, one rounding exception and independent complete source audit](scripts/manual_review/stage_syvh3_close_18_qc0_vpd_valid_derived_rh_and_rounding_audit.py), revision `51acbc12de6b741f879c7bd91165893997fcaf27`. It may modify **only 18 derived RH fields**, retains native VPD/T/QC and all old science source-HOLD provenance, produces a complete 438288-HH new research candidate and an exact ten-site selection manifest. [Operator science evidence and one-command execution](docs/US_SYV_SYVH2_415_FIXED_18_QC0_RH_CLOSURE_AND_1_ROUNDING_NEXT_2026-10-26.md). No further Syv user manual science decision is needed for these exact 18 as long as source/closure assertions pass. **Post-v5, DATM, CIME, Slurm and spinup remain pending independent all-ten-site input QA.**


## USER APPROVED US-Syv six direct-ERA temperature intervals: 106 native HH — research script READY (2026-10-26)

**New operator decision supersedes six-episode source-T review request:** Directly replace candidate `TA_F` with same-native **FLUXNET packaged `TA_ERA`** (ERA5-derived) and mark candidate `TA_F_QC=2` on six explicitly approved native-local-standard-time intervals: **2007-Feb08 17:30–21:30 (9 HH), Feb09 17:30–23:30 (13), Feb10 17:30→Feb11 07:00 (28), Feb11 17:30→Feb12 07:00 (28), Feb12 17:30–22:30 (11), and 2003-Apr27 11:30–19:30 (17)**. **Exactly 106 authorized HH**. The user's written **2017-Feb10/11** means **2007-Feb10/11** from preceding exact source history. Feb11→Feb12 07:00 is **eight hours? No: eight native half-hours (4h)** beyond the original Feb12 03:00 scientific-HOLD endpoint; the user expressly extended the two overnight intervals to 07:00. **No per-day offset correction is used**, in contrast to previously approved SP1 Oct2007.

The [source-SHA and model-manifest-guarded direct application](scripts/manual_review/apply_US_Syv_six_operator_ERA_temperature_intervals_106HH_research_trial.py), commit `110b32f3aac32c359c3b966e5c91b6605820a291`, produces a new **complete 438288-HH US-Syv trial candidate** and a 10-site research manifest retaining prior operator-audited US-SP1 137-HH/2000 two-HH and US-SRG one-HH candidates. Uses FLUXNET processed packaged ERA **not independently downloaded ERA5-Land**. For the selected T replacements only, physically safe paired `VPD_ERA` is preferred and tested against saturation at new T, otherwise valid previous Stage07 VPD, otherwise humidity stays explicit HOLD without inventing replacement. Every actual changed native time is checked in a complete parent-versus-candidate audit. No previous source or model writes.

**Script and detailed execution/remainder science checklist:** [User-authorized Syv 106-HH repair document](docs/US_SYV_USER_APPROVED_SIX_ERA_T_INTERVALS_106HH_EXECUTION_2026-10-26.md). **Code committed, not yet run on IRIDIS6; no verified new 106-HH output SHA at this time.** After the operator's `--apply`, print actual remaining source `SITE_ERA_TA_DIFFERENCE` and VPD physical HOLDs. Based on prior 616 verified unique HOLDs and 98 original selected HOLD times, **518 old HOLD HH remain outside the six approved T replacement windows** (plus any humidity-only failures newly selected); do not silently mark them repaired. Other example T episodes 2003-May08/2002-May22–23/2008-Apr04 need individual science evidence, while 2007-Feb03–05/2019-Jan30–31/2008-Feb10 mostly require humidity physics, not T substitution. **Post-v5/DATM/CIME/Slurm/spinup remains blocked** until additional science gate.

## US-Syv HUMAN T DECISION DATA: exact tower TA/QC and processed ERA before, during and after six episodes — code READY (2026-10-26)

**User explicitly requires NUMERIC BEFORE/AFTER native halfhour temperature pairs before any science approval.** The read-only [six-episode detailed evidence extractor](scripts/manual_review/show_US_Syv_six_T_suspect_episodes_full_flanks_readonly.py), commit `99490b05f86ac320ab8db51522dc188fc4f854cb`, pins original Stage05 source SHA, Stage07 complete 438,288-HH Syv candidate SHA, and matched source-packaged FLUXNET ERA. It prints all **98 original science HOLD halfhours** in **2007 Feb08/09/10–11/11–12/12 and 2003 Apr27** together with **±2h original/ERA/QC context**. It ALSO outputs the **entire 336 HH for 2007 Feb08–13 (6 days) and 2003 Apr27 (1 day)** so the user can see where abnormal QC1 low plateaux actually end (a HOLD endpoint is not necessarily a plateau endpoint). **QC1=gap-filled consolidated TA, QC2=ERA-filled, QC0=original tower data**. `TA_ERA` is processed FLUXNET ERA5-derived temperature, **not independently retrieved ERA5-Land**; all claims labelled appropriately. `--report` writes only two new CSV evidence reports under the user's HOME and prints everything via a log. [Exact existing source numerical table, distinctions and run command](docs/US_SYV_SIX_EPISODES_HUMAN_REVIEW_TOWER_VS_ERA_FULL_FLANKS_2026-10-26.md). **Not yet run on IRIDIS6; no Syv fixes approved**, prior 598 VPD-invalid/18 physics-valid science holds and 86 contiguous episodes remain.

## USER MANUAL DECISION: US-SP1 JAN/FEB 2008 KEEP ORIGINAL TA_F — US-Syv remains the only untriaged original science-HOLD site (2026-10-26)

**Explicit user decision after reviewing native Jan/Feb 2008 tower-versus-ERA panels: `这里都应该使用TA_F`.** Apply this to **US-SP1 all original Jan 15–17 and Feb 2–4 2008** tower temperature values, including original science focal times `200801160800`, `200801160830`, `200802030800`: **KEEP `TA_F`, keep the original temperature QC0 provenance and do not replace with ERA5/ERA5-Land or fit a bias correction.** For the three previously Stage14 corrected implausible VPD/RH source pairs, keep **existing Stage14 humidity-only derived candidate** numerics; **no new temperature or VPD writes**. Does not revoke previously **operator-verified user-approved** US-SP1 Oct2000 2-HH ERA temperature alternative or Oct2007 137-HH daily-offset research temperature alternative. US-SRG Mar2019 ERA-flank trial also remains as already fully validated.

**US-Seg Dec27 2016 18:00:** provisional retain original cold-trajectory `TA_F=0.015°C/QC0`, Stage14 existing humidity-only closure `VPD_F=2.63121106028` hPa remains unchanged. This is an evidence-based scientific recommendation, not a fabricated separate user sign-off.

**Remaining source-held science work: US-Syv** only, **606 historical Stage05 HOLD entries and 10 Stage07 ERA-edge failures**. Some timestamps may overlap; these are *not yet 616 separate unique records*. The six other Batch04 sites **US-Rpf, US-Ses, US-Slt, US-SRM, US-Ton, US-Uaf** have no additional named temperature conflict among Stage13's eight non-Syv original source exceptions. US-Syv was intentionally deferred when Stage12 repaired **148/156 non-Syv** events; the 8 others are covered by explicit alternative/retain decisions without rewriting original source HOLD history. **Do not infer Post-v5/DATM/spinup approval** or that all US-Syv events are harmless.

**Next one-pass read-only source-based US-Syv priority triage:** [`triage_US_Syv_606_holds_10_skipped_boundaries_readonly.py`](scripts/manual_review/triage_US_Syv_606_holds_10_skipped_boundaries_readonly.py), commit `8fe1d9523fa71781a2c609c309da26183f7be4ed`. It SHA-validates Stage05/Stage06/Stage07 receipts, full original and Stage07 US-Syv **438288 HH** source files, combines/deduplicates **606 + 10**, and groups continuous episodes, source and derived TA/VPD/RH physics, QC and same-time packaged ERA before showing the highest-priority 12 examples. **Script is published, not yet run on IRIDIS6.** It performs **no fixes/writes** beyond an optional operator `tee` log. [Exact operator manual retain decision and per-site remaining gate](docs/OPERATOR_MANUAL_RETAIN_SP1_2008_TA_AND_BATCH04_REMAINING_SITE_GATES_2026-10-26.md).

## Four remaining source-temperature holds REVIEWED — independent airport evidence, 1 SP1 science decision left (2026-10-25)

**Operator read-only review completed** with original SHA-pinned US-SP1 91 Jan HH and 85 Feb HH, US-Seg 39 Dec HH, and all 4 original QC0 focal times. **External independent contemporaneous airport observation adds evidence:** Gainesville Jan16 2008 minimum **+6.67°C** (NWS CF6 44°F), compared to original US-SP1 **−11.144°C**; Gainesville Feb03 2008 minimum **+9.44°C** (49°F), compared to original US-SP1 **−6.588°C**. The discrepancy is extreme and strongly suggests a source sensor/processing problem; airport minimum is a different location/time aggregate and **does not determine exactly what native HH to replace**. Jan15 19:30–Jan16 08:30 and Jan16 15:30–Jan17 13:00 contain 27 and 44 source QC0 HH ≥10°C below processed FLUXNET TA_ERA. Feb2 23:30–Feb3 08:30 contains 19 HH, plus shorter Feb03–04 nocturnal repeats. **Do not apply the unrelated Oct2007 daytime step repair rule** to these overnight series.

**US-Seg 2016-12-27 18:00:** original 0.015°C occurs during a sustained multi-hour freezing trajectory; preserve original T rather than auto-ERA substitution. Its original VPD=7.037 hPa exceeded es(T)≈6.119 hPa, but the already operator-VERIFIED Stage14 candidate uses **2.631211 hPa**, retaining original source T, so **no repeated humidity repair is needed**. This is a provisional scientific retain-T recommendation, not a declaration that original science source HOLDs are erased.

**Only remaining human intervention asked of the researcher now:** choose whether to construct separate, explicitly labelled **US-SP1 Jan/Feb2008 extended episode ERA-derived research substitution candidates**, which require independent interval delineation/healthy site bias validation, or to **keep the original T and hold for site sensor/nearby SP2/SP3 BASE evidence**. No additional numerical-only, source-blind interpolation of the three single SP1 2008 timestamps. [Full four-HOLD source review, NWS January and airport February daily observation evidence, and existing Seg Stage14 VPD result](docs/NEXT_FOUR_T_HOLDS_JAN_FEB2008_INDEPENDENT_WEATHER_AND_SEG_REVIEW_2026-10-25.md).

**Batch04 Stage14, previous three-point manual alternative and 137-HH SP1 Oct2007 research repair already operator-VERIFIED, retain all source SHA/paths and no new writes. Eight original scientific T-HOLD records and US-Syv 606+10 deferred remain; Post-v5/DATM/CIME/Slurm/spinup prohibited until separate approval.**

## NEXT: four remaining original temperature science HOLDs — source review code READY (2026-10-25)

**Do not re-run the already PASS six Oct 2007 days** or overwrite existing SP1 137-HH and prior 3-point independent research candidates. The remaining **four** original T-specific unresolved HH lack user-selected alternatives: **US-SP1 2008-01-16 08:00 and 08:30, 2008-02-03 08:00; US-Seg 2016-12-27 18:00**. These are not the clock-locked 2007 06:30/18:00 jumps; previous full original review showed **multi-hour/overnight** cold relative to processed FLUXNET TA_ERA. They need a different direct tower-T scientific decision; blindly using 2007's daytime offsets on 2008 night-time data is not supported.

For rapid single-run manual review: [`next_four_temperature_holds_science_review_readonly.py`](scripts/manual_review/next_four_temperature_holds_science_review_readonly.py), GitHub pinned commit `d4dae63ad876e298341f7225e1c9245eee5af6f1`, reads original **SHA-pinned** US-SP1/US-Seg full-release FLUXMET sources without changing any files. Prints exact native local-standard 30-minute T, TA_ERA, temperature QC, VPD/QC and marked 4 original QC0 holds; duration/count of **QC0 tower-minus-processed-ERA ≤−10°C** episodes for **SP1 Jan15 17:00–Jan17 14:00, SP1 Feb2 18:00–Feb4 12:00, Seg Dec27 15:00–Dec28 10:00**. This is **source evidence, not an approved automated replacement**. Script is committed to GitHub, not yet executed in returned user logs. Once the operator chooses a treatment, make a **new source-pinned isolated candidate** extending the verified current 10-site manifest, with explicit QC lineage and row-by-row audit. No Post-v5/DATM/CIME/Slurm/spinup release authorised; US-Syv 606+10 remains separate.

## US-SP1 six-day 137-HH manual T correction — OPERATOR EXECUTED & FULL SOURCE AUDIT PASS (2026-10-25)

**NEW OPERATOR VERIFIED COMPLETION (supersedes below's historical v1/v2/v3 READY notes):** Six dates Oct 15–18 and 22–23 were repaired in the independent, SHA-pinned **user-selected** research candidate, **exactly 137/137 HH** with 6 separate same-day QC0 `TA_F−TA_ERA` normal-period means. Original SP1 complete **368,208 rows** verified; independent same-row parent-versus-output check **PASS 137 changed HH and exactly 314 changed field cells** = **137 `TA_F`, 137 `TA_F_QC` and 40 rederived `VPD_F`**, with **97 missing-RH cases retaining original *parent* VPD/QC** and **0 `VPD_F_QC` changes**. Source VPD QC1 count in original FLUXMET was 40 but parent Stage14 had already incorporated VPD-only QC changes. **All six start/end transitions <2°C**, 8 other unrelated sites plus US-SRG parent manifest source unchanged, original/Stage14/Stage15/parent scenario untouched. [Complete verified receipt, exact six mean offsets and scientific scope](docs/SP1_SIX_DAY_137HH_MANUAL_REPAIR_FULL_AUDIT_VERIFIED_2026-10-25.md).

**New SP1 full 368208-HH research CSV SHA256:** `357a0c89892365e41e1b932663953fcff33487a2cbf6171ba3b9347b7482a9b0`. **Final research directory:** `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_sp1_six_day_bias_adjusted_research_not_approved/candidate_20261025T231828Z_ed7de7ac`. **No further human review needed for the user's six Oct2007 day-specific candidate intervention**; original scientific HOLD records remain unchanged (now four distinct unresolved sites/times without any corresponding new intervention: US-SP1 Jan16 08:00/08:30 2008, Feb03 08:00 2008; US-Seg Dec27 18:00 2016). **US-Syv 606+10 deferred. No Post-v5/DATM/CIME/SLURM/spinup approval.**


**Additional fix:** Stage14's existing 2007 `VPD_F` or `VPD_F_QC` may differ from original FLUXMET because previously approved humidity-only research changes were retained in the source-pinned parent. V3 does **not** require VPD to equal the original raw version, and always uses/preserves the SHA-pinned Stage14-derived parent values. **Only measured TA/TA QC/TA_ERA are required to match the original release.** The v2 script is superseded and should not be executed.


**Actual operator run:** all six original 24-hour source days, mean healthy source offsets, original full FLUXMET SHA, 137 target census and 40 original VPD QC1 provenance PASS. The first v1 `--apply` **stopped safely before writing** on **2007-10-15 06:30**, because Stage14 `RH` is missing, preventing the original algorithm from recalculating VPD. **No six-day research CSV produced in this v1 run**; parent already verified three-point trial unchanged.

**Next (v3):** [source-pinned RH-safe replacement script](scripts/manual_review/apply_sp1_six_oct2007_daily_era_offset_rh_safe_v3.py) and [science/operational run note](docs/SP1_SIX_DAY_DAILY_OFFSET_RH_SAFE_V2_AFTER_MISSING_RH_2026-10-25.md), at GitHub commit `4ca2346496cd166ba5805f5f9b381eebf3dd22f4`. **Temperature repair stays the same 137 HH, six original QC0-healthy daily mean residuals, FLUXNET original processed TA_ERA inputs and trial QC2.** With valid retained Stage14 RH, recompute VPD at corrected T and set trial VPD_QC2; **with RH missing, keep existing original QC1/QC2 VPD and QC bytes untouched if original VPD is nonnegative and ≤ saturation at corrected T**. Finite-but-invalid RH or unavailable/physically invalid VPD hard-stop *before a new research candidate is created*. V3 independently checks full 368,208-row modified CSV; total modified field-cell count is **data-dependent 274–548**, **not v1's 451-cell assumption**. **V3 is published but not yet executed** in the provided IRIDIS6 logs. No original/Stage14/Stage15/three-point case edits or model/Post-v5/DATM/CIME/Slurm authorisation.

## Operator-directed US-SP1 Oct 2007 six-day, 137-HH daily ERA-bias correction — research script READY (2026-10-25)

**Operator manually selected temperature repair strategy** after reading full 6×48 original half-hour source observations: within each 2007-10-15/16/17/18/22 day replace original site TA **06:30–17:30** (23 HH/day), and on **2007-10-23 replace 07:00–17:30** (22 HH). Total **137** candidate replacements, with **151 original QC0 same-day healthy records unchanged** for per-date bias calibration. For each day `mean(original TA_F−original TA_ERA)` is calculated over the QC0 native records **before the broken morning onset and at/after 18:00**, then new site-like trial `TA_F = original processed FLUXNET TA_ERA + daily mean residual`. Six exact daily means in order: **−2.832680°C, −2.472120°C, −2.251880°C, −1.555640°C, −3.633480°C, −2.844576923°C**. The input is **FLUXNET processed `TA_ERA`, NOT standalone ERA5-Land**. All user-selected intervals, source values, daily means and 06:30/07:00 and 18:00 boundaries are explicitly pinned; abnormal timing is not guessed from a general residual threshold.

[Manual science plan, all six exact means, example corrected TA and ready-to-run operator command](docs/SP1_SIX_DAY_OPERATOR_MANUAL_ERA_BIAS_REPAIR_READY_2026-10-25.md); [source-locked 137-HH research candidate generator with full-site independent readback](scripts/manual_review/apply_sp1_six_oct2007_daily_era_offset_research_candidate.py) pinned at commit `e0694f481a5f5950343851bbc552bf32179f36d3`. When run on IRIDIS6, the script first verifies the original 368,208-HH US-SP1 source SHA, six complete 48-HH days, **the already verified manual 3-point scenario parent files**, Stage14 retained RH, precise daily offset and required boundary smoothness. `--apply` writes **one completely new research-only** US-SP1 368,208-row CSV (trial `TA_F_QC=2`; recalculated `VPD_F`, trial `VPD_F_QC=2`), full 137-HH provenance, ten-site research manifest and receipt, and performs a complete 368,208-row **post-write source comparison** requiring **137 new HH and 451 changed field cells** (137×3 numeric/QC changes plus 40 VPD_F_QC1→QC2). All 9 other site manifest entries remain identical, including earlier US-SRG 2019 QC2-flank interpolation; US-SP1 2000 two-point ERA5-Land candidate is retained in parent source. **Code is READY, not yet executed in user-provided IRIDIS logs.** No original or preexisting candidate overwritten.

**Scientific boundary:** manually requested substitute source does not imply original tower QC0 was scientifically disproved; the eight original temperature science HOLDs and US-Syv **606 + 10** deferred issues remain, and this cannot be called officially approved Post-v5/DATM/CIME/SLURM/spinup forcing without further validation.

## Manual 6 × full 24-hour native original TA/QC/ERA visual report — code READY (2026-10-25)

**User requested all 48 half-hour points for each day:** **2007-10-15/16/17/18 and 2007-10-22/23**. Earlier IRIDIS6 logs covered only Oct 15 **05:00–21:00**, Oct 16–18 **08:00–20:00** and just 17:30/18:00 for Oct 22–23; values outside those windows cannot be inferred. The [SHA-pinned six-full-day script](scripts/manual_review/inspect_sp1_six_october_days_full_24h_original_T_ERA_QC.py) reads the **original** `368208`-HH US-SP1 FLUXMET release and verifies exact source SHA, all **six dates × 48 native HH**, plus original 17:30/18:00 QC0/TA anchors. It prints **all 288** records with `TA_F`, `TA_F_QC`, `TA_F_MDS`, `TA_F_MDS_QC`, processed `TA_ERA`, `VPD_F`, `VPD_F_QC`, and tower-minus-ERA difference. `--report` also writes just two **new standalone** report files beneath `$HOME/ameriflux_batch04_manual_review/`: exact six-day CSV and self-contained visual HTML with **six daily TA/ERA curves, separate 48-point QC tables and flagged ≥10°C QC0 departures**. `--inspect` is entirely read-only. **GitHub code created, not run on IRIDIS6 yet**, no claims about unobserved early-morning/late-evening values and no modifications to original/Stage14/Stage15/candidate sources, DATM, CIME, Slurm or model.

## US-SP1 2000–2020 exact clock-step source inventory VERIFIED — next independent three-tower BASE evidence (2026-10-25)

**Operator IRIDIS6 read-only 368,208-HH, 7,671-day original source scan PASSED**, exact source SHA `d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963`. **Exactly 6/6** original **QC0 17:30→18:00 ≥10°C step days**, ALL October 2007, with **≥5 original QC0 daytime HH at least 10°C colder than processed `TA_ERA`**. Six dates: **2007-10-15, 16, 17, 18, 22, 23**, split into **4-day** and **2-day** clusters. The six 17:30 original QC0 TA values span only **11.123–11.169°C**, followed by **+12.070 to +15.102°C** 18:00 jumps. Source-cold-screen days (≥5 QC0 daytime HH `TA_F−TA_ERA≤−10°C`): **1 in 2000, 2 in 2005, 33 in 2007, 37 in 2008**. The latter are a broader diagnostic screen, not 73 independently validated bad-data days. Source scan provides **no** grounds to auto-replace all daytime original QC0 values.

**Better next action with *genuinely new independent field evidence*:** AmeriFlux officially lists **US-SP2 (29.7648°N, 82.2448°W; 50m; BASE 1999–2008)** and **US-SP3 (29.7548°N, 82.1633°W; 50m; BASE 1999–2010)** near **US-SP1 (29.7381°N, 82.2188°W; 50m; BASE 2000–2020)**. Download **2007/2008 BASE and BADM** for all three sites, inspect original TA sensor variable names, heights, native clocks and QC and compare the October 2007 six-day episodes and 2008 Jan/Feb cold spells. **No BASE files have been inspected in this workflow**; BASE is site-submitted AMP QA/QC data, not necessarily raw logger. Verify sensor/channel independence and timestamp alignment. If corroboration is unavailable, ask the US-SP1 operators for the original TA logger/QC/clock history before changing the full anomaly intervals. [Full source-verified 6-day results, source screening thresholds, verified nearby station data links and science gate](docs/SP1_ALL_YEARS_1800_STEP_AUDIT_VERIFIED_AND_NEARBY_BASE_NEXT_2026-10-25.md).

**No new data edits or additional internal ERA-only stages.** Previously approved technical **3-HH/9-cell research alternative remains full-CSV VERIFIED PASS**, but **8 original TA science HOLDs and US-Syv 606+10 deferred questions remain**, no Post-v5, DATM/CIME, Slurm/spinup authorisation.

## Operator three-temperature alternative — complete independent full-CSV audit VERIFIED (2026-10-25)

**The operator completed the full independent read-only audit PASS:** **2/2 entire site CSVs, 3/3 changed native HH, exactly 9 field cells changed (`TA_F`, `TA_F_QC`, `VPD_F`)** across **683,808 half-hour rows** (US-SP1 368,208; US-SRG 315,600). The other **8/8 site manifest entries are identical**, full candidate SHA256s and provenance receipts verified, trial QC2 follows ERA-derived sources, and recalculated VPD satisfies original Stage14 RH/water saturation. [Complete operator-verified full-source audit and scientific release boundary](docs/MANUAL_THREE_T_FULL_SOURCE_AUDIT_VERIFIED_2026-10-25.md).

- **US-SP1 candidate SHA256** `96d8c6ad2a082bb243160ee91c2aee0d2fcd3dc0a862515519c34dab2fa664d3`: 2000-10-09 **18:00** original −6.900°C/QC0 → ERA5-Land trial **14.370813°C/QC2**, VPD **10.194556 hPa**; **18:30** original −7.100°C/QC0 → **13.776224°C/QC2**, VPD **9.445459 hPa**.
- **US-SRG candidate SHA256** `d65523022718819d7013d79f1015fe419958078a8d1fde4f062fa8470929933f`: 2019-03-19 **12:00** original **0.718°C/QC0** → **20.136500°C/QC2**, VPD **17.060332 hPa**. Interpolated using ERA-filled QC2 neighbors **11:30 19.668°C** and **12:30 20.605°C**, **NOT independent raw tower readings**.

The separate unapproved research-alternative directory remains `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_temperature_alternative_not_approved/candidate_20261025T183441Z_254f8181`. The prior Stage15 US-SP1 alternative remains a **different** scenario. **All original 8/8 TA-science HOLDs remain** (3 have technically audited alternative candidates; 5 still require separate science judgement). US-Syv **606 older holds + 10 skipped ERA edges** remain deferred. **Technical candidate verification does not authorise Post-v5, DATM/CIME, Slurm or CLM-FATES spinup**. The next science gate is raw/site-operator/BASE evidence for US-SP1's repeated four-day 18:00 jump, its two extended 2008 cold spells, and US-Seg's winter humidity-vs-T consistency.

## Operator-returned expanded original TA series — 7 windows VERIFIED (2026-10-25)

**Original FLUXMET `--inspect` completed read-only for 7 windows**, including all Oct 15–18 daytime source rows, the Jan 15–17 and Feb 2–4 2008 cold spells, and US-Seg Dec 27 after 20:00 through Dec 28 10:00. [Operator-verified full interpretation, exact source SHA and representative native observations](docs/MANUAL_EXTENDED_T_OPERATOR_VERIFIED_2026-10-25.md).

- **Major new source concern, US-SP1 Oct 2007:** at local 17:30→18:00 on four consecutive dates, original `TA_F_QC=0` jumps **+12.070°C (Oct 15), +12.071°C (Oct 16), +12.541°C (Oct 17), +15.102°C (Oct 18)**. At 17:30 source T is repeatedly ~**11.14–11.17°C**, while the source `TA_ERA` is ~**25.9–27.5°C**. This is a repeated daily time-of-day discontinuity, **not one bad point**, and needs original sensor/source/clock audit before any segment-wide intervention.
- **US-SP1 2008 Jan/Feb:** full original QC0 half-hour sequences show extended measured cold regimes relative to processed ERA, not isolated spikes. Do not interpolate only Jan 16 08:00/08:30 or Feb 3 08:00.
- **US-Seg Dec 27–28:** source QC0 T remained below freezing through much of the night (down to **−3.948°C at 03:00**), while processed `TA_ERA` also fell to below zero by 04:00. This lends support to preserving original T, with humidity/VPD physics adjudicated separately.

**Manual trial assessment environment:** the first `--assess` in conda `(base)` failed `ModuleNotFoundError: numpy`. The operator activated `clm_fates_env` and retried; the provided transcript has only a second **SELF-TEST PASS**, **not** the required exact `MANUAL PROPOSAL` entries or `MANUAL ASSESS ONLY` completion. Consequently **manual three-point candidate assessment remains NOT VERIFIED** and **no new trial-created files are confirmed**. Check `manual_three_T_changes_assess.log` and the Python process before rerunning; do not interpret self-test as assessment completion. No original files or science flags should be rewritten.

## Operator-requested targeted manual T trial and longer half-hour review (2026-10-25)

**A NEW, NARROWLY SCOPED operator request (not a reopening of routine internal QC):** inspect **original native `TA_F`, `TA_F_QC`, `TA_ERA` and VPD at longer 30-minute windows** covering US-SP1 Oct 15 **before 15:30** and Oct 16–18 daytime, Jan 15–17 2008, Feb 2–4 2008, and US-Seg Dec 27 **after 20:00** into Dec 28. [Pinned read-only extended-window script](scripts/manual_review/show_extended_native_temperature_windows_readonly.py) and [instructions](docs/MANUAL_TEMPERATURE_DECISIONS_AND_EXTENDED_WINDOWS_2026-10-25.md) are committed, **not executed on IRIDIS6 yet**. The full extra HH values cannot be asserted until operator output.

**Operator specifies two trial changes, scientifically isolated from original tower QC:** (a) US-SRG 2019-03-19 12:00 native `0.718°C` (QC0) → **20.1365°C**, computed from the 11:30 `19.668°C` (QC2) and 12:30 `20.605°C` (QC2) values. Both flanks are **ERA substituted**—this is an ERA-origin manual interpolation, **not independent observed truth**. (b) US-SP1 2000-10-09 18:00 `−6.9°C` and 18:30 `−7.1°C` QC0 → **exact SHA-receipted ERA5-Land 2m temperatures at original local-standard HH timestamps** (prior approximate ~14.37/13.78°C, exact numerical results pending IRIDIS). All three updates receive `trial_TA_QC=2` ERA-derived provenance in a **new, separate two-site research candidate**, with VPD recomputed against Stage14 RH. [Read-only `--assess` plus optional `--trial` script](scripts/manual_review/build_manual_T_replacement_trial_only.py). **No trial job run; no original/Stage14/Stage15 source edits; eight source-validity science HOLDs retained; no Post-v5/DATM/CIME/Slurm/spinup release.**

US-SP1 has official AmeriFlux elevation **50 m a.s.l.** ([site metadata](https://ameriflux.lbl.gov/sites/siteinfo/US-SP1)). Ordinary small elevation mismatch is unlikely to explain a 10–20°C tower-vs-ERA discrepancy, but actual ERA5-Land grid elevation and specific thermometer height have **not been independently checked**. No claim of zero height representativeness error.

## Latest Batch04 checkpoint — Stage21 VERIFIED, internal-only source availability gate CLOSED (2026-10-25)

**Stage21 operator-VERIFIED PASS on IRIDIS6** ([full actual results and original SHA ledger](docs/STAGE21_VERIFIED_ORIGINAL_TEMPERATURE_SOURCE_COVERAGE_2026-10-25.md)). The original FLUXNET v1.3_r1 releases for **US-SP1, US-SRG, US-Seg** each have **16 CSV files**: 1 BIF, 5 BIFVARINFO, 5 ERA5 and 5 FLUXMET. **48 original CSV headers inspected in total; zero separately named original sensor-level air-temperature channels identified**. The native FLUXMET_HH files instead include `TA_F_MDS`, `TA_F_MDS_QC`, `TA_ERA`, `TA_F`, `TA_F_QC`. This is a **release-contents finding**, not proof that original site loggers, separate AmeriFlux BASE products, unpublished data or other archives lack independent temperature records.

Original BIF `FLUX_MEASUREMENTS` groups refer to **CO2/H2O/H eddy-covariance flux**, not the specific original air-temperature sensor. Stage20's BIF `ERA_VARIABLE=TA` groups are also **not independent temperature observations**. Repeated FLUXMET-versus-ERA comparisons cannot validate the original `TA_F_QC=0` temperatures.

**Required next evidence (not a new Stage22):** [verified AmeriFlux site PI/data manager pages, exact dates, and prepared UNSENT source-data requests](docs/STAGE21_SITE_OPERATOR_TEMPERATURE_REQUESTS_2026-10-25.md). Official AmeriFlux also offers separate BASE data products, which were **not** evaluated by Stage21; source TA field(s), height, timestamps, quality flags and their independence still require verification. A contact draft does not mean data were requested or received.

- **US-SP1:** 2000-10-09 18:00/18:30 Stage15 alternative remains separate and unapproved; 2007-10-15 17:30 and three 2008 original events form part of wider multi-hour QC0 temperature-versus-ERA discrepancies. Need original logger/raw thermometer data, calibration and time-keeping notes before revising T.
- **US-SRG:** 2019-03-19 12:00 original `TA_F=0.718°C QC0`, `TA_ERA=20.399°C`; both adjacent consolidated TA_QC2 temperatures are **ERA-based fills rather than independent raw tower temperature**. Suspected single-point outlier **still scientific HOLD**.
- **US-Seg:** 2016-12-27 18:00 original QC0 `0.015°C` in sustained original cooling; preserve original T until independent source/weather evidence confirms otherwise.

**Release gate remains BLOCKED** for these unresolved inputs: all **8/8 original temperature science HOLDs unchanged**, **US-Syv 606 older science HOLDs + 10 skipped Stage07 ERA end-points deferred**. Stage14 humidity-only research candidates and Stage15 isolated alternative are not scientifically released forcing. **Do not run Post-v5, DATM/CIME, Slurm or CLM-FATES spinup based on these candidates.** No more incremental internal-only temperature QC stages without **new** independent evidence.

Fourth independent ten-site AmeriFlux campaign following [Batch03](../AmeriFlux_MultiSite_10_Batch03/), [Batch02](../AmeriFlux_MultiSite_10_Batch02/) and [Batch01](../AmeriFlux_MultiSite_10/). This directory contains the exact release manifest and reproducible scripts. Never commit raw tower ZIPs or derived large files to GitHub.

## Exact 10-site release manifest

| Site | Original archive name (expected) | Release-year labels |
| --- | --- | --- |
| US-Rpf | `AMF_US-Rpf_FLUXNET_2008-2024_v1.3_r1.zip` | 2008–2024 |
| US-Seg | `AMF_US-Seg_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-Ses | `AMF_US-Ses_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-Slt | `AMF_US-Slt_FLUXNET_2005-2022_v1.3_r1.zip` | 2005–2022 |
| US-SP1 | `AMF_US-SP1_FLUXNET_2000-2020_v1.3_r1.zip` | 2000–2020 |
| US-SRG | `AMF_US-SRG_FLUXNET_2008-2025_v1.3_r1.zip` | 2008–2025 |
| US-SRM | `AMF_US-SRM_FLUXNET_2004-2025_v1.3_r1.zip` | 2004–2025 |
| US-Syv | `AMF_US-Syv_FLUXNET_2001-2025_v1.3_r1.zip` | 2001–2025 |
| US-Ton | `AMF_US-Ton_FLUXNET_2001-2025_v1.3_r1.zip` | 2001–2025 |
| US-Uaf | `AMF_US-Uaf_FLUXNET_2003-2025_v1.3_r1.zip` | 2003–2025 |

Machine-readable manifest: [sites.tsv](sites.tsv). Year labels and FLUXNET release names are operator-provided identifiers, **not** independently verified station coverage, native cadence, measurement quality or land-cover/PFT assignment. Accept only an exact `<package>.zip` archive (case-insensitive extension) or an exact same-named release directory in the Windows source folder. ZIP takes priority when both exist. No renaming, repacking or altered year-range substitutions.

## Stage00 — Copy and SHA256-verify all original packages

**Run in your LOCAL WSL terminal, not on IRIDIS and not in native PowerShell.** Windows source: `D:\Fluxes_Tower_Experiment\Ameriflux`; WSL mount: `/mnt/d/Fluxes_Tower_Experiment/Ameriflux`.

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch04'
  BASE="$HOME/ameriflux_batch04_transfer"
  mkdir -p "$BASE/scripts/stage00"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage00/00_upload_ameriflux_batch04.sh"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage00/00_upload_ameriflux_batch04.sh" -o "$SCRIPT"
  bash -n "$SCRIPT"
  LOCAL_ROOT='/mnt/d/Fluxes_Tower_Experiment/Ameriflux' \
    bash "$SCRIPT" 2>&1 | tee "$BASE/upload_$(date +%Y%m%d_%H%M%S).log"
)
```

Requirements: Bash, `curl`, `ssh`, `rsync`, `sha256sum`, `find`, `awk`, `mktemp` and `head`. The script first preflights the **entire ten-site manifest** and refuses to connect if any source is missing. It then establishes **one SSH master session** to `ly3n24@iridis6.soton.ac.uk`; normal authentication may be required once. Later operations reuse only the master (batch mode, no fallback connection). Run again to resume an interrupted transfer. It neither changes nor deletes local originals.

Expected destination for each ZIP:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<US-SITE>/forcing/packages/<EXACT-PACKAGE>.zip
```

Same-named release directories, if provided instead of ZIP, go under `packages/<EXACT-PACKAGE>/`. Existing completed destination archives are preserved (`rsync --ignore-existing`); an existing different SHA256 is a **hard stop** rather than being replaced. ZIPs are verified end-to-end by local/remote SHA256; folders are checked with checksum-based `rsync --dry-run` including unexpected remote files. Source and destination package files are never deleted; any cleanup of temporary transfer files is managed by rsync.

**Do not report success unless the full output contains:**

```text
UPLOAD VERIFIED: 10/10 (AmeriFlux Batch 04). Originals retained. No extraction or model jobs started.
```

Store the WSL upload log outside GitHub; it contains actual sizes, SHA256 digests, SSH errors (if any) and the verified site tally. Confirm remote disk/inode quotas if transfers fail.

## Stage01 — Extraction and structure inventory (Stage00 has now passed)

Stage01 script is ready at [scripts/stage01/01_extract_ameriflux_batch04.py](scripts/stage01/01_extract_ameriflux_batch04.py), adapted from Batch03. It extracts CSV products without altering original archives; recursively handles nested ZIPs; checks output CRC/size and inventory structure; records a timestamped JSON report. It does **not** approve site meteorology, produce forcing or submit model jobs.

To run only after a verified 10/10 upload, execute **on IRIDIS6**:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch04'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage01"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage01/01_extract_ameriflux_batch04.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage01/01_extract_ameriflux_batch04.py" -o "$SCRIPT"
  python3 -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" 2>&1 | tee "$HOME/AmeriFlux_Batch04_stage01_$(date +%Y%m%d_%H%M%S).log"
)
```

The Stage01 CLI also supports `--audit-only`, `--sites US-Rpf`, `--sites-root` and `--reports-dir`. Stage01 runs no Slurm jobs. Default output inventory location: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/reports/`.

## Stage02 — APPROVED AND REVERIFIED (10/10 PASS)

Batch04 Stage02 follows the Batch03 metadata preflight, with one **explicit user-approved coordinate exception** in [coordinate_decisions.tsv](coordinate_decisions.tsv): **US-Seg original BIF GROUP_ID 1495, latitude 34.3623, longitude -106.7020, elevation 1596 m, LOCATION_DATE_START 200701010000**. Script verifies the exact BIF group pairing and elevation/date before accepting. The other nine sites still require unambiguous original BIF locations; no general fallback or silent coordinate guessing. IGBP and FATES PFT/height selections remain independently unapproved.

On the **IRIDIS6 login terminal**, run:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch04'
  BASE="$HOME/ameriflux_batch04_stage02"
  mkdir -p "$BASE/scripts/stage02"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  curl -fLsS --retry 3 "$RAW/$REL/coordinate_decisions.tsv" -o "$BASE/coordinate_decisions.tsv"
  SCRIPT="$BASE/scripts/stage02/02_check_batch04_metadata.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage02/02_check_batch04_metadata.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage02_$(date +%Y%m%d_%H%M%S).log"
)
```

This script **does not write any output** itself. The shell `tee` saves an external operator log. The operator **reran the revised checker** successfully: `STAGE02 SUMMARY: 10/10 coordinate + first-interval checks PASS; failures: none`. Final execution details are in [Stage02 post-approval verification](docs/STAGE02_POST_APPROVAL_VERIFIED_2026-10-24.md). The historical 9/10 before approval remains in the [original evidence](docs/STAGE02_METADATA_PREFLIGHT_2026-10-24.md). Investigate exclusions (WET/CRO/WAT), non-forest PFT applicability, sensor-to-TA mapping and time continuity in later independent scientific stages.

## Stage02B — US-Seg coordinate provenance (completed; approval recorded)

The original US-Seg BIF contains latitude `34.3623`, longitude candidates `-106.7020` and `-106.7019`. These longitudes are only about 9.18 m apart, but the currently published AmeriFlux site point is `34.3603, -106.7003`, roughly 267–272 m from these BIF candidates. The [research team site](https://www.litvaklab.org/grassland---us-seg.html) lists `34.3623, -106.7019`. The source mismatch has been investigated; the operator has now **explicitly selected original BIF GROUP_ID 1495**. The decision is recorded in [the approval ledger](docs/STAGE02_US_SEG_GROUP1495_USER_APPROVAL_2026-10-24.md). Other reference points are retained only for provenance and are not used in the approved site location.

Run **on IRIDIS6** after Stage02; the diagnostic is read-only:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage02"
  mkdir -p "$BASE/scripts/stage02"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage02/02b_diagnose_US_Seg_coordinate_conflicts.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage02/02b_diagnose_US_Seg_coordinate_conflicts.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage02b_US_Seg_$(date +%Y%m%d_%H%M%S).log"
)
```

The original Stage02 result was 9/10; the explicit location approval is now documented, but **the revised read-only Stage02 checker has now passed 10/10 on IRIDIS6**. External points remain historical references only, not selected coordinates.

## Stage02C — full HH time-series and basic scientific flags (READ ONLY)

[Stage02C script](scripts/stage02/02c_audit_batch04_HH_time_coverage.py) **was executed by the operator: time_pass=10, review=none, failed=none**. See [full HH results and QC HOLD report](docs/STAGE02C_FULL_HH_TIME_QC_AUDIT_2026-10-24.md). It checks all 10 original `FLUXMET_HH` series for full chronological continuity, malformed timestamps, non-30-minute intervals, gaps and overlaps, plus missing/available counts for basic named meteorological fields and review-only negative VPD/RH/PA/wind/precipitation diagnostics. Variables not present under the explicit names are marked `NOT_FOUND`, not silently inferred. **It does not approve or apply repairs**, shift UTC, choose US-Seg coordinates or create model jobs.

On IRIDIS6, run:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage02"
  mkdir -p "$BASE/scripts/stage02"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage02/02c_audit_batch04_HH_time_coverage.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage02/02c_audit_batch04_HH_time_coverage.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage02c_HH_$(date +%Y%m%d_%H%M%S).log"
)
```

For a smaller audit use `python3 -B "$SCRIPT" --sites US-Rpf US-Seg`. The `STAGE02C SUMMARY` indicates timestamp gates, **not** full scientific QC. No file writes occur inside the Python audit; shell `tee` creates only an operator log.

## Stage03 — timestamped extreme meteorology and same-label ERA5 comparison (READ ONLY)

**Prepared and executed for 3/10 priority stations; remaining seven not executed.** The [Stage03 script](scripts/stage03/03_audit_batch04_extreme_met_and_ERA5.py) reports every station's counts and top-eight most extreme timestamped examples per category for `TA_F < -80 °C`, `TA_F > 60 °C`, `PA_F <= 0`, `PA_F < 50 kPa`, `PA_F > 115 kPa`, `RH < 1%`, `1% <= RH < 5%`, `RH > 100%` and `VPD_F < 0`. It prints native values, available original native QC columns, derived `RH(TA_F,VPD_F)` for valid tower values, and **only exact raw string timestamp-label matched** ERA5 HH variables if present. It never changes inputs, makes UTC assumptions, adopts external station coordinates or combines unrelated-source ERA variables to produce humidity/forcing.

For a first targeted audit on US-SP1, US-Syv and US-Ton, run on **IRIDIS6**:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage03"
  mkdir -p "$BASE/scripts/stage03"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage03/03_audit_batch04_extreme_met_and_ERA5.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage03/03_audit_batch04_extreme_met_and_ERA5.py" -o "$SCRIPT"
  python3 -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --sites US-SP1 US-Syv US-Ton
    2>&1 | tee "$BASE/stage03_priority_$(date +%Y%m%d_%H%M%S).log"
)
```

For all ten sites later, omit the `--sites` argument. The Stage03 output is a **read-only scientific screening, not a repair ledger or production approval**. Exact raw timestamp-label matches do not by themselves establish time-zone equivalence, forcing units, or a permitted replacement. Review events manually before any ERA5 repairs.

## Stage03 priority execution — 3/3 site science HOLD (2026-10-24)

The operator executed the initial Stage03 diagnostic for `US-SP1 US-Syv US-Ton`: `flagged=US-SP1,US-Syv,US-Ton none_of_selected_flags=none failed=none`. Actual event counts, timestamps and source values are documented in the [Stage03 priority ledger](docs/STAGE03_PRIORITY_MET_ERA_DIAG_2026-10-24.md).

**Important correction:** packaged `ERA5_HH` columns `TA_ERA` and `PA_ERA` should not be assumed to be physically independent unadjusted ERA5 reanalysis. The standard FLUXNET naming system denotes `*_ERA` as **downscaled/calibrated ERA-derived products**, while `*_F` consolidates tower and ERA-derived values. For example `PA_F_QC=2` denotes an ERA-downscaled fallback (see [FLUXNET variable codes](https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/)). v1.3 has updated ONEFlux processing, so further details must be verified from its own BIFVARINFO metadata. `PA_F=PA_ERA` can thus reflect product lineage rather than independent confirmation. Anomalous `TA_ERA` values of -243 to -271 °C at flagged rows make blind replacement scientifically unsafe.

The Stage03 script also supports `--sites US-Rpf US-Seg US-Ses US-Slt US-SRG US-SRM US-Uaf` for the remaining seven stations. **No repair policy is approved**.

## Stage04 — focused source lineage and neighbour checks (READ ONLY; not executed)

New script: [04_trace_batch04_meteorology_ERA_neighbours.py](scripts/stage04/04_trace_batch04_meteorology_ERA_neighbours.py).

Stage04 inspects exactly selected extreme time windows with two original half-hours on each side for US-SP1, US-Syv and US-Ton. It reports native `TA`, `TA_F_MDS`, `TA_F`, `TA_ERA`, `PA`, `PA_F`, `PA_ERA`, `VPD`, `VPD_F`, `VPD_ERA`, `RH` and available QC columns alongside **time-label matching** packaged ERA5 variables. It flags exact equality but never considers equality independent validation.

Run on IRIDIS6:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage04"
  mkdir -p "$BASE/scripts/stage04"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage04/04_trace_batch04_meteorology_ERA_neighbours.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage04/04_trace_batch04_meteorology_ERA_neighbours.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage04_neighbours_$(date +%Y%m%d_%H%M%S).log"
)
```

No original file, forcing, temperature, vapor or pressure values are modified. An external, independently retrieved ERA5/ERA5-Land meteorology source with independently validated units, times and spatial interpolation must be reviewed before authorizing per-timestamp substitutions.

## Stage04 operator verified / Stage05 QCv5 candidate repair builder

The operator ran Stage04 self-test and checked all three priority sites: `STAGE04 SUMMARY: examined=3/3 failed=none`. See [Stage04 evidence, previous QCv5 policy and explicit user repair instruction](docs/STAGE04_VERIFIED_AND_STAGE05_QCV5_APPROVED_METHOD_2026-10-24.md).

The user explicitly selected the historical QCv5 short-gap interpolation for obvious `TA_F`/`PA_F` outliers and ERA-based humidity reconstruction for problematic `RH`. We therefore published an **isolated candidate builder**, [Stage05](scripts/stage05/05_build_batch04_qcv5_repair_candidates.py) (prepared, not yet executed on IRIDIS6). It is strictly scoped to `US-SP1 US-Syv US-Ton`, uses only the original exact FLUXMET and packaged ERA5 products, and follows the historic `TA_F/PA_F/VPD_F` 4-HH (2-hour) **complete-run** interpolation cap. The 2004 and 2016 multi-row pressure pulses are detected as `PA_F<65 kPa` so the 49–51 kPa shoulders are not silently preserved. A single `TA_F=0,VPD_F=6.110,RH=0` joint anomaly is separately identified. With a physically valid **same-source** `TA_ERA,VPD_ERA,PA_ERA` pair and `|TA_tower-TA_ERA|<=8°C`, suspect `RH<5%` or `RH>100%` is estimated from ERA source humidity **at preserved tower temperature**, with corresponding `VPD_F` changed consistently.

This is NOT a blanket RH replacement: isolated low-RH values can be physically plausible, subzero humidity phase definitions require review, and the packaged ERA-derived products contain documented absurd values in some windows. Invalid ERA cases are routed to `unresolved_hold.csv`, not patched. Missing raw RH alone is not an error if consolidated TA/VPD/PA are usable. No native CSV, archived source, existing case or DATM is altered.

**IRIDIS6 command — first inspect, then write isolated sparse candidate and hold ledgers:**

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage05"
  mkdir -p "$BASE/scripts/stage05"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage05/05_build_batch04_qcv5_repair_candidates.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage05/05_build_batch04_qcv5_repair_candidates.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage05_preview_$(date +%Y%m%d_%H%M%S).log"
  python3 -B "$SCRIPT" --build-candidates \
    2>&1 | tee "$BASE/stage05_build_$(date +%Y%m%d_%H%M%S).log"
)
```

By default the **build** creates a new, never-overwritten directory under `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage05_candidates/`, containing sparse `candidate_patch.csv` and `unresolved_hold.csv` plus SHA256-pinned `report.json`. The script is NOT a complete processed forcing dataset; a separately audited patch materialisation and Post-v5 gate are required before model forcing may use the overlay. Continue full Stage03 review on the other seven sites.

## Stage05 — QCv5 research candidates actually built (2026-10-24)

Stage05 **self-test PASS; preview PASS; `--build-candidates` PASS on IRIDIS6**, priority **3/3** stations (US-SP1, US-Syv, US-Ton), no runtime failures and no original file edits. **5,336 variable-level candidate patch entries** consist of **16 local TA/PA interpolation/joint-zero entries** and **2,660 humidity times × 2 RH+VPD fields = 5,320 entries**. **754 HOLD rows** remain (US-SP1 147, US-Syv 606, US-Ton 1). Original FLUXMET HH rows scanned in this targeted pass total **1,244,784**. Exact counts, science caveats and the source output location are in [Stage05 operator-verified execution record](docs/STAGE05_VERIFIED_3_SITE_QCV5_CANDIDATE_BUILD_2026-10-24.md).

**Created operator output on IRIDIS6:**
```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage05_candidates/candidate_20261024T103113Z/
```

Stage05 generated *sparse repairs*, not `processed_v5` model forcing; the files are `candidate_patch.csv`, `unresolved_hold.csv`, `report.json` and `README.txt`. The 754 unresolved cases are predominantly US-Syv ERA humidity pair/temperature-screen failures. They are **not** silently replaced from invalid `*_ERA` values. The FLUXNET source and all other site files remain immutable. **Post-v5, DATM and spin-up remain unapproved.**

## Stage06 — source SHA, paired humidity physics and new VPD jump audit (READY, NOT EXECUTED)

[06_audit_batch04_qcv5_candidate_effects.py](scripts/stage06/06_audit_batch04_qcv5_candidate_effects.py) reads exactly the previously generated Stage05 candidate version, checks `report.json` origin SHA256, confirms per-site 87/534/4715 patch rows and 147/606/1 holds, independently reconciles each sparse candidate with original native source half-hours and ERA-RH/VPD thermodynamics at **retained site temperature**, counts cold temperature/source-QC0 changes, and flags **new VPD half-hour jumps greater than 4 hPa or increasing by more than 2 hPa**. The thresholds are *review flags*, not invalidity proofs and never trigger automatic smoothing. Failures halt without modifying candidates.

On IRIDIS6 first run `--check`, and then optionally `--run` for **new reports only**:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage06"
  mkdir -p "$BASE/scripts/stage06"
  SCRIPT="$BASE/scripts/stage06/06_audit_batch04_qcv5_candidate_effects.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage06/06_audit_batch04_qcv5_candidate_effects.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --check 2>&1 | tee "$BASE/stage06_check.log"
  python3 -B "$SCRIPT" --run 2>&1 | tee "$BASE/stage06_report.log"
)
```

Stage06 reports go into a new `reports/stage06_qcv5_candidate_effects_*` folder with SHA receipts and a boundary review list, without editing original or Stage05 files. **No production sparse-patch merge before the 754 HOLDs and boundary/physical QC have been resolved and seven remaining Batch04 sites have completed appropriate scientific screening.**

## Stage15 read-only QA — latest 10 site sources and exact eight humidity cell changes

[15_audit_stage14_latest_ten_repaired_candidates.py](scripts/stage15/15_audit_stage14_latest_ten_repaired_candidates.py) was added **after Stage14 operator success**; **not yet executed on IRIDIS6**. It verifies the full Stage14 `stage14_latest_ten_candidate_manifest.tsv` against all ten selected complete FLUXMET HH files and SHA256 receipts. It compares every one of the 1,016,928 source-length half-hour rows across US-SP1, US-SRG and US-Seg against their Stage12 baseline. Only `VPD_F` and `RH` at the **exact eight** original suspect half-hours may change; all source `TA_F`, `PA_F`, `*_QC` fields and all other timestamps must be exactly unchanged. Verifies `VPD_F=e_s(TA_F)×(1−RH/100)` for all eight and keeps the **eight unresolved original QC0 T science HOLDs** distinct from numerical VPD/RH corrections.

Run on IRIDIS6:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/a4d0a696c2b93a52fcf981752a2ccb5fcde778a6"
  BASE="$HOME/ameriflux_batch04_stage15"
  SCRIPT="$BASE/15_audit_stage14_latest_ten_repaired_candidates.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage15/15_audit_stage14_latest_ten_repaired_candidates.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --audit 2>&1 | tee "$BASE/stage15_readonly_audit.log"
)
```

This Stage15 source verification performs **no writes**, CDS calls, Post-v5 approval, DATM setup or spinup. US-Syv 606 original science HOLDS plus 10 skipped Stage07 edge targets remain deferred.

## Stage15 IRIDIS6 VERIFIED: two US-SP1 temperature sensitivity candidates; Stage16 exact-diff audit next

Operator actually completed Stage15 `--self-test`, read-only `--assess` and isolated `--trial` successfully. Only **US-SP1 2000-10-09 18:00 and 18:30** have alternative changes: **T −6.9/−7.1°C (original QC0) → trial 13.182/15.363°C (QC1)**; VPD is recalculated as **9.4362/10.4653 hPa** with the retained independently sourced ERA5-Land RH, compared with the primary Stage14 **2.2746/2.1569 hPa** calculated at unchanged original TA. The two trial temperatures approximate ERA5-Land temperatures **14.371/13.776°C**.

**Actual immutable Stage15 alternative US-SP1 full CSV:**

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage15_sp1_two_point_temperature_sensitivity/candidate_20261025T080658Z_cca73e0e/US-SP1_Stage15_alternative_two_TA_times_FLUXMET_HH.csv`.

[Stage15 full verified execution record](docs/STAGE15_VERIFIED_TWO_POINT_ALTERNATIVE_2026-10-25.md). Its trial `stage15_receipt.json` contains the new full CSV SHA (not printed in operator output). The output also includes a ten-site alternative manifest that switches **only US-SP1** to the trial file and preserves the other nine Stage14 version pointers.

**Next runnable read-only verification:** [Stage16 two-row exact difference audit](scripts/stage16/16_verify_sp1_stage14_vs_stage15_exact_two_cell_trial.py). It streams all **368208** US-SP1 half-hours across primary Stage14 and trial Stage15, checks the respective source SHA256 and evidence receipts, and must find **exactly two changed timestamps** with **only TA_F, VPD_F and TA_F_QC changed**. It verifies VPD/RH closure at both trial TA values, unchanged other nine site input selections and the immutable scientific decision ledger. No external downloads or source/model writes.

Run on IRIDIS6:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/25722b041e0c74a8a0e9cfd690d193975313b4c4"
  BASE="$HOME/ameriflux_batch04_stage16"
  SCRIPT="$BASE/16_verify_sp1_stage14_vs_stage15_exact_two_cell_trial.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage16/16_verify_sp1_stage14_vs_stage15_exact_two_cell_trial.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --audit 2>&1 | tee "$BASE/stage16_audit.log"
)
```

**Science status unchanged:** Stage15 is an alternative temperature sensitivity candidate, NOT a proof of original tower sensor failure. All 8 QC0-temperature scientific HOLDs remain; US-Syv 606 + 10 earlier skipped edge targets are deferred. No Post-v5/DATM/CIME approval.

## Stage15 focused alternative two-point US-SP1 temperature sensitivity (not yet run)

The eight Stage14 humidity-only physical closure candidates succeeded, but none of the eight source QC0 tower-temperature disagreements was independently resolved. As the next bounded experiment, [Stage15](scripts/stage15/15_sp1_oct2000_two_point_temperature_sensitivity.py) examines **just two US-SP1 tower TA anomalies on 2000-10-09 at native 18:00 and 18:30**. Original T −6.9/−7.1 °C conflicts sharply with the unbroken warmer tower flanks (17:30=11.0°C QC0; 19:00=17.545°C QC1) and the independently downloaded grid T2m≈14.37/13.78°C. A two-half-hour flanking interpolation would yield **13.1817/15.3633°C**, within **2.5°C** of the grid reference at both timestamps.

Stage15 is an **alternative sensitivity candidate**, not a committed correction or model input. It enforces exact Stage14 SHA, recorded flank observations and existing CDS BIF-aligned 2000 grid evidence before producing one new full US-SP1 derived CSV; retains the Stage14 independent RH and recomputes VPD at proposed T; sets **trial TA_F_QC=1**, preserving original QC0 provenance in a separate ledger. Other nine Stage14 sites are not duplicated and the complete ten-site alternative manifest is separate. **All eight original temperature science HOLDs continue**, and US-Syv original 606 HOLDs remain deferred. [Stage15 method, source evidence and runnable command](docs/STAGE15_SP1_OCT2000_TWO_POINT_SENSITIVITY_TRIAL_2026-10-25.md).

Run the current Stage15 pinned source (`f8e83e08dc60c1843b12964a4441b508b4705173`) after fetching it to the Stage10 helper directory; `--assess` is read-only and `--trial` writes a new isolated candidate. No original/Stage14/production inputs overwritten.

## Stage14 actual operator result VERIFIED: 8/8 humidity closure candidates, 8 tower-temperature HOLDs unchanged

Stage14 ran on IRIDIS6 with syntax and self-test PASS, 8 exact VPD/RH half-hours recalculated using independent ERA5-Land relative humidity while preserving all original native `TA_F`, `PA_F` and QC labels. **US-SP1 6, US-SRG 1, US-Seg 1**. Three full new derived source-length candidate files created at:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage14_humidity_closure_candidate/candidate_20261025T075601Z_3473a555`

Verified full CSV SHA256 receipts from operator log:
- US-SP1 `3f2489eea6e7016b3c184bd90c93acd6597d32fc3d4cc8872ac28237a5181806` (368208 HH; 6 humidity replacements)
- US-SRG `57f650493a510cffe3146e3371599479f243ee188fb676b55c269683a1a63f39` (315600 HH; 1)
- US-Seg `22db08e969883cb7f5bc0dd7c3b161c60582c6fe6fe8715a0c9e23598cafbea6` (333120 HH; 1)

**Science gate:** 8/8 tower temperature disputes remain `HOLD_QC0_TOWER_TEMPERATURE_CONFLICT`. Numerically valid VPD at suspect tower TA is not independent proof of a valid tower temperature. US-Syv 606 older original science holds and 10 direct ERA boundary exceptions remain explicitly deferred. Stage14 wrote `stage14_latest_ten_candidate_manifest.tsv` for research candidates, not approved Post-v5/DATM forcing.

[Full operator output interpretation, all eight revised VPD numbers and original data SHA receipts](docs/STAGE14_VERIFIED_8_HUMIDITY_CLOSURE_QC0_T_HOLDS_2026-10-25.md).

## Stage13 VERIFIED eight supersaturated tower TA/VPD disagreements; Stage14 cautious VPD+RH candidate next

IRIDIS6 Stage13 completed read-only detailed inspection of the last eight non-Syv unresolved original half-hours (**US-SP1 6, US-SRG 1, US-Seg 1**): all eight original `TA_F_QC=0`, VPD source QC 1 or 2, and **native VPD_F exceeds e_s(water,TA_F)**. Original native RH absent. All independent ERA5-Land grid year data already exist. These are **physically inconsistent source humidity rows**; they do not establish which temperature is objectively true, and 7 have unstable ±6 h tower flanks; one lacks two-sided QC0/1 anchors.

[Stage13 original data, saturation evidence and Stage14 method](docs/STAGE13_VERIFIED_EIGHT_QC0_T_VPD_DISAGREEMENTS_STAGE14_2026-10-25.md)

[Stage14 runnable script](scripts/stage14/14_eight_humidity_physical_closure_keep_qc0_t.py) prepares a **separate numeric humidity repair candidate**, not a final observation correction: it uses exact native timestamps/BIF UTC offsets and already validated independent ERA5-Land T2m/D2m source to derive humidity, then replaces ONLY the eight physically invalid `VPD_F` plus `RH` at retained tower QC0 TA. It never overrides the **original QC0 temperature, PA or QC labels**. It creates three new complete site-derived CSVs and updates a ten-site selection TSV; other seven existing source files are not copied. Eight `HOLD_QC0_TOWER_TEMPERATURE_CONFLICT` records remain explicitly unresolved scientifically, while **US-Syv 606** older original holds + **10** skipped Stage07 ERA jump endpoints remain deferred. Post-v5/DATM/spinup are not approved.

Stage14 is committed but **not yet executed on IRIDIS6**. To run beside the existing Stage10 helper downloaded into `$HOME/ameriflux_batch04_stage12`:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_stage12"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/2c6b83ed9d55c487e9eaa32460ef7c5d56262f88"
  SCRIPT="$BASE/14_eight_humidity_physical_closure_keep_qc0_t.py"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage14/14_eight_humidity_physical_closure_keep_qc0_t.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --apply 2>&1 | tee "$BASE/stage14_apply.log"
)
```

## Stage13 exact remaining eight temperature conflicts (2026-10-25)

Operator Stage12 `stage12_science_decisions.tsv` shows **eight** unresolved events, all `NEIGHBOUR_OR_GRID_TEMPERATURE_NOT_CONFIRMED` from the original `SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID` HOLD category. **US-SP1 = 6 native HH timestamps**, **US-SRG = 1**, **US-Seg = 1**. Exact timestamps and HOLD sources are in the [Stage13 eight-event technical record](docs/STAGE13_EIGHT_TEMPERATURE_CONFLICTS_2026-10-25.md).

**No additional CDS source-year download needed.** [Stage13 exact-evidence script](scripts/stage13/13_inspect_eight_temperature_conflicts.py) is committed (not executed on IRIDIS6). Its read-only run compares original and latest source TA/QC/VPD/PA for the eight records, native QC0/1 nearest trustworthy temperatures on both sides within 6 hours, independent ERA5-Land hourly T2m and dewpoint-derived RH at the matching BIF standard local clock. It classifies where extended tower+grid evidence supports a safe temperature replacement versus where **original QC0 must remain a science HOLD**. The script makes no data or model writes. Use its numeric output, not an assumed correction, to define a bounded Stage13 repair action.

Run from the same local directory as the already-downloaded Stage12+Stage10 helper:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_stage12"
  SCRIPT="$BASE/13_inspect_eight_temperature_conflicts.py"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/62ee93c5475219fb05d891921803cb5e6e33550b"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage13/13_inspect_eight_temperature_conflicts.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --inspect 2>&1 | tee "$BASE/stage13_inspect.log"
)
```

The Stage12 148/156 real repairs and current ten-site derived manifest are unchanged. US-Syv remains out of scope and cannot silently be treated as model-ready.

## Stage12 second run VERIFIED — 148/156 corrected; isolate last eight physical exceptions

The operator reran Stage12 on IRIDIS6 with `--run --max-downloads 5` and completed/recovered **all five previously missing independent ERA5-Land site-year responses**: US-Seg 2018, US-Uaf 2004, US-SRG 2019, US-Seg 2014, US-Seg 2016. All **8 needed source site-years are now present**.

**Verified:** `STAGE12 RESULT 148 of 156 resolved 8 not resolved`. The first Stage12 was 143/156; this is a net **five additional repaired targets**. No original FLUXNET, earlier candidate source version, DATM, CIME, or Slurm operations were changed. Source SHA verification and physical screening still apply.

**Current authoritative Stage12 ten-site derived candidate manifest:**
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage12_non_syv_repaired/candidate_20261025T065108Z_6814ab0c/stage12_repaired_source_candidates.tsv`.

The remaining eight lack operator-provided event/physics reasons; extract them from the adjacent `stage12_science_decisions.tsv`, not from another CDS download. US-Syv 606 original holds plus 10 original Stage07 edge skips remain intentionally excluded. [Stage12 148/156 final source evidence and eight-target extraction](docs/STAGE12_FINAL_ERA5LAND_148_OF_156_2026-10-25.md).

## Stage12 verified first real repair: 143/156 resolved — finish last 5 ERA5-Land years (2026-10-25)

**IRIDIS6 operator PASS:** 143 of 156 distinct non-US-Syv Stage12 target timestamps have been resolved in actually produced derived CSV candidates. This unites 155 old non-Syv original HOLD entries and 2 additional US-SP1 skipped direct-ERA high-jump entries, with one overlap.

**Existing Stage12 derived output:**
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage12_non_syv_repaired/candidate_20261025T055139Z_9bc58872/stage12_repaired_source_candidates.tsv`.

**13 unresolved**, including **7** grid-needed native times in five as-yet-missing CDS site-years (US-Seg 2018 [2], US-Uaf 2004 [2], US-SRG 2019 [1], US-Seg 2014 [1], US-Seg 2016 [1]); **6 others** await the exact event statuses from `stage12_science_decisions.tsv`. Do not assume new CDS retrievals fix all 13.

US-SP1 2008, 2007 and 2000 external inputs were validated and made available in this run (2008 recovered pre-existing valid partial, the others freshly acquired). The original 10-site Stage11 inputs remain preserved and were reused in writing this first Stage12 candidate.

**Next IRIDIS6 command** (no code change/re-download required):

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_stage12"
  python3 -B "$BASE/12_repair_non_syv_science_holds.py" --run --max-downloads 5 \
    2>&1 | tee "$BASE/stage12_complete_five_years.log"
)
```

The program downloads or recovers at most five missing site-years, reuses the verified SP1 inputs, and writes a **new immutable Stage12 output version** with a fresh ten-site candidate manifest. Original FLUXNET, Stage05–11, and the prior Stage12 output are untouched. US-Syv 606 old science HOLD events and 10 missed ERA jump-edge targets remain explicitly deferred. Post-v5, DATM and spinup model input acceptance are separate gates.

[Stage12 first-run verified operator counts and download SHA records](docs/STAGE12_FIRST_APPLY_143_OF_156_2026-10-25.md).

## Stage11 operator VERIFIED / Stage12 active non-Syv fixes (2026-10-25)

**Stage11 operator result VERIFIED:** all 10 latest complete derived FLUXMET HH source files SHA-checked, full CSVs not duplicated, new `LATEST_10_SITES_FOR_POSTV5_INPUT.tsv` written:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage11_latest_ten_manifest/candidate_20261024T232100Z_1c6ef02a/LATEST_10_SITES_FOR_POSTV5_INPUT.tsv`.

Current source selection: Stage07 3 sites, Stage08 5 sites, Stage10 2 sites; 689/689 previous Rpf/SRM humidity faults are resolved. The old science HOLD ledger still has **761 entries**: **606 US-Syv deferred** and **155 other sites** (US-SP1 147; US-Seg 4; US-Uaf 2; US-SRG 1; US-Ton 1), plus up to 12 Stage07 skipped ERA jump-edge event timestamps which may overlap old HOLDs (2 SP1, 10 Syv).

**Next Stage12**: [source-repair script](scripts/stage12/12_repair_non_syv_science_holds.py) with [method and progress record](docs/STAGE11_VERIFIED_AND_STAGE12_NON_SYV_2026-10-25.md). It targets the 155 non-Syv old holds plus two SP1 missed jump-edge timestamps. It retains physically consistent original tower temperature/VPD wherever corroborated by trustworthy neighbouring native measurements and acquires **independent ERA5-Land** hourly T2m/dewpoint/surface pressure at precisely BIF located and local-standard UTC-offset-aligned years where source VPD is invalid or a high-jump edge was not repaired. It uses the pinned Stage10 helper to recover/download NetCDF. It creates new complete derived CSVs **only for actually modified sites**, a new latest-ten-site TSV, resolved/unresolved decision ledger and SHA receipt. US-Syv not touched. Any ambiguous original BIF holds only its site.

To run on IRIDIS6, download BOTH scripts beside each other (Stage12 imports Stage10 helper by filename):

```bash
(
  set -euo pipefail
  REPO="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  BASE="$HOME/ameriflux_batch04_stage12"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$REPO/c3a44684134a6a50e4086543301adc05e66365d9/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage12/12_repair_non_syv_science_holds.py" -o "$BASE/12_repair_non_syv_science_holds.py"
  curl -fLsS --retry 3 "$REPO/b8ff0c2aaf41683d70bb94e9d70715c25c5eea45/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage10/10_era5land_independent_humidity_fill.py" -o "$BASE/10_era5land_independent_humidity_fill.py"
  python3 -B -m py_compile "$BASE/12_repair_non_syv_science_holds.py"
  python3 -B "$BASE/12_repair_non_syv_science_holds.py" --self-test
  python3 -B "$BASE/12_repair_non_syv_science_holds.py" --run --max-downloads 3 2>&1 | tee "$BASE/stage12_run.log"
)
```

Stage12 is **committed but not yet executed**. Its actual science repair counts are to be established by the IRIDIS6 operator output; model-ready Post-v5, DATM and spinup remain unapproved.

## Batch04 Stage10 VERIFIED 689/689; Stage11 ten-site latest-source selection ready

Operator IRIDIS6 confirmed Stage10 successful **689/689 independent ERA5-Land source VPD repairs** (US-Rpf **688**, US-SRM **1**, remaining **0**). Original BIF station points/UTC_OFFSET were used, and source hourly T2m/D2m/SP was physically screened; the previously partial US-Rpf 2022 NetCDF was recovered and reused with a SHA receipt, while US-SRM 2023 was successfully downloaded from CDS.

**Latest complete independent ERA5-Land candidate files** (no original input overwrite):
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage10_independent_era5land/candidate_20261024T231424Z_d9967326`.

[Stage10 689/689 operator-verified result, receipts and remaining external gates](docs/STAGE10_VERIFIED_689_OF_689_ERA5LAND_REPAIR_2026-10-25.md).

**Stage11 (new executable, NOT run on IRIDIS6):** [11_register_latest_ten_derived_forcing_candidates.py](scripts/stage11/11_register_latest_ten_derived_forcing_candidates.py) builds **one precise 10-site data selection TSV**, SHA-checks the complete derived FLUXMET HH source files and selects the *latest* actual data:
- **3 from Stage07:** US-SP1, US-Syv, US-Ton
- **5 from Stage08:** US-Seg, US-Ses, US-Slt, US-SRG, US-Uaf
- **2 from Stage10:** US-Rpf, US-SRM

It does not duplicate millions of NetCDF/CSV source records or overwrite anything. It keeps remaining scientific decisions separate: **754 Stage05 original three-site HOLD entries + 7 Stage08 non-Rpf/SRM HOLD entries = 761**; **12 additional Stage07 skipped ERA jump endpoints may overlap** existing holds. These are *not* 689 newly unresolved Stage10 events, all of which were repaired. US-Syv remains deferred per explicit user instruction.

Run Stage11 on IRIDIS6:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/d9b8a6f66c844514249b71c9daa27e6ede7c6c6a"
  BASE="$HOME/ameriflux_batch04_stage11"
  SCRIPT="$BASE/11_register_latest_ten_derived_forcing_candidates.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage11/11_register_latest_ten_derived_forcing_candidates.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --build 2>&1 | tee "$BASE/stage11_build.log"
)
```

The manifest output `qcv5_stage11_latest_ten_manifest/candidate_*/LATEST_10_SITES_FOR_POSTV5_INPUT.tsv` is a **version-pinned input selection, NOT Post-v5-approved production forcing**. The model/DATM transition requires separate validation and unresolved science-gate resolution.

## Stage10 BIF verified; three external site-years present; safely resume missing two (2026-10-24)

Stage10 reached its first CDS download after a successful self-test. Original BIF readings are unambiguous: US-Rpf **65.1198°N, -147.429°, UTC_OFFSET -9** and US-SRM **31.8214°N, -110.8661°, UTC_OFFSET -7**. The operator's 689 exact target HH timestamps fall into only **five site-years**: US-Rpf 2024 (390), 2008 (218), 2021 (69), 2022 (11), US-SRM 2023 (1). The first **three have existing SHA receipts**; US-Rpf 2022 has a saved `.download.partial`, and US-SRM 2023 needs a new retrieval.

The old `FileExistsError` is a safety guard that stopped a potential overwrite of US-Rpf 2022's earlier partial response. **No Stage10 derived repairs are confirmed yet.** [Fixed Stage10](scripts/stage10/10_era5land_independent_humidity_fill.py) first verifies and reuses a complete previous partial (or isolatedly preserves a failed one and retries); it never deletes original data, and only then obtains missing years and creates new **full native-length** source-derived CSVs.

Read the [Stage10 interrupted partial provenance and fix](docs/STAGE10_INTERRUPTED_CDS_PARTIAL_RESUME_2026-10-24.md). On IRIDIS6, re-download the pinned source from commit `b8ff0c2aaf41683d70bb94e9d70715c25c5eea45` and run `--run --max-downloads 2`. Existing 3 year receipts are preserved, and at most 2 new CDS requests are needed (or 1 if the pre-existing 2022 partial verifies).

## Stage09 VERIFIED (zero source repairs) / Stage10 independent ERA5-Land next

The operator completed Stage09 (`--self-test` and `--apply`) on IRIDIS6, generated two complete source-length derived CSVs, **0 new patches**, and preserved all **696 Stage08 HOLDs**. **US-Rpf 688/688** and **US-SRM 1/1** source-native VPD samples in the ERA-physics HOLDs are themselves physically invalid and cannot be safely rescued by max-four-HH original-tower interpolation. The repeated Stage09 source-CSV SHA256 matches Stage08 unchanged files.

[Stage09 VERIFIED and Stage10 CDS replacement method](docs/STAGE09_VERIFIED_ZERO_REPAIRS_AND_STAGE10_INDEPENDENT_ERA5LAND_2026-10-24.md).

**Next runnable Stage10 program:** [10_era5land_independent_humidity_fill.py](scripts/stage10/10_era5land_independent_humidity_fill.py), **not yet run on IRIDIS6**. It reads original BIF coordinates/UTC_OFFSET for US-Rpf and US-SRM (never hardcodes an invented location), groups the **689** exact blocked native timestamps by year, automatically retrieves at most **3 targeted CDS ERA5-Land point/year responses** per run, verifies each NetCDF time/units/physical data and SHA receipt, transfers gridded dewpoint-derived RH to retained tower temperature and directly creates **two new complete derived FLUXMET HH candidate CSVs** for all successfully repaired time points. Unavailable grid years or invalid source temperature/pressure remain HOLD. No production, DATM, CIME or Slurm operations.

Run after CDS credentials `~/.cdsapirc` and `cdsapi,numpy,netCDF4` are configured:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/b8ff0c2aaf41683d70bb94e9d70715c25c5eea45"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage10"
  SCRIPT="$BASE/scripts/stage10/10_era5land_independent_humidity_fill.py"
  mkdir -p "$(dirname "$SCRIPT")"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage10/10_era5land_independent_humidity_fill.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --run --max-downloads 3 2>&1 | tee "$BASE/stage10_run.log"
)
```

If some site-years remain after the first run, run the same `--run` again. Use `--apply-existing` to generate full derived files from already-verified grid evidence without more CDS requests. All Stage10 results remain incomplete research data until unresolved scientific issues are settled.

## Stage08 success and Stage09 next direct native-VPD fixes (2026-10-24)

**Stage08 VERIFIED 7/7:** `US-Rpf, US-Seg, US-Ses, US-Slt, US-SRG, US-SRM, US-Uaf` have complete derived FLUXMET_HH CSVs. 2,384,448 original native half-hours were copied; exactly 208 half-hours in five sites received 416 RH/VPD variable-level patches. US-Rpf and US-Slt had no modified source values. Stage08 has **696 HOLD** records (US-Rpf 688, US-Seg 4, US-SRG 1, US-SRM 1, US-Uaf 2; US-Ses and US-Slt zero). See [Stage08 verified SHA receipt summary](docs/STAGE08_VERIFIED_SEVEN_SITE_DERIVED_CSVS_2026-10-24.md).

**Actual Stage08 output:** `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage08_remaining_seven_candidates/candidate_20261024T120137Z/`.

**10/10 Batch04 site candidates now exist**, combining three Stage07 and seven Stage08 complete derived CSVs. They are NOT yet Post-v5 approved forcing.

**Stage09 (ready, NOT run):** target **689** invalid paired ERA humidity HOLDs, including **688 US-Rpf + 1 US-SRM**, without touching the deferred US-Syv or any other site. Apply actual physically admissible short original tower VPD interpolations (maximum four half-hours, trustworthy original QC0/QC1 flank records) and derive RH when original VPD is already valid but separate RH is invalid. Long runs and physically implausible interpolations remain HOLD. The command creates **two new full derived source CSVs** (not merely a diagnostic report), retains all original/Stage08 file SHA receipts and never overwrites previous candidate directories.

[Stage09 code](scripts/stage09/09_repair_ERA_invalid_native_humidity_short_gaps.py) | [Stage09 approved approach and run](docs/STAGE09_US_RPF_SRM_DIRECT_NATIVE_HUMIDITY_REPAIR_2026-10-24.md).

Run on IRIDIS6:
```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/c794f403bac063092d17030d1939121fae3b94a9"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage09"
  SCRIPT="$BASE/scripts/stage09/09_repair_ERA_invalid_native_humidity_short_gaps.py"
  mkdir -p "$(dirname "$SCRIPT")"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage09/09_repair_ERA_invalid_native_humidity_short_gaps.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --apply 2>&1 | tee "$BASE/stage09_apply.log"
)
```

The 754 Stage05 inherited HOLDs at the three original priority sites (plus 12 Stage07 invalid direct ERA edge targets, possibly overlapping) remain separate. The Stage08 696 HOLD entries and any Stage09 survivors must not be silently ignored in future model forcing.

## Latest verified: Stage07 three complete site candidates DONE; Stage08 remaining seven prepared

**Stage07 IRIDIS6 execution verified on 2026-10-24.** Three complete native-length derived FLUXMET_HH files were written, with original Stage05/Stage06 inputs SHA-pinned and unchanged:

- **US-SP1:** 368,208 source rows; 32 direct same-time ERA5 VPD replacements; 62 actual rows changed; SHA256 `9390f88948eaf621b4e697682da701675f08330b268f3661d5a98cd130364b28`
- **US-Syv:** 438,288 rows; 12 direct ERA5 VPD replacements; 270 actual rows changed; SHA256 `5086cbc0f08f73b218d08fdcf34cf0643a6ae1ea95c05c200a98800452b5b32e`
- **US-Ton:** 438,288 rows; 332 direct ERA5 VPD replacements; 961 actual rows changed; SHA256 `4ca4467a7f6180136ef06c8595bb36d2f25ae5413c91cd357c5c0d84a99d5646`

**Totals:** 376 successful physical ERA5 VPD substitutions among 388 distinct Stage06 jump-endpoint times; 12 unsuccessful exact-source cases remain skipped/HOLD. **1,566** physically plausible native US-Ton QC0 samples preserved against other Stage05 proposed overrides. 1,293 unique native rows changed in derived full CSVs. 754 Stage05 HOLD entries carried forward and may overlap the 12 new skip entries. Verified output:

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage07_applied/candidate_20261024T114538Z_6a6b36ba
```

[Stage07 verified output and SHA record](docs/STAGE07_VERIFIED_THREE_FULL_DERIVED_CSVS_2026-10-24.md). **This is a derived research candidate, not approved Post-v5/CIME/DATM spinup forcing.**

**Stage08 VERIFIED on IRIDIS6:** the [remaining seven-site script](scripts/stage08/08_build_remaining_seven_qcv5_candidates.py) was executed successfully for US-Rpf, US-Seg, US-Ses, US-Slt, US-SRG, US-SRM, US-Uaf. It extends the established Stage05 QCv5 max4-HH interpolation + physically screened same-time ERA RH method, but **protects physically plausible native VPD QC0 readings** and **does not treat positive RH<5% alone as an ERA replacement requirement**. It does not invent the US-Syv one-off joint-zero TA fix for other sites. A source RH column is optional if missing in a particular FLUXMET release. It writes a new independent seven-site **complete derived FLUXMET_HH CSV per site** plus sparse candidates and HOLD ledger, original source SHA receipts, **no original or existing model edits**. The seven-site pipeline can advance without reopening the successful three-site Stage07 derived runs.

Execute:
```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/33770619bbc68e9030a70190ffe3c901beb2187f"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  BASE="$HOME/ameriflux_batch04_stage08"
  SCRIPT="$BASE/scripts/stage08/08_build_remaining_seven_qcv5_candidates.py"
  mkdir -p "$(dirname "$SCRIPT")"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage08/08_build_remaining_seven_qcv5_candidates.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --build-candidates 2>&1 | tee "$BASE/stage08_build.log"
)
```
Output: new `qcv5_stage08_remaining_seven_candidates/candidate_*` folder with **seven complete derived FLUXMET_HH CSVs**, exact site source SHA256 + `candidate_patch.csv`, `unresolved_hold.csv`, `report.json` and INCOMPLETE research-candidate marker. Scientific warning: packaged ERA5 comes from the FLUXNET release and is not independent gridded ERA5-Land truth.

## Stage06 VERIFIED; Stage07 new full derived ERA5 VPD repair ready (2026-10-24)

Stage06 user execution: full original SHA checks, 5,336 Stage05 candidate variable patches and 754 holds VERIFIED; 210 flagged VPD jump edges (19 US-SP1; 12 US-Syv; 179 US-Ton), plus 2,259 original US-Ton QC0 VPD values potentially overwritten. Operator report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/reports/stage06_qcv5_candidate_effects_20261024T105030Z_8cc1f59c`.

**New user direction:** directly replace both endpoints of **these 210 flagged VPD jump edges** with **same-exact-native-timestamp packaged ERA5 `VPD_ERA`**, compute physically consistent derived RH at **retained EC tower temperature**, and create actual **three full-length derived FLUXMET HH CSVs** in a new isolated Stage07 version. Any nonphysical ERA VPD/pair is recorded as a skipped new HOLD; original native site VPD and stage05 source remain unchanged. **Outside the flagged edges**, protect original physically admissible US-Ton VPD QC0 and drop its previous Stage05 humidity overwrite. Defer the 419 bad US-Syv ERA pair cases.

[Stage07 script](scripts/stage07/07_apply_jump_ERA5_vpd_three_sites.py) | [Science method and executable shell command](docs/STAGE07_USER_APPROVED_DIRECT_ERA5_VPD_REPAIR_2026-10-24.md). The Stage07 Python code is **published but has not yet been run on IRIDIS6**. Only its user execution can confirm counts of valid vs invalid same-time ERA endpoints.

The paired FLUXNET `ERA5_HH` fields are downscaled ERA-derived data **not independently downloaded ERA5-Land**. Original ZIP/CSV, prior Stage05/06 results, `processed_v5`, DATM, CIME and Slurm jobs are not touched. Post-v5 model authorization remains withheld pending remaining scientific holds.

## Scientific gates outstanding after structural/timestamp preflight

1. Inventory each site's actual BIF, FLUXMET, FLUXES and companion products and native HH versus HR cadence, time zone, timestamp continuity and actual year coverage.
2. Audit tower-specific coordinates, vegetation/PFT evidence and instrument/measurement heights. Do not assign tower vegetation or ZBOT from coarse IGBP or unverified sensor layers.
3. Evaluate native sensor QC, implausible TA/VPD/RH/QBOT and wind/radiation records; any ERA5-Land replacements require source-level evidence, a repair ledger and explicit approval.
4. Perform the separately versioned QCv5 and Post-v5 verification gates before building DATM or submitting CLM-FATES spin-ups.

**Provenance:** the transfer script and extraction script are Batch04 adaptations of the Batch03 scripts, maintaining the same independent per-site package directory and dry-run/no-overwrite safeguards. Do not copy scientific acceptance outcomes from earlier batches to these ten new sites.
