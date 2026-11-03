# Stage05BD: 17-group manual scientific review packet

**Decision boundary: all 45 source fields remain SCIENCE HOLD; zero replacement values are approved.** The numbers are review-only shadows. They are not edits to forcing, original ZIPs or model inputs.

## How to read

Rows list native interval **start** labels. Within each row, original, bridge and alternative numbers correspond to consecutive 30-minute starts, in order; two or three numbers mean two or three flagged intervals. PA is in kPa, TA in °C, LW in W m⁻². Values are rounded to four decimals for review; use the full-precision ledgers for any future authorized operation.

Left/right endpoints are the immediate outside-group source F values; both are QC2 and equal the same-release ERA field, not QC0 tower measurements. Bridge interpolates across the full flagged group. The alternative is existing ERA5-Land matched hourly context plus the median source-QC2-minus-grid residual from the event-excluded local background; it inherits QC2 background bias and is not an independent tower observation. Tef/Tmd reference matching uses unverified UTC+9; their README says local solar time. Clock mapping and hour-versus-half-hour support remain unresolved.

The 17-group masked comparison favored bridge against same-release QC2 in every group, but overlapping blocks and a same-source target make this a local-shape sensitivity result, not a validation against physical truth. JMA sites are separately operated but may not be statistically independent of ERA reanalysis and are not tower observations.

## Actual 45 fields in 17 groups

| Site | Variable | Native date and first–last start | Original F | Left / right QC2 | QC2 bridge (held) | Grid + QC2 median (held) |
|---|---|---|---|---|---|---|
| JP-Fjy | PA | 2005-08-12 02:30–03:30 | 45.1600, 0.3340, 45.1610 | 89.9850 / 89.9890 | 89.9860, 89.9870, 89.9880 | 89.9250, 89.9292, 89.9518 |
| JP-Fjy | PA | 2011-12-17 06:30–07:30 | 45.1230, 0.3340, 45.2110 | 89.9110 / 90.0870 | 89.9550, 89.9990, 90.0430 | 89.9945, 90.0252, 90.0550 |
| JP-Khw | LW_IN | 2005-08-12 02:00–02:30 | 39.1710, 39.1710 | 400.9390 / 402.6130 | 401.4970, 402.0550 | 406.8622, 406.8622 |
| JP-Khw | PA | 2005-08-12 02:30–03:30 | 48.9120, 0.0000, 48.9220 | 97.8230 / 97.8440 | 97.8282, 97.8335, 97.8387 | 97.7705, 97.7902, 97.8273 |
| JP-Khw | PA | 2011-12-17 06:30–07:30 | 49.5060, 0.0000, 49.5710 | 99.0130 / 99.1430 | 99.0455, 99.0780, 99.1105 | 99.0918, 99.1219, 99.1383 |
| JP-Khw | TA | 2005-08-12 02:30–03:30 | -122.1440, -268.2760, -122.6650 | 23.9880 / 22.9460 | 23.7275, 23.4670, 23.2065 | 23.9015, 23.8365, 23.8094 |
| JP-Tef | LW_IN | 2011-12-17 06:00–06:30 | 26.1640, 26.1640 | 205.2770 / 204.5030 | 205.0190, 204.7610 | 204.1792, 204.1792 |
| JP-Tef | LW_IN | 2022-04-09 02:00–02:30 | 26.1640, 26.1640 | 272.0290 / 255.3680 | 266.4753, 260.9217 | 257.4121, 257.4121 |
| JP-Tmd | LW_IN | 2005-08-12 02:00–02:30 | 28.5190, 28.5190 | 395.3130 / 402.3080 | 397.6447, 399.9763 | 401.9041, 401.9041 |
| JP-Tmd | PA | 2005-08-12 02:30–03:30 | 49.5020, 0.0000, 49.5060 | 99.0040 / 99.0130 | 99.0063, 99.0085, 99.0108 | 98.9816, 98.9843, 98.9914 |
| JP-Tmd | PA | 2011-12-17 06:30–07:30 | 49.4480, 0.0000, 49.5140 | 98.8960 / 99.0290 | 98.9292, 98.9625, 98.9958 | 98.9723, 98.9978, 99.0281 |
| JP-Tmd | PA | 2022-04-09 02:30–03:30 | 49.6160, 0.0000, 49.5790 | 99.2320 / 99.1580 | 99.2135, 99.1950, 99.1765 | 99.0979, 99.0993, 99.1144 |
| JP-Tmd | TA | 2005-08-12 02:30–03:30 | -132.3990, -284.2220, -132.6880 | 19.4250 / 18.8470 | 19.2805, 19.1360, 18.9915 | 19.2801, 19.2205, 19.1612 |
| JP-Yms | LW_IN | 2005-08-12 02:00–02:30 | 44.7900, 44.7900 | 416.6630 / 424.1310 | 419.1523, 421.6417 | 426.5174, 426.5174 |
| JP-Yms | LW_IN | 2011-12-17 06:00–06:30 | 44.7900, 44.7900 | 248.4470 / 261.6860 | 252.8600, 257.2730 | 264.0903, 264.0903 |
| JP-Yms | PA | 2005-08-12 02:30–03:30 | 67.7940, 37.3490, 67.8010 | 98.2400 / 98.2530 | 98.2432, 98.2465, 98.2498 | 98.2409, 98.2509, 98.2735 |
| JP-Yms | PA | 2011-12-17 06:30–07:30 | 68.1600, 37.3490, 68.2020 | 98.9710 / 99.0550 | 98.9920, 99.0130, 99.0340 | 99.0469, 99.0788, 99.1047 |

