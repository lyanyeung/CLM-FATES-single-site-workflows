# US-MMS — efficient manual source triage of 16 selected hourly gaps (Batch03)

**Prepared 2026-10-29.** This is a human-review decision rule and an executable one-pass *read-only* source report, not a claim that IRIDIS6 has run it, a new applied repair or a Slurm job.

## Why US-MMS next

US-MtB has the explicit delegated Claude workstream, US-NR3 is reserved for higher reasoning, and US-Me6 has an independent 19-HH cold-event science HOLD. Of remaining incomplete sources, US-MMS is the most compact current finite-forcing hole: the **US-MMS FLUXMET_HR 1999–2023 release is hourly** (60 minutes, **219000** NOLEAP records), not HH; last signed Stage12G/Stage12AI selected meteorology has exactly **16 native hourly missing VPD_USE and QBOT values**, with no other missing source-meteorology time row in that report. US-MMS is not yet Post-v5/DATM/model ready.

Historic Stage12E/12G separates these 16 into **15 missing already-verified ERA5-Land source-year record instances** plus **one previously protected original physical science HOLD** (Stage12G has no approved new US-MMS source-year data). Independently, Stage10D/10H/10I earlier examined **18 original hourly cold source anomalies**, all original source \`VPD_F_QC=2\`, matching paired source \`VPD_ERA\` at the same time; their paired \`TA_ERA/VPD_ERA\` gives **negative actual water vapour e = es_water(TA_ERA)−VPD_ERA**. These 18 events are a *different scope* from current selected 16 missing hour rows. Whether they overlap must be found by exact original native timestamps, **do not add 16+18**.

Stage10B/C alternative A (ERA5-Land dewpoint-derived absolute e) was water physically valid 18/18 with 2 potential ice-supersaturation cases; alternative B (gridded water RH at retained T) passed liquid-water 18/18 with 1 ice-phase caution. These are *old diagnostic candidates* with limited independence and no approval. Stage10F/G for the single US-MMS high-priority episode had **zero** dual measured T/VPD QC0 flank anchors within 7 days. Do not infer direct tower humidity from QC1/QC2/MDS or grid values.

## One-pass manual evidence and explicit dispositions

Run the single SHA-checked phone launcher once on an IRIDIS6 login; it verifies exact original Stage07 source SHA, Stage12G signed selected US-MMS shadow/holds and Stage10D 18-event receipt; then reconstructs original/native **+/-2 hours** of tower \`TA_F/TA_F_QC,VPD_F/VPD_F_QC\`, exact same-release \`TA_ERA,VPD_ERA\`, retained site \`TA_USE,PSRF\` and previous/next selected VPD. It prints and saves:
- \`US_MMS_16_missing_hour_manual_science_decisions.csv\`: **exactly 16 hourly rows**, 15 source-year shortage vs one original science hold, source QC, signed historical-18 overlap, water e, RH_w, RH_ice, QBOT and bounded companion-ERA RH mathematical *preview* only if ERA is physically valid.
- \`US_MMS_16_hour_neighbours_plusminus2h_original_ERA.csv\`: **four context hours** per missing row with raw measured/QC/ERA and selected VPD.
- \`US_MMS_18_historical_negative_ERA_e_overlap.csv\`: exact **18 original source anomalies**, negative paired same-release ERA water vapour and overlap with current 16, retained as source science warnings.
- \`US_MMS_onepass_16hour_manual_evidence_summary.json\` and SHA receipt.

**Manual decision rules (not approvals):**

1. All 18 historic original same-release \`e_ERA<0\`: original QC2 and exact paired ERA VPD scientifically unsuitable for direct humidity use; **HOLD** any repair that would reuse the invalid source pair, whether or not selected forcing is finite. This does not mean 18 new missing records.
2. The **15 currently unverified ERA5-Land source-year slots**: first test original measured tower RH/T/VPD QC0 at exact times and nearest neighbours, if any; never claim an external gridded year is verified when absent. A physically valid original same-release companion RH transfer may be printed as **research candidate ONLY**, not adopted. Prefer a single bounded original-source-quality evaluation instead of blindly downloading years.
3. The **one separately protected physics HOLD**: preserve missing; inspect exact original source/time, near-hour QC0 T/VPD, water/ice and original ERA physical state. Never override previous immutable Stage12B hold without new independent evidence and explicit scoped user approval.
4. Each candidate requires \`e_s(T_site)−VPD > 0\`, \`RH_water\` physically plausible, \`QBOT = 0.622 e_Pa/(PSRF−0.378 e_Pa)\` finite and consistent, \`RH_ice\`/installed model saturation compatibility at T<0C, source/QC provenance, and physically defensible adjacent **one-hour** VPD changes. Do not create fake 30-minute midpoints.
5. **No automatic approval**: \`RESEARCH_ONLY_COMPANION_RH_PHYSICALLY_POSSIBLE\` means merely algebraically possible. Even measured-QC0-like source fields require original timestamps/source verification and a final human decision before a new versioned isolated research shadow. Check actual 16/18 outputs before any subsequent fix.

## Existing exact source paths and methods

Root: \`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03\`.

Original exact FLUXMET_HR (1999–2023) and paired ERA file paths with full SHA must be extracted from:
\`qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json\`.
Do not guess raw FLUXMET filenames or replace these paths with generic ERA5.

Signed selected input:
\`science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f/US-MMS_STAGE12G_INCOMPLETE_NOLEAP.csv\`.
Same folder \`stage12g_research_only_sha_receipt.json\`, \`2810_original_missing_year_source_review_after_stage12g.csv\`, \`six_site_stage12g_science_status.csv\`, \`INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP\`.

Original events:
\`reports/stage10d_humidity_manual_triage_20261024T042016Z_7fa50aaa/all_1924_manual_review.csv\`, original signed \`read_only_provenance.json\`; 18 US-MMS source rows inside the earlier seven-site 1,924-event manual ledger.

Existing science references:
[Stage12AI 10-site 16-hour count](STAGE12AI_20261026_TEN_SITE_STATUS_AFTER_KON_12AH.md),
[Stage12G no new US-MMS gridded years](STAGE12G_NINE_YEAR_138_REPAIRS_AND_STAGE12M_NON_MTB_HOLD_DIAGNOSIS_2026-10-25.md),
[Stage10E–10K ERA negative-e and source QC classification](STAGE10E_TO_10G_QC_EVIDENCE_2026-10-24.md),
[Stage10B–D water/ice candidate evidence](SCIENTIFIC_REVIEW_STATUS_2026-10-24.md).

**Reproducible code**:
[Stage14B one-pass full original source manual review](../scripts/stage14/14b_US_MMS_16hour_manual_onepass_READONLY.py) (Git blob \`d6bd10b5d125f4d8daeb01071af7bfa26f82f4f5\`),
[Stage14B mobile fixed one-click launcher](../scripts/stage14/14b_US_MMS_16hour_manual_onepass_MOBILE.sh), pinning source commit \`1b6b463c47f42707e45a070d74e73f020c577460\` and SHA.

## Actual state and exit condition

As of this writing **Stage14B is committed but NOT executed on IRIDIS6**. The observed full-site source still has **16 hourly VPD/QBOT gaps and no Post-v5/AD400 admission**. An immediate subsequent operator output must show the actual native 16 rows; review all in ONE human decision, not an endless 14C/14D/... re-tuning cycle. A defensible science decision can keep some gaps if actual observation is unavailable; complete number filling is not the same as verified model forcing.

No original source/ERA/previous shadow, no model input, no GitHub earlier science ledgers, no active cases/Slurm jobs are modified by this read-only assessment.


## 2026-10-29 final human adjudication after actual 48-hour original FLUXMET/MDS check

**Operator ran Stage14B on IRIDIS6 and then the exact 2014-09-22 00:00–2014-09-24 00:00 original 48 hourly FLUXMET/MDS window plus current selected source review. This is an evidentiary MANUAL DISPOSITION, not a new source modification.**

- Exact 2014 source window: **48 hourly records, 47 original VPD_F_QC1 and one VPD_F_QC2; zero original VPD QC0, zero original VPD_F_MDS_QC0**. At the displayed early-morning samples original VPD_F_MDS==VPD_F with matching QC1; no independent observed humidity anchor was obtained. **16 of 47 VPD QC1 hours** give water-based derived RH<15%, including the **five already missing** original negative-RH hours; **11 additional finite** selected values in that two-day window are extremely dry (QC1) and are retained as **SCIENTIFIC_QC_WARNING**, not silently deleted.
- Exact transition example 2014-09-22 11:00 (original VPD QC1; site T 13.874 C, VPD 15.389 hPa, derived RHwater 2.870%) -> 12:00 (original QC2; site T 15.239 C, VPD 7.116 hPa, RHwater 58.878%). It would be scientifically unsound to treat this QC1/QC2 discontinuity as a trusted VPD boundary or smooth five 2.47–4.12 hPa ERA-RH *preview* values to an apparent 12–16 hPa desert-like QC1 plateau. The abrupt transition alone is not proof of bad meteorology, but provenance plus absent measured corroboration forbids a validated repair.
- Stage14B **16 current missing hourly positions**, all original VPD values invalid at retained site temperature by water vapour e=esw(T_site)−VPD <0: **2000-03 6 source T QC1 plus 9–12 C source/grid discrepancy = HOLD; 2014-09 5 T QC0+VPD QC1 original water-negative and source QC0 absent = HOLD, keep five ERA-RH alternatives as unapproved diagnostic only; 2015-02-24 07:00 1 original QC2 water-negative ERA pair = HOLD; 2019-01-30 10:00–13:00 4 original QC2 ERA water-negative = HOLD.** Zero approved new numeric replacements.
- Historical Stage10D **18 raw ERA-negative-e original events**, one overlaps latest 16 missing; the other **17** were checked in the selected Stage12G site: **all 17 currently finite VPD_USE/QBOT pairs are physically water-consistent** and one is still NaN. That is a **water-closure test**, not independent measured RH confirmation. Do not count those 17 as repaired by this adjudication or add 18 to missing 16.
- **FINAL MANUAL SCIENCE STATUS: CLOSED_WITH_16_MISSING_HOURS_AND_QC1_WARNING**. For efficiency STOP further post-hoc RH regression, matched-window tuning, and repeated extra 'Stage' scripts for this site unless a genuinely different measured source becomes available. Do not release US-MMS Stage12G as Post-v5, DATM, AD400 or production-ready. Do not overwrite source, selected shadow, 47 QC1-hour data, or prior signed science receipts. Preserve audit and document the 11 additional low-RH finite QC1 warnings for any future site-wide scientific release gate.

**Operator-supplied final source result:** 2014 original 48-hour data: 0 VPD_QC0, 47 VPD_QC1, 0 MDS_QC0, 5 selected missing and 16 QC1 calculated RH<15%; current selected original Stage10D 18 raw-negative event overlay water-closure **17/18 PASS**, 1 originally protected 2015-02-24 07:00 remains missing. No source or Slurm writes.

Next lower-friction Batch03 site to review: **US-Mpj**, current research source numerically complete but still pending PFT, original VPD physics and formal production scientific admission. US-NR3 is separately reserved for advanced reasoning and US-MtB for Claude.
