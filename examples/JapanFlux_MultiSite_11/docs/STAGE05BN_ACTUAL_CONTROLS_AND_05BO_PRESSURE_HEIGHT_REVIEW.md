# Stage05BN actual control diagnostics and Stage05BO pressure-height review

All 45 selected shadows remain HOLD, with zero replacements approved. This report combines operator-provided IRIDIS output with local calculations; the reviewer did not directly read IRIDIS files. The user-selected method remains grid plus the original-release QC2 background median.

## Actual Stage05BN run

The operator supplied output beginning with the Stage05BN invocation; the earlier download/hash/self-test lines were not included. The script reported completion, verified the exact Stage05BM pairs and Stage05BF selected ledger, and did not submit any CDS request. Its diagnostic table SHA256 was `98d58af445e267c6f1f9e28f52af80a24ce54775be30cc5076a59837d6d73354`; output directory `/home/ly3n24/japanflux_stage05bn/run_20261104T030255Z_297673`. The supplied terminal paste SHA256 is `a25cf9b5731262adde6bd9a15d7eb2819cfcd4bb0371ba169baf435a5c4632fc`.

| Control, UTC day; UTC+9 diagnostic | n | Grid MAE | Selected MAE | Selected mean bias |
|---|---:|---:|---:|---:|
| TA Aug 14, all | 44 | 0.8784 °C | 0.8111 °C | −0.7543 °C |
| TA Aug 19, all | 44 | 0.8374 °C | 0.9153 °C | +0.9153 °C |
| LW Sep 10, all | 35 | 23.1738 W/m² | 16.8591 W/m² | −16.8364 W/m² |
| TA Aug 14, native 02:00–before 04:00 | 4 | 0.2775 °C | 0.3164 °C | +0.3082 °C |
| TA Aug 19, native 02:00–before 04:00 | 4 | 0.3482 °C | 0.4262 °C | +0.4262 °C |
| LW Sep 10, native 02:00–before 04:00 | 2 | 7.6908 W/m² | 1.7500 W/m² | −1.3534 W/m² |

The prior inferred LW grid MAE of 23.1738 is directly confirmed by the pair table. The fixed event background correction helps LW on that particular control day, but the all-day mean remains negative. TA's +0.07794 °C event offset helps Aug 14 overall and worsens Aug 19 overall. The early-time rows are post-hoc subsets of only 2–4 autocorrelated half-hours; their low error must not be interpreted as a robust uncertainty bound or event-time validation. These results do not test pressure or other sites.

## 17-group boundary screen and review

The table is reproduced from the hash-pinned locally calculated Stage05BE sensitivity output (SHA256 `df630467aa393331c5c4116af687c988976d9b747b5ff1aed87ef3eea66fcb7e`), based on earlier operator-derived windows, not a new independent IRIDIS read. It compares the largest selected/source adjacent half-hour change with the local same-release QC2 descriptive p95. The p95 is **not** a physical threshold or confidence interval; being below it is not approval.

| Site | Variable / event start | Selected max jump | Local QC2 p95 | Review |
|---|---|---:|---:|---|
| Fjy | PA 2005-08-12 02:30 | 0.0600 kPa | 0.0330 | Above local p95; height/grid context |
| Fjy | PA 2011-12-17 06:30 | 0.0835 kPa | 0.0510 | Above local p95; height/grid context |
| Khw | PA 2005-08-12 02:30 | 0.0525 kPa | 0.0260 | Above local p95; no local QC0 control |
| Khw | PA 2011-12-17 06:30 | 0.0788 kPa | 0.0340 | Above local p95; no local QC0 control |
| Yms | PA 2005-08-12 02:30 | 0.0226 kPa | 0.0170 | Above local p95; keep all three flags together |
| Yms | PA 2011-12-17 06:30 | 0.0759 kPa | 0.0250 | Above local p95; keep all three flags together |
| Tmd | PA 2005-08-12 02:30 | 0.0224 kPa | 0.0200 | Above local p95; JMA/site-height mismatch |
| Tmd | PA 2011-12-17 06:30 | 0.0763 kPa | 0.0380 | Above local p95; JMA/site-height mismatch |
| Tmd | PA 2022-04-09 02:30 | 0.1341 kPa | 0.0550 | Above local p95; largest Tmd PA boundary jump |
| Khw | TA 2005-08-12 02:30 | 0.8634 °C | 1.0370 | MDS QC3 conflicts with surrounding source; no QC0 control |
| Tmd | TA 2005-08-12 02:30 | 0.3142 °C | 0.5040 | Other-time controls available; clock/background still uncertain |
| Khw | LW 2005-08-12 02:00 | 5.9232 W/m² | 10.0310 | Hourly-to-half-hour assumption; no QC0 control |
| Yms | LW 2005-08-12 02:00 | 9.8544 W/m² | 9.7650 | Above local p95; no QC0 control |
| Yms | LW 2011-12-17 06:00 | 15.6433 W/m² | 14.4940 | Above local p95; bridge and selected differ |
| Tef | LW 2011-12-17 06:00 | 1.0978 W/m² | 10.5920 | Clock and hourly support unresolved |
| Tef | LW 2022-04-09 02:00 | 14.6169 W/m² | 14.6240 | Clock-sensitive; p95 near equality is not acceptance |
| Tmd | LW 2005-08-12 02:00 | 6.5911 W/m² | 11.6140 | Other-time LW bias; clock and support unresolved |

