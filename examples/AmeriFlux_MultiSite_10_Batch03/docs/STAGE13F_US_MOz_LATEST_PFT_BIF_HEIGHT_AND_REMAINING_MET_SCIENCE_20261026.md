# US-MOz Batch03 final remaining science scope — 26 October 2026

> **VERIFIED 2026-10-26 18:08 UTC — Stage13g succeeded on IRIDIS6.** The operator's exact 5 source-native half-hour / 9 TA+VPD changes were successfully applied to one isolated **315,360-row** research forcing shadow, with 5 associated TBOT recalculations and 5 QBOT recalculations. Original tower SHA \`6e823ef0aa59be7c47f4e244c72fea8d9f9e5cd6c8e49715f1931e1e25c832a9\`; original standalone ERA companion SHA \`77107f67fc28cb051ab44abfbdf5527f55c28510342bbaeb2610d32ee7b4de7c\`; original Stage07 selected SHA \`4aac66f9e62ca4f0d2b2907542aecae577b9fb250c3e586b6ec1d899eee593e8\`. The original 6 operator-approved Stage07 changes remain intact. **Actual resulting shadow:** \`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage13g_US_MOz_approved_native_T_VPD_20261026T180756Z_f75518a5\`. **NEXT science gate is only the original 2005-01-06 QC1 multi-hour tower vs companion ERA warm bias**, plus source-specified ZBOT/PFT implementation; do not continue to present the three resolved 2014/2016 QC0 candidates as unapproved. The new [Stage13h independent source/ERA episode preflight](../scripts/stage13/13h_MOz_2005_QC1_full_episode_provenance_and_paired_ERA_preview_READONLY.py) will locate the *actual* full contiguous QC1 warm-bias source episode and show a purely numeric ERA T+VPD/QBOT replacement **preview** with the source immutably preserved. \`Postv5_approved=False\`, \`DATM_ready=False\`, \`spinup_authorized=False\`; do not submit Slurm.

## Scope and approved records

**All 6 of 6 original Stage07 US-MOz meteorological edits are already explicitly operator approved.** The scope is pinned in:

- [Stage13D: exact one US-MOz source-QC0 temperature approval](../decisions/STAGE13D_OPERATOR_APPROVED_SIX_QC0_TOWER_TA_INTERPOLATIONS_20261026.json).
- [Stage13E: five additional US-MOz TA/VPD approvals](../decisions/STAGE13E_OPERATOR_APPROVED_FIVE_ADDITIONAL_US_MOz_TA_VPD_FIXES_20261026.json).
- Stage13E audited output at `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13e_MOz_six_approved_09T_recheck_20261026T174412Z_3e98ca6c`.

These approvals **do not cover previously unmodified source records**.

## New operator-reviewed meteorology — four groups

Stage13E showed a multi-hour tower-vs-ERA source discrepancy (separate from three flagged isolated centers):

| Scope | Current tower TA and QC | Paired original ERA5 TA | Current decision |
| --- | --- | --- | --- |
| 2005-01-06 05:00–09:00 (9 half-hours) | +4.620 to +8.024 °C, tower `TA_F_QC=1` | −6.342 to −7.096 °C | **HOLD.** One multi-hour source-quality/clock/MDS episode. It MUST NOT be "fixed" by a single-point interpolation. At 09:30 tower TA switches to −7.189 °C, `QC=2`, exactly matching companion ERA5 |
| 2014-04-02 10:00 | +18.110 °C, `QC=0` | +7.879 °C | **HOLD**, Stage13E screened isolated temperature candidate |
| 2016-04-11 13:00 | +23.671 °C, `QC=0` | +12.214 °C | **HOLD**, Stage13E screened isolated temperature candidate |
| 2016-04-14 06:30 | +17.543 °C, `QC=0` | +6.433 °C | **HOLD**, Stage13E screened isolated temperature candidate |

The three screened QC0 centers have **not** been interpolated or approved. [Stage13f three-center independent read-only 2-hour neighborhood extraction](../scripts/stage13/13f_three_US_MOz_QC0_spike_neighbors_READONLY.py) reads the original Stage07 SHA-verified tower and standalone ERA source and prints the preceding/following tower and ERA conditions; only after that can the operator decide.

**Important:** In 2004, 10,960/17,520 tower-vs-companion ERA air-temperature half-hours are numerically *identical* (62.56%). Treat the "ERA" field in these periods as potentially non-independent, NOT as independent independent evidence of source errors. Stage13E is SHA verified but did not replace any 2005 05:00–09:00 temperatures.

## Confirmed current GitHub PFT recommendations (no old surface veto)

The new curated cross-batch 50-site PFT catalog is **present** and explicitly documents all three Batch03 sites:
`examples/Ameriflux_Site/Ameriflux_PFT/RECOMMENDED_50_SITE_CLM_FATES_INPUT_PFT_20261026.csv`
and
`examples/Ameriflux_Site/Ameriflux_PFT/PFT_INPUT_VALIDATION_20261026.csv`.

