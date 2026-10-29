# AmeriFlux MultiSite 10 — Batch 05

## Stage100 actual SUCCESS; operator PFT/soil research chosen; move to physical DATM and surface production (29 October 2026)

**Actual operator IRIDIS6 Stage100 SUCCESS:** `/home/ly3n24/ameriflux_batch05_directAD400_PFT_soil_surface/pft_soil_surface_scan_20261029T083355Z_3740913/`. All ten Batch05 entries in SHA-pinned 50-site scientific PFT prescription register have 15-slot host FATES model mapping candidates, all ten CLM10 depth soil records exist with mathematically valid sand/clay texture, and all ten have relevant original ZBOT/measurement-height table records. Soil source `/home/ly3n24/CLM_FATES_SOIL/AmeriFlux50_20261026/09_RECOMMENDED_CLM10_PCT_SAND_PCT_CLAY_WIDE.csv` SHA256 `ab142c12b7e200f0f65e9d04354c87acc6593af08373844ad5d9f2d008cc11b7`; height table `BASE_MeasurementHeight_20260908.csv` SHA256 `1c1e4171d295406a13d503f877b58661a651c88ffb6f0b6ec498f56bb1fcec5a`. Stage100 did not locate already-made surface files within its bounded site path search, and created none. **Operator explicitly states original PFT proportions have been thoroughly researched and the GitHub soil references are sufficient, so do not cycle into further PFT/soil literature verification**; use source-pinned existing recommended PFT/soil figures as **selected model input hypotheses**, retaining their original uncertainty/provenance notes (particularly the prefire static US-Vcm 2013 wildfire and Whs/Wkg HYDRO_SHRUB/bare=57/60). This is an operator modeling choice, not a claim that PFT fractions were all directly measured or that complete surface files already exist.

**Immediate remaining engineering work, not another PFT review:**
1. Adapt the proven complete full-record meteorological **production forcing construction** method from `Non-Competition-CLM-experiment/examples/AmeriFlux_Batch03_10/scripts/B3_01_direct_AD400_FIXNC_80x5.py` for these **exact ten Batch05 sites**, using original immutable FLUXMET/FULLSET source and Stage84 source-pinned 1,675 modified T/RH/VPD research rows. **No silent Stage89 separate 51 T/VPD preview merge**; independently select/approve before adding. Do not automatically feed 63 originally held source HH (56 humidity +7 temperature), invalid ERA-pair RH for 35 QC2 P1, or the 1,281 source-processed ERA humidity proxy HH into production forcing without a consistent explicit original source/uncertainty policy. Output NEW complete selected DATM year NetCDF with source clock, native half-hour/hour interval, NO_LEAP, UTC conversion, ZBOT, pressure, rainfall, radiation, wind, all seven model-required variables, source original/data source and full SHA manifests. Production forcing release is still BLOCKED pending unresolved science choices.
2. **Construct ten new site-specific point surfaces** (none currently found by bounded Stage100) from an approved unmodified CTSM gridded source and the selected already-reviewed host PFT/bare model hypotheses + CLM10 site-specific soil, using fresh Batch05 output paths. Maintain the private HYDRO_SHRUB FATES parameter map for Whs/Wkg, exact site coordinates and plant/natural landunit fractions. No need to redo user's completed PFT literature review; check **resulting NetCDF dimensions/physical inputs**.
3. **Prepare** (not submit) ten unique Batch05 FIXNC CIME startup cases with pinned selected DATM, surface and FATES params, `CLM_ACCELERATED_SPINUP=on`, `spinup_state=2`, `STOP_N=5`, `REST_N=5`, `RESUBMIT=79`, `RESUBMIT_SETS_CONTINUE_RUN=TRUE`, `DOUT_S=TRUE`. Reference successful Batch03 direct AD400 code, but never execute it unchanged because it hardcodes a **different cohort**. At real case.submit stage require Batch05 same-process stack >=65536 KiB and Slurm `PropagateResourceLimits=ALL/STACK`, ledger BEFORE first submit and archive/continuation check. **No pilot AD5, no Slurm submit during preparation.**

## Stage99 actual ten-site direct AD400 HPC readiness SUCCESS; Stage100 exact PFT/soil/height candidate audit ready (29 October 2026)

**User operator Stage99 second IRIDIS6 run SUCCESS:** `/home/ly3n24/ameriflux_batch05_AD400_full_preparation/preparation_20261029T082510Z_3687870/`. Native original-source folder/HH CSV present for **all ten Batch05 AmeriFlux sites**; 63 release-risk source HH have 5 affected-site original FLUXMET SHA verified in Stage90, unaffected 5 source SHA are **not** claimed as reverified by Stage90. Actual login6001 shell stack **300000 KiB → unlimited**; live Python soft/hard **unlimited**, minimum **65536 KiB**, Slurm `PropagateResourceLimits=ALL`, checks PASS. Verified existence of CTSM/FATES code + default parameters, NOAA annual CO2 table, original Batch02 ZBOT heights table and one candidate CLM10 ten-layer soil-wide table. Three prior **REFERENCE-ONLY** independent already-built AD400 CIME cases exist with executable, `use_fates_nocomp=true` and `spinup_state=2`: `CA-Ca3_AMF_FIXNC_AD400_UTC_V2_PTS_AD5`, `CA-TP4_AMF_FIXNC_AD400_UTC_V3_PTS_AD5`, `IT-Noe_B02_FIXNC_GPPNPP_HISTFIX_AD400`; no source/case reuse is permitted before exact scientific/equivalence audit. **No current Batch05-specific DATM NetCDF, PFT point surface or CIME case was found within Stage99 bounded paths** (0/10 for each), so actual production input construction/selection is outstanding. Stage99 observed shared-filesystem free blocks/inodes, **NOT the user's Scratch byte/inode quota**; explicitly check account quota before producing annual NetCDF, cases or logs. No source/QC/DATM/PFT/CIME/Slurm edits.

**Batch05 PFT candidate scientific catalog now compiled from pinned actual 50-site model-hypothesis register:** [exact ten site host and FATES fractions, provenance and science limitations](data/BATCH05_TEN_SITE_PFT_HYPOTHESES_SOURCE_PINNED_CANDIDATES_20261029.json). All proposed PFT fractions are **model hypotheses**, NOT verified full-tower ground area percentages; all retain `operator_model_surface_approval=NOT_APPROVED` and no surface/case writes. Initial recommended site PFT scenarios: US-UiD C3 20/C4 80 (unmeasured prior), US-UMB ENF 9/DBF 91 (2010 tree basal-area proxy), US-UMd ENF10/DBF90 (pretreatment prior), US-Var C3 100, US-Vcm ENF100 (**prefire ONLY 2007-2012**, 2013 wildfire, postfire PFT unverified), US-Vcp ENF100, US-WCr DBF100, US-Whs evergreen shrub20/drought-deciduous shrub20/C4 3/host bare **57%**, US-Wjs ENF26/C4 74 (BADM cover-complement prior), US-Wkg drought-deciduous shrub3/C4 37/host bare **60%**. US-Whs and US-Wkg **require HYDRO_SHRUB private FATES PFT mapping**, not the DEFAULT14 forest/grass mapping; host index0 bare is NOT itself an active FATES vegetation cohort. A static prefire ENF100 case cannot be described as observationally representative of the full postfire US-Vcm record without explicit design choice.

**Stage100 prepared (NOT yet operator-run):** [SHA-pinned ten-site scientific PFT/CLM10 soil/height/actual original-surface search code](scripts/AD400_direct_preflight/100_batch05_PFT_soil_surface_height_source_gate_READONLY.py) and [one-command IRIDIS6 runner](scripts/AD400_direct_preflight/run_stage100_batch05_PFT_soil_surface_height_science_gate_iridis6.sh). It reads the original pinned 50-site register, confirms all ten host and FATES proportions (including bare 57/60), checks present CLM10 sand/clay source rows and actual ZBOT height table schema, searches bounded site subdirectories for pre-existing original `surfdata*.nc` point surfaces and, if `netCDF4` is available, their host natpft/soil/landunit variable schema. It emits precise source candidates and uncertainty/status into **NEW HOME reports only**; it does not produce, overwrite or approve a production Batch05 surface, DATM NetCDF, FATES private parameter or CIME case. The next technical construction, after actual Stage100 source results, is site-specific versioned surface/PFT and complete selected meteorological forcing proposals, verifying all scientific HOLDs before production release.

**Direct AD400 design stays fixed:** ten per-site independent startup accelerated CIME cases, `STOP_N=5`, `REST_N=5`, `RESUBMIT=79` -> **80×5 = 400 years from one submit per site**, no separate AD5 trial. At actual future case.submit, enforce `batch05_direct_ad400_stack_guard.require_for_submission` **within the very same submitting Python process**, preserve high/unlimited stack, verify Slurm ALL/STACK propagation, persist ATTEMPTED receipt first, check quota/inodes and restart/archive. **MODEL RELEASE REMAINS BLOCKED** until complete science/forcing/PFT/soil/CIME input gates pass. Stage99 success alone does not authorize Slurm submission.

## Stage99 first HPC attempt: stack/Slurm PASS; exact five-site Stage90 SHA manifest guard corrected (29 October 2026)

**Actual operator Stage99 first run [partial, no model writes]** from login6001 reported shell stack **300000 KiB → unlimited**, Python RLIMIT_STACK **soft=unlimited/hard=unlimited**, and live Slurm **`PropagateResourceLimits=ALL`**, so STACK inheritance resource precheck passed. Both SHA-pinned source files, Python syntax and synthetic preflight self-tests passed; original source/QC/DATM/surface/CIME/Slurm remained untouched. The subsequent inventory stopped before writing the final report due to a **Stage99 source-manifest schema/scope assertion bug**, not new physical science evidence: Stage90's ten-site risk study processed **63 unique risk HH at five affected sites** (US-Vcm, US-Vcp, US-WCr, US-Wjs, US-Wkg) and explicitly stores SHA fingerprints for ONLY THOSE FIVE site source files. The original Stage99 source mistakenly demanded ten Stage90 source SHA entries, despite five other sites having no original release-risk records.

**Corrected Stage99 code** [direct AD400 technical preflight](scripts/AD400_direct_preflight/99_batch05_real_path_surface_datm_case_stack_and_quotas_READONLY.py) now requires the **exact five affected site names and pinned Stage90 original source SHA hashes**, the actual Stage90 63 unique source-risk records, Stage90 original-source/approved-overlay science counts, and the original risk output CSV SHA. It faithfully labels the other five `NOT_HASHED_IN_STAGE90_NO_ORIGINAL_RISK` rather than claiming Stage90 verified every site SHA again. The other five had been checked by earlier stages, but that is separate provenance. The [SHA-pinned Stage99 runner](scripts/AD400_direct_preflight/run_stage99_batch05_full_HPC_AD400_stack_surface_DATM_case_inventory.sh) was updated to fetch the corrected code. **This change neither relaxes original risk-source validation nor modifies any prior Stage90 results.** User rerun required before presenting a Stage99 SUCCESS or full ten-site inventory.

The **future** direct AD400 submit controller still must re-check stack inside its own actual case.submit Python process and preserve inherited Slurm limits; a separate successful standalone preflight is not alone proof of an actual submitted job's stack. Scientific release remains BLOCKED until approved forcing, original HOLD policies, PFT/soil/surface and CIME cases are ready. **No AD400 jobs submitted.**

## Stage97+Stage98 actual SUCCESS and Batch05 direct AD400 full preparation — Stage99 stack/HPC audit ready (29 October 2026)

**Operator decision: PREPARE ALL TEN FIRST; DIRECT AD400 400 years, NOT standalone AD5 smoke, with one submit per site after fully verified inputs.** Stage97 actual IRIDIS6 success: **56** original P1/RH-platform source HOLD HH precisely split **35+10+1+4+6** in **ten contiguous original source episodes**, report `/home/ly3n24/ameriflux_batch05_stage97/original_56_holds_five_science_groups_20261029T075507Z_3517881/`. Exact 35 QC2 source-negative RH also negative in the *same source processed-ERA* humidity pair; do not use identical invalid source ERA for repair. No approval to override original HOLD.

**Stage98 actual IRIDIS6 direct AD400 readiness SUCCESS (READ-ONLY)**: ten original site sources present; original P2/P3 1,574 dispositioned, research overlay 1,675 source SHA preserved, US-Whs separate 51 T/VPD preview preserved. **1,281 research ERA-proxy HH NOT independently production validated**. Original risk **46 P1, 10 RH platform, seven T source anomalies** remain. All ten sites showed **zero** candidate production DATM, surface and Batch05 CIME cases at Stage98's *limited search paths*, not proof of universal nonexistence. Stage98 report `/home/ly3n24/ameriflux_batch05_directAD400_preflight/readiness_20261029T080621Z_3578563/`. Its gate **`BLOCKED_PRODUCTION_SCIENCE_FORCING_SURFACE_CIME`** is correct, not permission to submit.

**Stage99 new full ten-site HPC technical preflight prepared (NOT operator-run):** [SHA-pinned standalone launcher](scripts/AD400_direct_preflight/run_stage99_batch05_full_HPC_AD400_stack_surface_DATM_case_inventory.sh), [read-only inventory](scripts/AD400_direct_preflight/99_batch05_real_path_surface_datm_case_stack_and_quotas_READONLY.py) and [Batch05 specific stack guard](scripts/AD400_direct_preflight/batch05_direct_ad400_stack_guard.py). It inspects real source and possible DATM/surface path locations, prior reference-only successful Batch01–04 CIME cases/parameters, source soil/ZBOT and CO2 candidates, Scratch/RFS free blocks and inode counts, live Slurm scheduler status and **RLIMIT_STACK 65536 KiB minimum** / Slurm propagation of STACK or ALL. **Any actual future AD400 submission must call the Batch05 guard inside the *same* Python process as `case.submit`**, with an ATTEMPTED ledger *before* real submission; running a standalone guard does not protect a different subsequent process. Never lower a higher/unlimited stack. No files in original/forcing/surface/CIME/Slurm are changed by Stage99.

**Detailed cross-batch method and release specification:** [Direct AD400 Batch05 science, DATM, PFT/soil, FATES, stack/Slurm and CIME preparation requirements](docs/DIRECT_AD400_BATCH05_PREPARATION_AND_PRE_SUBMIT_GATES_20261029.md). References actual scripts from Batch01 Lane A, Batch02 direct IT-Noe AD400, Batch03 PFT and early ESMF stack failure, AmeriFlux Batch03 DATM readiness, and AmeriFlux Batch04 validated resource propagation guard. Intended fresh independent ten Batch05 FIXNC accelerated cases: `RUN_TYPE=startup`, `CLM_ACCELERATED_SPINUP=on`, private checked `spinup_state=2`, `STOP_N=REST_N=5`, `RESUBMIT=79`, `RESUBMIT_SETS_CONTINUE_RUN=TRUE`, **80×5 years from one site submission**. No separate five-year smoke/pilot or Normal phase. Archiving, Slurm walltime/stack, all seven meteorological DATM variables, native source clocks and selected original site PFT/soils/height must be independently verified before creating/sending the real submitter.

**Still BLOCKED:** No model-ready selected complete forcing, scientifically released 56 source original HOLD cases, independent proxy-ERA source/uncertainty validation or fully source-pinned 10 surface/CIME cases have been demonstrated. Do not fabricate approval or submit any Slurm case on Stage99 alone.

## Direct AD400 requested (no AD5 pilot): Stage97 actual 56 HOLD episode results and Stage98 ten-site readiness (29 October 2026)

**Updated operator runtime decision:** **DIRECT accelerated AD400 year spinup for all ten Batch05 original AmeriFlux sites. No standalone AD5 test run, no NORMAL5 prerequisite.** As proven in prior independent Batch02 workflows, configure one properly checked startup CIME AD400 case **per site** (not one shared case) with `STOP_OPTION=nyears`, `STOP_N=5`, `REST_OPTION=nyears`, `REST_N=5`, `RESUBMIT=79`, `RESUBMIT_SETS_CONTINUE_RUN=TRUE`, `CLM_ACCELERATED_SPINUP=on`; this is **80 chained five-year chunks = 400 years from a single per-site submission**. Dividing the job chain into 5-year checkpoint segments is not an AD5 pilot. **Do not submit yet:** science/complete input preparation and CIME case audits are separate required release gates.

**Stage97 actual IRIDIS6 SUCCESS:** `/home/ly3n24/ameriflux_batch05_stage97/original_56_holds_five_science_groups_20261029T075507Z_3517881/`. The exact **56** original manually protected P1/saturation-platform HH belong to **10** contiguous original-native science episodes (zero source/approved-overlay modifications): **35** original source QC2 T/VPD RH-negative in US-Vcm (32) and US-Vcp (3), original processed source ERA pairs identical and likewise RH-negative so cannot be substituted as source humidity; **10** original source P1 RH-positive but low and two-sided source QC0 donors missing, **one** such P1 case with both donors, **four** US-Vcm original ~99.46% RH, and **six** US-WCr original exactly 100% RH. The group-specific action plan is to retain HISTORICAL HOLD and either obtain genuine independent source meteorology and justification, or explicitly adopt documented conditional masking/gapfill/exclusion policy; DO NOT silently use invalid processed ERA humidities, overwrite source QC, or declare source historical HOLDs approved. The seven source-T anomalies documented by Stage90–95 remain separate. All 63 source risk HH are mutually distinct, with zero overlap between historical 56 and Stage89 separate 51.

**Stage98 direct AD400 readiness inventory [prepared, NOT yet operator-run]:** [read-only ten-site Python](scripts/AD400_direct_preflight/98_batch05_ten_site_direct_AD400_science_and_case_preflight_READONLY.py) and [SHA-pinned one-command IRIDIS6 launcher](scripts/AD400_direct_preflight/run_stage98_batch05_ten_site_direct_AD400_readiness_iridis6.sh). Verifies actual Stage84 immutable **1,675 versioned research RH/VPD/T repair** SHA256 `63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce`, Stage86 ten-site original P2/P3 **1,574/1,574 dispositioned**, Stage89 independent US-Whs **51 T/VPD/RH PREVIEW** SHA256 `95aefd6027e6f981ac821266bc379b89d9f1299d1c307b7575a17fec65588561`, Stage90 original 63 source-release-risk HH and Stage97 actual 56 HOLD/10 contiguous events. It **inventories** per-site original CSV presence (does not redundantly hash all large raw site CSVs again), nearby candidate DATM/surface files (presence is **not approval**) and *Batch05-named* independent CIME cases (other batch case names are explicitly excluded). Reports each site's intended direct AD400 start-year and end-year. **Strictly READ ONLY:** never creates, edits or submits cases, forcing, surfaces, CIME, Slurm; its `direct_AD400_submit_permission` is False by design until the separate full science/inputs/case release audits have passed.

**Must prepare and pass before any direct AD400 submit:**
1. Decide the scientific outcome of 56 historical P1/platform HOLDs (independent humidity reconstruction or explicitly permitted masking/gapfill/exclusion), seven original T exceptions, and verify the source-processed ERA RH proxy repair uncertainties. The mere presence of a numerically physically consistent 1,675-row research overlay does not validate its independent meteorological origin.
2. Build **NEW complete, versioned ten-site meteorological DATM forcing files**, keeping original source/quality labels immutable and preserving the exact native source clock, timestamps and cycle boundaries, source lineages, units, QC0/1/2 measurement source and model thermodynamics. This work is **not yet established as completed or model-ready**.
3. Verify suitable ten-site PFT/bare/soil and point-surface configuration, source coordinates, heights, single-site grid/coupling, FATES no-competition design and carbon/CO2 spinup config against the existing cross-cohort method (never assume a surface inherited from another experiment is scientifically identical). PFT and soil provenance must be audited before using or creating production cases.
4. Create **ten uniquely named Batch05 AD400** CIME cases with the intended original per-site dates (US-UiD 2008; US-UMB 2007; US-UMd 2007; US-Var 2000; US-Vcm 2007; US-Vcp 2007; US-WCr 1999; US-Whs 2007; US-Wjs 2007; US-Wkg 2004). Each must use **one direct AD400 submit, 80 × 5-year segments, 79 automatic resubmissions**, full verified stack >=65536 KiB and **attempt ledger written before the one CIME case.submit call**; never resubmit blindly on an uncertain error. No Normal stage is requested.
5. Pre-submit check 10/10 exact site stream paths, source SHA/selected forcing fingerprints, 1x1 PFT/surface, build executable, `RUN_TYPE=startup`, `CLM_ACCELERATED_SPINUP=on`, `STOP_N=5`, `REST_N=5`, `RESUBMIT=79`, `RESUBMIT_SETS_CONTINUE_RUN=TRUE`, restart/archive dependence, scratch quota/inodes, and remaining science-gate status; only then request explicit execution authorization for the one-submit-per-site AD400 rollout. Note that user has already specified **direct AD400**, so do not reintroduce a 5-year trial.

**Status as of Stage97:** Source anomaly triage advanced, but **production forcing release remains blocked** due to 56 protected original source HOLD HH, seven temperature uncertainties and source ERA humidity proxy scientific reliability; ten selected DATM/surface/CIME cases have not been demonstrated ready. Do not claim AD400 submitted or completed.

## Stage96 actual SUCCESS: 56 historical P1/platform source HOLDs classified; Stage97 compact release policy group review (29 October 2026)

**Actual operator IRIDIS6 Stage96 SUCCESS** source evidence `/home/ly3n24/ameriflux_batch05_stage96_P1_platform/three_sites_P1_46_platform10_20261029T075010Z_3490715/`. Exact immutable Stage63/90 source HOLD ledgers, original Stage05 three-site source SHA fingerprints and the Stage84 protected **1,675** main research overlay SHA256 `63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce` verified; **no original/QC/prior-1675/DATM/CIME/Slurm writes**. All **56 distinct original RH science HOLD half-hours** precisely classified and still HOLD:

| Source group | Native HH | Observed source/reanalysis science decision |
|---|---:|---|
| Original P1 negative or unassessable physical RH | **35** | **US-Vcm 32, US-Vcp 3**; source original T and VPD QC2, derived original RH negative. The same native processed-source ERA T/VPD humidity pair reproduces the **same negative RH**, therefore **do not reuse it for replacement**; needs independent meteorological reference/gapfill policy. |
| P1 original RH low but positive, missing two-sided native VPD_QC0 physical RH donors within ±2h | **10** | US-Vcm 2015-12-06 04:30–09:30 (one source row on that day has donors); original T/VPD QC0 and source implied RH ~0.07–0.63% in these ten no-donor cases, source-processed ERA RH differs; requires actual source-level physical evidence; does **not** license arbitrary ERA substitution. |
| P1 original RH positive, valid both-sided native VPD_QC0 RH anchors within ±2h | **1** | US-Vcm 2015-12-06 09:30 original T/VPD QC0 RH ~0.722%, processed source ERA RH ~20.716%, still manual HOLD pending original nearby context and independently grounded meteorological interpretation. |
| RH saturation/platform original Vcm | **4** | `2025-10-14 12:00–13:30`, source original RH ~99.458–99.463%, T/VPD QC0; consecutive platform-like near-saturation, **physically possible** but needs plateau sensor/provenance review, not a 100% numeric failure. |
| RH saturation/platform original WCr | **6** | `2025-08-25 09:30–12:00`, original VPD=0.0 hPa and derived RH **exactly 100%** for six consecutive HH, original T/VPD QC0 while processed-source ERA RH only ~66.5–81.0%; could be sustained near saturation or source sensor plateau. Do **not** replace automatically with drier ERA. |

**Stage96 five historical class totals:** 35 source RH negative/unassessable, 10 P1 low-positive RH without both measured donors, one P1 low-positive RH with both measured donors, four Vcm ~99.46% platform and six WCr exact RH100 platform; site breakdown US-Vcm 43 P1 +4 platform, US-Vcp 3 P1, US-WCr six platform. Stage96 zero repair approvals and no model forcing release. In particular, source processed ERA RH is **invalid for the 35 QC2 cases**, unlike many separately approved earlier Stage84/86 proxy-replacement rows; do not assume reliability transfers across episodes.

**Stage97 prepared [not operator-executed]:** [five-group original 56 HOLD science decision audit](scripts/stage97/97_batch05_56_holds_five_science_groups_episode_decision_matrix_READONLY.py) and [SHA-pinned one-command IRIDIS6 launcher](scripts/stage97/run_stage97_56_holds_science_episode_gate_iridis6.sh) reuse actual Stage96 original SHA-manifest report, group the 56 source-native timepoints into **contiguous issue episodes** and generate a five-group per-site science decision/release-policy matrix without copying the source ERA negative RH or overriding original quality HOLD. The expected group counts are strictly checked as **35+10+1+4+6=56**; actual number of time-contiguous episodes is intentionally computed rather than guessed. It is an evidence and research-release policy triage, **not** source T/VPD/RH replacement and not a model-ready DATM forcing production authorization.

**Remaining before full release:** original source P2/P3 1,574 fully dispositioned; main 1,675 research numeric corrections science/physics verified; separate Stage89 Whs 51 T+VPD preview physical. Only a relatively small set of workstreams remains, but **the 56 original manual HOLD records, seven original T-source exceptions and broad source-product ERA-humidity proxy validation still gate forcing**. Prioritize group-level science decisions/independent reference checks, then a global forcing-preflight and short model run; do not prolong the previous 56-record source anomaly screening repeatedly.

## Stage95 actual original US-Wkg ZIP provenance SUCCESS; Stage96 46 P1 +10 RH-platform HOLD review next (29 October 2026)

**Operator Stage95 actual IRIDIS6 SUCCESS** (`/home/ly3n24/ameriflux_batch05_stage95_Wkg/Wkg_archive_lineage_20261029T073438Z_3402450/`) read the **original SHA-pinned US-Wkg 2004–2025 FLUXNET ZIP**, original BIFVARINFO_HH provenance, README, ERA5_HH and native original FLUXMET source. Original ZIP SHA256 **`d9c31372ad29fa79946a97ac30eb02ad679b261f0b925db97ef88cf6b325221e`**; prior Stage84 main **1,675** research-approved RH/VPD/T source overlay SHA256 **`63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce`** protected throughout. The native product `P_F` BIF definition explicitly states **precipitation is consolidated from `P` and `P_ERA`, with original measured `P` used if available, in mm per dataset sampling interval** (here half-hour). The original **`P=P_F`** at `2025-09-10 12:30` is **11.049 mm**, at `13:00` **1.524 mm**, total **12.573 mm** in two adjacent half-hours (one hour) with **`P_F_QC=0` measured-source**, while the packaged original ERA5 `P_ERA=0` at both slots. That supports a native reported rainfall event but **does not independently verify instrument behavior, calibration, physical rainfall amount, or temperature sensor wetting**.

Original source at `2025-09-10 13:00`: `TA_F=TA_F_MDS=12.89°C`, `TA_F_QC=0` per original BIF means source measured, but NOT a scientifically validated abrupt transient; `RH=-9999` is **missing** (its previously reconstructed 43.444% RH is not a center-time tower measurement). BIF definition `TA_F` consolidates `TA_F_MDS` and `TA_ERA`, using `TA_F_MDS` if `TA_F_MDS_QC` is 0 or 1. `TA_F_MDS` is therefore the *same source temperature*, not independent corroboration. Product processed `TA_ERA=29.396°C`, packaged `ERA5_HH` independently matches this archived processed companion, but is **not an independent tower sensor**. The same ZIP BIF model metadata identifies `[TA] TEMP-ElectResis` and `[RH] RH-Capac` measurement technologies, without providing a second independent T time series. Original source immediate QC0 temperatures `29.52°C` before and `23.47°C` after; derived midpoint **26.495°C** remains **nonapproved** because source neighbors differ by 6.05°C during the reported storm and the original T/QC transient remains potentially physical or instrumental. **Disposition after Stage95: preserve source T 12.89°C and currently approved numerical RH/VPD for research provenance, flag source-T uncertainty, do NOT automatically substitute the 26.495°C QC0 midpoint or 29.396°C ERA value; model-ready forcing remains HOLD until explicit uncertainty policy or independent source evidence.** Original source, QC, prior1,675, DATM/CIME, Slurm unchanged.