Every row remains HOLD. The pre-existing [45-field review packet](STAGE05BD_MANUAL_REVIEW_PACKET_17_GROUPS.md) lists the actual original and candidate values; the selected method is its grid-plus-QC2-median column. The bridge is retained only as an alternate sensitivity, not substituted automatically.

## Additional JMA historical barometer-height evidence

The official [JMA site metadata page](https://www.data.jma.go.jp/stats/data/mdrr/man/kansoku_gaiyou.html) links a history file; its [format specification](https://www.data.jma.go.jp/stats/data/mdrr/man/smasterindex_format.pdf) documents an instrument-height field. The official ZIP could not be retrieved from this workstation. A [third-party mirror pinned to commit e151e5b63c7d79ed77d15738fbc6b6dfdc4b5bfe](https://github.com/jsasaki-utokyo/GWO-AMD/blob/e151e5b63c7d79ed77d15738fbc6b6dfdc4b5bfe/smaster.index), Git blob `314328629e5dc6b244bd0d1dd60b5929f254f558`, contains records for JMA Tomakomai 424 and Kawaguchiko 640. We read the mirror, not the official ZIP; official file identity and provenance remain unverified. The records show Tomakomai 7.9 m in periods covering all three event dates, and Kawaguchiko 860.5 m in 2005 and 861.3 m in 2011. The values are interpreted here as barometer altitude, rather than added to ground elevation; the JMA format's height datum should be confirmed directly before treating this as definitive.

Applying the same simple isothermal dry-air approximation used in Stage05BB, with the previously read JMA hourly station pressure/temperature and tower **ground** BIF elevation (not known tower sensor elevation), changes the illustrative site-height pressures as follows. JMA is a separate station, and shared ERA5 data inputs are possible; these are not tower QC0 measurements. Native event time is matched to JMA JST only as a working hypothesis.

| Event | Previously assumed JMA ground m | Mirrored barometer m | Previous illustrative kPa | New illustrative kPa | User-selected centre minus new context kPa |
|---|---:|---:|---:|---:|---:|
| Tmd 2005 | 6.0 | 7.9 | 99.8298 | 99.8519 | −0.8676 |
| Tmd 2011 | 6.0 | 7.9 | 99.8440 | 99.8684 | −0.8706 |
| Tmd 2022 | 6.0 | 7.9 | 100.0630 | 100.0864 | −0.9870 |
| Fjy 2005 | 860.0 | 860.5 | 89.7520 | 89.7572 | +0.1721 |
| Fjy 2011 | 860.0 | 861.3 | 89.5816 | 89.5964 | +0.4287 |

These comparisons use the **user-selected grid-plus-median centres**, not the bridge centres shown in Stage05BB. Source temperatures, hydrostatic simplification, spatial separation (~12.7 km Tmd, ~5.1 km Fjy), measurement-height and clock assumptions remain material. Changing the assumed JMA instrument height moves the illustrative comparison by only about 0.005–0.024 kPa in these examples; it does not explain the full discrepancy. It also does not prove either source wrong or justify modifying a whole QC2 run. The underlying hourly JMA observations and links are documented in [Stage05BB](STAGE05BB_JMA_TMD_INDEPENDENT_PRESSURE_CONTEXT.md).

`05bo_jma_barometer_height_context_READONLY.py` reproduces the five rows locally from the documented values. Its self-test passed. Script SHA256 `be25a417106efc765676d01761d34619e6636bbf36e21a976821c82a5b5ff2b5`. It does not read originals, query CDS, write forcing, or approve values.
