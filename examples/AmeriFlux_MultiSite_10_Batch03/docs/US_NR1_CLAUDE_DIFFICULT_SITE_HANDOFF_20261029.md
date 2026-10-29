# Claude handoff — US-NR1, AmeriFlux Batch03

**New Claude assignment 2026-10-29, after US-MtB research gap closure.** The user retains all final science and model job approval. **US-NR3 excluded and reserved for separate advanced model; US-Me6 is the other newly assigned difficult site; ChatGPT/operator handles US-Mpj.** Do not confuse US-NR1 forest site with US-NR3 alpine tundra. This is a saved handoff, not an automatic Claude session.

## Source and actual status

- Original release `AMF_US-NR1_FLUXNET_1998-2025_v1.3_r1`, native halfhour 1998–2025, **490560 NOLEAP rows**.
- **Stage13P was actually applied** after operator approval on 2026-10-26 22:36 UTC: output `science_trials/stage13p_NR1_6ERA_RH_5_PSRF_FLDS_OPERATOR_APPROVED_20261026T223628Z_6b3f07eb`. Exactly 6 original Sept2022 native humidity VPD_USE/QBOT slot changes and 5 old December2004 nonhumidity field-value changes (3 PSRF + 2 FLDS) across four native dates; six source RH physical and 7 half-hour adjacent VPD joins PASS, max edge 0.063194 hPa; preserve original source and previously approved Stage12AF site TA.
- Latest signed **234 remaining selected VPD_USE/QBOT halfhours still missing**. The source is still research-only; neither this numerical gap nor Post-v5/DATM/AD400 is resolved.
- Important exact three 2022-09-10 source temperature corrections from measured QC0 bookends were previously signed in Stage12AF: 06:30 →1.241°C, 07:30→1.556666667°C, 08:00→1.393333333°C. Preserve each `TA_USE/TBOT` and the user-approved 2022 six VPD/QBOT repair at 06:00–08:30, do not re-interpolate.

## Why difficult

Stage12G missing-source years and original physically suspect source humidity are not independent. The signed previous Stage12G showed 238 missing NR1 on its parent; Stage13P 6 humidity repairs and upstream different source lineage yield latest **234**. The original full audit flagged many candidate reanalysis transfers despite no locally validated same-time measurement. For 173 source-negative winter residual Stage10D original events, 148 were original `VPD_F_QC=2` (ERA), 25 QC1; Stage10B had 57 tower/grid |ΔT|>5°C flags. Stage12G acquired a new 2022 source year that covered 22 original native events but **0/22** physical/QC/temperature checks passed the strict candidate method, including 19 tower/grid T difference and 3 VPD join failures. Thus downloading a new gridded year or clipping numerical RH is not a science answer. Stage12E previously had 135 missing verified annual ERA5-Land source events; after 2022 source year 113 remained in that subset, not 113 total missing. These scopes must be reconciled against current 234 source gaps, not added.

## Required one-pass science deliverable

1. **Verify actual signed Stage13P 490560-row shadow and extract exact 234 HH** with source-native timestamp, year, variable missing, original `TA_F/TA_F_QC`, `VPD_F/VPD_F_QC`, source ERA `TA_ERA/VPD_ERA`, official BIF UTC offset and original observation provenance. Partition by consecutive episode/year and source QC/physics/unknown missing-year classification. Ensure no duplicate times and NOLEAP retained.
2. **Root-cause** 2001, 2018, 2021 and all other active missing years, using actual tower BASE/BADM available RH/TA or other independently measured inputs if present. Check sensor height/source QA and gridded representativeness (original strong winter tower−ERA divergence); do not generalize Stage13P's Sept2022 method.
3. **Use fully measured source QC0 as evidence**, not QC1/QC2/MDS or ERA-to-ERA reuse, testing candidate `e`, RHwater/ice, `VPD_USE`, `QBOT`, PSRF/FLDS and native 30min temporal joins against measured QC0 locally and with blocked-day/year cross-validation as feasible. Quantify uncertainty per source-year and record strict source provenance.
4. Provide **one classified 234-HH manual decision matrix** with approved existing 2022 and Dec2004 edits protected, true alternate validated measurement where found, reanalysis-only low confidence, and impossible/insufficient science HOLD. Do not push to Post-v5/DATM/AD400 until science evidence and separate operator signoff.

## Key material (not guessed)

- Experiment root: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03`
- Original SHA pinned release manifest: `qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json`
- Actual Stage13P full shadow: `science_trials/stage13p_NR1_6ERA_RH_5_PSRF_FLDS_OPERATOR_APPROVED_20261026T223628Z_6b3f07eb/`
- [Stage13P actual applied result and operator decision](STAGE13P_NR1_USER_APPROVED_2022_SIX_RH_2004_FIVE_PSRF_FLDS_MOBILE_20261026.md).
- [Original signed 2022 original temperature and Kon science manual hold background](STAGE12AF_NR1_T_APPROVAL_KON_CLUSTER_REPAIR_POLICY_MTB_ICE_GATE_20261026.md).
- [Stage12G 22 new 2022 source records 0 passing and other source years](STAGE12G_NINE_YEAR_138_REPAIRS_AND_STAGE12M_NON_MTB_HOLD_DIAGNOSIS_2026-10-25.md).
- [10-site current source status](MANUAL_HOLD_TRIAGE_AND_TEN_SITE_STATUS_20261029.md).
- Exact source original script [Stage13P](../scripts/stage13/13p_NR1_operator_approved_two_group_ERA_RH_PSRF_FLDS_shadow.py).

**Deliver to user:** source-level chronological 234-HH decision ledger, summary of 2001/2018/2021 and any other missing-year sources with independent measurement options, per-episode physically coupled humidity proposals, scientifically justified remaining HOLD and specific approval requests. Keep the work efficient (batch original episodes, **no serial ad hoc thresholds or repeated individual Stage scripts**). Absolutely NO original source overwrite and NO CIME/DATM/AD400/Slurm job without explicit user approval.
