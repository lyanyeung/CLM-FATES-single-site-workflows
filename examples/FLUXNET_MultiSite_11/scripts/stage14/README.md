# Stage 14 — Search ALL local BIF CSV sources for older TA_F and WS_F metadata

**READ ONLY**: this script scans every BIF-named CSV under each station's `forcing/raw*/` tree, including HH, DD and MM files when present; records the dated `VAR_INFO_HEIGHT` for `TA_F` and `WS_F` only. It is a secondary audit after Stage13b, not a generator of accepted ZBOT, DATM or spin-up.

Run on IRIDIS6:

```bash
conda activate clm_fates_env
python ~/FLUXNET_MultiSite_11_stage14/01_scan_all_bif_sources_readonly.py 2>&1 | tee ~/FLUXNET_11_stage14_all_bif.log
R=~/FLUXNET_MultiSite_11/stage14_all_BIF_source_search
column -s, -t "$R/04_cross_source_earliest_height_summary.csv"
```

Outputs:
1. `01_all_BIF_file_inventory.csv`: every scanned BIF filename, SHA256, how many valid TA/WS height entries.
2. `02_all_TA_WS_height_evidence.csv`: unmerged records, timestamp, height, date precision, BIF path, group, SHA256.
3. `03_unusable_or_conflicting_BIF_records.csv`: empty, malformed or contradictory heights.
4. `04_cross_source_earliest_height_summary.csv`: earliest date across all available BIF products.

Notes: DD/MM and HH from the same source commonly duplicate the *same* BIF instrument metadata; do not confuse duplication with independent evidence. BIF `VAR_INFO_DATE` is the reported start date of instrument variable metadata (not necessarily complete site history). A flux/sonic anemometer tower height is not necessarily the `TA_F` instrument height. `ZBOT` must only follow the accepted `TA_F` timeline. Historic height backfilling requires evidence and a decision ledger, especially BE-Bra, whose historical 40 m EC observations and 32 m ICOS EC observations differ (see https://www.icos-belgium.be/ESBrasschaat.php); these EC heights must not be assigned to TA without verifying a TA sensor reference.
