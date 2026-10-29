# Stage65 — US-Whs 2012-05-26: does measured tower TA differ from source ERA TA by ~11.5°C?

## Grounded reason for targeted original observation investigation

Stage64 actually executed on IRIDIS6. The US-Whs one original P2/P3 flag is site-native `201205260600`; `TA_F=29.620°C`, `TA_ERA=18.131°C`, **+11.489°C**. At 05:30 the corresponding difference was +11.236°C and at 06:30 +10.962°C. However the **13 surrounding half-hour TA_F and VPD_F fields all have source QC1**, with no measured QC0 anchors; source RH is missing. This is **not evidence that measured tower TA is 11°C warmer than source ERA**, because `TA_F_QC=1` refers to filled products.

User specifically requested a check of better-quality actual tower temperature measurements surrounding 26 May 2012 and of whether the unusually large TA–ERA TA difference persists in **measured** data.

## Stage65 targeted measurement/QC comparison

Source: original AmeriFlux `AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1.zip`, original Stage45-verified SHA256 `0e25b768c60114aba5bc7600c1d08e4d629e4d147e32c208b7e7f8cca12d3767`. The script locks the actual Stage64 original 13HH CSV/manifest and re-verifies the original ZIP and exact 13 old pairs. It does not replace source data or infer an undocumented clock conversion.

Use source `TA_F_QC == 0` only to designate original AmeriFlux source-reported observation-based TA, distinct from QC1 MDS/gap fill and QC2 source processed ERA. Temperature observations still require instrument-level provenance QC before using them as scientific ground truth.

- Scan the same native 2012 site data ±120 days for the nearest true QC0 records before and after the incident.
- Summarise all matched `TA_F(QC0)−TA_ERA` in windows ±1, ±3, ±7, ±14 and ±30 days, **never mixing QC1 into measured bias estimates**.
- For each of 29 native calendar days ±14 around May 26, report source QC0 measurement count, paired source ERA coverage, median observed − ERA temperature difference, QC1/QC2 counts, and nearest matched original clock `06:00 ±1 hour` QC0 observations.
- Print nearest eight QC0 observations before and after by native time and nearest 16 QC0 records around 06:00 local clock for a fairer same-hour comparison.
- Print nearby day-of-event source records at 05:00–07:30 across May 25–27, keeping QC1 filled temperature clearly distinguished.
- Save CSV reports and manifest under **new** Stage65 report directory, not inside any original, previously approved overlay or model forcing.

[Stage65 Python](../scripts/stage65/65_US_Whs_20120526_QC0_TA_vs_source_ERA_before_after_READONLY.py) source commit `9aaca947101905f9062f9a8a3c82c1859ec2b0d5`, Git blob `3c53fb7a8028c13a51449b61192c0f3f3170e5cf`.

[Stage65 IRIDIS6 launcher](../scripts/stage65/run_stage65_US_Whs_QC0_vs_ERA_iridis6.sh) source commit `cfc78d5236ba8321eec8a8c2567024c0ce722f2c`, Git blob `9c77cd09a0ce4d46973e025e7731f74b3229d00f`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/cfc78d5236ba8321eec8a8c2567024c0ce722f2c/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage65/run_stage65_US_Whs_QC0_vs_ERA_iridis6.sh" -o "$HOME/run_stage65_Whs.sh" && test "$(git hash-object "$HOME/run_stage65_Whs.sh")" = "9c77cd09a0ce4d46973e025e7731f74b3229d00f" && bash "$HOME/run_stage65_Whs.sh"
```

**Status:** GitHub script/launcher SHA verified; actual Stage65 IRIDIS6 source-QC results and syntax/self-test require operator execution. No assumption about measured versus ERA discrepancy until QC0 evidence is printed. This is a scientific source investigation, not authorisation to change the 204 approved candidates, original FLUXMET, DATM, CIME or Slurm jobs.
