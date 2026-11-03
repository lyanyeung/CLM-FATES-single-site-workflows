# OzFlux_JapanFlux_PostSpinup — inputs for the observation-period run after AD400 → NORMAL400

Started 3 November 2026. This is the third OzFlux / JapanFlux topic. [OzFlux_JapanFlux_PFT](../OzFlux_JapanFlux_PFT/) gives the vegetation and [OzFlux_JapanFlux_Soil](../OzFlux_JapanFlux_Soil/) the soil. This folder covers what is needed *after* spin-up. **Nothing here creates a case, changes a file or submits a job.**

**Status, 3 Nov 2026: design and a read-only inventory script.**
- None of the 20 sites has finished spin-up.
- AU-ASM is the furthest along: its direct AD400 case passed the Stage08 check, and prepare / submit are pending.
- All other sites have no DATM forcing yet.

So this topic prepares the inputs and decisions in advance.

## What the observation run is

The project protocol ([AD400_NORMAL400_PROTOCOL](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/docs/AD400_NORMAL400_PROTOCOL.md)) runs 800 years of recycled site forcing: AD400, then NORMAL400. Model years in that spin-up are artificial.

The observation run comes after it:
- it starts from the final NORMAL400 restart;
- it runs the site's real forcing years **once, in calendar order**;
- its output is compared with the tower's GPP, NEE, LE and H.

The protocol leaves this step open. The table below fixes each input.

## Inputs and recommended choices

| # | Input | Spin-up (as run) | Observation run (recommended) | How it is settled |
| --- | --- | --- | --- | --- |
| 1 | **Initial state** | cold start → AD400 → NORMAL400 | The final NORMAL400 restart (model year Y+800) as a hybrid branch: `RUN_TYPE=hybrid`, `RUN_REFCASE` = the NORMAL400 case, `RUN_REFDATE` = Y+800-01-01, `RUN_STARTDATE` = first observation year. This is the same mechanism as the AD → NORMAL hand-off already proven here. The alternative is `startup` with `finidat` | Stage01 reads a finished NORMAL400 case: last restart set, `spinup_state` = 0, FATES restart variables |
| 2 | **Model configuration** | — | **Identical to the spin-up.** Same `fsurdat` (SHA), FATES parameter file (default, or the needleleaf F file), executable (patched build where the phenology rule applies), FIXNC flags and `calc_human_stress_indices`; `CLM_ACCELERATED_SPINUP=off` | Checklist in the prepare script |
| 3 | **Calendar and forcing** | The site's DATM years recycled; model calendar artificial | The same DATM files on the real calendar: `DATM_YR_START` / `DATM_YR_END` / `DATM_YR_ALIGN` = the observation years, one pass, `STOP_N` = number of years | Per site, once its forcing is approved |
| 4 | **CO₂** | Constant: NOAA global annual mean of the first forcing year (`CLM_CO2_TYPE=constant`) | **Transient:** the NOAA global annual mean of each year, from the [same NOAA file](data/NOAA_GML_co2_annmean_gl_rev20261009.csv) used for the spin-up values (revision 9 Oct 2026, SHA256 `d82714c8…`, 1979–2025). It is supplied as a DATM CO₂ stream with the same layout as the model's default CO₂ file. `CLM_CO2_TYPE=diagnostic` | Stage01 reads the pinned stream definitions and the default file header; Stage02 then writes the NOAA file |
| 5 | **N deposition, aerosol deposition** | As set by the spin-up case | Keep them **the same as the spin-up**, so the hand-off has no step change. Transient deposition can be a sensitivity run | Stage01 reports the spin-up settings |
| 6 | **Output** | Monthly: `TOTSOMC TOTSOMN TLAI FATES_GPP FATES_NPP TWS H2OSNO` | Three tapes (see below) | Stage01 reports how often each FATES field is updated |
| 7 | **Evaluation window** | — | The years that match the fixed PFT state (site plan below); other years are run but not evaluated | [site plan](data/OZ_JP_POST_SPINUP_SITE_PLAN_20261103.csv) |

Output tapes for the observation run:
- **Monthly:** the spin-up list plus `FATES_NEP`, `FATES_AUTORESP`, `FATES_HET_RESP`, `EFLX_LH_TOT`, `FSH`, `QVEGT` and `FATES_VEGC`.
- **Daily:** the EC fluxes.
- **Half-hourly:** the EC fluxes for diurnal comparison. A single point keeps these files small.

**CO₂ continuity.** The spin-up CO₂ is the NOAA mean of the first forcing year. The observation run starts in that same year with the same value, so CO₂ has no step at the hand-off.

**Soil and surface.**
- The observation run must use the spin-up surface.
- For the 19 sites that have not started spin-up, adopt the [soil v1 recommendation](../OzFlux_JapanFlux_Soil/OZ_JP_SOIL_TEXTURE_20_SITES_20261103.md) **before** the spin-up surface is built. Changing soil later means repeating the 800 years.
- AU-ASM's prepared AD400 uses the grid-reference soil (sand 90 / clay 6).

