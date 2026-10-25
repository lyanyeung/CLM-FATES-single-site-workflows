# AmeriFlux Batch04 Stage20 — VERIFIED original BIF temperature metadata inventory (2026-10-25)

**Result: IRIDIS6 OPERATOR VERIFIED PASS.** Stage20 `--self-test` and `--audit` completed; original BIF metadata for **3/3 sites** was inventoried, source contracts for **6/6 target events** checked, and **0/8 original temperature science HOLDs cleared**. This report transcribes the operator's stdout, not a remote execution by GitHub or an independent assessment of raw sensor data.

## Original full-source provenance and BIF record counts

| Site | Original FLUXMET SHA256 | Original BIF SHA256 | BIF rows | BIF groups | BIF group with TA reference | Native UTC offset |
| --- | --- | --- | ---: | ---: | --- | ---: |
| US-SP1 | `d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963` | `7d8be284cacb1d4b8e503fb15ba354beabb8db4ed82c0225a50f3d5e77081890` | 7,085 | 1,547 | 1551, 5 rows | −5 h |
| US-SRG | `bce57eebcce1babf9f9310e76c8f41451a8e3632c8d08a95f03345e35a189567` | `68d2a977e11919d298e6df46b60d05ff6d8c1e06fb4771cf7a749c7710a7e64a` | 6,103 | 1,335 | 1643, 5 rows | −7 h |
| US-Seg | `2fc2fc1c846749070f62c981b0f71789bdc9dae7585eeb0b0f30455a9e88034d` | `29be3a4e5c216eb8749cb36273c7e8678936ca3f207518266abd8579c4412ae3` | 6,427 | 1,407 | 1518, 5 rows | −7 h |

All three **TA-related BIF candidate groups** were identified by the field `ERA_VARIABLE = TA`. Their five BIF rows were **not demonstrated to describe a physical tower air-temperature sensor**, raw sensor height, installation period, instrument model or the validity of a given QC0 temperature event. `ERA_VARIABLE` is metadata about the ERA-related product. It is **not original tower-instrument provenance**.

Stage20's field-level inventory listed:
- **US-SP1:** `FLUX_MEASUREMENTS_DATE_START:3`, `FLUX_MEASUREMENTS_METHOD:3`, `FLUX_MEASUREMENTS_OPERATIONS:3`, `FLUX_MEASUREMENTS_VARIABLE:3`, `HEIGHTC:1`, `HEIGHTC_DATE:1`.
- **US-SRG:** `FLUX_MEASUREMENTS_DATE_START:2`, `FLUX_MEASUREMENTS_METHOD:2`, `FLUX_MEASUREMENTS_OPERATIONS:2`, `FLUX_MEASUREMENTS_VARIABLE:2`, `HEIGHTC:1`, `HEIGHTC_DATE:1`, `HEIGHTC_STATISTIC:1`.
- **US-Seg:** `FLUX_MEASUREMENTS_DATE_START:2`, `FLUX_MEASUREMENTS_METHOD:2`, `FLUX_MEASUREMENTS_OPERATIONS:2`, `FLUX_MEASUREMENTS_VARIABLE:2`, `IGBP_DATE_START:1`, `LOCATION_DATE_START:1`, `UTC_OFFSET_DATE_START:1`.

**Caution:** these are only the subset of BIF *VARIABLE* names selected by the Stage20 scanner's keyword rules. They are not a complete station-instrument metadata catalogue and cannot prove the complete absence of an air-temperature sensor description elsewhere. Stage20 printed only matching rows of candidate groups; it did not inspect all five rows of each ERA group. `HEIGHTC` is not automatically the height of the specific temperature sensor, and `FLUX_MEASUREMENTS_*` need not be the original air-temperature source.

## Six event contracts retained

| Site | Original native local HH conflict timestamps | Stage20 scientific evidence |
| --- | --- | --- |
| US-SP1 | 200710151730, 200801160800, 200801160830, 200802030800 | No time-linked original temperature-instrument identity or independent raw sensor QC established |
| US-SRG | 201903191200 | Same; lone original QC0 spike relative to ERA-derived neighbours still suspicious but unverified |
| US-Seg | 201612271800 | Same; original sustained cooling remains plausible |

Two previous US-SP1 alternative sensitivity half-hours (`200010091800`, `200010091830`) remain separately held. **Total: 8/8 original temperature science HOLDs unresolved.**

## Operator completion log

```text
STAGE20 SELF-TEST PASS: six source events, metadata token filter, eight unchanged holds; read-only
STAGE20 RESULT: 3/3 ORIGINAL SITE BIF METADATA INVENTORIED, 6/6 EVENT SOURCE CONTRACTS PINNED
STAGE20 TEMPERATURE_METADATA_CANDIDATE_GROUP_COUNTS {'US-SP1': 1, 'US-SRG': 1, 'US-Seg': 1}
STAGE20 SCIENCE DECISION: 0 OFFICIAL T HOLDS CLEARED; 8/8 PRESERVED
STAGE20 US-Syv 606 OLD SCIENCE HOLDS + 10 STAGE07 ERA EDGE SKIPS DEFERRED
STAGE20 READ ONLY: NO SOURCE/QC/CDS/POST-v5/DATM/CIME/SLURM/MODEL WRITES
```

## Decision

**Do not treat BIF `ERA_VARIABLE=TA` as a new, independent source of temperature truth.** Before any production temperature replacement, obtain site-specific native sensor/field measurements, original instrument and sampling time information, and the source-side QC/change log. In particular:
- **US-SP1:** recurring 2007 daytime and 2008 winter multi-hour cold-vs-ERA episodes must be reviewed as potential *periods*, not only four isolated cells.
- **US-SRG:** 2019-03-19 12:00 (0.718°C QC0 versus 20.399°C TA_ERA) is the strongest individual point hypothesis, but adjacent QC2 values are ERA-derived and not independent raw tower anchors.
- **US-Seg:** retain original QC0 temperature through continuous cooling; difference from ERA alone is insufficient for a temperature correction.

**Next scientific gate:** one focused read-only inventory of **all native release product files/headers and any explicit raw TA channel**, rather than further reclassifications of the same ERA data. If no original independent temperature instrument source exists in the supplied package, stop internal-only QC escalation and seek independent AmeriFlux/site operator source data. Do not create further default ERA replacements.

Post-v5, DATM, CIME, SLURM and CLM-FATES spinup remain **NOT APPROVED** for these unresolved source candidates. US-Syv **606** original science HOLDs + **10** skipped Stage07 ERA jump edges are still deferred.

**Stage20 script and instructions:** [source code](../scripts/stage20/20_audit_original_BIF_temperature_instrument_metadata.py), [reproducible pinned IRIDIS6 run command](STAGE20_ORIGINAL_BIF_TEMPERATURE_INSTRUMENT_PROVENANCE_NEXT_2026-10-25.md).
