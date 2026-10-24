# AmeriFlux Batch 04 — Stage00 upload integrity ledger

**Date recorded:** 2026-10-24.
**Evidence source:** operator-supplied complete WSL Stage00 console log (`FOUND` 10/10, each `VERIFIED`, final `UPLOAD VERIFIED: 10/10`). The source and destination hashes were compared by the published Stage00 upload script; the assistant has not independently logged into IRIDIS6.
**State:** ORIGINAL PACKAGE TRANSFER PASSED; STAGE01 NOT EXECUTED IN THIS RECORD.

Source: `D:\Fluxes_Tower_Experiment\Ameriflux` via WSL `/mnt/d/Fluxes_Tower_Experiment/Ameriflux`.
Destination root: `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<site>/forcing/packages/`.

| Site | Exact ZIP filename | Bytes | SHA256 (local = IRIDIS) |
| --- | --- | ---: | --- |
| US-Rpf | `AMF_US-Rpf_FLUXNET_2008-2024_v1.3_r1.zip` | 175147801 | `99b550855077b03d8bfdd79364648348e93a3993695c3551814d9f5bf29dca5a` |
| US-Seg | `AMF_US-Seg_FLUXNET_2007-2025_v1.3_r1.zip` | 195115891 | `4fbe84a950c7b411866e6c4a4e08bb30aeafdcdd15d5644ade112aca505b6904` |
| US-Ses | `AMF_US-Ses_FLUXNET_2007-2025_v1.3_r1.zip` | 187868399 | `b03cd379370face906d6f6d5813981719fee32a587e83ba28b6333d8146ad5dd` |
| US-Slt | `AMF_US-Slt_FLUXNET_2005-2022_v1.3_r1.zip` | 173357986 | `5d89e49947b3e4f7cf8357f345bfe02ce5c90bccb58f786b561a88ec8539e707` |
| US-SP1 | `AMF_US-SP1_FLUXNET_2000-2020_v1.3_r1.zip` | 190153345 | `18ed3072e108033f55b3a1f966aa44a5f3e6cb5a816a35f203d4421e89a5d0bb` |
| US-SRG | `AMF_US-SRG_FLUXNET_2008-2025_v1.3_r1.zip` | 200899926 | `befe85db803555060d8c84ea2ccde8c97956d28d987f64fc3d8f36d25f4d4751` |
| US-SRM | `AMF_US-SRM_FLUXNET_2004-2025_v1.3_r1.zip` | 250527863 | `ed96659970398064b7e875aea47aa57f35bb5617defce3fb5fc80be29499f654` |
| US-Syv | `AMF_US-Syv_FLUXNET_2001-2025_v1.3_r1.zip` | 151088329 | `40a7952c7400364e169725ca98445e4005c3a733701874e39f3ce5a82ffe81d4` |
| US-Ton | `AMF_US-Ton_FLUXNET_2001-2025_v1.3_r1.zip` | 249129100 | `b1bc6d7c5daecb193db7ab818e65c7672ef08f3b36c594c807e75cb7c4fb59d6` |
| US-Uaf | `AMF_US-Uaf_FLUXNET_2003-2025_v1.3_r1.zip` | 143198514 | `a80307ba2946df87f704ecf861942b2495d946874c26260a729df468d82c791e` |

**Aggregate original archive size:** 1,916,487,154 bytes (10 packages).

## Explicit completion evidence

```text
LOCAL PREFLIGHT: 10/10. ZIPs take priority over same-named extracted folders.
IRIDIS hostname: login6001
UPLOAD VERIFIED: 10/10 (AmeriFlux Batch 04). Originals retained. No extraction or model jobs started.
```

Every site in the supplied console log contains `VERIFIED: <site> SHA256=<digest>` after `rsync` and a remote checksum comparison. Files were copied without modification. Actual operational log remains outside this GitHub repository.

**Next gate:** run the published `scripts/stage01/01_extract_ameriflux_batch04.py` on IRIDIS6, check scratch bytes/inodes first, then inspect per-site BIF, FLUXMET HH/HR and other release data structure. Do not infer actual year coverage, trust QC science, modify forcing or start model jobs from Stage00 alone.
