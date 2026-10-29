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
