# AmeriFlux Batch05 — investigator humidity decisions, 2026-10-26

## Explicit user decisions recorded

1. **G01 — US-WCr, 2025-08-25 13:00 to 2025-08-26 01:30, 26 P1 QC0/0**: original RH≈0 replaced **in a diagnostic candidate only** by source-processed ERA-inferred RH. Preserve original measured `TA_F`. Recompute VPD coherently from original temperature and reference RH. Do **not** directly substitute `VPD_ERA`: source ERA temperature differs.
2. **G02 — US-Vcm, 2007-12-15/16**: user asks if original/source ERA RH is negative. **Yes:** native original RH in all 19 P1 half-hours is missing (-9999); ERA water-Magnus RH from native source `TA_ERA` and `VPD_ERA` is between roughly -0.71 and -12.21%. `TA_F_QC=2, VPD_F_QC=2`, so there is no measured tower TA or original RH for these 19. Preserve **HOLD_NO_REPLACEMENT_SOURCE**. Independent reference or source processor diagnostics required; cannot re-use negative ERA RH.
3. **G03 — US-Vcm, 2007-01-16 22:00 to 2007-01-17 14:30, 34 HH including BEFORE, P1, AFTER**: user instructs using existing native original `RH` for all windows/transition periods, not just 10 anomalous QC2 source VPDs. Native original RH exists for **all 34 HH**. Calculate `VPD_new=es_water(TA_F)*(1-RH_original/100)` using original selected `TA_F` at each time, while recording original TA/VPD/QC. Note 20 QC0/0 original pairs already largely agree; QC1 09:00 original RH gives some difference from MDS VPD; this full 34-HH scientific reconstruction is user-requested.
4. **G04 — US-Vcm, 2008-02-06**: native original RH is missing for **all 38** native context HH (including 12 P1); 11 of the 12 have formula-negative ERA RH; one RH≈0.63% not formula negative. HOLD. No original RH exists to reconstruct from.
5. **G05 — US-Vcm, 2024-11-21 19:00 to 2024-11-22 20:00, 26 P1 QC0/0**: user authorizes using processed source ERA-inferred RH but **preserving original measured tower `TA_F`**. Convert to consistent VPD by `es(TA_F)*(1-RH_ERA/100)`. Do **not** substitute source `VPD_ERA`. Nearby non-P1 RH<5% events are not covered by these exact 26 P1 decisions and remain unchanged pending explicit scope/continuity verification.
6. **G06 — US-Vcm, 2025-10-13/14**: user authorizes replacing extreme-low RH by processed ERA-inferred RH, preserving QC0 tower TA where available and recomputing VPD. **All 31 original source RH<1% rows are selected**, including **23 exact P1 QC0/0** records and **eight extra QC1/1** rows whose raw RH is ≈0.3% while selected MDS VPD itself yields 66–83% RH. The 8 QC1 source rows are labeled separately, preserving original MDS VPD and QC values in audit; reconstructed candidate VPD with selected MDS TA is a user-requested alternative, not an automatic approval of MDS source replacement.
7. **G07 — US-Vcp, 2011-01-01 07:00–08:00**: original RH is missing for all **3** QC2/2 P1 HH. Source ERA-inferred RH = -6.00%, -6.20%, -6.42%. Original tower RH first reappears in context at **09:30 68.05389% QC0/0**, then at **11:00 49.83034% QC0/0**. These are **not contemporaneous** replacements for 07:00–08:00. HOLD.

## Repair candidate (Stage20) and provenance

[Stage20 exact original-native source-pair user decision candidate generator](../scripts/stage20/20_make_investigator_decision_candidate_overlay_readonly.py) draws from the *already SHA-verified original Stage18 775-HH context reports*. It exports a NEW candidate-only ledger with G01 26 + G03 34 + G05 26 + G06 31 = **117** RH/VPD candidate HH (G06 QC0 23 / QC1 8 separately sourced), plus a **34-row science HOLD ledger**: G02 19, G04 12, G07 3. The script **never overwrites original FLUXMET files, QC0 observational labels, DATM forcing, CLM-FATES cases, or Slurm jobs**.

The selected formula is the same as Stage10–19 water Magnus diagnostic:
```text
es_water(T_C) = 6.112 * exp(17.67*T_C/(T_C+243.5))   [hPa]
ERA_source_RH_pct = 100 * (1 - VPD_ERA/es_water(TA_ERA))
candidate_VPD_hPa = es_water(TA_F) * (1 - RH_target_pct/100)
```
For G03 `RH_target_pct` comes from the **native original tower RH field**, for G01/G05/G06 from the **source-provided processed ERA pair**. For G05/G06, the tower air temperature is retained **exactly** and never substituted by ERA temperature. New provenance labels must explicitly state reconstructed/processed humidities, not claim original measured QC0 for altered VPD. Formula coherence alone does not independently validate meteorology; long-term native source tower humidity vs ERA discrepancies at near-zero RH may reflect instrument/processing failure, site spatial representativeness or time alignment.

**Source ERA verification limit:** original FLUXMET `TA_ERA/VPD_ERA` are source-provided processed ERA variables; these were **not independently downloaded ERA5/ERA5-Land**, and their exact reanalysis lineage/version has not been independently established. This remains relevant for physically suspicious G05 tower-vs-ERA T differences.

## Numerical candidate examples, not written to forcing

| Group and original native time | Original TA (°C) | Original VPD (hPa) | Target RH (%) | Recomputed VPD using original TA (hPa) |
|---|---:|---:|---:|---:|
| G01 WCr 2025-08-25 13:00 | 15.485 | 17.599 | 63.78379 | 6.367 |
| G01 WCr 2025-08-26 01:30 | 8.443 | 11.059 | 90.214992 | 1.081 |
| G03 Vcm 2007-01-17 04:00 | -14.254 | 2.387 | original RH 89.08233 | 0.222 |
| G03 Vcm 2007-01-17 05:00 | -14.623 | 2.380 | original RH 88.02724 | 0.237 |
| G05 Vcm 2024-11-22 07:30 | 4.316 | 8.279 | 12.556896 | 7.270 |
| G06 Vcm 2025-10-14 07:00 | 14.233 | 16.181 | 74.915212 | 4.068 |

The correction objective is physically coherent **candidate RH and VPD** at the same preserved `TA_F`. In G03, all 34 source RH rows are explicitly included even where no abnormality exists to prevent artificial approach/exit discontinuities. Investigators should screen VPD/temperature/RH transitions at each candidate segment boundary before a production forcing writer is used.

## Stage20 initial execution status

Code on GitHub only; no operator IRIDIS6 Stage20 output yet. This is a scientific-authorized proposed *direction*, not a claim that production forcing was modified. All originals preserved.