**Next Stage96 (prepared; operator not yet run):** [SHA-pinned original-source P1/platform 56 HH read-only audit](scripts/stage96/96_batch05_P1_46_platform10_native_source_qc_review_READONLY.py) and [one-command IRIDIS6 launcher](scripts/stage96/run_stage96_46P1_10RHplatform_iridis6.sh). Revalidate exact historical Stage63 **46 original P1 manual HOLD HH + ten RH-saturation platform HOLD HH**, Stage90 **63 distinct original release-risk HH** source crosswalk, and Stage84 protected **1,675** main research overlay. Original site-native FLUXMET raw-file SHAs pinned at three sites: **US-Vcm** (43 P1 +4 RH platform), **US-Vcp** (3 P1), **US-WCr** (6 RH platform). For all **56 distinct HOLD source-native times**, report original source T/VPD/QC, original RH source field, derived original RH, processed source ERA humidity proxy, original VPD_QC0 physically valid RH anchors both sides within two hours, and native ±2h context; separate platform sustained high RH from P1 physical anomalies. Preserve all historical HOLD designations, all source QC and approved research overlays; **do not automatically approve any 56 or substitute ERA humidity proxy**. Stage96 data analysis still requires actual operator IRIDIS6 run before findings can be accepted.

**Batch05 status:** P2/P3 all **1,574** original source HH dispositioned; main **1,675** versioned research repairs numerically physical, separate Stage89 US-Whs 51 T+VPD preview numerically physical. Outstanding original records: **63** distinct source risk HH (46 P1, 10 RH-platform, seven source-T), PLUS independent reliability assessment of source-processed ERA humidity-proxy methods. Scientific source audit is substantially advanced, but model-ready DATM forcing **release gate remains BLOCKED**. Source QA evidence is not interchangeable with independent observation confirmation.

## Stage94 actual original US-Wkg source companion audit SUCCESS; Stage95 ZIP BIFVARINFO/ERA5 provenance next (29 October 2026)

**Stage94 actual user operator IRIDIS6 SUCCESS** (`/home/ly3n24/ameriflux_batch05_stage94_Wkg/original_Wkg_source_companions_20261029T072933Z_2405803/`) revalidated source-US-Wkg immutable original FLUXMET HH SHA and Stage93/Stage84 protected original/main **1,675 HH** research overlay. At `2025-09-10 13:00` source original **TA_F=12.89°C QC0**, **TA_F_MDS=12.89°C identical to TA_F**, **TA_ERA=29.396°C** (FLUXNET processed original-source ERA companion, not second independent tower sensor), **VPD_F=18.952 hPa QC1**, and **RH=-9999 (missing)**. Thus neither TA_F_MDS nor the missing RH independently resolves the physical source T controversy. Source original precip `P_F` at `12:30` **11.049**, `13:00` **1.524**, `13:30` **0.0**, with original `P_F_QC=0`; source product `P_ERA=0.0` at 12:30/13:00. In the user's Stage94 optional native-source rows, **raw original `P` equals `P_F`** at both 12:30 (11.049) and 13:00 (1.524), each `P_F_QC=0`, whereas `P_ERA=0.0`; this strengthens evidence that the precipitation values come from a reported native source rather than only an ERA fill, but does not independently verify physical rain, gauge performance, or units. Product precipitation units and variable provenance remain to be checked in original BIFVARINFO/README. Shortwave `SW_IN_F` 228.3/591.7/434.9 over those times, abrupt original TA_F `−16.63°C` then `+10.58°C`. Previous Stage93 **both immediate TA/VPD original QC0** humidity donors and alternative candidate T 26.495°C are *research diagnostics only*, not user-approved T replacements. No source/QA/1,675-model forcing/DATM/CIME/Slurm changes.

**Original ZIP inventory observed Stage94:** `AMF_US-Wkg_FLUXNET_FLUXMET_HH_2004-2025_v1.3_r1.csv`, `AMF_US-Wkg_FLUXNET_ERA5_HH_1981-2025_v1.3_r1.csv`, `AMF_US-Wkg_FLUXNET_BIFVARINFO_HH_2004-2025_v1.3_r1.csv`, `README.txt`, and product temporal aggregation/license members. Packaged `ERA5_HH` is another reanalysis-data view **not an independent observational tower temperature sensor**. Source-native actual `RH` missing at event, no `TA` or `TA_PI_F` columns; a second observed air-temperature channel has **not** yet been verified.

**Stage95 prepared [not yet operator-run]**: [read-only original ZIP BIFVARINFO metadata and packaged ERA5 source audit](scripts/stage95/95_US_Wkg_20250910_archive_BIFVARINFO_ERA5_lineage_READONLY.py), [SHA-pinned one-command IRIDIS6 launcher](scripts/stage95/run_stage95_US_Wkg_20250910_original_zip_BIF_ERA5_iridis6.sh). Revalidates Stage94 25 native HH and protected Stage84 SHA, computes original ZIP SHA, reads `BIFVARINFO_HH` and `README.txt` for precipitation `P/P_F/P_F_QC/P_ERA` and temperature `TA_F/TA_F_MDS/TA_ERA` variable definitions, then reads only three relevant half-hours from `ERA5_HH` (if explicit timestamp column is present). Records units verbatim when available, not by assumption. Displays original `P` versus `P_F` versus reanalysis `P_ERA`; scientific source-rain / instrument ambiguity remains HOLD pending genuinely independent evidence or a documented release policy. No automatic source T change, no source/QC/model forcing or 1,675 research overlay writes, no Slurm.

**Batch05 release readiness:** The original P2/P3 1,574 HH source science triage is closed, original 1,675 main versioned numeric research repairs are physically consistent, and the separate 51 US-Whs T+VPD preview passed. Nonetheless 63 distinct source-risk half-hours remain (46 P1 manual HOLD, 10 RH saturation-platform HOLD, seven T source exceptions), plus reliability questions for source product processed-ERA humidity-proxy interventions. Do not conflate scientific numerical pass with permission to generate production DATM forcing.

## Stage93 actual US-Wkg September storm source context SUCCESS; Stage94 original companion provenance check (29 October 2026)

**Stage93 actual user IRIDIS6 SUCCESS** (`/home/ly3n24/ameriflux_batch05_stage93_Wkg/Wkg_Sep2025_T_QC0_context_20261029T072420Z_3346776/`) verified original US-Wkg `2025-09-10 13:00` FLUXMET source SHA and native 49 half-hour context, Stage92 source alignment, and Stage84 approved research **1,675** overlay exact SHA256 `63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce`. Center original T **12.890°C QC0**, original VPD **18.952 hPa QC1**, source-processed companion ERA T **29.396°C**, ERA-pair RH **22.686%**. Immediate original QC0 T **29.520°C** at 12:30 and **23.470°C** at 13:30 (temperature midpoint **26.495°C**, with 6.050°C donor disagreement). Crucial meteorological context: native `P_F` values **11.049** at 12:30 and **1.524** at 13:00 (do not assert units until original product metadata establishes them), accompanied by highly variable shortwave `SW_IN_F` **228.3**, **591.7**, **434.9** at 12:30, 13:00 and 13:30 respectively. There is evidence for an active precipitation/radiation event; this creates ambiguity between a genuine rapid temperature transient and instrumentation/QA artifact. Original same-source T drops **16.630°C** from 12:30 to 13:00 then rises **10.580°C** by 13:30; direct automatic replacement is **NOT justified** without further source quality/independent temperature evidence.

