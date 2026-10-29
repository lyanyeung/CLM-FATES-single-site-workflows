# US-NR3 — scientific handoff to higher-reasoning model (AmeriFlux Batch03)

**Prepared 2026-10-29. Project selection: provisionally second-hardest after US-MtB.** Scientific analysis and read-only audit ONLY. User retains approval rights for every physical repair, new trial shadow, source change and model job. This document does not start an autonomous agent or authorise new work on IRIDIS6. Current site-specific numerical snapshots have different timestamps/scopes; the first objective is source-of-truth reconciliation.

## 0. Exact identity: DO NOT CONFUSE WITH US-NR1

- Official AmeriFlux site **US-NR3: Niwot Ridge Alpine (T-Van West)**, latitude **40.0520°N**, longitude **-105.5864°**, elevation **3504 m**, **GRA alpine tundra/dry meadow**, Köppen **ET**, tower approximately **3 m** tall (not a measurement-height claim).
- Official metadata: https://ameriflux.lbl.gov/sites/siteinfo/US-NR3; same site is near US-NR4 and US-xNW but they are NOT identical tower records. Original BASE and BADM may provide alternate tower meteorology or sensor provenance after actual coverage and units are checked; verify first, do not copy nearby site blindly.
- Input exact package in repository **sites.tsv**: \`AMF_US-NR3_FLUXNET_2007-2024_v1.3_r1\` (2007–2024; original HH source, 30-minute cadence), **not US-NR1** (forest ENF, different location, different years) and **not the AmeriFlux BASE product**. Scientific findings refer to this release, not all possible BASE versions.
- Source/native clock: Stage09h release BIF indicates **UTC_OFFSET=-7 h**, Stage10a solar analysis consistent with that, interpreted as local *standard* time without applying daylight saving. This was a source hypothesis, not full approved native→DATM forcing clock; verify actual BIF and precise interval start/midpoint before any external reanalysis join.

## 1. Why this is the second-hardest unresolved site

Among the *remaining nine* (US-MtB handled by Claude), US-NR3 is the strongest scientifically underdetermined case: multiple entire years without source-labeled measured T/VPD; source ERA itself physically inconsistent at a large number of original records; severe cold/phase, grid vs tower differences, and missing validated source for selected years; little existing advanced dedicated repair work. A close alternative is US-NR1 with 234 latest missing HH, but NR1 already has a scoped operator-approved 2022 six-humidity/five-nonhumidity research-only patch, while NR3 does not. US-Kon has 77 latest *research shadow* gaps but still needs release audit; compare scopes, do not rank purely by missing count. This ranking is an expert **prioritisation**, not a quantified universal difficulty metric.

### Do not mix these counts

- **238 missing NOLEAP halfhours**: most recently verified US-NR3 Stage12G candidate (also Stage12AI 2026-10-26), **315,360 model time rows** over 2007–2024. Stage12G code declares \`PRIOR_HOLD["US-NR3"]=172\` **original protected physics-hold rows** and \`PRIOR_GAP["US-NR3"]=66\` other original gap rows; separate source-year ledger has **6** non-covered records within its narrower reason population. **Do not add 172+66 to 1,484, do not automatically equate source-year count with all gaps, and recheck the actual signed Stage12G CSV before assuming these categories remain unchanged.**
- **1,484 abnormal original source halfhours**: Stage08–10d selected *winter residual source-physics audit* of original companion ERA inconsistency, spanning affected years. **All 1,484 had source VPD_F_QC=2**, and matched companion \`VPD_ERA\` at exact native time; they are not all 1,484 NaNs in current selected forcing. Many original numeric records can be invalid even if finite.
- All **2017, 2018, 2023**, each **17,520 HH**, original source \`TA_F_QC=2\` and \`VPD_F_QC=2\` in the examined FLUXMET release, **zero QC0 or QC1** for those two variables. The 52,560 positions are **source-derived** values, not 52,560 necessarily missing model rows, not proof tower never had instruments, and not proof all ERA values are invalid.
- Other affected years with direct original physical dual QC0 coverage: 2007 **8,890/17,520**, 2019 **5,857/17,520**, 2022 **3,789/17,520** (Stage10G, annual affected-year comparison). No Stage10F/G 16 high-priority NR3 cold-episode clusters have directly observed both-side T+VPD QC0 anchors within **7 days**, so simple event interpolation is unsupported.

## 2. Evidence already proven on IRIDIS6 (do not repeat without reason)

**Source ERA algebra**: \`e_a = es_water(TA_ERA) - VPD_ERA\`; all **1,484/1,484** selected US-NR3 residual records imply **negative e_a** in their *original paired same-release* \`TA_ERA/VPD_ERA\`, before mixing with tower T. Median negative implied ERA water RH **−13.699%**, median \`VPD_ERA − es_water(TA_ERA)\` **+0.186228 hPa**, max **+0.889337 hPa** (Stage10I). This proves algebraic inconsistency in selected source fields, NOT negative real atmosphere or the causal flaw in the product's regression/downscaling. Do not reinsert original VPD blindly, clip negative e or RH, or assert a time shift as solution.

**Stage10B/C two *diagnostic* humidity hypotheses on same 1,484 events**:
- A, ERA5-Land dewpoint-derived **absolute vapour e** transferred to original retained tower T/pressure: **1,458** liquid-water physical passes and **26** failures; **163** A ice-relative RH>100% cautions.
- B, ERA5-Land **grid relative humidity** transferred to original tower T/pressure: **1,484** liquid-water numerical physical passes but **77** ice RH>100% cautions.
- **91** NR3 event-level tower–grid temperature mismatches \`|ΔT|>5°C\`. Source temperature/grid mismatches may reflect high-alpine topography, representativeness, instruments, time or other causes; do not assume elevation alone is sufficient.
- Stage10D mutually exclusive *priority* groups, summing to 1,484: P0=**26** A-water-fail; P1=**57** residual B ice RH>100; P2=**86** residual A ice RH>100; P3=**87** residual tower-grid ΔT>5; P4=**1,228** other cold-humidity review. These priority groups are mutually exclusive but original physical caveat flags can overlap. The P0/P1/P2/P3 categories are NOT approved replacements.
- MDS gap-fills are **not independent tower observations**. In pooled seven-site Stage10D, no source MDS pair met the combined physical + QC0/1 evidence rule; do not infer NR3 direct measurement from a nonmissing MDS field.

**Two exact impossible mixed-product counterfactual examples (Stage10K)**:
- Native **2018-02-21 09:30**, original CSV row **195333**: \`TA_ERA=-21.064°C\`, separately acquired ERA5-Land \`T2M=-15.569540°C\`, \`VPD_ERA=1.572 hPa\`, grid dewpoint-derived \`VPD=1.179913 hPa\`, resulting \`es_water(TA_ERA)-VPD_grid=-0.033131 hPa\`.
- Native **2018-02-21 10:00**, row **195334**: \`TA_ERA=-19.050°C\`, ERA5-Land \`T2M=-13.880003°C\`, \`VPD_ERA=1.623 hPa\`, grid-derived \`VPD=1.425444 hPa\`, implied e **−0.061299 hPa**.
These are **mixed-source algebra examples** — if grid T and dewpoint are used consistently, the moisture calculation is different. Their existence is not proof that raw ERA5-Land is wrong or that the source temperature may be overwritten.

## 3. Required research questions, in priority order

1. **Reconcile release and 238 true missing model rows first.** Read Stage07 signed original and Stage12G US-NR3 incomplete selected CSV and full SHA receipt. Produce a 238-row exact native timestamp/year/month/episode/variable/reason/source provenance ledger, confirming overlap of original 172 physics holds and remaining 66 source gaps, **including 6 external-year source unavailability**. Never "repair" 1,484 just because they were flagged in a different audit; explicitly cross-join the 1,484 original source event IDs with the 238 selected missing rows.
2. **Source-provenance investigation for 2017, 2018, 2023.** Confirm in source FLUXMET \`TA_F_QC=VPD_F_QC=2\` at all 52,560 rows and why: release processing, data-submit gap, variable availability, instrumentation/QC history. Inspect original **AmeriFlux BASE/BADM** data and source sensor series for each year (if actually available), accounting for unit, interval, timestamp, QA and year coverage. **Avoid treating BASE as independently verified until original observation and QC are established.** Nearby US-NR4, US-xNW, Niwot Ridge LTER station instruments can be cross-context only, with provenance, height and distance checks. Confirm timing and altitude before comparisons.
3. **Establish why original same-release paired \`TA_ERA,VPD_ERA\` imply negative e on selected cold records.** Is it downscaling/regression of separately estimated variables, product definitions, water/ice eSat equation, resolution, or a source processing issue? Verify exact 1,484 row identities and original QC2 against Stage10H/I; examine upstream FLUXNET processing documentation **without assuming cause**. Show year/season/T regime and \`TA_ERA\` vs \`VPD_ERA\` distributions. Native BIF UTC offset is -7 nominal; DST/shift hypothesis must be independently proven, not chosen for lower RMSE.
4. **Thermodynamics and model compatibility.** Derive eSat over water and ice, actual e, VPD, RHwater/ice, \`QBOT\` from retained site T and \`PSRF\` (pressure Pa). Check grid \`T2M,D2M,SP\` source file receipts, actual static grid geopotential/orography and tower elevation 3504 m. Separately check CTSM/CDEPS installed \`datm_esat\`, cold-ice saturation and whether datm might clamp QBOT. No automatic RH clipping or phase assumptions. Contrast A and B with properly matched source temperatures; do not blend VPD estimated at gridded T with retained tower T without recalculation.
5. **Validation where genuinely measured truth exists.** Use original simultaneous \`TA_F_QC=0,VPD_F_QC=0\` from supported years. Source/year/month/T/VPD regime matching; block by whole day and preferably whole **source year**, report MAE/bias/extreme error share/coverage per regime and cold year. Avoid overfitting after seeing results and avoid recycling ERA-derived QC2 as "truth". Unobserved 2017/2018/2023 should remain uncertainty-labelled if no independent field observations exist.
6. **PFT, surface, height and time gate.** Verify GRA alpine meadow/tundra surface and true observed cover with scientific source; do not borrow US-NR1 ENF. Check actual 3 m *tower height vs sensor height* (not equal by default), landunit, soil/snow, native 30-min time start vs midpoint, BIF, gridded UTC interpolation and current active case/PFT before any model admission.
7. **Explicit science disposition and alternatives.** Each original missing HH and source invalid numeric episode must be classified \`SOURCE_MEASURED_SUPPORTED\`, \`EXTERNAL_ERA_CANDIDATE_UNCERTAIN\`, \`PHYSICS_CONFLICT_HOLD\` or \`EVIDENCE_INSUFFICIENT_HOLD\`, with event ID, original source SHA, justified method and validation uncertainty. \`APPROVED_FOR_NEW_VERSION\` is currently **false** for ALL. Provide choices (strict HOLD, verified bounded research candidate, low-confidence sensitivity-only exploratory input) for the user's *manual* acceptance, rather than silently filling everything.

## 4. Existing primary source and research evidence locations

**Exact IRIDIS6 root:** \`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03\`. Confirm existence and SHA receipts in the runtime; paths are from previous audited run records, not a live mount read in this handoff.

- \`qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json\` — exact original site \`primary\`, companion \`era\`, original SHA and selected release. **Do not guess raw CSV location.**
- \`qcv5_native_trial_20261022T024559Z_36c46e58/INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP\` — original hold marker, must preserve.
- \`science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f/US-NR3_STAGE12G_INCOMPLETE_NOLEAP.csv\` — latest **verified common-ensemble NR3 selected candidate** with 238 missing, not model admitted.
- Same Stage12G dir: \`six_site_stage12g_science_status.csv\`, \`2810_original_missing_year_source_review_after_stage12g.csv\`, \`stage12g_research_only_sha_receipt.json\`, \`INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP\`.
- \`reports/stage10d_humidity_manual_triage_20261024T042016Z_7fa50aaa/\` — \`all_1924_manual_review.csv\`, \`site_triage_summary.csv\`, \`consecutive_event_clusters.csv\`, \`A_water_failure_27.csv\`, \`B_ice_supersaturation_78.csv\`, signed science receipt.
- \`reports/stage10g_source_qc0_7day_20261024T045334Z_691519c6/\` — site-year original measured QC coverage and absence of within-seven-day dual QC0 brackets.
- \`reports/stage10h_original_source_provenance_20261024T054425Z_faf342a8/\` — \`US-NR3_2017_2018_2023_source_qc.csv\`, \`affected_years_source_qc_distributions.csv\`, \`read_only_provenance.json\`.
- \`reports/stage10i_era_vpd_physics_20261024T055509Z_b5a44de8/\` — original same-release ERA saturation test, signed receipt.
- \`reports/stage10b_external_humidity_20261024T040142Z_be6a9d78/\` and \`reports/stage10c_independent_cold_humidity_20261024T041355Z_36d578f4/\` — grid A/B candidate physics.
- \`reports/stage10k_exception_provenance_20261024T061150Z_13a3a08a/exception_2_US-NR3_events.csv\` — two 2018 source-grid algebra exceptions and original row ids.
- \`external_evidence/era5land_timeseries/\` — previous separate ERA5-Land evidence files; source-year receipt coverage to be verified; ERA5-Land is ERA5-driven, not independent tower observation.

**GitHub original executable and explanatory material** (do NOT modify original scripts without a distinct source and SHA):
- [Ten sites, exact release](../sites.tsv)
- [2026-10-29 manual ten-site status](MANUAL_HOLD_TRIAGE_AND_TEN_SITE_STATUS_20261029.md)
- [10-site signed summary](BATCH03_TEN_SITE_CURRENT_STATUS_20261026_1939UTC.md)
- [Stage12AI nine-site numerical baseline](STAGE12AI_20261026_TEN_SITE_STATUS_AFTER_KON_12AH.md)
- [Original physics/P0-P4](SCIENTIFIC_REVIEW_STATUS_2026-10-24.md)
- [Stage10F/G/H/I/K and source QC0 provenance](STAGE10E_TO_10G_QC_EVIDENCE_2026-10-24.md)
- [Stage10K formal science gate](STAGE10K_SCIENTIFIC_DECISION_GATE_2026-10-24.md)
- [Stage12G original source-only trial](../scripts/stage12/12g_apply_new_year_ERA5Land_RH_shadow.py) — Git blob \`14eabe09a56614808d6186d88fa5576233ed240b\`.
- [Stage10H native timestamp-keyed QC audit](../scripts/stage10/10h_v2_timestamp_keyed_qc_provenance.py) — Git blob \`f36a4bbfa98cd70b7e6690083b9a0c70c69766c4\`.
- [Stage10I original ERA water saturation audit](../scripts/stage10/10i_source_ERA_vpd_saturation_audit.py) — Git blob \`2636a3baec42560d774a8dfa3a723032b87326a1\`.
- [Stage10K exact exceptional source audit](../scripts/stage10/10k_exception_provenance_science_gate.py) — Git blob \`04039542bb08c13df7b971a013b0cc72174199af\`.
- [Official AmeriFlux site/BADM/photo and data citation](https://ameriflux.lbl.gov/sites/siteinfo/US-NR3); [FLUXNET-1F release DOI](https://doi.org/10.17190/AMF/3365271); [BASE dataset DOI](https://doi.org/10.17190/AMF/1804491).

## 5. Requested handoff deliverables from the higher-reasoning model

Produce, preferably in one coherent science package:

1. **One overview**: original FLUXNET-1F version + tower BADM time/elevation/provenance; why NR3 should be categorized hard, without invented facts.
2. **\`US_NR3_238_missing_current_stage12g_ledger.csv\`**: exact 238 original native keys, year/month/continuous episode, missing VPD/QBOT or other field, parent Stage12G reason/ancestor receipt, source QC, existing gridded year coverage, potential method and decision. Verify the 238 count instead of assuming old summary equals new status.
3. **\`US_NR3_1484_source_QC2_thermodynamic_anomaly_matrix.csv\`**: exact source key and original row, \`TA_F/TA_F_QC, VPD_F/VPD_F_QC, TA_ERA,VPD_ERA,T2m,D2m,PSRF\`, \`es_w,es_i,e_a,RH_w,RH_i,VPD,QBOT\`, phase cautions, temperature/grid difference, proposed alternative and independent evidence status. Reconcile overlap with 238; preserve original 2018 exception row IDs 195333/195334.
4. **Year/source trust table**: especially 2017, 2018, 2023 original all-QC2 and any actually available contemporaneous measured BASE, BADM or neighbor QC truth, with original hash, time offsets, height and accepted uncertainties.
5. **Decision options matrix**: per anomaly episode/source-year, physically valid vs independently empirically supported vs source-only uncertain vs strict HOLD; quantify exact eligible count and residual HOLD without forced all-year fill, annual/blocked-day QC0 validation where possible.
6. **Short human science memo** with recommended action, unresolved evidence, accepted model-risk if alternatives considered. **No scripts that write/overwrite the original, no selected shadow changes, no production forcing, no Slurm jobs unless later explicitly authorised.**

**First action in next conversation:** read this handoff and actual SHA-verified IRIDIS6 receipts, then **only a read-only grouped inventory** to reconcile Stage10/Stage12 counting identities. Report the old-vs-new source versions and missing raw files, if any, before proposing a method. Never report implementation success based solely on an old GitHub summary.

## 6. New model paste-ready instruction

> Please continue the advanced US-NR3 scientific analysis in the AmeriFlux Batch03 repository, using this exact handoff: https://github.com/lyanyeung/CLM-FATES-single-site-workflows/blob/main/examples/AmeriFlux_MultiSite_10_Batch03/docs/US_NR3_ADVANCED_MODEL_SCIENTIFIC_HANDOFF_20261029.md . US-MtB belongs to Claude and US-Me6 has a separate manual HOLD decision. Restrict yourself to US-NR3 and READONLY original provenance, actual 238 missing vs 1,484 anomalous source-QC2 events, full-year no-QC0 2017/2018/2023, original ERA negative vapour pressure, high-alpine ice/temperature/height physics, native clock and independent truth validation. Return the exact reconciled 238-ledger, 1484 anomaly evidence matrix, source-year confidence, rigorous proposed alternatives and human decisions; do not write model forcing, do not submit Slurm/AD400, do not silently relax physics or override original QC0.
