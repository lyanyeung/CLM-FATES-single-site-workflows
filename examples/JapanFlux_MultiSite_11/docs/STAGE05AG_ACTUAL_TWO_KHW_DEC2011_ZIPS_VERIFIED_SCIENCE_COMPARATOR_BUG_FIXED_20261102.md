# JapanFlux Stage05AG actual two JP-Khw 2011 ZIP contents validated; science comparator source-variable scope bug corrected (2026-11-02)

## Operator-observed source evidence

User re-ran **original Stage05AB** read-only source audit on the original downloads directory after Stage05AG initial one-day-request collision. Both JP-Khw Dec-2011 ZIPs were confirmed as real regular source files with compatible CDS CSV, 24 UTC hourly surface pressure records, ZIP CRC, exact original station/nearest-grid match:

```text
STAGE05AB SIX 2011-CDS DAY EXISTING FILES/CRC/TIME/GRID SOURCE INVENTORY PASS | NO CDS / SLURM / REPAIR
DAY JP-Khw 2011-12-16 ZIP REGULAR PARTIAL ABSENT CSV_ZIP_STATUS COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR SHA256 fb2d7677d7c8a38fe4d5d31eb0af37434cfe0932a59343e36601f61b7e407821 GRID 33.10000000000104 130.69999999999686 NEXT REUSE_VALID_EXISTING_ZIP_FOR_SEPARATE_SOURCE_QC2_REVIEW_NO_REDOWNLOAD
DAY JP-Khw 2011-12-17 ZIP REGULAR PARTIAL ABSENT CSV_ZIP_STATUS COMPLETE_CDS_STYLE_ZIP_PAYLOAD_VERIFIED_NOT_A_REPAIR SHA256 f590c32432ffac5c10460ea074ea8fc05fb9b8742af96f8301e9d35ed6fb6188 GRID 33.10000000000104 130.69999999999686 NEXT REUSE_VALID_EXISTING_ZIP_FOR_SEPARATE_SOURCE_QC2_REVIEW_NO_REDOWNLOAD
DAY JP-Yms 2011-12-16 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT
DAY JP-Yms 2011-12-17 ZIP ABSENT PARTIAL ABSENT CSV_ZIP_STATUS ABSENT
COUNTS {'REUSE_VALID_EXISTING_ZIP_FOR_SEPARATE_SOURCE_QC2_REVIEW_NO_REDOWNLOAD': 4, 'NO_PAYLOAD_FOUND_ONE_DAY_OPERATOR_CDS_SUBMISSION_ELIGIBLE_AFTER_LICENCE_PREFLIGHT': 2}
INVENTORY /home/ly3n24/japanflux_stage05ag/inventory_20261102T183318Z/stage05ab_six_2011_CDS_archive_existing_payload_inventory_HOLD.tsv
SOURCE_AUDIT /home/ly3n24/japanflux_stage05ag/inventory_20261102T183318Z/stage05ab_six_2011_CDS_original_archive_science_audit.json
JP-Khw BOTH DAYS SCIENCE SOURCE GATE PASS
```

This means **7 of 9** original site×UTC-day external reference payloads contents are now SHA/CRC/24 UTC hour/variable/grid verified. Dec17 JP-Khw ZIP existed before the current run, and **its original CDS request transaction ID was not provided**. No download was triggered in this attempt and the ZIP is preserved unchanged.

## Actual Stage05AG source-selector failure: deterministic programming bug

The operator then executed the first version of the two-day JP-Khw original JPF source-QC2 vs independent ERA5-Land pressure comparator:

```text
=== STAGE05AG TWO-DAY SCIENTIFIC COMPARISON ===
Traceback (most recent call last):
  ...
  File "/home/ly3n24/japanflux_stage05ag/stage05ag_checked.py", line 79, in source_events
    raise ValueError("Original JP-Khw source QC2 variable / units unexpected")
ValueError: Original JP-Khw source QC2 variable / units unexpected
```

This **is not a CDS ZIP/CRC/grid failure**. The code was adapted from a JP-Fjy pressure-only comparator; its `source_events()` enforced `r['variable']=='PA'` on **all 11 original JP-Khw source-QC2 fields**, including **eight separately reviewed 2005 mixed-variable records** (LW_IN×2, PA×3, TA×3). The three **2011** source candidates are PA-only, but the code must first distinguish the historical August 2005 anomalies. This code bug blocked the comparison before any derived output or scientific amendment.

## GitHub fix

[Stage05AG fixed source-exact three-variable historical gate and 2011 PA-only selector](../scripts/stage05/05ag_JP_Khw_2011_two_day_pressure_3_QC2_independent_context_NO_REPAIR.py), commit `99cc25636d2f8b70f705a83417e5170d4ea87ab4`, blob SHA `f99bed7f7f91828b7ae4cb4597a3aab032a176ff`.

- Original 27 source UTC-verified field records and F/embedded ERA equality/QC2/UTC+9 gates are preserved.
- First verify all 11 JP-Khw original field records: eight August-2005 fields **2 LW_IN +3 PA +3 TA**, three 2011 fields strictly **3 PA**.
- Select only the three 2011 original PA QC2 fields for two-day independent CDS comparison.
- Add synthetic regression self-test with 27 source rows including the 2005 mixed field classes; assert it accepts history and rejects a 2011 non-PA field. This test was **published on GitHub but real IRIDIS self-test has not yet been observed**.
- Keep the original Stage05R source-specific variable-hour, BIF, SHA/CRC, same-grid, hourly alignment, grid elevation UNKNOWN, and 45-field all-HOLD/NO_REPAIR gates intact.

Next operator action: run only patched **Stage05AG --self-test + read-only actual two-day source comparison** with the original Stage05O/R/AE and latest Stage05AB inventory above, plus same two original CDS ZIP files. **Do not repeat Stage05S CDS download** or delete/rename either ZIP.

**Scientific state:** 19 of 45 original source-selected QC2 anomalies already strongly supported by independent gridded meteorological context (JP-Fjy6, JP-Khw8, JP-Yms5), 8 further UTC-verified source fields not yet independently compared (JP-Khw3+JP-Yms5), 18 original Tef/Tmd clock conflicts. All **45 source fields remain HOLD** until a validated scientific repair decision; no original JPF, forcing, model, AD400, or Slurm changes.
