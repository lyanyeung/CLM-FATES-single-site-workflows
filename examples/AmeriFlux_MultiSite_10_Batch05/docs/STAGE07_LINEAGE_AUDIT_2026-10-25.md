# Batch05 Stage07 — original MDS/ERA consolidation lineage audit

**Observed:** 2026-10-25 operator run of `07_verify_fluxnet_qc_lineage_and_era_inheritance.py`. Syntax and self-test PASS; **STAGE07 SUMMARY audited=10/10 failed=none**; all ten original SHA256 fingerprints verified, no original writes, UTC conversions, repairs, forcing or Slurm jobs.

## Key result: exact inheritance of all flagged QC2 ERA variables

The *actual extracted* original `FLUXMET_HH` or US-UMB `FULLSET_HH` sources each contain `TA_F_MDS`, `TA_F_MDS_QC`, `TA_ERA`, `VPD_F_MDS`, `VPD_F_MDS_QC`, `VPD_ERA`, `TA_F`/`TA_F_QC`, `VPD_F`/`VPD_F_QC` and `RH`. None contains unsuffixed `TA`/`VPD` or `RH_QC`. These are facts about the ten selected files, not all raw AmeriFlux releases.

- **50,287** unique source-flagged rows found and matched with original `ERA5_HH` companion data by their *printed labels*; **0 unmatched**.
- **9,018/9,018** flagged `TA_F_QC=2` samples agree numerically with `TA_ERA` from their release companion (absolute tol 0.002°C); **9,632/9,632** flagged `VPD_F_QC=2` samples agree with `VPD_ERA` (0.002 hPa).
- **41,269/41,269** flagged `TA_F_QC=0/1` samples with a populated MDS comparison agree with `TA_F_MDS`; **40,655/40,655** flagged `VPD_F_QC=0/1` samples agree with `VPD_F_MDS`. These counts are within the selected source-flagged population, not an exhaustive full-series validation.
- **346** ERA `TA_ERA/VPD_ERA` pairs at flagged timestamps fail `0 <= VPD_ERA <= es_water(TA_ERA)`: **US-Vcm 343**, **US-Vcp 3**. This expanded screen includes Stage04's earlier 55 and should not be added to 55.
- No numerically detectable departure from advertised FLUXNET consolidated-variable selection was found in the Stage07 flagged population.

### Breakdown

| Site | Unique flagged rows | QC2 TA matches/tested | QC2 VPD matches/tested | QC01 TA matches/available MDS | QC01 VPD matches/available MDS | ERA self nonphysical at flagged rows |
|---|---:|---:|---:|---:|---:|---:|
| US-UiD | 3,644 | 3,428/3,428 | 3,428/3,428 | 216/216 | 216/216 | 0 |
| US-UMB | 119 | — | — | 119/119 | 119/119 | 0 |
| US-UMd | 38 | — | — | 38/38 | 38/38 | 0 |
| US-Var | 1,507 | — | — | 1,507/1,507 | 1,507/1,507 | 0 |
| US-Vcm | 16,549 | 985/985 | 1,025/1,025 | 15,564/15,564 | 15,524/15,524 | 343 |
| US-Vcp | 11,138 | 1,087/1,087 | 1,541/1,541 | 10,051/10,051 | 9,597/9,597 | 3 |
| US-WCr | 12,512 | 3,038/3,038 | 3,047/3,047 | 9,474/9,474 | 9,465/9,465 | 0 |
| US-Whs | 15 | — | — | 15/15 | 15/15 | 0 |
| US-Wjs | 4,703 | 480/480 | 591/591 | 4,223/4,223 | 4,112/4,112 | 0 |
| US-Wkg | 62 | — | — | 62/62 | 62/62 | 0 |
| **TOTAL** | **50,287** | **9,018/9,018** | **9,632/9,632** | **41,269/41,269** | **40,655/40,655** | **346** |

## Scientific interpretation and hold conditions

1. Official FLUXNET2015 metadata specify the HH consolidated `TA_F_QC/VPD_F_QC`: 0 = measured; 1 = good MDS fill; 2 = ERA-downscaled. **Different QC scale:** `TA_F_MDS_QC/VPD_F_MDS_QC`: 0 measured; 1 good; 2 medium; 3 poor. Do not use MDS_QC 2/3 automatically as valid alternative for poor ERA records.
2. `TA_F` and `VPD_F` are independently consolidated using their **own** flags. Mixed-source records can pair tower measured TA with ERA VPD, generating apparent RH contradictions. Two practical examples from original Stage07:
   - US-Vcp, 2008-04-09 11:00 printed local standard time: `TA_F=-3.424°C` (QC0); `VPD_F=6.643hPa` (QC2), identical to ERA VPD at `TA_ERA=7.022°C`.
   - US-Wjs, 2007-08-09 13:30: `TA_F=18.079°C` (QC0); `VPD_F=25.275hPa` (QC2), identical to ERA VPD at `TA_ERA=27.708°C`.
3. `RH` is present as a native release column, but its measurement/derivation and separate QC provenance are not established from Stage07. Even substantial RH agreement for QC0 does not prove it is independent. Do not reconstruct humidity forcing from it without original-source provenance.
4. The `346` ERA-pair negative-vapour-pressure results are conditional upon the explicit water saturation formula, the assumed pressure units and the currently printed local time labels. Evaluate release's source vapour-pressure reference and local station elevation before declaring ERA products broken.
5. All original operator checks are diagnostic. No adoption of ERA5-Land or MDS source values, automatic clipping, surface/ZBOT/PFT assignment, time shifts, forcing writes or Slurm jobs is authorized.

Official reference documents:
- FLUXNET FULLSET variable metadata: https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/
- FLUXNET SUBSET consolidated QC: https://fluxnet.org/data/fluxnet2015-dataset/subset-data-product/
- FLUXNET2015 timestamps as local standard time without DST: https://fluxnet.org/data/fluxnet2015-dataset/

### Stage08 scientific gate

[Stage08 all-row QC and MDS alternatives](../scripts/stage08/08_full_consolidation_QC_and_MDS_alternatives_readonly.py) is available for operator execution. Unlike Stage07's flagged-only lineage verification, it checks the **whole time series** for QC 0/1 versus MDS values, QC2 versus native ERA columns, `*_F_MDS_QC` distribution (0/1/2/3), source-selection contradictions, and alternative MDS paired humidity feasibility **without adopting poor MDS**. Stage08 should be run next and remain read-only.
