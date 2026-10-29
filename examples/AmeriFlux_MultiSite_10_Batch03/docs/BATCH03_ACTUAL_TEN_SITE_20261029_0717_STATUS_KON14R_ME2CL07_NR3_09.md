# Batch03 AmeriFlux 10-site checkpoint — actual 2026-10-29 07:17 UK, source-evidence status

Read across **actual user-reported** US-Kon Stage14R output, and **current GitHub** Claude source handbacks for US-NR3 and US-Me2. Do not confuse numerical research-only shadow `NaN=0` with independent source-validation and production DATM/AD400 readiness.

## US-Kon Stage14R ACTUAL

Signed input Stage14Q produced a research-only 280320 native halfhour noleap 2004–2019 site tape with **2** original science held humidity gaps. The user ran Stage14R source `scripts/stage14/14r_US_Kon_final_two_connected_dual_ERA_sensitivity.py`, version `batch03-Kon-14R-last-two-dual-ERA-connected-source-research-v1-20261029`. Result from user log:

- 2011-09-29 18:30: **PASS**, one originally missing VPD/QBOT filled, bounded source 17:00–20:00 VPD QC2 paired-companion ERA RH transferred onto original tower T, plus two original T QC1 repairs at 17:30 and 18:30. Maximum halfhour ΔVPD 3.606020 hPa, ΔRHwater 14.930599pp, ΔQBOT 0.001695 kg/kg, ΔT 1.395°C. Actual original T/VPD QC0 preserved.
- 2011-05-26 11:00: **FAIL/HOLD** after enlarging 18 source intervals from 2011-05-26 02:30 to 11:00; original source companion ERA and ERA5-Land humidity agrees, and all **inside** candidate-source boundaries pass, except the external *02:00→02:30* T step **4.4070687256°C** against a 4°C gate. The other measures at that edge are within limits: ΔVPD 2.011286 hPa, ΔRH 3.02451pp, ΔQBOT 0.00190676 kg/kg. This is *not* a reason to lower temperature thresholds without examining **original 02:00/02:30 TA_F_QC, TA_F and ERA5-Land source/support**; group correctly rejected atomically and the original gap remains.
- Full isolated research-only output saved by operator, not original forcing:
```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/US_Kon_14R_last_two_reanalysis_source_RESEARCH_ONLY_20261029T071709Z_37710989
```
Source parent Stage14Q SHA256 `78379376341115d2523800f1f71ac887e81aa28113701a7fa65a34a49a6ae9a2`. Original tower `f228c7be096f5b79462d5281c80a15a0768c3ef6264853af93753889882777c0`; paired ERA `3aacd53fae73f18e4c7ea305195a246d977969d4548cd0e461aa64bb461c25c9`. ERA5-Land 2011 ZIP verified. Stage14R summary: accepted_research_groups **1**, remaining_HOLD_count **1**, extra finite VPD edits **6**, original QC1 temperature edits **2**; original QC0 unchanged; no Slurm or AD400 approval.

**Decision:** US-Kon **76/77 original missing humidity halfhours rebuilt** in research-only tape, one original scientifically held native timestamp `201105261100` remains. The next minimal action is an **original 02:00/02:30 temperature source/QC diagnostic and locally bounded candidate if justified**, not threshold relaxation. Do not claim all 280320 humidity points complete.

## Claude US-NR3

[US-NR3 Claude handback](US_NR3_CLAUDE_HANDBACK_20261029.md): Stage09 **MAIN** and SENSITIVITY 315360-row NOLEAP research shadows each have **238/238 original humidity gaps filled, NaN 0**; independent verification returned **VERIFY ALL PASS** for signed source/provenance and water/QBOT/ice saturation. Still marked `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP`, and 123/198 T* / ERA interface edges have >3°C T steps, max 12.4°C. Scientific temporal continuity and production signoff remain.

## Claude US-Me2 (likely user's “US-Ne2”)

[US-Me2 Claude CL04–CL07 handoff](US_ME2_CL04_FOUR_EVENT_DECISION_20261029.md) has original UTC−8 and 4 historical humidity gaps. Expanded full-record source scan found 365 QC1/QC2 nonphysical/extremely dry candidates (and 1 original true QC0 held). The latest actually logged **CL07** provided candidate values for all 243 previously unresolved warm-season events: **224 site-calibrated M2, 19 M1** low confidence; other **122** source events EMP_LOYO, including 4 legacy. **No complete selected US-Me2 model shadow / 0-NaN model tape existed as of that handoff.** Open source/site issues: four CL04/07 candidate decisions need integrating to a complete source; 2020 Green Ridge Fire, 2021 salvage logging, post-2022 shorter new tower and representative forcing period, other long outage QC1 rows and unavailable BASE sensor provenance. Thus it is incorrect to say US-Me2 full forcing is completed on the strength of CL07 **candidate ledger alone**. No production approval.

## Current ten-site status at this source snapshot

| Site | Signed research humidity timeline numerical coverage | Production DATM / AD400 approval? |
|---|---|---|
| US-MMS | no NaN research | no |
| US-MOz | no NaN research | no |
| US-Mpj | no NaN research | no |
| US-MtB | 280320 no NaN Claude MTB04 research | no |
| US-NC2 | no NaN research | no |
| US-Me6 | no NaN Claude CL03 research | no |
| US-NR1 | 1999-onward no NaN Claude CL03 research | no |
| US-NR3 | 315360 no NaN Claude NR3 Stage09 MAIN research | no |
| **US-Kon** | **1 protected original humidity NaN** after actual Stage14R | no |
| **US-Me2** | 365 source candidate decisions but NO validated complete selected research tape | no |

**Summary: 8/10 have zero-NaN research shadows; 2/10 do not. 0/10 have an overall Batch03 production-ready AD400 approval established by the cited research evidence.** The count is as of actual records; future Claude work could revise it. Preserve source prefixes and no false claims of on-cluster runs.
