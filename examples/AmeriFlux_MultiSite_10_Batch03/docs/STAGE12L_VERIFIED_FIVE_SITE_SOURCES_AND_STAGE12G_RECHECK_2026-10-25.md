# Batch03 Stage12l VERIFIED: US-Kon new ERA5-Land yearly evidence; reuse Stage12g to count accepted RH

On 2026-10-25 (07:54–07:57 UTC), the user ran [Stage12l](../scripts/stage12/12l_five_site_non_MtB_year_source_priority.py) on IRIDIS6. AST syntax, `--self-test`, full `--check`, and `--download --max-new 3` PASSED, including SHA provenance from Stage12k, Stage12f, Stage12e, Stage10b and the original site/year source plan.

| New yearly source | Stage12e original native RH source-missing rows now with source | CDS hourly coverage | Verified SHA256 |
|---|---:|---:|---|
| US-Kon 2008 | 101 | 8,928 hours | `ccffba5c84d9ce738036b29a7e23ed79b0ec55ceb2b2609fa5c6dca7693fbc32` |
| US-Kon 2011 | 51 | 8,904 hours | `d64de7ac23b11b40bf67485edb7ca3dfaf985fc567cab21110daecd452658cda` |
| US-Kon 2012 | 44 | 8,928 hours | `6067f72efd4a6499b69639a8fc752f0d01196b7dbb882d8a6f53180b9a9d6bbb` |
| **Total** | **196** | **3 site-years** | |

The original Stage12e five NON-US-MtB sites had 447 missing-year source-native RH cases across **30** source site-years. Now 196 have newly verified gridded yearly evidence, with **251 cases across 27** missing year/site sources. The five-site records by station are US-Kon 211, US-NR1 135, US-Me6 80, US-MMS 15, US-NR3 6. All new datasets were downloaded to the original SHA-pinned Stage12f external evidence source directory using its same coordinates, raw CDS request schema, QA and immutable receipts. Source-only download did **not** modify any original tower TA, pressure, raw FLUXMET timestamp, six-site science-trial forcing, DATM, Slurm or CIME. **US-MtB received NO new source-year download**; its original 1,035 scientific holds and failed measured-QC0 GRID_RH validation remain unchanged.

## Next operation: re-use tested existing Stage12g, do not invent Stage12m download loop

[Existing Stage12g script](../scripts/stage12/12g_apply_new_year_ERA5Land_RH_shadow.py) has Git blob `14eabe09a56614808d6186d88fa5576233ed240b`, previously passed IRIDIS6 AST, --self-test, --check and --run in its earlier three-US-MtB-source-year state. The script's `sources()` **discovers all newly Stage12f-VERIFIED site/year receipts dynamically**, without hardcoding 3 years. Therefore no code edits or new source data copies are needed.

Re-running `--check` and then `--run` after Stage12l will check **six** independently verified new source-years (US-MtB 2020, 2022, 2024 + US-Kon 2008, 2011, 2012); together these cover **1,234** original missing-year native RH source events. The remaining **1,576** original missing-year source events break down as **1,325 US-MtB** and **251 across five non-US-MtB stations**. Importantly, evidence coverage is **not** successful humidity repair: Stage12g applies original source VPD QC1/QC2, unchanged EC tower temperature/pressure and exact native time, valid dewpoint/water/ice RH and strict 5C tower/grid T/pressure/boundary checks. Output count `new_ERA5Land_RH_only_research_repairs` will include **the prior US-MtB 3** plus the as-yet-unknown US-Kon accepted count. Subtract three from that total (after successful receipt and site-level verification) to obtain newly accepted US-Kon candidate count. Do not infer acceptance of all 196.

Stage12g always builds a **new, isolated, INCOMPLETE six-site NOLEAP shadow** from the original Stage12e reference, never overwriting the previously sealed Stage12g run or any prior Stage12b–e/source files. It preserves the original **233 physics source holds** and excludes all valid original humidity/QBOT. Its `--check` is read-only. If any input checksum or source science guard fails, do not run `--run`. **Post-v5, DATM, spinup releases remain zero**.

The next download action is conditional on the **actual US-Kon 196-case acceptance fraction**, not automatically obtaining the other 27 missing-year sources. US-MtB remains quarantined scientifically until independent observed humidity validation supports a specific change.
