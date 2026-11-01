# JapanFlux Stage05I — actual 45-field / 35 site-time unapproved source HOLD register (2026-11-01)

## Actual IRIDIS6 result

The operator executed `05i_merge_41_absolute_plus_4_Yms_PA_shoulder_HOLD_NO_ZIP.py` against the pre-existing Stage05G and Stage05H TSV audit tables. The operator pasted:

```
/home/ly3n24/japanflux_stage05i/stage05i.py: FAILED
STAGE05I SELF-TEST PASS | fixed science invariants, QC2 source equality; no writes
STAGE05I MERGE SUCCESS | NO ZIP / NO SLURM / NO REPAIR
VARIABLE_RECORDS 45
DISTINCT_SITE_HALF_HOURS 35
BY_VARIABLE {'LW_IN': 12, 'PA': 27, 'TA': 6}
BY_SITE {'JP-Fjy': 6, 'JP-Khw': 11, 'JP-Tef': 4, 'JP-Tmd': 14, 'JP-Yms': 10}
SOURCE_HOLD /home/ly3n24/japanflux_stage05i/run_20261101T065709Z/stage05i_45_review_candidates.tsv
SUMMARY /home/ly3n24/japanflux_stage05i/run_20261101T065709Z/stage05i_45_review_summary.json
```

The standalone `FAILED` was emitted by a **wrong verification command supplied by the assistant**, which compared raw `sha1sum -c` to the expected **Git blob SHA-1** `e7814046081e8aa2a18fc78d8138c7fc39503c76`. These hashes are calculated differently; `sha1sum` compares a bare file SHA-1, whereas `git hash-object` uses the Git object header and content. The assistant's command contained a fallback `test "$(git hash-object "$D/stage05i.py")" = "e781..."`, which passed because the subsequent `--self-test` and main process ran. **Do not report this as a script-failure or an unverified source**. Future pinned code checks must use only `git hash-object` against a Git blob SHA, or `sha256sum` against a known actual SHA-256 digest.

**Evidence scope:** the operator's stdout establishes scientific audit invariants and output paths. The new Stage05I TSV and JSON remain on IRIDIS6 and have **not** been uploaded to GitHub as data files; this GitHub report records the operator's verified statistics and path, not actual TSV contents. The source-input files themselves remain unchanged.

## Exact Stage05I HOLD-scope accounting

| Site | TA field candidates | PA field candidates | LW_IN field candidates | Variable candidates |
|---|---:|---:|---:|---:|
| JP-Fjy | 0 | 6 | 0 | 6 |
| JP-Khw | 3 | 6 | 2 | 11 |
| JP-Tef | 0 | 0 | 4 | 4 |
| JP-Tmd | 3 | 9 | 2 | 14 |
| JP-Yms | 0 | 6 | 4 | 10 |
| **Total** | **6** | **27** | **12** | **45** |

The **35 unique station × native half-hour keys** count removes repeated variables that are flagged in the same half-hour. The four additional Stage05H JP-Yms pressure shoulders overlap with two already LW-flagged half-hours, hence 41 flagged field rows across 33 keys becomes 45 across 35 keys.

**Everything remains `HOLD_UNAPPROVED_SOURCE_REVIEW`.** The five-station scoped flagged events do not imply every other time/value is validated. The source archive's timezone, QA metadata semantics, pressure and radiation units, and true independent ECMWF ERA5/ERA5-Land reference data are not yet verified.

## Next steps

1. **Stage05J:** inspect original JPF inner-ZIP text metadata, BIF and README for original source QC meanings, units, timezone and provenance. This is a small, per-site **read-only** audit without Slurm; inspect actual contents, do not assume those documents establish every item.
2. Independently compare original external ERA5/ERA5-Land, exact timestamps (after time-basis validation), raw tower and available MDS values. Do not recommend blindly replacing erroneous `*_ERA` with same-release ERA or automatically trusting MDS.
3. Only after event-by-event source approval, propose a reversible SHA-pinned **derived forcing-copy overlay**. Original ZIPs and normal QC0 selected source values remain unchanged.
4. Separately audit the large RH>100% and negative VPD issue at JapanFLUX2024 JP-Tom and JP-Tgf before model forcing.
5. **No AD400/Normal400** has been scientifically cleared by Stage05I.