**Stage93 source-QC0 moisture diagnostics:** both immediate original T_QC0 / VPD_QC0 donors have derived physical RH; center previously approved research `T=12.890°C, VPD=8.403669668 hPa, RH=43.444307565%`. Candidate T **26.495°C** with VPD **unchanged** leads RH **75.721238800%**; retaining approved RH instead yields candidate VPD **19.575766373 hPa**; directly interpolating original VPD_QC0 donors (29.693 and 11.908 hPa) gives **20.800500000 hPa** and RH **39.905970571%**. The thermodynamic RH-preserving and direct-VPD interpolation pathways differ **1.224733627 hPa** (unlike Stage88's stable <0.05 hPa cases), consistent with unstable meteorology during rain. The already approved 43.4443% humidity is numerically identical to immediate two-sided QC0-inferred RH midpoint, but remains an interpolation, **not a measured center RH**. No source/QC/approved 1,675/DATM/CIME/Slurm writes or source temperature changes.

**Stage94 prepared but not yet operator-executed:** [source-native companion / potential original source-package metadata audit](scripts/stage94/94_US_Wkg_20250910_original_source_alternative_fields_precip_provenance_READONLY.py) and [SHA-pinned IRIDIS6 one-command launcher](scripts/stage94/run_stage94_US_Wkg_20250910_source_companions_iridis6.sh) reverify Stage93 original 49 HH and source/previous 1,675 immutable SHAs; then inspect any actually present Wkg source-native alternate T/QC/RH, P/RH/radiation companion fields and list any optional original archive member names that might contain separately sourced station/tower observations. Explicitly report if alternative fields or source package are absent; **do not infer they exist, are independently measured or are reliable**. Inspect ±6h native source meteorology and precip/radiation, with **no source data, source QC, approved research overlay, DATM/CIME or Slurm changes**. Original `P_F` unit provenance remains unverified until product metadata supplied.

**Current overall release gate remains blocked:** 10 original AmeriFlux sites have P2/P3 1,574 HH completely dispositioned, research numerical main 1,675 valid under Stage86; 63 distinct remaining originally flagged scientific risk records (46 P1 manual HOLD; 10 RH plateau; seven source T anomalies) and processed-source-ERA RH proxy uncertainty require separate qualified scientific decisions. A "passed" read-only stage is **not** a complete model-ready forcing release.

## Stage92 actual seven-source-T 12h original evidence SUCCESS; Stage93 US-Wkg September source physics (29 October 2026)

**Actual user IRIDIS6 Stage92 SUCCESS:** `/home/ly3n24/ameriflux_batch05_stage92_T/seven_T_extended_source_20261029T071754Z_3310751/`. Original source FLUXMET CSV SHA verified for four sites (US-Vcm, US-Vcp, US-Wjs, US-Wkg), with **seven** original TA_F-QC0 source temperature exception timepoints independently checked against the native **±12-hour** time window; **0 automatic T repairs**, previous **1,675** research RH/VPD/T versioned repairs preserved at SHA256 `63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce`, and Stage90/91 provenance intact. Actual evidence classification: `NEAR_QC0_BRACKET_RETAIN_ORIGINAL_T_CANDIDATE=1`, `SOURCE_T_REVIEW_UNRESOLVED_NO_AUTOMATIC_REPLACEMENT=4`, `TWO_QC0_SOURCE_T_DONORS_DISAGREE_NEEDS_LOCAL_CONTEXT=1`, `STRONG_ORIGINAL_T_OUTLIER_EVIDENCE_T_QC0_AND_SOURCE_ERA_AGREE_NEEDS_LOCAL_APPROVAL=1`.

- **Strongest T science hypothesis**: US-Wkg `2025-09-10 13:00`, original native T **12.890°C QC0**, adjacent original QC0 T **29.520°C at 12:30** and **23.470°C at 13:30**. Bracketed midpoint **26.495°C**, source T **13.605°C below** midpoint. Same original AmeriFlux product processed ERA companion T **29.396°C** (not independently retrieved ERA5-Land). Neighbors differ by **6.05°C in an hour**, so exact source T bias plausible but no automatic interpolation/production forcing approval.
- **Nearest-QC0 source T consistency suggests retain original candidate**: US-Wjs `2025-04-19 16:00`: original **1.032°C QC0**, source QC0 bracket midpoint **1.0835°C**, discrepancy **−0.0515°C**. Neighboring source QC1 temperatures around 10–12°C contradict original QC0 pair; humidity/VPD source validity remains distinct.
- **Other five source T cases not independently settled**: US-Wkg `2025-03-07 12:30` original −4.120°C vs 1h QC0 mean −1.3275°C (source processed ERA +9.902°C): don't substitute processed ERA T; US-Vcm `2014-09-06 23:30` original 2.978°C vs far original QC0 bracket candidate 7.0288°C, donor difference 7.819°C; US-Vcp `2008-05-22 15:30` original 0.487°C vs remote native QC0 midpoint 2.1649°C; US-Vcp `2014-04-26 23:30` original −8.941°C vs remote midpoint −3.1326°C; US-Wjs `2022-03-31 03:30` original −5.946°C vs original QC0 midpoint −0.5262°C. All original TA/VPD/QC unchanged; no automatic source T approval.

**Stage93 prepared; not yet operator-run**: [SHA-pinned read-only source audit](scripts/stage93/93_US_Wkg_20250910_T_VPD_native_QC0_local_physics_READONLY.py) and [IRIDIS6 one-command runner](scripts/stage93/run_stage93_US_Wkg_20250910_local_original_QC0_iridis6.sh) focus on the single strongest source-T hypothesis at US-Wkg 2025-09-10 13:00. Revalidate exact Stage92 49 original native HH and Wkg original FLUXMET SHA, compare native original T and VPD/QC, shortwave, precipitation and processed-source ERA, report ±6h native context, and independently show **counterfactual** T/VPD/RH scientific sensitivities for original source T, nearest-two original-QC0 midpoint T, old approved VPD or old approved RH, and if appropriate actual two-sided original source VPD-QC0 RH/VPD donor constraints. Explicitly fail closed on source SHA and prior 1,675 approved overlay drift. **No source data, QC labels, prior main research overlay, model forcing, DATM/CIME or Slurm changes.** Stage93 output does not constitute user-science approval for source T or T/VPD/RH forcing promotion.

Batch05 remaining release-gating provenance: original P2/P3 source screened 1,574 native HH entirely dispositioned; separate **63 distinct scientifically flagged source risk HH** (46 historical P1 HOLD, 10 original RH plateau, seven unresolved source-T exceptions) plus substantial *source product processed ERA humidity-proxy* repair uncertainty. Publication/model forcing **remains BLOCKED** pending source-science resolution and independent validation; research overlay physical consistency of 0 errors does not establish full model meteorology realism.

## Stage91 actual 7 original-source T science screens; Stage92 extended original context prepared (29 October 2026)

**Actual operator IRIDIS6 Stage91 SUCCESS:** `/home/ly3n24/ameriflux_batch05_stage91_T/seven_T_original_QC0_source_20261029T071238Z_2351612/`. All **seven** original TA_F_QC0 anomalous source half-hours remain numerically T-unchanged in the validated Stage84 1,675 approved research RH/VPD/T overlay, consistent with earlier deliberate preservation of source-T source uncertainties. Strict original source SHA/crosswalk and Stage90 63 risk records validated. **Zero** of seven pass the conservative automatic source-T interpolation gate: **four** have NO original measured/native QC0 T anchors on both sides within ±3h (US-Vcm 2014-09-06 23:30; US-Vcp 2008-05-22 15:30 and 2014-04-26 23:30; US-Wjs 2022-03-31 03:30). **Two** have both native QC0 T donors but fail the current ≥8°C original-T outlier threshold: US-Wjs 2025-04-19 16:00 source T=1.032°C versus midpoint 1.0835°C (difference −0.0515°C, strong reason to consider keeping original T), and US-Wkg 2025-03-07 12:30 source T−4.120°C versus QC0 donors −1.708/−0.947°C (midpoint −1.3275°C, original minus midpoint −2.7925°C; needs targeted source physics judgment). **One** US-Wkg 2025-09-10 13:00 source T=12.890°C against immediate native measured QC0 donor T=29.52/23.47°C; midpoint **26.495°C** and source-minus-midpoint **−13.605°C**, original source-processed ERA T=29.396°C, but donor differences **6.05°C** exceed the 5°C stability gate; **prioritize targeted review, not automatic approval**. Original source temperatures are labelled source QC0, but code never assumes that proves their physical correctness. None of these data alone warrant relabeling source QC or declaring source-ERA T an independent measurement.

**Stage92 prepared, not yet actual HPC-run:** [read-only original source Python](scripts/stage92/92_seven_temperature_exceptions_extended_original_native_day_context_READONLY.py) and [SHA-pinned one-command IRIDIS6 launcher](scripts/stage92/run_stage92_seven_T_extended_12h_original_native_iridis6.sh). Rechecks the actual Stage91 science 4/2/1 classification and Stage90/84 original identity + approved main 1,675 SHA `63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce`, and then validates original Stage05 native FLUXMET SHA and source T/VPD/QC/ERA for the four affected sites (Vcm, Vcp, Wjs, Wkg). Examines the full **±12-hour native original context** around seven timestamps (not only ±3h), shows 30-minute immediate neighbors, nearest genuine QC0 original T donors within 12h, source-ERA difference and T–VPD–RH sensitivity for each. Distinguishes potentially trustworthy original-T values from strongly suspect spikes and unsupported intervals, but **no numerical T modification is approved or written**, and no production forcing/DATM/CIME/Slurm is touched. This is a targeted science decision aid, not another wholesale P2/P3 screen.

**Separate remaining release controls** remain 46 historically held P1 HH (43 Vcm, 3 Vcp), 10 original RH saturation-platform HH (4 Vcm, 6 WCr), source-processed ERA humidity proxy reliability, and all seven original temperature source exceptions until independently resolved/explicitly retained with a justified uncertainty policy. Stage90 confirms these 63 release-risk native keys are mutually distinct; none overlap Stage89 separate 51 Whs TA/VPD science preview. Main 1,675 numerical research repair physical consistency was independently validated Stage86 at zero issues; this does not certify complete forcing release. **Release gate BLOCKED.**

## Stage90 actual 63 unique historical source risks verified; Stage91 seven-T original QC0 sensitivity (29 October 2026)

**Stage90 actual IRIDIS6 SUCCESS**: `/home/ly3n24/ameriflux_batch05_stage90/ten_site_remaining_risks_20261029T070834Z_2339016/`. The ten-site original source files were SHA verified at each affected site. **Exactly 63 distinct site/native HH release-risk records**, **no overlap among the three hold/exception category sets** and **no missing original native source timestamps**: 46 historical P1 manual HOLD (US-Vcm 43, US-Vcp 3), ten original RH saturation-platform source HH (US-Vcm 4, US-WCr 6), and seven original source T anomaly cases (US-Vcm 1, US-Vcp 2, US-Wjs 2, US-Wkg 2). All seven original-T risk site/native keys overlap the immutable approved **1,675 HH research versioned overlay**; none of the 63 overlap separate Stage89 US-Whs 51 HH. Stage90 itself is **read-only source evidence, not a source T correction or production forcing approval**. The source-temperature exceptions still flagged by original source/QC and prior analyses are `US-Vcm 2014-09-06 23:30`, `US-Vcp 2008-05-22 15:30 / 2014-04-26 23:30`, `US-Wjs 2022-03-31 03:30 / 2025-04-19 16:00`, `US-Wkg 2025-03-07 12:30 / 2025-09-10 13:00`. The exceptional source `TA_F_QC=0` does not itself prove the recorded source T is physically valid. Do not overwrite immutable original T based solely on unrelated source-processed ERA T or QC1 neighbor T; local independent physical/scientific validation still required.

**Stage90 per-site distribution** (63 unique):
- US-Vcm: 48 (43 P1, 4 RH plateau, 1 T source anomaly; 1 overlaps research 1675)
- US-Vcp: 5 (3 P1, 2 T; 2 overlap research 1675)
- US-WCr: 6 (six RH platform)
- US-Wjs: 2 (two T; both overlap research 1675)
- US-Wkg: 2 (two T; both overlap research 1675)
- US-UiD, US-UMB, US-UMd, US-Var, US-Whs: 0 historic risk category records.
P1/platform records retain scientific HOLD, and any other source-ERA humidity-proxy research repairs still need independent evidence/uncertainty validation. No numerical RH-only pass establishes source meteorological accuracy.

**Stage91 prepared, not yet operator run:** [read-only source Python](scripts/stage91/91_batch05_seven_T_source_exceptions_QC0_anchor_sensitivity_READONLY.py) and [SHA-pinned one-command IRIDIS6 runner](scripts/stage91/run_stage91_seven_T_original_QC0_sensitivity_iridis6.sh). Rereads actual Stage90 63 unique SHA-verified source risk records and 7×13 original native ±3h source T/VPD/QC context; revalidates Stage84 main 1,675 immutable SHA `63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce` and Stage89 separate 51 preview immutable SHA `95aefd6027e6f981ac821266bc379b89d9f1299d1c307b7575a17fec65588561`. For each seven source temperature anomalies, prints nearest source **native measured QC0 temperature donors within three hours on either side**, whether true two-sided candidates exist, their bracket stability and differences versus source T, existing versioned approved T/VPD/RH and source-processed ERA companion. Potential candidate T and its T/VPD/RH sensitivity are **scientific diagnostics only**, not approved corrected temperature; if QC0 donors are unavailable, it records unavailable rather than fabricate an anchor or substitute processed-ERA/QC1 as source measured. Creates NEW HOME read-only reports; **no original, main approved 1,675 HH, separate Stage89 51 HH, DATM/CIME or Slurm changes**. Release remains blocked for source T local review, P1 46, RH platform 10, and source processed-ERA humidity-proxy independent validation.

## Stage89 actual SUCCESS US-Whs separate 51 T/RH/VPD physics; Stage90 focused original release-risk audit (29 October 2026)

**Operator actual Stage89 read-only SUCCESS**: separate US-Whs **51 accepted Stage67 native T interpolations** in one cross-variable science preview, of which **47 preserve original VPD** and **four use the separate Stage88 original immediate QC0-anchored RH/VPD numerical proposals**. All 51 recomputed RH values numerically physical; original/source/QC unchanged. The Stage89 preview CSV SHA256 is **`95aefd6027e6f981ac821266bc379b89d9f1299d1c307b7575a17fec65588561`**, actual report `/home/ly3n24/ameriflux_batch05_stage89_Whs/Whs_51_T_plus_four_VPD_20261029T070333Z_2322432/`. The independent Stage84 main **1,675 versioned approved research correction rows** remain unmodified and SHA-verified **`63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce`**. No DATM/CIME/Slurm, no production forcing changes. **Stage89 is a research integration PREVIEW, not proof of independently measured humidity or permission to release the 51 source T modifications into production forcing.**

**Original P2/P3 across all ten site-native sources:** source-screen 1,574 HH fully dispositioned (9 prior approved, 1,468 subsequent RH-negative source reconstructions, 97 original nonnegative-RH passes), leaving **zero unclassified P2/P3 HH**. The main approved science overlay 1,675 rows is a different cohort/scope, not the number of remaining worklist HH.

**Stage90 focused ten-site original-source scientific release risk evidence [prepared; not yet operator-run]**: [read-only source Python](scripts/stage90/90_batch05_remaining_science_risks_original_source_evidence_READONLY.py) and [SHA-pinned IRIDIS6 launcher](scripts/stage90/run_stage90_batch05_remaining_science_risks_iridis6.sh) crosswalk the exact Stage86 **seven source T exception HH, 46 historical P1 HOLD HH and 10 original RH platform HOLD HH** with SHA-verified original Stage05 FLUXMET/FULLSET native TA/VPD/QC, original processed ERA companion, prior 1,675 main research overlay and separate Stage89 51 HH preview. The 7/46/10 groups may overlap, so Stage90 reports **unique site/native source risk HH** and categories/overlaps, rather than incorrectly claiming 63 distinct records. It also reports original native ±3h temperature, VPD, and original/ERA RH for the seven temperature exceptions, per-site ERA-proxy method counts from Stage86, original-site SHA pins and outputs a focused manual science-evidence review table. This is evidence collection only: no automatic meteorological substitutions, no QC relabeling, no P1 or RH-platform HOLD override, no model-ready forcing approval.

**Release gate remains BLOCKED** pending independent scientific assessment of the seven T source cases, protected P1 and RH-platform historical decisions, and original source-processed ERA humidity-proxy reliability before model-ready DATM forcing can be generated. A numerical RH between 0–100% by itself does not establish independent field accuracy.

## Stage88 actual 4/4 US-Whs QC0 source-based joint RH/VPD proposals PASS; Stage89 preview next (29 October 2026)

**Stage88 actual operator IRIDIS6 SUCCESS:** four of four source-native US-Whs timepoints with Stage67-approved TA candidates plus original QC1 VPD physically impossible RH now have distinct **research-grade QC0-bracketed RH/VPD repair proposals**, without mutating the 51 already accepted Stage67 TA candidate dataset or the immutable 1,675-row RH/VPD research overlay. Original source TA/VPD QC0 donor times are **immediately before and after each target**, and each RH interpolation was independently checked against direct original QC0 VPD linear interpolation. Maximum absolute discrepancy **0.012215204 hPa** (predeclared check ≤0.05 hPa). Proposed newly reconstructed VPD: `2009-10-29 04:30 → 2.665875164 hPa`, `2009-10-30 02:00 → 2.959918383 hPa`, `2009-10-30 11:00 → 9.618784796 hPa`, `2013-03-08 11:00 → 5.292077962 hPa`, at their unchanged accepted Stage67 interpolated TA. Stage88 exact four-row candidate CSV SHA256 **`f2a77c748ec0d87a43b855af6a600a5635381b982da508a4bde6ddf48308fb64`**, report `/home/ly3n24/ameriflux_batch05_stage88_Whs/Whs_QC0_four_cross_variable_20261029T065626Z_2301104/`. **Four numerical research proposals pass the original QC0 source-science two-method check, but are not yet merged into a production-forcing release or claimed as original RH tower measurement at their target timestamps.**

**Next Stage89 source-provenance full separate Whs temperature+humidity integration preview (prepared, not yet operator-run):** [read-only Python](scripts/stage89/89_US_Whs_51_T_plus_four_VPD_integration_PREVIEW_READONLY.py) and [SHA-pinned one-command IRIDIS6 runner](scripts/stage89/run_stage89_US_Whs_51_joint_preview_iridis6.sh). Strictly check source original Whs CSV SHA, Stage67 all 51 T candidates/manifest, Stage84 1,675 overlay exact source SHA, Stage86 10-site original release blocks, and actual Stage88 four-row source SHA and provenance. Create one **separate 51-row nonproduction joint T/VPD/RH preview**: preserve the **47 other original VPD values** where RH remains numerically 0–100% with Stage67 accepted TA, and include the **four Stage88 paired QC0-derived VPD proposals**. This checks all 51 candidate-stage humidity physics without editing any originals, previously accepted overlays, DATM/CIME or Slurm. It does not constitute a blanket scientific RH verification of the 47 other HH. Expected `47+4=51` and zero combined numeric RH violations; **actual operator execution still required to confirm**.

**Outstanding release-policy categories after Stage88 remain:** 7 source-T anomaly HH needing independent local scientific review, 46 historically held P1 original source HH, 10 original source RH-platform records, and independent source-reliability validation for substantial original source-processed ERA humidity-proxy replacements. These categories are not necessarily disjoint. Thus the P2/P3 1,574 original-screen HH are fully dispositioned, but **the Batch05 production forcing release gate is still blocked**. Avoid claiming all scientific issues are resolved simply because Stage88 four site-specific cross-variable physics candidates now pass.

## Stage87 actual US-Whs 4 joint T–VPD physics failures; Stage88 QC0 cross-variable science candidates (29 October 2026)

**Stage87 operator IRIDIS6 actual SUCCESS:** strict 51/51 exact Stage67 independent US-Whs approved original temperature candidate source keys and immutable original Stage05 native FLUXMET CSV verified; exact **4/4** Stage86 physics exceptions reproduced at `2009-10-29 04:30`, `2009-10-30 02:00`, `2009-10-30 11:00`, `2013-03-08 11:00`. All four original `TA_F_QC=1` and `VPD_F_QC=1`; original QC1 temperature is substantially higher than scientifically accepted QC0-bracketed Stage67 interpolated temperature. Original QC1 VPD was **unchanged** in Stage67, yielding candidate RH **−96.0496%, −87.4092%, −96.5162%, −21.3368%**, respectively, although original high-temperature pair RH was originally positive. These are four **actual physical T/VPD inconsistencies, not missing source VPD**. In the original source context, both immediate native ±30min neighboring TA and VPD have source original QC0 and physically valid source-derived RH for each of the four flagged times. Verified Stage87 report: `/home/ly3n24/ameriflux_batch05_stage87_Whs/Whs_four_T_VPD_20261029T064851Z_2274533/`. Previous 1,675 versioned approved RH/VPD/T overlay and Stage67 51 temperature proposals unchanged.

**Targeted Stage88 proposed cross-variable numerical reconstruction (not yet operator-executed):** [SHA-pinned source script](scripts/stage88/88_US_Whs_four_Stage67_T_VPD_RH_QC0_joint_correction_READONLY.py), [one-command IRIDIS6 runner](scripts/stage88/run_stage88_US_Whs_four_QC0_joint_T_VPD_iridis6.sh). Preserve each prior Stage67 approved candidate TA (−1.3455, −0.4015, 9.545, 11.425°C); derive RH from *two immediate original QC0 VPD/T-derived humidity values* at native times (linear midpoint, explicitly an interpolation rather than a humidity observation at the target); compute `VPD_new = es(T_approved) × (1−RH_interpolated/100)`. Expected diagnostic candidates from user's Stage87 printed rounded source data: approx `2.666`, `2.960`, `9.619`, `5.292` hPa, respectively. Independently cross-check numerical VPD against direct two-sided original VPD_QC0 interpolation (approximately `2.6665`, `2.9620`, `9.6310`, `5.3010` hPa): **all differences expected below 0.05 hPa**, but the HPC script checks exact original source native values and fails closed on any mismatch. Source QC1 labels are retained as original provenance and are never relabeled QC0. The Stage88 output is a **new four-row versioned *science proposal*** for joint T/RH/VPD, not four additional existing approved source rows or automatically production-validated modifications. The original 1,675 approved research repair rows and separate 51 approved T candidate rows remain unchanged; no DATM, CIME, Slurm or original data writes.

The Stage86 full model-forcing release gate still remains **BLOCKED** pending separate original source-temperature exceptions (seven), P1 46 and RH-platform 10 original holds, and broad validation of source-processed ERA RH proxy interventions. Do not assume that eliminating four additional Stage67 T/VPD physics failures is proof of model-ready meteorological forcing.

## Stage86 actual ten-site QC reconciliation SUCCESS; Stage87 four Whs temperature-VPD physics exceptions (29 October 2026)

**Stage86 actual operator IRIDIS6 SUCCESS** (`/home/ly3n24/ameriflux_batch05_stage86/ten_site_final_QC_20261029T064013Z_2246464/`), all ten original sites P2/P3 fully dispositioned with **1574 original P2/P3 source half-hours = nine prior source P2/P3 approvals + 1468 Stage63-scope negative-RH direct-repaired + 97 source-nonnegative original-pass**. Latest Stage84 **1,675 versioned approved research repair half-hours** preserved under exact SHA256 `63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce`: 204 previous baseline +1,468 P2/P3 new source RH-negative + three additional US-WCr 2016 source T exceptions. Stage86 independently verified **0** physical RH/VPD inconsistencies in 1,675, **0** unassessable numeric records, **0** original source T/VPD/QC provenance drift, **0** remaining original P2/P3, and Stage67 51 separate approved source TA candidate time keys **0 overlapping** the main 1,675 overlay. Original 46 P1 HOLD / 10 RH plateau holds and seven site source T science exceptions remain separate; old QC/archives/previous overlays/model forcing/DATM/CIME/Slurm unchanged.

**Crucial distinct cross-variable science finding:** **four out of Stage67 51 independently approved Whs interpolated TA candidates yield nonphysical or non-computable RH when combined with the original, unchanged source VPD** (Stage86 flags missing source VPD as a physics issue too; Stage87 distinguishes this from a physically impossible numeric T/VPD pair). This is **not** the same as the zero physics errors in the main 1,675-row RH/VPD overlay. Never concatenate the 51 TA edits into production forcing without an explicit T–VPD/RH thermodynamic reconciliation. Final `RELEASE_GATE=BLOCKED_UNTIL_RH_PROXY_SOURCE_VALIDATION_P1_PLATFORM_T_EXCEPTION_STAGE67_T_PHYSICS_RECONCILED`; approval of research reconstructions does not imply production forcing readiness. From the printed Stage86 method inventory, **1,266 of 1,675 research repair records have a source-processed ERA humidity-proxy provenance label**, not independent tower RH or separately downloaded ERA5-Land; retain source-specific uncertainty and prioritize validation rather than treating RH range bounds as proof of atmospheric realism.

**Stage87 next targeted read-only verification**: [GitHub script](scripts/stage87/87_US_Whs_four_stage67_T_candidate_VPD_physics_diagnosis_READONLY.py) and [SHA-pinned one-command IRIDIS6 launcher](scripts/stage87/run_stage87_US_Whs_four_T_VPD_physics_iridis6.sh). Revalidates Stage84 1,675 SHA and Stage86 four exception source keys and outcome, verifies the 51 original Stage67 candidate T/QC/VPD fields against original Stage05 Whs FLUXMET CSV SHA256 `653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca`, and prints all four original source TA/VPD/QC, changed TA, physical original/candidate RH, processed-source ERA, and native ±3-hour source measurements. Alternative VPD values retaining original RH or using source-processed ERA RH are **counterfactual numerical diagnostics only, not approved repair proposals**. Stage87 output is NEW read-only scientific report under HOME, no original, previously approved T, 1,675 overlay or production forcing changes. **Stage87 on-cluster execution not yet reported.**

## Stage85 SUCCESS: all ten-site original P2/P3 source episodes dispositioned; Stage86 final release gate (29 October 2026)

**Actual operator Stage85 success:** final US-Whs original P2/P3 key `2012-05-26 06:00`: `TA_F=29.620°C` QC1, `VPD_F=41.132` hPa QC1, implied RH **0.974%** (positive), original source processed-ERA pair inferred RH **33.912%** (a much more humid proxy). Both ±3-hour source T/VPD history and no original VPD_QC0 donor nearby were verified. The time does **not** overlap the earlier separately accepted Stage67 **51** TA interpolation candidate HH or the ten Stage67 bracket-unrepairable runs that the investigator chose to pass unchanged. Therefore **PASS original RH nonnegative (with science-provenance caveat), do not increase the 1,675 overlay count**. Source, QC, previous 1,675, production DATM/CIME and Slurm unchanged. Actual Stage85 report: `/home/ly3n24/ameriflux_batch05_stage85_Whs/Whs_last_1HH_20261029T063406Z_2227405/`.

**Latest verified Stage84 research overlay:** **1,675 versioned numerically approved reconstruction HH**, SHA256 `63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce`, from exact completed Stage84 US-Vcp. **Not** a model-ready forcing output. The original **P2/P3 1,574 HH** differs in scope from the 1,675 approved rows: **nine** were already within the baseline 204 before Stage63; the Stage63 **1,565 original remaining HH** were dispositioned as **1,468 RH<0 original-source times repaired** and **97 RH≥0 original-source times left unchanged**. The research overlay contains **204 baseline versioned rows + 1,468 new P2/P3 negative-RH repairs + three additional 2016 US-WCr original-source T context corrections = 1,675**. The 51 separate Stage67 US-Whs accepted TA candidates are not silently merged into it. Therefore **0 remaining unclassified original P2/P3 times**, not 0 remaining scientific forcing issues.

**Next Stage86 SHA-verified read-only final ten-site crosswalk** [Python](scripts/stage86/86_ten_site_final_P2P3_reconciliation_release_gates_READONLY.py) and [IRIDIS6 one-command runner](scripts/stage86/run_stage86_ten_site_final_qc_readonly_iridis6.sh): revalidates exact latest 1,675 SHA and previous Stage84 manifest; original Stage27 1,574 / Stage63 1,565 source time+QC+values and nine prior source keys; Stage85 Whs original nonnegative decision; Stage67 51 separate approved candidate TA HH and ten source runs passed unchanged; separately verifies historical **46 P1 HOLD HH** and **10 RH-saturation platform HOLD HH**. Detects original-source QC drift, reconstructed RH(T,VPD) physics/delta errors, potential Stage67 T/VPD cross-variable overlaps, source-temperature exceptions (Wkg two, Vcm one, Wjs two, Vcp two) and any overlap with protected historical HOLDs. Produces a ten-site disposition table, 97 original PASS ledger, methods summary, focused risk ledger and machine-readable release gate. Processed source ERA humidity remains a **proxy** and is *not independent tower RH or separate ERA5-Land reanalysis*. This is an audit, **not permission to promote any science overlay to production DATM/CIME**, and does not submit Slurm.

**Stage86 is prepared and committed, but no operator IRIDIS6 successful run has yet been reported.** Its self-test, source SHA and all stage-manifest checks run before any new audit output is created. Do not take the planned Stage86 statistics as actual validated output until its on-cluster verification is complete.

## Stage84 US-Vcp verified; Stage85 last US-Whs source-science key (29 October 2026)

**Operator actual Stage84 SUCCESS:** US-Vcp original source SHA `eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42` and original Stage27/63 626/626 event/native T,VPD,QC keys verified. Across 171 source episodes: **582 original RH-negative directly reconstructed** in a NEW versioned approved research overlay; **44 original nonnegative RH passed unchanged**. Exact previous 1,093 approved rows retained, new **1,675 versioned approved rows** SHA256 **`63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce`**, operator report `/home/ly3n24/ameriflux_batch05_stage84_Vcp/Vcp_direct582_20261029T062857Z_2211876/`. Method counts: **32** two-sided original measured VPD-QC0 inferred-RH interpolations, **548+2=550** same-native original processed source ERA humidity-proxy replacements (not independently measured/validated tower humidity, nor independent ERA5-Land). Exact two original TA spikes remain **numerically unresolved** because original immediate neighbors are QC1/QC2, not required original QC0 donors: `2008-05-22 15:30` original T 0.487°C QC0, 12.591°C QC1 before and 8.987°C QC2 after; `2014-04-26 23:30` original T−8.941°C QC0, 4.097/4.113°C QC1 before/after. Source original T and QC left unchanged, RH/VPD reconstructed and narrowly labeled local temperature exceptions **for pre-forcing review**. No originals/QC/older overlay/DATM/CIME/Slurm altered.

**Exactly one original Stage63 P2/P3 selected HH remains before complete source-cohort disposition:** US-Whs `2012-05-26 06:00`; this is a *humidity* consideration, separate from the previously accepted Stage67 US-Whs **51 versioned interpolated TA half-hours and ten original-passed bracket-failure target runs**. The 51 accepted T candidate rows have not been silently merged into the 1,675 RH/VPD versioned approved table. **Stage85** [SHA-pinned source/read-only crosswalk Python](scripts/stage85/85_US_Whs_last_1HH_stage67_crosswalk_READONLY.py) and [one-command IRIDIS6 launcher](scripts/stage85/run_stage85_US_Whs_final_1HH_crosswalk_iridis6.sh) verify original Stage05 Whs FLUXMET source SHA `653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca`, original Stage27/63 exact timestamp+source QC, previous 1,675 overlay exact SHA, Stage67 manifest 51 candidate TA HH + 10 earlier HOLDS now operator passed original, and inspect the ±3-hour native source QC/T/VPD/RH/processed-ERA context. It detects whether the exact Whs humidity HH is one of the separately accepted Stage67 TA candidates; no repair or model modification is silently applied. **Stage85 has been published, not yet operator-run.**

**After Stage85:** make a *read-only ten-site integration/release-gating report* with exact source/repair key reconciliation, all modified T/RH/VPD physical consistency, original source QC lineage preserved, 51 separate Stage67 TA candidates reconciled, original P1 46 source HOLD records, original RH-saturation-platform 10 source records, and localized temperature exceptions at Wkg/Vcm/Wjs/Vcp. Tag 1,675 approved versioned numerical reconstructions by direct measured QC0 anchors versus processed-source ERA proxies; target manual comparison **only** at source-T science exceptions, P1/ten platforms, and scientifically uncertain proxy cases. Numeric RH between 0% and 100% is necessary but not sufficient for production forcing quality; do not automatically promote the approved versioned research overlay to model-ready DATM forcing.

## Stage83 US-Vcp original 626 passed; Stage84 582 direct negative-RH corrections prepared (29 October 2026)

**Actual operator IRIDIS6 Stage83 read-only SUCCESS:** source Stage05 US-Vcp original FLUXMET native HH/HR CSV SHA256 `eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42`, exact Stage27 and Stage63 source native T/VPD/QC match **626/626**, **171 source P2/P3 episodes**, zero previously approved Vcp P2/P3 keys, prior Stage82 1,093 versioned approved repairs exact SHA `b8bc7a34715e58b7f22efb5b25d352f02a57b59b2ee26cef1e7515850c2a38a4`. Original source inferred **RH<0 on 582 HH**; **44 original HH have nonnegative (all under 1%)** and pass numerically unchanged, with their very-low inferred humidity never relabeled as independently observed tower RH. Original QC pair counts: `TA0/VPD1=172; TA0/VPD2=333; TA1/VPD2=121`. Original bundled source-processed ERA pair internally physical at all selected 626 HH. Two originally negative-RH source T spike exceptions: `2008-05-22 15:30`, original TA=0.487°C QC0, immediate native T=12.591/8.987°C, original VPD=6.868 hPa, implied RH=−8.475%; `2014-04-26 23:30`, original TA=−8.941°C QC0, immediate T=4.097/4.113°C, original VPD=5.154 hPa, implied RH=−65.379%. Original temporal context printed neighboring T but not their QC grade, so **do not call those neighbors QC0 before reading the original QC**. Stage83 exact report: `/home/ly3n24/ameriflux_batch05_stage83_Vcp/Vcp_original626_20261029T062235Z_2193625/`. All original source/previous approved/DATM/CIME/Slurm unchanged.

**Next Stage84 prepared (not yet operator-executed):** [Python source](scripts/stage84/84_US_Vcp_582_negative_RH_direct_approved_1675.py), [SHA-pinned one-command launcher](scripts/stage84/run_stage84_US_Vcp_direct_582_to_1675_iridis6.sh). Stage84 rechecks Stage83 report SHA/classification, Stage27/63 native 626HH original QA and source FLUXMET SHA, verifies previous 1,093 approved overlay exact SHA, then **directly reconstructs 582 negative RH HH** under operator science rule, preserves **44 source nonnegative RH HH** unchanged. Uses two-sided original measured VPD-QC0 physical RH donors within 3 hours if available, otherwise **same-native original source processed ERA derived RH as explicitly labeled proxy, not independent CDS ERA5-Land or measured source RH**. At the **two** obvious T exceptions (already among 582), performs bounded linear T interpolation only when both *immediate original native* bracket temperatures are QC0, coherent, and retaining original VPD becomes physically feasible; otherwise reconstructs numerical RH/VPD with T unchanged, and marks unresolved original T spike for targeted inspection before forcing. No automatic replacement of QC0 with neighboring QC1/2 or rewriting original QC labels. Reports the exact two T decisions and methods in a new HOME overlay. **Expected after successful Stage84: 1,093+582 = 1,675 versioned scientifically approved reconstruction rows** (not yet production DATM forcing). Once 626 original Vcp HH are dispositioned, the original Stage63 P2/P3 remaining site is **US-Whs one HH**, while separate P1 historical 46 HOLD and 10 RH-platform source events require final reconciliation. Stage84's actual successful output has **not** been observed yet.

## Stage82 US-Wjs actual success; Stage83 US-Vcp next (29 October 2026)

**Stage82 actually executed successfully on IRIDIS6.** US-Wjs original Stage05 source SHA256 `9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6`; 401/401 historical source HH, of which 393 original Stage63 P2/P3 pending HH (150 events), eight historical previously-approved Wjs HH protected. Of the 393, **379 original inferred RH<0 directly repaired**, 14 original RH≥0 passed unchanged. Full previous **714** approved versioned rows preserved. New **1,093 versioned user-approved repair HH** SHA256 **`b8bc7a34715e58b7f22efb5b25d352f02a57b59b2ee26cef1e7515850c2a38a4`**, actual report `/home/ly3n24/ameriflux_batch05_stage82_Wjs/Wjs_direct379_20261029T061912Z_2183874`. No original FLUXMET/QC or production forcing/DATM/CIME/Slurm modifications.

**Methods/provenance:** **116** new source negative-RH replacements use two-sided original measured VPD-QC0 humidity donor interpolation (115 ordinary plus one source-temperature-warning case), while **263** use same-native original *source-processed ERA* RH proxy (262 ordinary plus one source-temperature-warning case). This is not independent ERA5-Land/tower RH validation. Original flagged `2022-03-31 03:30` T=−5.946°C vs adjacent QC1 T=8.707/8.701°C and `2025-04-19 16:00` T=1.032°C vs adjacent QC1 T=10.404/11.779°C **remain unresolved original-T spikes**: Stage82 repaired numerically impossible RH/VPD with source T unchanged because adjacent donor temperatures were QC1 rather than measured QC0. Exact localized source-temperature review remains necessary before production forcing promotion; these scientific caveats do not invalidate unrelated already-approved research rows.

**Remaining original Stage63 P2/P3 after Stage82:** **627 HH at two sites: US-Vcp 626, US-Whs 1**. P1 historical 46 HOLD and platform RH saturation 10 HH are separate and require final release reconciliation. The original source P2/P3 disposition count and 1,093 total versioned repair-row count are not the same cohort.

**Next Stage83 US-Vcp source-only audit** [source script](scripts/stage83/83_US_Vcp_626_original_QC_RH_T_audit_READONLY.py), [one-command SHA-pinned launcher](scripts/stage83/run_stage83_US_Vcp_original_626HH_iridis6.sh). Strictly verify original Stage05 US-Vcp source FLUXMET CSV SHA256 `eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42`, all **626** Stage27 historical source time/T/VPD/QC against **626** Stage63 original still pending P2/P3, zero already-approved Vcp original P2/P3, and Stage82 1,093 approved overlay exact SHA. Reports original inferred RH-negative/nonnegative count, T/VPD QC pair distribution, internal source-processed ERA physics, localized temperature excursions and high-volume source events. **Only a new HOME read-only audit report** is written; source, previous 1,093, DATM/CIME and Slurm untouched. Stage83 script/launcher are published and Git SHA verified, **but actual US-Vcp Stage83 HPC execution has not yet been reported**.

## Stage81 actual US-Wjs review; Stage82 user-directed 379 repairs (29 October 2026)

**Stage81 operator run verified (read-only):** US-Wjs source Stage05 native FLUXMET CSV SHA256 `9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6`, **401/401 original historical Stage27 keys verified**, of which eight were already in SHA-verified Stage80 714 approved overlay; **393/393 remaining Stage63 original P2/P3 HH across 150 original source episodes**. 379 original derived RH<0, **14 original RH>=0** (all below 1%, not independent tower RH measurements), QC: TA0/VPD1=282; TA0/VPD2=111. Zero original processed ERA internal nonphysical humidity selected; two source temperature anomalies: `2022-03-31 03:30` original TA_F−5.946°C vs immediate 8.707/8.701°C, and `2025-04-19 16:00` original TA_F1.032°C vs immediate 10.404/11.779°C. Stage81 reports `/home/ly3n24/ameriflux_batch05_stage81_Wjs/Wjs_original393_20261029T045811Z_2546054`; source, QC, prior714, DATM/CIME and Slurm unchanged.

**Stage82 prepared, not yet actually run:** [source script](scripts/stage82/82_US_Wjs_379_negative_RH_direct_approved_1093.py) and [SHA-pinned one-command launcher](scripts/stage82/run_stage82_US_Wjs_direct_379_to_1093_iridis6.sh). The script rechecks Stage81 summary+SHA, all original 401 source T/VPD/QC, precise 393 pending and eight previously approved Wjs original keys, and previous 714 overlay SHA256 `e65b0c854cd391c1ae6c26b3b627dd60a99ee4a9f574219ead65ef1cc76d253c`; repairs **379 negative RH** directly per investigator policy, passes 14 original nonnegative RH unchanged. For source-native T exceptions, repairs original T by interpolation between immediate original QC0 T donors only if both are physically stable and retaining the original VPD produces feasible RH; otherwise repairs RH numerically and explicitly records the **unresolved T-source warning before model forcing**. Other negative RH uses both original measured QC0 VPD-derived RH donors within 3h where possible, else same-native source-processed ERA RH as a stated **proxy, not independent ERA5-Land or direct tower humidity**. All fixes are only in a versioned science overlay, immutable original source/QC and DATM/CIME/Slurm unchanged. **Expected after successful Stage82:** existing 714 + 379 Wjs new = **1093 approved versioned correction records**. The original P2/P3 queue would drop from **1020 to 627 HH** (US-Vcp 626 and US-Whs 1). This is contingent on actual IRIDIS6 Stage82 success, not currently confirmed.

## Stage80 actual success / Stage81 next US-Wjs original 393 HH (29 October 2026)

**Operator actual Stage80 SUCCESS (US-Vcm):** source original Stage05 CSV SHA256 `c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c`, 72 original events / 362 original Stage63 P2/P3 HH. **336 original negative RH directly repaired** and **26 original nonnegative RH kept unchanged** under investigator user-policy. Existing 378 approved versioned rows preserved exactly. Latest actual **714 versioned user-approved research reconstruction rows**, overlay SHA256 `e65b0c854cd391c1ae6c26b3b627dd60a99ee4a9f574219ead65ef1cc76d253c`; report `/home/ly3n24/ameriflux_batch05_stage80_Vcm/Vcm_direct336_20261029T045457Z_2529299/`. The old source, original QC, DATM/CIME forcing and Slurm jobs remain unchanged.

**Important method provenance, not independently validated observations:** Of the 336 new negative RH fixes, **four** use two-sided original `VPD_F_QC=0` native humidity anchors within 3h, while **331+1=332** use same-native original `TA_ERA/VPD_ERA` processed-product RH as a proxy (**not independent ERA5-Land, and not tower-measured humidity**). The one temperature exception is `2014-09-06 23:30`: original `TA_F=2.978°C` QC0, `VPD_F=8.195` hPa QC1, source-inferred RH=−8.3046%; original source-proxy ERA RH≈73.4793%. Immediate native before/after original `TA_F` values are 11.377°C and 11.338°C, but both **QC1**, not independently observed QC0; therefore Stage80 correctly **did not overwrite original 2.978°C** or misrepresent QC1 donors as QC0. Its RH/VPD is reconstructed numerically, and this exact original TA remains a **local scientific uncertainty requiring independent checking before model forcing promotion**. The 714 versioned output is an auditably reconstructed dataset, not a production-ready forcing approval.

**Next source-science Stage81 US-Wjs**, [strict source SHA-pinned Python](scripts/stage81/81_US_Wjs_393_original_HH_QC_RH_T_audit_READONLY.py), [one-command IRIDIS6 runner](scripts/stage81/run_stage81_US_Wjs_original_393HH_iridis6.sh). Stage05 original source-native Wjs FLUXMET CSV SHA256 `9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6`. Verify entire original Wjs **401** Stage27 source keys and original **393** still pending Stage63 P2/P3, with the eight already-covered historical source keys present in the 714-row approval ledger. Print original QC pair counts, negative/nonnegative RH tally, source-ERA physics and localized suspicious temperature, plus largest original events. This step writes *new read-only audit reports under HOME*, no original CSV/QC/approved714/DATM/CIME/Slurm changes. **Stage81 has not yet been executed on IRIDIS6.**

**Pending original Stage63 P2/P3 after US-Vcm:** 1,020 HH: US-Vcp 626, US-Wjs 393, US-Whs 1. Independently tracked older P1 46 HOLD and RH platform 10 HH are not included. Do not conflate 714 versioned repair rows with the number of native P2/P3 source records disposed; both sets have different scopes.

## Stage79 US-Vcm verified; Stage80 336 negative-RH repairs queued (29 October 2026)

**Actual operator Stage79 read-only SUCCESS:** US-Vcm 72 original P2/P3 events, **362 original selected HH verified 362/362** against Stage27/63 and Stage05 source original FLUXMET CSV SHA256 `c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c`. **336 original RH<0**, **26 source RH>=0**. Source selected T/VPD QC pairs: 0/1=317; 0/2=35; 1/1=3; 1/2=5; 2/2=2. **Zero** original processed source ERA internally nonphysical RH pairs within this *selected 362 HH*, **one** source temperature anomaly screen at original native `2014-09-06 23:30` (TA_F 2.978°C QC0, original VPD_F 8.195 hPa QC1, derived RH −8.30%, original source ERA-derived RH≈73.48%). This stage79 result does **not** remove older US-Vcm source meteorological concerns at other times or P1/RH-platform source holds. Stage79 reports `/home/ly3n24/ameriflux_batch05_stage79_Vcm/Vcm_original_362_20261029T044939Z_2502322`, original and previous Stage78 378 source/approval files unchanged.

**Next Stage80 Vcm direct science repair**, [Python](scripts/stage80/80_US_Vcm_336_negative_RH_direct_repair_preserve_378.py), [SHA-pinned IRIDIS6 runner](scripts/stage80/run_stage80_US_Vcm_direct_336_to_714_iridis6.sh): verify Stage79 report, Stage05 source SHA, Stage27/63 native T/VPD/QC and Stage78 versioned 378 overlay SHA `400757c166d03fa8d7e7b72aa39879c14c2d9db5ada818d930c647c71d06f7b5`. Directly correct **336** source negative RH entries under operator rule, using two-sided original native VPD_QC0 RH donors within 3h when available, otherwise original same-native source processed ERA-derived RH (scientific proxy; **not independently observed tower humidity or downloaded ERA5-Land**). Preserve original T/QC for ordinary records, and the 26 numerically nonnegative original rows unchanged. The single obvious-temperature-anomaly flag is separately logged: interpolate T using immediate *original QC0* neighbors only if they are mutually consistent and original VPD becomes physically feasible; otherwise leave original T, perform direct RH numerical repair and flag a precisely scoped temperature science caution **before production forcing**. **Expected after successful Stage80 execution: 378+336=714 versioned approved repair rows**, original US-Vcm 362/362 P2P3 fully dispositioned (336 repaired, 26 passed). Remaining original P2P3 queue after Stage80 would be **1020 HH**: US-Vcp 626, US-Wjs 393, US-Whs 1. Old P1 46 and RH platform 10 remain separate final release ledgers. **Stage80 execution is not yet confirmed**; existing 378 is the latest operator verified approved overlay count.

## Stage78 success and Stage79 US-Vcm next (29 October 2026)

**Stage78 actually succeeded on IRIDIS6.** Original US-Var 37 events / 62 selected P2/P3 half-hours: 55 original negative RH repaired directly using source native two-sided inferred-RH donors at unchanged QC0 tower T (**46 both original VPD QC0 donors; nine both mixed-QC RH donors**); seven original positive but very-low RH source HH passed unchanged with science caution. Prior **323** versioned approved rows verified exact SHA and preserved. New **378 versioned approved** overlay SHA256 `400757c166d03fa8d7e7b72aa39879c14c2d9db5ada818d930c647c71d06f7b5`, exact report `/home/ly3n24/ameriflux_batch05_stage78_Var/Var_378_20261029T044442Z_2477410`. Original source, QC, DATM/CIME forcing and Slurm remain unchanged.

**Remaining original Stage63 P2/P3** `1382` native flagged HH after US-Var full disposition: US-Vcp 626, US-Wjs 393, **US-Vcm 362**, US-Whs 1. This excludes separate P1 46 historical HOLD and 10 source RH-platform windows; a final integrated release reconciliation is still necessary. The `378` tally is approved versioned *repair rows*, not the count of P2/P3 original scientifically disposed time points.

**Next, Stage79 US-Vcm original source-science audit**, [Python](scripts/stage79/79_US_Vcm_362HH_original_QC_temperature_RH_event_audit_READONLY.py) and [verified pinned launcher](scripts/stage79/run_stage79_US_Vcm_original_362HH_iridis6.sh). US-Vcm original Stage05 FLUXMET CSV SHA256 `c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c` will be checked against original Stage27/Stage63 362 time-specific T/VPD/QC/episode values before classifying (i) RH negative for direct approved VPD/RH repair under operator rule, (ii) RH nonnegative to preserve original, and (iii) source T spikes or original source ERA internal nonphysical humidity as narrow exceptions. Unlike US-Var, US-Vcm has historical source QC0/0 low-saturation and QC2/2 source-ERA pathologies; do not blindly apply a uniform RH/VPD correction to such source exceptions. This Stage79 audit writes **only new HOME report files**, with no source, prior 378 overlay, DATM/CIME or Slurm mutations. **Stage79 actual run not yet verified**.

## Stage77 source result and Stage78 US-Var direct repair (29 October 2026)

Actual operator Stage77 read-only result: **US-Var original 37 events / 62 HH verified, 55 RH<0, 7 RH>=0; all TA_F_QC0 and VPD_F_QC1, zero flagged temperature jump exceptions**. Source FLUXMET ZIP SHA256 `2e0ff6fe7f7de6dfde3ebfd2e822266e899bd80f1ad0377f78fde34efcb410f2`.

Under the investigator's established rule, [Stage78 source repair](scripts/stage78/78_US_Var_55_negative_RH_direct_approved_378.py) directly corrects 55 negative-RH source VPD at unchanged QC0 temperature using bounded two-sided original source RH; measured VPD QC0 donors preferred where available. Seven original positive RH half-hours (0.19–0.92%) pass unchanged but carry QC1 humidity-science caveats. [Pinned Stage78 launcher](scripts/stage78/run_stage78_US_Var_iridis6.sh). After successful operator execution **323+55=378** versioned approved records; the original Stage63 P2/P3 queue drops from 1444 to **1382 HH** (US-Vcp 626, US-Wjs 393, US-Vcm 362, US-Whs 1). **Stage78 execution has not yet been confirmed**; existing Stage76 323 output is verified complete. Prior overlay, originals, QC, DATM/CIME and Slurm unchanged.

## CURRENT Stage76 success / outstanding sites / Stage77 US-Var next (29 October 2026)

**Actually observed operator Stage76:** original US-WCr SHA `f13c3a26a051bbe351fe5aa66a2cd7eef3849b33645732810bfc74a34c5e6f75`, 24/24 original episodes, 62/62 original source HH verified; original RH<0 **61 HH directly repaired**, source RH>=0 **one passed unchanged**. Of the 61, 59 RH/VPD-only replacements retain original TA and two original-flagged 2016 temperature faults are corrected in TA instead. A further three nonflagged, clearly corrupt native 2016 temperature HH are repaired as narrowly scoped local exceptions. Prior approved **259 rows preserved exactly**, new **64 versioned approved rows = 323**. Exact approved overlay SHA256 `494cfe0d92a376a796687a9d6a61d0e6133b750775dd851602c51dc71bee4f37`, reports `/home/ly3n24/ameriflux_batch05_stage76_WCr/WCr_direct61_Tplus3_20261029T043428Z_2423219/`. No source QC, original files, DATM/CIME, production forcing or Slurm jobs modified. **Stage76 actually succeeded, no longer merely expected.**

**Outstanding original Stage63 P2/P3 selected half-hour queue after US-UMd, US-UMB, US-Wkg and US-WCr reviews:** initial Stage63 1565 original not yet covered by prior 204 repair overlay; 15+22+22+62 = **121 original selected native HH scientifically disposed**, of which source RH>=0 **5 passed unchanged** and **116 directly repaired**; remaining **1444 HH across five sites** (these counts are *original P2/P3 cohort dispositions*, not total approved overlays or percentage of 1750 source screen). Sites: **US-Vcp 626; US-Wjs 393; US-Vcm 362; US-Var 62; US-Whs 1**; total 1444. US-Whs has separate Stage67 temperature decisions and only one residual original P2/P3 key that still needs an explicit final join check. US-UiD has **0** original P2/P3 to review. Thus four substantial sites remain plus a one-record US-Whs integration check. Historical P1 46 HOLD and two RH-saturation platform groups 10 HH are **separate** and require a distinct final release reconciliation. Do not subtract 323 from 1574: the 323 overlay includes earlier P1/context plus 3 extra WCr source temperature rows outside original P2/P3 worklist.

**Next Stage77**: start with manageable US-Var **62 original P2/P3 HH, 37 events**. [US-Var source SHA-pinned read-only audit](scripts/stage77/77_US_Var_37_events_62HH_original_context_READONLY.py) verifies original 62 source T/VPD/QC against Stage27/63, source original ZIP SHA `2e0ff6fe7f7de6dfde3ebfd2e822266e899bd80f1ad0377f78fde34efcb410f2`, prints original RH-negative/nonnegative tally and obviously anomalous source T, then all events with ±3h native T/VPD/QC and source processed ERA. [Stage77 one-command launcher](scripts/stage77/run_stage77_US_Var_37_events_62HH_iridis6.sh), pinned to commit `3903dc3048a1fe4f26172739b0cedc68078991fb` and blob `086986a236aa4e5cb3e9986b30b2d1f10636c6b2`. After reviewing its actual output, directly create versioned source RH-negative repairs under existing operator rule, avoid new operator HOLD for normal source periods and preserve already approved 323, while handling obviously corrupted source temperature as narrow exceptions. **Stage77 not yet executed in the supplied operator logs.**

## LATEST Batch05 acceptance rule — routine pass, only visibly erroneous native periods exempt (29 October 2026)

**Investigator's latest clarification (after the successful US-Wkg Stage74 run):** Routine events following the already approved source/QC temperature interpolation or negative-implied-RH repairs are **accepted directly by default**. Do **not** create extra HOLD queues, demand repeated human approval, reopen physically reasonable `RH>=0%` original time steps, or undertake broad investigations merely because a QC1/MDS value differs from source processed ERA. The only exemption is an interval whose **original native temperature or meteorological time series is visibly erroneous** (implausible spikes, physically incompatible same-period T/VPD, an exact anomalous sensor plateau). Review only such local exception intervals and explicitly distinguish original-source temperature corruption from QC1-VPD imputation problems; do not "repair" moisture in isolation by using a known-corrupt original temperature.

The source-temperature hierarchy remains: at a **suspicious QC0→QC1 transition**, linearly interpolate the **full contiguous QC1 run** from original native QC0 observations directly on both ends. At a **suspicious QC1→QC2 transition**, linearly interpolate the **full contiguous QC2 run** from original native QC1 values at both ends. Do not confuse QC codes with post-interpolation measurement provenance; preserve them in the immutable source and record versioned replacement values and methods separately. If suitable same-level bracketing anchors are missing, default to **PASS_KEEP_ORIGINAL** for this particular QC-transition audit rather than invent new values or reopen a pending HOLD. Physically impossible original source-implied RH<0% remains a **direct user-approved repair** rule, distinct from the source-QC transition rule.

**Verified Stage74 operator result (2026-10-29):** US-Wkg 10 events, 22 flagged original half-hours; 19 original RH-negative event HH directly repaired (13 original-QC0 T preserved / new VPD via RH interpolation; six 2020-02-18 source TA=0°C points under strong SW corrected via T interpolation using original QC0 bracketing T, VPD preserved); 3 nonnegative original RH flagged HH passed unchanged. New versioned approved record total **240 + 19 = 259**. Actual operator printed `STAGE74 SUCCESS`, SHA256 of the 259-row approved overlay **`c94e0adc96df846b682f69e3c85d2be8247d23ba7debed686a3462bb5927fc6f`**, `/home/ly3n24/ameriflux_batch05_stage74_Wkg/Wkg_direct_19_negative_RH_20261029T042245Z_2362992/stage74_VERSIONED_259_APPROVED_RH_VPD_TA_native_overlay.csv`. Original ZIP, original QC and prior 240 remain unchanged; no DATM/CIME forcing was changed.

**Only two visible source-temperature exceptions warrant focused follow-up, not broad re-review:**

- `US-Wkg 2025-03-07 12:00–13:00`: source QC0 TA -1.708°C at 12:00 and -4.120°C at 12:30 after +6.315°C at 11:30, source processed `TA_ERA` around +10°C. Stage74 repaired the negative RH numerically at 12:30 by changing original QC1 VPD from 9.560 to 0.051 hPa, maintaining suspicious -4.120°C source TA. This numerically valid RH=98.87% does **not** independently validate source TA; inspect the anomalous source temperature segment before applying this row in production.
- `US-Wkg 2025-09-10 13:00`: source QC0 TA=12.890°C between QC0 29.520°C at 12:30 and QC0 23.470°C at 13:30; source processed TA_ERA≈29.396°C. Stage74 repaired source negative RH only, changing VPD 18.952→8.404 hPa, RH→43.44%, while leaving the suspect TA unchanged. Rain/storm conditions make an actual cooling episode possible but **do not prove** the extremely rapid drop/rebound. Review this single temperature excursion locally before using its modified RH/VPD in production.

**Exception bookkeeping:** both numerical RH/VPD fixes are currently *present* in the SHA-verified **259-row** research-approved versioned overlay and are **not** secretly deleted or unapproved by this README update. Flag the **source-temperature evidence** for targeted follow-up, keep all other Stage74 science approvals and three original-row PASS decisions intact. A production integration/release decision must avoid silently treating the two source-T exception rows as physically verified solely because the repaired RH became >=0. This is not a new site-wide HOLD.

### US-WCr Stage75 verified and Stage76 direct-repair implementation (29 October 2026)

**Operator-verified Stage75 read-only result:** US-WCr 24 original P2/P3 episodes / **62 native HH** source T/VPD/QC all verified against original archive SHA256 `f13c3a26a051bbe351fe5aa66a2cd7eef3849b33645732810bfc74a34c5e6f75`. **61** HH have derived RH<0 (direct scientific repair per the operator rule), **one** `2011-05-26 08:00` has RH=0.33% (pass original unchanged). QC pairs: 60 original `TA_F_QC=0,VPD_F_QC=1`, two original `TA_F_QC=1,VPD_F_QC=2`.

**One visibly anomalous original-source temperature episode:** `2016-10-01 08:30–11:30`, notably source QC0 T at 10:30 −43.523°C despite original source processed ERA ≈14.2°C, QC1 T at 09:30 −21.173°C, 10:00/11:30 −13.734°C; native plausible temperatures at 08:00 11.783°C, 09:00 11.701°C, 11:00 16.055°C and 12:00 16.910°C. These known-bad QC0 values **cannot** serve as source-priority interpolation anchors. The 2016 event therefore uses a documented local same-time native source interpolation exception that repairs five corrupted TA records, two of them in the 61 flagged RH-negative HH, with original VPD unchanged. Other 59 negative RH rows are directly repaired by physically bounded nearest-neighbor inferred RH interpolation at original selected T (source processed ERA RH is a fallback if no finite dual bracket exists); the one nonnegative HH passes unchanged.

[Stage76 actual source-audit-informed direct repair script and pinned command](docs/STAGE76_US_WCR_61_NEGATIVE_RH_AND_20161001_OBVIOUS_T_SENSOR_20261029.md). **Expected after operator IRIDIS6 success:** previous 259 approved records exactly retained + **64 new WCr records** (61 original flagged repairs plus 3 extra physically erroneous temperature context) = **323 versioned approved HH**, 0 new operator-level review HOLD. This is a *predicted post-run outcome*, not yet a verified Stage76 completion. All source files, original QC, model forcing, DATM/CIME and Slurm are unchanged.

## ACTIVE Batch05 operator rule — temperature source-QC transitions and contiguous blocks (29 October 2026)

**Investigator instruction (takes precedence over older Stage66/67 temperature-transition HOLD guidance):** When reviewing or repairing a sudden jump in `TA_F` associated with source-QC grade changes, **respect the hierarchy of actual source provenance**: `TA_F_QC=0` source tower measurement, `1` MDS gap-fill, `2` source processed ERA replacement. Use the **preceding higher-priority grade as both bracketing interpolation anchors** for the following lower-priority grade, *including an entire contiguous block of those lower-priority values*, not merely the first flagged half-hour.

| Original TA source transition at a suspect jump | Target to reconstruct | Required donor anchors | Default operator choice |
|---|---|---|---|
| `QC0 → QC1` | All contiguous QC1 half-hours after that boundary (one HH or a full run) | Native QC0 `TA_F` immediately **before and after** the QC1 run | Linear temporal interpolation between the two QC0 measured temperatures |
| `QC1 → QC2` | All contiguous QC2 half-hours after that boundary (one HH or a full run) | Native QC1 `TA_F` immediately **before and after** the QC2 run | Linear temporal interpolation between two original QC1 MDS-fill temperatures |

**The user's source priority is `0 > 1 > 2`; never interpolate from QC2 to replace QC1 where the requested QC1 donor is available, nor use QC1 as the default donor for QC0→QC1.** Read each original native `TIMESTAMP_START`/QC series; identify the **maximal contiguous target-QC interval**, and interpolate all its points together using actual elapsed time. The rule is about **how to repair an identified suspicious transition**, not a directive to rewrite every valid QC1 or QC2 source value anywhere in the record. Retain the immutable original source numerical `TA_F`, `TA_F_QC`, other QC labels and existing approval ledger. Store each approved replacement in a separate, SHA-validated, versioned repair overlay, with original source values, timestamps, source/donor QC, boundary donor values and interpolation method explicitly recorded.

If a requested source QC0/QC1 donor is absent, source native clock is discontinuous, or the run has no complete two-sided same-grade bracket, **do not invent an anchor, silently use a different QC grade, or mislabel original QC**. Under the investigator's Stage67 disposition, pass that unrepairable *temperature-transition* run **unchanged and document `PASS_KEEP_ORIGINAL` rather than retain a pending operator HOLD**. This disposition does not override any independent *physically impossible* RH event: the separate site-wide operator rule is that **source-derived RH<0% must be repaired directly**, not sent through another manual candidate-approval round.

For RH/VPD, treat the source `TA_F_QC` and `VPD_F_QC` as independent provenance codes. Use `e_s(T)=6.112 exp(17.67 T/(T+243.5))` hPa and `RH=100(1-VPD/e_s(T))` for the numerical screen. If original source tower temperature is physically credible, retain it and repair only inconsistent QC1 VPD by approved, physically bounded RH interpolation/recomputed VPD. **Exception for demonstrably corrupt nominal QC0 temperature**: US-Wkg original `2020-02-18 12:00–14:30` reports exactly 0°C QC0 under daytime SW radiation, whereas two original QC0 boundary temperatures are 17.510°C and 20.850°C; its six HH are restored in a separate, explicitly labeled temperature-repair overlay, preserving original QC0 labels and not inventing measured data. Do not automatically trust a nominal QC0 label in the face of such verified numerical source corruption. Any new corrected temperature must be checked against dependent RH/VPD/QBOT and pressure before model forcing is promoted.

**Batch05 actual science state:** US-Whs Stage67 temperature decisions: 30/30 original ≥5°C transition boundaries disposed; 51 interpolated TA HH accepted and ten no-anchor/too-long target runs passed unchanged, not source edits. US-UMd Stage69 actually executed 15 RH<0 HH → **219 approved RH/VPD overlay HH**. US-UMB Stage72 **actually executed successfully**, another 21 directly repaired and one positive RH HH passed unchanged → **240 approved RH/VPD overlay HH**. US-Wkg Stage74 originally failed on a Python formatter name collision *before* writing the new output; the fix has been pushed, **259 approved HH is the expected result only after a successful rerun**, not yet verified from the operator's terminal log. Do not conflate these RH/VPD approved overlays with the separate US-Whs 51 temperature repair records unless an explicit integration pass and source-scope check has been performed. None of the listed script runs replaced original downloads, active DATM/CIME or submitted Slurm model jobs.

[Stage67 US-Whs temperature decisions](docs/STAGE67_US_WHS_USER_DIRECTED_QC1_QC2_QC0_QC1_TA_CANDIDATE_REPAIRS_20261029.md) · [Stage69 US-UMd / Stage70 US-UMB](docs/STAGE69_70_UMD_DIRECT_APPROVED_219_AND_UMB_NEXT_MANUAL_20261029.md) · [Stage72 US-UMB](docs/STAGE72_UMB_21_DIRECT_APPROVAL_AFTER_STAGE69_219_20261029.md) · [Stage74 US-Wkg](docs/STAGE74_US_WKG_19_NEGATIVE_RH_DIRECT_REPAIR_AND_2020_TA_QC0_ZERO_20261029.md)

**经用户确认的简明规则：温度异常出现 QC0→QC1，用该连续 QC1 区段前后两侧 QC0 实测温度插值；出现 QC1→QC2，用该连续 QC2 区段前后两侧 QC1 填补温度插值。无可靠双侧同等级锚点则原值通过，不伪造插值或修改原始 QC。反推 RH<0 的物理异常按独立规则直接修复并保留原始来源记录。**

**Status (2026-10-25): Stage00 upload/checksum 10/10 verified; Stage01 extraction 10/10 verified; Stage02 complete original native time PASS 10/10, with metadata review US-UMB/US-Vcp and scientific review required for all ten. Stage03 read-only humidity QC / ERA5 clock scout executed successfully 10/10 (operator log); Stage04 full-event ERA provenance/paired-physics shadow executed 10/10, with 3,129 abnormal source timestamps fully matched to ERA printed labels; Stage05 original RH/QC/phase audit executed successfully 10/10 (3,541,632 HH; 47,267 RH differences >10pp; 503,174 RH missing); Stage06 RH disagreement episode/source-header audit completed 10/10 (6,782 continuous episodes, 47,267 severely discordant RH records); Stage07 QC/ERA/MDS inheritance audit complete 10/10 (50,287 event timestamps, 9,632/9,632 VPD-QC2 matches ERA, 9,018/9,018 TA-QC2 matches ERA); Stage08 all-row consolidated provenance and MDS alternatives PASS 10/10: 3,541,632 records, 0 inconsistent source-selection, 1,750 low-derived-RH screens (700 MDS-pair mathematically feasible, 1,050 nonphysical); Stage09 read-only low-RH triage completed 10/10 (1,750 records: 1,559 negative, 191 nonnegative <1%; 170 without ERA/tower-T physically feasible pairing); Stage10 SHA-verified report-only export DONE 10/10 (1,750 original humidity flags, 1,559 negative) at review_20261025T180413Z_682688; Stage11 existing Stage10 review ledger QA PASS 10/10 (229 mathematically feasible unapproved bracketed interpolation candidates, 1,510 lacking both QC0 anchors, 11 nonphysical interpolations, 170 overlapping ERA-pair holds, 27 negative measured-QC0/0 source events); Stage12 original native temporal context report COMPLETED 10/10 (382 unique priority records from 1,750 low RH flags, 4,966 original HH contextual rows, approved=0); Stage13 independent native-context QA DONE 10/10 (382 priority events/4,966 original HH, 229 bracketed interpolations reproduced, 27 measured negative RH discrepancies all <=0.2 percentage points, 0 forcing repairs); Stage14 science sensitivity report completed 10/10 (240 bracketed trials, 173 change >5 hPa; 27 source QC0/0 near-zero RH checked with Magnus/Buck/Tetens, only one nonnegative under Buck/Tetens; no forcing changes); Stage15 full 1750-event source-provenance/hold inventory PASS 10/10 (VPD QC0=119, QC1=965, QC2=666, negative=1559, original RH missing=1605, approved=0); Stage16 report-only source-pair study PASS 10/10 (MDS pair 700/1050 physical/nonphysical; ERA pair 1695/55; mixed TA_F+ERA VPD 1102/648; ERA vapor e+TA_F 1580/115 among 1695 valid ERA pairs; approved=0). Stage17 original native 1,750-HH source anomaly episode manifest COMPLETED 10/10 (522 continuous native episodes: P1 human review 39, P2 meteorological evidence needed 89, P3 remaining source-reference check 394; approved 0). FORCING HAS NOT BEEN MODIFIED. NO model-ready forcing has been approved.**

Fifth independent ten-site AmeriFlux campaign, following [Batch04](../AmeriFlux_MultiSite_10_Batch04/). Current scope is transfer, CSV extraction and structural inventory. Raw data are not committed to GitHub.

## Exact ten-site release manifest

| Site | Expected original archive | Release-year labels |
| --- | --- | --- |
| US-UiD | `AMF_US-UiD_FLUXNET_2008-2024_v1.3_r1.zip` | 2008–2024 |
| US-UMB | `AMF_US-UMB_FLUXNET_FULLSET_2007-2021_3-5.zip` | 2007–2021 |
| US-UMd | `AMF_US-UMd_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-Var | `AMF_US-Var_FLUXNET_2000-2025_v1.3_r1.zip` | 2000–2025 |
| US-Vcm | `AMF_US-Vcm_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-Vcp | `AMF_US-Vcp_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-WCr | `AMF_US-WCr_FLUXNET_1999-2025_v1.3_r1.zip` | 1999–2025 |
| US-Whs | `AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-Wjs | `AMF_US-Wjs_FLUXNET_2007-2025_v1.3_r1.zip` | 2007–2025 |
| US-Wkg | `AMF_US-Wkg_FLUXNET_2004-2025_v1.3_r1.zip` | 2004–2025 |

Machine-readable source: [sites.tsv](sites.tsv). Names and years are supplied by the operator, not independently verified temporal coverage, cadence, QC or PFT classification. **US-UMB deliberately retains the distinct `FLUXNET_FULLSET_2007-2021_3-5` release name.** Its content/schema will be inspected separately after transfer. US-UiD and US-UMd remain distinct, with case preserved.

## Stage00 — run in LOCAL WSL

Windows source: `D:\Fluxes_Tower_Experiment\Ameriflux`; WSL mount: `/mnt/d/Fluxes_Tower_Experiment/Ameriflux`. Run the following in local WSL, not on IRIDIS or native PowerShell:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch05'
  BASE="$HOME/ameriflux_batch05_transfer"
  mkdir -p "$BASE/scripts/stage00"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage00/00_upload_ameriflux_batch05.sh"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage00/00_upload_ameriflux_batch05.sh" -o "$SCRIPT"
  bash -n "$SCRIPT"
  LOCAL_ROOT='/mnt/d/Fluxes_Tower_Experiment/Ameriflux' \
    bash "$SCRIPT" 2>&1 | tee "$BASE/upload_$(date +%Y%m%d_%H%M%S).log"
)
```

Requires Bash, curl, ssh, rsync, sha256sum, find, awk, mktemp and head. [Transfer script](scripts/stage00/00_upload_ameriflux_batch05.sh) follows Batch04's implementation with only batch labels/socket prefix changed.

The full ten-site source preflight finishes before SSH connects. Each source must be an exact `<package>.zip` (case-insensitive match) or an exact same-named release directory. A ZIP takes priority if both are present. Missing or ambiguous sources stop execution; packages are never renamed or repacked.

One SSH master connection to `ly3n24@iridis6.soton.ac.uk` handles all transfers and checks. Authentication normally occurs once; a lost master stops the script rather than opening another password session. Logs remain in `$HOME/ameriflux_batch05_transfer/` on WSL. Rerun the same command to resume.

Remote layout:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/packages/<EXACT-PACKAGE>.zip
```

