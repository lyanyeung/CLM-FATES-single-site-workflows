# Batch04 Stage07 VERIFIED — three full-length derived FLUXMET files created

**Evidence:** operator IRIDIS6 terminal output on 2026-10-24. Stage07 `--self-test` PASS (twice; explicit and inside `--apply`), original Stage05/Stage06 receipts and source CRC/SHAs verified, three new complete derived data CSVs generated. Original source FLUXMET/paired ERA and older Stage05/Stage06 candidate and report files were not modified.

### Results

| Site | Original HH rows | Unique flagged Stage06 jump endpoints | Native-time packaged ERA5 matches | Direct ERA5 VPD replacements applied | Actual modified rows in complete derived FLUXMET CSV | File SHA256 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| US-SP1 | 368208 | 34 | 34/34 | **32** | **62** | `9390f88948eaf621b4e697682da701675f08330b268f3661d5a98cd130364b28` |
| US-Syv | 438288 | 22 | 22/22 | **12** | **270** | `5086cbc0f08f73b218d08fdcf34cf0643a6ae1ea95c05c200a98800452b5b32e` |
| US-Ton | 438288 | 332 | 332/332 | **332** | **961** | `4ca4467a7f6180136ef06c8595bb36d2f25ae5413c91cd357c5c0d84a99d5646` |
| **TOTAL** | **1,244,784** | **388** | **388/388** | **376** | **1,293** | — |

There are **210 flagged Stage06 VPD edges**, with overlapping endpoints; hence **388 unique half-hour endpoints** rather than 420. **12** endpoints were skipped because the exact paired ERA5 VPD or its physical relation to retained site temperature failed the script's criteria. They are not silently copied from bad ERA. Counts of skipped endpoints by site, inferred from differences: US-SP1 2, US-Syv 10, US-Ton 0.

Additionally, Stage07 protected **1,566 physically plausible original US-Ton VPD QC0** time points outside flagged jump endpoints from Stage05's exploratory ERA-RH override; Stage07 preserved the original values at those times.

### Generated candidate directory and provenance

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage07_applied/candidate_20261024T114538Z_6a6b36ba
```

Generated `US-SP1_Stage07_ERA_VPD_repaired_FLUXMET_HH.csv`, `US-Syv_Stage07_ERA_VPD_repaired_FLUXMET_HH.csv`, `US-Ton_Stage07_ERA_VPD_repaired_FLUXMET_HH.csv` (one full native CSV per station), `stage07_applied_changes.csv`, `stage07_unsafe_ERA_target_holds.csv`, `stage07_inherited_754_holds.csv`, `stage07_sha_receipt.json` and an explicit `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker.

**Interpretation:** 376 = exact-time ERA5 VPD replacements; 1,293 = total modified unique rows after combining Stage05 and Stage07. They are different counts. The **754 Stage05 inherited HOLD records** and **12 newly skipped ERA boundary endpoints** are stored separately and can overlap, so `754+12` is a count of ledger entries, **not** a verified distinct timestamp count.

### Scientific and operational boundaries

- This is an **actually written derived data product** rather than inspection-only, but still a **candidate**, not `processed_v5` Post-v5 accepted forcing. The original FLUXNET release contains packaged ERA5-derived calibrated/downscaled `VPD_ERA`, not an independently obtained raw ERA5-Land source.
- The selected rule explicitly permits native QC0 replacement **only** at Stage06 flag endpoints, while protecting the other 1,566 physically credible US-Ton QC0 samples. The 12 invalid replacements were held.
- **0 Post-v5 accepted, 0 DATM jobs, 0 spinups** from this run.
- Next substantive step: advance **seven remaining Batch04 sites** (US-Rpf, US-Seg, US-Ses, US-Slt, US-SRG, US-SRM, US-Uaf) through source QC and isolated candidate creation in a separate stage, rather than re-auditing successful Stage07 work.
