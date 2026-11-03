# Stage05AY full-window review: 17 grouped shadow scenarios, all HOLD

## Evidence and scope

The operator's read-only export reported `INPUT_SHA256 89e9b41055b782da97ebcbda9c6ddb55a3c6bf6426ad40fdd2bb865e98a687d9` for the IRIDIS6 `native_windows.tsv`; its export command checked all 45 target windows have offsets −48..+48 and consistency across duplicate windows. This digest was supplied by the operator; it was not independently recomputed from the original IRIDIS6 file here. The pasted de-duplicated terminal text received here has SHA256 `bb0e0317caf3ddf56d1aa003edc518a03e19f17ea5a6a95a4588bb3f18e9c0e6`. It has 1,677 unique site×variable×native records, 45 flagged fields, 35 site×native times and 17 consecutive site-variable flagged groups. The saved Stage05AY window did not record an earlier file hash at generation time, so the later operator digest cannot cryptographically prove that the file was unchanged between generation and export; retain that limitation. Source ZIP hashes, README and source rows were checked in the earlier actual Stage05AY run.

The grouped windows contain 99 half-hours for a three-flag group and 98 for a two-flag group: 24 hours before the first flag through 24 hours after the last. Each group has full 30-minute cadence, no missing selected F values, and no unflagged selected F outside the broad PA 50–115 kPa, TA −70–65 °C, LW 70–650 W m⁻² screens. A co-timed PA/TA/LW screen found no additional outside-range value outside the original 45 flags. This does not detect subtle or in-range contamination; no screen proves that the duration is exactly the flagged group. Most selected window F values are QC2; JP-Tmd 2005 TA includes six QC1 values. Target flags and the immediate unflagged group anchors are QC2 and F=ERA. None of the QC2 anchors is an independent tower observation.

The 17 grouped native-time descriptions and evidence for shared midpoint-like PA/TA distortions and repeated LW values appear in [the preceding actual-window review](STAGE05AY_ACTUAL_NATIVE_WINDOWS_SCIENCE_REVIEW.md). Tef/Tmd source README solar-time versus operator JST+9 remains unresolved. No new CDS downloads or repeats of the existing independent ERA5-Land 45-field comparisons were performed.

## Grouped exploratory QC2 bridge and same-source masking checks

For each existing flagged group, a linear shadow bridges its immediate *unflagged* QC2, F=ERA outer endpoints. The whole Yms PA triplet is grouped, avoiding the invalid centre-only bridges of the first Stage05AY run. The numbers below are reproducible **unapproved scenarios**, not scientific approvals, independent observations or forcing edits. A screen-passing endpoint may still carry shared-source error. Values are rounded for display; use the script's underlying calculations for exact reproducibility.

For sensitivity only, mask each possible contiguous clean same-release QC2 block of the same length within the group window, require all masked points and both endpoints to be QC2 F=ERA and inside the broad screen, exclude blocks whose points or endpoints fall within two hours of any same-site/variable flagged time, bridge the endpoints, and compare to the masked source values. `blocks` overlap heavily. MAE and p95 summarize individual absolute point differences against the **same downscaled product**, not independent tower truth, calibrated uncertainty, confidence intervals or independent samples. p95 uses the sorted observation at Python `round((N-1)*0.95)`. Results assess local shape sensitivity only; they do not demonstrate absence of common bias or validate extreme-weather behavior.

