# AmeriFlux Batch04 Stage19 — IRIDIS6 operator-verified multi-day original temperature regime audit

**Status: VERIFIED PASS, 6/6 events analysed, 8/8 original tower-temperature science HOLDs preserved.** Based on the operator's complete Stage19 stdout from 2026-10-25. The GitHub repository records these operator results; the GitHub tool did not execute the model or this audit on IRIDIS6.

```text
STAGE19 RESULT: 6/6 MULTI-DAY NATIVE TEMPERATURE REGIMES REVIEWED; 8/8 T SCIENCE HOLDS PRESERVED
STAGE19 US-Syv 606 SCIENCE HOLDS AND 10 STAGE07 SKIPPED ERA EDGES DEFERRED
STAGE19 READ ONLY: ZERO SOURCE, QC, CDS, POST-v5, DATM, CIME, SLURM OR MODEL WRITES
```

## Immutable original-source and clock verification

| Site | Original FLUXMET SHA256 | Rows | BIF UTC offset |
| --- | --- | ---: | ---: |
| US-SP1 | `d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963` | 368208 | −5 h |
| US-SRG | `bce57eebcce1babf9f9310e76c8f41451a8e3632c8d08a95f03345e35a189567` | 315600 | −7 h |
| US-Seg | `2fc2fc1c846749070f62c981b0f71789bdc9dae7585eeb0b0f30455a9e88034d` | 333120 | −7 h |

Stage19 source integrity and BIF/source time offset tests passed. All six event timestamps retain original `TA_F_QC=0`. Stage19 tested **original `TA_F - TA_ERA <= -10 °C`**, an *exploratory grid-reference discrepancy threshold*, **not** a validated erroneous-temperature definition. Event-specific windows are ±3 days (289 inclusive HH each); January 16 08:00/08:30 windows heavily overlap and counts **must not be added** as separate events.

## Six event-level results

| Site, native local time | Original QC0 TA °C | TA_ERA °C | TA−TA_ERA °C | ±3d source QC counts 0/1/2 | HH with T−ERA≤−10°C / episodes | Longest episode |
| --- | ---: | ---: | ---: | --- | --- | --- |
| US-SP1 2007-10-15 17:30 | 11.150 | 25.919 | −14.769 | 289/0/0 | 66 / 5 | 17 HH = 8.5 hours |
| US-SP1 2008-01-16 08:00 | −8.211 | 8.569 | −16.780 | 289/0/0 | 85 / 4 | 44 HH = 22 hours |
| US-SP1 2008-01-16 08:30 | −4.365 | 8.555 | −12.920 | 289/0/0 | 86 / 4 | 44 HH = 22 hours |
| US-SP1 2008-02-03 08:00 | −3.613 | 11.410 | −15.023 | 289/0/0 | 56 / 7 | 19 HH = 9.5 hours |
| US-SRG 2019-03-19 12:00 | 0.718 | 20.399 | −19.681 | 231/16/42 | 1 / 1 | 1 HH = 0.5 hours |
| US-Seg 2016-12-27 18:00 | 0.015 | 8.273 | −8.258 | 289/0/0 | 0 / 0 | None |

**Source terminology:** HH=30-min half-hour, `TA_ERA`=processed ERA-derived time series in the original FLUXNET package, *not another original thermometer*. QC2 consolidated `TA_F` values indicate ERA-derived gap fill and are not independent tower data.

## US-SP1 2007-10-15: recurring daytime discrepancies, not a confirmed 11.15°C stuck sensor

The Oct 15 ±3-day analysis found **66 half-hours in five discrete episodes** with `TA_F - TA_ERA ≤ −10°C`. Four substantial daytime episodes were:
- Oct 15 **11:00–17:30**, 14 HH, original TA range 11.150–15.408°C.
- Oct 16 **09:30–17:30**, 17 HH, TA range 11.149–12.932°C.
- Oct 17 **09:30–17:30**, 17 HH, TA range 11.169–13.201°C.
- Oct 18 **09:30–17:30**, 17 HH, TA range 11.138–15.268°C.
- Oct 15 10:00, 1 HH, was isolated with respect to the exploratory −10°C threshold.

