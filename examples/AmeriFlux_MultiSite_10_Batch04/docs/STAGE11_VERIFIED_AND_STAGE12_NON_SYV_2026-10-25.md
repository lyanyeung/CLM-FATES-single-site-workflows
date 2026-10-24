# Batch04: Stage11 verified; next Stage12 non-Syv repair

IRIDIS6 operator output verifies Stage11: `--self-test` PASS, **10/10 latest complete derived FLUXMET HH files SHA-verified**, no full data duplication, input manifest created at:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage11_latest_ten_manifest/candidate_20261024T232100Z_1c6ef02a/LATEST_10_SITES_FOR_POSTV5_INPUT.tsv`

Data provenance selection: **Stage07** = US-SP1, US-Syv, US-Ton; **Stage08** = US-Seg, US-Ses, US-Slt, US-SRG, US-Uaf; **Stage10** = US-Rpf, US-SRM.

**Remaining science HOLD entries (761):** US-Syv 606 (explicitly deferred by user), US-SP1 147, US-Seg 4, US-Uaf 2, US-SRG 1, US-Ton 1. Stage07 also skipped 12 direct ERA jump endpoints, including US-SP1 2 and US-Syv 10; some skipped timestamps may overlap earlier HOLDs. Stage10 successfully repaired the older 689 US-Rpf/US-SRM events, which are therefore not part of these remaining 761.

## Stage12 implementation

The script `scripts/stage12/12_repair_non_syv_science_holds.py` is committed on main at `c3a44684134a6a50e4086543301adc05e66365d9`; it has NOT YET run on IRIDIS6. It targets 155 old non-Syv HOLDs plus two SP1 skipped-edge timestamps (deduplicated). It retains native TA when trustworthy neighbours agree, never automatically overrides plausible native VPD; for invalid VPD or explicit unresolved jump endpoints it uses independent ERA5-Land from exact native-local-standard-time/BIF-aligned hourly T2m/dewpoint/surface pressure. For badly missing/non-QC0 tower TA, only physically checked neighbour interpolation or independent ERA5-Land T fallback is allowed. US-Seg location uses the previously approved original BIF group 1495 with 0.0001° input rounding tolerance. Ambiguous BIF stops only that site. US-Syv remains untouched.

The script reuses the already proven pinned Stage10 download/ZIP/NetCDF verifier as an imported local Python helper (requiring download of both files). Each Stage12 run downloads no more than three absent site-years, SHA-verifies latest full inputs, produces complete new site candidate CSVs only where values changed, writes a **new latest-ten input TSV**, exact-event decisions, SHA receipt and an `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker. It leaves all original FLUXNET and Stage05–11 outputs unchanged.

No Stage12 repair counts, source grids or production approvals can be claimed before Stage12 executes on IRIDIS6. Current verified gate: 10/10 complete input *candidate* files, not validated Post-v5/DATM.