Same-named source directories go under `packages/<EXACT-PACKAGE>/`. Existing final destination files are preserved with `rsync --ignore-existing`; a different checksum is a hard stop, not permission to replace data. Interrupted uploads use rsync partial files. ZIPs receive local/remote SHA256 checks; directories receive recursive checksum comparison, including detection of unexpected remote files (`--delete` is dry-run only). Local originals are retained.

Only a complete run may print:

```text
UPLOAD VERIFIED: 10/10 (AmeriFlux Batch 05). Originals retained. No extraction or model jobs started.
```

Publication of these scripts is **not** evidence that transfer succeeded. Record actual sizes/checksums and operator output after the run. No extraction, forcing repair, DATM, surface generation or Slurm submission occurs in Stage00.

## Stage00 operator result — 10/10 VERIFIED

The operator supplied the final successful upload line on 2026-10-25. See the [transfer evidence ledger](docs/STAGE00_TRANSFER_VERIFIED_2026-10-25.md). The visible excerpt contains sizes and SHA256 for the last four sites; no hashes for the first six are invented. Stage01 records the SHA256 of each source ZIP in its own new inventory report.

## Stage01 — run on IRIDIS6

[Extraction script](scripts/stage01/01_extract_ameriflux_batch05.py), adapted from Batch04. It requires only Python 3's standard library, validates the exact ten-site release manifest, extracts CSV products (including nested ZIPs), checks destination size/CRC, skips identical existing outputs and refuses to overwrite different CSVs. Original packages remain intact.

US-UMB is explicitly inventoried as FULLSET, separately from FLUXMET. Missing BIF or separate ERA5 companions for FULLSET are reported as metadata/source gaps for subsequent investigation. Both HH and HR products are preserved; filenames are not proof of actual cadence. This stage checks headers and the first row only; full time continuity, variable units, source QC, metadata and meteorological science remain later work.

Execute on IRIDIS6, after the successful Stage00 upload:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch05'
  BASE="$HOME/ameriflux_batch05_stage01"

  mkdir -p "$BASE/scripts/stage01"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"

  SCRIPT="$BASE/scripts/stage01/01_extract_ameriflux_batch05.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage01/01_extract_ameriflux_batch05.py" -o "$SCRIPT"

  python3 -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 |
    tee "$BASE/stage01_$(date +%Y%m%d_%H%M%S).log"
)
```

Success ends with `BATCH05 SUMMARY: 10/10 PASS (extraction/structure only); failures: none` and a `REPORT:` path. Operator execution now passed 10/10; see the [Stage01 evidence ledger](docs/STAGE01_EXTRACTION_VERIFIED_2026-10-25.md).

Extracted CSVs: `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/raw/<EXACT-PACKAGE>/`.

New timestamped JSON inventory: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch05/reports/stage01_extraction_*.json`.

Optional CLI: `--audit-only` (no extraction/report writes), `--sites US-UMB`, `--sites-root PATH`, `--reports-dir PATH`. Self-test uses synthetic temporary archives only and checks nested ZIPs, FULLSET/FLUXMET, HH/HR labels, reruns, overwrite refusal and unchanged source ZIP SHA256s. No forcing, DATM, CIME or Slurm jobs are created in Stage01.

## Stage02 — original metadata, complete HH/HR chronology and basic met screen

[Stage02 read-only auditor](scripts/stage02/02_audit_batch05_metadata_time_met.py) was locally tested on all ten synthetic release layouts (including FULLSET without BIF and an hourly source) and has now been run on all ten actual IRIDIS6 source files by the operator; see the Stage02 results below.

It validates the exact Batch05 manifest; inventories original BIF coordinate/location groups, IGBP and height records; scans every native FLUXMET or FULLSET HH/HR record for malformed timestamps, durations, gaps, overlaps and missing values; records source CSV SHA256s, field names, source QC counts, extremes and up to three timestamped examples per flag. Conflicting coordinate candidates are retained for review; no coordinate is selected for model inputs. If BIF is absent (possible for FULLSET), it still scans the site's full meteorology series and marks metadata for follow-up. All available HH/HR files are scanned; none is automatically chosen as forcing.

Screening assumptions are explicitly TA in degC, VPD in hPa, PA in kPa and RH in percent. Derived RH uses a water-saturation formula only; subzero water/ice cases and release-specific units need later verification before repair. Source labels and original QC are reported, not treated as independent ERA validation. Threshold flags are evidence for later work, not automatic replacement decisions. Full native Gregorian chronology is preserved, including leap days; no NO_LEAP conversion or time-zone shift occurs. Label-year boundary differences are printed separately from internal continuity.

