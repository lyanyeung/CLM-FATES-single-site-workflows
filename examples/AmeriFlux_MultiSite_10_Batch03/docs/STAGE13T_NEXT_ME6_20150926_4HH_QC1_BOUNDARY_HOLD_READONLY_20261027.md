# US-Me6 — Stage13s actual success, Stage13t next READ-ONLY 2015-09-26 four-QC1 original source review

## ACTUAL IRIDIS6 Stage13t result — 2026-10-27 07:12 UTC

Original user log from `login6001`: pinned Git SHA PASS, `--self-test`, `--check` and `--run` PASS; source original Stage13s 280320-row output sealed SHA `02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565`, original tower `721d87464c70ea38c7ab6206deee6953647709072cde33827a825408970971e0`, original ERA `af2be6dce8b9d1310540f29b3a87d57fbac4da7d2f8192434e93217e5079f98f`.

**Measured VPD QC0 (must preserve)** `2015-09-26 04:30 VPD 5.413hPa`, `07:00 VPD 6.468hPa`. Four original source QC1 VPD timestamps are 05:00 5.593 (ERA-RH candidate 1.410641); 05:30 5.593 (ERA 1.476824); 06:00 original 13.124 (Stage13s `VPD_USE=NaN`, ERA 1.567620); 06:30 original 9.829 (ERA 1.667645). Companions' ERA RH 88.16%, 87.53%, 86.90%, 86.53% while original **measured** QC0 anchor RH implied by VPD strongly differs from the ERA estimates. Source paired ERA-RH at site TA yields **two** violating edges `04:30–05:00 4.002359hPa` and `06:30–07:00 4.800355hPa`; candidate interior three edges are 0.066183/0.090796/0.100024 hPa and pass.

One hypothetical **not operator-approved, not independently validated** interpolation between exact measured QC0 5.413 and 6.468 would yield five 30-min edges of **0.211 hPa**, but a smooth interpolation is not proof that the intermediate true humidity was linear. **Do not silently approve a source method or relax the 4hPa gate.** All 4 original source QC1 records remain held; original Stage13s successfully repaired 12 other complete 2015 episodes and remains unchanged.

Signed new Stage13t **read-only scientific report**:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13t_Me6_20150926_four_QC1_original_QC0_ERA_RH_READONLY_20261027T071247Z_a30c3a4e`.

**User strategy update:** prioritise **batch repair and one grouped operator signoff** rather than bringing this one four-HH case for isolated approval. Next analysis should jointly triage **all six remaining originally held Stage13r runs (2015 Sep 4HH, 2015 Nov 469HH and 2017 four runs)**, source-missing/TA-QC, true QC0 anchor proximity and preserved five 2017 Stage12ac updates, and present bounded realistic options; no write or approval of the other 761 original QC1 neighbor records until further explicit signoff.

## Actual Stage13s verified on user IRIDIS6 (2026-10-27, reported successful 06:50 UTC)

Original operator log from `login6001`: **Git source hash, self-test, check and apply all PASS**, new **independent full 280320-row (16 NOLEAP years) research-only US-Me6 selected model forcing candidate**:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage13s_Me6_12x2015_235HH_ERA_RH_operator_approved_20261027T065056Z_6890a105`

The exact 12 approved original 2015 VPD QC1 *full* episodes cover **235 native HH** (17 previously method-approved original centers + 218 newly user-approved QC1 neighbors). Final output comparison from the real cluster: **214 actual VPD_USE changes and 214 actual QBOT changes**, among which **18 previously missing VPD_USE/QBOT original native times were filled**. All 24 original measured QC0 boundary VPD values, original 2017-07-04 five previously operator-approved Stage12ac records and six other held full source runs remain unchanged. No PFT, original tower, model case, Post-v5, DATM, AD400 or Slurm operations. Do **not** claim this source candidate is production-ready.

Signed source SHA from terminal log: original approved Stage12ac site selected `54bccdadde9ff72c8c60a17bd17c28e5695aad0431fdee6dfca18faff4e2f085`, original primary tower `721d87464c70ea38c7ab6206deee6953647709072cde33827a825408970971e0`, original companion ERA `af2be6dce8b9d1310540f29b3a87d57fbac4da7d2f8192434e93217e5079f98f`, original signed Stage13r receipt `498a0de192bf982c5751fa0b9dab2fbb7d1b2fa702a50b61b7de51445af1dbcb`. Full source record length **280,320**, not 315,360 from other sites.

## Next narrow source science issue (operator approval for repair NOT yet granted)

Original Stage13r signed full source run **ID 12**, `2015-09-26 05:00,05:30,06:00,06:30`: exact four original-native `VPD_F_QC=1` humidity points within measured original `VPD_F_QC=0` boundaries at `04:30` and `07:00`. Paired same-native original ERA RH-at-retained tower T/QBOT basic physics had passed for the earlier center, but the *complete 4HH source 30min transition* exceeds the fixed 4hPa source-science threshold: **4.800355 hPa**. Hence original Stage13r held this *entire* source run and excluded it from Stage13s, even though Stage13s repaired 12 other full 2015 groups.

[New Stage13t explicit read-only detailed source science script](../scripts/stage13/13t_Me6_20150926_four_QC1_measured_QC0_ERA_RH_READONLY.py) and [mobile one-click launcher](../scripts/stage13/13t_Me6_mobile_one_click_READONLY.sh):

- SHA-lock original Stage13r historical science code, Stage13q/source manifest through Stage13r verification, last approved Stage12ac source and **actual** successful Stage13s 280320-row candidate receipt/output before any science judgments;
- prove Stage13s has **not changed any 2015-09-26 held original native records** or their ±3h context (allowing numeric CSV reserialization tolerance <=1e-12 and exact source-native time);
- compare native original tower TA_F/VPD_F QC, selected Stage13s VPD/QBOT and original ERA TA_ERA/VPD_ERA-derived source RH across ±3h from the two measured QC0 bookends; show **exactly which of five 30min transitions** from 04:30→05:00 through 06:30→07:00 breaks the fixed 4hPa check;
- show *one hypothetical* straight-line source-measured-QC0-anchored VPD/QBOT curve solely as a diagnostic comparison. It is **not independent evidence** that a straight-line interpolation is correct science and **is not operator-authorized**. No replacement value is adopted by this script.
- Modes `--self-test` without files, `--check` read-only, `--run` **READ-ONLY signed report CSV and JSON under new `reports/stage13t_*`**. Never create or alter any forcing, original FLUXMET/ERA, US-Kon/NR1, Stage13s 2015 corrected candidate, Stage12ac 2017 values, surface/PFT/ZBOT, DATM, AD400, Normal400 or Slurm.

**Status:** GitHub source code/mobile launcher prepared, not yet tested on IRIDIS6. After actual Stage13t check/run readout, decide whether this one 4HH original QC1 run should receive an additional exact-scoped user science approval for an independently evidenced alternative method, or remain HOLD. Other 2015 Nov 469HH and all four 2017 full QC1 runs remain entirely HOLD.
