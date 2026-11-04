# Stage05BP: six-site source meteorology diagnostics

**Implemented and synthetic-tested locally; no real Stage05BP run is claimed.** The batch covers JP-Api, JP-Fhk, JP-Spp and JP-Tak, and the JapanFLUX2024 sources JP-Tom and JP-Tgf. It records evidence only. No site is cleared for use and no repair is approved. The separate five-site 45-field Stage05BF ledger remains all HOLD and is not altered or reassessed here.

## Four JPF stations

Consume the operator's existing full Stage04 JSON, four Stage05D same-release companion ERA audit JSONs and three Stage05F selected-source impact JSONs. Require Stage04's full-11 read-only status, the four exact source-row counts and no triggered Stage04 selected-F threshold flags. Verify Api's Stage05D reported zero source anomaly starts; require Fhk 8 in/12 outside, Spp 6/9 and Tak 9/6 selected-source coverage, and zero selected-F flags in the existing Stage05F event-scope screens. These gates test the recorded report structures and stated counts; the Stage04/05D/05F input file hashes are newly observed before and after, not independently pinned at their earlier creation. Exact source ZIP hashes are independently checked against the Stage00 transfer records.

Also run the hash-pinned existing Stage05K metadata reader for each original JPF nested ZIP. It records BIFVARINFO variable/QC/unit groups and README/site metadata time hints. These are source excerpts, not automatic interpretation of QC codes or time zones. Reused Stage05F event points may be measured QC0 and numerically different from same-release ERA, but the raw labels and product semantics must be verified; those event screens do not certify other weather, subtle in-range shoulders or a complete forcing. The four sites remain **review only**.

## Two JapanFLUX2024 stations

Read the original direct ZIPs, streaming Tom COREVARS HR and HH plus Tgf COREVARS HH once each to EOF. Validate headers, row widths, exact native intervals and continuous order, previously reported row counts, Tom's native HR/HH abutting boundary, and the Stage04 per-stream counts for RH>100, VPD<0, P<0, PA<50 and SW<−20. Outer ZIPs are SHA256 checked before and after; member CRC is exercised by reading each selected member fully. Separate stream timestamps are not converted to UTC.

For each native row, preserve raw QC labels and pair RH_F with VPD_F at the same source interval. Count valid pairs, RH>100, any VPD<0, VPD<−1e−9, tiny negatives −1e−9≤VPD<0, overlap and disagreement categories, by native year. Apply the same tiny/material split to negative precipitation. These are diagnostic tolerances in *native assumed units*, not approval to clamp or a published scientific validity threshold. Count distinct stream/time rows once when any screen fires; do not add RH and VPD counts as independent events. Report field minima/maxima and raw-QC histograms. Capture original fields/QC for two prior and two subsequent intervals around PA<50 or SW<−20. A missing context at a source boundary is explicitly marked.

`special_derived_screen_events_HOLD.tsv` records every selected source row meeting these diagnostic conditions once, with original F and raw QC strings, stream identity and tags. It is an audit table, not a forcing file. `summary_HOLD.json` includes the full metadata excerpts, yearly counts, isolated event contexts, source hashes, observed report hashes and output SHA256. A compact summary is printed for the operator to paste back. Existing source values, source QC labels and original ZIPs are never modified.

## Operational boundary

No CDS downloads or reruns of the 45 existing comparisons. The script opens six original ZIPs and hashes each before and after; Fhk/Api/Spp/Tak nested ZIPs are buffered in memory one at a time by the existing Stage05K helper (256 MiB cap). Tom/Tgf source tables are streamed without extraction. This is a substantial read on a shared login node; run serially with `nice -n 10`, and follow local cluster usage rules. No scheduler job is submitted. A hash, chronology, row-count, schema, previous-count or report-scope mismatch stops the batch without manufacturing a PASS.

The six-source expected SHA256s are the [Stage00 operator-verified transfer hashes](STAGE00_01_VERIFIED_TRANSFER_AND_ZIP_INVENTORY_20261101.md). Input JSON hashes are logged rather than claiming preexisting hash pinning. All outputs are written exclusively into a fresh child of `~/japanflux_stage05bp/` after input and source rechecks. The script never opens PFT, soil data, model cases, Slurm or AD400 files.
