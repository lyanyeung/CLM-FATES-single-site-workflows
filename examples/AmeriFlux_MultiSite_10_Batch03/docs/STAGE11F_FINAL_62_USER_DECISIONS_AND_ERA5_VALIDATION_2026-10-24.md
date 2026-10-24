# AmeriFlux Batch03 — final 62 Stage11f user-selected review directions

**Date:** 24 October 2026.  
**Document type:** User-decision ledger, **not a completed physical forcing repair or approved Post-v5 simulation input**.  
**Supersedes unresolved decision statuses** in [the previous 59-of-62 decision snapshot](STAGE11F_USER_REVIEW_DECISIONS_2026-10-24.md), which is intentionally preserved for historical provenance.

## Decisions the user explicitly made

The six originally measured-flagged QC0 air-temperature events will **retain the already-produced Stage07 interpolated TA candidate values**. The user previously selected **ERA5-based humidity replacement** for source temperature/VPD records producing nonpositive implied actual vapour pressure and for all five Stage07 positive but RH<1% records, with one event appearing in both scientific categories. The user has now explicitly instructed that the **remaining three original-positive, near-zero-vapour VPD records retain their existing Stage07 candidate humidity values**, rather than be replaced or reverted again.

| Mutually exclusive outcome | Event IDs | Status of USER decision | Status of IMPLEMENTATION |
| --- | ---: | --- | --- |
| Keep existing Stage07 corrected/interpolated air temperature at six original source QC0 events | **6** | Decided | Current Stage07 candidate is already present; no new files written |
| ERA5-based humidity replacement method for source nonpositive implied water vapour | **49** | Method direction decided | Exact ERA5 product, VPD/RH conversion, compatibility and physical audit pending |
| ERA5-based humidity replacement method for other candidate RH<1% events | **4** | Method direction decided | Exact product/method and scientific validation pending |
| **Keep existing Stage07 VPD** at the three positive-but-near-zero source vapour events | **3** | **New explicit decision** | Current Stage07 candidate retained unchanged; no new files written |
| **Total** | **62** | **62/62 selected** | **No new forcing / Post-v5 / DATM / spinup approvals** |

The five positive RH<1% records include one source-negative-VPD-pair event (`US-NC2 202503181900 VPD_F`) already counted in the 49 source nonpositive implied-vapour cases, hence 53 **unique** selected ERA5-humidity event IDs.

### The three latest decisions — KEEP Stage07 candidate

| Station | Original native HH key | Variable | Original QC | Stage07 candidate RH over water | Explicit user selection |
| --- | --- | --- | ---: | ---: | --- |
| US-Mpj | **201410210830** | `VPD_F` | QC1 | 81.079% | KEEP existing Stage07 `VPD_USE` |
| US-NC2 | **202503220130** | `VPD_F` | QC1 | 58.708% | KEEP existing Stage07 `VPD_USE` |
| US-NC2 | **202503270730** | `VPD_F` | QC1 | 79.776% | KEEP existing Stage07 `VPD_USE` |

These three source values had **positive but near-zero implied water vapour**, not negative actual vapour pressure. Their higher candidate RH results were obtained through Stage07 ERA-RH reconstruction at retained site TA. Retaining the existing candidate is a documented USER decision; there is no claim of independent measured validation.

### Six original QC0 T candidates — retain as previously chosen

| Station | Native key | Stage07 retained candidate T (°C) |
| --- | --- | ---: |
| US-MOz | 201603172200 | 12.1715 |
| US-Mpj | 202002110630 | 1.1795 |
| US-NC2 | 201901031300 | 13.3525 |
| US-NC2 | 201901040330 | 9.3935 |
| US-NC2 | 201901041630 | 9.5665 |
| US-NC2 | 201901080330 | 7.5215 |

These values are original-sealed Stage07 products. The underlying source QC0 identity and neighbour QC should remain visible in every subsequent scientific summary.

## Machine-readable 62-event versioned decision ledger

[**STAGE11F_ALL62_USER_DECISIONS_2026-10-24.csv**](STAGE11F_ALL62_USER_DECISIONS_2026-10-24.csv) contains exactly **62 unique** source-native `(site,native_key,variable)` keys, disjoint method classes (6/49/4/3), the user's explicit choice and **false** for all model-readiness flags. All 62 event IDs are based on the operator's previously verified Stage11f source report and [fully printed human review rows](STAGE11F_VERIFIED_HUMAN_REVIEW_QUEUE_2026-10-24.md).

**The CSV and Markdown ledger are hosted on GitHub; the user's existing IRIDIS working copy is NOT automatically updated by this repository change.** Stage11f SHA-sealed originals and original forcing remain unchanged. A separate script checks exactly these 62 IDs against the sealed on-cluster record and fails rather than generating a new candidate if they differ.

## Stage11g — actual companion ERA5 provenance and physical feasibility audit

Script: [**11g_user62_ERA5_source_method_audit.py**](../scripts/stage11/11g_user62_ERA5_source_method_audit.py).

**Committed; NOT YET RUN on IRIDIS6.** It will:
- Verify Git blobs of the selected human-decision CSV and the previously verified Stage11c source-audit module; compare 62 event IDs to the SHA-sealed Stage11f original, without mutating either.
- Reopen only previously SHA-verified Stage07 source flux/companion ERA datasets and the existing three-site Stage07 candidate forcing, by **exact source-native timestamp keys**.
- For each of 53 events directed to ERA5 humidity replacement, evaluate **(A)** whether direct use of original companion `VPD_ERA` at retained site TA is mathematically admissible, and **(B)** whether the companion source's `TA_ERA/VPD_ERA` yields a valid humidity fraction which can be transferred to retained site TA, deriving VPD and QBOT using the existing Stage07 pressure.
- Flag invalid companion ERA pair or source humidity, missing evidence, negative/nonpositive actual vapour pressure, incoherent QBOT, incompatible temperature/pressure. No clipping, RH 1% floor or silent record replacement.
- Preserve the nine KEEP-Stage07 selections (six TA and three VPD) unchanged and list their exact current VPD/RH/QBOT.
- Explicitly report **NOT EVALUATED** for a separate gridded ERA5-Land T2m/dewpoint alternative: there is currently no verified original grid T/Td pairing for these three sites in this decision scope.

This is a *source/method feasibility assessment*, not independent tower truth. The two companion methods can yield different humidity values, especially at different source versus site temperatures. **The user's label “ERA5” does not by itself identify whether the intended dataset is site-downscaled release companion ERA5 or independently extracted ERA5-Land**. Do not assume they are interchangeable; select and freeze one documented exact-source formulation after the actual method audit.

**Do not treat a physical pass as a Post-v5 approval.** Full-year variability/QC, clock offset, height/elevation, PFT/surface mapping, CO2 policy, sensitivity and scientific sign-off are still separate prerequisites.

## Invariants and current status

**All 62 choices are recorded. No remaining undecided Stage11f priority IDs.** This does **not** extend to the seven other AmeriFlux Batch03 sites or their **1,924 Stage08–10 humidity blocker records**.

- User-method selections: **6 KEEP existing Stage07 TA / 53 ERA5 humidity method / 3 KEEP existing Stage07 VPD**.
- Verified new ERA5 humidity values actually written: **0**.
- Newly permitted official Post-v5 sites: **0**.
- DATM / spinup authorizations: **0**.
- Original Stage07 `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker retained; source/Stage07/Stage11e/Stage11f hash-sealed data untouched.
