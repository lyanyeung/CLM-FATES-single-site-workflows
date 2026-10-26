# Batch04 SYVH9 — independent ERA5-Land longwave successfully fixes all 12 HH, ten-site seven-met NOLEAP numeric Gate-0 PASS

**Actual operator IRIDIS6 output, 2026-10-26 12:11 UTC; all statements below are grounded in user-returned log, not inferred completion.**

## Six independent CDS requests: 6/6 completed & source-verified

CDS `reanalysis-era5-land-timeseries`, `surface_thermal_radiation_downwards` (`strd`), de-accumulated hourly `J/m²`, divided by `3600` seconds to get **W/m²**, sampled at each site's **original BIF latitude/longitude and local-standard UTC offset**, then mapped to exact UTC **hour ending** for two local halfhours. Source full response SHA and original BIF SHA are recorded in SYVH9 receipts.

| Site / source year | Verified raw independent-CDS SHA256 |
| --- | --- |
| US-SP1 2004 | `3392907917247a0db2dc4767e8722da4b508fca51591776fb2125e1e05a4eee5` |
| US-SP1 2016 | `c90ca8c9ca75938213b859e2360dc327206f2aeeb761ca56df9212eb1bce8a8c` |
| US-Slt 2016 | `e3281ebc770db60ec1c3a3369741628922ccc0e6ae6f2c3310c6b012abe8c3a0` |
| US-Syv 2004 | `f326bdc828cc62ddd947153b62c8c5e57f4ff6c9106ec07f2a10e6966ad2a5fd` |
| US-Ton 2004 | `45c285c154e577fed9d96782b86a2335af0ad31ea73cf3209be43e8a1b87034f` |
| US-Uaf 2004 | `b33e5fce5cdbe25355ea929ef03d6b65312457beeddcc11019a2709ce70a69cf` |

**Source contamination established 12/12:** all 12 existing erroneous low `LW_IN_F` values are identical to their respective original processed `LW_IN_ERA`. The earlier SYVH7 matched original source and packaged ERA and correctly aborted. The actual independent ERA5-Land data are different and physically plausible.

## Actual corrections, exact local native halfhour starts

| Site | Times `YYYYMMDDHHMM` | Previous `LW_IN_F` (W/m²) | Independent ERA5-Land replacement (W/m²) |
| --- | --- | ---: | ---: |
| US-SP1 | `200412040000` and `200412040030` | 44.764 | **315.523750** |
| US-SP1 | `201610091900` and `201610091930` | 44.764 | **346.473854** |
| US-Slt | `201610091900` and `201610091930` | 45.855 | **282.656771** |
| US-Syv | `200412032300` and `200412032330` | 43.388 | **287.980694** |
| US-Ton | `200412032100` and `200412032130` | 8.353 | **241.692639** |
| US-Uaf | `200412032000` and `200412032030` | 34.390 | **206.298472** |

All **six** changed two-HH episodes passed before/after boundary checks and actual `SYVH9 INDEPENDENT CDS LONGWAVE EXACT 12/12 PREFLIGHT PASS`.

Five newly generated complete research CSVs were compared rowwise with their immediately preceding SHA-verified candidate; **only four SP1, and two each Slt/Syv/Ton/Uaf original native halfhours were edited** (with ERA-origin `LW_IN_F_QC=2` where the field exists); no other T/VPD/PA/RH/SW/WS/P or prior trial field changed. Other five site selected source pointers remain unchanged. User-previously approved Syv 297 temperature, 415 humidity, 18 derived RH halfhours preserved.

### Actual research manifest and output source SHA

Full output:
```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_Batch04_SYVH9_12_low_LW_5sites_independent_ERA5Land_research_not_approved/candidate_20261026T121123Z_a8b8146f
```
Final ten-site source selection:
```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_Batch04_SYVH9_12_low_LW_5sites_independent_ERA5Land_research_not_approved/candidate_20261026T121123Z_a8b8146f/RESEARCH_TEN_SITE_MANIFEST.tsv
```

| Changed site | Verified new complete CSV SHA256 |
| --- | --- |
| US-SP1 | `52dc605ac7f1076aa94581c0d968d369ad237945ba01082acfef5524be889236` |
| US-Slt | `d1fd715b3ceb0104d81db040a84fc7754f3ccd3f985dac0aaa9c3ae5de45dbb4` |
| US-Syv | `79a26035ba687d216a84e4ed624e3f872478b488248f78de0686a847b52b6c71` |
| US-Ton | `c5960991fdddf5516cea28238f05f60edf894a527d18c8b5cf50f00ac182a9b9` |
| US-Uaf | `e5a5dd5d99839beb6d5443caa11f4624d4c5e24acdf547c420c72f37315b5204` |

## Final ten-site Gate-0 result: **10/10 PASS**

On the *new SYVH9 manifest*, the existing fully independent SYVH6 reviewer verified **all ten** complete input source SHAs, complete native 30-minute chronology, leap/NOLEAP calendar coverage, and numerical plausibility of `TA_F,VPD_F,PA_F,SW_IN_F,LW_IN_F,WS_F,P_F`, with **`NUMERIC_BLOCKERS={}` for every site**:

US-Rpf, US-SP1, US-SRG, US-SRM, US-Seg, US-Ses, US-Slt, US-Syv, US-Ton, US-Uaf.

Exactly **3 source VPD quantisation exceptions** retained at US-Rpf (2) and US-Syv (1), each <0.0005 hPa above source T saturation due to three-decimal VPD precision. Model humidity conversion must use an **explicit output-only precision policy** for those three; never overwrite raw source QC0 VPD/T. `QBOT` preview within previous numeric plausible source limits for all other halfhours.

Terminal: `SYVH9 FINAL 10 SITE NOLEAP SEVEN MET GATE0 READY 10 BLOCKED {} SOURCE_ROUNDING_HH 3`, followed by `SYVH9 COMPLETE TEN SITE NUMERICAL SEVEN MET GATE0 PASS - RESEARCH ONLY`.

**Scientific boundary:** Gate-0 is NOT Post-v5 production release. Before actual DATM/CLM-FATES, independently check and document source-sensor scientific approvals, tower/site met observation heights ZBOT, longwave/shortwave/precipitation unit convention and time centering, surface point domain/PFT, exact active CIME version stream mapping; source QA and user-approved fixes must be retained. Do not run Slurm or activate a DATM stream merely because numerical Gate-0 passed.
