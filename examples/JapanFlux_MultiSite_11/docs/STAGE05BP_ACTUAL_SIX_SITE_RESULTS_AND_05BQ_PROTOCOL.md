# Stage05BP actual results and Stage05BQ protocol

The operator reported an actual Stage05BP run with all six original ZIP SHA256s checked before and after, full Tom HR/HH and Tgf HH source scans, completion and zero approvals. The pasted output began at source checks; the earlier download checksum/self-test/test lines were not included. This reviewer did not directly read the IRIDIS files. Output is `/home/ly3n24/japanflux_stage05bp/run_20261104T031424Z_359887`; the pasted terminal attachment SHA256 is `b83c33596d465d06f26e3048dfd9d85673a3e2956a56f63ed7e513c25df272d6`. Operator-reported `summary_HOLD.json` SHA256 is `dbbd436cfb1ab40fca58ed6d7905a5477ccc92e55902f8d332df36e55069be5f`; `special_derived_screen_events_HOLD.tsv` is `dbf35b76fea6623241239f94dfdb22277c4ae10e05d40f7bbc14ec0fcaa944d0`.

## Four JPF sites

Api, Fhk, Spp and Tak retained no selected-F Stage04 threshold flags. The four original READMEs say local standard time without DST and each BIF reports UTC_OFFSET=9. Their exact BIFVARINFO records specify TA in °C, PA in kPa and VPD in hPa; for these selected F variables the source states QC 0 = measured, 1 = good gapfill, 2 = downscaled ERA. This source-label description does not guarantee an individual QC0 observation is physically correct. RH_F is absent in all four streams.

Stage05D's companion ERA screen reported Api 0 flagged native starts, Fhk 20, Spp 15 and Tak 15. At the screened events within selected-F coverage, existing Stage05F reports 8 Fhk, 6 Spp and 9 Tak starts; their flagged-variable selected F values differ from the companion ERA and have source QC0. The other flagged companion starts lie outside each selected stream's time coverage. These are specific-event results, not proof that all 1.47 million selected rows, non-screened source episodes, or the eventual forcing are error-free.

## Tom/Tgf complete COREVARS screens

| Stream | Source rows | RH>100 | VPD<−1e−9 | Both on same row | Tiny VPD negative [−1e−9, 0) | Tiny P negative |
|---|---:|---:|---:|---:|---:|---:|
| Tom HR 1999–2002 | 35,064 | 0 | 0 | 0 | 0 | 0 |
| Tom HH 2003–2013 | 192,864 | 6,583 | 6,583 | 6,583 | 753 | 4,322 |
| Tgf HH 2002–2022 | 368,160 | 9,493 | 9,493 | 9,493 | 21 | 3 |

RH/VPD pairs are the **same native rows**, not independent counts to sum. All 6,583 Tom high-RH cases occur in 2013. At Tgf, 8,466 of 9,493 occur during 2016–2020; temporal concentration suggests a source/instrument/processing hypothesis, not a proven cause. The smallest precipitation values were −2.0013e−15 for Tom and −1.31894e−15 for Tgf in source native units. The 1e−9 VPD tolerance is a diagnostic classification, not a published uncertainty threshold. The 21,177 exported rows are unique by site, source stream and native timestamp across all selected tests, including tiny negative precipitation/VPD and the two isolated Tgf cases.

The native Tgf 2003-12-31 23:30 PA is 0 kPa with raw QC0, between 100.67 and 100.55 kPa (also raw QC0). At the same timestamp TA is 0, RH 100 and VPD 0; these other fields deserve investigation rather than automatic replacement. Tgf 2015-12-15 14:30 SW_IN is −70.11575 W/m² with raw QC0, flanked by 165.3173 (QC1) and 15.8802 (QC0) W/m². Rapid cloud changes and differing source quality make interpolation uncertain. No value is approved.

The [JapanFlux2024 dataset paper](https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.html) explains that RH, vapor pressure and ERA gapfilling are linked and that ALLVARS contains original/input variables. Thus RH>100 and negative VPD are not independent confirmations of physical humidity; examine original channels and QC provenance before choosing how to treat them. Its generic format description should not be treated as verification of every per-variable QC semantics in these exact archives. Tiny negatives are obvious numerical candidates, but the original values are retained.

## Stage05BQ, prepared but not run on IRIDIS

The read-only batch verifies the actual BP summary and event-table SHA256s, then scans the four original JPF FLUXMET_HH files with Stage00 source hashes checked before and after. It computes a **diagnostic-only** water-saturation approximation and feasibility of `e = es(T) − VPD`, `q = 0.622e/(p − 0.378e)`, with PA kPa converted to hPa. The [UCAR equations](https://archive.eol.ucar.edu/projects/ceop/dm/documents/refdata_report/eqns.html) document the water-saturation approximation and q relationship. Saturation over ice, original VPD formulation, instrument and time support can change interpretations; results are screens, not validated QBOT or site clearance. No derived full forcing is written.

The batch independently checks the expected 21,177 unique saved BP event rows, 6,583/9,493 high-RH pairs, 753/21 tiny VPD and 4,322/3 tiny precipitation cases. It creates an **unapproved** per-field shadow ledger assigning zero to strictly tiny negative VPD/P values (5,099 fields) and reports two linear-neighbor **sensitivity-only** Tgf candidates. The two linear values are not chosen repair methods; in particular the SW neighbors have different QC labels and may span a cloud transition. RH>100 and material VPD negatives are not clipped or approved. It does not alter any source, forcing, PFT, soil, case, Slurm or AD400. All 45 earlier JPF candidates also remain HOLD. Four nested archives are read serially; no CDS request or repeat of the 45 ERA5-Land anomaly comparisons.
