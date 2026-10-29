# US-NR3 scientific source audit

Scope: **US-NR3 Niwot Ridge Alpine (T-Van West)** only. US-MtB and US-Me6
belong to separate review streams. The user authorised new audit code and
GitHub synchronisation on 2026-10-29; this is not data-repair approval.

`nr3_01_source_inventory_READONLY.py` is a first-pass reconciliation tool.
It requires Python, NumPy and pandas, and never imports or runs historical
repair/download scripts. It has no output-file, download, repair, or model
execution mode. A Python audit hook rejects file writes and subprocesses.
All tables, provenance and errors go to the terminal. Use `python -B`.

Version `nr3-01-v1.1-20261029` fixes the first operator-run stop on historical
`2007-01-12T04:00:00` timestamps. Only the ISO `T`/space separator is
normalised; native instants, SHA pins, physical thresholds and HOLD rules
are unchanged. Tests reject timezone-bearing values, nonzero seconds,
off-grid minutes, invalid dates and duplicated equivalent timestamps.
The v1 cluster run passed original source SHA/annual QC and metadata checks,
then stopped before the 238-row reconciliation; it was not a complete PASS.

In the existing `clm_fates_env` environment on IRIDIS6, from this repository:

```bash
python -B examples/AmeriFlux_MultiSite_10_Batch03/scripts/us_nr3_science/nr3_01_source_inventory_READONLY.py --self-test
python -B examples/AmeriFlux_MultiSite_10_Batch03/scripts/us_nr3_science/nr3_01_source_inventory_READONLY.py --check
```

The default experiment root is the exact path in the handoff. `--root PATH`
allows an explicitly identified read-only copy with the same internal
layout. Never point to another station or fabricate absent receipts.

First return the grouped terminal output. After the source inventory passes,
these optional switches print complete CSV sections to the terminal:

```bash
python -B examples/AmeriFlux_MultiSite_10_Batch03/scripts/us_nr3_science/nr3_01_source_inventory_READONLY.py --check --emit-missing
# 1,484 rows is substantially more output; request it separately if needed:
python -B examples/AmeriFlux_MultiSite_10_Batch03/scripts/us_nr3_science/nr3_01_source_inventory_READONLY.py --check --emit-anomalies
```

Do not add `tee`, file redirection or a report-generation wrapper without
separate permission to write those result files.

## What the first pass checks

- Exact Stage07 release, original input-manifest/output-receipt link and
  original primary/companion SHA256. The independently read local ZIP member
  hashes are embedded; a different release or changed original fails.
- Exact native `TIMESTAMP_START` join, independent continuous 30-minute
  chronology, start/end intervals, original CSV line IDs (header is line 1),
  and Stage10K exception lines 195333/195334.
- Original annual QC0/1/2 and simultaneous dual-QC0 coverage, numeric RH
  availability (which is **not** automatically measured/QC-approved truth),
  and original same-release ERA negative water-vapour-pressure inventory.
- Stage12G -> Stage12E and Stage10I -> Stage10H -> Stage10D/07 receipt links;
  individually hashed evidence CSVs actually used. SHA consistency does not
  establish an independent digital signature or scientific approval.
- Complete 315,360-row NOLEAP native calendar; exact **238 = 172 protected
  physics HOLD + 66 other gaps**, with the **six** Stage12G source-year
  rows nested within the other gaps. All missing fields, inherited reasons,
  native timestamps, source QC, contiguous episodes and overlap with the
  1,484 Stage10 anomaly identities are computed, not assumed equal.
- Existing NR3 ERA5-Land receipt/file hashes and recorded requests. This
  first inventory explicitly does **not** revalidate NetCDF CF coordinates,
  grid orography, physical representativeness or an admitted forcing clock.
- Before/after SHA256 for every evidence file read through the file checker.

The historical paths and counts are intentionally explicit: if any fail,
return `NR3_STOP` and the preceding output. Do not relax assertions or pick
another shadow to obtain a pass. Shared receipts contain other sites, but
no other site's raw meteorology or forcing file is opened.

## Local original-package audit

```bash
python -B nr3_01_source_inventory_READONLY.py --raw-zip /path/to/AMF_US-NR3_FLUXNET_2007-2024_v1.3_r1.zip
```

This hashes the original primary, companion ERA, BIF and HH BIFVARINFO
members without extraction, reads only needed columns and prints annual QC
and metadata. It makes no claim to have checked IRIDIS6 Stage12G/10 ledgers.

The original local package establishes ONEFlux `1.3.5-rc`, processing date
`20260401`, LST without DST, nominal UTC offset -7, elevation 3504 m and GRA.
Variable-specific HH BIFVARINFO records nominal 3 m TA/VPD/RH measurement
height and generic resistance-temperature/capacitance-RH sensor types,
effective from `200705171300`. These metadata do not prove continuous
sensor operation in every year. The separate BADM workbook does not explain
the missing 2017/2018/2023 QC0 observations.

