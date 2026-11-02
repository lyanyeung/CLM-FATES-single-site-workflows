# Stage05AV — ACTUAL 45/45 original JapanFlux QC2 source fields independently contextualized; all source fields HOLD (2026-11-02)

## Exact operator-executed outcome

The operator executed corrected [Stage05AV](../scripts/stage05/05av_remaining_4_CDS_days_8_Tef_Tmd_QC2_hourly_CONTEXT_ONLY.py) with Git blob SHA `0fffdab5a3848dd73235fb4c38e809c9bf0ab206`. Syntax and self-test PASS. Original Stage05AR/AQ/AT/AU science and BIF/source SHA preflight PASS (`37_OF_45_CONTEXT_REVIEWED`). Prior four target CDS site-days were initially absent. The operator explicitly submitted four separate `reanalysis-era5-land-timeseries` requests; all were completed, original ZIP payloads passed CRC/schema/24UTC-hour/variables/nearest grid verification, and final READONLY `--assess` PASS.

### Four REAL original external source ZIPs (not GitHub files)

| Station | Hypothetical candidate UTC day | Independent hourly CDS variable | Original ZIP bytes | SHA256 | Returned nearest ERA5-Land grid |
|---|---|---|---:|---|---|
| JP-Tef | 2022-04-08 | `strd` | 476 | `eaa4a4e522dfa18e07e8e52a54fccb2a48bec4fd8b7e9b017adfd9c04e492bd3` | 45.10000000000121 N,142.09999999999621 E |
| JP-Tmd | 2011-12-16 | `sp` | 488 | `a719ed536b1860fa46c1217ed09b8509232312ef949589951d6e2cf0b4754763` | 42.700000000001175 N,141.49999999999625 E |
| JP-Tmd | 2011-12-17 | `sp` | 488 | `a0e17f4da7f855b5f98c8ea109dca0994889caf074ed48e0b43a91dd9a892a18` | 42.700000000001175 N,141.49999999999625 E |
| JP-Tmd | 2022-04-08 | `sp` | 493 | `315a75242e2db2692c3f80d076702a3d88b87e061c21ceae1b04397d924259c2` | 42.700000000001175 N,141.49999999999625 E |

The native ZIPs remain on IRIDIS6 in `/home/ly3n24/japanflux_stage05as/downloads/`, not attached to GitHub. Stage05AV real request logs reported accepted→successful for all four independent site days.

### Last eight REAL original variable-field comparisons

Values below are **original JPF source selected F=embedded ERA QC2** versus independently sourced ERA5-Land *nearby model grid hourly context envelope*, NOT a scientifically approved site 30-minute replacement.

| Original native JPF timestamp | Variable | Original F value | Hypothetical UTC+9-to-UTC start | Independent source hourly range | Outside |
|---|---|---:|---|---|---|
| JP-Tef 2022-04-09 02:00 | LW_IN | 26.164 W/m² | 2022-04-08 17:00 | 282.653–302.753 W/m² | YES |
| JP-Tef 2022-04-09 02:30 | LW_IN | 26.164 W/m² | 2022-04-08 17:30 | 282.653–302.753 W/m² | YES |
| JP-Tmd 2011-12-17 06:30 | PA | 49.448 kPa | 2011-12-16 21:30 | 99.569–99.852 kPa | YES |
| JP-Tmd 2011-12-17 07:00 | PA | 0 kPa | 2011-12-16 22:00 | 99.569–99.852 kPa | YES |
| JP-Tmd 2011-12-17 07:30 | PA | 49.514 kPa | 2011-12-16 22:30 | 99.569–99.852 kPa | YES |
| JP-Tmd 2022-04-09 02:30 | PA | 49.616 kPa | 2022-04-08 17:30 | 99.846–100.042 kPa | YES |
| JP-Tmd 2022-04-09 03:00 | PA | 0 kPa | 2022-04-08 18:00 | 99.846–100.042 kPa | YES |
| JP-Tmd 2022-04-09 03:30 | PA | 49.579 kPa | 2022-04-08 18:30 | 99.846–100.042 kPa | YES |

