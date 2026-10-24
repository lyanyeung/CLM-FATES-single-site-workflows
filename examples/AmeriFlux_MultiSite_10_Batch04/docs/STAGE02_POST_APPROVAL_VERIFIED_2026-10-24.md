# Batch04 — Stage02 final metadata recheck after approved US-Seg BIF 1495

**Operator execution date:** 2026-10-24  
**Verification basis:** operator-supplied full IRIDIS6 terminal output of the updated read-only `02_check_batch04_metadata.py` together with published `coordinate_decisions.tsv`. This is not an independent remote cluster run by the assistant.

**Actual program result:**
```text
STAGE02 SUMMARY: 10/10 coordinate + first-interval checks PASS; failures: none
No raw data, surfaces, forcing, model cases, Slurm jobs or reports written.
```

| Site | IGBP | Site latitude | Site longitude | Coordinate provenance | Native first interval |
| --- | --- | ---: | ---: | --- | --- |
| US-Rpf | DBF | 65.1198 | -147.4290 | RELEASE_BIF | 30 min HH |
| US-Seg | GRA | **34.3623** | **-106.7020** | **RELEASE_BIF_APPROVED_GROUP_1495** | 30 min HH |
| US-Ses | OSH | 34.3349 | -106.7442 | RELEASE_BIF | 30 min HH |
| US-Slt | DBF | 39.9138 | -74.5960 | RELEASE_BIF | 30 min HH |
| US-SP1 | ENF | 29.7381 | -82.2188 | RELEASE_BIF | 30 min HH |
| US-SRG | GRA | 31.7894 | -110.8277 | RELEASE_BIF | 30 min HH |
| US-SRM | WSA | 31.8214 | -110.8661 | RELEASE_BIF | 30 min HH |
| US-Syv | MF | 46.2420 | -89.3477 | RELEASE_BIF | 30 min HH |
| US-Ton | WSA | 38.4309 | -120.9660 | RELEASE_BIF | 30 min HH |
| US-Uaf | ENF | 64.8663 | -147.8555 | RELEASE_BIF | 30 min HH |

## US-Seg approval verification

The updated checker explicitly reported:
```text
COORDINATES: LAT=34.3623 LON=-106.702
APPROVED SITE ELEVATION: 1596.0 m | APPROVED_BY_USER | GROUP_ID 1495 | start 200701010000
IGBP LABELS: GRA
COORDINATE SOURCE: RELEASE_BIF_APPROVED_GROUP_1495
PASS: coordinate + first-interval preflight only
```

Approved values were validated against the original BIF group pairing and start date. `-106.702` is Python's numeric display for approved longitude `-106.7020`, not a changed value. Original BIF GROUP_ID 1479 remains intact for traceability, but is not an operational location option for this experiment.

**Final metadata gate:** **10/10 PASS**; this closes the US-Seg coordinate conflict **for this experiment**. It does not approve PFT fractions, meteorological measurement height/ZBOT, site surfaces, meteorological QC or FATES forcing.

**Independent scientific gate:** Stage02C full HH time continuity also previously passed 10/10, but severe forcing anomalies remain on US-SP1, US-Syv and US-Ton; see [Stage02C HH/QC ledger](STAGE02C_FULL_HH_TIME_QC_AUDIT_2026-10-24.md). **QC SCIENCE HOLD**, no source replacement or model run approved.
