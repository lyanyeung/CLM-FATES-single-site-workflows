# US-Mpj Stage14D — actual whole-site gate and manual decision (2026-10-29)

**ACTUAL IRIDIS6 execution, not a hypothetical success.** Operator supplied transcript for SHA-pinned `14d_US_Mpj_final_315360_science_gate_READONLY.py` from `login6001`, source commit `346720f0c665dcfeabaaa26918f2a039e606fca3`, Git blob `f1bef658ebd1c5aec899b4fc12c6297678f778c7`. Python self-test PASS and full signed-source read-only run SUCCESS.

Exact signed report folder (operator stdout):

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/us_mpj_315360_science_gate_READONLY_20261029T035628Z_7d961f02
```

Original successful Stage13O research shadow:

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage13o_Mpj_20HH_operator_approved_ERA_RH_20261026T210746Z_5c3c8653
```

Original pre-Stage13O Stage07 source `SHA256=c227f65b800baca3160efe40442fee91ee83c5f04308a0453e0c22bd05d0f592`; Stage13O signed receipt `SHA256=9a0217c1b18b4aeb9a4b3fc6eb980fb76dfe100b773eebd218e147df1711df27`. Previous approved 2014 source repair and all 2018/2020 protected rows verified. Nothing overwritten and no Slurm job.

## Actual quantitative operator result

- Exactly **315,360** native site **30-minute** NOLEAP half-hours, 2008–2025, with all ten meteorological fields finite, no missing rows or nonconsecutive time source.
- Actual **17** 2014 Stage13O native VPD_USE/QBOT repairs only; all other model source fields/rows protected.
- **0** failed water-saturation/VPD/QBOT closure; **0** `TBOT−TA_USE−273.15` errors.
- **0** negative wind, precipitation, shortwave radiation or longwave radiation rows under the specified script thresholds.
- **610 native HH** water-relative RH **below 5%** (caution). Year distribution: 2008 2; 2009 0; 2010 0; 2011 39; 2012 15; 2013 3; 2014 22; 2015 0; 2016 3; 2017 50; 2018 33; 2019 5; 2020 0; 2021 40; **2022 247**; 2023 36; 2024 12; **2025 103**. 247+103=350 of 610 in 2022 and 2025. This diagnostic does NOT distinguish original tower-measured QC0 from QC1/2 MDS/ERA. Low RH alone is not a physical impossibility. Do not arbitrarily erase or replace 610 values.
- **3,791 native HH** ice-relative RH **above 100%**, *only for subfreezing tower T*. Year distribution 2008 262, 2009 189, 2010 320, 2011 285, 2012 174, 2013 178, 2014 160, 2015 490, 2016 195, 2017 255, 2018 199, 2019 307, 2020 168, 2021 173, 2022 197, 2023 100, 2024 52, 2025 87. This is a phase-specific caution: water-relative VPD/QBOT consistency PASS does NOT mean ice-relative RH<=100%. At -0.09°C and VPD=0 (2008-01-06 18:30), RHwater=100% and RHice=100.088% follow mechanically from two different saturation formulations. At ~-12°C on 2008-01-16, source may imply ice RH around 103–109%, requiring a phase/model-treatment caveat. It is not demonstrated that all 3,791 are unphysical or that model will abort; conversely do not assume CDEPS cannot cap them. Do not mass-clip/correct based solely on this screen.
- All **18 annual intervals** contain 17,520 rows, zero missing and zero water/QBOT/TBOT numerical physics failures. Source original 2014 repairs have no new 17-row misclosure.

## MANUAL SCIENTIFIC DECISION — stop per-event cycling

1. **PASS for numerical meteorology completeness and selected forcing water-based VPD/QBOT/TBOT physics**, and **CLOSE US-Mpj Stage13O/Stage14D source-gap workstream**. No additional numerical fill, no repeated 2014 humidity QC1 review, no automatic correction of the 610 low-water-RH or 3,791 ice-RH cautions.
2. **PRESERVE** all original tower measurements, user-approved 2014 Stage13O 20-source-HH operator decision (17 newly changed), original two 2018 low-but-positive-RH and Feb2020 approved one-T correction. DO NOT overwrite the Stage13O research shadow.
3. **Classify the 610 low-water-RH as QC/provenance warnings**, not necessarily bad data: prioritize 2022/2025 *only if* source-level instrument QC evidence or active scientific application needs them. No blanket refusal to use all site data purely for 610 low RH.
4. **Classify 3,791 ice supersaturation as phase-model-compatibility cautions**, not an automatic atmospheric error. Since the user's CTSM/CDEPS may compute `datm_eSat` over ice and cap humidity, later actual case-input compatibility must be confirmed by the precise installed code/input method. No automatic mass clipping. If the application forces no ice supersaturation, quantify the actual per-row cap and model impact *only at model admission*, not by inventing a new humidity source version.
5. **Post-v5/DATM/AD400 NOT YET AUTHORIZED.** Full-site numeric meteorology PASS is necessary but not sufficient for admission: existing PFT/surface composition/landunit, original BIF UTC/native-source→DATM time and units, sensor height `ZBOT`, original site meteorological QC/provenance (where relevant), and installed DATM saturation treatment are outside the current screen and need one model-specific preflight. No Slurm jobs have been submitted.
6. **Efficiency policy:** the scientific input candidate is now stable; do not create more per-timestamp repair stages merely to drive warnings to zero. Run one integrated site-specific case preflight after actual model/surface configuration is known, or keep scientific caveats without altering source.

The user's previous confirmed team ownership (2026-10-29) is unchanged: Claude studies US-Me6 and US-NR1, US-NR3 reserved for an advanced model, ChatGPT/operator owns the US-Mpj numerical science admission workstream. US-MtB MtB04 and US-MMS Stage14C already have independent numerically complete research versions.
