# Stage05AY grouped shadow versus existing independent ERA5-Land envelopes

## Evidence and interpretation

The operator supplied a terminal export of the actual Stage05AW 45-field ledger, reporting source-file SHA256 `6b717bdf8232388f59af849da01dbc316a8166e0a07305d3d2567d2d7d55e6ad`. The paste received here has SHA256 `26389c5d0e6c3ccf784160fb729846565ba0a98909dc90ca46ab10a65cf57dc0`. The prior de-duplicated full Stage05AY window paste has SHA256 `bb0e0317caf3ddf56d1aa003edc518a03e19f17ea5a6a95a4588bb3f18e9c0e6` and reported original window SHA `89e9b41055b782da97ebcbda9c6ddb55a3c6bf6426ad40fdd2bb865e98a687d9`. These original IRIDIS6 hashes were reported by the operator; they were not independently recomputed from the remote files here. Stage05AW original evidence is its previously completed audit; the present computation does not re-download or rerun the original 45 ERA5-Land comparisons.

The accompanying deterministic text analyzer reconstructs the 17 full-flag-group linear shadows from the supplied Stage05AY native windows and joins all 45 fields to the Stage05AW ledger by exact site, variable and native timestamp. It checks distinct fields, populations, original source F agreement, units, clock provenance, original HOLD, F=ERA QC2 unflagged shadow endpoints and original F outside its prior envelope. It tests the *unrounded* shadow against that field's saved hourly minimum and maximum, inclusively. The sign and distance are measured to the closest envelope edge, not to a matched hourly observation.

The hourly envelope is gridded context from the original Stage05AW definition. It is **not** a tower half-hour measurement, calibrated uncertainty interval, pass/fail tolerance, or validation dataset. An outside value is not automatically wrong, and an inside value is not automatically right. Station-versus-grid elevation, model and site bias, differing spatial support, instantaneous versus interval-averaged variables, meteorological variability and timing can cause differences. Tef/Tmd candidate UTC uses an unverified operator JST+9 hypothesis despite their source README solar-time wording. No clock or processing root cause is resolved by this comparison. All 45 fields remain SCIENCE HOLD; zero replacement values are approved.

## Results: 45 fields, not 45 independent events

12 shadows fall inside their corresponding previously saved context envelope, 20 fall below and 13 above. The following are individual field counts. Differences are distances from the *nearest envelope edge*, not estimates of station bias:

| Site | Variable | Inside | Below | Above | Outside-edge distance |
|---|---|---:|---:|---:|---|
| Fjy | PA | 0 | 0 | 6 | 1.295–1.478 kPa above |
| Khw | PA | 4 | 2 | 0 | 0.0068–0.0393 kPa below |
| Khw | TA | 0 | 0 | 3 | 0.163–0.506 °C above |
| Khw | LW_IN | 2 | 0 | 0 | — |
| Yms | PA | 0 | 6 | 0 | 0.639–1.048 kPa below |
| Yms | LW_IN | 0 | 0 | 4 | 1.10–17.35 W m⁻² above |
| Tef | LW_IN | 2 | 2 | 0 | 16.18–21.73 W m⁻² below |
| Tmd | PA | 0 | 9 | 0 | 0.573–0.669 kPa below |
| Tmd | TA | 2 | 1 | 0 | 0.029 °C below |
| Tmd | LW_IN | 2 | 0 | 0 | — |

The comparison exposes structured discrepancies rather than establishing a failure of one source. Fjy PA shadows are higher than the saved grid envelope in both 2005 and 2011; Yms PA shadows are lower in both years; Tmd PA shadows are lower in 2005, 2011 and 2022. These signs suggest possible persistent representativeness or source-processing differences worth testing, but **are not proof** of an elevation error, correct station value or a stable bias. First obtain the exact site and model-grid elevation/pressure metadata and inspect independently acquired hourly samples outside the flagged interval. Do not fit a correction from the anomalous cells or infer it from just these few envelope summaries.

Yms 2011 LW shadows are 12.94 and 17.35 W m⁻² above the saved envelope; Tef 2022 shadows are 16.18 and 21.73 W m⁻² below it. These differences warrant interval-ending, source-clock sensitivity, cloud/radiation variability and grid-site representativeness review. The earlier same-source masking exercise found a maximum LW point discrepancy of 20.37 W m⁻² in the local windows, but that number is **not** an uncertainty bound and cannot be used to excuse or reject these specific discrepancies.

For Yms PA the candidates use full three-point flagged groups with genuinely unflagged outer QC2 endpoints. The two old centre-only Yms shadows produced by the initial Stage05AY script remain invalid. No new 30-minute estimate is classified as approved.

## Next evidence gate

1. Reuse the already downloaded, hash-verified ERA5-Land files and saved Stage05AL/AT/AU/AV hourly context; confirm the exact variable, grid point, elevation/terrain, timezone hypothesis, units and valid-time/interval convention. For `strd`, the existing hourly time-series product is already de-accumulated; do not difference it again.
2. Compare clean source windows and the grid time series over the actual common coverage, including station versus grid elevation for PA and ±clock/half-hour alignment sensitivity for solar-clock sites. Report coverage and source dependence. A stable offset may indicate representativeness but cannot be assumed a constant correction without independent validation.
3. Wherever available, use measured QC0 as a genuinely independent temporal holdout; do not relabel QC1, QC2 or MDS as measured, and do not convert the overlapping same-source pseudo-gap tests into tower uncertainty.
4. Retain both the continuity shadow and independent-reference-assisted method as competing hypotheses alongside manual HOLD. Any subsequent repair requires per-field documented scientific review and explicit approval.

No original JPF ZIP, production forcing, PFT, model case, Slurm or AD400 was modified, and no replacement was authorized by this comparison.