- **US-MOz**: proposed model natural-landunit FATES PFT 2 ENF 10% + PFT 6 DBF 90%, host bare 0%, `DEFAULT14`. Primary PFT validation: `round_trip=PASS`, `natural_area_sum=100`.
- **US-Mpj**: ENF 60%, C4 20%, bare 20%; validated recommended model hypothesis.
- **US-NC2**: ENF 90% + DBF 10%; validated recommended model hypothesis.

Do **not** incorrectly cite Stage04a year-2000 gridded PFT as the operator's most recent proposed *model* biogeography. The latest 50-site prescriptions resolve **which PFT inputs to test**; however the same curated CSV explicitly states `active_case_parameter_verified=NO`, `case_surface_or_job_modified=NO`: the measured tower footprint percentages were not independently established. This is an **implementation/preflight verification**, not a request to re-research the station PFTs.

## User-uploaded original US-MOz BIF Excel (reviewed, not uploaded to GitHub)

`AMF_US-MOz_BIF_20230331.xlsx`, `AMF-BIF` sheet, columns SITE_ID/GROUP_ID/VARIABLE_GROUP/VARIABLE/DATAVALUE:

- Row 117: `US-MOz | 24325 | GRP_HEIGHTC | HEIGHTC | 24.2`.
- Row 118: `HEIGHTC_DATE = 20070407`.
- Row 119: `IGBP = DBF`.
- Row 112: `FLUX_MEASUREMENTS_METHOD = Eddy Covariance`, followed by `FLUX_MEASUREMENTS_VARIABLE = CO2`.
- The 439-row Excel does **not** include a per-`TA_F` or `WS_F` sensor height, instrument `ZBOT`, or variable-specific meteorological height history. `HEIGHTC=24.2 m` is CANOPY HEIGHT, not input wind/temperature measurement height.
- Independent Missouri Ozark literature `Gu et al. (2016), https://doi.org/10.1002/2015JG003302` documents a 32 m flux tower; `Yang et al. (2007), https://doi.org/10.1029/2006JD008243` describes multi-level air temperature/RH measurement. **A 32 m tower structure does not alone establish the actual vertical reference of the FLUXNET TA_F/WIND forcing stream.** `ZBOT` needs a variable-level sensor metadata source or an explicitly documented model hypothesis.

Do **not** ask the user to resend this BIF workbook, and do not re-open PFT research as if no recommended catalog existed.

## Stage13f verified science recommendations after operator's 17:53 UTC run (NOT APPROVAL)

