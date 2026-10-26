# AmeriFlux Batch03 — ten-site science and forcing progress at 2026-10-26 19:39 UTC

## Latest changes after the original 19:39 UTC inventory

- **US-Mpj Stage13o 21:07 UTC — actual IRIDIS6 check/apply SUCCESS:** full 20/20 original QC1 2014 source halfhours passed operator-approved two-group SHA, original source QC0 bookends, paired original ERA RH and <=4hPa joins. New isolated 315360-row site science shadow at `science_trials/stage13o_Mpj_20HH_operator_approved_ERA_RH_20261026T210746Z_5c3c8653`; exactly 17 VPD_USE +17 QBOT field-value edits, three existing centers plus original 2018 and 2020 protected. No further human review of those same two 2014 segments needed. Production DATM/AD400 still HOLD. [Exact results](STAGE13O_OPERATOR_APPROVED_US_MPJ_TWO_10HH_ERA_RH_RESEARCH_SHADOW_20261026.md).
- **US-NR1 Stage13p 22:36 UTC — operator IRIDIS6 actual --check and --apply SUCCESS:** approved exactly six 2022 original-native VPD/QBOT source companion ERA RH sites plus five 2004 QC2 original native PSRF/FLDS values. Isolated signed new NR1 candidate `science_trials/stage13p_NR1_6ERA_RH_5_PSRF_FLDS_OPERATOR_APPROVED_20261026T223628Z_6b3f07eb` passed original signed Stage12af/ak/al SHA chain, 490560 native row re-read and exactly 17 changes (6 VPD_USE, 6 QBOT, 3 PSRF, 2 FLDS), with 234 NR1 VPD/QBOT source holds still unresolved; US-Kon untouched, no Post-v5/DATM/Slurm. New Stage13q signed Me6 33 original source-native group audit now GitHub committed; read-only, not yet run on IRIDIS6. [Operator source approval and phone launcher](STAGE13P_NR1_USER_APPROVED_2022_SIX_RH_2004_FIVE_PSRF_FLDS_MOBILE_20261026.md).

## What the newest evidence actually establishes

This note reconciles **separate stages with different validation status**. It is not a new IRIDIS6 ten-site inventory and does not claim new HPC job submissions.

