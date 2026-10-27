# AmeriFlux Batch03 US-Me6: Stage13x completed; Batch method validation concrete batch candidates

## Actual operator result, 27 October 2026 14:09 UTC

The uploaded terminal log establishes Stage13x self-test, check and report generation PASS on IRIDIS6. The actual report directory is:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13x_Me6_QC0_ERA_RH_empirical_skill_and_2017_QC2_edges_20261027T140953Z_342b79ec`

Stage13s input remains SHA256 `02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565`. Its 235 approved original halfhours and five earlier Stage12ac July2017 halfhours were preserved. Six full original QC1 runs, 782 source halfhours, remain held. Stage13x did not write forcing or submit jobs.

Within 48 hours of each run, directly measured tower QC0 RH versus same-native ERA RH had MAE approximately 7.93–13.59 percentage points where observations were available. Run16 had **zero** such samples within that window. Restricting those samples to site–ERA temperature differences <=8°C reduced the available-sample MAE to approximately 7.93–12.59 percentage points. These are context-dependent sample errors, not an uncertainty interval for the unobserved events. The ±14-day windows provided wider context but do not turn distant QC0 into direct interpolation anchors.

All eight immediate 2017 source boundaries were VPD QC2. Their retained-versus-ERA candidate differences were about 0.62–5.35 hPa. Fourteen original event halfhours still exceeded the strict 8°C site–ERA temperature difference. None of this establishes a valid blanket replacement of the held runs.

## Next runnable work: one six-run candidate comparison

The separately published Stage13Y eleven-subepisode gate is preserved. Batch method validation tests alternative repair methods directly from the already completed Stage13X and its original sources; it does not require an additional Stage13Y cluster run and does not supersede Stage13Y's source warnings.

[Batch method validation script](../scripts/stage13/13_validation_Me6_six_run_repair_candidates.py) creates explicit per-time candidate VPD and QBOT values and one batch decision table. **Batch method validation has not been executed against the actual IRIDIS6 source data at publication.** Local synthetic tests do not establish real event PASS or successful repairs.

| Source run | HH | Candidates | Retained limits |
|---|---:|---|---|
| 12, 26 Sep 2015 05:00–06:30 | 4 | Raw ERA RH; locally adjusted ERA RH; direct measured-QC0 VPD interpolation | Interpolation only within this exact four-HH gap, with measured immediate anchors; empirical pseudo-gap checks |
| 14, 4–14 Nov 2015 | 469 | Raw ERA RH; locally adjusted ERA RH | Five original >8°C source holds remain; long event requires independent source review |
| 15, 28–30 Jun 2017 | 95 | Same two ERA candidates | Eight >8°C holds; QC2 boundaries retained |
| 16, 30 Jun–1 Jul 2017 | 30 | Same two ERA candidates | QC2 boundaries retained; absent 48-hour QC0 context is not an anchor |
| 17, 1–4 Jul 2017 | 137 | Same two ERA candidates | One >8°C hold; five already approved July4 values remain exact |
| 18, 4–5 Jul 2017 | 47 | Same two ERA candidates | QC2 boundaries retained |

There are **13 run/method comparisons and 1,568 candidate-value rows**. This is two methods over the same 782 source times, plus one four-time interpolation candidate; **it is not 1,568 distinct repaired observations**. Candidate tables retain before/after values, measured temperature and pressure, source QC, protected timestamps, local jumps, empirical support, and HOLD reasons.

The local adjustment adds the median measured-minus-ERA RH residual from the ±14-day outside-event QC0 sample. It is evaluated by leaving out each entire native calendar date **and the adjacent date on each side** from training. Each fold needs at least 96 training records on three dates. The declared empirical screen needs at least 96 held-out records across five dates, physically valid RH without clipping, and adjusted MAE and P90 no greater than raw ERA. This is a research screening convention, not a universal accuracy threshold or proof about missing data.

For the four-HH short gap only, validation hides the middle four values in nonoverlapping six-record windows of actual preserved QC0 observations within ±14 days. Candidate gap starts must match the true native start time to within three hours. It needs at least 12 pseudo gaps on five dates, physically valid predictions, MAE and P90 no greater than the matched ERA predictions, and P90 absolute VPD error <=4 hPa. All predictions, including invalid ones, remain failures rather than being dropped to improve the score. Actual event QBOT always uses its retained site temperature and pressure. The source temperature-transfer gate applies to ERA methods; tower-anchor interpolation does not transfer ERA RH and is evaluated by its own source/physics checks.

All methods retain the existing 8°C donor-temperature rule and 4 hPa native VPD continuity rule. No RH clipping, no source time shifts, no QC2 neighbour edits and no long-gap interpolation. Both immediate source bookends must remain preserved measured QC0 for `CANDIDATE_FOR_GROUPED_REVIEW`. Physically/numerically plausible QC2-bounded events still show an explicit HOLD; they do not gain observed anchors through calibration. The baseline raw ERA method remains a reference rather than a new empirically supported repair proposal.

`CANDIDATE_FOR_GROUPED_REVIEW` is a proposed method/scope, not operator approval or forcing admission. If nothing meets the declared screens, every comparison remains HOLD. This intentionally permits an honest empty candidate set.

## Execution and outputs

The phone-compatible launcher is maintained with the experiment repository under `examples/AmeriFlux_Batch03_10/scripts/run_Me6_batch_method_validation.sh`; it pins the science source commit and checks all three downloaded Python source blobs. It runs the source-free self-test and **one** actual `--run`. A separate `--check` mode is available but is not repeated by the launcher because `--run` performs the same input audits.

All new files are report CSV/JSON under `reports/stage13_validation_Me6_six_run_repair_candidates_*`, plus home-directory launcher/log files. No production or research forcing is generated. Stage13s, Stage12ac, raw tower/ERA, other sites, PFT/ZBOT, DATM and Slurm are unchanged. Receipts are SHA256 integrity manifests, not digital signatures or independent scientific validation.

Local validation: syntax, source-free self-test and synthetic regression tests cover the complete 6-run/782-time calculation, 14 unrelaxed temperature holds, eight QC2 boundary positions, protected-value equality, blocked-validation leakage, insufficient samples, invalid saturation, native chronology, and rejection of altered source scope. Actual site results remain pending the next IRIDIS6 execution.
