# Batch05 — Direct accelerated AD400, no separate 5-year trial

**Decision, 29 October 2026:** prepare all TEN Batch05 AmeriFlux sites for direct 400-year accelerated spinup, one submission per separate case, **80 chained 5-year segments, RESUBMIT=79**. Five-year checkpoint length is not a standalone AD5 pilot. No NORMAL phase is requested. This is a technical preparation specification, NOT science approval or a submission record.

## Actual Stage97/98 status

- All 10 original site FLUXMET/FULLSET sources were found and verified in earlier source audits. Stage98 used a limited location-specific file inventory and reported 0 selected production DATM, 0 surfaces, 0 Batch05 CIME cases **at those searched paths**: do not interpret this as proof that no files exist anywhere else.
- Original P2/P3 1,574 HH have zero unclassified cases. Versioned main research repair overlay 1,675 HH has consistent numerical physics and SHA256 63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce. Separate Stage89 US-Whs 51 HH T/VPD preview is research only, not merged into production.
- 63 distinct original source-risk HH remain: 46 original P1 HOLD, 10 RH saturation-platform HOLD, seven original temperature exceptions. Stage97 grouped the 56 P1/platform holds into ten consecutive events.
- Stage97 source classes: 35 original source T/VPD QC2 produce negative RH AND the same original processed-source ERA T/VPD pair reproduces that same negative RH (not valid for naive ERA substitution); ten low-positive P1 RH without two-sided physically valid QC0 donors; one P1 with donors; four original US-Vcm RH ~99.46% plateau; six original US-WCr RH exactly 100%. Source QC and holds were retained. None automatically approved.
- Stage98 original processed-source ERA humidity proxy research repairs = 1,281 HH; not independently validated as production forcing. Do not conflate source product ERA companion with separately downloaded, clock-aligned independent reference.
- **Present release gate BLOCKED:** scientific treatment of 63 original risk HH, independent assessment of 1,281 source-ERA proxy HH, production DATM, independent site PFT/soil surface, and ten source-pinned CIME cases.

## Detailed engineering references from previous cohorts

| Previous verified method | Repository source (lyanyeung/Non-Competition-CLM-experiment) | Specific Batch05 use |
|---|---|---|
| Batch01 Lane A AD/FATES and submission ledger | examples/AmeriFlux_Batch01_10/scripts/21_laneA_AD400_NORMAL400_controller.py | Confirm PFT/bare host-to-FATES fractions; protect old cases; put an ATTEMPTED receipt on disk before a real submit. NORMAL is not requested here. |
| Batch02 direct AD400 with no standalone pilot | examples/Batch02_10/scripts/15_IT_Noe_direct_AD400_conditional_submit.py | Use STOP_N=5, REST_N=5, RESUBMIT=79, RUN_TYPE=startup, accelerated spinup and one submission for 400 years. |
| Batch02 hist variables and regenerated private model namelist | examples/Batch02_10/scripts/40_IT_Noe_new_case_GPP_NPP_histfix_AD400.py | Verify FATES history fields; do not select unsupported GPP/NPP conventional outputs; preserve private FATES accelerated namelist state. |
| Batch03 ten-site PFT, bare ground and early ESMF crashes | examples/Batch03_10/scripts/11_batch03_AD400_oneclick.py and 13_batch03_continue_verified_AD395.py | Check exactly mapped HLM/FATES PFTs and soil; stack low 8192 KiB was implicated in early crashes; verify CLM/DATM/CPL restart and archive dependencies, 5-year segments. |
| AmeriFlux Batch03 research source-to-DATM inventory | examples/AmeriFlux_Batch03_10/scripts/B3_00_AD400_input_inventory_READONLY.py | Source-selected met, NOLEAP 365d clock, native local-to-UTC, 7 required DATM meteorology variables, soil, PFT/point surface, instrument ZBOT, CO2 table, private FATES overlay and a built template executable. |
| AmeriFlux Batch04 live stack/Slurm resource guard | examples/AmeriFlux_Batch04_10/scripts/b04_stack_guard.py | Soft stack >=65536 KiB, prefer 300000 KiB if raising, NEVER decrease high/unlimited or modify hard limit, confirm PropagateResourceLimits=STACK or ALL. Guard must run in the same process as case.submit. |
| AmeriFlux Batch04 input/case preflight | examples/AmeriFlux_Batch04_10/scripts/03_batch04_AD5_readiness_gate_READONLY.py | Adapt its strict unit, UTC, NOLEAP, ZBOT and CIME name checks, but NOT its standalone AD5 pilot policy. |

