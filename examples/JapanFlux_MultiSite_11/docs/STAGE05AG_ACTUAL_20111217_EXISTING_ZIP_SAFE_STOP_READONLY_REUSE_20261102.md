# JapanFlux Stage05AG — actual JP-Khw 2011-12-17 existing CDS target safe stop (2026-11-02)

## Operator-observed execution, not a scientific source audit failure

The operator invoked the earlier Stage05AG shell controller. The pinned JP-Khw 2011-12-16 original CDS ZIP SHA256 check succeeded. Stage05AG `--self-test` succeeded but its previously published print label incorrectly said `STAGE05AD` (cosmetic upstream adaptation bug, not a Stage05AD execution). Science source-gated preflight PASS. Before any new CDS request or Stage05AB fresh inventory was made, the shell found the **2011-12-17 JP-Khw final ZIP pathname already existed** and stopped:

```text
/home/ly3n24/japanflux_stage05s/downloads/JP-Khw_ERA5Land_timeseries_20111216_CSV_response.zip: OK
STAGE05AD SELF-TEST PASS | source-verified two-day UTC-midnight, exact per-variable Stage05P context, SHA/CRC; NO WRITES
=== SCIENCE PREFLIGHT ===
STAGE05AG SOURCE PREFLIGHT PASS
STOP: Existing CDS payload /home/ly3n24/japanflux_stage05s/downloads/JP-Khw_ERA5Land_timeseries_20111217_CSV_response.zip
```

This output confirms only that the final ZIP pathname existed when the shell checked it. It **does not** establish its size, SHA256, ZIP CRC, actual data contents, date, variable, grid, original CDS request ID, or timing of its creation. No evidence is present that this attempt submitted or downloaded a new Dec17 request, and no user-facing correction approval should be inferred.

The project previously established JP-Khw 2011-12-16 UTC `surface_pressure` ZIP via real CDS request ID `e9d0b2f4-d165-4dd1-a39b-a2083b6b048b`, 491 bytes, ZIP SHA256 `fb2d7677d7c8a38fe4d5d31eb0af37434cfe0932a59343e36601f61b7e407821`, returned grid **33.10000000000104°N,130.69999999999686°E**. This Dec16 source stays unchanged.

## Decision: do not re-download or delete/rename existing ZIP

Use the original source-scoped, pinned [Stage05AB](../scripts/stage05/05ab_inventory_six_2011_existing_CDS_ZIP_partial_CRC_READONLY.py) **first** on the current `$HOME/japanflux_stage05s/downloads` tree and fresh report folder. This validates both JP-Khw Dec16 and Dec17 ZIPs, checks SHA256/CRC, expected `sp` CSV variable in Pa, exact 24 UTC hour stamps per day, original BIF tower/ERA5-Land grid proximity, and no duplicate variable/hour records. A `.zip.partial` collision, invalid CRC, missing hours or wrong date remains science HOLD with no deletion/overwrite. The original ZIP SHA from Dec17 will be documented as **observed current file digest**, never guessed and never mistaken for a newly observed CDS submission request.

If **both** JP-Khw site-days pass, run [Stage05AG](../scripts/stage05/05ag_JP_Khw_2011_two_day_pressure_3_QC2_independent_context_NO_REPAIR.py) using actual Stage05O (original 27 source QC2 UTC+9 records), Stage05R (original 87 variable-hour source association records), Stage05AE (actual 19/45 original field context evidence ledger), the **fresh** Stage05AB six-day audit, and the two **unchanged original ZIPs**. Stage05AG independently requires **48 hourly pressure values** from the **same returned grid** and compares original 2011 JP-Khw source QC2 `F=ERA` records against their source-verified nearby hourly reference intervals. This is an independent **source-context diagnostic**, not scientific approval of an ERA5-Land to half-hour forcing replacement. The model-grid elevation is unverified.

The Stage05AG code was patched on GitHub to correct **SELF-TEST PASS** and **two-day audit PASS** print labels from `STAGE05AD` to `STAGE05AG` (no science algorithm change). It must be fetched with a fresh SHA pin.

**Portfolio at observed stop:** 19/45 original QC2 fields strongly supported by independent hourly physics; 8 UTC-verified fields pending external context; 18 JP-Tef/Tmd original solar/standard clock conflicts; **6/9 independent CDS source days verified**, **3/9 not yet re-audited** (including the pre-existing JP-Khw Dec17 file whose content has *not* yet passed Stage05AB). All 45 source field candidates remain HOLD. No model, forcing, original JPF ZIP, Slurm, or AD400 changes.
