# OzFlux_JapanFlux_PostSpinup — inputs for the observation-period run after AD400 → NORMAL400

Started 3 November 2026. This is the third OzFlux / JapanFlux topic. [OzFlux_JapanFlux_PFT](../OzFlux_JapanFlux_PFT/) gives the vegetation and [OzFlux_JapanFlux_Soil](../OzFlux_JapanFlux_Soil/) the soil. This folder covers what is needed *after* spin-up. The aim is a run whose GPP, NEE, LE and H can be compared with the towers half-hour by half-hour.

**Status, 3 Nov 2026: design decided; Stage01 run; Stage02 published.**
- Stage01 (IRIDIS6 read-only inventory) ran at 12:54 UTC. Results are [below](#stage01-result-3-nov-2026).
- Stage02 writes the NOAA CO₂ stream file and previews the observation-run namelists on a clone of one finished NORMAL400 case. It does not build or submit anything.
- None of the 20 sites has finished spin-up. AU-ASM's direct AD400 case **has not been created yet** (Stage01), and the other 19 sites have no DATM forcing.

## What the observation run is

The project protocol ([AD400_NORMAL400_PROTOCOL](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/docs/AD400_NORMAL400_PROTOCOL.md)) runs 800 years of recycled site forcing: AD400, then NORMAL400. Model years in that spin-up are artificial.

The observation run comes after it:
- it starts from the final NORMAL400 restart;
- it runs the site's real forcing years **once, in calendar order**;
- its output is compared with the tower's GPP, NEE, LE and H.

## Inputs and decisions

| # | Input | Spin-up (as run; Stage01) | Observation run (decided) | Evidence |
| --- | --- | --- | --- | --- |
| 1 | **Initial state** | cold start → AD400 → NORMAL400 | **Hybrid start from the final NORMAL400 restart** (model year Y+800). This is the same mechanism as the AD400 → NORMAL400 hand-off ([Batch03 script 14](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/main/examples/Batch03_10/scripts/14_batch03_AD400_to_NORMAL400.py)): `create_clone --keepexe` of the NORMAL400 case; `RUN_TYPE=hybrid`; `RUN_REFCASE` = the NORMAL400 case; `RUN_REFDATE` = Y+800-01-01; `GET_REFCASE=FALSE`; the restart set is copied (SHA-checked) into the new RUNDIR with rpointers; `finidat` is set explicitly. `RUN_STARTDATE` = 1 January of the first forcing year | <ul><li>The last restart set holds `clm2.r`, `cpl.r`, `datm.r`, `rh0a/rh0i` and three rpointers. `spinup_state` = 0. The land restart has 220 FATES variables.</li><li>FATES phenology counts days with its own counter, `fates_phen_model_date`, which is kept in the restart. So the calendar jump from Y+800 to the real year does not disturb leaf-on / leaf-off timing.</li></ul> |
| 2 | **Model configuration** | `2000_DATM%1PT_CLM60%FATES…`, `CLM_NML_USE_CASE=2000_control`, `suplnitro='ALL'`, `fates_parteh_mode='carbon_only'`, `use_lch4`, nocomp + fixed biogeography | **Identical.** `create_clone --keepexe` keeps the executable, SourceMods, surface, FATES parameter file and every namelist value. Only rows 3–6 change. The 2000 compset brings no transient land use or deposition | Stage02 diffs the generated `lnd_in` / `datm_in` / streams against the template |
| 3 | **Forcing** | The site DATM files cycled (`taxmode=cycle`); model calendar Y…Y+800 | The same files and stream settings (`year_first` / `year_last` / `year_align`). `RUN_STARTDATE` = `year_first`-01-01, so model year = data year. `STOP_N` = number of forcing years: one pass | Stage02: met stream unchanged |
| 4 | **CO₂** | Constant: `CLM_CO2_TYPE=constant`, `CCSM_CO2_PPMV` = NOAA global mean of the first forcing year (e.g. AT-Neu 2002 = 372.58) | **Transient NOAA global annual mean**, from the [same NOAA file](data/NOAA_GML_co2_annmean_gl_rev20261009.csv) as the spin-up values (revision 9 Oct 2026, SHA256 `d82714c8…`, 1979–2025). Settings: `CLM_CO2_TYPE=diagnostic`, `CCSM_BGC=CO2A`, `DATM_CO2_TSERIES=cmip6_20tr`, and `user_nl_datm_streams` points `co2tseries.cmip6_20tr` at the NOAA stream file (1979–2025). `CCSM_BGC` matters: a `_DATM` compset defaults to `none`, and without `CO2A` the mediator does not pass `Sa_co2diag` and CLM aborts | Pinned source (CTSM `d5ea9d01`, CDEPS `cdeps1.0.105`, CMEPS `cmeps1.1.64`, FATES `121723f6`):<ul><li>`CCSM_BGC=CO2A` → `flds_co2a`;</li><li>`DATM_CO2_TSERIES` ≠ none → datm `flds_co2` and the co2tseries stream;</li><li>CLM `diagnostic` requires `Sa_co2diag`;</li><li>the stream override reaches the input-data list.</li></ul>Stage02 repeats these checks on IRIDIS |
| 5 | **N / aerosol / O₃ deposition** | DATM streams `presndep.clim_2000_cmip6`, `presaero.clim_2000`, `preso3.clim_2000` (year-2000 climatology) | **Keep, unchanged.** With `suplnitro='ALL'` and carbon-only FATES, N deposition cannot change carbon; aerosol deposition only affects snow albedo. A transient-deposition sensitivity run is therefore not needed | Stage01 |
| 6 | **Output** | One **daily** tape (`hist_nhtfrq=-24`, 365 per file): `TOTSOMC TOTSOMN TLAI FATES_GPP FATES_NPP TWS H2OSNO` | Two tapes, [below](#output-tapes) | Stage02 checks every field name, and the update frequency of the half-hourly FATES fields |
| 7 | **Evaluation window** | — | The years that match the fixed PFT state ([site plan](#per-site-plan)). Other years are run but not evaluated | Stage01 L6 coverage |

### CO₂ stream file

Stage02 writes `experiments/NonCompetitionObserved22/co2_adopted/fco2_datm_global_NOAA_GML_annmean_1979-2025_rev20261009.nc`. It writes the file once, makes it read-only, writes a receipt next to it, and never overwrites it.

- **Layout.** The same layout as the model's default `fco2_datm_global_simyr_1750-2014_CMIP6_c180929.nc` (CESM inputdata, SHA256 `28dcbdf0…`; that file is not on IRIDIS):
  - NETCDF3 classic, one global cell;
  - `CO2(time, lat, lon)` in ppmv;
  - time in days since 1979-01-01, gregorian calendar, stamped at mid-year;
  - the same grid variables.

  A local test confirmed that every dimension, variable, data type and attribute name matches.
- **How DATM reads it.** DATM reads it as a single-point stream (`meshfile none`, `mapalgo none`), interpolates linearly between mid-year values, and holds the end values (`taxmode extend`). Runs past mid-2025 therefore see the 2025 mean.
- **Hand-off continuity:**
  - in the first forcing year, the stream's annual mean is within 0.1 ppm of the spin-up constant;
  - on 1 January of that year, the stream is 1.0–1.4 ppm lower, which is half of one year's rise. Example: 2002 spin-up 372.58, stream on 1 Jan 371.58, 2002 mean 372.65.

  Stage02 tabulates this for every finished NORMAL400 case.

### Output tapes

| Tape | Frequency | Fields |
| --- | --- | --- |
| 1 | daily (`-24`, 365 per file) | the spin-up seven + `FATES_NEP FATES_HET_RESP FATES_AUTORESP FATES_MAINT_RESP FATES_GROWTH_RESP FATES_LAI FATES_VEGC FATES_LEAFC HR EFLX_LH_TOT FSH QVEGT QVEGE QSOIL FSA FIRA FGR FSDS TSA RH2M TSOI_10CM SOILWATER_10CM PCO2 TOTECOSYSC` |
| 2 | every model time step (`1`; 30 min when `ATM_NCPL`=48; 365 × `ATM_NCPL` per file) | `FATES_GPP FATES_NEP FATES_HET_RESP FATES_MAINT_RESP EFLX_LH_TOT FSH QVEGT FSA FIRA FGR FSDS TBOT TSOI_10CM` |

- **Which fields can go on tape 2.** Only FATES fields that are updated every time step (`upfreq=group_hifr_simple`): `FATES_GPP`, `FATES_NEP`, `FATES_HET_RESP` and `FATES_MAINT_RESP`. `FATES_AUTORESP`, `FATES_GROWTH_RESP`, `FATES_NPP`, `FATES_LAI` and `FATES_VEGC` are updated once a day (`group_dyna_simple`), so they stay on tape 1.
- **NEE = −`FATES_NEP`.** In this FATES version, `FATES_NEP` is:
  - GPP;
  - minus maintenance respiration of the time step;
  - minus the previous day's growth and excess respiration, spread evenly over the day;
  - minus heterotrophic respiration.

  With `FATES_NEP` in kg C m⁻² s⁻¹: NEE (µmol CO₂ m⁻² s⁻¹) = −`FATES_NEP` × 10⁹ / 12.011. Ecosystem respiration on tape 2 = `FATES_GPP` − `FATES_NEP`.
- **`PCO2`** (tape 1) shows the CO₂ that CLM actually used. It must rise from year to year in the observation run.
- **`FSDS` and `TBOT`** on tape 2 are there to check the time alignment against the tower's incoming shortwave and air temperature.

### Time stamps for the EC comparison

- **Model clock.** The model clock is the DATM time base. Solar geometry assumes UTC, so the forcing must be in UTC. AU-ASM's provisional DATM ([OzFlux_MultiSite_09](../OzFlux_MultiSite_09/) Stage12) uses UTC interval centres; the other 19 sites must do the same.
- **Model time stamps.** CLM stamps averaged history values at the end of the averaging interval; `time_bounds` gives the interval.
- **Tower time stamps.** OzFlux L6 and JapanFlux use local time stamps. Confirm the convention (interval start or end) per release before the comparison.
- **Calendar.** The model calendar is NO_LEAP, so tower data for 29 February are dropped.

### What these inputs can and cannot do for NEE

**What they fix:** the CO₂ path, the output (NEE every time step) and the timing.

**What they cannot fix:** an 800-year spin-up with fixed vegetation ends close to equilibrium, so the model's mean NEE is near zero apart from a small CO₂-driven sink. Most towers are net sinks because of stand age and disturbance history.

**How to evaluate NEE, therefore:**
- First, by its diurnal cycle, its seasonal cycle and its year-to-year anomalies.
- GPP and ecosystem respiration separately.
- The annual NEE sum mainly tests the equilibrium assumption. This applies most to the regrowth stands: JP-Tef (clear-cut 2003), JP-Tmd (windthrow) and JP-Fhk (plantation).

### Soil and surface

- The observation run must use the spin-up surface; `create_clone --keepexe` guarantees this.
- For the 19 sites without spin-up, adopt the [soil v1 recommendation](../OzFlux_JapanFlux_Soil/OZ_JP_SOIL_TEXTURE_20_SITES_20261103.md) **before** the spin-up surface is built. Changing soil later means repeating the 800 years.
- **AU-ASM.** Its AD400 case has not been created (Stage01), so adopting soil v1 now costs no spin-up time:
  - soil v1 is T1, 0–30 cm sand 74 / clay 15;
  - the prepared grid-reference surface has sand 90 / clay 6;
  - the surface comes from the [OzFlux_MultiSite_09](../OzFlux_MultiSite_09/) Stage16 pipeline, so the switch is a decision for that pipeline.

## Per-site plan

The full table is [OZ_JP_POST_SPINUP_SITE_PLAN_20261103.csv](data/OZ_JP_POST_SPINUP_SITE_PLAN_20261103.csv).
- Windows follow the `target_period` of the [PFT master](../OzFlux_JapanFlux_PFT/OZ_JP_RECOMMENDED_CLM_FATES_INPUT_PFT_20261102.csv), cut to the full calendar years of the OzFlux L6 files (Stage01).
- Disturbances that the fixed PFT vector does not represent are left out of the evaluation.

| Site | Fixed PFT state | Evaluation window | Forcing / spin-up (3 Nov) | Expected rules class |
| --- | --- | --- | --- | --- |
| AU-ASM | Mulga, pre-dieback | 2013–2017 (2018 run, not evaluated) | DATM 2013–2018 built; AD400 case not created | UNCHANGED |
| AU-Cow | Rainforest | 2009–2022 | not built | UNCHANGED |
| AU-Cpr | Mallee, pre-fire | 2011–2013 (L6 starts 30 Jul 2010) | not built | UNCHANGED |
| AU-DaS | Uncleared savanna | 2008–2021 | candidate 2009–2021 | UNCHANGED |
| AU-Dry | Savanna | 2010–2024 within the forcing years (candidate 2010–2018) | candidate 2010–2018 | UNCHANGED |
| AU-Gin | Banksia woodland | 2012–2022 (L6 starts 13 Oct 2011) | not built | UNCHANGED |
| AU-How | Savanna (fire part of the state) | 2002–2025 (L6 starts 1 Jan 2002) | not built | UNCHANGED |
| AU-Stp | Mitchell grassland | 2009–2025 (L6 starts 28 Aug 2008) | not built | UNCHANGED |
| AU-Tum | Wet eucalypt forest, pre-fire | 2003–2019 (L6 starts 7 Jan 2002) | not built | UNCHANGED |
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

The classes are derived from the PFT vectors and must be confirmed with script 22's functions when each case is built. Spin-up and observation run use the same class, and `create_clone --keepexe` carries it over.

## Stage01 result (3 Nov 2026)

`$HOME/ozjp_post_spinup_stage01_20261103T125440Z/stage01_inventory.json` on IRIDIS6.

- **Pinned source.** CTSM `d5ea9d0136530370a62ef267ccfaff6f001ef914`, FATES `121723f64e94be97fd91fc95cfd1ba72dfc191ee`.
- **CO₂ and aerosol options.**
  - `DATM_CO2_TSERIES`: `none` (default), `cplhist`, `cmip6_20tr`, `cmip7_20tr`, `omip.*` and SSP options.
  - `CLM_CO2_TYPE`: `constant` (default), `diagnostic`, `prognostic`.
  - `DATM_PRESAERO` default: `clim_2000`.
- **Default CO₂ file.** `fco2_datm_global_simyr_1750-2014_CMIP6_c180929.nc` is **not in IRIDIS DIN_LOC_ROOT**. Its layout was read from the CESM inputdata copy instead.
- **History update frequency.** Every time step (`hifr`): `FATES_GPP`, `FATES_NEP`, `FATES_HET_RESP`. Once a day (`dyna`): `FATES_NPP`, `FATES_AUTORESP`, `FATES_LAI`, `FATES_VEGC`.
- **Finished NORMAL400 cases.** There are **78**, from ICOS Batch01–03 and AmeriFlux Batch01–05. Each has 80 restart sets, 400 years, and a constant CO₂ equal to the NOAA mean of its first forcing year. Stage01 listed 79 cases; DE-Tha's 5-year test case is not counted.
- **Template case `AT-Neu_B03_FIXNC_NORMAL400`.**
  - Hybrid from `AT-Neu_B03_FIXNC_AD400` at 2402-01-01; `RUN_REFDIR=ccsm4_init`; `GET_REFCASE=FALSE`; `finidat` set in `user_nl_clm`.
  - Shared EXEROOT; default FATES parameters.
  - DATM met stream 2002–2020, align 2002, `taxmode=cycle`.
  - Output: daily tape, 365 per file.
  - Last restart 2802-01-01: `spinup_state` 0, 220 FATES restart variables.
- **AU-ASM.** `AU-ASM_OZ_FIXNC_GRIDREF_AD400_DIRECT` does not exist yet.
- **OzFlux L6 coverage (first → last time stamp):**

  | Site | First | Last |
  | --- | --- | --- |
  | AU-ASM Mulga1 | 2010-09-03 | 2023-03-08 |
  | AU-ASM Mulga2 | 2024-08-21 | 2026-04-23 |
  | AU-Cow | 2009-01-01 | 2026-04-23 |
  | AU-Cpr | 2010-07-30 | 2026-01-01 |
  | AU-DaS | 2008-01-01 | 2026-04-23 |
  | AU-Dry | 2009-10-25 | 2025-02-02 |
  | AU-Gin | 2011-10-13 | 2026-02-02 |
  | AU-How | 2002-01-01 | 2026-02-02 |
  | AU-Stp | 2008-08-28 | 2026-04-23 |
  | AU-Tum | 2002-01-07 | 2022-12-03 |

## Scripts

| Script | Where | What |
| --- | --- | --- |
| [01_post_spinup_inputs_inventory_READONLY.py](scripts/01_post_spinup_inputs_inventory_READONLY.py) | IRIDIS6 login node, read only | Items 1, 4, 5 and 6 above, plus the time coverage of the OzFlux L6 files. Done 3 Nov |
| [02_noaa_co2_stream_and_obsrun_preview.py](scripts/02_noaa_co2_stream_and_obsrun_preview.py) | IRIDIS6 login node | <ul><li>**A** pinned-source checks of the CO₂ chain, the FATES phenology counter and all 44 tape fields.</li><li>**B** writes the NOAA CO₂ stream file once, with a receipt.</li><li>**C** CO₂ continuity for every finished NORMAL400 case.</li><li>**D** `create_clone --keepexe` of one finished NORMAL400 case into the new Stage02 folder; observation-run settings; `case.setup`, `preview_namelists`, `check_input_data`; diffs against the template. No build, no submit.</li></ul> |
| 03 observation-run prepare / submit | next, after Stage02 passes | The real hybrid hand-off: restart copy, settings as previewed, segments sized from the template throughput; guarded like the existing prepare / submit scripts |

## Next steps

1. Run Stage02 on IRIDIS6 and record the result here.
2. Stage03, a technical pilot: one real observation run on one of the 78 finished NORMAL400 cases. Check after the first year:
   - `PCO2` changes between years;
   - tape 2 exists;
   - `FATES_NEP` is plausible;
   - the restart chain works.
3. Then apply the same Stage03 to each OzFlux / JapanFlux site once its NORMAL400 is verified.