**Never copy or overwrite the other cohorts' original cases, selected forcing, PFT surfaces, executable or outputs without a site-equivalence audit.** They are methodological reference only.

## Production data and scientific gate

For each site choose and document *a single full-length, physically defensible, immutable selected forcing source* with per-HH original QC, corrected T/VPD/RH, original source/met provenance, uncertainty and a selected-force checksum. Release a new scientific approval manifest before building NetCDF.

Stage97 decisions must explicitly handle the 35 original source QC2 negative-RH cases without reusing the *identically invalid* original source-ERA pair; the 11 low-positive P1 cases need a documented measurement/replacement or exclusion decision; the 4 near-saturated Vcm and 6 RH100 WCr source plateaus cannot automatically be declared faulty; all seven temperature exceptions need retain/mask/substitute policy. The 1,281 original product ERA humidity proxy research cases require independent evidence or a defensible model forcing uncertainty policy. If a site cannot provide defensible forcing, leave it HOLD rather than silently filling invalid data.

Create **new versioned** annual DATM NetCDF for each site; never overwrite original CSVs or ZIPs. Validate:
- TBOT [K], QBOT [kg/kg], PSRF [Pa], FSDS/FLDS [W/m²], WIND [m/s], PRECTmms [mm/s] plus model-required fields. Confirm source product units first.
- The source's native HH or HR resolution, TIMESTAMP_START/END, source local-standard vs UTC, actual zone offset and no DST interpretation, interleaved year transitions and exact NO_LEAP calendar. Remove Feb 29 only by documented rule; do not shift half-hour edges.
- Thermodynamic reconstruction of q using validated T, e, p: q = 0.622 e / (p - 0.378 e), with the source pressure in consistent units, 0<=RH<=100, positive finite vapor pressure and source-appropriate ice/water saturation at cold temperatures.
- Rain from source P/P_F (mm per actual source interval) to PRECTmms by dividing by that interval in seconds. Check total water conservation, source QC and ERA contribution. US-Wkg's Stage95 observed 12.573 mm over the two 30-min intervals is only one event.
- Pressure, longwave, shortwave, wind, measurement heights, ZBOT and any source reanalysis fallback must have separate QC/unit/provenance checks. Source T/VPD QC0 alone does not certify scientific truth.
- Compare exact full input files/stream paths (including actual CaseDocs/datm.streams.xml versus RUNDIR/datm.streams.xml), no NaN, no gaps, proper model-year forcing cycle start/end.

## Per-site PFT, soil and point surface

Audit each tower's observed PFT percentages, bare fraction and crop/natural landunits, not generic grid PFT guesses. Verify all 15 host NATPFT slots, host bare at index 0, and actual fates_hlm_pft_map in the pinned private FATES parameter file. Check exact surface location/longitude/latitude and 1x1 point domain. Soil sand/clay must follow verified CLM ten-layer source and organic content, with documented proxy uncertainty. Earlier AmeriFlux50 tables and previous Batch02 BASE_MeasurementHeight and co2_annmean_gl are potential *reference data*, not automatic site-level approval.

## CIME settings for each NEW distinct Batch05 case

