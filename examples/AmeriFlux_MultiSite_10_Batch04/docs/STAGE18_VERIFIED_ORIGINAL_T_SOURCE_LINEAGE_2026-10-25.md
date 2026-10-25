# Batch04 Stage18 — VERIFIED original FLUXMET temperature source lineage (IRIDIS6 2026-10-25)

**Status: OPERATOR-VERIFIED PASS (6/6).** The original Stage18 `--self-test` and `--audit` completed on IRIDIS6. The data below are transcribed from operator stdout. This is read-only evidence, **not an approval to rewrite original TA/QC0 or use candidate forcing in DATM/CIME/CLM-FATES**.

**Final operator output:**
```text
STAGE18 RESULT: 6/6 NATIVE FLUXMET PROVENANCE WINDOWS AUDITED; 8/8 ORIGINAL T SCIENCE HOLDS PRESERVED
STAGE18 US-Syv 606 OLD HOLDS + 10 STAGE07 ERA JUMP SKIPS DEFERRED
STAGE18 READ ONLY: NO ORIGINAL/DERIVED SOURCE, CDS, DATM, CIME, SLURM OR MODEL WRITES
```

## Original tower source integrity

| Site | Original FLUXMET full-source SHA256 | HH rows | Original columns present | BIF original fixed UTC offset |
| --- | --- | ---: | --- | --- |
| US-SP1 | `d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963` | 368208 | `TA_F_MDS`, `TA_F_MDS_QC`, `TA_ERA`, `TA_F`, `TA_F_QC` | −5 h |
| US-SRG | `bce57eebcce1babf9f9310e76c8f41451a8e3632c8d08a95f03345e35a189567` | 315600 | same five columns | −7 h |
| US-Seg | `2fc2fc1c846749070f62c981b0f71789bdc9dae7585eeb0b0f30455a9e88034d` | 333120 | same five columns | −7 h |

Original BIF points verified: US-SP1 29.7381, −82.2188; US-SRG 31.7894, −110.8277; US-Seg 34.3623, −106.7020 (approved original BIF group 1495). SHA checks passed against earlier evidence.

**QC meaning:** The official FLUXNET FULLSET variable specification defines `TA_F_QC=0` as measured, `1` as good quality MDS gapfill, and `2` as downscaled ERA substitution. `TA_F_MDS_QC=0` denotes measured input. A `TA_F=TA_F_MDS` equality for QC0 is expected ONEFlux lineage, **not two independent instrument confirmations**. `TA_ERA` is a processed ERA-derived reference, not a second tower sensor. Original v1.3 instrument-level evidence still requires verification; these semantics are based on the published FLUXNET2015/ONEFlux convention. References: https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/ and https://www.nature.com/articles/s41597-020-0534-3.

## Six exact target events from original FLUXMET

| Site | Native time | TA_F °C QC0 | TA_F_MDS °C, MDS_QC | TA_ERA °C | original VPD_F hPa/QC |
| --- | --- | ---: | --- | ---: | --- |
| US-SP1 | 200710151730 | 11.150 | 11.150 / 0 | 25.919 | 14.025 / 2 |
| US-SP1 | 200801160800 | −8.211 | −8.211 / 0 | 8.569 | 6.148 / 1 |
| US-SP1 | 200801160830 | −4.365 | −4.365 / 0 | 8.555 | 6.597 / 1 |
| US-SP1 | 200802030800 | −3.613 | −3.613 / 0 | 11.410 | 4.717 / 1 |
| US-SRG | 201903191200 | 0.718 | 0.718 / 0 | 20.399 | 17.133 / 2 |
| US-Seg | 201612271800 | 0.015 | 0.015 / 0 | 8.273 | 7.037 / 2 |

All six original VPD values were physically incompatible with saturation vapour pressure at their original tower temperatures. Stage14 already recomputed RH/VPD numerically while **preserving original tower TA/QC0**, and it did not clear these scientific HOLDs.

### US-SP1 2007-10-15: sudden jump and repeated low reading on adjacent dates

