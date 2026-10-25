# Batch04 — VERIFIED independent full-source audit of manual 3-temperature research candidate

**Status (2026-10-25): IRIDIS6 OPERATOR-VERIFIED PASS, COMPLETE 2/2 candidate site files, 3/3 native half-hours, exactly 9 changed field cells.** This page records the user's successful read-only output from [pinned full-CSV audit code](../scripts/manual_review/verify_manual_three_T_trial_full_source_readonly.py); it does **not** claim the repository itself ran on IRIDIS6, and does **not** authorize publication or production CIME forcing.

## Provenance, case and source integrity

| Candidate site | Native HH rows completely compared to Stage14 | Changed native HH | New *candidate full-CSV* SHA256 |
| --- | ---: | ---: | --- |
| **US-SP1** | **368,208** | **2** | `96d8c6ad2a082bb243160ee91c2aee0d2fcd3dc0a862515519c34dab2fa664d3` |
| **US-SRG** | **315,600** | **1** | `d65523022718819d7013d79f1015fe419958078a8d1fde4f062fa8470929933f` |

The trial sits at:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_temperature_alternative_not_approved/candidate_20261025T183441Z_254f8181
```

The independent audit checked:
- **2/2** Stage14-versus-candidate full native CSV pairs, aligned row by row.
- **3/3** explicit native HH timestamps, with **exactly three changed fields each**, `TA_F`, `TA_F_QC`, `VPD_F`, and **no other field or timestamp differences**, across **683,808 HH rows** total. **9 changed field cells overall.**
- Source, candidate, receipt and ten-site manifest SHA256/pinning; exact **8/8 other-site manifest rows identical**.
- Stage14 RH retained at each event and **TA/RH/VPD saturation physical closure**.
- Originally QC0 tower temperature is retained **unchanged in Stage14 and original FLUXNET**. In new research-only candidate changed fields use **trial QC2** because the proposed replacement is ERA-derived, never a new observed tower temperature.

## Exact researcher-requested manual alternative

| Site, native local standard HH | Original TA_F °C / QC | New research TA_F °C / QC | Trial VPD_F hPa | Replacement source |
| --- | --- | --- | ---: | --- |
| US-SP1 2000-10-09 18:00 | −6.900 / 0 | **14.370813 / 2** | **10.194556** | Existing separately receipt-verified ERA5-Land T2m, UTC half-hour aligned |
| US-SP1 2000-10-09 18:30 | −7.100 / 0 | **13.776224 / 2** | **9.445459** | Same ERA5-Land data and native clock |
| US-SRG 2019-03-19 12:00 | 0.718 / 0 | **20.136500 / 2** | **17.060332** | Linear midpoint between 11:30 **19.668°C/QC2** and 12:30 **20.605°C/QC2** consolidated values |

**Important: US-SRG's interpolated flanks are already ERA-substituted QC2 values**. That choice does not constitute independent raw tower validation. The US-SP1 2000 values differ from the separate Stage15 two-point *flanking-tower interpolation* scenario and should remain distinct scenarios.

## Verbatim completion evidence

```text
MANUAL FULL AUDIT SELF-TEST PASS: exact three HH, expected 9 cells, immutable source contracts
MANUAL AUDIT SITE VERIFIED US-SP1 source_rows 368208 modified_HH 2 new_SHA256 96d8c6ad2a082bb243160ee91c2aee0d2fcd3dc0a862515519c34dab2fa664d3
MANUAL AUDIT SITE VERIFIED US-SRG source_rows 315600 modified_HH 1 new_SHA256 d65523022718819d7013d79f1015fe419958078a8d1fde4f062fa8470929933f
MANUAL AUDIT PASS 2/2 FULL-SOURCE CSV, 3/3 HALF-HOURS, EXACTLY 9 CELLS (TA_F, TA_F_QC, VPD_F)
MANUAL AUDIT PASS 8/8 OTHER-SITE MANIFEST ENTRIES IDENTICAL, 10/10 SITE MANIFEST
MANUAL AUDIT PASS ERA-ORIGIN QC2, RETAINED STAGE14 RH, SATURATION PHYSICS, SHA256 AND RECEIPTS
MANUAL AUDIT ORIGINAL T SCIENCE HOLDS 8 UNCHANGED; US-Syv 606+10 DEFERRED
MANUAL AUDIT READ-ONLY: NO SOURCE OR MODEL WRITES; NOT APPROVED FOR POST-v5/DATM/CIME/SLURM/SPINUP
```

## Correct phase and remaining science decisions

**Technical file integrity is now VERIFIED.** This is **not** evidence that the original tower temperature observations are scientifically disproven, nor that Stage14's eight original scientific temperature HOLDs are resolved. No production forcing or model job was authorised.

- Of the **eight unchanged official temperature science HOLDs**, **three** now have a separate fully audited manual research-alternative temperature/VPD scenario (two US-SP1 October 2000; one US-SRG March 2019). They are **not cleared in the original scientific ledger**.
- **Five further original T holds remain without the new manual alternative**: US-SP1 2007-10-15 17:30; US-SP1 2008-01-16 08:00/08:30; US-SP1 2008-02-03 08:00; and US-Seg 2016-12-27 18:00. The extended read-only review revealed a **four-day repeated 18:00 US-SP1 discontinuity**, and **extended winter QC0 versus grid-T differences**—not independent raw thermometer confirmation. **US-Seg continued cooling below freezing after 20:00**; current evidence supports preserving native source TA while reviewing independent RH/VPD.
- US-Syv's **606 inherited science HOLDs** and **10 skipped Stage07 ERA edge points** remain explicitly deferred.

**Next scientific decision:** review original raw sensor/BASE data for the broad US-SP1 2007/2008 source anomalies and US-Seg's humidity consistency; classify separately whether to retain tower TA, make an alternate sensitivity experiment, or flag/remove an invalid instrument interval. Avoid pointwise ERA replacement for the 2007–08 US-SP1 multi-hour episodes without independent evidence. Do not use this experimental CSV/manifest as an approved Post-v5, DATM/CIME or CLM-FATES spinup input.

Related: [operator-created candidate record](MANUAL_THREE_T_TRIAL_CREATED_VERIFY_NEXT_2026-10-25.md); [Stage21 original source-coverage limitations](STAGE21_VERIFIED_ORIGINAL_TEMPERATURE_SOURCE_COVERAGE_2026-10-25.md).
