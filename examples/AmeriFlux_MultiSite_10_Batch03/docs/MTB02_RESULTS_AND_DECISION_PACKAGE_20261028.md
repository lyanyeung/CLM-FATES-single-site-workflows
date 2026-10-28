# US-MtB MtB02 `--check` results and decision package (2026-10-28 19:55 UK)

The run was read-only: nothing was written to the forcing. The predeclared verdicts were:
- temperature bridge gate: **FAIL**, because the 22 HH length fails;
- humidity `METHOD_PASS`: **NONE**.

The decisions below belong to the user.

## T. Tower temperature

### T-a. 2022 cold fault (user criterion: constant and no analogue) — 27 HH

The flatline rule caught 21 HH on 2022-12-04 18:00 – 12-05 04:00. TA_F stays between −39.32 and −39.28 °C while TA_ERA is about +5.6 °C.

The other 6 HH were not caught as flatline and landed under REVIEW:
- 2022-10-22 11:30–13:30 (5 HH). TA_F falls from −26.2 to −39.3 °C at midday while TA_ERA is +13.3 °C.
- 2022-12-04 17:30 (1 HH), at −36.08 °C, the onset of the December failure.

All 27 HH are QC0. All are treated as an instrument fault: they are removed from the truth, together with their VPD.

### T-b. Warm constant runs — 10 runs, about 53 HH, not previously known

The tower holds a constant +9.4 to +13.3 °C at night in December or November, while TA_ERA is about 0 °C. Examples:
- 2013-12-17, 7 HH at exactly 13.33 °C;
- 2011-12-29, 4 HH at exactly 9.444 °C;
- 2013-12-10, 12.22 °C.

Several of these values are exact whole °F: 13.33 °C = 56 °F, 12.22 °C = 54 °F, 9.444 °C = 49 °F. That suggests a substituted source with 1 °F resolution, even though the records carry TA_F_QC = 0. A mountain top can be warmer than a valley-based grid during a night inversion, but readings that stay exactly constant for hours are suspect.

### T-c. Floor at −10 °C, 2013–2020 — source censoring

In 2013–2020 there are **no** TA_F values below −10.0 °C. Values pile up in the [−10.0, −9.9) bin (2013: 18 there against 8 in the next bin).

In 2010–2012 and 2021–2024 values do go below −10 °C (2011: 118; 2023: 110). The cold extremes for 2013–2020 are therefore probably clipped at −10 °C in the FLUXMET release. This cannot be repaired from FLUXMET alone. The AmeriFlux BASE file (TA_1_1_1) or the site PI would be needed.

### T-d. February 2011 event — keep

The tower reads −24.0 to −17.6 °C for 29 HH from 2011-02-02 21:00 to 02-03 11:00, varying throughout. This coincides with the documented February 3, 2011 Southwest cold outbreak: Tucson International Airport recorded 18 °F, a record low. The episode is plausibly real.

### Bridge for the faults

The bridge uses the ERA shape anchored on tower QC0 within ± 2 h. Validation on 2000 synthetic gaps per length:

| Gap length | MAE | Bias | Fraction > 3 °C | Gate |
| --- | --- | --- | --- | --- |
| 5 HH | 0.78 °C | +0.00 °C | 1.3 % | PASS |
| 22 HH | 1.67 °C | −0.10 °C | 15.9 % | FAIL |

So the 5 HH October fault has a validated bridge length; this needs one more run, because those 5 HH sit under REVIEW. The 21–22 HH December fault does **not**. Run 2013-01-15 (QC1, no anchors) stays on HOLD.

## H. Humidity in the gap regime (TA_F − TA_ERA ≤ −5 °C, fault rows removed)

| Method | Pooled N | Pooled MAE / bias / > 2 hPa | Cold-regime > 2 hPa | Years passing / gated | METHOD_PASS |
| --- | --- | --- | --- | --- | --- |
| **COMPANION_E** | 10 970 | **0.94 / +0.27 / 8.3 % (PASS)** | 6.0 % | **12 / 15** | NO |
| EMP_ADJ_RH | 10 970 | 1.05 / −0.12 / 11.4 % | 7.7 % | 7 / 15 | NO |

COMPANION_E fails only in 2015 (14.9 %), 2017 (10.8 %) and 2018 (10.3 %), each on the > 2 hPa share. By season it is good in DJF (4.7 %) and MAM (7.6 %), weak in SON (18.8 %) and poor in JJA (61 %, N = 118).

**Coverage of the 2840 gaps plus the fault rows, under COMPANION_E:**

| Class | Count |
| --- | --- |
| Candidate if approved | 2808 |
| HOLD, out of regime | 75 |
| HOLD, not formable | 29 |
| HOLD, fault with no bridge | 8 |

## Four frozen-phase points (2024-02-11 05:00–06:30)

The installed CDEPS 1.0.105 `datm_eSat` uses the Flatau polynomial over ice when `tbot` < 273.15 K. A specific-humidity stream is capped at that saturation value.

The GRID_RH candidate gives RH_ice of **100.5 / 102.6 / 103.6 / 102.9 %** under the DATM polynomial. **All four would be silently capped** to ice saturation. The installed model therefore does not accept them: by the user's rule they are not kept as GRID_RH.

Under COMPANION_E these four points are ordinary candidates, not ice-supersaturated.

## Decisions for the user

1. **Humidity.** Choose one:
   - **(A)** strict HOLD of all gaps, which means no complete US-MtB forcing;
   - **(B)** adopt COMPANION_E for the 2808 candidates, labelled "pooled gate PASS, 12/15 years, known weak in SON/JJA", and keep 112 on HOLD;
   - **(C)** a further predeclared test. This is not recommended, because each new iteration after seeing results adds selection risk.
2. **T-a December fault (21–22 HH).** Choose one: HOLD, or the unvalidated bridge labelled as such. The October 5 HH can take the validated bridge if approved.
3. **T-b warm constant runs.** Treat them as faults (bridge where the gap length is ≤ 5 HH), or keep them.
4. **T-c −10 °C floor.** Accept it as documented, or pull the BASE TA_1_1_1 record to test the clipping.

Sources: [Tucson Sentinel, 3 Feb 2011: Tucson record low 18 °F](https://www.tucsonsentinel.com/local/report/020311_tucson_record_cold/); [NWS Tucson February climate](https://weather.gov/media/twc/climate/February.pdf).