## Review priorities and current recommendation

- **Tmd PA, 3 groups / 9 fields:** same-source QC2 background may be biased. Under a rough 111 m station-to-site height assumption, three centre bridge shadows are 0.821–0.881 kPa below JMA Tomakomai site-height estimates. Station distance, sensor heights, spatial gradients and source clock are unresolved. Tmd 2022 includes one residual just outside its observed local QC2 background range; that descriptive range is not an uncertainty bound. Recommendation: HOLD; do not apply a uniform correction.
- **Fjy PA, 2 groups / 6 fields:** the 2005 first two bridge residuals lie just outside the observed QC2 background range; grid-site elevation differences and possible background bias need review. Illustrative JMA Kawaguchiko site-height comparison places the two centre shadows 0.235 and 0.417 kPa above estimates, with limited height/temperature scenarios and no demonstrated spatial-error bound. Recommendation: HOLD.
- **Khw PA, 2 groups / 6 fields:** candidate bridge and median-adjusted grid are relatively close in these windows, but this is not independent QC0 validation. Recommendation: bridge is a candidate for further validation; HOLD.
- **Yms PA, 2 groups / 6 fields:** both apparently less-extreme flanks are already flagged and must stay in each three-field group; do not use them as anchors. Background source-minus-grid medians are about −0.649 and −0.995 kPa, which may reflect representativeness or source effects. Recommendation: full-group bridge candidate only; HOLD.
- **Khw TA, 1 group / 3 fields:** MDS values 1.133/1.322/1.464 °C have MDS QC3 and disagree with adjacent QC2 selected values around 23 °C. MDS QC codes must not be equated to selected-F QC codes. Recommendation: do not substitute MDS automatically; HOLD.
- **Tmd TA, 1 group / 3 fields:** MDS values 20.337/20.343/20.342 °C have MDS QC2; they are gapfilled and differ from bridge values around 19 °C. The source clock conflict remains. Recommendation: review MDS provenance/quality and independent observations; HOLD.
- **LW, 6 groups / 12 fields:** evaluate hour-ending accumulated-radiation semantics, cloud variability and native half-hour alignment. Yms 2011 first field differs by 11.230 W m⁻² between alternatives; Tef 2022 first field differs by 9.063 W m⁻². Tef/Tmd have the additional unresolved clock conflict. Neither method difference is an uncertainty interval. Recommendation: HOLD.

The reviewer can endorse the above research priorities or provide relevant original-publisher clock, instrument and independent-observation evidence. An endorsement of priorities is not approval of any numerical value. Before approval, reconcile original source integrity/gate attestations, clock and interval semantics, selected field provenance, independent corroboration, cross-variable physics and production-file application plan, then record a separate explicit per-value decision.

## Provenance and reproduction

Source: local actual-output-derived Stage05BA `shadow_45_NOT_APPROVED.tsv` SHA256 `35f9f064983bec73c16fac44a8259093ffa7ec36f23caa4b28c93e44113677f2`; Stage05BC `alternative_shadow_45_HOLD.tsv` SHA256 `67547a7cce5aaf10b776e44c2b4e683bf742f3bb0ea3306034a9dbc43b2d021c`. The output is derived from operator-supplied material; this stage does not independently read the IRIDIS6 source ZIPs. The Stage05AZ output excerpt omitted its execution log and summary JSON, so individual source-gate results were not directly seen. See [Stage05BA](STAGE05BA_OPERATOR_AUDIT_AND_SHADOW_DECISION.md), [Stage05BB](STAGE05BB_JMA_TMD_INDEPENDENT_PRESSURE_CONTEXT.md), and [Stage05BC](STAGE05BC_MASKED_METHOD_COMPARISON_AND_05BB_OPERATOR_RESULT.md).
