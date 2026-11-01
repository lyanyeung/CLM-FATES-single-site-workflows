# JapanFlux Stage05B — actual JPF source/ERA comparison, 2026-11-01

## Actual operator-provided output

**Site:** JP-Khw, JP-Tmd. **Source:** JPF FLUXMET_HH extracted for tiny event windows through [Stage05B](../scripts/stage05/05b_JPF_shared_timestamp_source_ERA_QC_READONLY.py). `STATUS: READONLY_CONTEXT_EXTRACTED`: JP-Khw 16 context rows, JP-Tmd 24. No user report of source modification or extra Slurm audit. Times represent **native package clock**, not proven UTC/JST.

### Central finding — simultaneous zero-pressure and ultra-negative ERA air-temperature artefacts

| Native start | JP-Khw TA_ERA = TA_F when QC2 (°C) | JP-Tmd TA_ERA = TA_F when QC2 (°C) | JP-Khw PA_F=PA_ERA (kPa) | JP-Tmd PA_F=PA_ERA (kPa) |
|---|---:|---:|---:|---:|
| 2005-08-12 02:00 | 23.988 | 19.425 | 97.823 | 99.004 |
| 2005-08-12 02:30 | −122.144 | −132.399 | 48.912 | 49.502 |
| 2005-08-12 03:00 | −268.276 | −284.222 | 0 | 0 |
| 2005-08-12 03:30 | −122.665 | −132.688 | 48.922 | 49.506 |
| 2005-08-12 04:00 | 22.946 | 18.847 | 97.844 | 99.013 |

These numbers show **exact linear interpolation of the corrupted central value at 02:30 and 03:30**:
- Khw: (23.988 + (−268.276))/2 = **−122.144**, and ((−268.276)+22.946)/2 = **−122.665**.
- Tmd: (19.425 + (−284.222))/2 = −132.3985 ≈ **−132.399** (to printed source precision), and ((−284.222)+18.847)/2 = −132.6875 ≈ **−132.688**.
- PA Khw: 97.823/2=48.9115 ≈48.912; 97.844/2=48.922. PA Tmd: 99.004/2=49.502; 99.013/2=49.5065 ≈49.506 to printed precision.

For all corresponding 2005 cells shown above, `TA_F_QC=2` and `PA_F_QC=2`. At these rows, `TA_F=TA_ERA` and `PA_F=PA_ERA`. **The sampled pressure series is impossible as real atmospheric pressure; it is derived/fallback-path contamination, not a tower pressure anomaly.** The exact upstream failure is not proven.

For 2005-08-12 02:00 and 02:30, `LW_IN_F=LW_IN_ERA` equals **39.171 W m−2 at Khw**, **28.519 W m−2 at Tmd**, each with `LW_IN_F_QC=2`. These are similarly improbable low LW values. At 03:00 the longwave column jumps to plausible ~400 W m−2 (despite invalid temperature/pressure). Each science field should be treated independently.

### Repetition on 2011-12-17 confirms defective ERA values can be shielded by tower observations

| Native start | JP-Khw TA_F (QC0) | JP-Khw TA_ERA | JP-Tmd TA_F (QC0) | JP-Tmd TA_ERA | PA_F=PA_ERA each site |
|---|---:|---:|---:|---:|---|
| 2011-12-17 06:00 | −0.697 | 0.260 | −16.130 | −8.198 | ~99 kPa |
| 2011-12-17 06:30 | −0.497 | −134.008 | −15.780 | −146.210 | ~49–50 kPa |
| 2011-12-17 07:00 | −0.450 | **−268.276** | −15.320 | **−284.222** | **0 kPa** |
| 2011-12-17 07:30 | −0.587 | −133.671 | −13.890 | −146.234 | ~49–50 kPa |
| 2011-12-17 08:00 | −0.283 | 0.934 | −11.730 | −8.246 | ~99 kPa |

At 2011 affected dates **TA_F_QC=0** with `TA_F=TA_F_MDS` on shown rows. **Do not replace these good source-selected TA_F values with corrupted TA_ERA**. `LW_IN_F_QC=0` and physically plausible `LW_IN_F` likewise preserve tower input where `LW_IN_ERA` has extremely low values at 06:00–06:30. Pressure **remains contaminated**: `PA_F_QC=2`, `PA_F=PA_ERA` and invalid ~half/zero kPa at 06:30/07:00/07:30.

Identical site-specific extreme temperatures and LW minima **recur across August 2005 and December 2011**. For Khw, `TA_ERA=-268.276` repeats and `LW_IN_ERA=39.171` repeats. For Tmd, `TA_ERA=-284.222` and `LW_IN_ERA=28.519` repeat. This is strong indication of **repeated placeholder/sentinel or an upstream data-transform defect** in the processed ERA-related pathways, not evidence of physical repetition. The underlying cause has yet to be verified in an independent raw ERA5 acquisition.

### Important nuance — MDS is *not automatically a trusted substitute*

Khw on 2005-08-12 shows `TA_F_MDS ≈1.1–1.5°C` while nearby `TA_ERA` values on uncorrupted steps are around 23–24°C; the two products disagree strongly. Tmd `TA_F_MDS ≈20.3°C` over the same event, more consistent with nearby `TA_ERA ≈19°C`. **Never blanket-replace flagged ERA with MDS**; inspect source/observations, seasonal meteorology, alternate candidates and support before any repair.

## Interpretation bounds and next step

This stage compares `FLUXMET_HH`'s **embedded** `*_ERA` columns against `*_F` selected values and `*_F_QC`. The evidence shows embedded `*_ERA` values are corrupted at specific native timestamps and propagate through some `*_F` fields where those fields use QC2. It does **not** prove whether the original separate `ERA5_HH` product contains the same problem, nor whether the defect occurred upstream during reanalysis download, processing, resampling, missing-value handling, or archive packaging.

Next use [Stage05C](../scripts/stage05/05c_compare_embedded_ERA_to_release_ERA5_HH_READONLY.py) to compare **separate `ERA5_HH` and `FLUXMET_HH` files from the SAME published ZIP** at exact suspect timestamps. This is a same-release test, **not an independent external reanalysis verification**. Operate one site per invocation without Slurm and without writing source data.

**Science decision:** no auto-substitution and no modification to original ZIP; source-specific targeted correction could be proposed **after** provenance verification, with SHA-controlled overlay and separate science approval. No AD400/Normal400 is authorized by these checks.
