# Batch04 Stage15 — operator VERIFIED two-point US-SP1 temperature sensitivity candidate

**Status:** Stage15 syntax, standalone self-test, read-only `--assess`, and isolated `--trial` succeeded on IRIDIS6 on 2026-10-25. No DATM, CIME, original sources or prior Stage07–14 candidates modified. This is an **alternative temperature sensitivity branch only**.

## Original, Stage14 and Stage15 values

| Native US-SP1 timestamp | Original TA °C (original QC0) | Stage14 primary TA °C (QC0 retained) | Stage14 VPD hPa | Stage15 trial TA °C (trial QC1) | ERA5-Land T2m °C | Stage15 trial VPD hPa |
|---|---:|---:|---:|---:|---:|---:|
| 2000-10-09 18:00 | −6.900 | −6.900 | 2.27462321445 | 13.1816666667 | 14.3708129883 | ≈9.4362 |
| 2000-10-09 18:30 | −7.100 | −7.100 | 2.15689710498 | 15.3633333333 | 13.7762237549 | ≈10.4653 |

Stage15 keeps Stage14's independently gridded ERA5-Land RH and recomputes water-referenced VPD at **trial temperature**, so Stage14's VPD and Stage15's VPD differ substantially. Never combine a Stage15 trial TA value with Stage14's VPD by mistake.

**Sensitivity evidence**: the flanking original native US-SP1 temperature record 17:30=11.0°C QC0, 19:00=17.545°C QC1 (with 16:30=14.0°C QC0, 17:00=12.6°C QC0 and later three QC1 17.54°C values), and verified ERA5-Land native-clock-correct temperature 14.371/13.776°C suggested two isolated suspicious negative measurements. The script interpolated both temperatures across the 17:30 to 19:00 bracket; it did not use ERA5-Land T as the direct source replacement. This is a scientifically reasonable **test scenario**, but neither independent proof nor official tower QC correction.

## Exact output

```text
STAGE15 SELF-TEST PASS: strict 2 HH isolate, original QC0 provenance to trial QC1
STAGE15 SP1 TEMP SENSITIVITY 200010091800 old_TA -6.9 trial_TA 13.182 ERA_T 14.371 trial_VPD 9.4362 TA_QC:0->1
STAGE15 SP1 TEMP SENSITIVITY 200010091830 old_TA -7.1 trial_TA 15.363 ERA_T 13.776 trial_VPD 10.4653 TA_QC:0->1
STAGE15 ASSESS ONLY: no writes, science holds remain
STAGE15 ALTERNATIVE TWO-POINT FULL SOURCE /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage15_sp1_two_point_temperature_sensitivity/candidate_20261025T080658Z_cca73e0e/US-SP1_Stage15_alternative_two_TA_times_FLUXMET_HH.csv
STAGE15 RESULT: 2 proposed TA/VPD changes; 8 QC0 temperature science holds remain; NO DATM/CIME
```

The output candidate folder should additionally hold:
- `STAGE15_ALTERNATIVE_LATEST_TEN_MANIFEST.tsv` — ten-site sensitivity-branch selection; the nine other sites inherit their existing Stage14 input paths;
- `STAGE15_TWO_POINT_SCIENCE_PROVENANCE.tsv` — original/QC0 and proposed/QC1 values, source bracket and independent ERA comparison;
- `stage15_receipt.json` — exact source Stage14 SHA, full trial file SHA and proof that model acceptance is disabled;
- `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` — explicit science and operational guardrail.

**Note:** The operator output did not print the complete Stage15 CSV SHA256. Use the immutable `stage15_receipt.json` generated on IRIDIS6 to extract it; do not invent or copy a Stage14 source SHA into the Stage15 trial record.

## Remaining scientific questions

- **All 8 temperature science HOLDs still open**, including the two for which this alternative demonstrates a plausible replacement; neither the Stage14 primary candidate nor Stage15 alternative is model-approved.
- **US-Syv 606 original science HOLDs and 10 Stage07 skipped ERA high-jump endpoints remain deferred**.
- Next sensible action: review the six *other* temperature conflicts separately (four more US-SP1 events, one US-SRG, one US-Seg), and compare any proposed repair alternatives against the primary Stage14 temperature-retained branch; request site operator or independent instrument evidence where possible.
- No new CDS download is needed. No new code-driven T modification should silently override QC0 as if it were a verified measurement.

**Code:** [Stage15 two-point sensitivity script](../scripts/stage15/15_sp1_oct2000_two_point_temperature_sensitivity.py).

