# Batch04 Stage10 — 689/689 independent ERA5-Land humidity replacements (operator VERIFIED)

**Evidence: IRIDIS6 operator terminal output, early 2026-10-25 UK local time.** Stage10 pinned script `b8ff0c2aaf41683d70bb94e9d70715c25c5eea45` rerun using `--run --max-downloads 2`; Python syntax and self-test PASS. Stage08/Stage09 provenance, BIF location and fixed native clock inputs are rechecked by the execution code. No original FLUXNET source or Stage07–09 derived data was overwritten.

## Full operator evidence

```text
BIF SITE US-Rpf latitude 65.1198 longitude -147.429 UTC_OFFSET -9.0 native_local_standard_clock
BIF SITE US-SRM latitude 31.8214 longitude -110.8661 UTC_OFFSET -7.0 native_local_standard_clock
STAGE10 TARGET CENSUS 689 site_years 5
TARGET US-Rpf 2024 n 390 PRESENT
TARGET US-Rpf 2008 n 218 PRESENT
TARGET US-Rpf 2021 n 69 PRESENT
TARGET US-Rpf 2022 n 11 NEEDS_INDEPENDENT_ERA5LAND
TARGET US-SRM 2023 n 1 NEEDS_INDEPENDENT_ERA5LAND
CDS RECOVER PREVIOUS PARTIAL: .../US-Rpf/2022/ERA5Land_US-Rpf_2022_T2M_D2M_SP_Stage10.download.partial bytes 285347
CDS VERIFIED/RECOVERED US-Rpf 2022 b5b7b5b66f9c89f0b640f3c9d79827f87e244fcb5555fc9d12f8223682340939
CDS REUSED PREVIOUS VERIFIED ARTIFACT US-Rpf 2022
CDS REQUEST START US-SRM 2023 ... 2m_temperature, 2m_dewpoint_temperature, surface_pressure ...
CDS status successful
CDS VERIFIED/RECOVERED US-SRM 2023 25d197c8c208b6b0d5da45ea1c66236b7fed962d6d9b6b9a7f2aa30024f9b84d
STAGE10 NEW CDS SITE-YEARS DOWNLOADED 2
STAGE10 REPAIR RESULT US-Rpf changed 688 still_unrepaired 0 reasons {}
STAGE10 REPAIR RESULT US-SRM changed 1 still_unrepaired 0 reasons {}
STAGE10 RESULT: 689 repaired, 0 remaining of 689
NO ORIGINAL SOURCE, STAGE07/08/09, DATM OR MODEL WRITES
```

The phrase **`NEW CDS SITE-YEARS DOWNLOADED 2` is a code counter of acquired/reused site-years in this invocation**: the existing US-Rpf 2022 partial was validated/reused, while US-SRM 2023 was downloaded from CDS in this invocation. The other 3 site-years were previously present with receipts.

## Actual latest complete derived site data

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage10_independent_era5land/candidate_20261024T231424Z_d9967326
```

Contains new full `US-Rpf_Stage10_ERA5Land_humidity_derived_FLUXMET_HH.csv` and `US-SRM_Stage10_ERA5Land_humidity_derived_FLUXMET_HH.csv`, `stage10_applied_ERA5Land_humidity.csv` with 689 repairs, `stage10_remaining_689_holds.csv` with 0 target rows, `stage10_receipt.json` with source BIF/grid/data SHA proofs and explicit model-not-ready flags.

**Scientific meaning:** 689/689 refers ONLY to US-Rpf/US-SRM ERA-invalid native VPD events. Stage10 recovers RH from independently sourced ERA5-Land 2m temperature+dewpoint at UTC hourly resolution and reconstructs VPD under retained tower temperature; scripts require grid physics and exact original BIF local standard time offset. Grid data remain reanalysis estimates rather than tower truth.

**Other Batch04 scientific blockers remain**: previously Stage08 seven-site HOLD ledger 696 = 689 targeted Stage10 repaired + **7** other site holds (US-Seg 4, US-SRG 1, US-Uaf 2); and Stage07 three-site Stage05 inherited **754** holds (US-SP1 147, US-Syv 606, US-Ton 1) plus 12 skipped direct-ERA high-jump endpoints, whose unique overlap with those holds is not confirmed. The 689 repaired entries must not be counted again as remaining blockers.

**Current gate:** All 10 Batch04 sites have complete *derived candidate* FLUXMET HH data. None is yet officially designated validated Post-v5 DATM or CLM-FATES spinup input; coordinate QA, physical forcing closure across all final rows and remaining explicit HOLD adjudications are separate.