Original source SHA, Stage13e receipt, 3-source-center identities and `--check/--run` passed. Sealed original report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13f_MOz_three_extra_QC0_tower_ERA_neighbors_20261026T175310Z_f93e321f`.

All three additional source T flags are `QC0` and were **unchanged** in the original Stage07 candidate. The following are proposed values only, **not operator-approved** and not written into any model file.

| Time | Original T | ERA T | Tower TA neighbors −30/+30 | Tentative T interpolation | Original VPD | Tower VPD neighbors −30/+30 | Tentative VPD interpolation | Decision |
|---|---:|---:|---|---:|---:|---|---:|---|
| 2014-04-02 10:00 | 18.110 | 7.879 | 8.896 / 8.647 | 8.7715 | 0.475 | 3.940 / 0.427 | 2.1835 | **HOLD** entire early-morning TA/VPD cluster; 08:30 T 13.310, 09:00 T 14.457, and abrupt 09:30 VPD changes need review; do not approve one isolated value |
| 2016-04-11 13:00 | 23.671 | 12.214 | 12.059 / 16.076 | 14.0675 | 17.735 | 8.303 / 11.354 | 9.8285 | **Recommend approve BOTH TA and VPD two-sided tower interpolation**, not T alone |
| 2016-04-14 06:30 | 17.543 | 6.433 | 7.756 / 10.314 | 9.0350 | 7.288 | 3.622 / 4.812 | 4.2170 | **Recommend approve BOTH TA and VPD** after operator decision; retains original 07:00+ course |

At 2016-04-11 13:00, using interpolated T 14.0675°C but retaining original VPD 17.735 hPa would imply liquid-water RH ~**−10.54%** (because saturation VPD would be only 16.044 hPa), demonstrably invalid. Using interpolated VPD 9.8285 hPa gives RH ~**38.74%**, physically valid. At 2016-04-14 06:30 the paired-interpolation RH is ~**63.33%** (both values preliminary, not forcing changes). Conversely, at 2014-04-02, the abrupt adjacent VPD change 3.940 to 0.427 hPa makes the simple 2.1835 hPa interpolation unverified and the 08:30/09:00 temperature values are also suspect.

**Operator decision remains pending on the 2016 two paired T+VPD replacements, pending for the wider 2014 event, and pending for the 2005-01-06 05:00–09:00 MDS/source mismatch.** Neither the original T/QC0, selected Stage07 candidates, PFT, or CIME/Slurm was edited.

## 2026-10-26 Stage13G operator decision — 5 new native timestamps / 9 variable values

**The operator explicitly approved implementing the prior two 2016 paired T+VPD repairs and expanded the 2014-04-02 event to interpolate the original 08:30 and 09:00 tower temperatures as well.** The scoped scientific implementation also interpolates the coincident 08:30/09:00 humidity spikes, while **retaining original 10:00 VPD=0.475 hPa** because the 10:30 VPD is similarly low (0.427 hPa). The signed decision and script are:

- [Stage13G scoped five-time, nine-field operator decision](../decisions/STAGE13G_OPERATOR_APPROVED_MOz_FIVE_TIMESTAMPS_NINE_TA_VPD_CHANGES_20261026.json)
- [Stage13G isolated versioned research shadow generator](../scripts/stage13/13g_apply_user_approved_US_MOz_five_times_nine_T_VPD_shadow.py).

| Original source-native timestamp | Approved tower T from interpolation (°C) | Approved VPD from interpolation (hPa) |
|---|---:|---:|
| 2014-04-02 08:30 | 8.904666667 | 3.974666667 |
| 2014-04-02 09:00 | 8.900333333 | 3.957333333 |
| 2014-04-02 10:00 | 8.771500000 | **keep original** 0.475 |
| 2016-04-11 13:00 | 14.067500000 | 9.828500000 |
| 2016-04-14 06:30 | 9.035000000 | 4.217000000 |

This represents 5 tower TA repairs and 4 VPD repairs (9 exact variable edits), with **TBOT and QBOT regenerated only on the five affected half-hours** from the Stage07 source saturation-vapour-pressure and specific-humidity equations. No pre-existing Stage07 repair, unrelated time/variable, original FLUXMET, standalone ERA companion, PFT/surface or Slurm job is changed.

**Status:** GitHub operator decision recorded and isolated successor script committed; actual IRIDIS6 run/receipt not yet reported. It would be inaccurate to claim the new candidate has been generated already. In all cases, 2005-01-06 05:00–09:00 source QA episode retains independent HOLD, and Post-v5/DATM/Spinup admission is still **FALSE** pending its review and actual case height/PFT implementation evidence.

## 2026-10-26 18:20 UTC — Stage13H proven QC1 source pattern; Jan06 8-hour threshold NOT actual complete fault

Stage13h \`--check\` and \`--run\` both completed on IRIDIS6. The source immutable and current signed Stage13g forcing SHA passed. Its isolated signed report is:
\`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13h_MOz_Jan2005_full_source_run_20261026T182004Z_d47ac8e2\`.

- From **01:30 to 09:00 2005-01-06** (16 halfhours, 8h), \`TA_F_QC=1\` all along, and tower source \`TA_F - TA_ERA\` between **+8.166 and +15.120°C**. Paired original standalone FLUXNET ERA5 \`TA_ERA/VPD_ERA\` reconstructs physically valid water-RH and QBOT for all 16; **16/16 is a physics test, not proof of independent ERA measurement validation**.
- **The anomaly is demonstrably not confined to those 16 halfhours**: Jan06 00:00–01:00 tower QC1 is already +7.126 to +7.750°C higher than ERA, and **14:00–23:30** contains 20 more continuous \`TA_F_QC=1\` warm biases ~+9–15°C. Additional 10:00 QC1 spike was **already specifically approved and repaired in the original Stage07** and must not be double-modified.
- The surrounding Jan06 **09:30**, **10:30–12:30** \`QC2\` source temperatures exactly equal companion ERA. This is a change in source gapfill/QC provenance, not independent cross-validation, and highlights the need to treat whole QC1 stretches separately from QC2.
- Jan06 **13:00,13:30** are also \`QC1\` with ~+3.93 to +3.95°C tower vs ERA, below the arbitrary 8°C threshold. Do not silently treat them as verified valid or invalid.
- Hence do **NOT** approve blind replacement just for 01:30–09:00. Investigate the native QC1 source blocks across adjacent days and the 2005 source ERA offset using [Stage13i full QC1 multiday source and boundary audit](../scripts/stage13/13i_MOz_2005_QC1_ERA_multi_day_episode_boundaries_READONLY.py). This makes no forcing changes.
- \`2005_QC1_paired_ERA_replacement_approved=False\`, \`Postv5_approved=False\`, \`DATM_ready=False\`, \`spinup_authorized=False\`. The finished Stage13g 315360-row shadow remains immutable.

## Current scientific gate

- US-MOz Stage07 numerical forcing: complete; 6 originally modified source events operator approved.
- Remaining meteorology: four groups above, source/QC provenance still unresolved.
- Model PFT: latest curated 90/10 ready for **proposed case input** (validate applied surface/case, not yet claimed applied).
- Tower geometry: 32m tower literature and 24.2m canopy BIF; exact variable-level `ZBOT` unresolved, and must NOT be invented.
- `Postv5_approved=False`; `DATM_ready=False`; `spinup_authorized=False`; no new Slurm jobs or original source modifications.

Next required operator decisions: the three exact QC0 source centers after Stage13f ±2h context; and policy for multi-hour 2005 05:00–09:00 suspect gap-fill/clock segment. Those are separate decisions.
