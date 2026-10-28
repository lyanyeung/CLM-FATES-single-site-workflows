# US-MtB MtB01 `--check` results (IRIDIS6, 2026-10-28 19:46 UK)

The run was read-only. No repairs were made and no method is approved.

**Inputs**
- FLUXMET `AMF_US-MtB_FLUXNET_FLUXMET_HH_2009-2024_v1.3_r1.csv`, sha256 `67dc8fe0…`
- Companion ERA `AMF_US-MtB_FLUXNET_ERA5_HH_1981-2025_v1.3_r1.csv`, sha256 `42ac8fa2…`
- Stage12g `…083234Z_e168f29f`, timeline sha256 `af513cf0…`
- Verified ERA5-Land years: 2020, 2022 and 2024. The years 2010–2013, 2015–2018 and 2023 are not verified.
- CTSM `ctsm5.4.056` (`d5ea9d01`), CDEPS `cdeps1.0.105` (`af8c89fc`).

## A. The 2840 gaps sit almost entirely in one regime

- **Temperature difference:** dT = TA_F − TA_ERA is between −8 and −5 °C for **2555** gaps and ≤ −8 °C for **257** (99 % of the total). Only 28 gaps have dT > −5 °C.
- **Quality flags:** VPD_F_QC is 1 for 2305 gaps and 2 for 535. TA_F_QC is 0 for 2837 gaps.
- **Gap length:** gaps are mostly long. Runs of 13–48 HH contain 1292 gaps, runs of 5–12 HH 902, and runs of 1–4 HH 646. Only 57 gaps have QC0 anchors on both sides within ± 2 h, so short-gap interpolation is not a general route.
- **Stage12g reason:**
  - 1031 `HOLD_SITE_GRID_T_DIFF_GT5C`
  - 1325 with no verified ERA5-Land year
  - 4 ice holds
  - 480 not in the 2810 ledger (other upstream origin, still to be traced)

## B. Measured truth exists in the gap regime

There are 10 405 QC0 records (VPD_F_QC = TA_F_QC = 0) with dT in (−8, −5] and 589 with dT ≤ −8, spread over 2009–2024.

## C. Predeclared verdict: NO method passes

| Method | Yearly cold gate (years passing / 16) | Predeclared REGIME (\|dT\| > 5, pooled) MAE / bias / > 2 hPa | dT −8:−5 MAE / bias / > 2 hPa | dT ≤ −8 MAE / bias / > 2 hPa |
| --- | --- | --- | --- | --- |
| COMPANION_RH (the Stage12d formula) | 0 / 16 | 2.03 / −0.78 / 44.8 % | 1.52 / +1.41 / 30.1 % | 1.41 / +1.36 / 25.0 % |
| **COMPANION_E** | 7 / 16 | 1.05 / +0.02 / 11.9 % | **0.95 / +0.27 / 8.6 %** | **0.73 / +0.45 / 2.3 %** |
| EMP_BIN_RH | 2 / 16 | 1.28 / −0.04 / 20.0 % | 1.23 / −0.04 / 19.0 % | 0.81 / +0.09 / 6.5 % |
| EMP_ADJ_RH | 5 / 16 | 1.10 / −0.10 / 13.6 % | 1.06 / −0.12 / 11.8 % | 0.81 / +0.10 / 4.7 % |

**Interpretation.** These are hypotheses, not approvals:

- **The Stage12d formula is biased in the gap regime.** It carries the reanalysis RH down to the colder tower, which is biased by about +1.4 hPa there.
- **Keeping the reanalysis vapour pressure behaves best.** COMPANION_E keeps the companion vapour pressure and recomputes VPD at the tower temperature. On the tower-colder side it meets every Stage12j threshold.
- **The predeclared REGIME gate does not test the gap regime.** It pooled both signs of dT, and the tower-warmer side (dT > 5, 16 742 records, almost no gaps) pulls COMPANION_E to 11.9 %. That gate was therefore mis-specified relative to the gap population.
- **The one-sided result was found after the fact.** It must be confirmed by a newly predeclared, year-by-year test (MtB02) before anyone treats it as evidence.

## D. Tower temperature: 27 QC0 values near −39.3 °C in 2022 look like a sensor fault

