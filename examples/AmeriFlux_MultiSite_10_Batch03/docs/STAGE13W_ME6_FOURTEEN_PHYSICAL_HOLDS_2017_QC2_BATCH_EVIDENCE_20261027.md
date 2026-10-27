# US-Me6 — actual Stage13v results and next Stage13w signed batch physical-source diagnosis

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
