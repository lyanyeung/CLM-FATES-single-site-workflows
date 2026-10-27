# US-Me6 — actual Stage13v results and next Stage13w signed batch physical-source diagnosis

## Next Stage13x original measured tower QC0 empirical validation — GitHub ready, cluster not yet run

The 14 original source science failures all result only from **measured site TA minus companion native ERA TA >8°C**, but the original ERA RH remains between 0 and 100%; do not infer that ERA RH is reliable at site TA or silently relax the temperature tolerance. The 4 original 2017 full-run borders are source QC2 on both immediate sides; far measured QC0 observations are **not** direct anchors.

[Stage13x actual original tower QC0-vs-ERA RH source-skill diagnostic](../scripts/stage13/13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py) and [phone one-line launcher](../scripts/stage13/13x_Me6_mobile_QC0_RH_skill_2017_QC2_BATCH_READONLY.sh) SHA-lock the original Stage13r signed source/TIME/ERA and original Stage13s protected research input plus **actual** signed Stage13w 14 event receipt. They look for genuinely measured original source `VPD_F_QC=0` and `TA_F_QC=0` to infer site RH, compare with original same-native companion ERA RH at those native stamps, and calculate median/MAE/P90 original site-minus-ERA RH in ±48h and ±14d windows outside each of six held full original QC1 source runs. A stricter subset retains only original QC0 reference times with |TA_site-TA_ERA|<=8°C. They separately assess **eight immediate original source VPD QC2 neighbors** of four 2017 full-run episodes against retained Stage13s and ERA RH, without treating remote measured QC0 as local bookends. No UTC offset modification, no automatic seasonal QC2 promotion.

**Stage13x --self-test/--check/--run is NOT YET executed on IRIDIS6.** Its `--run` writes only a new independent SHA-sealed report under `reports/stage13x_Me6_QC0_ERA_RH_empirical_skill_and_2017_QC2_edges_*`, never new original/source forcing, DATM, AD400, Slurm or PFT/ZBOT edits. Await true nearby QC0 skills and eight QC2 context before deciding if any operator-scoped **batch** correction is scientifically justified. No authorisation now for other 761 source QC1 neighbours.

## ACTUAL IRIDIS6 Stage13w source-science PASS (operator terminal 2026-10-27 08:57 UTC)

Operator ran pinned Stage13w `--self-test`, `--check`, and `--run` successfully on IRIDIS6. Full original signed Stage13u SHA256 `432f8ce81348be6ab54d8b0791886481c61e71bf2f945e90a33f23dccf1cd9a4`; Stage13v SHA256 `c8b661f779a3aa4ec6aa01352a2926d69d3704d9adb621c01651cfcb104d7f0c` checked. Signed **READONLY** report:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13w_Me6_14_exact_physics_causes_and_2017_QC2_BOUNDARIES_READONLY_20261027T085711Z_f6efb289`

**All 14 original-source physical-HOLD cases have EXACTLY ONE failure clause: site measured TA versus paired original ERA TA exceeds existing strict 8°C threshold.** None of these 14 fail the water RH 0–100%, derived QBOT 0–0.08 or VPD saturation tests by themselves. Exceedance temperature magnitudes by run:
- Stage13r original run14: 2015-11-07 five original native halfhours 03:00, 04:00, 04:30, 05:00, 08:00, |TA_site - TA_ERA| = **8.190–9.168°C**; source ERA RH 60.953–68.701%.
- Run15: 2017-06-29 23:00 to 2017-06-30 02:30 (eight 30min halfhours), TA mismatch **8.291–11.088°C**, ERA RH 26.381–36.377%.
- Run17: 2017-07-03 07:00, mismatch **8.378°C**, ERA RH 82.168%.
All 782 previous original full-run QC1 source records, 768 physical PASS, 11 provisional subgroups and original 5 approved Stage12ac July04 rows unchanged.

**Four 2017 original full QC1 runs ID15–18 have QC2 on both IMMEDIATE original VPD boundaries** (zero direct two-QC0 anchors). Nearest truly measured source QC0 distances in original 30min halfhours (before, after) are: run15 **(17,233)**; run16 **(113,202)**; run17 **(151,57)**; run18 **(296,2)**. These *remote* QC0 cannot be used as direct 30min group bookends. ERA-RH candidate max native VPD jumps and number of >4hPa edges respectively: run15 **5.741840 (2)**, run16 **4.489297 (2)**, run17 **4.190815 (1)**, run18 **6.552221 (4)**. **No approved blanket QC2 bridge; no new forcing and no model jobs.**

**Scientific implication:** the 8°C mismatch is an empirical concern about RH source transferability, not proof tower TA is wrong; do not relax the threshold to 12°C or auto-impute 14 cases just because water thermodynamics are feasible. Next batch should independently measure original tower QC0 VPD-implied RH minus native ERA RH skill on surrounding available directly measured tower QC0 records, and compare QC2 immediate edge records against ERA RH; remote QC0 only source-skill context, not interpolation anchors. User prefers a single justified grouped operator approval after evidence.

## Stage13v actual signed success (user IRIDIS6, 27 Oct 2026 08:35 UTC)

User ran `--self-test`, `--check`, `--run` PASS. New read-only signed science report at

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13v_Me6_14_source_QC1_failures_BATCH_READONLY_20261027T083537Z_7151cdf8`

