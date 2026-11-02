# JapanFlux Stage05L — actual metadata gate result 3/5, JP-Tef and JP-Tmd README evidence pending (2026-11-02)

> **FOLLOW-UP 2026-11-02 — Stage05N source evidence resolved WHY the gate failed, NOT the time convention.** JP-Tef and JP-Tmd share one original, source-SHA-verified 75-line README: **line 64 explicitly says `local solar time (without DST)`**. It was not a generic missing paragraph or excerpt cap. All original BIF UTC_OFFSET values still equal +9; FLUXNET's official standard is local **standard** time without DST. Thus the source release contains a genuine text/specification ambiguity. The 3/5 stage gate is scientifically correct to remain unresolved for Tef/Tmd until independent producer or data/time-series evidence. See [Stage05N actual full source](STAGE05N_ACTUAL_SOLAR_VS_STANDARD_README_CONFLICT_STAGE05O_SCOPE_20261102.md) and [Stage05O 3-mapped/2-unresolved scoped mapping](../scripts/stage05/05o_scoped_3site_UTC_2site_solar_README_HOLD_NO_ZIP.py). Earlier diagnosis of 'possible missing paragraph' below is superseded by this evidence.

## Actual operator IRIDIS6 result

The operator completed Stage05K per-site metadata scans for JP-Fjy, JP-Tef, JP-Tmd, JP-Yms; JP-Khw had already passed Stage05K. Each Stage05K reported `READONLY_BIF_VARIABLE_AND_TIME_METADATA_EXTRACTED` with `METADATA PASS` (this confirms JSON structure and scan completion, **not complete temporal provenance validation**). Stage05L subsequently printed:

```
STAGE05L SELF-TEST PASS | original BIF QC/time/unit gates and JST→UTC algebra; NO WRITES
STAGE05L HOLD_INCOMPLETE_OR_CONFLICTING_METADATA VERIFIED 3 /5
SITE JP-Fjy VERIFIED UTC_OFFSET 9.0 ISSUES []
SITE JP-Khw VERIFIED UTC_OFFSET 9.0 ISSUES []
SITE JP-Tef HOLD_METADATA_UNVERIFIED UTC_OFFSET 9.0 ISSUES ['README local standard time without DST not confirmed']
SITE JP-Tmd HOLD_METADATA_UNVERIFIED UTC_OFFSET 9.0 ISSUES ['README local standard time without DST not confirmed']
SITE JP-Yms VERIFIED UTC_OFFSET 9.0 ISSUES []
NO UTC JOIN GENERATED: FIX ORIGINAL METADATA PROVENANCE FIRST
METADATA_REPORT /home/ly3n24/japanflux_stage05l/run_20261102T010150Z/stage05l_source_metadata_validation.json
NO ORIGINAL SOURCE WRITES OR APPROVED REPLACEMENTS
```

**Supported conclusion:** all five affected sites' original BIF `GRP_UTC_OFFSET` values are **+9** and all five pass Stage05L's direct variable unit/QC/ERA-downscaling-definition checks. However the release-specific README local-standard-time-without-DST phrase gate only matched for **Fjy, Khw, Yms**. Tef and Tmd remain HOLD **because the required README evidence wasn't recognized in Stage05K's stored excerpt lines**, not because the original reported a contradictory UTC offset or numerical units. Whether this is a wording, extraction limit or genuinely missing README clause is **not yet proven**.

Stage05L intentionally wrote **NO derived UTC join** of the 45 source-HOLD field records (35 unique station×native half-hour keys). This is the appropriate fail-closed behavior, not a broken experiment.

## Root-cause-specific forensic plan

The original Stage05L condition is exact and potentially over-restrictive: a `README.txt` line must contain **both** `local standard time` **and** `without DST` (case-insensitive). Equivalent source phrasing (e.g., `no daylight saving time`) or split text across lines could fail despite authoritative support. The original Stage05K saved only its first 90 regex-derived time/unit hint lines, rather than a complete README verbatim; the absence of a matching excerpt is not proof that the source README lacks the statement.

Do **not** simply remove this metadata requirement or force 5/5. Diagnose original evidence first with [Stage05M JSON-only original README hint inspector](../scripts/stage05/05m_inspect_saved_stage05k_README_time_hints_NO_ZIP_NO_SLURM.py). It examines the **five existing Stage05K JSONs**, prints README SHA-256 (to identify shared README editions), saved source-excerpt line numbers and exact text, and notes if the stored 90-excerpt cap might have hidden relevant lines. No ZIP reopen, Slurm, data replacement, or model run.

Based on actual Stage05M evidence:

- If source README already contains an unambiguous equivalent local-standard-time/no-DST statement, amend Stage05L's recognizer with a narrowly supported test and verify all five original BIF units/QC/offset checks remain intact.
- If the saved excerpts are incomplete, inspect **only the small source README** for JP-Tef and JP-Tmd directly, one site at a time, bounded in memory; do not re-scan large meteorological CSV time series.
- If the source README or original metadata truly lacks an authoritative time-basis statement, maintain HOLD pending an independent official record. The matching `UTC_OFFSET=9` is strong support but does not, by itself, establish absence of DST or the interpretation of every timestamp.

Once source provenance is established for all five, run Stage05L to generate **derived** `stage05l_45_hold_native_to_utc.tsv`. It must never modify 45 original source selections, independent ECMWF data, or forcing.

## Science status

Stage05I **45 source-science HOLD** candidates / **35 unique site×native half-hour keys** remain pending; no automatic repairs, source edits, Slurm, AD400 or Normal400. Stage05L has completed a **3/5 site metadata gate** and must not be reported as 5/5 yet. JP-Tom and JP-Tgf humidity provenance still requires independent study.
