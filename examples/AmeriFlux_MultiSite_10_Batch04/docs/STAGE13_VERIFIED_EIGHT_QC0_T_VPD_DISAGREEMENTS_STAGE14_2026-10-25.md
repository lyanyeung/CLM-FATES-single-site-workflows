# Batch04 Stage13 operator verified: eight QC0 temperatures and impossible source VPD

2026-10-25 IRIDIS6 Stage13 `--self-test` and `--inspect` PASS. All eight targets have original `TA_F_QC=0`; none has a physically possible source VPD at that recorded temperature. All raw RH are `-9999`. US-SP1 6, US-SRG 1, US-Seg 1.

| Site | FLUXMET LST TIMESTAMP_START | Source TA °C | Source VPD hPa | e_s(TA) hPa (water) | ERA5-Land T2m °C | ERA5-Land RH % | Prior Stage13 verdict |
|---|---|---:|---:|---:|---:|---:|---|
| US-SP1 | 200010091800 | -6.900 | 4.894 | 3.651 | 14.371 | 37.695 | unstable towers |
| US-SP1 | 200010091830 | -7.100 | 4.927 | 3.595 | 13.776 | 40.004 | unstable towers |
| US-SP1 | 200710151730 | 11.150 | 14.025 | 13.249 | 25.547 | 57.965 | unstable towers |
| US-SP1 | 200801160800 | -8.211 | 6.148 | 3.299 | 8.173 | 71.866 | unstable towers |
| US-SP1 | 200801160830 | -4.365 | 6.597 | 4.427 | 8.720 | 73.167 | unstable towers |
| US-SP1 | 200802030800 | -3.613 | 4.717 | 4.684 | 13.005 | 98.987 | unstable towers |
| US-SRG | 201903191200 | 0.718 | 17.133 | 6.438 | 18.865 | 27.612 | no two-sided tower anchors |
| US-Seg | 201612271800 | 0.015 | 7.037 | 6.119 | 6.689 | 56.997 | unstable towers |

Scientific implication: **the original VPD and TA cannot both be right at these eight times**. This is sufficient to demonstrate failed numerical physical closure, but NOT sufficient to conclude which TA sensor values should be replaced. Extreme US-SP1 temperature steps can indicate suspect observation segments. Original TA_QC=0 alone is not an external station-independent validation. US-SRG lacks two-sided tower temperature support; US-Seg rapid gradient remains ambiguous.

## Stage14 created in GitHub; NOT yet run

[Stage14 physics-only builder](../scripts/stage14/14_eight_humidity_physical_closure_keep_qc0_t.py) (commit `2c6b83ed9d55c487e9eaa32460ef7c5d56262f88`) uses all eight already downloaded and SHA-validated point/year ERA5-Land sources. For each exact native timestamp:

1. SHA-verify final Stage12 receipt (148/156), all exact eight unresolved event timestamps/status, latest source manifest and unchanged baseline full CSV.
2. Require exact original TA, VPD, PA and QC fields from Stage13, no silent source version drift. Require VPD>e_s(water,TA).
3. Retrieve independent grid RH = 100·e_s(D2m)/e_s(T2m) and interpolate to native half-hour through original BIF fixed local-standard UTC offset.
4. **KEEP original QC0 tower TA, PA, and all *_QC source columns unmodified**; replace only VPD_F with `e_s(TA_original)·(1−RH_grid/100)` and RH with matching `RH_grid`.
5. Output **three new full-length derived FLUXMET HH CSVs** for US-SP1, US-SRG and US-Seg. Other 7 stations simply retain final Stage12 selection pointers. Output one new 10-site manifest and independent SHA receipts.
6. Maintain **8 UNRESOLVED QC0 T SCIENCE HOLD** entries in a separate ledger. The eight are numeric humidity closure *candidates*, NOT 8 scientifically resolved tower temperature disagreements.
7. Continue to defer US-Syv old 606 science HOLDs and Stage07 10 unsuccessful ERA high-jump endpoints. Keep Post-v5, DATM, CIME and spinup disabled.

Run Stage14 on IRIDIS6 from the existing local directory with Stage10 helper already present:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_stage12"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/2c6b83ed9d55c487e9eaa32460ef7c5d56262f88"
  SCRIPT="$BASE/14_eight_humidity_physical_closure_keep_qc0_t.py"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage14/14_eight_humidity_physical_closure_keep_qc0_t.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --apply 2>&1 | tee "$BASE/stage14_apply.log"
)
```

Stage14 must retain the `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker even if 8/8 humidity closure candidates are numerically produced. No further independent ERA5-Land downloads are needed for these 8 exact timestamps.
