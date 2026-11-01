# JapanFlux Stage05F — actual final 8/8 selected-F vs ERA-source impact (2026-11-01)

## Evidence

Operator supplied the complete terminal summary from eight successful site executions of the [Stage05F read-only source event impact audit](../scripts/stage05/05f_source_event_selected_forcing_impact_READONLY.py). All eight returned `READONLY_SOURCE_IMPACT_SCREEN_COMPLETE`; `STAGE05F SUMMARY: 8 / 8`. These are exact-event full selected-F vs source `*_ERA` screens, *not* a complete forcing-science acceptance. Stage05D has already confirmed companion ERA5-source defects in 8 of 9 JPF stations; `JP-Api` did not trigger that screening.

| Site | ERA5 abnormal site×half-hour starts inside FLUXMET_HH | Outside FLUXMET_HH | Selected TA_F flags | Selected PA_F flags | Selected LW_IN_F flags | Exact Stage05F raw QC and source comparisons |
|---|---:|---:|---:|---:|---:|---|
| JP-Fhk | 8 | 12 | 0 | 0 | 0 | TA 6× QC0 DIFFERENT; PA 2× QC0 DIFFERENT; LW 4× QC0 DIFFERENT |
| JP-Fjy | 8 | 12 | 0 | 6 | 0 | PA 6× QC2 EQUAL; TA 6× QC0 DIFFERENT; LW 4× QC0 DIFFERENT |
| JP-Khw | 8 | 12 | 3 | 6 | 2 | TA 3× QC2 EQUAL / 3× QC0 DIFFERENT; PA 6× QC2 EQUAL; LW 2× QC2 EQUAL / 2× QC0 DIFFERENT |
| JP-Spp | 6 | 9 | 0 | 0 | 0 | TA 6× QC0 DIFFERENT; PA 2× QC0 DIFFERENT; LW no Stage05D flag |
| JP-Tak | 9 | 6 | 0 | 0 | 0 | TA 9× QC0 DIFFERENT; PA 3× QC0 DIFFERENT; LW no Stage05D flag |
| JP-Tef | 12 | 8 | 0 | 0 | 4 | LW 4× QC2 EQUAL / 2× QC0 DIFFERENT; TA 9× QC0 DIFFERENT; PA 3× QC0 DIFFERENT |
| JP-Tmd | 12 | 8 | 3 | 9 | 2 | TA 3× QC2 EQUAL / 6× QC0 DIFFERENT; PA 9× QC2 EQUAL; LW 2× QC2 EQUAL / 4× QC0 DIFFERENT |
| JP-Yms | 12 | 8 | 0 | 2 | 4 | LW 4× QC2 EQUAL / 2× QC0 DIFFERENT; PA 2× QC2 EQUAL / 1× QC0 DIFFERENT; TA 9× QC0 DIFFERENT |
| **Total** | **75** | **75** | **6** | **23** | **12** | **41 variable-specific selected-F threshold triggers** |

**Important:** selected-F physical `F FLAGS` count is limited to the exact Stage05F event context (the ERA5 anomaly half-hours and ±30-minute neighbors). It may omit weakly contaminated values that do not trip the explicit numerical thresholds, and a field-specific count is not equal to unique affected half-hours. Raw QC digits are reproduced from original source and require confirmation of product semantics. It is wrong to equate all QC0 with scientifically valid in general, though **those particular selected F values differ numerically from the defective ERA source and do not trip the present physical screens**.

## Scientific interpretation

- **5/8 original-JPF-ERA-anomaly stations have nonphysical source-selected forcing values on this test:** `JP-Fjy` (PA), `JP-Khw` (TA, PA, LW), `JP-Tef` (LW), `JP-Tmd` (TA, PA, LW), `JP-Yms` (PA, LW).
- **3/8 are shielded at these screened events:** `JP-Fhk`, `JP-Spp`, `JP-Tak` have no selected `*_F` physical flag and all stage-flagged ERA variables tested differ from selected `*_F` with QC0 source labels. No automatic need for substitution in the screened event windows; further climate QC remains mandatory.
- **JP-Api** is the ninth JPF site with zero detected `ERA5_HH` physical flags under Stage05D's current screens, not a universal certification.
- **PA_F** contributes **23/41** flags and is the biggest affected variable. All 23 selected `PA_F` flags listed by the operator coincide with a source `PA_ERA` flag and `PA_F=PA_ERA` under QC2 in the event-impact comparisons. This is powerful evidence of selected-forcing contamination by the same-release erroneous ERA data, but does not validate its exact upstream origin.
- **TA_F** contributes 6 and **LW_IN_F** 12; their affected selected `*_F` values also numerically equal flagged `*_ERA` in the operator's affected-site summaries.
- **Do not automatically use MDS replacement.** Prior Khw August 2005 MDS `TA_F_MDS≈1°C` disagreed with nearby physically plausible ERA around 23°C; full original source and independent ERA provenance required.
- **Do not blanket-replace all dates**: the same date has protected selected `TA_F` / `LW_IN_F` with raw QC0 alongside corrupted reference `*_ERA`, and many flagged ERA half-hours exist before a tower's earliest FLUXMET record or after its final year.
- **No source ZIP overwrites, forcing edits, automatic scientifically approved overlays, or model submissions have taken place.** JP-Tom/JP-Tgf humidities are a separate pending science audit.

## Next stage

[Stage05G aggregate selected-forcing source impact](../scripts/stage05/05g_aggregate_selected_forcing_source_impact_NO_ZIP_NO_SLURM.py) reads exactly the eight already generated `$HOME/japanflux_stage05f/<site>_impact.json`, validates site/stage/read-only/status and ERA event coverage counts, and creates a **derived read-only TSV decision ledger** `stage05g_source_selected_event_ledger.tsv` plus a `stage05g_source_selected_summary.json`. It makes no new ZIP reads, no Slurm calls, no climate repairs, no AD400. Its source script passed Python syntax and an eight-station synthetic end-to-end test; **it has not been executed against the operator's real eight JSONs yet**.

For selected nonphysical F values it records native start, variable, `*_F`, `*_ERA`, `*_F_MDS` (when present), `*_F_QC` raw, underlying source ERA threshold flags, equality of F with affected ERA, and a candidate classification. It also distinguishes selected F values that numerically differ from flagged ERA at the same timestamp. **Classifications are audit-screen categories, not permission to repair.** Stage05G can determine the unique station×timestamp count after it runs on the full JSONs.

Next scientifically justified independent checks: compare external ERA5/ERA5-Land values on the exact corrupted native timestamps, confirm native timestamp timezone and units and flux product QC definition, and perform original measurement/ERA/MDS event context review before approving a SHA-controlled derived forcing overlay. No model runs until science gates pass.
