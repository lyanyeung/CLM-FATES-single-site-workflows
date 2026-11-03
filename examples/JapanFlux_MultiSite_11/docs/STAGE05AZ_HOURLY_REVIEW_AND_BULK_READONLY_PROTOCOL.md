# Stage05AZ: existing hourly context review and one-batch source audit

**Status:** local analysis of operator-supplied precomputed tables and synthetic code tests only. The 16-ZIP Stage05AZ batch has **not yet run on IRIDIS6**. All 45 original fields remain SCIENCE HOLD and zero half-hour replacements are approved.

## What the existing hourly tables actually show

The operator supplied terminal output for Stage05AT Tef 2011, Stage05AU Tmd 2005 and Stage05AV Tef 2022/Tmd 2011+2022 tables. Reported file SHA256 values are respectively `76150a3759de8877972dc6c7f883c582d8901346e7eb5b55616bfb9034db3566`, `b495a5ec81e9da2e427bb870c8b6a53c105bfbe1d797d7445ff84221d5e00182` and `37b86b556ad7239e693dde8dfdc6e6bf36a89c619ab204199ea0a60fa66c4e68`. They identify the files according to the operator command; this local analysis did not independently hash those remote files. The supplied terminal-paste SHA256 is `abe5fa975129cc6d57f20ecae81d70cc451150755d073307a25864685fb13f3c`. The previous 1,677-row source-window paste SHA is `bb0e0317caf3ddf56d1aa003edc518a03e19f17ea5a6a95a4588bb3f18e9c0e6`.

The companion pasted-table analyzer uses the already reported grouped QC2 bridge shadows and compares them to these existing hourly values. It uses the operator's **unverified** UTC+9 hypothesis for the base results. For `sp`/`t2m` it interpolates hourly instantaneous grid values to the midpoint of the half-hour interval, a temporal approximation. For `strd` it uses the hourly mean for the hour ending after the half-hour interval; for a fractional offset that crosses an hourly boundary it weights adjacent hourly means by overlap, assuming within-hour constancy. This assumption cannot recover actual half-hour radiation. Timestamps, half-hour support and grid/site differences remain limitations, not exact tower observations.

Nearby background means source F minus ERA5-Land grid context, restricted to the supplied short hourly-table coverage; the comparison excludes every flagged same-site/variable point and ±2 hours around it. Reported examples below contain only **QC2 ERA-derived source values**, not independent QC0 tower measurements. Their small sample sizes and overlapping temporal support do not support a calibrated correction or uncertainty bound.

| Group | At shadow points: shadow minus matched grid | Nearby QC2 F minus grid: median, count | Interpretation |
|---|---|---|---|
| Tmd PA, 2005 | −0.653 to −0.658 kPa | −0.694 kPa, n=5 | Difference is of comparable sign and scale to nearby source/grid context, not proof of its cause. |
| Tmd PA, 2011 | −0.778 to −0.767 kPa | −0.720 kPa, n=5 | Background comparison is close in scale but the event differs from that local median. |
| Tmd PA, 2022 | −0.660 to −0.714 kPa | −0.678 kPa, n=5 | Same caution; no independent tower anchor or grid height verified. |
| Tmd TA, 2005 | −0.092 to +0.078 °C | −0.088 °C, n=5 | A grid-context comparison only; MDS is separately gapfilled. |
| Tmd LW, 2005 | +2.08 and +4.41 W m⁻² | +3.46 W m⁻², n=8 | Each grid value is an hour mean, not measured half-hour truth. |
| Tef LW, 2011 | −11.55 and −11.81 W m⁻² | −13.11 W m⁻², n=6 | Small QC2 context sample; unverified clock. |
| Tef LW, 2022 | −16.18 and −21.73 W m⁻² | −31.77 W m⁻², n=6 | Nearby same-source discrepancy is also substantial; this alone neither validates shadow nor supports a correction. |

The source QC2 background shows why a simple test of whether a shadow falls within a grid-hour envelope is not sufficient: source/grid offsets also occur outside the flagged values. The opposite conclusion is equally unwarranted: agreement with a QC2 background does not prove the source or bridge is accurate.

Original BIF longitudes are 142.107122°E for Tef and 141.523147°E for Tmd, giving local **mean** solar offsets of about UTC+09:28:26 and UTC+09:26:06 via longitude × 4 minutes/degree. This calculation is an informative sensitivity case, not proof the publisher used local mean solar time, applied no equation-of-time adjustment, or encoded interval start as assumed. In that alternative, Tef 2022 shadow-minus-grid values are approximately −24.98 and −21.73 W m⁻² under the hourly-mean overlap approximation; Tmd 2005 PA is roughly −0.654, −0.650 and −0.652 kPa. The sensitivity does not resolve the clock conflict.

## One read-only batch for all five sites

`05az_bulk_existing_era5l_source_clock_audit_READONLY.py` reuses the already downloaded **16** explicitly SHA-pinned CDS source ZIPs (nine Fjy/Khw/Yms and seven Tef/Tmd site-days), validates CRC, CSV schema, variable/hour coverage, grid coordinates, physical screens and units, and does not call CDS or the network. The pre-existing Fjy 2005 ZIP had a verified payload but its original request transaction was not observed; do not upgrade that provenance claim. It checks all five original outer JPF ZIP SHA256s, and the previously recorded AW ledger and AY-window hashes, both before and after the analysis. Source ZIPs are read to hash them, not altered. If any source file, schema, grid, timestamp or hash is different, the run fails rather than bypassing the gate.

For each original flagged group it calculates a full-group QC2 bridge shadow, joins to existing grid support, records AW's UTC+9 envelope without treating it as approval, exports original F/MDS and co-timed PA/TA/LW/F_QC fields, and computes descriptive source-minus-grid background separately for QC0, QC1 and QC2, split before and after the event. Flagged points and ±2 h are excluded; only actual common grid coverage is used. This background is not applied as a correction. QC0, QC1 and QC2 must never be conflated.

Fjy/Khw/Yms use their prior source-verified UTC+9 standard-time convention. Tef/Tmd receive four diagnostic scenarios: UTC+8:30, UTC+9 operator hypothesis, UTC+9:30 and longitude-derived local mean solar offset. The ±30-minute cases are sensitivity checks, not verified uncertainty bounds. Instantaneous PA/TA use midpoint interpolation; strd uses de-accumulated hourly energy /3600 and weighted hourly overlap, **without a second difference**. No approach generates a unique measured tower half-hour.

The run creates a new direct child of `~/japanflux_stage05az` containing `summary_HOLD.json`, `candidate_hourly_context_HOLD.tsv`, `group_source_grid_residuals_HOLD.tsv` and `background_pairs_READONLY.tsv`. It never creates a shadow forcing file. No raw JPF/CDS ZIP, production forcing, PFT, model case, Slurm or AD400 is written. The included synthetic end-to-end test creates its own fake 16 ZIPs, 45 flags and 97-point windows, verifies 99 scenario rows / 17 groups / zero approved, and checks that a tampered ZIP aborts before output. The tests do not prove the actual IRIDIS input will pass.