## Scientific boundaries and next work

This is an inventory, **not a completed scientific review**. No repair
method has yet been independently validated by this script, and no event is
approved for a new version. Next steps require the actual returned evidence:
reconcile missing/anomaly overlaps; trace BASE and original sensor QA
(including 2017 numeric RH); establish the upstream cause of inconsistent
paired ERA variables; check grid temperature/dewpoint/pressure/orography and
the installed CTSM/CDEPS code; then test candidate humidity methods against
genuine simultaneous tower QC0 using held-out dates and source years.

No threshold relaxation, automatic QC2 filling, source/shadow overwrite,
DATM, AD400 or Slurm is authorised.

## Second pass: grid physics and genuine QC0 tests (v2)

```bash
python -B examples/AmeriFlux_MultiSite_10_Batch03/scripts/us_nr3_science/nr3_01_source_inventory_READONLY.py --science --compact
```

This rechecks the inventory before comparing fixed, uncalibrated hypotheses
using existing NR3 ERA5-Land files only. It needs the same `netCDF4` package
already used by Stage09/10. ZIP NetCDFs are opened in read-only memory,
without extraction or downloads. The first operator-returned successful
inventory established 238 missing across 53 episodes, intersection 172 with
the 1,484 source anomalies, and 66 other gaps (41 temperature-difference,
19 ice-screen failures and six missing external-year rows). These are
operator-returned, SHA-linked results, not a new remotely executed run here.

The science mode:

- Checks the exact padded UTC hourly coordinates, units, point consistency,
  finite T2m/D2m/SP and available static/orography variables for all existing
  NR3 years. Absent grid elevation remains explicitly unresolved; pressure
  differences are not converted into a claimed measured grid altitude.
- Uses only the documented native midpoint +7-hour alignment. It does not
  optimise time shifts or approve a DATM clock.
- Compares **A: absolute vapour pressure**, **B: water-relative humidity**,
  and **C: specific humidity** transferred from grid to retained tower T/P.
  C is computed by converting grid e/P to q, then q to e at retained site P.
  No method is fitted or bias-corrected after seeing the observations.
- Validates against original simultaneous tower TA/VPD QC0, with basic
  water-physical truth checks. It retains observed ice-supersaturation and
  site-grid-temperature conflicts in the truth cohort rather than filtering
  away difficult cases according to the proposed method. Reports VPD/e MAE,
  bias, RMSE, P95 absolute error and >1 hPa error share, by whole source year
  and temperature regime, plus equal-date and equal-year weighted summaries.
  The 1 hPa level is a reported error diagnostic, not an admission threshold.
  These fixed methods have no training folds; full-year test blocks and
  complete-date summaries avoid random-halfhour splits. The downscaled
  companion may have used tower observations in its original fit and is
  therefore not scored as an independently withheld prediction.
- Evaluates all three methods separately on the original 1,484 anomalies
  and current 238 missing slots. Existing water/ice/T/P/QBOT limits and the
  4 hPa adjacency guard are retained. Proposed adjoining values are screened
  jointly in memory. Numerical passes are **sensitivity counts**, never
  repaired counts or permission to fill the protected 172. Actual HOLD=238
  and approved repairs=0 throughout this workflow.
- Reports matched month/temperature-regime QC0 support without inventing a
  scientific sample-size cutoff. No truth in 2017/2018/2023 is inferred from
  ERA-derived QC2. Original RH/MDS availability and true QC0 brackets are
  shown separately, without interpolating any event.
- Prints a public CDEPS saturation/cap sensitivity using reference Git blob
  `181eac30acb63214204fd54476a599827e886bfa` from
  [datm_datamode_clmncep_mod.F90](https://github.com/ESCOMP/CDEPS/blob/8b51a06b7e1633f640983d619bc9c7d34de34b84/datm/datm_datamode_clmncep_mod.F90).
  The formula is a reference, not assumed to be the installed/active model.
  It also reads DATM source excerpts under the existing project `CTSM`
  directory (override with `--model-root PATH`). Installed source alone does
  not prove the active case datamode or executable build.

`--compact` omits repetitive baseline metadata and the long hash dictionary;
it still verifies those files before and after the run and prints the source
manifest and selected-shadow hashes. `--emit-science-rows` prints the 238x3
method-support table, and `--emit-anomaly-science-rows` prints the 1484x3
physics table. Both are terminal-only and should be requested separately
because they produce substantial output. Neither switch writes a report.

Grid dewpoint is interpreted over water. Ice-relative RH at retained air
temperature is a separate diagnostic; true ice supersaturation must not be
described as negative vapour pressure. The inherited ice HOLD remains in
force. See [ECMWF near-surface humidity documentation](https://confluence.ecmwf.int/pages/viewpage.action?pageId=177484060).
