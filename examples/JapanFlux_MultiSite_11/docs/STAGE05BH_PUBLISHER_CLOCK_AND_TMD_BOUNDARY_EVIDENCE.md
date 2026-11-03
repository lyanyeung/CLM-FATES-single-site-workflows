# Stage05BH: publisher time metadata and selected Tmd pressure boundaries

## Publisher evidence for the time convention

The [ICOS Carbon Portal JP-Tmd FLUXMET product page](https://meta.icos-cp.eu/objects/bnc9Cg8Jxf1opT9_Fq8boBvS) describes a ONEFlux half-hourly product named `JPF_JP-Tmd_FLUXNET_FLUXMET_HH_2005-2023_v1.3_r1.zip`, 333,072 rows, at 42.735912°N / 141.52315°E / 117 m. Its displayed `TIMESTAMP_END` type is **local non-DST time**. It displays acquisition start and stop as `2004-12-31 15:00 UTC` and `2023-12-31 15:00 UTC`; interpreting the advertised 2005–2023 local-year coverage as midnight-to-midnight is consistent with UTC+9. That interpretation is an inference about the endpoint convention, not a separate observation of every timestamp.

The earlier source audit reported JP-Tmd BIF `UTC_OFFSET=9`, which also supports UTC+9. The publisher page identifies a *separately packaged FLUXMET subset for plotting*, with SHA256 `6e773d0a0f09c5fd68a53f7f16af1ba01bd2702513ff462e588b1725f12fd7f6`; this is not the SHA of the operator's outer archive. Matching name, version, row count and coordinates provides strong related-product evidence but is **not** a byte-for-byte identity verification of the operator's nested source member. This source page concerns Tmd; do not silently transfer its specific evidence to Tef.

The [FLUXNET2015 product documentation](https://fluxnet.org/data/fluxnet2015-dataset/) states its data use local standard time without DST and specifies separate start/end timestamps. The [AmeriFlux temporal-variable conventions](https://ameriflux.lbl.gov/data/aboutdata/data-variables/) likewise describe local standard time and explicit half-hour start/end columns. These are relevant pipeline conventions, not an explicit retraction of the Tef/Tmd packaged READMEs. Previous original-package review recorded that both READMEs say **local solar time**. The conflict is therefore **not fully resolved**: UTC+9 is now better supported for the related published Tmd product, while the exact archive-member relationship and README wording still require direct reconciliation. Tef has BIF UTC_OFFSET=9 and general convention evidence, but a corresponding same-version publisher FLUXMET metadata page was not verified in this review. Do not treat a solar-versus-standard scenario spread as proof of either clock.

## Pressure change context

The [JMA Tomakomai hourly 2005](https://ds.data.jma.go.jp/obd/stats/etrn/view/hourly_s1.php?prec_no=21&block_no=47424&year=2005&month=08&day=12&view=a1), [2011](https://ds.data.jma.go.jp/obd/stats/etrn/view/hourly_s1.php?prec_no=21&block_no=47424&year=2011&month=12&day=17&view=a1) and [2022](https://ds.data.jma.go.jp/obd/stats/etrn/view/hourly_s1.php?prec_no=21&block_no=47424&year=2022&month=04&day=09&view=a1) pages provide independently operated station-pressure context. JMA station and tower are ~12.7 km apart; JMA values are hourly, native source values represent half-hours, and Tmd's exact time convention and historical sensor heights are not independently reconciled. The table is **not** a matched half-hour validation or proof of a pressure gradient.

| Event date | JMA station hourly pressures, hPa | Adjacent JMA hourly changes, kPa | Selected maximum source/selected half-hour jump, kPa | Same-release local QC2 jump p95, kPa |
|---|---|---|---:|---:|
| 2005-08-12 | 02/03/04: 1011.4, 1011.3, 1011.3 | −0.010, 0.000 | 0.02244 | 0.020 |
| 2011-12-17 | 06/07/08: 1012.5, 1012.8, 1013.4 | +0.030, +0.060 | 0.07635 | 0.038 |
| 2022-04-09 | 02/03/04: 1014.4, 1014.4, 1014.2 | 0.000, −0.020 | 0.13415 | 0.055 |

For the 2022 first flagged field, the unchanged left source-QC2 endpoint is 99.232 kPa. First selected candidate minus that left endpoint is, respectively, −0.143263, −0.134150, −0.114675, −0.117319 kPa for UTC+08:30, UTC+09, UTC+09:30 and longitude-derived mean solar diagnostics. All four absolute differences exceed the local same-source QC2 jump p95 of 0.055 kPa; this is a descriptive screen, not a statistical confidence interval or automatic rejection. It shows that these particular tested clock shifts do not eliminate the boundary contrast, assuming the same native source endpoint. The comparison to JMA context is limited by different stations, hourly sampling and unverified subhourly timing; smaller JMA hourly changes do not prove the 30-minute tower value is wrong.

The user-selected grid-plus-QC2-median method remains selected for all 45 shadow values. Do not substitute the prior bridge without a separate decision. The numerical physical/representativeness questions, including Tmd QC2 background level, remain open; **all 45 are SCIENCE HOLD, zero approved replacements**.

## Reproduction and integrity

`05bh_tmd_jma_pressure_changes_READONLY.py` reads the SHA-pinned local Stage05BE boundary table, Stage05BG 18-field clock table and Stage05BA 45-field ledger. It recomputes JMA hourly differences and the four 2022 left-boundary values; it does not request JMA, CDS, original ZIP or IRIDIS files and prints context to stdout. Its self-test and two unit tests pass locally, including hPa-to-kPa/sign and changed-input rejection. The JMA observations were previously read from the linked official pages, not downloaded or hashed. No production forcing, raw ZIP, PFT, soil, model case, Slurm or AD400 was modified.