Run on IRIDIS6:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch05'
  BASE="$HOME/ameriflux_batch05_stage02"

  mkdir -p "$BASE/scripts/stage02"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"

  SCRIPT="$BASE/scripts/stage02/02_audit_batch05_metadata_time_met.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage02/02_audit_batch05_metadata_time_met.py" -o "$SCRIPT"

  printf '%s  %s\n' \
    'eb16d333f515cb85500aca0f1b384af0c2fa3204ec64bad02ec48d55cad6b199' "$BASE/sites.tsv" \
    'fc3caa5ca8589aae2369f5343efa25dd71e65ac0b3d7ae7db7c8d19343d20402' "$SCRIPT" |
    sha256sum -c -

  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 |
    tee "$BASE/stage02_$(date +%Y%m%d_%H%M%S).log"
)
```

The audit itself writes no files. Shell `tee` saves its output under `$HOME/ameriflux_batch05_stage02/`. A normal completion prints `STAGE02 SUMMARY` with separate time, metadata and science review lists. Review flags are findings; exceptions produce `failed=` entries and a nonzero exit. Time PASS is internal chronology only; compare the separately printed label-boundary screen. Missing coordinates, IGBP or physical anomalies do not silently become approved inputs. Use `--sites US-UMB` for a focused rerun. No meteorological repairs, downloaded reanalysis, surfaces, DATM, PFT/ZBOT choices or model jobs are produced.


## Stage02 actual IRIDIS6 result — PASS 10/10 for native chronology

The operator's complete Stage02 output on 2026-10-25 is recorded in the [Stage02 evidence ledger](docs/STAGE02_FULL_NATIVE_AUDIT_2026-10-25.md). Every site reports `TIME PASS` and `LABEL_BOUNDARY_SCREEN FULL_LABEL_YEARS`. Metadata review: **US-UMB** (no BIF in FULLSET) and **US-Vcp** (two coordinate/elevation candidates). Derived water RH is negative at a total of **1,559 half-hour records** across the batch; counts are screen diagnostics (TA degC / VPD hPa assumption), not certified repairs. All ten sites need scientific QC. Stage02 performed no writes to the extracted source files.

## Stage03 — humidity-event source QC + original ERA5 companion/clock scout (read-only)

[Stage03 source](scripts/stage03/03_review_humidity_qc_and_era5_clock.py) inventories native TA/VPD/RH abnormal events with their original QC, per-year distributions and sample timestamps; separately inspects the matching original ERA5 CSV's header/schema, time span and available variables. It computes TA agreement diagnostics across **integer-hour offset hypotheses −12..+12** using a limited set of QC0 source-TA anchors. It **does not select an offset** or declare any ERA5 record scientifically valid. Sub-hour offset requirements and units must be checked before any replacement. If the ERA5 candidate does not contain a recognizable TA column, this is reported without inventing one.

Run on IRIDIS6 (main branch script is downloaded; verify filename, syntax and self-test before full scan):

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage03"
  SCRIPT="$BASE/03_review_humidity_qc_and_era5_clock.py"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage03/03_review_humidity_qc_and_era5_clock.py" \
    -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage03_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Output includes `ORIGINAL_AUDIT`, `ERA_SCOUT`, `SITE_AUDIT_DONE` and `STAGE03 SUMMARY: audited=10/10 failed=none` on successful data scans. The program writes **nothing to the source**; only the command's `tee` creates a local log. Interpretation of the source and ERA5 clock, replacement decisions, ZBOT, PFT, and all forcing/model modifications remain pending.


## Stage03 operator result — executed 10/10 (2026-10-25)

**Verified from the complete supplied Stage03 log:** `audited=10/10 failed=none`. All ten source and original release-bundled ERA5_HH companions are available; no ERA companion RH column was detected. There are **1,559** derived water-RH-negative half-hours, **1,750** derived water-RH<1% half-hours, **1,296** native RH>100 records, and **201** native RH<1 records; these sets overlap. The complete source-derived tables and source/ERA examples are recorded in [Stage03 evidence and scientific interpretation](docs/STAGE03_HUMIDITY_ERA_PROVENANCE_2026-10-25.md).

**Critical discovery:** US-Vcm has abnormal native TA/VPD examples identical to bundled ERA values; US-Vcp and US-Wjs have abnormal VPD values identical to ERA but much colder native TA. **Blindly replacing abnormal VPD with the bundled VPD_ERA would not resolve those records.** Stage03 offset rankings from sparse temperature samples do not authorize shifting any timestamps.

## Stage04 — complete event-level original / ERA humidity provenance (READ ONLY)

[Stage04 script](scripts/stage04/04_full_native_era_humidity_provenance.py) performs an exact-label comparison of **every** flagged native humidity record (not just Stage03's 12 per-site examples). It separates inherited ERA VPD from temperature incompatibility, evaluates ERA-internal vapour-pressure nonnegativity and computes a provisional physically constrained native-T+ERA-vapour-pressure candidate without writing it. Exact-label comparison is purely diagnostic; clock alignment, grid/height corrections, ice-phase physics, independent ERA5-Land science and model readiness remain **unapproved**.

Execute on IRIDIS6:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage04"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  SCRIPT="$BASE/04_full_native_era_humidity_provenance.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage04/04_full_native_era_humidity_provenance.py" \
    -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage04_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected successful final line: `STAGE04 SUMMARY audited=10/10 failed=none`. The source itself writes nothing; `tee` writes a shell log. Operator output will determine the next evidence-gated repair design. There is **no** forcing overwrite, timestamp shift, ERA adoption, DATM construction or Slurm model job.


## Stage04 actual IRIDIS6 run — complete 10/10 (2026-10-25)

The operator's full console output reports `STAGE04 SUMMARY audited=10/10 failed=none`; full site table and scientific caution are in [Stage04 evidence ledger](docs/STAGE04_FULL_EVENT_ERA_PAIR_SCREEN_2026-10-25.md). Of **3,129** distinct flagged half-hours, **2,336** have a mathematically feasible ERA-vapour-pressure / tower-temperature pairing, **738** do not, and **55** have ERA-internal physically inconsistent humidity under the stage's water-saturation assumption (US-Vcm 52, US-Vcp 3). **762** event rows have native VPD numerically identical to the bundled ERA VPD. None of these is a completed repair, and same-label joins do not establish UTC alignment.

## Stage05 — original RH provenance and frozen-temperature sensitivity (READ ONLY)

Published: [`scripts/stage05/05_native_RH_provenance_phase_screen.py`](scripts/stage05/05_native_RH_provenance_phase_screen.py). It re-audits all native rows, fingerprints each original source against the exact SHA256 logged in Stage04, compares the original RH field to the independent *calculation* from TA/VPD, tabulates near-identity and large disagreements by original TA/VPD QC, and separates water/ice saturation formula results below 0C. **This statistical comparison does not establish whether the original RH field is independently observed or an intermediate processed variable.** It writes no source files.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage05"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  SCRIPT="$BASE/05_native_RH_provenance_phase_screen.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage05/05_native_RH_provenance_phase_screen.py" \
    -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage05_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected on a successful operator run: `STAGE05 SUMMARY audited=10/10 failed=none`. This is an expectation, not a claimed run. Stage05 **does not** change timestamps, forcing, CIME, DATM, surface files or Slurm queues.


## Stage05 operator result — completed 10/10 (2026-10-25)

The operator's Stage05 source SHA fingerprints and self-test passed at IRIDIS6; `STAGE05 SUMMARY audited=10/10 failed=none`. Across 3,541,632 native HH records, 503,174 original RH values are missing; 47,267 populated-RH cases disagree by more than 10 percentage points with the RH calculated from original `TA_F` and `VPD_F` using water saturation. The major sites are US-Vcm (16,065), US-Vcp (10,509), US-WCr (12,425). All severe discrepancies occur under TA/VPD QC1/1 (38,278), QC2/2 (8,981), or QC1/2 (8); none occur under QC0/0. For 503 subfreezing low-derived-RH records, substitution of the Stage05 ice formula leaves all 503 below 1% RH. These are screening counts, not proof of independently measured RH or of the QC categories' processing meaning. See the full [Stage05 evidence ledger](docs/STAGE05_NATIVE_RH_PROVENANCE_2026-10-25.md).

## Stage06 — source-lineage candidates and contiguous severe-RH discrepancy episodes (READ ONLY)

[Stage06 auditor](scripts/stage06/06_rh_disagreement_lineage_and_episodes.py) scans all 10 original native CSVs, validates the operator-reported Stage05 SHA256 for each, reports any **actually present** unsuffixed TA/VPD columns and their equality with processed TA_F/VPD_F, quantifies original-RH vs derived-RH discrepancies by original QC pair, and reports the longest contiguous >10 percentage-point mismatch episodes. RH remains a *candidate with unverified provenance*, not an adopted input. No original CSV/forcing write, timestamp shift, ERA5 adoption or Slurm submission occurs.

Run on IRIDIS6:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage06"
  COMMIT="a6d0db95e575f8159c8cecbe8561615ccc1f7e1e"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/06_rh_disagreement_lineage_and_episodes.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage06/06_rh_disagreement_lineage_and_episodes.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "31d9db0179fc9743b8058f90119dbfb734f8426b"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage06_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

On a successful operator run, the script prints `STAGE06 SUMMARY audited=10/10 failed=none`. Stage06 has been published but **not yet run** on the user's full IRIDIS6 dataset.


## Stage06 actual IRIDIS6 operator run (2026-10-25) — PASS 10/10

[Complete Stage06 result, 10-site episode table, and QC documentation](docs/STAGE06_SEVERE_RH_EPISODES_AND_QC_PROVENANCE_2026-10-25.md): 3,541,632 original HH records scanned; 47,267 source-RH differences >10 pp in 6,782 distinct contiguous episodes. The longest is US-Vcm 297 half-hours (148.5 h) spanning 2023-03-04 05:00 to 2023-03-10 09:00 (printed source timestamps, local-standard convention). No independent unsuffixed TA/VPD columns were found in the ten **selected** native FLUXMET/FULLSET files; other source packages have NOT been excluded.

**Official FLUXNET meanings** for `TA_F_QC` and `VPD_F_QC`: 0 = measured; 1 = good-quality gapfill (MDS); 2 = downscaled ERA. See https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/ and https://fluxnet.org/data/fluxnet2015-dataset/variables-quick-start-guide/. QC2 inherited ERA values must **not** be replaced with the very same companion ERA values. The official dataset time convention is *local standard time without DST* (https://fluxnet.org/data/fluxnet2015-dataset/); do **not** adopt Stage03 correlation-based shifts. Source-release and site-specific metadata still require verification.

## Stage07 — verify actual gapfill lineage, MDS availability, and QC2 ERA value inheritance (READ ONLY)

[Stage07 script](scripts/stage07/07_verify_fluxnet_qc_lineage_and_era_inheritance.py) scans all native HH rows for physical humidity alarms or disagreement; checks original hashes against Stage06; inventories optional `TA_F_MDS/VPD_F_MDS` columns without inventing them; and joins flagged native records to original release-bundled `ERA5_HH` by **printed source timestamp** solely to audit QC2 inheritance. This is NOT a source repair; `RH` is not assumed to be independent or measured.

On IRIDIS6:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage07"
  COMMIT="c04ae1454a4ee506588092cd08c01773c5885e84"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/07_verify_fluxnet_qc_lineage_and_era_inheritance.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage07/07_verify_fluxnet_qc_lineage_and_era_inheritance.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "184fe85ce0756ce22b069d8cd26bf8b9cfee816e"
  echo "STAGE07 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage07_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

On a successful run, expect `STAGE07 SUMMARY audited=10/10 failed=none`. The code has been committed and hash-verified on GitHub but its operator self-test and real IRIDIS6 run are **pending**. The script does not overwrite source files, build forcing, change clocks or submit jobs.


## Stage07 — actual IRIDIS6 source-lineage result 10/10 (2026-10-25)

Stage07 passed original SHA fingerprints and `STAGE07 SUMMARY audited=10/10 failed=none`. All 50,287 screened source-flagged timestamps have an exact printed-label release `ERA5_HH` companion record. Among **only those flagged rows**, QC2 `TA_F` matches `TA_ERA` for 9,018/9,018, and QC2 `VPD_F` matches `VPD_ERA` for 9,632/9,632. Likewise 41,269/41,269 flagged QC0/1 TA and 40,655/40,655 flagged QC0/1 VPD agree with available `*_F_MDS`. **These are a confirmed consolidation/source-lineage relationship, not independent source agreement or model forcing approval.**

Of those Stage07 anomalous rows, 346 had an ERA TA/VPD pair that violates the present water-saturation assumption (US-Vcm 343; US-Vcp 3); this larger sample includes Stage04's 55 cases. Ten selected native FLUXMET/FULLSET files have `TA_F_MDS`, `VPD_F_MDS`, their MDS QC and `TA_ERA/VPD_ERA`, but no unsuffixed `TA`/`VPD` or `RH_QC`. See [Stage07 evidence ledger](docs/STAGE07_LINEAGE_AUDIT_2026-10-25.md). The difference between consolidated `*_F_QC` codes (0 measured, 1 good MDS, 2 ERA) and MDS `*_F_MDS_QC` codes (0 measured, 1 good, 2 medium, 3 poor) is essential; never auto-promote MDS QC2/3.

## Stage08 — all-row original source-selection and MDS alternative quality screen (READ ONLY)

Published: [Stage08 full 10-site original CSV check](scripts/stage08/08_full_consolidation_QC_and_MDS_alternatives_readonly.py). It scans **every** native half-hour, not just Stage07's 50,287 flagged points, comparing `*_F` with `*_F_MDS` at consolidated QC0/1, with `*_ERA` at consolidated QC2, and inventories `*_F_MDS_QC` 0–3 at QC2 events. It additionally counts any violations of the published F-variable source-selection convention and tests whether lower-quality MDS intermediate TA/VPD combinations are physically plausible — **never approving or writing an alternative**. Stage08 operator run is pending.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage08"
  COMMIT="803b725ece37472ddfde339aa4034a6bd51ae262"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/08_full_consolidation_QC_and_MDS_alternatives_readonly.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage08/08_full_consolidation_QC_and_MDS_alternatives_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "3eaf03109e8e80ae97aaa3fb0e1eb0d328bc03ca"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage08_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected when the real operator run succeeds: `STAGE08 SUMMARY audited=10/10 failed=none`. Stage08 has been committed and file hash checked on GitHub, but has **not** been executed on IRIDIS6. **NO original overwrite, RH adoption, fallback forcing, timestamp conversion, CIME case, or SLURM job.**


## Stage08 — actual operator run 10/10 (2026-10-25)

Full results: [Stage08 complete original row QC, provenance and MDS alternative science report](docs/STAGE08_FULL_CONSOLIDATION_AND_LOW_RH_2026-10-25.md).

**3,541,632** original half-hour rows scanned, all ten original SHA256 fingerprints matched: `STAGE08 SUMMARY audited=10/10 failed=none`. Source choice was fully consistent with the FLUXNET consolidation rules, across the entire series: **3,119,032/3,119,032** TA QC0/1 matched TA_F_MDS; **422,600/422,600** TA QC2 matched TA_ERA; **3,097,311/3,097,311** VPD QC0/1 matched VPD_F_MDS; **444,321/444,321** VPD QC2 matched VPD_ERA.

For the **1,750** `RH_water(TA_F,VPD_F)<1%` original source rows (**1,559** negative and **191** nonnegative), pairing original MDS TA and MDS VPD is *mathematically plausible* for **700** and nonphysical for **1,050**. **666** low-RH records inherit VPD_ERA (F_QC2); all have lower-quality VPD_F_MDS_QC2/3, so none can be indiscriminately promoted to MDS. **119** low-RH records have `TA_F_QC/VPD_F_QC=0/0`, requiring tower-observation review. Mathematical plausibility is not validation; source `RH` has no independently verified provenance.

## Stage09 — low derived-RH event triage (READ ONLY, operator run pending)

[Stage09 script](scripts/stage09/09_low_RH_source_resolution_readonly.py) scans the exact 10 original SHA-verified source files, splits `RH_water <0` (physically impossible under the stated water formula) from `0<=RH_water<1%` (extreme but not categorically impossible), and classifies each low-RH event by consolidated QC, MDS-QC, original RH availability, MDS-pair physics, ERA-pair physics, and the *hypothetical* pairing of ERA implied vapour pressure with original tower temperature. It prints only summaries, representative examples and longest contiguous low-RH episodes; writes no source/forcing.

IRIDIS6 commands:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage09"
  COMMIT="e1d5a0d5326d3f1187800588a65283c06a5fd90e"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/09_low_RH_source_resolution_readonly.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage09/09_low_RH_source_resolution_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "96b969a6e6dd8f9c1f29cddda91c98a522c3d642"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$BASE/stage09_$(date -u +%Y%m%dT%H%M%SZ).log"
)
```

Expected on operator success: `STAGE09 SUMMARY audited=10/10 failed=none`. This has **not** been run on the operator's IRIDIS6 data; the script has been published and reviewed but not executed in this session. No output forcing has been authorised.


## Stage09 — actual operator PASS 10/10, scientific triage (2026-10-25)

Full results: [Stage09 exact 1,750 original-source low-RH inventory and QC breakdown](docs/STAGE09_1750_LOW_RH_TRIAGE_2026-10-25.md). `STAGE09 SUMMARY audited=10/10 failed=none` and ten original SHA256 checks verified. Water-derived RH<1% at **1,750** original HH records, of which **1,559 strictly negative** and **191 nonnegative**. **1,605** original RH values missing, with 145 populated RH values of still-undetermined independent provenance. Original QC of the 1,750: 119 measured/measured, 961 measured/good-MDS, 479 measured/ERA, 4 good-MDS/good-MDS, 128 good-MDS/ERA, 59 ERA/ERA. Exactly 666 original anomalous VPD values are ERA-derived, and their alternative `VPD_F_MDS` has medium/poor QC2/3; never auto-promote.

Using the hypothetical ERA vapour pressure (ERA water saturation minus ERA VPD) with tower TA is mathematically possible for 1,580, not possible for 115 more, and ERA itself is internally nonphysical under this water formula in 55 records. **Mathematical feasibility is never approval for source replacement.** The 119 measured-pair records should have separate original measurement review; **27** are negative (26 US-WCr, 1 US-Vcm), **92** are nonnegative below 1% (US-Vcm). No forcing modifications have been approved or written.

## Stage10 — manual review report export, with strict no-model-write guard

[Stage10 original SHA256-verified event CSV exporter](scripts/stage10/10_export_low_RH_manual_review_ledger.py) writes **only new review reports** to an explicit, previously nonexistent `--output-dir`. It lists all 1,750 source-flagged HH and original TA/VPD/RH, consolidated/MDS QC, ERA/MDS physical feasibility, and a purely exploratory interpolated VPD if two measured physically coherent TA/VPD anchors exist within 3 hours on each side of the event. **It does not adopt the interpolation, modify original FLUXMET/ERA sources, create forcing, alter timestamps, edit CIME, or submit Slurm.** No output directory may overlap the source root or exist already.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage10"
  COMMIT="3d1630c7f2930acbeaa693c4bb77ffd7cbced382"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/10_export_low_RH_manual_review_ledger.py"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage10/10_export_low_RH_manual_review_ledger.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "b33e85901c7c0502f68985ead116fc1cae187a72"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/review_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --output-dir "$OUT" 2>&1 | tee "$BASE/stage10.log"
  echo "STAGE10_REPORTS=$OUT"
)
```

On success the operator should observe `STAGE10 SUMMARY sites=10/10 events=1750 negative=1559`, plus 10 event CSVs and `audit_summary.json`. The script is published but still needs execution and its self-test on IRIDIS6. **Reports are diagnostic artefacts, NOT replacements or model-ready forcing.**


## Stage10 actual operator run: 10/10 review CSVs generated (2026-10-25)

[Stage10 original run log, exact 10-site row counts, and report semantics](docs/STAGE10_OPERATOR_MANUAL_REVIEW_REPORTS_2026-10-25.md). Operator output confirmed **SOURCE VERIFIED**, **SELF-TEST PASS**, and `STAGE10 SUMMARY sites=10/10 events=1750 negative=1559`. Report-only path:

```text
/home/ly3n24/ameriflux_batch05_stage10/review_20261025T180413Z_682688
```

The Python exporter printed the resolved path under `/iridisfs/home/ly3n24/...`; the shell path was `/home/ly3n24/...`. Use `realpath` locally to confirm these address the same files. Exactly 10 `<SITE>_low_RH_review.csv` reports and `audit_summary.json` are expected under that directory. The source logs do not provide the actual per-site interpolation candidate counts, so do **not** invent how many are bracketed, or claim any interpolation is approved. Original data/forcing remained unchanged, and no model runs or jobs were started.

## Stage11 (READ ONLY): check report arithmetic and list human-review candidates

[Stage11 review CSV/JSON validator](scripts/stage11/11_audit_stage10_review_ledgers_readonly.py) reads only the existing Stage10 report directory: verifies row counts (1,750), negative (1,559), nonnegative <1% (191), original per-site summaries, native physical formula, source QC0/0 cases, interpolation math and 3h anchor bounds. It prints per-site diagnostic categories and priority examples; writes NOTHING. It is **not an automatic forcing repair**.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage11"
  COMMIT="5025119232ff2f3a5f66b0d4bbead831c61a972d"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/11_audit_stage10_review_ledgers_readonly.py"
  REPORTS="$HOME/ameriflux_batch05_stage10/review_20261025T180413Z_682688"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage11/11_audit_stage10_review_ledgers_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "905ba71593569d0ba9451a008eef1bf1bd9f1d69"
  echo "STAGE11 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  test -f "$REPORTS/audit_summary.json"
  python3 -B "$SCRIPT" --report-dir "$REPORTS" \
    2>&1 | tee "$BASE/stage11.log"
)
```

When the IRIDIS6 run genuinely succeeds, expect `STAGE11 SUMMARY sites=10/10 events=1750 negative=1559 nonnegative_below1=191 files_valid=10`. Stage11's GitHub blob was verified, but it has **not** been executed on the private IRIDIS6 reports. No original data/forcing writes, no time changes, no model or Slurm activity.


## Stage11 actual operator result — 10/10 PASS (2026-10-25)

[Stage11 source-grounded complete result](docs/STAGE11_REVIEW_LEDGER_VALIDATION_2026-10-25.md) confirms all ten Stage10 CSV ledgers agree with `audit_summary.json` and original math and bracket checks. The 1,750 cases split into:

- 229 interpolations with verified +/-3-hour QC0/0 anchor times and **mathematically feasible, not approved** interpolated VPD
- 1,510 without two qualifying QC0/0 observations within +/-3 h
- 11 interpolations whose numeric VPD candidate remains nonphysical (4 US-Vcm; 7 US-Wkg)
- 170 overlapping ERA-pair holds (115 hypothetical ERA implied vapor pressures inconsistent with tower TA, 55 ERA pair internally nonphysical under water formulation)
- 27 negative computed-RH source cases with measured TA/VPD (26 US-WCr, 1 US-Vcm)

**Do not equate formula-negative RH of around −0.1% in measured VPD with a defective tower sensor.** Original RH in 26 US-WCr measured-pair cases is 0%; this may be a saturation-equation / numerical-precision boundary issue. None of the event groups is model forcing ready.

## Stage12 — full original FLUXMET/FULLSET +/-3-hour temporal context for priority cases (NO REPAIRS)

[Stage12 original data context script](scripts/stage12/12_export_priority_low_RH_source_context_readonly.py) reads existing Stage10 event CSV, verifies source SHA256 again, and exports the native meteorology/QC/MDS/ERA values from 3 h before to 3 h after each unique priority event. Categories: 229 unapproved bracketed, 11 unphysical bracketed, 27 measured source negatives, and 170 ERA-pair holds (these overlap). Also validates source event-center values and both actual QC0 measured anchors for any bracketed case. Outputs **new** independent report CSV/JSON only — neither original sources, original Stage10 reports, forcing, model cases nor Slurm are touched.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage12"
  COMMIT="1afc927170d16919946982e7bfe2136d4d442960"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/12_export_priority_low_RH_source_context_readonly.py"
  REPORTS="$HOME/ameriflux_batch05_stage10/review_20261025T180413Z_682688"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage12/12_export_priority_low_RH_source_context_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "267753d59b23ee102bedeb2706c59cefb09b8b91"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/context_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --report-dir "$REPORTS" --output-dir "$OUT" \
    2>&1 | tee "$BASE/stage12.log"
  echo "STAGE12_REPORTS=$OUT"
)
```

Expected after actual IRIDIS6 success: `STAGE12 SUMMARY sites=10/10 original_events=1750 priority_unique=... context_rows=... approved=0 reports=...`. The number of **unique** priority events and rows of temporal context are not guessed from the overlapping categories and will be printed by the real run. Script created/pinned on GitHub, but user operator run and self-test are **pending**.


## Stage12 completed — real operator's source-context export (2026-10-25)

[Stage12 exact original 10-site operator counts and science evidence](docs/STAGE12_NATIVE_TEMPORAL_CONTEXT_2026-10-25.md).

- Original ten site files were SHA256 verified; source and Stage10 reports were left unchanged; no forcing, model cases, clocks or Slurm were touched.
- Original Stage10 input cohort = **1,750** low-derived-RH records; 4 scientific priority categories from Stage11 overlap, yielding **382 distinct priority target half-hours**.
- **4,966** original native contextual records extracted, exactly **13 half-hours per target** (±3 hours; duplicated context timestamps between overlapping target windows are intentional). No repair approved.
- Category membership counts remain **229 bracketed math-feasible but UNAPPROVED**, **11 bracketed still nonphysical**, **27 measured QC0/0 negative**, and **170 ERA/tower-T pairing holds**. Sum 437 memberships, 55 duplicates by category overlap. The other **1,368** low RH cases were not among selected Stage12 priorities and remain unresolved in Stage10.
- IRIDIS6 report folder:
  `$HOME/ameriflux_batch05_stage12/context_20261025T192426Z_1264512`.
  Three outputs: `stage12_priority_targets.csv`, `stage12_original_native_context.csv`, `stage12_summary.json`.

## Stage13 — full context and science-priority consistency screen (READ ONLY; operator run pending)

[Stage13 original-context QA Python script](scripts/stage13/13_check_native_context_science_readonly.py) consumes the three Stage12 outputs **without modifying them**; independently checks every target's exact 13 native HH timestamps/offsets, reproduces original derived water RH, reconstructs original QC0 observed anchor brackets for all **229** mathematical interpolation hypotheses, separates nonphysical brackets from physically plausible ones, and prints all **27** measured QC0/0 formula-negative original RH comparisons. Produces no replacement candidate forcing and makes no science approval.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage13"
  COMMIT="1a4774d39691d13de8fad1397f26491b94c651b2"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/13_check_native_context_science_readonly.py"
  REPORTS="$HOME/ameriflux_batch05_stage12/context_20261025T192426Z_1264512"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage13/13_check_native_context_science_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "5966fecb0940e3db640c9340b23e158d4fb65a3c"
  echo "STAGE13 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --stage12-dir "$REPORTS" \
    2>&1 | tee "$BASE/stage13.log"
)
```

Expected only when actual IRIDIS6 operation succeeds: `STAGE13 SUMMARY sites=10/10 priority=382 context=4966 interpolations_reverified=229 approved=0`. Stage13 is uploaded/hash-verified but **has not been executed on IRIDIS6**. The next science decision is whether further external independent weather observations and station metadata provide acceptable corrections, **not automatic substitution of ERA or a mathematically possible interpolation**.


## Stage13 actual operator science-context verification (2026-10-25)

[Stage13 original native context verified science report](docs/STAGE13_ORIGINAL_CONTEXT_REVIEW_2026-10-25.md). Real run output: `STAGE13 SUMMARY sites=10/10 priority=382 context=4966 interpolations_reverified=229 approved=0`.

- All original 13-HH contexts and original measured bracketing anchors independently reproduced for 229 (strictly unapproved) math-feasible interpolation candidates; the 11 other bracketed candidates remained physically inconsistent.
- The 27 negative water-formula RH values with consolidated measured TA/VPD `QC0/0` (26 US-WCr, 1 US-Vcm) **all** differed from the original populated `RH` by **<0.2 percentage points**. Absolute discrepancies 0.084182–0.108221 percentage points across the 27. Formula variation may materially affect their status near RH=0; native saturation formula and independence of original RH remain unverified.
- Large mathematically feasible interpolation changes: US-Var `201908190600` native VPD 21.747 hPa, straight bracket interpolation 0.11271 hPa (change **−21.63429 hPa**); this must not be applied without independent evidence.
- Neither RH nor VPD source was modified; no output forcing, model runs, time shifts or Slurm submissions.

## Stage14 scientific screen — report-only saturation formula sensitivity and 240 bracketed candidate magnitudes