**US-MOz Stage13l** user-uploaded operator terminal log (login6003) verifies Stage13l v2 self-test, full immutable-source/CDS scientific `--check`, `--apply`, re-open and full 315,360-row differential **PASS**. Exact isolated candidate:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/stage13l_US_MOz_40HH_user_approved_CDSEra5Land_20261026T193902Z_95631db8`

Exactly **40** records changed in each `TA_USE, VPD_USE, TBOT, QBOT` (160 model-variable slots). Original Stage07, Stage13g and FLUXMET remain unchanged. The 2005-01-05 20:00–Jan06 09:00 **first 27 HH remain HOLD**, as does Jan09 negative QC1 source bias; no Postv5 / DATM / Spinup permission. See [Stage13L approved policy and signed script](STAGE13L_APPROVED_MOz_40HH_ERA5LAND_PAIRED_REPAIR_20261026.md).

**US-Me2 clock** user-reported actual cluster Stage14a PASS, documented separately on [GitHub PR #11](https://github.com/lyanyeung/CLM-FATES-single-site-workflows/pull/11), which is **OPEN / not merged to main** as of this check. The separately supplied original source BIF (US-Me2, GROUP_ID 12976) says fixed `UTC_OFFSET=-8` without DST; 368160 FULLSET native rows and 753840 standalone ERA native rows complete; four original source row identities local 2014-12-31 20:30–22:30 correspond to UTC **2015-01-01 04:30–06:30**. **Only the missing-clock-metadata hold has been resolved.** Four original humidity events remain to be checked for source/QC/thermodynamics/continuity; no new Me2 forcing or DATM run and no production approval.

## Ten-site comparison (last verified comparable site-numerical report vs newer separate research trials)

Last complete 10-site survey: [Stage12ai 2026-10-26 03:00 UTC](STAGE12AI_20261026_TEN_SITE_STATUS_AFTER_KON_12AH.md). Exact selected nine-site baseline was 3788 VPD/QBOT-missing site-native time-step rows (US-MMS is hourly; all other listed stations are half-hourly); 3789 any-source-missing rows (one extra US-NR1 nonhumidity-only source row); US-Me2 was not included in a comparable numeric source. **These counts are NOT a newly rerun post-19:39 inventory.** Later, some Kon and NR1 research candidates changed numerical completeness without production/admission. No ten-site model is verified as production-approved.

| Site | Verified latest production-selected source gaps (Stage12ai baseline) | Later research evidence / separately verified work | Blocking issue(s) |
|---|---:|---|---|
| US-MOz | 0 | **Stage13l 40/40 exact native slot repairs PASS in isolated 315360-row shadow, operator-approved** | earlier first 27 QC1 2005 halfhours & Jan09 bias held; source/PFT footprint, tower-specific ZBOT (HEIGHTC=24.2m is canopy not sensor), post-v5/DATM source QA |
| US-Mpj | 0 | Stage13b/13c source review, one QC0 temperature correction approved in operator's six-stage decision | five source VPD issues (three altered candidate values + two low-but-positive original held unchanged); PFT/land surface and Post-v5 release QA |
| US-NC2 | 0 | Stage11q numeric shadow and six QC0 temperature correction operator policy includes four NC2 spikes | **13 VPD manual records** incl 2025 source/ERA/time provenance, Jan2019 05:30 extra T source event, PFT and Post-v5 QA |
| US-Kon | 389 | Stage12ay latest signed **RESEARCH-ONLY** after Stage12an/ax/ay: **77 missing** (70 routine bridge proposals evaluated, 9 specially protected holds), 77 remains NON DATM; earlier VPD repairs unapproved as production | 77 unresolved source-native research gaps and approval/scientific provenance of prior hundreds of alternative humidity hypotheses |
| US-Me6 | 65 | Stage12ac operator-approved five native 2017 Jul04 source humidity patch already included; original 33 candidate procedure approvals require independent final on-grid native audit | missing humidity 65 in last signed selected source; 33 candidate methods / 29 >5°C source tower-grid T holds; source-specific continuity and original-source QC |
| US-MMS | 16 **hourly** records | Stage12g selected | 15 source-year evidence slots + one separate physics/source hold; native hourly clock (not 30min) and humidity QC |
| US-MtB | **2840** | Stage12j tested four bulk methods; **all four failed the original QC0 external analogue science gate** | high-elevation station/grid T bias, humidity physics, source-year evidence, protected hard holds; cannot approve blanket fill |
| US-NR1 | **240** | Stage12al six exact source-native ERA-RH science `RESEARCH-ONLY` values reduced separate research gap **240 -> 234**, but not operator-approved final input; Stage12ak nonhumidity research suggestions unapproved | 6 specific RH near 2022-09-10 QA, other 234 hold events, four original nonhumidity missing flags overlap VPD gaps except one unique timestamp |
| US-NR3 | **238** | Stage12g selected | source-year gaps, 172 original physics holds and native RH/VPD/QBOT QA |
| US-Me2 | not quantified | **Stage14a cluster time metadata verified in open PR #11**; local-standard UTC−8, no DST, four source local2014=UTC2015 records exact | four humidity-event source/ERA/physics/continuity reviews; no comparable selected 21yr NOLEAP source and 2020-fire/PFT historical surface policy; PR not yet merged |

### Reliable status distinctions

- **3/10 site candidates fully numerical** (US-MOz, US-Mpj, US-NC2) in the verified original census; US-MOz's 40 new repairs are now in a sealed isolated research-only successor.
- **6/10** had missing selected-source humidity (US-Kon, US-Me6, US-MMS, US-MtB, US-NR1, US-NR3). Original 3788 native-time-step subtotal is historical snapshot; Kon 77 and NR1 234 are not automatically admitted because latest source trials are not production-authorised and are not an independently rerun all-ten consolidated selected-input audit.
- **US-Me2** documented time metadata gate is resolved, but no forcing repair or production candidate has yet been established in the open PR.
- **0/10 confirmed Post-v5 / DATM / AD400 model-ready**; all ten still need input height (ZBOT) and actual active surface/PFT/case-forcing implementation validation where not already evidenced. Recommended PFT compositions are scientific assumptions, not evidence they have been applied.

## Recommended immediate next actions

1. **Merge or review PR #11** to propagate US-Me2 verified UTC metadata to main without losing concurrent README changes. The other conversation can handle the four local-2014/UTC-2015 humidity records; it cannot treat metadata verification as forcing repair.
2. **Parallel quick-gap work:** US-MMS 16 first (verify 15 missing year sources and one physics HOLD); US-Me6 65 (apply user-approved native-source 33-event policy only after original source QC and continuity); US-NR1 240 selected / 234 science proposal (explicit six-slot RH adoption decision + selected nonhumidity reconciliation). US-NR3 238 next. Treat existing isolated trials as candidates until explicitly admitted.
3. **US-Kon:** prioritise reviewing one final Stage12ay **77 missing research source-native** register, nine hard holds and complete approval of previously hypothetical filled values; do not claim its original selected source's 389 is already repaired in production. Avoid restarting one micro-stage per event.
4. **US-MtB:** fundamental critical-path site with 2840 missing. Needs external data/source and altitude/grid representativeness evidence; do not override the four Stage12j failed QC0 methods.
5. **Numerically complete three-site Post-v5 science:** US-MOz remaining first 27 and Jan09, US-Mpj five native VPD manual cases, US-NC2 thirteen VPD/time-related cases, plus ZBOT (meteorological measurement height vs canopy height) and active observed PFT/surface case. All must be resolved before any model submission.

**Do not invent a completion ETA** from these source statistics: missing source and unavailable independent validation are the critical path rather than script execution speed.
