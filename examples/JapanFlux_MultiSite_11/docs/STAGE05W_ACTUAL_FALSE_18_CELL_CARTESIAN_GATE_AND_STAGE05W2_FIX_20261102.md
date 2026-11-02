# JapanFlux Stage05W first execution stopped at FALSE Cartesian-hour gate; Stage05W2 corrective source-bound audit (2026-11-02)

## Operator's actual Stage05W output (failed before ZIP parsing)

```text
STAGE05W SELF-TEST PASS | original Yms BIF, 2×24 CDS hours, ZIP SHA pin; NO WRITES
/home/ly3n24/japanflux_stage05s/downloads/JP-Yms_ERA5Land_timeseries_20050811_CSV_response.zip: OK
Traceback ... validate_origin(...)
  ValueError: Exact JP-Yms UTC 9-hour × 2-variable source scope not matched
```

**Root cause is a programmer-authored Stage05W validation defect, not evidence of source corruption or an invalid CDS download.** Stage05W assumed the nine *union* UTC reference hours must form a complete 9 × 2 (18-row) Cartesian product with surface pressure and downward longwave at *each* hour. The actual upstream source pipeline does not make that assumption: Stage05P creates the full ±3-hour (index -3 through +4 relative to the UTC hour floored from each flagged original half-hour) request **independently for each source variable/event**, and Stage05R unions the distinct requested hours for the site/day. The union includes **nine distinct JP-Yms UTC hours 14:00–22:00**, but the per-variable hours can be fewer. Stage05V's source-day plan records the **union of hours and variables**, not per-variable hour pairs.

The earlier 9×2 invariant is scientifically unsupported and created this false STOP. It must not be 'fixed' by simply discarding source-provenance checks or assuming any arbitrary subset is valid.

**Confirmed at failure:** the actual ZIP's independent SHA256 checked OK; no CSV member content yet inspected; no source or forcing writes; no Slurm, model jobs, changes or new CDS requests. Original JP-Yms CDS 936-byte ZIP SHA256:
`4bf228a3a53ab7fc6751b8e7438fb459570536ce6f54af2f81de5afc083b59d5`.

## Stage05W2 published correct, stricter variable-specific UTC-source mapping

[Stage05W2](../scripts/stage05/05w2_JP_Yms_sparse_source_hours_CDS_ZIP_READONLY.py) is a **new script**, preserves the original Stage05W failure source as a diagnostic artifact and is **not yet run on the user's IRIDIS6 data**. It:

1. Validates **all 27** original Stage05O UTC-mapped source-selected fields, original three-site counts 6/11/10, QC2, HOLD statuses, JPF original F == same-release ERA and UTC+9 (BIF/README) timestamp algebra. For JP-Yms it further requires original **6 PA + 4 LW_IN** field records.
2. Recomputes Stage05P's source-variable-specific `range(-3,5)` hourly windows for each JP-Yms flagged native half-hour. It compares **the exact (UTC hour, ERA5-Land variable) keys AND the per-key original source event UTC-start associations** to the real Stage05R source-verified 87-row table. Conflicting or missing source keys fail closed, without assuming nine times two.
3. Verifies Stage05V's original 8 pending-day plan, exact JP-Yms BIF source SHA/coordinates/elevation and expected *union* of nine source-relevant hours.
4. Imports **only** the previously published original Stage05W ZIP parser, after checking the existing local source file's exact **Git blob SHA `c953a2d28a5dbc634179296e78c0b58ffa3be1df`**. That parser validates the operator's exact **936-byte original ZIP with observed SHA `4bf228...`**, reads two expected CSV files (pressure, longwave), checks one grid, 24 hourly valid_time labels per variable and physical bounds. No unverified replacement parser.
5. Writes **derived** source audit JSON and 48-row independent hourly TSV with all original-source candidate flags preserved as **HOLD**. No CDS calls/ZIP extraction, source meteorological or forcing edits, Slurm or AD400.

A new self-test includes a sparse-variable-source regression fixture: two independently centered 8-hour windows yield 9 union hours but **16 variable-hour pairs, not 18**. This test is mathematical/procedural; the actual output count should be read from the operator's source-generated records rather than guessed.

## Scientific status as of operator failure

- **CDS downloads: 2/9** confirmed site×UTC-day ZIPs (JP-Khw, JP-Yms both 2005-08-11 UTC); **7/9 not requested**.
- Independently compared original bad source fields: **8** JP-Khw fields/4 half-hours strongly supported as errors.
- Other original **19 UTC-resolved** fields: outside this successful JP-Khw comparison; new JP-Yms original CDS file **downloaded, not yet read**.
- **18 JP-Tef/Tmd** source fields: `local solar` versus `local standard` original README time basis unresolved. Do not translate them automatically.
- **All 45** original JPF source-selected abnormal fields remain science HOLD, no approved value replacements.

**Do not redownload the JP-Yms ZIP or edit the original Stage05W, Stage05P/R, original JPF ZIP or FATES forcing.** Execute only the pinned Stage05W2 source read-only audit, then inspect actual returned CSV/grid/pressure/longwave.
