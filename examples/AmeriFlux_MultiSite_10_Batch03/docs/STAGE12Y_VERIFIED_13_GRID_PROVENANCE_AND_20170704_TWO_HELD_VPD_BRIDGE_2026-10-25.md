# Stage12y VERIFIED: 13 historical gridded ERA5-Land provenance records and impossible native two-gap VPD bridge

**Operator result, IRIDIS6, 2026-10-25 19:44 UTC.** Stage12y v2 pinned source SHA/syntax, `--self-test`, `--check`, `--run` ALL PASS. SHA-sealed source-only report:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12y_13_G_grid_provenance_and_Me6_20170704_bridge_20261025T194355Z_461ff1e4/`

Exactly **13 previously finite Stage12g VPD candidate records** for US-Me6 reconcile with original SHA-signed ERA5-Land gridded `new_ERA5Land_year_source_RH_repair_candidates.csv`, not a new Stage12w original native ERA companion RH product. Their source-native-to-UTC offset remains only an **unapproved UTC−8 hypothesis** (`UTC_clock_approved=False` for 13/13). The gridded and paired-native-companion values often differ substantially; different source methodologies should not overwrite one another. No model approval from numerical match to source ledger.

## 2017-07-04 native four-point bridge — immutable original Stage12g and hypothetical new Stage12w candidate

| Original native HH | Original `VPD_F_QC` | Stage12g retained VPD, hPa | Stage12w hypothetical native companion ERA-RH VPD, hPa | Historical G HOLD |
| --- | ---: | ---: | ---: | --- |
| 06:30 | 1 | **3.974495** | 3.974495 | no |
| 07:00 | 1 | **missing** | **5.154795** | HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA |
| 07:30 | 1 | **missing** | **9.345609** | HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA |
| 08:00 | **1** | **21.391000** | unavailable in the Stage12w 355-source-invalid population | no |

All four original VPDs above were QC1 source values: **the right-hand 08:00 retained Stage12g finite value has source QC1, not directly measured QC0**. Physical feasibility of the 08:00 MDS source reading and its provenance/temporal representativeness need independent testing; this does *not* authorise discarding or altering it, and its existing adjacent-edge guard still applies.

Three **actual adjacent half-hour steps** for the combined purely hypothetical four-point sequence:
1. 06:30→07:00 `|ΔVPD|=1.180300 hPa` (within 4 hPa).
2. 07:00→07:30 `|ΔVPD|=4.190815 hPa` (**over** 4 hPa).
3. 07:30→08:00 `|ΔVPD|=12.045391 hPa` (**over** 4 hPa).

The earlier large 07:00-to-08:00 change spans **one hour**, not a single half-hour step, and must not be misidentified as an immediate neighbor jump. Stage12y explicitly checked the intermediate 07:30 and found the adjacent threshold violated twice. Hence neither 07:00 nor 07:30 may be inserted into Stage12g under the original 4 hPa rule. Valid source water RH, ice phase and QBOT closure for the two candidates do not override this boundary condition.

## Next source audit

Stage12z should inspect 08:00's original MDS VPD, QC, source measured `TA_F_QC`, `TA_F_MDS` and source companion `TA_ERA/VPD_ERA` over an original-native 06:00–09:00 window, compare the **07:30→08:00** transition to same-native ERA humidity and ±24h reliable original QC0 source anchors, and independently cross-check the original Stage12g right-hand VPD/QBOT physical closure. It must not assume that a plausible QC1 is an independent tower VPD observation. Check whether Stage12g 08:00 was inherited from C/D/E, not gridded newly in G. Preserve all old 86 source-held and 233 prior physics holds, source clocks, 5°C tower-ERA T mismatch, 4hPa half-hour rule, and Post-v5/DATM/spinup HOLD. Any output source-only and separately SHA sealed, no repair.
