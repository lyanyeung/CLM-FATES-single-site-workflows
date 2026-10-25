# Stage12ac — explicit operator approval for direct five-half-hour native ERA-RH replacement

**Explicit user decision on 2026-10-25:** For **US-Me6 original native 2017-07-04 06:00–08:00 INCLUSIVE**, apply original same-native paired ERA RH (derived from `TA_ERA/VPD_ERA`) at the unchanged original EC tower `TA_F` and existing Stage12g `PSRF`, replacing **both VPD_USE and corresponding QBOT** at exactly **five** original half-hour timestamps. No more alternate candidate science experiments are requested for these five records.

## Explicit exact authorized values

| Original native key | Timestamp | User-approved ERA-RH VPD, hPa (six-digit display, recompute full precision) | Original Stage12g VPD | Treatment |
| --- | --- | ---: | ---: | --- |
| 201707040600 | 06:00 | 3.205763 | 3.205763 | Keep same ERA-RH-derived value; recompute moisture QBOT closure |
| 201707040630 | 06:30 | 3.974495 | 3.974495 | Keep same ERA-RH-derived value; recompute moisture QBOT closure |
| 201707040700 | 07:00 | 5.154795 | missing | Replace this particular gap and release its existing hold in the separate user-approved derivative |
| 201707040730 | 07:30 | 9.345609 | missing | Replace this particular gap and release its existing hold in the separate user-approved derivative |
| 201707040800 | 08:00 | 12.292544 | 21.391000 (original MDS QC1) | Replace this one existing source gapfill in the separate user-approved derivative |
| 201707040830 | 08:30, OUTSIDE approved interval | unchanged: 13.204000 | 13.204000 | DO NOT EDIT |

The **07:00→07:30** adjacent 30min candidate VPD jump is **4.190815 hPa**, exceeding the earlier 4hPa automated science screening guard by 0.190815 hPa. **The operator explicitly authorizes exactly this one local exception** for the final selected source, not a global guard relaxation or a mathematical assertion that such a change is impossible. The 08:00→08:30 transition becomes approximately 0.911456 hPa with unchanged 08:30 Stage12g.

The source-verified original tower `TA_F_QC=0`; VPD `VPD_F_QC=1` and its `VPD_F_MDS` for the five selected rows. Original source's implied RH was negative in four of these five and 2.35% at 08:00. The original native ERA-RH candidate is not a direct measured humidity observation but is the specifically approved replacement under operator judgment.

## Scope and execution

The pinned source script is [12ac_apply_USER_APPROVED_Me6_20170704_0600_0800_ERA_RH.py](../scripts/stage12/12ac_apply_USER_APPROVED_Me6_20170704_0600_0800_ERA_RH.py), Git commit `5e1cf77238a3cbc1a21622930f2eb13f7a9ff8c1`, current Git blob `86251d3889fac98ec74a64d8ec31473e55e6feba`.

`--self-test` verifies the five original native keys, humidity equations and single exception without writing files. `--check` verifies Stage12aa original latest 20261025T231228Z and Stage12g SHA sealed source, computes all five VPD/QBOT and exact native boundaries in memory and guarantees no changes off-target; **zero files written**. `--apply` creates an **independent user-approved corrected full US-Me6 NOLEAP derivative**, five-row before/after receipt, all boundary diagnostics and SHA manifest, stored under a new `science_trials/stage12ac_USER_APPROVED_...` folder. It does NOT overwrite original FLUXMET, the original Stage12g, any other Batch03 site or preexisting hold ledgers. The original 86 science-event and 233 old physics hold ledgers are kept as immutable historical records; two 07:00/07:30 records change only in the separately approved derivative. Other holds must remain.

**This is a substantive operator-approved repair**, not merely a hypothetical sensitivity experiment. It is **NOT** a global declaration that the entire six-site Batch03 forcing is DATM or Post-v5 ready: earlier unrelated incomplete rows, other sites, source clock hypotheses and separate approval gates still need their own established procedures. No Slurm/CIME/DATM/PFT/spinup launched. **As of this document, Stage12ac has been committed to GitHub but not executed on IRIDIS6**; no repaired output folder is claimed to exist yet.
