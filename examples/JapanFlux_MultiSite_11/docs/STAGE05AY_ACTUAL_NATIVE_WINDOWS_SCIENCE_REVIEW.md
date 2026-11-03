# Stage05AY: review of actual ±2-hour native windows

## Scope and reproducibility

The operator pasted the output of the requested read-only `native_windows.tsv` subset from `/home/ly3n24/japanflux_stage05ay/run_20261103T070524Z_4159846/`. The supplied text has 405 rows: all 45 site/native/variable flags, nine offsets (−4 through +4 half-hours) per flag. Its local attachment SHA256 is `6e159076cf8cea9bafd4e4b8d3b123857960cace002e4f791e905370de123656`. It is a terminal-rendered excerpt, not the original TSV; empty fields were rendered as spaces. The original full ±24-hour windows and their file SHA were not supplied. Conclusions below are limited to visible rows, do not claim re-reading IRIDIS6 files, and retain all 45 HOLD / zero approved replacements.

The excerpt contains 27 PA, 6 TA, 12 LW target fields. Overlapping windows agree on shared target-variable F/QC/ERA/flag values. Every target has F_QC=2 and its displayed F equals same-release ERA. The exact original full source integrity evidence is the separately documented Stage05AY operator run; this is not a second ERA5-Land audit.

## Numerical shape and provisional grouped boundaries

The 45 original flags form **17 site-variable native-time groups**: nine PA triplets, two TA triplets, and six LW_IN pairs. In the visible ±2-hour excerpts, the immediate value just outside each group is inside the broad Stage05AX range and selected as QC2; this is a provisional description, not certification that those neighboring values are uncontaminated. A three-HH group is 90 minutes of flagged intervals; a two-HH group is 60 minutes. These are lengths of the pre-existing flagged sets, not proven complete physical anomaly durations. Other abnormal, range-passing or missing neighboring cells may extend an episode. Native labels are original interval starts.

| Site | Variable | Native date | Flagged starts | Outside-group F values, left / right | Flagged F sequence |
|---|---|---|---|---|---|
| JP-Fjy | PA | 2005-08-12 | 02:30–03:30 | 89.985 / 89.989 | 45.160, 0.334, 45.161 |
| JP-Fjy | PA | 2011-12-17 | 06:30–07:30 | 89.911 / 90.087 | 45.123, 0.334, 45.211 |
| JP-Khw | PA | 2005-08-12 | 02:30–03:30 | 97.823 / 97.844 | 48.912, 0, 48.922 |
| JP-Khw | PA | 2011-12-17 | 06:30–07:30 | 99.013 / 99.143 | 49.506, 0, 49.571 |
| JP-Khw | TA | 2005-08-12 | 02:30–03:30 | 23.988 / 22.946 | −122.144, −268.276, −122.665 |
| JP-Khw | LW_IN | 2005-08-12 | 02:00–02:30 | 400.939 / 402.613 | 39.171, 39.171 |
| JP-Yms | PA | 2005-08-12 | 02:30–03:30 | 98.240 / 98.253 | 67.794, 37.349, 67.801 |
| JP-Yms | PA | 2011-12-17 | 06:30–07:30 | 98.971 / 99.055 | 68.160, 37.349, 68.202 |
| JP-Yms | LW_IN | 2005-08-12 | 02:00–02:30 | 416.663 / 424.131 | 44.790, 44.790 |
| JP-Yms | LW_IN | 2011-12-17 | 06:00–06:30 | 248.447 / 261.686 | 44.790, 44.790 |
| JP-Tef | LW_IN | 2011-12-17 | 06:00–06:30 | 205.277 / 204.503 | 26.164, 26.164 |
| JP-Tef | LW_IN | 2022-04-09 | 02:00–02:30 | 272.029 / 255.368 | 26.164, 26.164 |
| JP-Tmd | PA | 2005-08-12 | 02:30–03:30 | 99.004 / 99.013 | 49.502, 0, 49.506 |
| JP-Tmd | PA | 2011-12-17 | 06:30–07:30 | 98.896 / 99.029 | 49.448, 0, 49.514 |
| JP-Tmd | PA | 2022-04-09 | 02:30–03:30 | 99.232 / 99.158 | 49.616, 0, 49.579 |
| JP-Tmd | TA | 2005-08-12 | 02:30–03:30 | 19.425 / 18.847 | −132.399, −284.222, −132.688 |
| JP-Tmd | LW_IN | 2005-08-12 | 02:00–02:30 | 395.313 / 402.308 | 28.519, 28.519 |

