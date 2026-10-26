# 2026-10-26 — Batch03 all ten sites after verified Stage12ah

**Latest operator IRIDIS6 log at 2026-10-26 02:47 UTC:** Stage12ah original script source blob/syntax, self-test, check, and apply **PASS**. New signed Kon research-only successor:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage12ah_USER_APPROVED_Kon_23_T_one_QC0_VPD_20261026T024732Z_8075bed8/`.

Verified 23 operator-approved original Kon source `TA_F_QC=1` T spikes interpolated with immediate `TA_F_QC=0` measured anchors and changed `TA_USE/TBOT`; VPD_USE/QBOT at these 23 old finite positions now held missing until next humidity repair. One individually approved source VPD QC0 physical outlier US-Kon 2008-09-26 05:30 was changed to VPD 2.801 hPa + QBOT 0.01003 kg/kg (site source T 16.141C, PSRF 96910Pa). Original Kon Stage12g 367 missing VPD -> signed Stage12ah **389 missing** (= 367 + 23 - 1); original source unchanged. Other 34 held center VPD unchanged. This is **operator-approved science source repair, not model-ready DATM forcing**.

## Exact ten-site selected candidate snapshot (nine signed numerical sources + Me2 clock hold)

| Site | Latest source stage | VPD/QBOT missing in selected source-native NOLEAP candidate | Outstanding science |
|---|---|---:|---|
| US-NR3 | Stage12g | 238 | 6 stage12g missing-source-year items, 172 original physics holds, other history sources; validate finite source RH and QBOT |
| US-Kon | Stage12ah approved-only successor | **389** | source-matched ERA humidity for 34 held QC1/QC2 VPD centers + 23 newly held temp-edit neighbor VPD, 10 other source QC1 T review, original prior holds/other sources |
| US-NR1 | Stage12af approved-T successor | **240** | 6 at 2022-09-10 span: three old missing plus three newly held QC1 VPD at corrected T; proposed native paired ERA RH ~72% needs user signoff; other holds, verified years |
| US-MMS | Stage12g | **16** | 15 missing verified gridded source-year items + one other source science hold; preserve source native hourly frequency |
| US-MtB | Stage12g | **2840** | 1031 grid/tower T >5C, 4 grid-water-vs-ice RH conditional holds, 1325 missing verified source-year items within stage12g 2810 ledger; Stage12j cross-validation **all four candidate transfer methods failed** predeclared multi-year science gate; cannot auto-approve humidity reconstructions |
| US-Me6 | Stage12ac approved derivative | **65** | 33 stage12g VPD jump events have operator-approved approach but not yet applied; 29 tower-grid >5C and 2 missing verified source-year, plus other legacy holds. Stage12ac original 5 HH 2017-07-04 direct paired ERA RH have already been applied only in this derivative |
| US-Me2 | Stage11a metadata | **Not quantified by six-site Stage12g NOLEAP inventory** | 4 original release-native clock metadata holds; missing BIF FULLSET release, disturbance/PFT history (2020 fire + post-fire dynamics); no verified science full shadow |
| US-MOz | Stage11h signed numerical research shadow | **to verify by Stage12ai ten-site current source scan** | complete numeric source only, not Post-v5 approved; surface/PFT + QC release gate |
| US-Mpj | Stage11h signed numerical research shadow | **to verify by Stage12ai** | numeric source, earlier isolated actual humidity changes; surface mixed PFT / QC release |
| US-NC2 | Stage11q signed 73-event humidity research shadow | **to verify by Stage12ai** | 13 immediately touched boundaries passed in Stage11q, separate other historic boundary and station native UTC offset hypotheses need source/science review before production |

**Six selected Stage12g/12ac/12af/12ah site-only humidity holes subtotal: 3788 half-hours** (238+389+240+16+2840+65). This is not total ten-site missing; do not count the 4 Me2 release clock hold events as humidity NaN and do not add prior historical hold populations as if disjoint. One historical NR1 other-field missing row was observed and requires inventory on latest selected source. All ten remain `Post-v5=0 DATM-ready=0 Spinup=0`.

Previous Stage12g source-year rejections: 1,476 missing gridded source, 1,119 grid vs measured tower T difference >5C; these were source-ledger categories **before** operator temperature/HUM science repair, not exact current 3788 repartition. The original 233 physics HOLDs remain a separate protected population, some possibly overlapping other historical gaps; do not double count them with 3,788. Stage12j US-MtB measured QC0 multi-year validation rejects direct all-year grid humidity transfer; cannot merely relax limit.

New source-inventory workflow: [Stage12ai ten site current source states, SHA and finite-input census](../scripts/stage12/12ai_ten_site_latest_selected_successors_STATUS_READONLY.py), pinned commit `eb8c84a58e6eb58857dc32fb60eb9b9f86efc324`, Git blob `f846d335fd58682a047708fdeb977fa56173d38a`. **GitHub committed but not yet run on IRIDIS**; --check read only, --run isolated report only.

## Immediately recommended next moves

1. US-NR1: user already approved 3 temperatures; request **one scoped signoff** for native paired original ERA RH at exact six source HH 202209100600–202209100830, prior to true humidity application. Valid candidate VPD values ~1.811838,1.873343,1.936537,1.912989,1.890739,1.853710 hPa and candidate QBOT available in signed Stage12af 6-row original source ledger.
2. US-Kon: prepared Stage12ah 23 source-T and 1 QC0 VPD approved application; **next Stage12aj** should generate event-episode source-native paired ERA-RH, VPD/QBOT, QC1/QC2 neighbor harmonization candidates for 34 VPD centers and the 23 newly held neighbors; no silent override measured QC0 source VPD, no blanket effect on 10 other QC1 TA records.
3. US-Me6: 33 previously approved source-method events should be applied with same native paired ERA source only after exact source/neighbor/QBOT QC rather than on unapproved ERA5-Land native UTC; preserve existing approved 5 HH Stage12ac overlay.
4. US-MtB: prioritize source-year evidence for 1325 plus evaluate elevation/temperature discrepancy 1031 with measured-QC0 analog validation; all four original Stage12j methodologies failed (do not mark suitable). Check FATES version water/ice humidity handling for four conditionally approved events, before releasing.
5. US-NR3 238 and US-MMS 16: pursue earlier original physics holds and missing source-year products; get down to 0 humidity holes without arbitrary source fill.
6. US-Me2 native FULLSET clock and 2020 fire/ENF land cover and US-MOz/US-Mpj/US-NC2 production QA/PFT and time offsets must be resolved before running models.

**None of these stage milestones authorizes Post-v5, DATM, model spinup.**
