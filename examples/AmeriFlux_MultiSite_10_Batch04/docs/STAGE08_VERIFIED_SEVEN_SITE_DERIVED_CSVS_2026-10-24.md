# Batch04 Stage08 VERIFIED — seven remaining complete derived FLUXMET HH files

**Date:** 2026-10-24. Operator IRIDIS6 output: Stage08 `--self-test` PASS and `--build-candidates` PASS. Seven full derived FLUXMET_HH files, sparse `candidate_patch.csv`, HOLD `unresolved_hold.csv`, `report.json` and original-source SHA receipts generated without original data changes.

## Exact results

| Site | Original HH records | Variable-level patch rows | Actual altered half-hours | HOLD count | Derived full file SHA256 |
| --- | ---: | ---: | ---: | ---: | --- |
| US-Rpf | 298080 | 0 | 0 | **688** | `63b0316017b6584137c3800ad3a99650fb567ba2e6a28686d3cb4d53e9fc7e57` |
| US-Seg | 333120 | 122 | 61 | 4 | `18dfe239f72ee37eeb773beb5e1c414a566323158ab8c475dc0a93058756c610` |
| US-Ses | 333120 | 238 | 119 | 0 | `3aca642cf1881725af36c2c5059b5f1f7bd58a41b2b607542b82a4051c6797cb` |
| US-Slt | 315552 | 0 | 0 | 0 | `9329e24ada05868674120e7023512296b675968c1367f7dd60774ce4fd192497` |
| US-SRG | 315600 | 16 | 8 | 1 | `28157c9cfd9c67f39f66186aae7ea070346bd3d39696c5b6822308b81d079365` |
| US-SRM | 385728 | 4 | 2 | 1 | `506b59a584ce446d5d6db15348b22b5346a515ee1a7cddc000c22598c865349f` |
| US-Uaf | 403248 | 36 | 18 | 2 | `72abb7b824f84439a34c2994c4396ab46dd8ca2aec357876d6e81c73521c267b` |
| **Total** | **2,384,448** | **416** | **208** | **696** | — |

Note: 416 are variable-level rows, comprising 208 RH + 208 VPD_F substitutions. These produce 208 different half-hours with modified source observations; none of the seven has a Stage08 TA/PA interpolation. QC0 physically admissible VPD were protected.

**Exact created directory**:
```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage08_remaining_seven_candidates/candidate_20261024T120137Z
```

## HOLD breakdown

- US-Rpf **688** `ERA_PAIR_HUMIDITY_INVALID`: the packaged ERA TA/VPD values fail the humidity-pair physical test. No Stage08 repair was applied for these; **do not substitute physically invalid ERA values**. Next workflow Stage09 can repair only short *physically confirmed* source VPD gaps using bounded neighbouring tower observations; if the native VPD is already physically valid, protect it and potentially only derive consistent RH.
- US-Seg **4**, US-SRG **1**, US-Uaf **2** have `SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID` holds. Compare native TA to trustworthy neighbours; preserve plausible tower TA. US-SRM **1** has `ERA_PAIR_HUMIDITY_INVALID`.
- US-Ses and US-Slt: zero Stage08 holds. This does not by itself certify completed model-ready processed_v5.
- **Ten Batch04 sites now have complete native-length derived candidate CSVs**: three Stage07 sites and seven Stage08 sites. Across Stage07 inherited Stage05 (754) plus seven Stage08 (696), **1,450 inherited HOLD entries** remain. Stage07 additionally skipped 12 direct ERA5 boundary endpoints; some may overlap other holds, hence no distinct new unique timestamp count can be asserted.

The seven full output files exist as user operator results on IRIDIS6. Their complete bytes were not independently accessible in this GitHub commit; SHA values and counts are directly transcribed from operator output.

**Model gate:** 0 approved Post-v5 outputs, 0 DATM launch, 0 CLM-FATES spinup. Keep original site releases, Stage05–08 outputs and named scientific blockers distinct.
