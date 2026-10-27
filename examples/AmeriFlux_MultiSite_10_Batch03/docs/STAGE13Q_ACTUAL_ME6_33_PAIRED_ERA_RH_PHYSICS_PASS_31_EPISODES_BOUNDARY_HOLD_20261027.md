# Stage13q — actual US-Me6 33 original source QC1 humidity points: 33/33 individual PASS, 0/31 boundary PASS

**Actual IRIDIS6 execution, 2026-10-27 00:27 UTC** (login6003): pinned Stage13q one-click script hash PASS, Python `--self-test` PASS, `--check` PASS, `--run` PASS. Stage13q created ONLY a new SHA-signed **read-only original source evidence report**, not any forcing file or model job:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13q_Me6_33_original_ERA_RH_group_source_review_20261027T002737Z_445444f6`

Exact terminal science summary:

```json
{
  "total_33_source_centers": 33,
  "contiguous_30min_original_source_groups": 31,
  "science_source_pass_centers": 33,
  "science_source_hold_centers": 0,
  "entire_bounded_source_groups_pass": 0,
  "groups_held_for_source_provenance_or_unapproved_neighbors": 31,
  "new_forcing_written": false,
  "DATM_ready": false,
  "Slurm_jobs": false
}
```

All 33 center original site `TA_F_QC=0` measured T, `VPD_F_QC=1` MDS/gapfilled humidity, same-native original FLUXNET companion ERA RH, source pressure and recomputed VPD/QBOT thermodynamics **pass**. Nevertheless, **all 31 groups of these 33 original source-native time steps FAIL** the source-native ±30min continuity gate of at most 4 hPa when only those preselected center points are patched and the adjacent old selected source Q1 remains untouched. This is a full group science HOLD, not a pipeline code failure. Example more serious group 2017-07-05 06:30–07:00 has max existing ±30min VPD boundary jump **17.019687 hPa**. Other examples 2015-09-03 05:30 **4.112364 hPa**, 2015-09-05 05:30 **4.128772 hPa**, and Oct21-type source neighbor switches far larger.

**Interpretation:** original QC1 is source MDS/gapfilled VPD, not measured valid QC0; physically sensible ERA RH cannot be inserted into a single QC1 source center while leaving surrounding inconsistent QC1 humidity unchanged. The previously operator-approved source method for these 33 points remains bounded, and does **not** independently permit extending the replacement to their neighbouring originally QC1 source halfhours. As with earlier US-Mpj Stage13m → Stage13n → Stage13o, the next step is a source-pinned full-run QC1/native measured QC0 boundary audit, NOT weakening the 4hPa limit.

**Next code:** Stage13r (read-only) examines full original-source contiguous QC1 runs containing these 33 centers, original true measured QC0 bookends, paired original ERA RH at signed retained site TA and QBOT, the unchanged already-approved Stage12ac five 2017-07-04 records, original Stage13q signed report and all candidate source full segment transitions. It generates a single grouped **operator approval proposal** for any newly implicated neighbouring QC1 time steps, but no new authorisation or forcing. **No Stage13r IRIDIS6 actual execution has yet been received**, and no new Me6 source edits have been applied since Stage12ac. US-NR1 Stage13p success is separate.

## Stage13r committed — next ONE mobile read-only command

GitHub code: [Stage13r full source-original QC1 run and measured QC0 episode survey](../scripts/stage13/13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py); [mobile one-click helper](../scripts/stage13/13r_Me6_mobile_one_click_readonly.sh). Stage13r audits the exact signed Stage13q IRIDIS6 report, original tower+ERA SHA and Stage12ac approved source; finds the **maximal full original VPD QC1 spans** containing those 33 already-reviewed source centers, deduplicates overlapping centers, reports total previously unapproved original QC1 neighbors, verifies original QC0 at both ends, protects five earlier 2017 July04 Stage12ac site-native changes, evaluates paired native source ERA RH/VPD/QBOT at tower T and full native VPD steps. Runs longer than 300 source halfhours are explicitly flagged HOLD rather than silently assumed valid. All extension rows are hypothetical and await a **separate grouped user science approval**.

Run modes: `--self-test` pure synthetic, `--check` no writes, `--run` writes **only** a new SHA sealed original source review to `reports/stage13r_*`; does not create or alter any forcing, original data, model case or Slurm work. **Not yet executed on operator's IRIDIS6.** Contact the user once at group level only after actual Stage13r source audit, never for 33 repeated individual votes.

Do not claim all 33 have been corrected or that any of 31 groups passes. **PFT is already updated separately**, no need to reopen here. Original Stage07, Stage12g/12ac, raw FLUXMET, PFT, DATM, AD400 and Slurm remain unchanged.