[Stage14 script](scripts/stage14/14_compare_saturation_formulas_and_interpolation_risk_readonly.py) uses the **already generated** Stage12 CSV/JSON files; does not re-read entire 3.5M HH sources. For all 27 original `QC0/0` slightly formula-negative RH records, compares three explicitly hypothetical water saturation formulas (Magnus, Buck and Tetens) against original RH. For the 229 physically feasible + 11 nonphysical bracketed interpolation trials, verifies source QC0 anchors again and stratifies **absolute VPD changes** into <=1, >1–5, >5–10, >10 hPa. These are *scientific sensitivity screens*, not assertions about FLUXNET native calculation methods. All remain `HOLD_NOT_APPROVED`. New files are **review-only** CSV/JSON in a new directory, never original, Stage10, Stage12, forcing or CIME.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage14"
  COMMIT="82dd7ff57950401d7fbd18c01dc9309da4863f97"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/14_compare_saturation_formulas_and_interpolation_risk_readonly.py"
  REPORTS="$HOME/ameriflux_batch05_stage12/context_20261025T192426Z_1264512"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage14/14_compare_saturation_formulas_and_interpolation_risk_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "78bccf052b6bce94d6eb4cfc682e1e2caf068e15"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/science_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage12-dir "$REPORTS" --output-dir "$OUT" \
    2>&1 | tee "$BASE/stage14.log"
  echo "STAGE14_REPORTS=$OUT"
)
```

Operator expected success only after actual run: `STAGE14 SUMMARY sites=10/10 priority=382 context=4966 bracketed=229 nonphysical_bracketed=11 measured=27 approved=0`. Outputs: `stage14_all_240_bracketed_risk.csv`, `stage14_27_measured_saturation_formulas.csv`, `stage14_summary.json`. The current GitHub code is committed/verified and has not been executed against the private IRIDIS6 Stage12 CSVs.


## Stage14 actual operator execution (2026-10-25): PASS 10/10, 0 science approvals

[Stage14 complete source-derived science audit](docs/STAGE14_FORMULA_SENSITIVITY_AND_VPD_INTERPOLATION_RISK_2026-10-25.md). Source script hash, syntax and self-test passed; original Stage12 context examined without source or forcing changes. Operator reported `STAGE14 SUMMARY sites=10/10 priority=382 context=4966 bracketed=229 nonphysical_bracketed=11 measured=27 approved=0`.

All **240** bracketing results include **229** math-feasible but unapproved proposals and **11** nonphysical proposals. Absolute changes from source `VPD_F`: **25 <=1 hPa; 42 >1 to 5 hPa; 122 >5 to 10 hPa; 51 >10 hPa**; overall **173/240 (72.1%) >5 hPa**. No change magnitude provides scientific approval. In 27 measured QC0/0 near-zero source-RH cases, zero are RH>=0 under Magnus; only one (US-Vcm) is RH>=0 under Buck, and one under Tetens. All **26 US-WCr records remain slightly formula-negative under all 3 water curves**; native `RH` is approximately 0%, so source zero-floor/precision and native VPD calculation method remain unresolved. This **does not prove** that US-WCr is faulty or that formula choice can fix it.

Original Stage14 report directory:
`$HOME/ameriflux_batch05_stage14/science_20261025T194317Z_1261521`. Outputs are `stage14_all_240_bracketed_risk.csv`, `stage14_27_measured_saturation_formulas.csv`, and `stage14_summary.json` (data stays on IRIDIS6).

## Stage15: consolidate EVERY 1,750 original low-RH source event, not only 382 priority events

[Stage15 full 1750-event scientific provenance inventory](scripts/stage15/15_full_1750_provenance_triage_readonly.py) reads **only existing Stage10 and Stage14 report files**. It independently rechecks all 1,750 native event TA/VPD and low-RH formula, every original source `F_QC`, the exact 240 Stage14 interpolation candidates and the 27 Stage14 original measured-RH sensitivity cases. All records receive a single *mutually exclusive VPD-source provenance* — 119 measured `VPD_F_QC0`, 965 good MDS `VPD_F_QC1`, 666 ERA `VPD_F_QC2` — plus traceable overlay risk tags and evidence follow-up needs. **None is accepted as a correction**. It verifies the exact 382 focus-event union across the existing reports and preserves 1,368 not previously in Stage12 focus.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage15"
  COMMIT="8fa013e2ae1677222581ab7913dc6a6d215f1cb2"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/15_full_1750_provenance_triage_readonly.py"
  STAGE10="$HOME/ameriflux_batch05_stage10/review_20261025T180413Z_682688"
  STAGE14="$HOME/ameriflux_batch05_stage14/science_20261025T194317Z_1261521"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage15/15_full_1750_provenance_triage_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "14bc20e15c6bd0e784827955e4bbd514a2a4c96c"
  echo "STAGE15 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/triage_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage10-dir "$STAGE10" --stage14-dir "$STAGE14" \
    --output-dir "$OUT" 2>&1 | tee "$BASE/stage15.log"
  echo "STAGE15_REPORTS=$OUT"
)
```

Only if actual IRIDIS6 reports pass all validations will it print `STAGE15 SUMMARY sites=10/10 reviewed=1750 negative=1559 measured=119 good_MDS=965 ERA=666 approved=0`. The script generates **only a new review CSV and JSON**, never changes native data, existing Stage10/14 reports, forcing or model jobs. Stage15 is currently **published but NOT executed** against the IRIDIS6 reports.


## Stage15 operator PASS 10/10 — original source provenance consolidated (2026-10-25 22:42 UTC)

[Stage15 actual operator audit and ten-site evidence](docs/STAGE15_ALL_1750_SOURCE_PROVENANCE_2026-10-25.md). All 1,750 low-RH source records were cross-checked against the Stage10 source-ledger and Stage14 science trials; 1,559 are strictly water-formula-negative, 191 nonnegative under 1%. Selected VPD source provenance: QC0 measured 119, QC1 good MDS 965, QC2 ERA 666. Original RH missing 1,605. Stage12 exact priority native temporal contexts cover 382 events, leaving 1,368 without that special context review. All `science_status=HOLD_NOT_APPROVED`.

The mutually exclusive Stage15 priority ranks were: measured QC0/0 negative 27, original ERA pair internally nonphysical 55, measured QC0/0 extreme low RH 92, interpolated change >10 hPa 51, ERA implied vapor pressure incompatible with tower TA 94, MDS good-QC1 humidity followup 822, ERA-QC2 humidity followup 609. These rank counts sum to 1,750 and are not independent physical event category counts. Original forcing unchanged, no Slurm.

Original Stage15 report folder on IRIDIS6:
`$HOME/ameriflux_batch05_stage15/triage_20261025T224213Z_1292191` (which resolves to `/iridisfs/home/ly3n24/...`).

## Stage16: scientifically distinguish tower/MDS/ERA source pairs across all 1,750 (report-only)

[Stage16 Python source-pair diagnostic](scripts/stage16/16_audit_all_1750_source_pairs_readonly.py) uses only the **existing Stage10 and Stage15 reports**. It joins every original timestamp from both sources, re-verifies all selected QC0/QC1/QC2 provenance and original values, and independently assesses:

- `(TA_F,VPD_F)`: originally selected, already flagged;
- `(TA_F_MDS,VPD_F_MDS)`: alternative native MDS source pair, with its QC0/1/2/3 retained;
- `(TA_ERA,VPD_ERA)`: internally paired original downscaled ERA variables;
- `(TA_F,VPD_ERA)`: **direct VPD mix**, which differs from conserving ERA-specific actual vapor pressure;
- ERA-implied `e_ERA=e_sat(TA_ERA)-VPD_ERA` paired with `TA_F`: an **independent hypothetical shadow**, not a validated replacement.

It reports site-level QC and physics counts, estimates selected TA vs ERA TA and VPD vs ERA VPD differences, and exports all 1,750 events to a **new** CSV/JSON folder. **No inference of scientific validity from a physical bound alone. No source/forcing writes.**

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage16"
  COMMIT="c3057bfbf6c2aa4a3556de857bc9e9d0faa527f7"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/16_audit_all_1750_source_pairs_readonly.py"
  STAGE10="$HOME/ameriflux_batch05_stage10/review_20261025T180413Z_682688"
  STAGE15="$HOME/ameriflux_batch05_stage15/triage_20261025T224213Z_1292191"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage16/16_audit_all_1750_source_pairs_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "e7c1eeca9021a1d900516c0bb3db523d1d72ec83"
  echo "STAGE16 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/source_pairs_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage10-dir "$STAGE10" --stage15-dir "$STAGE15" \
    --output-dir "$OUT" 2>&1 | tee "$BASE/stage16.log"
  echo "STAGE16_REPORTS=$OUT"
)
```

A successful IRIDIS6 full report should end with `STAGE16 SUMMARY sites=10/10 events=1750 measured=119 MDS=965 ERA=666 approved=0`. The previously verified original source-pair physical bound counts expected for Stage16 are MDS feasible=700/nonphysical=1,050; internal ERA feasible=1,695/nonphysical=55; original ERA implied actual water vapor pressure paired with tower TA feasible=1,580/nonphysical=115. These are **shadow tests**: no original source changes or scientifically approved replacement follows merely from passing.

At 2026-10-25 the GitHub source file is committed and hash verified, but the operator Stage16 run/self-test on IRIDIS6 has not yet occurred.


## Stage16 executed and Stage17 ready (2026-10-25)

[Stage16 actual operator results](docs/STAGE16_FULL_1750_SOURCE_PAIR_AUDIT_2026-10-25.md): all 1,750 original low-RH source event rows were checked. Original VPD QC0=119, QC1=965, QC2=666. Source ERA pair was formula-physical in 1,695 but direct mixing source tower TA and source ERA VPD produced 648 formula-nonphysical pairs; preserving ERA's implied vapor pressure with tower TA yielded only 115 incompatible cases among 1,695 valid native ERA pairs. Large difference counts: 437 tower TA vs ERA TA >5°C, 629 source VPD vs ERA VPD >5 hPa. **This does not authorize changes.** Stage16 files on IRIDIS6: `$HOME/ameriflux_batch05_stage16/source_pairs_20261025T225516Z_1291407`.

[Stage17 native half-hour episode and metadata evidence manifest](scripts/stage17/17_build_episode_evidence_manifest_readonly.py) groups all 1,750 events by site and contiguous native half-hour timestamps into review episodes. It writes only a NEW evidence request directory with three files: `stage17_episodes_evidence_requests.csv`, `stage17_site_metadata_gates.csv`, `stage17_summary.json`. It never downloads or substitutes ERA, creates UTC offsets, or approves humidity repair. Before independent verification using raw ERA5-Land 2m temperature/dewpoint, original source clock offset, coordinates/elevation, source algorithm and sensor provenance must be established.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage17"
  COMMIT="861509c28c955add7257b4217ad7dd6d2cb8a005"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/17_build_episode_evidence_manifest_readonly.py"
  STAGE16="$HOME/ameriflux_batch05_stage16/source_pairs_20261025T225516Z_1291407"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage17/17_build_episode_evidence_manifest_readonly.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "a9d50595899fff1623806d1c588a297f10d98d4e"
  echo "STAGE17 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/episode_manifest_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage16-dir "$STAGE16" --output-dir "$OUT" \
    2>&1 | tee "$BASE/stage17.log"
  echo "STAGE17_REPORTS=$OUT"
)
```

**Pending**: operator Stage17 run; then manually investigate prioritized episodes and request independent source/evidence at verified native timestamps before deciding any scientifically approved forcing repairs.


## Stage17 completed: 522 episodes, source-level human review is required before any data replacement

[Stage17 actual operator human-review gate and P1 examples](docs/STAGE17_EPISODE_HUMAN_REVIEW_GATE_2026-10-25.md).

```text
STAGE17 SUMMARY sites=10/10 original_HH=1750 episodes=522 approved=0
ONLY NEW EVIDENCE REQUEST CSV/JSON; NO ORIGINAL/OTHER_REPORTS/FORCING/MODEL/SLURM WRITES
```

Real IRIDIS6 reports:
`$HOME/ameriflux_batch05_stage17/episode_manifest_20261025T230607Z_1291407`; source long-term total 1,750 anomalous half-hours grouped into **522** contiguous native source-time episodes:

- **P1: 39 episodes** require priority human scrutiny (US-Vcm 37; US-Vcp 1; US-WCr 1). Includes original QC0 extreme-low observed RH, near-zero source RH and ERA source itself nonphysical. These should not be auto-overwritten.
- **P2: 89 episodes** need physically independent weather evidence and source processing metadata before selecting a replacement; these are not safe just because the alternative source pair passes water-saturation formula.
- **P3: 394 episodes** carry ordinary provenance and independent-reference checks. They are *not* automatically cleared or scientifically resolved.

**A requested conditional automatic forcing edit is NOT triggered**: scientific human review is nonzero and source/clock/metadata evidence still incomplete. Do not overwrite original/production forcing, clip negative RH, use the same source ERA as independent confirmation, or substitute poor MDS QC2/3. Stage17 did not approve any repair.

On IRIDIS6, print precisely the 39 P1 review episodes from the completed original manifest:

```bash
python3 - <<'PY'
from pathlib import Path
import csv
f=Path.home()/"ameriflux_batch05_stage17/episode_manifest_20261025T230607Z_1291407/stage17_episodes_evidence_requests.csv"
with f.open(newline="",encoding="utf-8") as fh:
    rows=list(csv.DictReader(fh))
p1=[r for r in rows if r["priority_tier"]=="P1_MEASURED_OR_ERA_INVALID"]
assert len(rows)==522 and len(p1)==39
for r in p1:
    print(r["episode_id"],r["native_start"],r["native_end"],r["half_hours"],
          "QC0="+r["qc0_measured_HH"],"ERA_INVALID="+r["ERA_internal_nonphysical_HH"])
PY
```

Next science gate: review original site sensor/RH/VPD formula for measured QC0 periods, and compare verified same-clock local meteorology with freshly acquired ERA5-Land 2m T and dewpoint **after site longitude/latitude/elevation and UTC conversion are verified**. These remain scientific checks not approvals to modify any forcing.


## Stage18: original observed half-hour evidence pack for investigator decisions

The operator completed Stage17, identifying **522** native contiguous low-RH episodes from **1,750** original anomalous half-hours, with **39 P1 episodes** (US-Vcm 37, US-Vcp 1, US-WCr 1). The investigator requested all the actual original source numeric data for a human **KEEP / HOLD / REPLACE** decision. **None of the original source meteorology has yet been changed.**

[Stage18 read-only, SHA-pinned original met review exporter](scripts/stage18/18_export_p1_original_review_pack_readonly.py) reads the exact Stage16 selected anomaly ledger, Stage17 P1 episodes, and only the three original native source files needed for those P1 episodes. SHA256 is verified against the prior Stage12 originals. It exports:

- `stage18_39_episode_index.csv`: all P1 event source dates, half-hour counts and provenance.
- `stage18_all_p1_original_flagged_HH.csv`: all P1 anomalous original half-hours, exact original `TA_F`, `VPD_F`, `RH`, two quality codes, MDS and ERA companion values, and derived water RH.
- `stage18_all_p1_original_6hour_context.csv`: native raw time series surrounding each P1 episode (±6 hours), marked context-only when outside the flagged half-hours.
- `stage18_7_priority_review_cards.md`: seven concise native-time user decision tables (US-WCr August 2025, US-Vcm December 2007, January 2007, February 2008, November 2024, October 2025, US-Vcp January 2011), with all other P1 source abnormal HH at the end.
- `stage18_summary.json`: exact hashes and counts and zero repair approvals.

As with earlier stages, this does not invent a UTC offset, infer a source instrument or modify any source/forcing/CIME/Slurm settings.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage18"
  COMMIT="cf6fb9fe7a8c8ea9905757b0086a05c9a1d486ec"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/18_export_p1_original_review_pack_readonly.py"
  STAGE16="$HOME/ameriflux_batch05_stage16/source_pairs_20261025T225516Z_1291407"
  STAGE17="$HOME/ameriflux_batch05_stage17/episode_manifest_20261025T230607Z_1291407"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage18/18_export_p1_original_review_pack_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "e58205016cda48d42d4732261ebc238fd7941ee7"
  echo "STAGE18 SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/original_review_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage16-dir "$STAGE16" \
    --stage17-dir "$STAGE17" --output-dir "$OUT" \
    2>&1 | tee "$BASE/stage18.log"
  echo "STAGE18_REPORTS=$OUT"
)
```

After success, show the actual reviewer decision cards with `cat "$OUT/stage18_7_priority_review_cards.md"` **inside the same shell**, or upload that `.md` and the flagged HH CSV to ChatGPT to conduct an evidence-based KEEP/HOLD/REPLACE review. This script is committed and SHA-verified on GitHub but has **not been executed on IRIDIS6**. All proposals remain `HOLD_NOT_APPROVED`.


## Stage19: P1 original-before-and-after user review tables

The operator completed Stage18: original P1 met from three SHA256-pinned native sources, **39 P1 episodes = 176 flagged original HH, 775 unique HH context rows**, with original Stage18 evidence at `$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929`.

User requested both the **before and after** meteorology and ERA5 data, by problem, so they can decide now. The Stage18 pasted terminal output showed P1-flagged hours but not all 775 surrounding HH values; Stage19 provides exact existing CSV data without fabricating missing rows.

[Stage19 report-only before/during/after source tables](scripts/stage19/19_make_before_during_after_decision_tables_readonly.py) reads only Stage18 reports and writes:
- `stage19_SEVEN_priority_original_before_after.md`, one full copy/paste-ready file combining the seven core review groups with original surrounding meteorology;
- `seven_priority_groups/G01...G07.md`, individual full before/P1/between/after table per top group;
- `all_39_episodes/US-...E....md`, individual exact original episode ±6h source context; neighboring abnormal P1 half-hours separately labeled;
- `stage19_all_episode_before_during_after_long.csv`, machine-readable audit rows for all 39 P1 episodes including source value QC, MDS alternatives, processed ERA counterparts, source RH and water-Magnus RH;
- `stage19_summary.json`.

**Critical data provenance:** the original source columns `TA_F` and `VPD_F` are not necessarily measured *tower* values: QC0=measured, QC1=MDS, QC2=source-supplied processed ERA. `TA_ERA` and `VPD_ERA` are source supplied downscaled ERA/reference counterparts; their exact reanalysis version has not been independently verified as **ERA5/ERA5-Land**. This script does not independently download ERA5/ERA5-Land. No source meteorology, QC, DATM forcing, CIME or Slurm changes.

```bash
(
 set -euo pipefail
 BASE="$HOME/ameriflux_batch05_stage19"
 COMMIT="b5081d1ebc18ab6d4622b1ac6d0ad4379072b92e"
 RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
 SCRIPT="$BASE/19_make_before_during_after_decision_tables_readonly.py"
 STAGE18="$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929"
 mkdir -p "$BASE"
 curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage19/19_make_before_during_after_decision_tables_readonly.py" -o "$SCRIPT"
 test "$(git hash-object "$SCRIPT")" = "47a9fb0e683ff32ba87993725856ab88998fe788"
 echo "SOURCE VERIFIED"
 python3 -B -m py_compile "$SCRIPT"
 python3 -B "$SCRIPT" --self-test
 OUT="$BASE/original_before_after_$(date -u +%Y%m%dT%H%M%SZ)_$$"
 python3 -B "$SCRIPT" --stage18-dir "$STAGE18" --output-dir "$OUT" \
   2>&1 | tee "$BASE/stage19.log"
 echo "HUMAN_REVIEW_FILE=$OUT/stage19_SEVEN_priority_original_before_after.md"
)
```

After success, `cat "$OUT/stage19_SEVEN_priority_original_before_after.md"` to copy into the chat, or transfer and attach the `.md`. **Stage19 has been committed to GitHub and hash checked, but operator has not yet executed it on IRIDIS6.** All 176 flagged original HH remain HOLD, nothing automatically approved.


## Stage20 user-approved RH source reconstruction candidates (2026-10-26; operator run pending)

[User source humidity decisions and exact evidence](docs/STAGE20_USER_HUMIDITY_DECISIONS_2026-10-26.md).
[Stage20 report-only original 117-candidate decision overlay script](scripts/stage20/20_make_investigator_decision_candidate_overlay_readonly.py).

The investigator decided:
- G01 WCr 2025-08-25 13:00 to 2025-08-26 01:30: 26 original low-RH measured HH → use original *processed ERA-pair RH* with tower T unchanged, rederive VPD coherently.
- G03 Vcm 2007-01-16 22:00 to 2007-01-17 14:30: all 34 original native RH values, **including transitions** (10 P1 + 24 surrounding) → rederive VPD coherently from each selected native T and original RH.
- G05 Vcm 2024-11-21–22: 26 P1 source QC0 low-RH records use processed ERA-derived RH with unchanged original tower T and rederived coherent VPD; nearby unapproved non-P1 source RH<5% is untouched.
- G06 Vcm 2025-10-13/14: 23 P1 measured low-RH records use processed ERA-derived RH with unchanged tower T and rederived coherent VPD. Another eight source-native RH≈0.3% appear during QC1/1 periods, but those original selected MDS VPD values already imply physical 66–83% RH, so hold separate source-RH-only field provenance and **do not rewrite good QC1 VPD without additional confirmation**.
- G02 Vcm 2007-12-15/16 original RH is missing all 19 P1 and original processed ERA RH itself becomes negative (as low as -12.21%).
- G04 Vcm 2008-02-06 original RH missing all 38 context HH; 11/12 P1 ERA RH negative.
- G07 Vcp 2011-01-01 original RH missing all three P1; processed ERA RH -6.00% to -6.42%; original tower measured RH resumes at 09:30 68.05% and 11:00 49.83%, not at 07:00–08:00.

At this stage **nothing has been written to forcing, original QC, CIME, or Slurm**. To create a **strictly NEW diagnostic candidate-only CSV/JSON** and examine exact proposed humidity/VPD values before preparing a production forcing update, run on IRIDIS6:

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage20"
  COMMIT="801e16fd5df76d4b88183690766ebf937d1ce050"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/20_make_investigator_decision_candidate_overlay_readonly.py"
  STAGE18="$HOME/ameriflux_batch05_stage18/original_review_20261025T235716Z_1394929"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage20/20_make_investigator_decision_candidate_overlay_readonly.py" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "e5ffc43fef13e79034e160058be478a819f5ad92"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/decision_candidates_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage18-dir "$STAGE18" --output-dir "$OUT" \
    2>&1 | tee "$BASE/stage20.log"
  echo "STAGE20_REPORTS=$OUT"
)
```

Expected **G01 26 + G03 34 + G05 26 + G06 31 = 117 candidate half-hours** (including G06 eight QC1 raw-low-RH entries with separate provenance). G02 19 + G04 12 + G07 3 = **34 separate missing-RH holds**. Two native source comparisons are essential: `RH_ERA` is diagnostic source-downscaled ERA RH, **not newly downloaded ERA5/ERA5-Land RH**; and the VPD must be `es(original TA_F)*(1 - chosen RH/100)`, never unmodified `VPD_ERA` combined with tower T. User has approved this candidate direction, but no source or production forcing changes have yet been run or verified.


## Stage22 user-approved NON-HOLD overlay (2026-10-26)

**Latest status supersedes any earlier Stage20 Stage21 instructions to keep all candidates on hold.** User: “hold我人工审核，其他的按照你的决定修改。” Stage21 was successfully run by operator (source verified) and categorized 57 remaining original P1 HH into A=44, B=11, C=2.

- **Scientific approval for a new reconstructed RH+VPD native-time overlay: 162 HH** = 117 original Stage20 candidate HH + 34 non-2015 US-Vcm QC0 extreme-low source RH records reconstructed using processed source ERA RH with observed tower TA + 11 QC2 records reconstructed using available original source RH and selected TA.
- **46 original P1 HH specifically HOLD for user's manual review** = 34 Stage20 native original RH missing events (G02 19, G04 12, G07 3), 10 A-class 2015-12-06 source extreme-low RH (source ERA T differs strongly and processed ERA RH can be <10%), plus 2 2008-12-27 C-class missing source RH events.
- **3 specific QC0 transition boundary HH not modified:** WCr 2025-08-25 12:30, WCr 2025-08-26 02:00, Vcm 2025-10-14 11:30, until user's explicit per-time replacement decision.
- Original 176 P1 HH = 130 approved P1 + 46 held P1; the 162-overlay row total additionally includes 32 Stage20 non-P1 transition / original source RH QC1 records. No double count.

[Stage22 operator-ready script](scripts/stage22/22_apply_decisions_to_versioned_native_overlay.py) and [decision provenance documentation](docs/STAGE22_APPROVED_NONHOLD_RECONSTRUCTION_2026-10-26.md).

**No IRIDIS6 Stage22 execution yet.** The script creates ONLY NEW output reports `stage22_VERSIONED_APPROVED_RH_VPD_native_overlay.csv` (162), `stage22_46_MANUAL_HOLD_P1_untouched.csv` (46), boundary QC table, manifest, and short operator review. It does NOT alter original source CSV/QC, existing DATM forcing, CLM-FATES cases, Slurm, or previous Stage18/20/21 files. Source `TA_ERA/VPD_ERA` were NOT independently verified as ERA5-Land; these values are processed source ERA and must carry reconstruction provenance.

Run the pinned one-call command in the Stage22 decision documentation; after checking exact results, manually review the 46 HOLD and source native edge discontinuities. Model-ready forcing creation remains blocked until full Batch05 1,750-HH QC/P2/P3 review, Post-v5 technical checks and remaining source-specific holds are resolved.


## Stage24 four explicitly approved edge-half-hour RH/VPD reconstructions (2026-10-26)

**Most recent investigator science decision** (supersedes earlier Stage23 manual EDGE HOLD *for precisely four named timestamps*): replace processed-source ERA-derived RH while **retaining original measured tower `TA_F`**, reconstruct physically coherent VPD; **do not expand interval**.

- E01 US-Vcm 2014-08-19 **08:30**, ERA-derived RH 56.194173% (previous source RH 17.18377%).
- E02 US-Vcm 2025-10-14 **11:30**, ERA-derived RH 75.805596% (previous source RH 37.98483%). Afterward 12:00–13:30 source RH≈99.46% is **unapproved plateau review**.
- E03 US-WCr 2025-08-25 **12:30**, ERA-derived RH 65.093868% (previous source RH 33.68535%). Preceding original 09:30–12:00 source RH=100% is **unapproved plateau review**.
- E04 US-WCr 2025-08-26 **02:00**, ERA-derived RH 91.924097% (previous source RH 32.35776%).

**Outputs after operator runs Stage24:** Stage22 existing 162 changed rows + exactly 4 approved edges = **166 versioned RH/VPD overlay half hours**; 46 original P1 human HOLD entries **byte-identical and unchanged**; original 176 P1=130 already approved + 46 held; 10 unapproved near-saturation plateau HH identified separately. All original FLUXMET, native source QC, DATM, CIME/Slurm remain unmodified; neither processed source `TA_ERA/VPD_ERA` nor derived `ERA_RH` has been independently verified as ERA5-Land.

[Stage24 pinned source script](scripts/stage24/24_merge_four_approved_edge_RH_to_versioned_overlay.py) and [Stage24 exact decisions, operation and provenance](docs/STAGE24_EXACT_FOUR_EDGE_APPROVALS_2026-10-26.md). **Script committed to GitHub; operator execution still pending.** Do not advertise a finished forcing: 46 P1 RH HOLD and P2/P3 source-science QC remain unresolved.


## Stage25 exact original 1750 anomaly crosswalk to Stage24 executed 166 approved rows

**Verified operator Stage24 SUCCESS 2026-10-26:** exactly 166 versioned approved RH/VPD overlay HH and 46 manual P1 HOLD with unchanged original FLUXMET/DATM/CIME/Slurm. Three previously identified large edge jumps fixed, **one remains**: WCr 2025-08-25 **12:00→12:30** jumps +6.032576601 hPa because source RH=100% at 12:00; do **not** auto-replace the earlier RH 100% plateau. WCr 2025-08-25 09:30–12:00 (six HH) and Vcm 2025-10-14 12:00–13:30 (four HH) source near-saturation platforms remain **unapproved science-review only**.

[Stage25 exact 1750/522 original source-to-overlay crosswalk](scripts/stage25/25_crosswalk_1750_source_anomalies_with_166_approved_readonly.py) and [Stage24 operator completion, Stage25 pinned execution instructions and science cautions](docs/STAGE25_ORIGINAL_1750_EXACT_CROSSWALK_AND_P2P3_QC_2026-10-26.md).

**Stage25 script already published to GitHub, operator still needs to run it.** Do not assume all 1574 original P2/P3 abnormal HH remain unapproved: Stage24's 166 approved overlay half-hours include 36 outside the original P1 tier and an **exact site+native-HH join** is needed to establish which coincide with original P2/P3 flags versus unflagged transition/edge rows. Stage25 reports per-original-event approved/HOLD/unapproved counts and per-episode/workstream evidence strategies. NO new automatic P2/P3 changes, no independent reanalysis downloaded, no final forcing or model jobs.


## Stage26 P2/P3 per-native-HH science candidate feasibility (2026-10-26)

Stage25 **successfully executed by IRIDIS6 operator** (not merely published):
- Original 1,750 abnormal native half-hours / 522 events exactly mapped.
- Current Stage24 **166 approved versioned overlay HH** consist of original anomaly P1 **130** and **36 out-of-original-screen transition/edge HH**.
- Original P1=176 consists of **130 candidate-approved** and **46 unchanged manual HOLD**.
- All **1,574 P2/P3 native flagged HH are still unapproved**; none overlaps the 166 approved overlay.
- Site breakdown remaining: US-Vcp 626, US-Wjs 401, US-Vcm 362, US-Var 62, US-WCr 62, US-UMB 23, US-Wkg 22, US-UMd 15, US-Whs 1, US-UiD 0.
- Stage25 first-match evidence groups **924 unresolved provenance**, **607 source processed ERA pair physically valid**, **38 MDS pair physically valid**, **5 original RH present**. These four groups are strictly mutually exclusive as implemented in Stage25, but they do *not* exhaust possible overlap of physically feasible source alternatives.

[Stage26 1,574 native-hour MDS/ERA/ERA-e/native-RH research-only candidates](scripts/stage26/26_reconstruct_p2p3_physics_candidates_research_only.py) and [operator command / scientific decision guide](docs/STAGE26_ALL1574_P2P3_SCIENCE_OPTIONS_2026-10-26.md).

Stage26 **pending operator execution**. It generates four mathematically distinct candidate hypotheses, records original source QC and source-vs-tower TA discrepancies, and partitions all 1,574 P2/P3 HH into *scientific evidence* subgroups. **No P2/P3 changes are approved by this step**; original FLUXMET, Stage24 approved 166, P1 HOLD 46, DATM and Slurm remain unmodified. This is intended to reduce human review to data-source/physics method decisions instead of 1,574 independent timestamps. Independent T/dewpoint meteorology is needed for unsupportable source alternatives and scientific corroboration. No actual full forcing or Post-v5 yet.