Units: PA kPa, TA °C, LW_IN W m⁻². Values are source F, not approved repairs.

For **all nine PA and both TA triplets**, the left flagged value equals `(outside_left + flagged_centre)/2` and the right equals `(flagged_centre + outside_right)/2`, within 0.0005 in the displayed variable units. The consistently repeated relationship across sites and dates strongly motivates testing for temporal interpolation around an anomalous source sample. It does not prove the upstream value, the processing code, a missing-value encoding, or where any error occurred. Each of the six LW groups instead consists of two identical flagged half-hours; JP-Yms repeats 44.790 and JP-Tef repeats 26.164 across two different dates. This separate signature warrants investigation of hourly radiation handling and downscaling, without asserting its cause.

For the two Yms PA groups, all three flagged points must remain together for further review; the broad 50 kPa absolute screen failed to identify the two side points. The first Stage05AY script's two Yms centre-only bridges are invalid because their anchors were also flagged; the subsequent fix rejects those anchors. A future group-based shadow screen can bridge the three *already flagged* intervals from the outer QC2 values only after explicitly checking the group boundaries and wider window; it would remain an unapproved same-release ERA-derived scenario, not measured data. The corrected current script still treats the centre's flagged boundaries as unresolved; it does not yet generate a three-point Yms shadow.

## Other variables, MDS and competing methods

The excerpt reports JP-Tmd 2005 TA MDS values 20.337, 20.343 and 20.342 °C with `TA_F_MDS_QC=2`; JP-Khw reports 1.133, 1.322 and 1.464 °C with `TA_F_MDS_QC=3`. These are gap-filled estimates, not tower QC0 observations. In general FLUXNET FULLSET documentation the MDS quality meanings for 2 and 3 are medium and poor, respectively, and are **different from** `TA_F_QC=2` ERA-source coding. Confirm that the exact JapanFlux release follows those conventions from its publisher documentation before relying on their labels: https://fluxnet.org/wp-content/uploads/variable_codes_FULLSET_20160711.pdf . The Khw MDS values disagree strongly with nearby selected TA around 23 °C; the Tmd MDS values are nearer the local context but still require independent validation. None is approved.

The exported co-timed PA, TA and LW F/QC fields permit checking other variables, but an individual QC0 label does not validate the anomalous variable, and QC2 fields can share common processing. The source PA raw field is shown as −9999 at the flagged PA points; target LW_IN MDS fields are shown as −9999 in this excerpt. Absence of a good local anchor is not proof that no independent measurement exists elsewhere.

Compare three options by event: (1) native same-release QC2 bridge over the full flagged group, with outer-neighbor provenance and endpoint sensitivity; (2) previously acquired independent ERA5-Land constrained by representativeness, clock, matching interval, and held-out reference errors; (3) manual HOLD where boundary/clock/physics is insufficient. The QC2 bridge carries shared-source-error risk. The independent hourly product does not uniquely determine a tower half-hour and may differ because of grid/elevation. For example, Tef 2022 LW QC2 bridge values printed in the original run, about 266.48 and 260.92 W m⁻², sit below the previously reported nearby independent hourly context envelope 282.653–302.753 W m⁻²; this is a context discrepancy to investigate, not by itself proof that the site bridge is wrong, especially given the unverified solar/JST clock and grid-site differences.

Inspect the full ±24-hour original windows, temporal and physical continuity, source MDS definitions, original-release generation provenance, and exact ERA5-Land interval matching before any proposed repair approval. No production forcing, raw ZIP, PFT, cases, Slurm or AD400 changes are made by this report.