The separate narrow-value screen (`|TA_F−11.15°C|≤0.05°C`) found **10 half-hours in eight short episodes**, longest only **2 HH**; there is **no direct evidence here for a single multi-day constant-value plateau**. The *time-of-day-locked discrepancy*, however, is reproducible and merits instrument/clock/radiation provenance review. Same 17:30 clock values Oct 13–17 were **23.720, 23.060, 11.150, 11.149, 11.169°C**, all original QC0. This is an observational pattern, not proof of sensor malfunction, 12-hour clock error or a particular alternative forcing.

## US-SP1 2008-01-16: linked 22-hour/13.5-hour temperature discrepancy segments

The original QC0 temperature versus `TA_ERA` residual threshold detects:
- **Jan 16 15:30–Jan 17 13:00: 44 HH (22 h)**.
- **Jan 15 19:30–Jan 16 08:30: 27 HH (13.5 h)**.
- A further 6 HH episode Jan 17 17:00–19:30, plus an 8–9 HH Jan 19 early-morning episode near the edge of the overlapping ±3-day windows.

The 08:00 and 08:30 centre times are **the same January 2008 phenomenon**, with windows shifted by 30 minutes. Their total 85 versus 86 half-hours should not be interpreted as independent additive evidence. The original `TA_F_MDS_QC=0` at both targets comes from ONEFlux field lineage, not second-sensor replication. A pointwise overwrite at only those two HH is scientifically indefensible without external station checks.

## US-SP1 2008-02-03: overnight discrepancies persist

The threshold found **56 HH in 7 episodes**; longest **Feb 02 23:30–Feb 03 08:30 (19 HH = 9.5 h)** with original temperature −6.588 to 1.929°C. This is not only the Feb 03 08:00 target. Significant original tower-vs-downscaled-ERA mismatch does **not** establish which series is the truthful air temperature.

## US-SRG 2019-03-19: strongest individual-cell discrepancy

The original QC0 12:00 TA **0.718°C** versus `TA_ERA=20.399°C` is the **only** original QC0 half-hour satisfying `TA−ERA≤−10°C` among the 289 local HH analysed. Original consolidated `TA_F=19.668/20.605°C` in adjacent half-hours is QC2 and equals `TA_ERA`, **not two independent tower observations**. Same-clock tower QC0 observations on March 17, 18 and 21 are 18.850, 19.920, 15.960°C. This supports **priority raw-source investigation** and an *isolated trial-only* hypothesis, not an automatic source/QC correction.

## US-Seg 2016-12-27: original continuous cooling remains plausible

All **289** examined half-hours have original `TA_F_QC=0`, with **zero** original `TA−TA_ERA≤−10°C` threshold hits. The target 18:00 difference is −8.258°C, so passing this threshold screen does **not** by itself validate its physically impossible original VPD pairing. Prior Stage14 humidity-only closure and eight original temperature HOLDs remain. Original neighbouring clock samples at 18:00 Dec 25/26/27/28/29 were 0.289, −0.222, 0.015, 7.235, −0.207°C. Together with the continuous cooling on Dec 27, this supports preserving the original temperature pending source/weather review.

## Science decisions, future branch criteria

1. **All original temperature science HOLDs remain 8/8.** Stage15 two-US-SP1-point alternative is a *separate sensitivity product*, never an accepted tower data correction.
2. **US-SP1 long stretches:** do not automatically substitute ERA or interpolate each flagged HH. Request original instrument/raw tower temperature and source QC history, inspect sensor timing and measurement-height metadata, and compare any independent nearby observations before deciding on an alternative forcing.
3. **US-SRG one HH:** strongest one-cell candidate; explicitly verify raw tower measurement metadata and decide whether a nonproduction trial is justified. ERA-filled flanks cannot prove the true temperature at 12:00.
4. **US-Seg:** retain tower original, leave its original VPD/T scientific hold unresolved; no Stage19 temperature repair.
5. **US-Syv** 606 inherited science HOLDs and 10 skipped Stage07 ERA endpoints remain deferred.
6. No new source, forcing, Post-v5, DATM/CIME, Slurm or model spinup was created or authorised by Stage19.

**Reproduce:** [Stage19 pinned source/run instructions](STAGE19_MULTIDAY_ORIGINAL_TEMPERATURE_AUDIT_NEXT_2026-10-25.md). **Planned next investigation:** a narrowly scoped, read-only **Stage20 original AmeriFlux BIF instrument/QC provenance check**, focused on whether original sensor metadata can distinguish US-SP1 systematic segments and US-SRG's isolated QC0 spike. Absent such proof, report `EVIDENCE_INSUFFICIENT` instead of inventing a fix.
