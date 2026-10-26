# US-Mpj Stage13m actual IRIDIS6 outcome: 0/3 source-neighbor continuity; Stage13n next (2026-10-26)

## Actual operator result, not a hypothetical approval

User terminal transcript (login6003, conda `clm_fates_env`) verifies Stage13m source blob `2eae8663e64739db78ce9dd305ae3aa4b840b06d`, decision blobs `4437edb2d28e20bce428ce159c8746cbf147b583` (Stage13m) / `3461d9590877578cc18f8519d2c7c7e46db6c156` (Stage13d). AST and self-test PASS; `--check` PASS as *source auditing*, **all three operator-conditional scientific adoption gates FAIL**. The subsequent `--apply` exited `STAGE13M SCIENCE HOLD: all three fail source science; no independent forcing written`. Thus **0/3 approved source changes adopted; zero new candidate forcing produced**. This is **not** a broken Python script.

| Source native center | Original `VPD_F` / already existing Stage07 `VPD_USE` hPa | Original VPD source QC | Paired ERA RH / Stage07 RH (%) | Stage07 site humidity and QBOT physics | Immediate earlier selected VPD hPa (QC) | Immediate later selected VPD hPa (QC) | left / right ΔVPD hPa | Science |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014-10-11 02:30 | 8.245 / 1.032049 | 1 | 84.364955 / 84.364955 | PASS | 8.263 (QC1) | 8.227 (QC1) | **7.230951 / 7.194951** | HOLD both sides |
| 2014-10-11 04:30 | 8.170 / 1.163165 | 1 | 85.578683 / 85.578683 | PASS | 8.189 (QC1) | 8.149 (QC1) | **7.025835 / 6.985835** | HOLD both sides |
| 2014-10-21 08:30 | 11.018 / 2.103106 | 1 | 81.078718 / 81.078718 | PASS | 9.382 (QC1) | 1.462 (QC0) | **7.278894 / 0.641106** | HOLD earlier side |

Stage13m output confirms exact `original_Stage07_SHA256=c227f65b800baca3160efe40442fee91ee83c5f04308a0453e0c22bd05d0f592`, original FLUXMET SHA `11f4383dd6deebec8d8ec4f8d82ea00b94e2d4100144811f335f395925451e75` and companion ERA SHA `fb9dc6954b585c125669fab10af1f6d1ca22f2ee84ef18b59f55c9d2449b7f2e`. Original 2018 Feb02 17:30 and 19:00 VPD are **11.261** and **9.178 hPa**, source VPD QC2, preserved unchanged; their source-relative RH 0.668699% and 0.439167% is low but positive, not alone an approval for replacement. Previous operator-approved US-Mpj 2020 Feb11 06:30 tower TA short-gap interpolation `1.1795°C` preserved. Original 315,360-row 2008–2025 NOLEAP site input identity/source receipts preserved.

**Interpretation:** two isolated 2014 Oct11 target VPD corrections appear thermodynamically sound but are bounded by original `VPD_F_QC=1` neighbor humidity values, a possible *multi-record source QC1 MDS humidity anomaly*. Do not call these neighboring QC1 records measured true VPD. Third Oct21 target borders QC1 before and measured QC0 after, suggesting a bounded QC1-to-QC0 event. A 4hPa adjacent-transition guard cannot be relaxed just because a center is plausible. The operator authorized only three exact timestamps, and the original condition explicitly says failed events HOLD. **No extension to neighbors, no implicit reanalysis overwrite or model submission**.

## Stage13n: next combined read-only original QC1 episode review

GitHub added [Stage13n source-pinned event-context script](../scripts/stage13/13n_Mpj_2014_three_VPD_QC1_original_ERA_episode_context_READONLY.py). It SHA-locks the previously successful Stage13m helper, re-verifies the original Stage07 / tower / companion ERA / 2020 TA / two 2018 preserve decisions, then provides for **all three** source-native 2014 centers:

- each original ±6-hour 25-halfhour `TA_F_QC, VPD_F_QC, TA_F, VPD_F, ERA_T, ERA_VPD, source implied RH, selected Stage07 VPD, QBOT` and physically recomputed **hypothetical** source ERA-RH-at-tower-T VPD/QBOT;
- original maximal consecutive QC1 humidity sequence around each center, nearest actually measured original VPD QC0 anchor and joint TA/VPD QC0 anchors;
- strictly bounded ±6-hour exploratory, **not-authorized** search for minimal additional original QC1 slots that would make the whole ERA-RH event smooth (<=4hPa for every edge, original source temperature/ERA mismatch <=8°C and valid water RH/QBOT), with all outer original source values preserved; if none, reports HOLD;
- 75 context rows, 3 independent event assessments, a SHA-sealed report; **no forcing writes, no authority to change neighboring QC1 records**.

`--self-test`: no files. `--check`: reads original sources and prints 3x ±3-hour abbreviated native context, outputs *only to terminal*. `--run`: same, writes one isolated SHA-receipted research report to `reports/stage13n_Mpj_original_QC1_ERA_RH_episode_READONLY_*`. **Not yet executed/verified on IRIDIS6** at commit time. The prior Stage13m false claim of repairing three additional VPD cells must not be repeated: the exact candidate values already exist in original Stage07, though their operator acceptance remains held due to source neighbor inconsistency.

When Stage13n is returned, make ONE operator group decision on whether the specifically evidenced *additional* source QC1 neighbors can be repaired consistently, or remain held for independent source validation. Avoid three separate new approvals. US-NR1 six RH science candidate approval remains the next separate manual site after this one.