| Site | Variable | First native flagged start | Flags | Shadow values, unapproved | Masked blocks | Mean abs. difference | p95 abs. difference |
|---|---|---|---:|---|---:|---:|---:|
| Fjy | PA | 2005-08-12 02:30 | 3 | 89.986, 89.987, 89.988 | 80 | 0.0102 | 0.0295 |
| Fjy | PA | 2011-12-17 06:30 | 3 | 89.955, 89.999, 90.043 | 80 | 0.0127 | 0.0345 |
| Khw | PA | 2005-08-12 02:30 | 3 | 97.828, 97.833, 97.839 | 80 | 0.0071 | 0.0160 |
| Khw | PA | 2011-12-17 06:30 | 3 | 99.046, 99.078, 99.111 | 80 | 0.0089 | 0.0240 |
| Yms | PA | 2005-08-12 02:30 | 3 | 98.243, 98.246, 98.250 | 80 | 0.0050 | 0.0130 |
| Yms | PA | 2011-12-17 06:30 | 3 | 98.992, 99.013, 99.034 | 80 | 0.0075 | 0.0187 |
| Tmd | PA | 2005-08-12 02:30 | 3 | 99.006, 99.008, 99.011 | 80 | 0.0071 | 0.0185 |
| Tmd | PA | 2011-12-17 06:30 | 3 | 98.929, 98.963, 98.996 | 80 | 0.0113 | 0.0285 |
| Tmd | PA | 2022-04-09 02:30 | 3 | 99.213, 99.195, 99.177 | 80 | 0.0120 | 0.0325 |
| Khw | TA | 2005-08-12 02:30 | 3 | 23.727, 23.467, 23.207 | 80 | 0.2288 | 0.8268 |
| Tmd | TA | 2005-08-12 02:30 | 3 | 19.280, 19.136, 18.992 | 74 | 0.1399 | 0.3937 |
| Khw | LW_IN | 2005-08-12 02:00 | 2 | 401.497, 402.055 | 82 | 2.1746 | 6.1947 |
| Yms | LW_IN | 2005-08-12 02:00 | 2 | 419.152, 421.642 | 82 | 2.3252 | 6.5383 |
| Yms | LW_IN | 2011-12-17 06:00 | 2 | 252.860, 257.273 | 82 | 3.3058 | 10.7603 |
| Tef | LW_IN | 2011-12-17 06:00 | 2 | 205.019, 204.761 | 82 | 2.9832 | 8.1693 |
| Tef | LW_IN | 2022-04-09 02:00 | 2 | 266.475, 260.922 | 82 | 3.2980 | 9.9030 |
| Tmd | LW_IN | 2005-08-12 02:00 | 2 | 397.645, 399.976 | 82 | 3.3652 | 9.4373 |

Units: kPa, °C and W m⁻² respectively. Display uses Python rounding; 99.008 for the Tmd 2005 centre represents 99.0085 before display rounding. The maximum masked point error across the six LW groups ranges from 8.50 to 20.37 W m⁻², larger than the corresponding means; even the p95 is not an uncertainty bound for the true event. PA shadows are locally smooth in this limited same-source exercise; TA and especially LW show larger local interpolation sensitivity. These comparisons do not authorize any of the 45 numbers.

## Scientific next steps

1. Treat the PA triplets as a promising continuity-based **shadow design**, while retaining shared ERA-source dependence and unresolved timebase for Tmd. Compare full-group bridge to independent hourly ERA5-Land with exact source time, grid/elevation context and held-out measured QC0 where actually available.
2. For TA, compare the two shadow bridges against independently verified reference timing and MDS quality; Khw MDS_QC3 and Tmd MDS_QC2 are gapfills, not QC0. Check temperature/humidity relationships if those fields and valid QC are available.
3. Give LW special attention: hourly mean/half-hour mapping and cloud variability make linear bridge sensitivity greater. Tef 2022 previously reported nearby ERA5-Land hourly 282.653–302.753 W m⁻² versus shadow 266.475/260.922; this is a representativeness/clock/interval question, not proof either is correct. Confirm original publisher clock for Tef/Tmd and independently verify hourly-end interval and grid/site representativeness before narrowing candidates.
4. Resolve the processing chain for the repeated zero/offset and midpoint patterns using authoritative original-release material or verified upstream inputs; do not infer a root cause solely from coincident native dates.

**All 45 remain SCIENCE HOLD; approved replacements 0.** No raw ZIP, production forcing, PFT, model case, Slurm or AD400 changes occurred. A complete shadow forcing file was not produced, so identity of its non-event rows has not been tested. The accompanying text analyzer reads only the supplied terminal export and performs deterministic checks/self-test; it is not an IRIDIS6 source scan, and must not be presented as independent source or timebase verification.
