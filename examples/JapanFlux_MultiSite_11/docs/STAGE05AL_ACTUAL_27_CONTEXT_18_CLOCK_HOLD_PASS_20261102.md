# JapanFlux Stage05AL — ACTUAL 27/45 source QC2 fields independently contextualized; 18 original clock-source HOLD (2026-11-02)

## Actual operator-run read-only audit

The operator executed the pinned Stage05AL unified original source QA script with exact Stage05O original 27 fields with verified UTC+9 source timestamps, 18 original source native timebase-conflict HOLD fields, Stage05AH 22 prior strong-context variables, Stage05AK five independent JP-Yms PA/LW context-only variables and Stage05AB validated original six December ERA5-Land CSV ZIP files. Output:

```text
STAGE05AL SELF-TEST PASS | 22 prior strong +5 new independent context-only +18 original time-source HOLD; 9/9 sources, no repair/NETWORK/WRITES
STAGE05AL 27 ORIGINAL SOURCE QC2 INDEPENDENT HOURLY CONTEXT MERGE PASS | NO CDS / SLURM / REPAIR
INDEPENDENT_HOURLY_CONTEXT_REVIEWED 27 /45 OUTSIDE_REFERENCE_ENVELOPE 27
PRIOR_STRONG_CONTEXT 22 NEW_STAGE05AK_CONTEXT_ONLY_HOLD 5
BY_SITE {'JP-Fjy': 6, 'JP-Khw': 11, 'JP-Yms': 10} DISTINCT_SITE_NATIVE_HALF_HOURS 21
SOURCE_CLOCK_TIMEBASE_HOLD 18 BY_SITE {'JP-Tef': 4, 'JP-Tmd': 14}
REFERENCE_SITE_DAYS_VERIFIED 9 /9
UNIFIED_SOURCE_CONTEXT_TSV /home/ly3n24/japanflux_stage05al/run_20261102T200818Z/stage05al_27_original_QC2_source_independent_context_22strong_5context_HOLD.tsv
SCIENCE_HOLD_REPORT /home/ly3n24/japanflux_stage05al/run_20261102T200818Z/stage05al_45_original_field_science_status_27_context_18_clock_HOLD.json
ALL_45_ORIGINAL_SOURCE_FIELDS_HOLD; NO MET_REPAIR_VALUES APPROVED
```

The **27 independently referenced flagged variables** occupy **21 distinct original site×native halfhours** (six Fjy fields, eleven Khw, ten Yms). All 27 show numerical disagreement outside their matched independent ERA5-Land hourly comparison envelopes. **22 prior original strong-context source records are preserved unchanged; five newest JP-Yms records retain the provenance/status `STAGE05AK_CONTEXT_ONLY_NOT_YET_STRONG_LABEL_APPROVED`**. The 18 remaining original variable fields, at 14 site×native halfhours, remain **JP-Tef (4) and JP-Tmd (14)**, which are unresolved source time conventions.

No source QC2 original ZIP, forcing, 30-minute replacement, model case, Slurm job, AD400, or repair approval occurred. Original source evidence remains **all 45 fields science HOLD**.

## Why JP-Tef/JP-Tmd cannot yet receive an automatic UTC lookup

The previously SHA-verified **original source README was two different release editions**:
- JP-Fjy/Khw/Yms: shared **85-line** original README `fe96face...`; line 69 explicitly says **local standard time (without DST)**.
- JP-Tef/Tmd: another shared **75-line** original README SHA256 `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5`; line 64 explicitly says **local solar time (without DST)**.
- Original BIF `UTC_OFFSET=9` for all five sites. For the latter two sites this is a **timezone metadata attribute**, not proof that all original source halfhour timestamps are already JST. Stage05L correctly classified Tef/Tmd **HOLD_METADATA_UNVERIFIED**. Stage05O intentionally did not generate Tef/Tmd UTC.
- The public FLUXNET2015/ONEFlux formatting convention uses local standard time without daylight savings, but cannot by itself supersede conflicting original release-specific README information (Pastorello et al. 2020, https://www.nature.com/articles/s41597-020-0534-3).
- The JapanFlux2024 dataset processing description notes source team data were reformatted into a FLUXNET-compatible product after consultation with site teams, which supports an investigation of **product timestamps versus original site raw timebase** but does not settle the exact Tef/Tmd release semantics (Ueyama et al. 2025, https://essd.copernicus.org/articles/17/3807/2025/).
- ICOS station metadata for JP-Tmd lists timezone offset 9, but this does **not** resolve whether its original packaged JPF timestamp `TIMESTAMP_START` was written in local solar or local standard time: https://meta.icos-cp.eu/resources/stations/ES_JP-Tmd.

## Next safe milestone

Stage05AM should **audit only exact original Tef/Tmd source time metadata and source-selected QC2 event records**, while retaining both contradictory README assertions and preserving UTC as `UNRESOLVED`. Candidate offsets based on longitude or daylight envelopes are **hypotheses only**, not enough to authorize UTC mapping or replacement. Seek site/PI-era timestamp convention evidence or original logger/data-file metadata anchored to the exact release. Any future comparison of alternative interpretations must be clearly **hypothetical, read-only**.

The Stage05AL outcome is actual operator-run. No Stage05AM downstream scientific verification has been run yet.
