# Batch03 Stage13c — 24 manual issues: original tower vs ERA5, 2026-10-26

> **2026-10-26 OPERATOR DECISION AFTER THIS REPORT:** All six specific source-T QC0 edits listed in section A were explicitly **APPROVED** using the existing two-sided original tower linear interpolation values. The original measured CSV and prior Stage07 science-only trial remain immutable. The 18 VPD manual-review records, US-NC2 2025 time/ERA source HOLD, broader Post-v5 acceptance, DATM and spin-up are **NOT APPROVED**. See [machine-readable scoped decision](../decisions/STAGE13D_OPERATOR_APPROVED_SIX_QC0_TOWER_TA_INTERPOLATIONS_20261026.json). In the historical tables below, any `PENDING` operator status for these exact six TA edits is superseded by this dated decision only; no other status is changed.

**Status:** SCIENTIFIC RECOMMENDATIONS ONLY. **0** operator approvals recorded. No DATM/spinup authorisation. **6** originally tower-QC0 TA_F edits; **18** Stage07 VPD manual-review items. Stage13c 24-event native ±2-hour context checked against the actual SHA-pinned original tower, paired ERA5 and Stage07 processed candidate; source timestamps verified complete for the three sites.

Source-of-truth on IRIDIS6:
- \`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13c_24_manual_original_tower_ERA_TA_context_20261026T171801Z_bed5a936\`
- Original Stage07 isolated candidate: \`qcv5_native_trial_20261022T024559Z_36c46e58\`
- Stage13b source ledger: \`reports/stage13b_THREE_NUMERIC_SITES_QC0_AND_MANUAL_DECISIONS_20261026T170134Z_06af8b8e\`
- Full original/native hourly context for *every* one of the 24 centers is in the Stage13c CSVs; this Markdown records the scientifically salient ±30-minute context plus the 2025 VPD triage. Source records and provenance receipts remain on IRIDIS6.

## A. Six original QC0 temperature changes — operator decisions requested

TA in °C; columns list \`−30 / CENTER / +30 minutes\`. ERA5 denotes the original standalone companion, **not** an independently validated substitute; the model candidate uses two-sided original tower linear interpolation. All six source center flags were misleading \`TA_F_QC=0\` (measured good), despite their large isolated negative spikes.

| Site and source-native center | Original tower TA: −30 / CENTER / +30 | Standalone ERA5 TA: −30 / CENTER / +30 | Current interpolated candidate | Center minus average neighboring tower TA | Scientific recommendation | Operator status |
|---|---|---|---:|---:|---|---|
| US-MOz 2016-03-17 22:00 | 13.382 / **−15.213** / 10.961 | 10.402 / 9.601 / 9.232 | **12.1715** | −27.3845 | **Recommend APPROVE tower interpolation**; obvious isolated spike, nearby tower & ERA5 continuous | PENDING |
| US-Mpj 2020-02-11 06:30 | 1.176 / **−17.667** / 1.183 | −3.797 / −3.869 / −3.941 | **1.1795** | −18.8465 | **Recommend APPROVE tower interpolation**, **not** ERA replacement (ERA is ~5 °C colder throughout; adjacent tower QC1) | PENDING |
| US-NC2 2019-01-03 13:00 | 13.567 / **−6.759** / 13.138 | 12.015 / 12.537 / 12.579 | **13.3525** | −20.1115 | **Recommend APPROVE tower interpolation** for this specific outlier | PENDING |
| US-NC2 2019-01-04 03:30 | 9.437 / **−14.342** / 9.350 | 9.727 / 9.524 / 9.321 | **9.3935** | −23.7355 | **Recommend APPROVE tower interpolation** for this specific outlier | PENDING |
| US-NC2 2019-01-04 16:30 | 9.058 / **−13.804** / 10.075 | 11.168 / 11.016 / 10.864 | **9.5665** | −23.3705 | **Recommend APPROVE tower interpolation** for this specific outlier | PENDING |
| US-NC2 2019-01-08 03:30 | 6.829 / **−11.506** / 8.214 | 9.294 / 10.410 / 11.526 | **7.5215** | −19.0275 | **Recommend APPROVE tower interpolation** for this specific outlier; separate later tower discrepancy remains | PENDING |

**Additional independent issue:** US-NC2 2019-01-08 **05:30** tower temperature 3.274 °C vs ERA5 12.108 °C after the 03:30 fixed outlier, while neighboring tower 05:00 was 9.068 °C. This is *outside* the six edits; flag it for targeted source-QC review, do not silently change.

### Operator decision options

- **A.** Approve all six **specific** QC0 TA_F tower-interpolation candidate values, while retaining any other VPD/clock/PFT science HOLDs.
- **B.** Approve **US-MOz and US-Mpj only** (two modifications) to prioritise two site preflights; retain four US-NC2 changes on HOLD.
- **C.** Continue HOLD for all six; leave candidate files untouched.

**Approval is not inferred from an assistant recommendation.** Never edit immutable original tower CSVs; an operator-approved change must be recorded in a separate versioned forcing/receipt with all source/selected SHA identities before Post-v5/DATM.

## B. Original 18 VPD manual-review records

The source driver signed these under Stage07; summaries and center temperatures from Stage13c. T, ERA TA °C; VPD in hPa. Original VPD values are not all original tower observations (in some rows exactly equal to standalone \`VPD_ERA\`), which is an important provenance/clock question.

| Site | Timestamp | Reason | Tower T / ERA T | Original tower VPD → Stage07 candidate | Scientific disposition |
|---|---|---|---|---|---|
| US-Mpj | 2014-10-11 02:30 | Large/measured VPD reconstruction | 1.065 / 6.654 | 8.245 → 1.032 | **Candidate physically plausible**; original > saturation at tower T; verify source time and adjacent VPD |
| US-Mpj | 2014-10-11 04:30 | Large/measured VPD reconstruction | 3.883 / 6.233 | 8.170 → 1.163 | **Candidate physically plausible**; original near/exceeds saturation; verify source time and adjacent VPD |
| US-Mpj | 2014-10-21 08:30 | Near-zero vapour pressure; repaired ERA RH | 8.530 / 8.473 | 11.018 → 2.103 | **Candidate scientifically plausible** (T agrees with ERA); confirm native adjacent VPD |
| US-Mpj | 2018-02-02 17:30 | Very low but positive RH preserved | 8.822 / 12.225 | 11.261 → 11.261 | **No source change.** Flag extreme low RH, don't blindly ERA-replace |
| US-Mpj | 2018-02-02 19:00 | Very low but positive RH preserved | 5.798 / 9.390 | 9.178 → 9.178 | **No source change.** Flag extreme low RH, don't blindly ERA-replace |
| US-NC2 | 2025-02-07 16:30 | Large/measured VPD reconstruction | 8.759 / 19.909 | 17.446 → 8.475 | **HOLD**; tower/ERA ΔT ≈11.15 °C and 2025 source time/ERA investigation |
| US-NC2 | 2025-02-07 17:30 | Large/measured VPD reconstruction | 12.091 / 18.655 | 15.491 → 10.163 | **HOLD**; tower/ERA ΔT ≈6.56 °C and source uncertainty |
| US-NC2 | 2025-03-11 18:30 | Large/measured VPD reconstruction | 12.677 / 20.339 | 16.478 → 10.118 | **HOLD**; tower/ERA ΔT ≈7.66 °C |
| US-NC2 | 2025-03-11 19:00 | Large/measured VPD reconstruction | 11.092 / 20.151 | 16.971 → 9.496 | **HOLD**; tower/ERA ΔT ≈9.06 °C |
| US-NC2 | 2025-03-11 19:30 | Large/measured VPD reconstruction | 9.654 / 18.747 | 14.319 → 7.943 | **HOLD**; tower/ERA ΔT ≈9.09 °C |
| US-NC2 | 2025-03-21 19:00 | Large/measured VPD reconstruction | 7.578 / 13.690 | 13.360 → 6.964 | **HOLD**; ERA5/Tower ΔT ≈6.11 °C |
| US-NC2 | 2025-03-23 06:30 | Large/measured VPD reconstruction | 2.508 / 7.544 | 10.271 → 1.552 | **HOLD**; ERA5/Tower ΔT ≈5.04 °C |
| US-NC2 | 2025-03-23 07:00 | Large/measured VPD reconstruction | 5.189 / 7.510 | 11.430 → 1.752 | **HOLD**; source time and ERA provenance still unapproved |
| US-NC2 | 2025-03-22 01:30 | Near-zero vapour pressure; repaired ERA RH | 2.166 / 8.589 | 7.101 → 2.949 | **HOLD**; tower/ERA ΔT ≈6.42 °C |
| US-NC2 | 2025-03-27 07:30 | Near-zero vapour pressure; repaired ERA RH | 6.278 / 2.827 | 9.489 → 1.927 | **HOLD**; explicit provenance/clock resolution needed |
| US-NC2 | 2025-03-18 19:00 | Very low but positive RH preserved | 8.664 / 15.284 | 11.591 → 11.198 | **HOLD**; Stage07 candidate VPD actually differs from original here; this is NOT an unchanged row |
| US-NC2 | 2025-03-23 12:30 | Very low but positive RH preserved | 18.135 / 16.537 | 20.621 → 20.621 | **No source change**; low-RH caution |
| US-NC2 | 2025-03-25 09:00 | Very low but positive RH preserved | 16.214 / 13.385 | 18.405 → 18.405 | **No source change**; low-RH caution |

**Important correction**: Stage13b's category \`very_low_but_positive_RH_preserved_review\` does NOT universally mean "no change". Stage13c shows **US-NC2 2025-03-18 19:00** changed from original VPD 11.591 to selected 11.198, so it remains on HOLD. This may involve a different Stage07 QC step; no unsupported attribution.

## C. Site-level immediate actions

| Site | Native timestamp & numeric check | QC0 TA changes | Stage07 VPD manual records | Next action |
|---|---|---:|---:|---|
| **US-MOz** | 0 missing; current Stage13a numeric pass | 1 | **0** | Obtain operator QC0 approval (A/B) → immutable Post-v5 candidate check; verify PFT, ZBOT, source clock → isolated DATM/case preflight |
| **US-Mpj** | 0 missing; current Stage13a numeric pass | 1 | **5** | Obtain operator QC0 approval and review 3 VPD altered candidates; preserve 2 low-RH unchanged source values |
| **US-NC2** | 0 missing; current Stage13a numeric pass | 4 | **13** | 2025 ERA/time/source and full Post-v5 science HOLD; do not authorise simulation |
| Six other non-Kon Batch03 sites | Stage07 numerical forcing blocked | — | — | Batch triage separately from nearest-to-ready MOz/Mpj |
| US-Kon | Stage12ay sealed research 77 humidity missing | — | — | Not a runnable forcing; do not block other sites |

No model, Slurm, production forcing, source timestamps, QC flags, or DATM input has been changed by this report.