This report is derived from actual Stage13u native-source science and contains 782 original source VPD QC1 halfhours in six held original full runs; **768** original ERA RH-at-tower-T / QBOT / source-TA physics passed and **14** failed; **11** contiguous provisional internally physically valid subgroups, but only **1** with original measured QC0 at both direct bounds, namely original 2015-Sep26 4HH run12, whose source ERA RH candidate fails native VPD continuity at original QC0 joins by **4.002359 and 4.800355 hPa**. Therefore none is currently eligible for operator-free model science adoption. Five prior Stage12ac user-approved 2017 values remain protected. Original Stage13s 235 user-approved 2015 native source observations/214 VPD numeric values plus 214 QBOT numeric values remain completely unchanged. No Slurm, AD400 or DATM.

Fourteen original halfhours with source ERA/site T/RH/QBOT physics HOLD:

| Stage13r run | Exact original source native times | Count |
|---|---|---:|
| 14 | 2015-11-07 03:00, 04:00, 04:30, 05:00, 08:00 | 5 |
| 15 | 2017-06-29 23:00 through 2017-06-30 02:30, every 30 min | 8 |
| 17 | 2017-07-03 07:00 | 1 |
| **Total** | | **14** |

Stage13v only categorized the fourteen records as source ERA/site water physics HOLD, rather than asserting one exact failing clause (site minus ERA temperature >8°C, RH invalid, VPD above saturation, QBOT invalid, missing source, etc). The next report must establish that distinction with signed native evidence, not infer from a high-level HOLD label.

## New Stage13w source-only work, committed to GitHub

[Stage13w scientific code](../scripts/stage13/13w_Me6_exact_14_failed_ERA_RH_T_QBOT_and_2017_QC2_BATCH_READONLY.py) and [phone single-command launcher](../scripts/stage13/13w_Me6_mobile_14_failure_causes_2017_QC2_READONLY.sh).

- Input is the existing **actually produced** Stage13u `reports/stage13u_Me6_six_held_source_QC1_runs_BATCH_SCIENCE_ONLY_20261027T074748Z_9e23952f` and Stage13v `reports/stage13v_Me6_14_source_QC1_failures_BATCH_READONLY_20261027T083537Z_7151cdf8`. Verify both report receipt schemas, exact immutable SHA256 for all original report output files, exact 782/768/14/11 scope and all fourteen timestamp identities; the Stage13u/v reports already verify parent original site/tower/ERA/Stage13s science provenance.
- Recompute from original retained tower TA_USE and PSRF and same-native companion original ERA TA/VPD: ERA RH; saturation vapor pressure; VPD_USE/QBOT physics, source complete, source site pressure, site-versus-ERA TA within the existing **8°C scientific tolerance**, 0<RH<100%, 0<VPD<es(T), 0<QBOT<0.08. List *all* failing physical conditions for each of the **14** times. Preserve original ERA as reanalysis source, not tower-observed humidity.
- For four original 2017 held runs IDs 15–18, extract the signed source-provenance **QC2 left/right immediate VPD neighbor** and nearest (remote) actually observed original source VPD QC0 distances. Do not treat distant QC0 as immediate bracketing evidence. Show source candidate within/boundary 30min native >4hPa step counts and five earlier operator-approved Stage12ac native rows preserved.
- All remaining **761 original QC1 neighbouring timestamps are unapproved**. The old 2015 Nov original 469 halfhours cannot be accepted just because 464 center records individually have plausible ERA RH; the failed five and full-run valid two QC0 joins are not yet a complete science-safe repair scope. There is NO blanket 761 approval, no relaxation of 4hPa or 8°C constraints, no interpolation or forcing application.
- Modes: `--self-test` synthetic with no source files, `--check` source-read-only, `--run` writes only a new independent SHA-sealed **REPORT** under `reports/stage13w_Me6_14_exact_physics_causes_and_2017_QC2_BOUNDARIES_READONLY_*`, not new forcing. No original site data, surface PFT, ZBOT, case, Post-v5, DATM, AD400, Normal400 or Slurm operations.

**Actual Stage13w cluster execution not yet performed.** Once the output identifies which physical clause failed for each native row, choose scientifically justified bounded repair proposals for **one group-level operator decision** consistent with user's preference for batch approvals, not 14 independent permissions. Other AmeriFlux Batch03 sites are separate workflows.