## Stage27 operator P2/P3 RH-source comparison, source risk and 483 episode priority (2026-10-26)

The Stage26 source audit has **executed successfully** on IRIDIS6. **All 1,574 original P2/P3 half-hours remain unapproved**, although all 1,574 have a mathematically feasible *processed source ERA-pair RH* candidate; options exist for 551 MDS pairs, 1,459 source ERA actual-vapor-pressure shadows, and 5 native source RH. These candidate counts overlap; 546 HH have both MDS and processed ERA RH alternatives. Original selected TA differs from source processed ERA TA by >5°C in **372 HH**, so unconditional source ERA pairing is scientifically unjustified. No independent ERA5/ERA5-Land downloaded.

[Stage27 native-HH MDS-vs-source-ERA RH disagreement, processed ERA assumption and 483 original P2/P3 episode risk screener](scripts/stage27/27_compare_p2p3_mds_era_and_temperature_risk_readonly.py); [Stage26 actual operator output and pinned Stage27 executable instructions](docs/STAGE27_P2P3_SOURCE_AGREEMENT_DISAGREEMENT_AND_RISK_2026-10-26.md). **Stage27 published; operator run pending.** It partitions by native RH present, MDS–ERA RH concordance, disagreement, ERA-only cases; flags temperature discrepancy and large VPD sensitivity, ranks original P2/P3 episodes and produces zero new forcing approvals.

The **166 Stage24 approved overlay** remains separate from 46 manual P1 HOLD and 10 unapproved saturated RH plateau HH. No original FLUXMET, production DATM, source QC or Slurm changes.


## Stage28 independent reference meteorology pilot and source UTC-offset gates (2026-10-26)

**Stage27 has been EXECUTED by operator (read-only):** all 1,574 original P2/P3 native HH remain SCIENCE-UNAPPROVED, across 483 original episodes. Stage27 source MDS and processed-source ERA humidity comparator outcomes were 23 pairs agreeing within 5 RH percentage points, 115 disagreeing 5–20 pp, **408 disagreeing >20 pp** (339 US-Vcp); **1,023 only processed-source ERA RH**, 5 original source RH available. Across all P2/P3, original selected-T minus processed-source ERA-T >5°C 372 HH, source ERA RH-conserving versus its actual vapor-pressure-conserving VPD difference >2 hPa 66 HH, and resulting candidate versus source original VPD >5 hPa 715 HH. Those flags overlap, and do not make any candidate scientifically approved.

Public AmeriFlux tower locations verified against official AmeriFlux pages: **US-Vcp (35.8641, −106.5965, 2501 m)**, **US-Wjs (34.4258, −105.8617, 1931 m)** and **US-Vcm (35.8885, −106.5322, 3043 m)**. The FLUXNET timestamp convention is local standard time without DST; release- and site-specific **BADM UTC_OFFSET has not yet been verified**.

[Stage28 high-risk native-hour pilot, official coordinates and source-ZIP/BADM UTC offset evidence preflight](scripts/stage28/28_independent_reference_metadata_and_priority_windows_readonly.py) and [operator instructions and time-metadata science cautions](docs/STAGE28_EXTERNAL_MET_REFERENCE_PILOT_CLOCK_GATE_2026-10-26.md). Code is on GitHub; operator Stage28 run is **PENDING**. Stage28 generates top 20 risk episodes (original timestamp windows), five P1 HOLD event reference windows and two RH platform windows plus original-site ZIP metadata evidence. It neither guesses timezone nor downloads ERA5-Land, modifies the original FLUXMET, existing approved 166, human HOLD 46, forcing or Slurm. Only after BADM UTC_OFFSET is verified can an independently downloaded ERA5-Land T/dewpoint pilot be joined correctly to the original tower clock for scientific decision-making.

This stage is designed to **break the audit-only loop** and prepare verifiable new observational/reanalysis evidence before deciding P2/P3 repair. Stage24's single residual WCr saturation-edge jump and the ten unapproved RH saturation-platform HH remain separately held for review.


## Stage29 original BIF grouped UTC_OFFSET evidence and conditional external meteorology request timestamps

**Stage28 successfully executed on IRIDIS6** (read-only). All three New Mexico priority-site original release ZIPs contain BIF `UTC_OFFSET=-7` evidence: US-Vcp GROUP_ID 4791/4799 (4799 DATE_START=200701010000), US-Wjs GROUP_ID 1493 (DATE_START=200705041330), US-Vcm GROUP_ID 1266/1274 (1274 DATE_START=200701010000). The previous Stage28 code's harmless `SyntaxWarning` about escaped Markdown backticks is fixed in GitHub; Stage28 rerun is not needed. The first Stage28 source review pilot comprises **20 high-risk P2/P3 episodes / 264 original anomalous HH**, 5 manual P1 HOLD windows containing **46 HH**, 2 unapproved saturated RH platforms; total **27 native event windows**. Source FLUXMET/DATM/Stage24 approved 166 rows/HOLD 46 unchanged.

[Stage29 verified BIF GROUP_ID UTC_OFFSET/date-range source scanner and exact 27 native-to-UTC conditional conversion](scripts/stage29/29_verify_bif_utc_offset_groups_and_convert_pilot_windows.py) and [Stage28 operator evidence, pinned Stage29 command and original BIF/ERA5-Land science prerequisites](docs/STAGE29_ORIGINAL_BIF_GROUP_TIMEZONE_COVERAGE_2026-10-26.md). Stage29 parses all native `UTC_OFFSET`, `UTC_OFFSET_DATE_START`, `UTC_OFFSET_DATE_END` under each GROUP_ID, checking full effective-dated intervals; it includes **US-WCr in Wisconsin** as a *separate source ZIP and timezone*, since WCr's saturation plateau cannot inherit the New Mexico -7 shift. No UTC conversion is authorized for external data requests if original grouped date ranges are ambiguous.

**Stage29 is on GitHub but operator execution pending**. Even after group verification, it does not make an ERA5-Land network request; the next step is a time-verified independent external 2 m T/dewpoint pilot, preserving provenance, dataset timezone, altitude discrepancies and original QC. No automatic P2/P3 repairs or model jobs.


## Stage30 Stage29-confirmed BIF offsets and research-only ERA5-Land pilot data requests

**Stage29 executed successfully on IRIDIS6.** All four original release BIF ZIPs parsed without conflict: original source UTC_OFFSET -7 h for **US-Vcp, US-Wjs, US-Vcm**, and -6 h for **US-WCr**. Actual SOURCE GROUP_ID: Vcp 4791 (undated), 4799 (start 2007-01-01 00:00); Wjs 1493 (start 2007-05-04 13:30); Vcm 1266 (undated), 1274 (start 2007-01-01 00:00); WCr 3522 (undated). All six groups lack END_DATE. Original 27 Stage28 pilot event windows had source coverage 26 `OPEN_ENDED_START_DATED_REVIEW`, 1 `ONLY_UNDATED_OR_END_ONLY_GROUP_REVIEW`; **no CLOSED_DATED complete source groups**. Candidate native LST to UTC conversion is +7h for 3 NM sites, +6h for Wisconsin WCr, without DST. The missing BIF end dates remain explicitly unverified; no alternate timezone inferred.

[Stage30 original source-preserving CDS ERA5-Land point time-series API request planner with explicit optional one-file research fetch](scripts/stage30/30_build_and_optionally_fetch_ERA5Land_reference_pilot.py) and [Stage29 operator original source evidence + pinned Stage30 commands](docs/STAGE30_ERA5LAND_RESEARCH_REFERENCE_PILOT_2026-10-26.md). The Stage30 script builds site+UTC-month T/dewpoint request manifests for the 27 original pilot event windows (20 original high-risk P2/P3 episodes, 5 P1 HOLD event ranges, 2 unapproved RH-saturation platforms), SHA-verifies Stage28/29 source reports, and outputs both per-event UTC candidates and CDS request JSON. Default **no network and no download**. Optional `--fetch --acknowledge-provisional-bif-offsets --max-fetch 1` requires operator-supplied CDS credentials and licence consent; it retrieves only one research reference payload to a new separate output path, not forcing.

**Stage30 script is committed but the IRIDIS6 operator has not run it.** Stage24 approved 166 versioned RH/VPD half-hours remain untouched; 46 P1 manual HOLD and original P2/P3 1574 unapproved. No full DATM forcing production, no model job submissions.


## Stage30 operator PASS — 11 research-only CDS plans, corrected time-series API dates

**Stage30 EXECUTED successfully on IRIDIS6 2026-10-26** (not a CDS download): 27 original native pilot windows grouped into **11 site/month reference acquisition requests**, `DOWNLOADS 0`. Sites selected by top-20 high-risk original episodes and manual holds/plateaus: **US-Vcm six**, **US-Vcp four**, **US-WCr one**, **US-Wjs zero** (Wjs 401 original P2/P3 anomalies are not represented by these particular 20 top-ranked episodes; a later balanced pilot must add Wjs). Prior Stage24 overlay 166, P1 manual HOLD 46, original P2/P3 unapproved 1574, native FLUXMET/DATM unchanged.

**CRITICAL POST-RUN CDS API request bug fix:** original Stage30 planner emitted `date` as a two-element list. ERA5-Land time-series API expects an ISO slash-separated date range string (`YYYY-MM-DD/YYYY-MM-DD`), not the standard ERA5-Land `year/month/day/time` request form. Patched Stage30 [script](scripts/stage30/30_build_and_optionally_fetch_ERA5Land_reference_pilot.py) commit `14d976fb4fb6e8d0514d677b0aa9ee5055a48a6b`, Git blob `3b5446297834ee4a4d587e668038d5eb0143a2c1`. **Do not use the old script for `--fetch`**. This patch changes only API request serialization and actual-request self-test, not original site times or scientific decisions.

[Stage30 operator PASS, limitations, corrected script and optional ONE research-only downloaded reference command](docs/STAGE30_ERA5LAND_RESEARCH_REFERENCE_PILOT_2026-10-26.md). First priority `ERA5L_US_Vcm_200712` (four-day H01 source RH missing P1 reference window), with user-configured CDS license/API. Original grouped BIF time zones have open-ended/undated effective-date metadata (Vcm/Vcp/Wjs UTC−7, WCr UTC−6): **UTC date candidates, not complete independently validated clock metadata**. ERA5-Land remains model reanalysis rather than an independent in-situ tower sensor. External data must be unit/time/grid-validated before any RH/VPD science approval.


## Stage31 real ERA5-Land first payload validated against H01 native HOLD (script ready, operator pending)

**Real first CDS request SUCCESS 2026-10-26 ~11:46 UTC** (user-provided log): `reanalysis-era5-land-timeseries` source **US-Vcm Dec 14–17, 2007**, original download ID `ERA5L_US_Vcm_200712`; source `ERA5L_US_Vcm_200712.cds_download` **20,935 bytes**, verified user-reported SHA256 `abda0a706aef79dc0eb7a8b50db1b66ed427c8a756b81965d9bb3dba2e315646`. Stage30 CSV/JSON plans still 11 site/month requests, 27 original study windows; **one actually fetched source**. This is NOT an approved humidity replacement. The BIF offset remains -7 LST (DATE_END missing).

[Stage31 exact first downloaded CDS file ZIP/NetCDF inspection plus 19 half-hour US-Vcm H01 P1 original RH manual-HOLD comparison](scripts/stage31/31_validate_first_ERA5Land_CDS_payload_and_Vcm_H01_readonly.py) and [operator-pinned command and provenance](docs/STAGE31_FIRST_CDS_PAYLOAD_H01_READONLY_REFERENCE_2026-10-26.md). Stage31 verifies actual downloaded file bytes and internal hourly UTC T/Td with xarray, compares to SHA-pinned original Stage18 tower source observations and Stage24's 46 unchanged manual P1 HOLD events, computes gridded ERA5-Land RH and research-only alternate tower-relative VPD hypotheses (fixed RH vs fixed actual water vapour pressure) with source-clock candidates. The first external download may be a **ZIP containing separate NetCDF parameter groups** (per official CDS ERA5-Land time-series PUG); the Stage31 script detects the format before opening.

**Stage31 is published, but operator has not run it yet.** Original H01 19 records remain human HOLD; all Stage24 approved 166 unchanged, 46 total P1 HOLD and 1574 P2/P3 unapproved. No model DATM/Slurm/science automatic approvals.


## Stage32 real H01 winter external humidity phase and forcing-boundary science screening

**Stage31 verified operator SUCCESS 2026-10-26**: real SHA-verified CDS ERA5-Land 2007-12-14..17 UTC downloaded ZIP (one internal NetCDF, 96 hourly records). Exactly **19** original H01 US-Vcm native LST (2007-12-15 21:00 to 2007-12-16 06:00) RH-missing half-hours paired with external 2m T and dewpoint; ERA5-Land **RH_w=67.680542–78.046519%**, bundled original processed source ERA-derived RH **−12.214486 to −0.708978%**; ERA5-Land 2m T **2.4203–6.002364°C colder** than original tower TA. Original source and model/DATM remain unchanged; grid RH does not prove actual tower RH. The original BIF -7 offset DATE_END absent; temporal and elevation sensitivity remain.

[Stage32 source-SHA-verified H01 ice/water phase, dewpoint water-vapour pressure reconstruction and pre/post boundary trial audit](scripts/stage32/32_Vcm_H01_19HH_ice_water_phase_and_boundary_sensitivity_readonly.py) and [operator instructions and technical science distinction](docs/STAGE32_VCM_H01_ICE_WATER_PHASE_BOUNDARY_REVIEW_2026-10-26.md).

**Critical physics:** ECMWF ERA5/ERA5-Land *dewpoint* is defined relative to water: derive actual e using `es_water(Td)`, then compute `RH_water=100e/es_water(T)` or `RH_ice=100e/es_ice(T)`. Do not use ice saturation at dewpoint as if it were an observed frost point. Stage32 keeps four distinct *unapproved* tower-VPD choices (grid RH or grid e retained, reference saturation over water or over ice); computes 19-row phase comparison, ±30min reference RH variability, two existing-source-boundary × four candidate checks. No scientific approval or automatic clipping of possible ice supersaturation. **Stage32 published, operator run PENDING.** Stage24 approved 166, original P1 HOLD 46 (H01 19), P2/P3 unapproved 1574, 10 prior RH plateau suspect HH remain preserved. Source FLUXMET/DATM/CIME/Slurm untouched.


## Stage33 original H01 humidity neighboring source gate and 10 extra independent reference pilots

**Stage32 EXECUTED successfully by operator (26 October 2026):** original Vcm H01 19 manually held RH-native HH are supported by actual independently retrieved ERA5-Land temperature/dewpoint reference; derived grid RH over water 67.68–78.05%, over ice 78.80–92.83% (water/ice difference up to 14.79 percentage points). Grid temperature 2.42–6.00°C colder than measured tower air temperature. Four alternate tower-temperature VPD sensitivities cause **no 30-min boundary jump >4 hPa** against immediately neighboring unchanged source original data, but the unchanged neighbors have original VPD **2.581 hPa (20:30 LST 15 Dec 2007)** and **2.588 hPa (06:30 LST 16 Dec 2007)**, suspicious near water saturation vapor pressure at ~−12°C. Source QC/original implied RH must be checked rather than treating artificial smoothness as a repair validation. No science approval was made; 46 P1 HOLD preserved.

[Stage33 exact original neighboring RH and QC audit, plus 10 optional real ERA5-Land gridded reference acquisitions](scripts/stage33/33_H01_neighbor_QC_and_prioritized_independent_ERA5Land_batch.py) and [pinned IRIDIS6 command and H01 human-review decision gate](docs/STAGE33_H01_NEIGHBORS_AND_OTHER_TEN_EXTERNAL_REFERENCES_2026-10-26.md).

Stage33 reuses the Stage30 corrected point time-series CDS request specs and sequentially fetches with explicit opt-in six original P1-HOLD / RH-platform targets (Vcm H02/H03/H04, Vcp H05, Vcm 2025 saturation, WCr 2025 saturation), three Vcp original high-risk P2P3 conflict months (2008 Apr–Jun), **and the first previously omitted US-Wjs high-risk Stage27 P2P3 episode**. Default is PLAN ONLY; `--fetch --acknowledge-provisional-bif-offsets --max-fetch 10` downloads all 10 to a **NEW research reference folder**, preserving filenames and SHA256. It does not overwrite the successful original Stage30 first H01 CDS file or any source/forcing/data assimilation. All original BIF UTC_OFFSET_DATE_END still missing, so scientific clock conversion remains provisional. **Stage33 published to GitHub; operator execution pending.**


## Stage34 10 actual ERA5-Land gridded reference files vs remaining QC source

**Stage33 successfully executed and downloaded all 10 CDS ERA5-Land research references** on 26 Oct 2026, including 4 remaining P1 HOLD original events (H02/H03/H04/H05), two RH saturation platforms (Vcm Oct 2025, WCr Aug 2025), three Vcp 2008 high-risk months and one first Wjs original P2/P3 high-risk episode. Together with Stage30 first H01 file, this is **11 externally downloaded gridded references**, not 11 scientifically approved RH/VPD replacements. All files have source size and SHA256 reported by the operator, retained in [Stage34 source-based documentation](docs/STAGE34_ACTUAL_TEN_ERA5LAND_FILES_HOLD_P2P3_EVIDENCE_2026-10-26.md).

**Stage33 original immediate H01 neighbor QC2 evidence:** 2007-12-15 20:30 US-Vcm tower/source TA=-11.136°C VPD=2.581 hPa implies water-RH **1.513015%**; 2007-12-16 06:30 TA=-10.784°C VPD=2.588 hPa implies water-RH **3.973442%**. Both are QC2/QC2, **not measured in situ QC0**. Stage33's `SUSPECT False` was only because it used RH<1% as a narrow flag; these records remain scientifically questionable and UNMODIFIED, adjacent to original 19 H01 human HOLD entries. No approval for expanding H01 to neighbors or choosing source ERA replacement.

[Stage34 actual ten-file SHA/ZIP/NetCDF/UTC Kelvin meteorology validator and original P1/P2P3/RH-platform source join](scripts/stage34/34_assess_10_actual_CDS_references_against_all_P1_P2P3_and_platforms_readonly.py). This reuses the **proven Stage31 parser pinned by Git blob SHA**, rather than implementing another parsing stack. It compares gridded T/dewpoint/RH to original tower T/VPD/QC, source MDS and processed source ERA companion, covers all **27 remaining H02–H05 original P1 HOLD HH** and all **10 original unapproved RH platform HH**, as well as the source P2/P3 HH coinciding with the 4-site external reference windows. Every downloaded source file is required to match exact operator SHA, original UTC date interval, variable names/units and site grid. No scientific automatic source approval.

**Stage34 GitHub code and docs committed, operator execution pending**. No change to existing 166 approved Stage24 overlay, 46 P1 HOLD (including 19 H01), remaining 1574 original unapproved P2/P3, source FLUXMET or DATM/Slurm. Original BIF UTC_OFFSET_DATE_END absent and reference remains gridded reanalysis, not in-situ station observation.


## Stage35 externally reference-matched P1/P2P3/plateau science decisions and VPD trials

**Stage34 executed successfully on IRIDIS6**: 10/10 actual new CDS ERA5-Land ZIP/NetCDF downloads fully SHA/UTC/2m T/dewpoint/grid verified against previously untouched native tower QC. Matched exactly **429 unique original unapproved HH** = **27 non-H01 manual P1 HOLD** + **10 unapproved original RH saturation-platform HH** + **392 original P2/P3**. H01 original 19 manually held native HH were previously assessed using the initial separately downloaded first CDS reference. Existing Stage24 **166 approved native source RH/VPD overlay** unchanged. 46 original P1 HOLD and 1574 original P2/P3 still unapproved, no DATM production forcing or Slurm jobs. Stage34 summary path: `/home/ly3n24/ameriflux_batch05_stage34/reference_validation_20261026T131903Z_715715`.

Stage34 Vcp P2/P3 original 382 matched native HH: **323** have RH reference closer to processed source ERA than original MDS (margin >5 RH pp), **10** closer to MDS, remainder **49** equivocal; **280** differ from source MDS RH by >20pp, only **6** differ from source processed ERA by >20pp. Wjs first 9 HH are all closer to processed source ERA than MDS, but these are only 9/401 total Wjs original P2/P3. Source processed ERA and newly downloaded ERA5-Land are both reanalysis-related: **concordance is not independent observed truth**. Vcm/Vcp original P1 manual HOLDs 26/27 differ from source ERA RH by >20pp, while RH platforms show meaningful disagreement for some original source HH. These results need event-based science decisions, not blind replacement.

[Stage35 SHA-pinned original 429 matched HH ➜ physical original-tower-temperature VPD method trials, 6 source-science review lanes and original P2/P3 episode-level decision matrices](scripts/stage35/35_external_reference_to_tower_VPD_trial_and_episode_decision_matrix_readonly.py) and [Stage34 operator real numerical results, science limitations and Stage35 IRIDIS6 command](docs/STAGE35_REAL_ERA5LAND_EVENT_METHOD_TRIALS_2026-10-26.md). The code derives two tower water-saturation VPD trials (source-ERA RH transported vs fresh-grid ERA5-Land RH transported) alongside separately preserving external-grid actual vapour pressure as a third RESEARCH-only hypothesis. It explicitly flags fresh tower-grid T>5°C, source RH disagreement, native source VPD reconstruction shift, original source-HOLD and saturation platforms, and separately records **two H01 pre/post source QC2 neighbors** with implied RH water 1.513% and 3.973% (not automatically edited). `P2P3_REANALYSIS_ERA_CONCORDANT_LOW_T_DIFF` is a **screening lane**, not a scientific forcing approval.

**Stage35 code and docs committed to GitHub, operator execution pending.** No source originals, approved overlays, user manual holds, or forcing CIME/Slurm edits.


## Stage36 source-ZIP-backed isolated 251 RH/VPD science trials and original boundaries

**Stage35 operator PASS 2026-10-26**: all 429 actual independently downloaded ERA5-Land referenced native anomalies have been checked against source processed ERA RH/MDS and source VPD at original tower T. Exactly **251 original P2/P3** pass a low-difference screening lane (processed source ERA vs fresh ERA5-Land RH within 10 pp; grid–tower T ≤5°C, gridded RH-to-tower VPD vs original VPD ≤5 hPa), **77** have larger T/VPD changes, **11** lean toward source MDS and **53** remain conflicting/ambiguous. Four additional event-based populations remain: original **27 non-H01 P1 HOLD**, 19 H01 P1 HOLD, **10 unapproved saturation-platform records**, and previously approved 166 versioned Stage24 source RH/VPD. None of the 251 are scientifically approved, and a second reanalysis agreeing with processed ERA does **not** constitute an independent tower observation.

[Stage36 isolated 251-row ORIGINAL-source-ZIP-authenticated RH-to-tower-VPD research trial and exact ±30min original FLUXMET source QC boundary audit](scripts/stage36/36_build_251_isolated_ERA_RH_trial_and_check_original_FLUXMET_boundaries.py); [pinned source hashes, procedure and one-call IRIDIS6 instructions](docs/STAGE36_251_SOURCE_ZIP_BOUNDARY_TRIAL_2026-10-26.md). Reads unchanged native source ZIP and QC directly, checks original Stage27 source/episode time provenance, compares actual original neighbor VPD and existing already user-approved overlay values where present, tags neighbor QC0, QC2, source-implied RH<10%, unapproved P1/P2/P3 platforms and partial episodes. Writes a **separate research-only trial CSV, not a model-ready forcing overlay**, plus a 502 transition review matrix and episode-level priority summary. This is the first trial-specific original source boundary audit, designed to prevent spurious sharp joins after apparently favorable gridded meteorology.

**Stage36 GitHub committed; actual IRIDIS6 run pending.** Approved 166 source overlay, 46 P1 HOLD, 1574 original P2/P3 unapproved, 10 RH plateau source records, original ZIP/FLUXMET/DATM/CIME/Slurm all unchanged. Original BIF UTC_OFFSET_DATE_END missing, so reanalysis-to-native alignment is provisional.


## Stage37 before/after 251-trial boundary cause: distinguish pre-existing from new 2/4 hPa jumps

**Stage36 actually executed successfully on IRIDIS6 (2026-10-26)**: 251 original native P2/P3 HH, all at **US-Vcp**, grouped into **65 original source events**; 0 QC0 original VPD records in this candidate group. All 65 source events require original-boundary or unapproved-neighbor review. Stage36 reported **94 hypothetically repaired external VPD transitions exceeding 2 hPa and 21 exceeding 4 hPa**, based on *original untouched native source ZIP and ±30-minute source VPD/QC comparison*. Those are AFTER-trial absolute jumps and **do not prove a repaired candidate created them**. Original approved Stage24 166, human P1 HOLD 46, P2/P3 unapproved 1574, original DATM and Slurm remain unchanged.

[Stage37 source-based original-vs-hypothetical VPD boundary change, 65 event prioritization and maximal contiguous candidate segments](scripts/stage37/37_before_after_native_boundary_causality_and_contiguous_segments_readonly.py) and [pinned GitHub command, Stage36 operator evidence and science-gate interpretation](docs/STAGE37_ORIGINAL_VS_TRIAL_BOUNDARY_CAUSALITY_2026-10-26.md). Stage37 reads Stage36 original 251/502/65 evidence and Stage35 429 original source-matched rows, verifies all SHA and original source clock/event identity, then computes original absolute boundary jump, hypothetical after-repair jump, *newly crossing* >2 and >4 hPa thresholds and >0.5 hPa improvement/worsening relative to the **same adjacent original or already-approved versioned VPD**. Keeps QC2/unapproved P2P3 native neighbors separate; never treats source RH <10%, absent adjacent VPD or a cross-event trial boundary as a trusted or zero-valued observation. Segments within source episodes are not automatically extended to neighboring native times.

**Stage36 nonfatal Python SyntaxWarning** (`\` backtick` escape in Markdown text) was removed from GitHub Stage36 script without affecting Stage36 science/results; re-executing Stage36 is unnecessary. **Stage37 committed on GitHub; operator runtime validation pending.** No candidate is authorized as model-ready forcing.


## Stage38 expedited small-site P2P3 source closeout and full US-Vcp source episode reconstruction

**Stage37 actually executed successfully on IRIDIS6 (26 October 2026).** 251 sparse source ERA RH/VPD trial half-hours all US-Vcp, over 65 original P2/P3 episodes and 81 maximal source-native 30-minute segments. Original external VPD boundary jumps >2 hPa **25**, post-trial **94**; original >4 hPa **1**, post-trial **21**, including **84 newly crossed >2 hPa** and **21 newly crossed >4 hPa**; original source-neighbor QC2/nonmeasured 162/162, other unapproved P2/P3 46, implied neighbor RH<10% or unphysical 135. **Do not apply Stage36 251 sparse trial directly as forcing.** The cause is fragment boundaries or unreliable source-neighbor VPD, not automatically that the source ERA humidity is wrong.

The actual Stage27 ten Batch05 site IDs include **US-Wkg**, omitted in an earlier chat summary; do not reuse unverified 1/10 pass counts. [Stage38 raw-original-ZIP-authenticated expedited science study](scripts/stage38/38_fast_small_site_closeout_and_Vcp_full_episode_method_trials_readonly.py) + [operator-pinned instructions](docs/STAGE38_FAST_SMALL_SITE_AND_FULL_VCP_EPISODE_SCIENCE_TRIALS_2026-10-26.md) use the **actual 1,574 source P2/P3 native rows and ten-site source summary** to print per-site remaining counts and source science gates.

Stage38 fast two tracks: (A) seven smaller sites: US-UiD, US-UMB, US-UMd, US-Var, US-WCr, US-Whs, US-Wkg; reads original FLUXNET v1.3 r1 package (source hash logged), confirms original T/VPD/QC with Stage27 and compares **full original contiguous episode** hypothetical processed-source ERA RH and source MDS RH at original tower T, checking original QC0 protection and 2/4 hPa original vs trial boundary jumps. (B) US-Vcp: reconstruct ALL original half-hours for the 65 Stage37 flagged episodes, not just sparse 251; compares full source ERA, MDS and external ERA5-Land methods **only where data span entire original episode**, checks no source-QC0 or unphysical VPD, no new >2/4 hPa internal or external discontinuity; no source changes. These are **research-only numerical decision gates**, not science approval.

