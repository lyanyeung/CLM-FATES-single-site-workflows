# Stage05BC: masked comparison of two held shadow methods

## Actual 05BB operator execution

The operator supplied the IRIDIS6 terminal output for commit `e090059702228d99c3b7acb6ea68f3af891836be`: both downloaded 05BB script/test SHA256 checks returned `OK`, the script's self-test passed and the two tests passed. The five output rows match the previously reported Tmd/Fjy illustrative values. This confirms execution of the hardcoded-public-observation calculator on that environment; it is not a new JMA download, original ZIP scan, clock proof, forcing validation or approval. The evidence here is the operator-supplied terminal text, not direct access to IRIDIS6.

## Input and approach

The local 05BC calculation reads the 1,677-row Stage05BA preview, SHA256 `81eaab3abff605991fe3fe1321eabea740279b8c09f629ce2aa664670953d8a7`, and the operator-pasted Stage05AZ tables, SHA256 `bd96cc5f0d80fe440c2db3540a8492d75c2641b8ee7bf95b810765f64925a26c`. These are derived/pasted inputs, not the original remote TSVs: this step does not independently recheck raw source ZIP integrity or prove that the remote export never changed. Earlier source-provenance evidence and the missing AZ execution-log/summary limitation remain as stated in the Stage05BA report.

For each of 17 previously flagged groups, at the UTC+9 diagnostic offset, start with the *existing* paired background points outside two hours of any flagged point. Require their selected values to be QC2, equal the same-release ERA field and equal the previously exported source values. For every contiguous background block of the same length as that event, with both immediate endpoints present, compare:

1. A linear bridge between the two same-release QC2 endpoints.
2. The pre-existing hourly ERA5-Land context plus the median QC2-minus-grid background residual, estimated from background records more than two hours from **every point in the masked block**, with at least ten calibration pairs. Both methods use observations on both sides; this is retrospective interpolation, not a prospective forecast.

The event candidates use the median of the available event-excluded paired background, while the pseudo-test calibration excludes the masked block and its two-hour buffer. The two methods are evaluated on exactly the same eligible masked blocks and targets. Those blocks overlap, their points are autocorrelated, and the available grid time support limits which blocks are eligible (especially 2005/2022). No inferential confidence interval, independence assumption or generalization to other weather is claimed. This is a **same-release QC2 pseudo-target**, not a tower QC0 observation. The experiment favors a method built from the same product's immediate endpoints and cannot detect shared QC2 background bias, establish true physical error or approve a candidate.

## Results

| Site / variable / event start (native) | Eligible overlapping blocks | Bridge MAE vs QC2 | Grid + held-out median MAE vs QC2 |
|---|---:|---:|---:|
| Fjy PA 2005-08-12 02:30 | 27 | 0.0079 | 0.0205 |
| Fjy PA 2011-12-17 06:30 | 75 | 0.0124 | 0.0519 |
| Khw PA 2005-08-12 02:30 | 27 | 0.0077 | 0.0265 |
| Khw PA 2011-12-17 06:30 | 75 | 0.0087 | 0.0250 |
| Yms PA 2005-08-12 02:30 | 27 | 0.0058 | 0.0599 |
| Yms PA 2011-12-17 06:30 | 75 | 0.0079 | 0.0893 |
| Tmd PA 2005-08-12 02:30 | 27 | 0.0062 | 0.0484 |
| Tmd PA 2011-12-17 06:30 | 75 | 0.0109 | 0.0283 |
| Tmd PA 2022-04-09 02:30 | 27 | 0.0109 | 0.0255 |
| Khw TA 2005-08-12 02:30 | 27 | 0.1663 | 1.3789 |
| Tmd TA 2005-08-12 02:30 | 27 | 0.1153 | 0.5137 |
| Khw LW 2005-08-12 02:00 | 32 | 1.8456 | 5.8015 |
| Yms LW 2005-08-12 02:00 | 32 | 2.4112 | 5.5714 |
| Yms LW 2011-12-17 06:00 | 78 | 3.3012 | 6.7275 |
| Tef LW 2011-12-17 06:00 | 78 | 3.0753 | 6.4208 |
| Tef LW 2022-04-09 02:00 | 32 | 3.6378 | 11.6012 |
| Tmd LW 2005-08-12 02:00 | 32 | 2.9060 | 6.4105 |

MAE is in kPa for PA, °C for TA and W m⁻² for LW; it averages point errors in overlapping blocks, not independent events. In all 17 groups the bridge has lower MAE **against this specific QC2 pseudo-target**, which provides a basis for prioritizing its continuity shadow but is not a ranking against actual tower truth. The grid-adjusted method inherits the same QC2 background level and cannot correct a common QC2 bias; its median offset is a statistical scenario, not an elevation correction. Tmd JMA comparisons from Stage05BB particularly caution against assuming that QC2 level is correct.

Across the 45 flagged fields, the absolute difference between the two unapproved candidates ranges 0.0023–0.1157 kPa for PA, 0.0004–0.6029 °C for TA and 0.582–11.230 W m⁻² for LW. The largest LW difference is JP-Yms 2011-12-17 06:00, 11.230 W m⁻²; JP-Tef 2022-04-09 02:00 differs by 9.063 W m⁻². These are method differences, **not uncertainty intervals**. Longwave still needs correct hour-ending/half-hour interval support, cloud variability and clock scrutiny.

## Audit status and outputs

`05bc_compare_shadow_methods_READONLY.py` has a self-test and three tests for whole-block training exclusion, input-hash fail-closed behavior and interpolation boundaries. The actual local run wrote 17 comparison rows and 45 alternative candidate rows, all explicitly `HOLD_NO_APPROVAL`. The local comparison TSV SHA256 is `b47a64cf168b0ba06fece224f18676d653ef8d62b9c88bb577566351c49ec007`; the alternative-shadow TSV SHA256 is `67547a7cce5aaf10b776e44c2b4e683bf742f3bb0ea3306034a9dbc43b2d021c`. It did not read a source ZIP or write production forcing; no PFT or soil investigation was undertaken. The script rejects different input hashes and creates output only in a fresh child of a directory named `japanflux_stage05bc`. The local preview and paste are not committed as raw source data. The new alternative is not ready for application and does not invalidate the original 45-field HOLD.

**Next scientific evidence:** verify Tef/Tmd source clock and historical sensor/elevation metadata; seek truly measured tower or spatially appropriate additional station checks, with temporal support documented; test candidate behavior against measured data where available. Examine the AZ source-gate summary if subsequently available. All 45 values remain HOLD; zero repairs approved.