## Per-site plan

The full table is [OZ_JP_POST_SPINUP_SITE_PLAN_20261103.csv](data/OZ_JP_POST_SPINUP_SITE_PLAN_20261103.csv). The observation windows follow the `target_period` of the [PFT master](../OzFlux_JapanFlux_PFT/OZ_JP_RECOMMENDED_CLM_FATES_INPUT_PFT_20261102.csv). Disturbances that the fixed PFT vector does not represent are left out of the evaluation.

| Site | Fixed PFT state | Evaluation window | Forcing (3 Nov) | Expected rules class |
| --- | --- | --- | --- | --- |
| AU-ASM | Mulga, pre-dieback | 2013–2017 (2018 run, not evaluated) | DATM 2013–2018 built | UNCHANGED |
| AU-Cow | Rainforest | 2009–2022 | not built | UNCHANGED |
| AU-Cpr | Mallee, pre-fire | start–2013 | not built | UNCHANGED |
| AU-DaS | Uncleared savanna | 2008–2021 | candidate 2009–2021 | UNCHANGED |
| AU-Dry | Savanna | forcing years | candidate 2010–2018 | UNCHANGED |
| AU-Gin | Banksia woodland | start–2022 | not built | UNCHANGED |
| AU-How | Savanna (fire part of the state) | 2001–2025 | not built | UNCHANGED |
| AU-Stp | Mitchell grassland | forcing years | not built | UNCHANGED |
| AU-Tum | Wet eucalypt forest, pre-fire | 2002–2019 | not built | UNCHANGED |
| JP-Api | Beech | 2000–2022 (flag 2007) | not built | NEEDS_PHENOLOGY_PATCH |
| JP-Fhk | Larch, pre-thinning | 2006–2013 | not built | NEEDS_PATCH_AND_F |
| JP-Fjy | Red pine on lava | 2001–2021 | not built | NEEDS_NEEDLELEAF_F |
| JP-Khw | Sugi / hinoki | 2000–2003, 2007–2021 | not built | NEEDS_NEEDLELEAF_F |
| JP-Spp | Birch-oak, pre-typhoon | 2000–2003 | not built | NEEDS_PHENOLOGY_PATCH |
| JP-Tak | Deciduous broadleaf | 1998–2021 | not built | NEEDS_PHENOLOGY_PATCH |
| JP-Tef | Post-clearcut larch + Sasa | 2004–2023 | not built | NEEDS_PHENOLOGY_PATCH |
| JP-Tgf | Mown C3/C4 grassland | 2002–2022 | not built | UNCHANGED |
| JP-Tmd | Windthrow regrowth | 2005–2014 and 2015–2023 separately | not built | NEEDS_PHENOLOGY_PATCH |
| JP-Tom | Deciduous broadleaf | 1999–2013 (check the second tower) | not built | NEEDS_PHENOLOGY_PATCH |
| JP-Yms | Oak-dominated secondary forest | 2000–2023 | not built | NEEDS_PATCH_AND_F |

**Expected rules class.** This comes from the [maintenance rules](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/maintenance/RULES_FOR_NEW_CASES.md):

| Class | Requirement |
| --- | --- |
| UNCHANGED | Shared executable, default parameters |
| NEEDS_PHENOLOGY_PATCH | Patched SourceMods and the site's own build (cold-deciduous PFT 3, 6 or 9 present) |
| NEEDS_NEEDLELEAF_F | The needleleaf F parameter file from `params_adopted/` (PFT 2 present) |
| NEEDS_PATCH_AND_F | Both |

The classes are derived from the PFT vectors. They must be confirmed with script 22's functions when each case is built. Spin-up and observation run use the same class.

## Scripts

| Script | Where | What |
| --- | --- | --- |
| [01_post_spinup_inputs_inventory_READONLY.py](scripts/01_post_spinup_inputs_inventory_READONLY.py) | IRIDIS6 login node, read only | Items 1, 4, 5 and 6 above, plus the time coverage of the OzFlux L6 files. Writes one JSON to a new folder in `$HOME` |
| 02 CO₂ stream builder | next | Writes the NOAA annual CO₂ as a DATM stream file in the layout Stage01 finds |
| 03 observation-run prepare | per site, after its NORMAL400 is verified | Hybrid branch from the final restart, real-calendar DATM, transient CO₂, output tapes; guarded like the existing prepare/submit scripts |

## Next steps

1. Run Stage01 on IRIDIS6 and record the result here.
2. Decide items 4–6 from it: CO₂ stream layout, deposition (same as spin-up or transient) and output tapes. Then write Stage02.
3. Build the observation-run prepare script on the first site whose NORMAL400 finishes. This is probably not one of these 20; an ICOS Batch01–03 site can serve as the technical test.
