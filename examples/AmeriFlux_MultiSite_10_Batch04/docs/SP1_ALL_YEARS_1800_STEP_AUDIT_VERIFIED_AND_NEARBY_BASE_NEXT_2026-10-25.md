# Batch04 US-SP1 complete original FLUXNET 2000–2020 clock-locked 18:00 step scan — operator-verified

**2026-10-25 — original full native FLUXMET SHA verified; read-only census PASS.** The operator ran the [source-pinned script](../scripts/manual_review/audit_sp1_full_record_clock_locked_1800_jumps_readonly.py) over **368,208 original 30-min observations**, **7,671 unique days**. This records operator-returned stdout; no GitHub or external tool executed the script on IRIDIS6.

## Source and exact screen

```text
SP1 CLOCK_STEP SELF-TEST PASS: exact original 4-day anchor, QC0 and 18h threshold, read-only
SP1 ORIGINAL VERIFIED SHA d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963 native_rows 368208 day_records 7671
TOTAL_18H_10C_OR_GREATER_QC0_JUMPS 6
TOTAL_STRONG_CLOCK_LOCKED_18H_DAYS 6
STRONG_MONTH_COUNTS 200710:6
CONSECUTIVE_CALENDAR_DAY_CLUSTERS 2
CLUSTER 20071015 20071018 calendar_days 4
CLUSTER 20071022 20071023 calendar_days 2
SP1_AUDIT_COMPLETE READ_ONLY; NO SOURCE, QC, POST-v5, CIME OR MODEL WRITES
```

`17:30→18:00` temperature jump screen: both original `TA_F_QC=0` and jump **≥10°C within 30 minutes**. The more selective strong screen requires **at least 5 half-hours between 08:00 and 17:30** on the same date, each original `TA_F_QC=0` and `TA_F − TA_ERA ≤ −10°C`. These are **diagnostic, not an automatic error-repair threshold**. `TA_ERA` is the processed AmeriFlux FLUXNET ERA reference, not independent tower sensor validation.

## All six detected strong 18:00 events (all in October 2007)

| Native local standard date | 17:30 original TA_F / QC | 17:30 processed TA_ERA | 18:00 original TA_F / QC | 18:00 TA_ERA | Original TA jump (°C) | 08:00–17:30 QC0 cold-discrepant HH |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2007-10-15 | 11.150 / 0 | 25.919 | 23.220 / 0 | 24.817 | **+12.070** | 15 |
| 2007-10-16 | 11.149 / 0 | 26.276 | 23.220 / 0 | 25.258 | **+12.071** | 17 |
| 2007-10-17 | 11.169 / 0 | 26.313 | 23.710 / 0 | 25.437 | **+12.541** | 17 |
| 2007-10-18 | 11.138 / 0 | 27.470 | 26.240 / 0 | 26.963 | **+15.102** | 17 |
| 2007-10-22 | 11.126 / 0 | 25.779 | 23.390 / 0 | 25.337 | **+12.264** | 20 |
| 2007-10-23 | 11.123 / 0 | 29.301 | 25.570 / 0 | 28.476 | **+14.447** | 20 |

**New strong concern:** the six separate 17:30 original QC0 readings all fall within **11.123–11.169°C** (range **0.046°C**), then jump **+12.070–15.102°C** exactly at 18:00. The same clock-step recurs in **two distinct calendar blocks**; this is consistent with a clock-locked instrumentation, channel selection, repeated 11°C value or processing artifact, but **none of these mechanisms has been independently proven**. Do **not** correct only one timestamp or all 2007 days automatically.

## Other daytime cold-discrepancy days without this 18:00 step

The operator's count of dates with **≥5 QC0 daytime HH** at `TA_F−TA_ERA ≤−10°C` was:

| Original year | Days with ≥5 unusually cold QC0 daytime HH | Days with QC0 17:30→18:00 ≥10°C jump | Strong days fulfilling both |
| --- | ---: | ---: | ---: |
| 2000 | 1 | 0 | 0 |
| 2005 | 2 | 0 | 0 |
| 2007 | **33** | **6** | **6** |
| 2008 | **37** | 0 | 0 |

These larger sets **are not necessarily all scientifically erroneous**: they are screened against processed ERA, and their exact calendar-day lists and raw sensor explanations have not been established by this particular script. The fact 2008 has **37 daytime-cold days but zero qualifying 18:00 jumps** shows at least a different temporal pattern, not grounds to apply the 2007 repair hypothesis to 2008 wholesale.

## Most informative next evidence: BASE original TA from adjacent Florida slashpine towers

**Official AmeriFlux public site search** identifies three geographically nearby sites at ~50 m elevation with overlapping AmeriFlux BASE coverage for 2007–2008:

| Site | Coordinates (lat, lon) | Station elevation | AmeriFlux BASE years | Evidence value |
| --- | --- | ---: | --- | --- |
| [US-SP1](https://ameriflux.lbl.gov/sites/siteinfo/US-SP1) | 29.7381, −82.2188 | 50 m | 2000–2020 | Suspect station; compare native BASE air-temperature channels against its processed FLUXNET `TA_F` |
| [US-SP2](https://ameriflux.lbl.gov/sites/siteinfo/US-SP2) | 29.7648, −82.2448 | 50 m | 1999–2008 | **Independent nearby station**, covers 2007 Oct and 2008 Jan/Feb |
| [US-SP3](https://ameriflux.lbl.gov/sites/siteinfo/US-SP3) | 29.7548, −82.1633 | 50 m | 1999–2010 | **Another nearby station**, covers both periods |

The station coordinates/50m/site data availability come from AmeriFlux site search, checked 2026-10-25. Relative distances are approximately 3.9 km (SP2 to SP1) and 5.7 km (SP3 to SP1) from station coordinates; slight local microclimate differences are possible even if simultaneous air-temperature differences should not normally span ~15°C. **The BASE tower temperatures have NOT been downloaded or compared yet**. Different instrument heights, sensor QC conventions, data submission teams and logger/UTC offsets must be checked before claiming cross-site independence or physical validity.

Official [AmeriFlux BASE Download](https://ameriflux.lbl.gov/data/download-data/) and [BASE Publish information](https://ameriflux.lbl.gov/data/flux-data-products/base-publish/) note site products are original site-submitted flux/met records processed by AMP QA/QC and accompanied by BADM; BASE is **closer to site inputs than FLUXNET but not guaranteed raw logger data**. Select **BASE for US-SP1, US-SP2 and US-SP3** (2007 and 2008) plus BADM/measurement-height metadata; compare native high-frequency `TA`, `TA_1_1_1` and any `RH/VPD/PA` channels **only if they actually exist**, at correctly aligned local-standard timestamps.

For six October 2007 strong days, include **08:00–19:00**, at least 10/15–18 and 10/22–23, plus adjacent 10/19–21 and 10/24. For 2008, include **2008-01-15–17, 2008-02-02–04** at native HH or finer. Use raw station/QC/BADM records to discriminate sensor error from local meteorology; preserve all other data until verified.

**Science release decisions:** prior 3-point US-SP1-2000/US-SRG-2019 alternative has complete row-level technical integrity [PASS](MANUAL_THREE_T_FULL_SOURCE_AUDIT_VERIFIED_2026-10-25.md) but original source T science HOLDs **8/8 still present**; US-Syv **606 previous science holds + 10 Stage07 skipped ERA edge points** remain deferred. Neither this audit nor the BASE research suggestion authorises Post-v5/DATM/CIME/Slurm/CLM-FATES spinup. **Do not create another internal-only ERA comparison stage** in place of real new independent BASE/sensor evidence.
