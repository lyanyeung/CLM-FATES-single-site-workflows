# Stage05BK: actual ICOS archive identity and QC2 background balance

## Operator's actual Stage05BI terminal result

The operator supplied the successful Stage05BI execution output, with report directory `/home/ly3n24/japanflux_stage05bi/run_20261103T180701Z_774126`. Both original outer ZIPs were reported SHA-verified before and after scanning. The two inner ZIPs match the published ICOS full-archive SHA256s **byte for byte**:

| Site | Inner bytes | SHA256 of inner ZIP and published full archive |
|---|---:|---|
| JP-Tef | 219,044,184 | `537ea32af19f1880874893b4d529388c465331ccfc42dd5987341568a5427527` |
| JP-Tmd | 170,739,845 | `d28f9eec6e3226029852ba638cb7bbc3496d74880da8f3f29fec95b0ea3cb48f` |

These exact publisher archive hashes were read from the ICOS [Tef archive](https://meta.icos-cp.eu/objects/U36jKvGfGICHSJO01Sk4jEZT) and [Tmd archive](https://meta.icos-cp.eu/objects/0o-e7G4yJgKYUrpjjLe7w0lt) metadata pages; no publisher ZIP was downloaded. Both original READMEs had SHA256 `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5` and line 64 states local solar time without DST. ICOS's corresponding separate Tef and Tmd half-hour subset metadata states local non-DST time; see [Tef subset](https://meta.icos-cp.eu/objects/5EPoidiNgWdizvMjVuk1G1vC) and [Tmd subset](https://meta.icos-cp.eu/objects/bnc9Cg8Jxf1opT9_Fq8boBvS). Archive identity is now established **for the user's operator-reported bytes**, but the linguistic/operational difference between the source archive README and separately packaged subset metadata is not resolved. The operator's pasted excerpt starts at `CHECK JP-Tef` and omits the earlier download SHA/self-test/test lines, so this review does not assert it saw those omitted lines. The Stage05BI tests passed locally before dispatch.

## What the publicly inspected ONEFlux code does and does not establish

The [public ONEFlux README](https://github.com/fluxnet/ONEFlux/blob/ef24050b783f4c7538f8acf15b488b363cd26796/README.md#L21-L23) describes a time zone adopted for timestamps. The inspected public repository commit `ef24050b783f4c7538f8acf15b488b363cd26796` has a [downscaling launcher](https://github.com/fluxnet/ONEFlux/blob/ef24050b783f4c7538f8acf15b488b363cd26796/oneflux/downscaling/rundownscaling.py#L73-L100) that carries site time-zone metadata into configuration; its [gap-filling code](https://github.com/fluxnet/ONEFlux/blob/ef24050b783f4c7538f8acf15b488b363cd26796/oneflux/downscaling/gapfilling.py#L40-L77) uses an explicit time shift or a longitude-based time-zone fallback. This makes a fixed time-zone interpretation technically consistent with the pipeline, but **does not prove that this code revision and configuration produced these exact site releases** or clarify what their README author meant by “solar”. The publisher subset pages and BIF UTC_OFFSET=9 support UTC+9 for diagnostics; retain the documented conflict until the responsible release documentation or an adequate independent mapping resolves it.

## Bias-median sensitivity to unequal pre/post coverage

The user chose `existing grid + overall QC2-minus-grid median` for all 45 held shadows. The actual saved UTC+9 background has 897 paired QC2 values in 17 groups. `05bk_background_side_balance_diagnostic_READONLY.py` rechecks the operator-pasted pair arithmetic and exact Stage05BA group medians, splits each group into before and after samples, and compares the chosen overall median with the arithmetic mean of the two side medians. The alternate is a **descriptive sensitivity only**: it is neither an independent measurement, a statistically established correction, nor a change to the chosen method. The sides have autocorrelation, different temporal distributions and—in several cases—very few post-event samples.

| Group | Pre / post n | Pre / post median source−grid | Overall chosen median | Equal-side-median sensitivity | Difference from chosen |
|---|---:|---:|---:|---:|---:|
| Tmd PA 2022 | 31 / 4 | −0.777724 / −0.748132 | −0.775634 | −0.762928 | +0.012706 kPa |
| Khw TA 2005 | 31 / 4 | +0.901562 / −1.047760 | +0.834065 | −0.073099 | −0.907164 °C |
| Tmd TA 2005 | 31 / 4 | +0.112445 / −0.872141 | +0.077940 | −0.379848 | −0.457788 °C |
| Tef LW 2022 | 32 / 6 | −24.720139 / −39.077889 | −25.241278 | −31.899014 | −6.657736 W m⁻² |

For Tmd PA 2022, even replacing the chosen median hypothetically by this side-balanced sensitivity would move the first selected value only +0.012706 kPa, leaving an approximately −0.121444 kPa jump relative to the same unchanged left QC2 endpoint. This is still above the 0.055 kPa **descriptive** local jump p95, which is not an automatic rejection threshold. These patterns show that method sensitivity varies by variable and support further boundary/clock review; they do not establish which median is right, a confidence interval, or a source bias. The user's overall-median candidate remains unchanged.

## Reproducibility and status

The 17-row local sensitivity artifact `background_side_sensitivity_NOT_APPROVED.tsv` has SHA256 `1629a2c2d16dbcadee8903435783d4d2972aac57b6723b174ffcef598d123a07`. The script hashes the local operator-pasted AZ text and BA group ledger before/after, requires exact 17-group and 897-pair coverage, verifies paired differences and selected medians, and emits HOLD-only diagnostics. Its self-test and two unit tests pass locally, including altered-input fail-closed behavior. It did not access IRIDIS6, original ZIPs, CDS or production forcing. Stage05BI was actually run by the operator; Stage05BK was run locally only. No PFT, soil, case, Slurm or AD400 changes were made. **All 45 original fields remain SCIENCE HOLD; zero replacement values approved.**
