# AmeriFlux Batch04 Stage21 — OPERATOR-VERIFIED original temperature source inventory

**Date:** 2026-10-25. **Status:** Stage21 IRIDIS6 OPERATOR VERIFIED PASS: original FLUXNET v1.3_r1 package **3/3 stations × 16 CSV files = 48/48 CSVs** inventoried; original source and BIF SHA contracts intact, original event contracts **6/6** intact, **no separate native temperature instrument-channel candidates detected in release CSV headers**, and **8/8 original tower-temperature science HOLDs retained**.

This report records operator-supplied stdout. The repository connector has not run IRIDIS6 or accessed unpublished site instrument readings.

## Source integrity

| Site | FLUXMET_HH SHA256 (full source) | Original BIF SHA256 | Native HH rows | HH FLUXMET columns |
| --- | --- | --- | ---: | ---: |
| US-SP1 | `d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963` | `7d8be284cacb1d4b8e503fb15ba354beabb8db4ed82c0225a50f3d5e77081890` | 368,208 | 223 |
| US-SRG | `bce57eebcce1babf9f9310e76c8f41451a8e3632c8d08a95f03345e35a189567` | `68d2a977e11919d298e6df46b60d05ff6d8c1e06fb4771cf7a749c7710a7e64a` | 315,600 | 243 |
| US-Seg | `2fc2fc1c846749070f62c981b0f71789bdc9dae7585eeb0b0f30455a9e88034d` | `29be3a4e5c216eb8749cb36273c7e8678936ca3f207518266abd8579c4412ae3` | 333,120 | 218 |

Each extracted **FLUXNET** product release contained exactly:
- **1 × BIF CSV**, 5 × `BIFVARINFO` CSVs (HH, DD, WW, MM, YY);
- **5 × ERA5 CSVs** (HH, DD, WW, MM, YY);
- **5 × FLUXMET CSVs** (HH, DD, WW, MM, YY).

Each original **FLUXMET_HH** contains the five consolidated temperature/processing fields: `TA_F_MDS`, `TA_F_MDS_QC`, `TA_ERA`, `TA_F`, `TA_F_QC`. Other FLUXMET aggregations provide summaries of these fields; ERA5 products offer `TA_ERA` and aggregate products. **None of the 48 scanned original CSV headers supplied a separately named sensor-level temperature observation such as `TA_1_1_1`, `TA_RAW`, or `T_AIR_1` as detected by Stage21.** Stage21 was an *original release header scan*, **not a download/evaluation of separate AmeriFlux BASE or private logger records**.

```text
STAGE21 PRODUCT COUNTS US-SP1 {'BIF': 1, 'ERA5': 5, 'FLUXMET': 5, 'OTHER': 5}
STAGE21 POSSIBLE INSTRUMENT-CHANNEL COLUMN CANDIDATES US-SP1 NONE_DETECTED_IN_RELEASE_HEADERS
STAGE21 PRODUCT COUNTS US-SRG {'BIF': 1, 'ERA5': 5, 'FLUXMET': 5, 'OTHER': 5}
STAGE21 POSSIBLE INSTRUMENT-CHANNEL COLUMN CANDIDATES US-SRG NONE_DETECTED_IN_RELEASE_HEADERS
STAGE21 PRODUCT COUNTS US-Seg {'BIF': 1, 'ERA5': 5, 'FLUXMET': 5, 'OTHER': 5}
STAGE21 POSSIBLE INSTRUMENT-CHANNEL COLUMN CANDIDATES US-Seg NONE_DETECTED_IN_RELEASE_HEADERS
```

## Original BIF flux-group provenance

| Site | FLUX_MEASUREMENTS groups | Actual reported measurements / method | Evidence relevance |
| --- | --- | --- | --- |
| US-SP1 | 1525, 1526, 1528 | H2O / H / CO2, each Eddy Covariance, dated 200007 | Flux instrumentation context, NOT independent original TA sensor provenance |
| US-SRG | 1609, 1620 | CO2 / H2O, each Eddy Covariance, dated 20080308 | Flux instrumentation, not a temperature sensor |
| US-Seg | 1484, 1491 | CO2 / H2O, each Eddy Covariance, dated 200701010000 | Flux instrumentation, not a temperature sensor |

