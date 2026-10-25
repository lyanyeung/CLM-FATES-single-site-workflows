# Batch04 Stage14: IRIDIS6 verified eight VPD/RH physical closure candidates

**2026-10-25 operator output:** pinned Stage14 script completed `--self-test` PASS and `--apply` PASS. It generated **three complete source-length FLUXMET HH candidate CSVs**, replacing **8 VPD_F values and paired RH** without modifying **TA_F**, **PA_F**, native source QC columns or prior Stage07–13 data.

**New source candidate directory (immutable):**

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage14_humidity_closure_candidate/candidate_20261025T075601Z_3473a555
```

| Site | Original source HH rows in new full CSV | Repaired HH | Complete derived FLUXMET file SHA256 |
|---|---:|---:|---|
| US-SP1 | 368208 | 6 | `3f2489eea6e7016b3c184bd90c93acd6597d32fc3d4cc8872ac28237a5181806` |
| US-SRG | 315600 | 1 | `57f650493a510cffe3146e3371599479f243ee188fb676b55c269683a1a63f39` |
| US-Seg | 333120 | 1 | `22db08e969883cb7f5bc0dd7c3b161c60582c6fe6fe8715a0c9e23598cafbea6` |
| **Total** | **1,016,928** | **8** | — |

## Exact humidity replacement ledger (source: Stage14 operator stdout)

| Site | Native timestamp | Unchanged original tower TA °C QC0 | Previous VPD hPa | Revised VPD hPa | ERA5-Land RH % | ERA5-Land T2m °C |
|---|---|---:|---:|---:|---:|---:|
| US-SP1 | 200010091800 | -6.900 | 4.894 | 2.27462321445 | 37.6948979723 | 14.3708129883 |
| US-SP1 | 200010091830 | -7.100 | 4.927 | 2.15689710498 | 40.0035876 | 13.7762237549 |
| US-SP1 | 200710151730 | 11.150 | 14.025 | 5.56929547941 | 57.9653888399 | 25.5472045898 |
| US-SP1 | 200801160800 | -8.211 | 6.148 | 0.928134030469 | 71.866079283 | 8.17287597656 |
| US-SP1 | 200801160830 | -4.365 | 6.597 | 1.18789835603 | 73.1668680824 | 8.71965942383 |
| US-SP1 | 200802030800 | -3.613 | 4.717 | 0.0474406318334 | 98.9871457277 | 13.005456543 |
| US-SRG | 201903191200 | 0.718 | 17.133 | 4.66027707879 | 27.6119445343 | 18.8648010254 |
| US-Seg | 201612271800 | 0.015 | 7.037 | 2.63121106028 | 56.9969123237 | 6.68883666992 |

**Operator final line:** `STAGE14 RESULT: 8/8 VPD-RH physical closure candidates; 8/8 original TA QC0 scientific HOLDs remain`.

## Scientific gate is intentionally still blocked

These **8/8 numerical VPD/RH replacements are PHYSICALLY CLOSED candidates**, not an assertion that tower TA is true. Previous Stage13 inspected ±6 h original tower neighbours and found 7 unstable thermal boundaries and 1 without bilateral QC0/1 anchors. The original TA QC0=0 is an original product flag, not an independent validation; grid T2m can differ by >20 °C at some sites/times, suggesting a temperature provenance issue. A physically closed humidity calculation at the retained anomalous TA does not resolve this science risk.

- Eight independent **`HOLD_QC0_TOWER_TEMPERATURE_CONFLICT`** entries remain.
- **US-Syv's 606 inherited science HOLDs + 10 Stage07 ERA edge failures remain deferred**; do not silently mark Batch04 10/10 as model-approved.
- Stage14 includes a new ten-site input-pointer manifest `stage14_latest_ten_candidate_manifest.tsv`; only the 3 above sites point to Stage14; 7 others inherit authoritative Stage12 pointers. SHA record `stage14_receipt.json`; explicit incomplete marker `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP`.
- No Post-v5 processing, DATM forcing or CLM-FATES spinup was approved or started. First scientifically distinguish false tower-T outliers from true unusual microsite temperature using original tower history and independent reference, then set explicit forcing acceptance policy.

**GitHub script:** [14_eight_humidity_physical_closure_keep_qc0_t.py](../scripts/stage14/14_eight_humidity_physical_closure_keep_qc0_t.py).