| Episode | Length | TA_F | TA_ERA |
| --- | --- | --- | --- |
| 2022-10-22 11:30–13:30 | 5 HH | −39.27 °C | +13.3 °C (mean) |
| 2022-12-04 17:30 – 12-05 04:00 | 22 HH | −39.32 °C | +5.6 °C (mean) |

All of these records are flagged QC0. A midday October reading of −39 °C against +13 °C in the reanalysis is not physical. The value looks like an instrument floor or error reading.

This affects the **temperature forcing (TBOT)** itself, not only humidity. It is a separate decision for the user. Nothing was changed.

Two further observations:
- 2011 has 21 HH below −20 °C (minimum −24.0 °C). This may be the real early-February 2011 cold outbreak and needs its context checked.
- In 8 of 16 years the yearly TA_F minimum is between −10.0 and −9.8 °C. This could be a lower clipping or filter in the source and is still to be checked.

## E/F. Four 2024-02-11 frozen-phase points

| | Value |
| --- | --- |
| Tower T | −8.39 to −8.64 °C |
| Grid T | −3.6 to −4.4 °C |
| GRID_RH (ERA5-Land RH at tower T) RH_ice | 100.5–103.5 % (Magnus), QBOT ≈ 0.0025 kg kg⁻¹ |
| COMPANION_RH RH_ice | ≈ 34 % |

The installed CDEPS `datm_datamode_clmncep_mod.F90` caps a specific-humidity stream at saturation (`if (qsat < strm_Sa_shum) Sa_shum = qsat`, with `e = datm_esat(tbot,tbot)`). Supersaturated QBOT is therefore silently limited rather than rejected.

Whether these four points exceed the cap depends on the exact ice formula in `datm_esat`; the Magnus excess is only 0.5–3.5 %. The function body must be read before the four points can be decided.

## Next (proposed, awaiting user agreement)

1. **`--run`.** Writes the CSV tables and SHA receipt into a new report folder only.
2. **Read `datm_esat`** in the installed CDEPS and compute the cap for the four points exactly.
3. **MtB02, predeclared confirmation.**
   - Test COMPANION_E against QC0 records in the gap regime (dT ≤ −5 °C, tower colder), with a runner-up method.
   - Apply the same five thresholds per year (years with N ≥ 50), and also to the cold subset and by season and hour.
   - Exclude the 27 suspect −39 °C records from the truth.
   - Report the remaining HOLD: the 28 gaps outside the regime and any non-formable ones.
4. **User decision** on the 27 suspect −39 °C TA_F values.

## User criterion and MtB02 (28 Oct 19:50)

The user's criterion: a cold value can be real only if the same period of the record has comparable values **and** the reading is not constant.

The 2022 values fail both tests:
- **Constant:** 27 HH lie within about 0.05 °C of −39.3 °C, including 22 consecutive HH.
- **No analogue:** the other 15 years have minima of −7 to −24 °C.

Decision (Claude, delegated by the user):
- Classify these rows as an instrument fault.
- Remove them, and their VPD (which comes from the same probe), from the validation truth.
- Do not carry −39 °C into the forcing; produce a validated replacement candidate instead.

[MtB02](../scripts/mtb/MtB02_temperature_fault_bridge_and_humidity_confirmation_READONLY.py) predeclares the following rules:

| Part | Rule |
| --- | --- |
| Fault | FLATLINE = ≥ 4 HH with range ≤ 0.1 °C and \|TA_F − TA_ERA\| > 10 °C |
| Review | REVIEW = below the other years' same-month minimum by more than 5 °C. These rows are reported with context and not excluded; the February 2011 cold event is expected to fall here. |
| Floor check | Histogram of TA_F near −10 °C |
| Replacement candidate | ERA-shape bridge anchored on tower QC0 ± 2 h. It is validated on 2000 synthetic gaps of 5 and 22 HH, and passes if MAE ≤ 1.5 °C, \|bias\| ≤ 0.5 °C and ≤ 10 % of errors exceed 3 °C. |
| Humidity confirmation | COMPANION_E, with EMP_ADJ_RH as runner-up, on QC0 truth with TA_F − TA_ERA ≤ −5 °C. It must pass the five Stage12j thresholds pooled and in every year with N ≥ 50, with at least 5 such years. |
| Coverage | Every gap (plus the fault rows) is classed as `CANDIDATE_IF_APPROVED` or one of the `HOLD_*` reasons. |