Stage05AV actual printed summary:
```text
STAGE05AV SELF-TEST PASS | remaining four candidate CDS days, 8 original Tef/Tmd QC2 fields, two-day Tmd Dec2011; no network/forcing
STAGE05AV SOURCE_PROVENANCE_PREFLIGHT_PASS 37_OF_45_CONTEXT_REVIEWED; REMAINING_8_ORIGINAL_QC2_CELLS
STAGE05AV FOUR_CANDIDATE_DAY_SOURCE_ZIPS_VERIFIED 4 /4
STAGE05AV ALL_REMAINING_EIGHT_ORIGINAL_QC2_INDEPENDENT_CONTEXT_SCIENCE_REVIEW_PASS | NO REPAIR
COVERAGE_INDEPENDENT_HOURLY_CONTEXT 45 /45; TOTAL_SCIENCE_HOLD 45 /45
USER_JST_UTC_PLUS9_NOT_SOURCE_PROVEN; NO SOURCE_ZIP/FORCING/MODEL/SLURM/30MIN_REPLACEMENTS
```

Exact original operator-generated files:
```text
/home/ly3n24/japanflux_stage05av/run_20261102T232904Z/stage05av_remaining_4_CDS_days_26_model_hour_variable_context.tsv
/home/ly3n24/japanflux_stage05av/run_20261102T232904Z/stage05av_remaining_8_original_Tef_Tmd_QC2_vs_ERA5L_CONTEXT_ONLY.tsv
/home/ly3n24/japanflux_stage05av/run_20261102T232904Z/stage05av_45_original_source_QC2_independent_hourly_context_completed_ALL_HOLD.json
```

## Exact scientific status

- **45/45** original selected-F=downscaled-ERA QC2 variable fields have now been compared to independent ERA5-Land hourly contextual evidence: original Fjy6/Khw11/Yms10 source-verified UTC fields = 27, plus JP-Tef original 2011 (2) + 2022 (2), JP-Tmd original 2005 (8) + 2011 (3) + 2022 (3) = 18.
- **22** were previously classified STRONG_CONTEXT (source-verified UTC), and **23** are CONTEXT_ONLY (five Yms new evidence + all 18 Tef/Tmd source fields). Do **not** reclassify 23 as strong automatically.
- The final eight are all **outside** the conservatively defined hourly reference envelope; this does not establish exact halfhour timing/flux replacement values, grid-cell representativeness, or land-model forcing corrections. The original Tef/Tmd **75-line README SHA `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5` explicitly says local solar time**, while the operator chose JST UTC+9 as a **diagnostic time mapping hypothesis**, not producer-verified source time.
- **All 45 original source variable fields still SCIENCE HOLD and 0 scientifically approved pointwise replacement values.** No source ZIP, derived production forcing, model/AD400, Slurm, PFT or other original data have been altered.
- Source metadata and the original 45 source-variable counts are *site×native-half-hour-variable* records (35 distinct site×native-half-hour timestamps), not a count of 45 independent physical episodes.

## Next: Stage05AW — science repair FEASIBILITY / neighbor source check ONLY

The next useful action is a **read-only adjacent-halfhour native source diagnostic**, prioritizing each source QC2 physical episode and exact original variables (`TA`, `PA`, `LW_IN`). Need ascertain original selected F/QC0/QC1 neighbors, same-variable raw sensor `*_MDS` availability, time-series continuity, hour-end conventions, and cross-variable thermodynamic consistency; only afterward build possible short-gap interpolation or source-constrained ERA5-Land candidates *as explicit hypothetical shadow proposals*, without modifying original source/forcing/model. Independent hourly gridded values are **not** direct 30-minute tower reconstructions. Keep the original time convention caveat explicit for Tef/Tmd, and retain all 45 holds.