Earlier Stage20's single apparent TA-relevant BIF group per site consisted of an `ERA_VARIABLE=TA` field. It is **not** an independently validated instrument trace. These facts are consistent with Stage21's original FLUXNET product inventory.

## Exact original-T scientific HOLDs

- **US-SP1:** `200010091800`, `200010091830` remain separate Stage15 temperature *sensitivity candidate* points only; the further four originals `200710151730`, `200801160800`, `200801160830`, `200802030800` remain unresolved. Long multi-day tower versus ERA differences documented in Stage19 must **not** be replaced one-by-one on that discrepancy alone.
- **US-SRG:** `201903191200` remains a probable single-outlier *hypothesis*, but original QC0 `0.718°C` and ERA-derived `20.399°C` discrepancy does not reveal a trustworthy measured tower value. Adjacent `TA_F_QC=2` readings are ERA-based fills, **not independent tower observations**.
- **US-Seg:** `201612271800` remains held; original 30-minute QC0 series showed ongoing cooling, and no independent raw instrument source was found in the downloaded FLUXNET package.

Total **8/8 original temperature scientific HOLDs retained.** US-Syv's **606 previous science HOLDs** plus **10 Stage07 skipped ERA jump-edge points** remain deferred. The existing Stage14 humidity-only physical correction candidates do **not** validate corresponding temperatures.

## Final internal-only escalation decision

```text
STAGE21 SELF-TEST PASS: source families, raw-channel candidate distinction, 8 science holds; read-only
STAGE21 RESULT: 3/3 ORIGINAL 16-FILE RELEASES INVENTORIED, 6/6 ORIGINAL T EVENT CONTRACTS RETAINED
STAGE21 SENSOR-LIKE COLUMN FILE COUNTS {'US-SP1': 0, 'US-SRG': 0, 'US-Seg': 0}
STAGE21 DECISION: THIS IS A SOURCE-AVAILABILITY INVENTORY, NOT A SENSOR VALIDATION
STAGE21 IF NO INDEPENDENT RAW SENSOR+TIMESTAMP QC IDENTIFIED: STOP INTERNAL-ONLY ESCALATION; REQUEST ORIGINAL SITE RECORDS
STAGE21 8/8 ORIGINAL T SCIENCE HOLDS PRESERVED; US-Syv 606 OLD HOLDS + 10 STAGE07 ERA EDGE SKIPS DEFERRED
STAGE21 READ ONLY: NO SOURCE/QA/QC/CDS/POST-v5/DATM/CIME/SLURM/MODEL WRITES
```

**Decision: STOP creating new incremental internal-only temperature QC stages.** Independent original sensor measurements, source-side QC, logger timestamp timezone, sensor level/height, any calibration/maintenance/event notes and met/air-temperature processing provenance must now be requested from station data holders or independently validated AmeriFlux BASE data. **Stage21 did not inspect AmeriFlux BASE**; those are distinct data products and may include measurement channels absent from FLUXNET products. A BASE column, if available, must still be verified before accepting it as independent evidence.

Continue non-temperature workstreams as scientifically appropriate only when independent of these held forcing decisions. **No Post-v5 release, DATM/CIME/Slurm preparation, or CLM-FATES spinup authorisation for these unresolved research sources.**

**Next:** [original sensor data request protocol and verified AmeriFlux site contacts](STAGE21_SITE_OPERATOR_TEMPERATURE_REQUESTS_2026-10-25.md), with no message yet sent.

**Code and pinned reproduction:** [Stage21 read-only source script](../scripts/stage21/21_audit_original_release_temperature_source_coverage.py); [Stage21 original operator commands](STAGE21_FINAL_ORIGINAL_TEMPERATURE_SOURCE_AVAILABILITY_NEXT_2026-10-25.md).