**Stage38 GitHub script and docs published; actual user-run pending.** Source originals, Stage24 approved166, original 46 P1 manually HOLD and all 1574 unapproved P2/P3, 10 saturation platform HH, DATM, CIME and Slurm unchanged. No site full-forcing scientific pass is inferred from zero remaining P2/P3 records.


## Stage39 exact 16 numerically favourable event×method trials, source-protected research pilot

**Stage38 actually executed successfully (26 Oct 2026)**: genuine 10-site original Batch05 P2/P3 science audit **1574 half-hours / 483 episodes**. Main result: **669 method×episode trials** (224 missing source-RH, 114 unapproved/nonmeasured neighbors, 125 candidate-created >2hPa jumps, 190 candidate-created >4hPa jumps, **16 numerically lower-risk method×episode tests**). Some methods may belong to the same original episode; 16 is not a source-native HH or distinct-event count. The site cohort includes **US-Wkg 22**, **US-UMB 23**, **US-Whs 1**, **US-UiD 0 P2/P3**, and high-priority Vcp 626, Vcm 362, Wjs 401. **0/10 full forcing admissions confirmed**. Original US-UMB FLUXMET_HH not found within 13 ZIP/CSV candidate sources; it remains an original source-acquisition HOLD, not a science pass. Stage38 native T/VPD/QC verification passed for US-UMd/Var/WCr/Whs/Wkg/Vcp. Model-ready forcing unchanged.

[Stage39 prioritize EXACT original 16 event×method options and check source/native QC, original Stage24 approval exclusions and RH/VPD water physical constraints](scripts/stage39/39_fast_16_event_shortlist_safe_trial_and_US_UMB_source_inventory.py). [Pinned three-line IRIDIS6 launcher](scripts/stage39/run_stage39_iridis6.sh) and [technical science/operation handoff](docs/STAGE39_FAST_EXACT16_MANUAL_REVIEW_AND_UNAPPROVED_REPAIR_PREVIEW_2026-10-26.md). Stage39 creates a **separate unapproved research-only source-native CSV** only for original episodes having one numerically lower-risk method, and a detailed event-level investigator decision shortlist with method ambiguity. It also inventories real US-UMB source ZIP and extracted CSV names and central archive members (plus SHA), to diagnose source availability without guessing or downloading an unverified source. No original source, existing approved166, manual P1 HOLD46, suspect RH plateaus10, DATM/CIME or Slurm changes; all original 1574 P2/P3 remain science-unapproved.

**Stage39 code and docs committed; actual IRIDIS6 operator run pending.**


## Stage40 source original RH physics for 16 Stage39 numerically favorable methods

**Stage39 actually executed** with exact original 669 Stage38 method×episode cases, 16 numerically screened methods over 15 source episodes, 14 unique-method events totaling 20 unapproved source-native research trial HH; one original US-Var 2015-08-20 event `E0017` has two methods: source MDS leaves original VPD unchanged vs source ERA changes VPD by 12.431942 hPa. Other apparently smooth original events have as much as an 18.229752 hPa VPD change. **Neither source ERA + ERA5-Land grid consistency nor absence of a NEW 2/4hPa VPD discontinuity constitutes a scientifically verified tower humidity replacement**. Original Stage27 P2/P3 1574 remains unapproved, 46 P1 manually HOLD, 10 humidity saturation platforms unapproved, Stage24 166 approved original source overlay unchanged. No site complete forcing pass confirmed.

[Stage40 original native source T/VPD implied RH physical sanity, ERA vs MDS RH, numerical candidate magnitude and real US-UMB inventory](scripts/stage40/40_original_humidity_physics_and_real_manual_decision_priorities.py) and [one-click Stage40 IRIDIS6 operator launcher](scripts/stage40/run_stage40_iridis6.sh). See [operator-executed Stage39 evidence and exact immutable Stage40 code/launcher SHA-pinned command](docs/STAGE40_EXACT16_SOURCE_RH_PHYSICS_AND_SCIENCE_REVIEW_2026-10-26.md). Stage40 flags original RH physically impossible (<0%, >100%) or extremely low (<5%/<10%), maximum per-event VPD change >5/10 hPa, ambiguity or no-change trials. Existing source native QC0 prevents modified science approvals. Stage39 real original US-UMB file/ZIP source member inventory is emitted for precise source diagnosis; never invent original source or force replace from a processed ERA product.

**Stage40 code/docs committed; actual IRIDIS6 runtime pending. No approved forcing writes or Slurm submissions.**


## Stage41 direct negative/nearzero source RH ERA-family isolated trial and UMB FULLSET original source provenance

**Stage40 actually executed on IRIDIS6 26 Oct 2026:** 14 out of 15 original shortlisted P2/P3 events have negative implied original tower RH (unphysical T+VPD) and one `US-Var_E0017` has extremely low implied RH 0.393141%. Existing investigator rule prioritizes ERA5/ERA5-Land repair candidates for negative or near-zero RH, but original source invalidity does not independently establish replacement ERA RH; original Stage39 full-event candidate VPD changes can exceed 18 hPa. No source Stage24 approved166, P1 manual HOLD46, original 1574 P2/P3, original ten saturation-platform HH or production DATM model forcing changed.

[Stage41 source](scripts/stage41/41_policy_negative_RH_ERA_overlay_trial_and_US_UMB_FULLSET_source.py) and [pinned one-click IRIDIS6 runner](scripts/stage41/run_stage41_iridis6.sh) use original Stage40/39/38 native science provenance plus Stage27 original source and Stage24 QC guards to assemble 15 original full-event source-ERA RH science **research-only** candidates, never auto-approve or overwrite production. It makes exact source T/VPD, original source QC0, original RH negative or below 1% trigger, source-relative water saturation and no-new-2/4hPa Stage39 screen assertions. Each candidate remains research trial status and zero DATM authorization.

**Critical UMB correction:** Original US-UMB source DOES contain an on-disk `AMF_US-UMB_FLUXNET_FULLSET_HH_2007-2021_3-5.csv`, as Stage40 operator listed. This is **FULLSET_HH, not missing-source FLUXMET_HH**. Stage41 checks that real file's original `TIMESTAMP_START/TA_F/VPD_F/(QC)` for all **23** original Stage27 native source anomalies, reporting verified T/VPD/QC equivalence or explicit provenance HOLD; never silently recodes FULLSET-derived QC0, nor claims gapfill values are measured observations. See [exact original source path, science policy and pinned operator command](docs/STAGE41_RH_POLICY_15_EVENT_ERA_TRIAL_AND_UMB_FULLSET_SOURCE_2026-10-26.md).

**Stage41 GitHub code/docs committed; actual IRIDIS6 verification pending. No added science-approved forcing records or submitted Slurm jobs.**


## Stage42 actual Stage41 native source Post-v5 preflight and now-verified UMB original FULLSET source methods

**Stage41 actually executed 2026-10-26:** precisely **15 original negative/near-zero water-RH source episodes with 21 native half-hours** in ERA-family event-complete research-only overlay; **4** `SEVERE_MAGNITUDE_GT10HPA_REVIEW` and **11** `SOURCE_ERA_PROVENANCE_REVIEW_BEFORE_FORCING`. US-UMB true original `AMF_US-UMB_FLUXNET_FULLSET_HH_2007-2021_3-5.csv` compared to Stage27 T/VPD/QC and **all 23/23 match**. This removes earlier false missing-data-source assumption, **not** any science approval. All original QC0 protection and source-version provenance retained.

[Stage42 scientific pilot](scripts/stage42/42_postv5_isolated_15_ERA_events_and_UMB23_fullset_source_trials.py), [immutable one-click IRIDIS6 script](scripts/stage42/run_stage42_iridis6.sh) and [Stage41 actual operator evidence, original source hashes, scientific gates and runnable CLI](docs/STAGE42_15_ERA_CANDIDATES_POSTV5_ORIGINAL_EDGES_AND_US_UMB_FULLSET_2026-10-26.md). Stage42 rechecks all **15** Stage41 source ERA original events (21 HH) directly against original SHA-pinned FLUXMET_HH ZIP, native selected T/VPD/QC and before/after half-hour original neighbors, and performs two humidity-method research trials (source ERA, source MDS) for the **9 original US-UMB P2/P3 events (23 HH total)** using the independently verified original FULLSET_HH product. Its total is 15+18=**33 method×episode** research comparisons; 33 is not the number of unique native half-hours. The two UMB methods are evaluated, **not** automatically combined or chosen. Original source VPD measured QC0, missing source RH, original noncontiguous episodes, native neighbor missing, newly-created >2 or >4hPa boundary jumps, extremes and user-held/approved source conflicts remain science HOLDs. Does not modify any original forcing or submit Slurm.

**Stage42 committed and verified by GitHub SHA, awaiting operator execution. No additional scientific approval, no source/forcing/DATM modifications.**


## Stage44 fast full ten-site 1574 native P2/P3 source-physics triage (after Stage43 numeric trial)

**Stage43 actually executed successfully:** 10 original method×event numerical research trials, 15 native half-hours (US-UMB 5, US-Vcp 6, US-WCr 2, US-Wkg 2), all **unapproved**. Stage42 other 23 failed method options: 9 source MDS humidity missing, 4 new >4 hPa original-native boundary discontinuities, 4 proposed corrections >10 hPa and 6 uncertain original source neighbors. No source/production forcing changes.

[Stage44 full original 1574 P2/P3 native humidity physics and 483 original-event 10-site priority audit](scripts/stage44/44_all_1574_p2p3_physics_and_event_prioritization_readonly.py), [immutable one-click IRIDIS6 script](scripts/stage44/run_stage44_iridis6.sh), [operator evidence, exact source SHA pins and commands](docs/STAGE44_ACTUAL_1574_P2P3_TEN_SITE_FAST_PHYSICS_TRIAGE_2026-10-26.md). Rather than continue only around the 15 native pilots, this source-first stage applies already established physically invalid original RH / extreme-low RH triggers to **ALL 1574 original half-hours**, examines source ERA/MDS physically plausible options and aggregate complete-event coverage (original 483 episodes), flags protected QC0 and >10hPa VPD changes, and prints per-site original remaining backlog and investigation priorities. This is a *bulk research QC triage*, **not** automatic ERA correctness or a finished DATM/CLM forcing QC/Slurm submission.

**Stage44 GitHub code and pinned launcher published; operator IRIDIS6 run pending.** Original Stage24 approved166, P1 manually HOLD46, RH-platform10, all 1574 original science-unapproved P2/P3 and model forcing remain untouched. 0 full-site forcing science passes established.


## Stage45 full 483 original-source episode and native contiguous-run VPD boundary QC

**Stage44 actually executed on IRIDIS6 26 October 2026**, covering 1574 original preselected P2/P3 native source half-hours across 483 original episodes: 1477 negative RH and 97 original RH below 1% when reconstructed from original selected T and VPD over liquid water. This is **the already-filtered RH/VPD anomaly cohort**, NOT the entire station dataset. Source-processed ERA RH appears physically within 0–100% for all input points, but original-native before/after edge safety, exact tower met provenance and independent reference remain unresolved. Original 166 approved Stage24 edits, 46 P1 human HOLD, 10 saturation platforms and all original 1574 P2/P3 untouched; NO production forcing or Slurm changes.

[Stage45 full 483 source-native episode true ZIP/FULLSET VPD boundary QA, plus maximal source-adjacent P2P3 connected-run alternative](scripts/stage45/45_actual_483_event_full_native_era_boundaries_and_connected_runs.py), [one-click pinned launcher](scripts/stage45/run_stage45_iridis6.sh), and [operator Stage44 evidence and immutable command](docs/STAGE45_ALL_483_SOURCE_EVENTS_AND_CONNECTED_RUNS_REAL_BOUNDARY_QC_2026-10-26.md). Stage45 verifies original native T/VPD/QC and SHA-pinned site ZIP or real US-UMB FULLSET source, calculates hypothetical source ERA RH at original T, actual original vs trial internal and external >2/4hPa VPD crossings, original QC0 and other unapproved P2/P3 neighbor protections. In addition to the **483 original Stage27 events**, maximal **physically contiguous source-native P2P3 runs** are screened across original episode IDs, mitigating artificial event-fragment boundaries without filling missing times. Site-source failures are explicit HOLDs rather than silently passed. Output is research-only input and numeric science triage; no automatic source edits or model-ready forcing acceptance.

**Stage45 code, docs and immutable one-click operator command committed and hash-verified; not yet run on IRIDIS6.** All Stage24 original approved/HOLD protections retained.


## Stage46 parallel review: assistant source neighbors versus Claude large VPD/jump events

**Stage45 actually executed on IRIDIS6 (2026-10-26):** source native T/VPD/QC verified **1574/1574 original P2P3 HH**, covering **483/483 original source episodes** (9/9 affected AmeriFlux sites, US-UiD 0 P2P3). Original ±30 minute native boundary analysis screened 483 events and exactly 483 native contiguous runs (no source event count reduction on merging). Mutually exclusive event priority: **333** `ORIGINAL_EXTERNAL_NEIGHBOR_QC_OR_RH_UNCERTAIN`, **77** `LARGE_VPD_CHANGE_GT10HPA_REVIEW`, **22** `NEW_EXTERNAL_OR_INTERNAL_GT2HPA_HOLD`, **9** `NEW_EXTERNAL_OR_INTERNAL_GT4HPA_HOLD`, **42** `NUMERIC_SOURCE_NATIVE_SCREEN_NO_SCIENCE_APPROVAL`. The 42 numerically low risk source original events are STILL science-unapproved; 1574 source P2P3 original HH, 46 P1 manually HELD, 10 RH plateau holds remain outstanding, and 166 Stage24 previously approved records are retained. No site overall met/forcing science pass inferred, no model or forcing modifications.

[Stage46 full source evidence and per-event split](scripts/stage46/46_split_483_events_between_science_tracks_readonly.py), [one-click verified launcher](scripts/stage46/run_stage46_iridis6.sh), and [Claude detailed safe research handoff, exact 108 owned events, Assistant 375 owned events, source SHA and command](docs/STAGE46_PARALLEL_CLAUDE_ASSISTANT_483_EVENT_HANDOFF_2026-10-26.md). The **Assistant track** owns the 333 problematic original native neighbors + 42 low-risk numeric science screens; **Claude track B** owns 77 >10hPa proposed changes + 22 new >2hPa and 9 new >4hPa VPD discontinuities. Stage46 exports exact site/original time/event/edge source-QC evidence as independent CSVs and the ten-site outstanding half-hour versus event census; the two tools should work in disjoint GitHub folders to avoid production overwrites. Crucially the original 1574 is a count of HH whereas 483/333/77/22/9/42 are event counts, **not** interchangeable. Original forcing source, DATM/CIME, 166 approved, 46 human HOLD, 10 RH platform, all 1574 unapproved remain unchanged.

**Stage46 source/docs and GitHub SHA-pinned operator launcher published; not yet run on user's IRIDIS6.**


## Stage47 Assistant Track A source-neighbor RH/QC and low-numeric ERA/MDS evidence

**Stage46 actually executed successfully on IRIDIS6** with all 483 original selected P2/P3 source events assigned disjointly: **375 Assistant** (333 unsafe/unknown external native source neighbors; 42 low-numeric-risk source ERA candidates), and **108 Claude** (77 proposed VPD reconstructions >10hPa, 22 newly crossed >2hPa VPD jumps, 9 newly crossed >4hPa jumps). Original 1574 source half-hours all remain science-unapproved; 166 earlier approved, 46 manual P1 HOLD, ten RH platform suspect remain unchanged. Nine of nine affected Batch05 original source site T/VPD/QC populations were verified, and US-UiD has zero identified P2/P3 source anomalies but no full forcing acceptance claim.

[Stage47 Track A native source QC and ERA/MDS relative reference science evidence](scripts/stage47/47_assistant_trackA_neighbor_qc_and_42_numeric_science_evidence_readonly.py), [SHA-pinned one-click IRIDIS6 launcher](scripts/stage47/run_stage47_iridis6.sh), and [real Stage46 split, operator paths, copyable commands, six source-only outputs, and Claude separate work handoff](docs/STAGE47_ASSISTANT_333_NEIGHBORS_42_NUMERIC_SCIENCE_2026-10-26.md). Stage47 explicitly classifies **333** original neighbor-source QC0/QC1/QC2/nonmeasured, original RH below 0/1/10/>100% and other unapproved P2/P3 edges, before-vs-after potential numerical jumps without treating invalid neighbor humidity as physical truth. It independently screens the **42** low numeric source-ERA events for complete original source half-hour coverage, original QC0 protection, ERA vs MDS RH source agreement, source tower-vs-ERA T discrepancies, and source reanalysis-only reference limitations. This is *science diagnostic work*; it neither automatically approves a candidate nor changes model-ready forcing. Claude's separate **108** high-risk event source audit is untouched.

**Stage47 published and immutable SHA-verified in GitHub, actual IRIDIS6 execution pending.**


## Stage48 Assistant Track A: corrected fail-closed screening of 122 source-priority events

**Stage47 actually passed on IRIDIS6.** Assistant owns 375 original source events; the 333 neighbor-uncertain ones comprise **217 original extreme-low RH neighbors, 80 QC1 neighbor cases and 36 QC2/nonmeasured neighbor cases**. The other **42** original events have low source-native VPD numerical risk, but still lack independent scientific ERA RH validation (31 ERA-only reference, 9 >5°C tower-vs-ERA temperature discrepancy, 2 ERA/MDS RH disagreements). Claude separately owns **108** higher-risk original events; no overlap.

**Stage48 v1 failed twice on IRIDIS6 on 2026-10-27:** its pinned source verified and self-test passed, but the first initial QC1 candidate with a native gap or newly introduced >2/>4hPa VPD jump raised `ValueError("source event has gap or ERA trial creates new VPD jump")` at source line 179. The **initial 80 QC1 + 42 low-numeric = 122 events are a shortlist, not 122 scientifically or numerically accepted repair events**. This failure did not produce an accepted new overlay, nor change original source, DATM, CIME, Slurm, or 166 Stage24 approved/46 P1 manually HOLD/10 RH plateau values.

[Corrected Stage48 source-science screen](scripts/stage48/48_trackA_full_event_122_unapproved_ERA_pilots_and_253_source_holds.py) and [SHA-pinned corrected IRIDIS6 launcher](scripts/stage48/run_stage48_iridis6.sh), documented with actual failure evidence and exact immutable source pins in [Stage48 corrected handoff](docs/STAGE48_ASSISTANT_122_RESEARCH_EVENTS_AND_253_HOLDS_2026-10-26.md). The corrected script checks source-native full-event half-hour continuity, Stage45 internal/external new 2/4hPa VPD crossings, original QC0 and complete ERA RH coverage, >10hPa source-ERA VPD shifts, original T/VPD/QC at Stage27, and disjoint prior approved/HOLD science cohorts. **An ineligible event is now explicitly placed into a *new event-level HOLD CSV*, and other events continue**, so `eligible_count + additional_gate_HOLD_count = 122`. The other 217+36=253 original source neighbor science HOLDs are preserved; across Assistant Track A, `eligible + newly_held + previously_held = 375`. Existing Stage43 15 unapproved native research candidate values are de-duplicated where overlapping, not forced through the new quality gate. The eligible count is determined only by actual corrected operator execution and is NOT asserted to equal 122. All science candidates remain `science_approval=NO` and `production_DATM_permission=NO`.

**Corrected Stage48 GitHub source/launcher SHA-verified; IRIDIS6 execution pending. No new science approvals, no model-ready forcing modification.**


## Stage49 Assistant science reference and source-native jump audit after Stage48 SUCCESS

**Actual Stage48 operator SUCCESS, 27 October 2026:** Initial Stage47 **122** source priority original events (80 QC1 neighbors + 42 previous low-numeric Stage45 candidates) were screened individually. **70** original events covering **141 native HH** passed *numerical* source ERA/RH-at-original-T VPD boundary checks and remain UNAPPROVED; **52** original events created new external native VPD threshold crossings and remain HOLD. In those 52 events, **46** triggered new >2hPa jumps, **40** triggered new >4hPa jumps, with **34 events overlapping both**. Other Assistant **253** earlier source-neighbor RH or QC2 holds remain: 217 extremely low source-neighbor RH and 36 QC2/nonmeasured neighbor events. Source original **375=70+52+253** Assistant events accounted for, all Stage43 earlier **15** unapproved source HH exactly included in 141 with no duplicate repair. Claude's exclusive **108** original science events not touched. Original **1574** P2P3 unapproved source HH, previously approved 166, 46 original P1 manually held, 10 RH source saturation holds and official DATM/CIME/Slurm remain unchanged, **zero new science approvals**.

[Stage49 readonly science source-evidence auditor](scripts/stage49/49_assistant_70_candidate_reference_and_52_new_jump_science_audit.py), [GitHub SHA-pinned one-click operator launcher](scripts/stage49/run_stage49_iridis6.sh), and [full actual Stage48 science event results, immutable commands and expected outputs](docs/STAGE49_ACTUAL_STAGE48_70_CANDIDATES_AND_52_NEW_JUMPS_2026-10-27.md). Stage49 audits the 70 eligible *numerical* source ERA candidates against original source tower T/VPD/QC, source ERA-vs-MDS RH and tower-vs-ERA temperature reference discrepancy, and examines the 52 **rejected** ERA methods' two actual native source external boundaries (104 original edges) for original and trial VPD discontinuities, original QC0/1/2 and physically dubious neighboring humidity; the other 253 original source neighbor holds and Claude's 108 remain untouched. **No ERA humidity validity claim, source science approval, forcing writes, or Slurm jobs. Stage49 code and fixed SHA launcher published, actual IRIDIS6 execution pending.**


## Stage50 Assistant source reference priority and true eventwide RH-offset VPD boundary sensitivity

**Stage49 actually succeeded on IRIDIS6 2026-10-27:** Assistant original 375 science-event split remains **70 numerical source-ERA research candidates over 141 original native HH** and **305 source science HOLD events (52 external new jump + 253 original low RH/QC2 neighbor)**. Stage49 original candidate source evidence: **44** source ERA-only (no MDS RH reference), **4** source MDS–ERA RH disagreements >10 percentage points, **22** tower-versus-source ERA temperature differences >5°C. Stage49 rejected source ERA original event boundary: **35** events with new jump relative to original QC0 neighbor, **17** relative to QC1 neighbor. Original Stage49 104 boundary records and Stage45 original signed neighbor source VPD permit actual physics-aware numerical counterfactual screening; do not alter QC0 or infer ERA RH is station-grounded truth.

[Stage50 SHA-pinned exact original full-event +/-30min RH offset research code](scripts/stage50/50_trackA_eventwide_RH_offset_hypotheses_and_70_reference_queue.py), [one-click mobile-safe IRIDIS6 launcher](scripts/stage50/run_stage50_iridis6.sh), and [full actual Stage49 results, scientific limitations and reproducible invocation](docs/STAGE50_TRACKA_70_REFERENCE_AND_52_TRUE_NATIVE_EDGE_RH_OFFSET_2026-10-27.md). Stage50 ranks the 70 unapproved source candidates by exact meteorological evidence gap, and tests one **constant RH offset across the complete event** for each of 52 rejected source ERA scenarios using actual original Stage45 signed native VPD at both external neighbors. Check exact Stage49 edge reproducibility, full event, original QC, physical RH bounds, new internal/external 2/4hPa jump thresholds, max 10hPa modification and maximum 0.5hPa newly worsened original jump. **This is intentionally an artificial controlled sensitivity**, never a scientifically validated original RH source calibration, and even mathematically passing hypotheses are still science HOLD. Original 166 approved, 46 P1 HOLD, ten RH plateau, all 1574 original P2P3, official forcing and Claude's 108 original events remain unchanged.

**Stage50 committed & pinned, not yet run on IRIDIS6; 0 new science approvals or DATM/Slurm modifications.**


## Stage51: source-authenticated 3 numeric RH hypotheses and 49 no-feasible-offset event science holds

**Actual Stage50 SUCCEEDED 27 October 2026:** Original Batch05 Assistant 375 science event split stays **70 previously source-ERA numerically passing but still science-unapproved (141 HH)**, **52 old-ERA source new-jump science holds**, and **253 original neighbor low RH/QC2 science holds**. Within 52 eventwide *constant RH offset* mathematical sensitivities, **3** met bounded physical RH and original VPD native continuity screening (not yet science-supported real humidity), while **49** had no feasible offset within ±20 percentage points / 0.5-pp grid and >2/4hPa native edge + <=10hPa original source delta screens. These 49 are **not declared unfixable** by other meteorologically supported methods. The earlier 70 still lack independent site RH/QC evidence (44 ERA-only, 4 MDS–ERA humidity disagreements >10 pp, 22 source tower–ERA temperature discrepancies >5°C). Original 1574 P2P3 native HH, Stage24 approved166, 46 P1 manual HOLD, 10 RH platform source HOLD, official DATM/CIME/Slurm and Claude's **separate 108** original source events all unchanged, **zero newly approved fixes**.

[Stage51 scientific source verification of the 3 original numeric-only RH offset hypotheses, plus mechanism-specific 49 no-feasible-offset source science holds](scripts/stage51/51_trackA_three_numeric_hypotheses_and_49_failed_offset_mechanisms_readonly.py), [one-click SHA-pinned IRIDIS6 launcher](scripts/stage51/run_stage51_iridis6.sh), and [Stage50 actual numbers, scientific limitations and immutable commands](docs/STAGE51_STAGE50_SUCCESS_THREE_NUMERIC_SENSITIVITIES_FORTYNINE_HOLDS_2026-10-27.md). Source Stage51 recomputes the 81 original eventwise offset grid possibilities with true Stage45 signed source ±30min neighbors and source T/VPD/QC, reproduces eligible **3** eventwide original native HH and identifies nearest still-ineligible constraints for **49**. Even numerically feasible solutions retain `science_approval=NO`, cannot become model forcing, and require original meteorology/source observations. Claude's 108 reserved event cases untouched.

**Stage51 original IRIDIS6 run FAILED at Python compile (invalid numeric-leading output keyword); corrected GitHub source commit `5778c165f100fe0d11b684c3d8cc5e1685ace479` and launcher commit `a3c80fbb35e53181c7fc25b1de24b00b8946d4e7` now pinned. Re-run required; corrected source not yet tested on IRIDIS6.**


## Stage52: original FULLSET/FLUXMET humidity provenance for Stage51 three numerical RH-offset hypotheses

**Stage51 corrected actually succeeded on IRIDIS6 28 October 2026**, confirming exactly **3** bounded constant RH-offset **numerical sensitivity only** source events: US-UMB E0003 1 native HH and −11.5 percentage points, US-Wjs E0079 3 HH and −19.5pp, US-Wjs E0114 4 HH and −9.0pp. These **8** original native HH are NOT science-approved humidity repairs, and each event touches a measured original QC0 neighbor that must be protected. Other **49** source events lacked a feasible offset under the finite ±20pp/0.5pp heuristic grid; **48** of their nearest failed candidates worsened at least one source-native original VPD boundary by >0.5hPa. This is only failure of the selected constrained method, not proof the original meteorology is unfixable. The remaining **70** earlier source-ERA numeric events and **253** neighbor science HOLDs remain original source science pending. Claude's **108** disjoint events untouched; previous 166 approved, 46 P1 manual HOLD, 10 RH plateau, all 1574 P2P3 original source HH and DATM/CIME/Slurm unchanged; zero new approvals.

[Stage52 original raw FULLSET/FLUXMET humidity-source observational provenance inspection](scripts/stage52/52_three_event_raw_humidity_provenance_and_49_source_holds_readonly.py), [pinned one-line IRIDIS6 launcher](scripts/stage52/run_stage52_iridis6.sh), and [actual Stage51 scientific evidence, exact event time/humidity source audit rules and full GitHub SHAs](docs/STAGE52_STAGE51_ACTUAL_THREE_NATIVE_RH_PROVENANCE_2026-10-28.md). Stage52 reads **only** the two relevant AmeriFlux sites' original raw ZIP/CSV native HH sources (US-UMB and US-Wjs) at the eight Stage51 original native half-hours, saves source package SHA256, raw available RH/H2O/T/VPD/QC columns and values, and flags whether raw candidate source tower T/VPD/QC matches previously verified Stage51 source meteorology. An original source `RH_F` is filled/processed, `RH_ERA` reanalysis, and any unfilled `RH` still needs original instrument/QC/units/provenance verification before being declared observation. **Never invent RH, shift timestamps without evidence, overwrite original observations, or treat numerical offsets as meteorological truth.** Additional read-only report tables carry forward 49 offset method holds and 70 source reference gaps. Claude's 108 untouched.

**Stage52 GitHub scripts/docs committed and immutable source pins verified; user IRIDIS6 execution pending.**