- RUN_TYPE=startup, initial CONTINUE_RUN=FALSE, CLM_ACCELERATED_SPINUP=on, validated FATES accelerated spinup_state=2, CLM_FORCE_COLDSTART policy from pinned matching FATES/CTSM.
- STOP_OPTION=nyears, STOP_N=5, REST_OPTION=nyears, REST_N=5, RESUBMIT=79, RESUBMIT_SETS_CONTINUE_RUN=TRUE. Expected 80 chained segments x 5 years from one initial case.submit; **no separate AD5 test**.
- Per-site RUN_STARTDATE at original forcing first year: UiD 2008, UMB/UMd/Vcm/Vcp/Whs/Wjs 2007, Var 2000, WCr 1999, Wkg 2004. End years +400; native forcing-years-cycle must be separately verified.
- FATES fixed-biogeography/no-competition design, valid private parameter file, surface and PFT mapping, co2 source, executable built with correct coupled FATES version; do not modify shared CTSM to force a local case.
- DOUT_S=TRUE and unique Batch05 RUNDIR/archive root. Confirm rpointer.lnd, rpointer.atm and rpointer.cpl plus archived CLM/DATM/CPL restarts at each 5-year boundary and correct dependency-driven next submission.
- Check persistent CIME skip-preview behavior across 79 auto-resubmits so namelist regeneration cannot drop private FATES spinup_state; compare actual CaseDocs and RUNDIR input/stream hashes.
- Proven older cases used one MPI task and srun --mpi=pmix, often 8G requested memory; check current executable/MPI environment, partition limits and measured per-segment runtime before setting the walltime. Do not simply carry forward one-hour time limits that have timed out in other workflows.

## Mandatory stack and job-protection policy

The new module scripts/AD400_direct_preflight/batch05_direct_ad400_stack_guard.py follows the previous Batch04 stack guard, with DIRECT_AD400 as the explicit submission phase. A future submit controller **must import and call require_for_submission(site=site, phase="DIRECT_AD400", may_raise=True) inside the same Python process that then executes case.submit**. Standalone Python that increases its own stack does not alter a later submitting process. Use a minimum soft stack 65536 KiB, preferred raised value 300000 KiB if hard limit allows, never decrease a high or unlimited setting, never modify hard limit. Check Slurm scontrol show config includes PropagateResourceLimits=ALL or STACK and no job-script override disables it.

Before real case.submit, atomically create a per-site ATTEMPTED receipt with selected DATM/surface/model hash, resource guard stack+Slurm proof, cycle years, case ID and no previously submitted job. If case.submit returns an error or ambiguous result, **never retry blindly**; inspect scheduler and CaseStatus first. Archive storage and Scratch **inode** quota must be checked before generating multi-year NetCDF and 10x80 job chains. Prior Scratch inode max 614400 and multiuser Slurm node contention warrant caution. No external user jobs should be touched.

## Stage99 operational next step — NO job submissions

Run the SHA-pinned one-command Stage99 launcher from scripts/AD400_direct_preflight on an IRIDIS6 login node. It:
1. Raises shell stack only if permitted without lowering, then verifies live same-shell Python stack and Slurm propagation.
2. Verifies successful actual Stage98 and Stage90 manifest+SHA and ten original source science identities.
3. Probes more realistic original-forcing, candidate DATM NetCDF, surface files, existing Batch05-named case locations, CIME reference-only templates, shared CTMS/FATES parameters, BIF measurement height/soil/CO2 candidate tables, and filesystem block/inode observations.
4. Writes only new HOME reports identifying exact sources, missing approvals and candidate paths. **A discovered NetCDF or case is not automatically scientifically approved.**

After Stage99, the remaining production work is real source-science release, selected forcing NetCDF construction, PFT/soil/surface review/build, new ten-site CIME prepare-only case generation, independent full pre-submit source/case/resource checks and finally single direct AD400 submit for each ready site.

**Current release status: BLOCKED_PRODUCTION_SCIENCE_FORCING_SURFACE_CIME. No AD400 submissions.**