Original tower QC0 TA at 17:00 **11.251°C**, 17:30 **11.150°C**, and 18:00 **23.220°C**, an abrupt **+12.070°C in 30 min**. `TA_ERA` at 17:30 is **25.919°C**; earlier 15:30–17:30 measured TA stayed around **11.15–12.25°C** against `TA_ERA` roughly **25.9–27.7°C**. Same-clock original TA on **2007-10-16 17:30 is 11.149°C**, and on **2007-10-17 17:30 is 11.169°C**; on Oct 13/14 at that clock TA was **23.720/23.060°C**. This repeated ≈11.15°C pattern is an important *possible* plateau/fallback/provenance clue, not proof of a stuck sensor. A fixed-value episode could span more than one point and should be audited across days before selecting corrections.

### US-SP1 2008-01-16 08:00/08:30: multi-hour measured cold regime

Original QC0 temperatures 06:00 −10.241°C, 06:30 −10.534°C, 07:00 −11.144°C, 07:30 −10.436°C, 08:00 −8.211°C, 08:30 −4.365°C, 09:00 −0.875°C and 09:30 2.027°C. `TA_ERA` remains roughly 8.5–9.2°C near those hours. Original `TA_F_MDS_QC=0` at both held events. This is not two independent one-half-hour anomalies and the co-occurring native series must be checked. Same-clock neighboring-day temperatures vary substantially (e.g. at 08:00 Jan 15 −3.727°C and Jan 17 −0.451°C).

### US-SP1 2008-02-03 08:00: another continuous winter cold regime

Original QC0 TA values 06:00 −4.651°C, 07:00 −5.145°C, 07:30 −6.588°C, 08:00 −3.613°C, 08:30 −0.565°C, 09:00 1.701°C, 09:30 4.358°C, 10:00 7.259°C. `TA_ERA` 08:00 is 11.410°C. Treat as a segment/source provenance concern; a single-point ERA override is unjustified.

### US-SRG 2019-03-19 12:00: strong single-point suspicion; independent tower anchors missing

11:30 original `TA_F=19.668°C, TA_F_QC=2, TA_ERA=19.668°C`; 12:00 `TA_F=0.718°C, QC=0, TA_F_MDS_QC=0, TA_ERA=20.399°C`; 12:30 `TA_F=20.605°C, QC=2, TA_ERA=20.605°C`. This is a **−18.950°C then +19.887°C** half-hour excursion in the consolidated series. Nearby QC2 `TA_F` equals `TA_ERA` **by processing design**, and those are not independent measured tower anchors. The 12:00 point is a **priority hypothesis** for an isolated source error, still **HOLD** pending raw met-channel, instrument QC, weather/event verification. A proposed correction, if warranted, must be isolated and separately versioned, not a claim of official measured TA.

### US-Seg 2016-12-27 18:00: plausible contiguous cooling

Original QC0 TA from 17:30 **4.332°C**, to 18:00 **0.015°C**, to 18:30 **−0.512°C**, 19:00 **−0.863°C**, and 19:30 **−1.491°C**. `TA_ERA=8.273°C` at 18:00, but original 30-minute observations form a continued cooling spell; on Dec 25 and 26 same-clock original values were **0.289°C** and **−0.222°C**. No automatic T substitution is supported. Verify met context if assessing its original QC.

## Independent decisions and next scientific gate

- Stage18 **6/6 audited** but **0 science temperature holds released**. Both prior US-SP1 Stage15 October 2000 two-point alternatives remain held: **8/8 original QC0 temperature science HOLDs** overall.
- Original `TA_F_MDS` and `TA_F` equality is not independent evidence; QC2 neighbours are ERA-derived and not measured tower validation.
- **Stage19 proposed next:** read-only multi-day analysis of US-SP1 2007-10 plateau/repetition and 2008 sustained cold-versus-ERA episodes, plus explicit US-SRG single-point source-lineage and US-Seg continuous cooling control; no original forcing or flags changed.
- US-Syv **606** original science HOLDs and **10** Stage07 skipped ERA jump endpoints remain deferred.
- No Post-v5, DATM, CIME, Slurm, CLM-FATES or spinup work is authorised.

**Reproducible prior script:** [Stage18 source](../scripts/stage18/18_original_tower_temperature_qc_source_lineage.py) and [pinned run instructions](STAGE18_ORIGINAL_TOWER_T_QC_LINEAGE_NEXT_2026-10-25.md).
