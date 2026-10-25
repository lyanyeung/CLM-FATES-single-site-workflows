# Batch04 Stage14 — eight VPD/RH closure candidates generated; QC0 temperature holds remain

**Operator evidence:** Stage14 IRIDIS6 command completed at 2026-10-25 07:56 UTC, syntax PASS, `--self-test` PASS and `--apply` PASS.

**What succeeded:** 8/8 exact anomalous native half-hours received physically consistent `VPD_F` and derived `RH` using independently sourced and SHA-verified ERA5-Land hourly T2m/dewpoint and original tower `TA_F`. The original `TA_F`, `TA_F_QC`, `PA_F`, `VPD_F_QC` were not overwritten.

| Site | Native half-hours changed | Full derived rows | Full file SHA256 |
|---|---:|---:|---|
| US-SP1 | 6 | 368,208 | `3f2489eea6e7016b3c184bd90c93acd6597d32fc3d4cc8872ac28237a5181806` |
| US-SRG | 1 | 315,600 | `57f650493a510cffe3146e3371599479f243ee188fb676b55c269683a1a63f39` |
| US-Seg | 1 | 333,120 | `22db08e969883cb7f5bc0dd7c3b161c60582c6fe6fe8715a0c9e23598cafbea6` |
| **Total** | **8** | **1,017,?** | — |

The complete files are in:
```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage14_humidity_closure_candidate/candidate_20261025T075601Z_3473a555
```

| Site | TIMESTAMP_START (LST) | Original tower TA °C (retained) | Old VPD hPa | New candidate VPD hPa | Grid RH % |
|---|---|---:|---:|---:|---:|
| US-SP1 | 200010091800 | -6.900 | 4.894 | 2.27462321445 | 37.6948979723 |
| US-SP1 | 200010091830 | -7.100 | 4.927 | 2.15689710498 | 40.0035876000 |
| US-SP1 | 200710151730 | 11.150 | 14.025 | 5.56929547941 | 57.9653888399 |
| US-SP1 | 200801160800 | -8.211 | 6.148 | 0.928134030469 | 71.8660792830 |
| US-SP1 | 200801160830 | -4.365 | 6.597 | 1.18789835603 | 73.1668680824 |
| US-SP1 | 200802030800 | -3.613 | 4.717 | 0.0474406318334 | 98.9871457277 |
| US-SRG | 201903191200 | 0.718 | 17.133 | 4.66027707879 | 27.6119445343 |
| US-Seg | 201612271800 | 0.015 | 7.037 | 2.63121106028 | 56.9969123237 |

**Distinct scientific gates:**
- Stage12 achieved **148/156** exact non-Syv original HOLD/jump-edge timestamps. Stage14 added **8/8 humidity numerical closure candidates** at the remaining eight, reaching **156/156 with numeric VPD/RH candidates**, but **eight original QC0 tower temperatures remain disputed**. They must not be called scientifically approved or fully corrected.
- US-Syv **606** original source HOLD entries plus **10** Stage07 skipped jump-edge entries remain deferred. Some old source HOLDs and edge skips overlap, so the unique count must be validated before any final production claim.
- Stage14 selected a new full ten-site candidate manifest `stage14_latest_ten_candidate_manifest.tsv`. It includes 3 new Stage14 full derived candidate CSVs and 7 unchanged previous Stage12 source file pointers. Preserve all SHA receipts and `UNRESOLVED_EIGHT_TOWER_TEMPERATURE_HOLDS.tsv`.
- The Stage14 output includes `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP`. No Post-v5 approval, DATM/CIME or spinup occurred.

## Next required check

Perform **read-only SHA/source-difference validation** for the full 10-site selection. For each of the eight new Stage14 target records confirm `TA_F`, `PA_F` and original QC fields remain bitwise unchanged, the only altered cells are VPD_F and RH, and `e_s(TA)`/VPD/RH closure is satisfied. Review original temperature anomaly sources separately; do not silently reclassify these 8 scientifically unresolved TA observations as solved.
