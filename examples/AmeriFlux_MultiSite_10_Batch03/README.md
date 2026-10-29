# AmeriFlux MultiSite 10 — Batch 03

> **2026-10-29 06:50 UTC US-Kon Stage14O ACTUAL verified tower QC+both ERA sources all 9 missing:** [complete original 2011/2012 ±2h published tower QC0/1/2, paired FLUXNET ERA and independently SHA-verified ERA5-Land T2m/D2m/RH](docs/US_KON_STAGE14O_ACTUAL_9_NATIVE_EVENTS_TOWER_ERA5LAND_HUMAN_DECISION_20261029.md). Source manual review identifies **3 original observed-QC0 RH contiguous group candidates**: 2011-Feb22 3 missing, 2011-Oct23 5 VPD QC1 including 1 missing, 2012-Feb25 3 VPD QC1 incl 1 missing + 2 original T QC1 candidate repairs. [Stage14P three exact original-QC0-endpoint bounded, per-group atomic research-only 11-VPD-HH/2-T-HH test](scripts/stage14/14p_US_Kon_three_QC0_connected_blocks_5of9_research.py), not yet IRIDIS6 executed; **if** all groups pass, 9 science missing may fall to 4, not zero. Other four (May26, Sep29, Oct15 2011, Aug05 2012) remain source-science HOLD; never alter original data or submit AD400.


> **2026-10-29 — US-Kon FINAL nine manual observation/ERA5-Land source-context task:** [9 exact original source TA_F/VPD_F QC0/QC1/QC2 and available Stage14M true-QC0 bracketing evidence](docs/US_KON_NINE_HOLD_FINAL_MANUAL_NATIVE_TOWER_PAIRED_ERA_ERA5LAND_CONTEXT_20261029.md); next [single Stage14O read-only script](scripts/stage14/14o_US_Kon_FINAL_nine_original_tower_ERA5Land_pm2h_READONLY.py) prints all nine actual native center and seven grouped ±2h FLUXMET tower/paired ERA/independently SHA-verified **ERA5-Land T2m/D2m/RH/SP**, explicitly unavailable if no verified local site-year archive. Current Stage14N 0/3 science passes; nine protected NaNs unchanged; no automatic source edits or DATM/AD400 submission.


> **LATEST 2026-10-29 06:36 UTC — third Batch03 ten-site checkpoint: 7/10 ZERO-NaN research meteorology, 3/10 not yet numerically complete.** [US-Kon Stage14N ACTUAL original-QC0 RH trial **0/3 passed**; all 9 protected humidity NaNs remain, Stage14K retains 68 low-confidence research fills, Stage14L 7-neighbor alternative still science-uncertain. **STOP further automatic Kon patches** pending new independent observations or separately authorized model sensitivity](docs/US_KON_STAGE14N_ACTUAL_0_OF_3_PASS_AND_FINAL_HOLD_DECISION_20261029.md). **Claude delivered** signed zero-NaN US-Me6 and US-NR1 CL03 research shadows ([handback](docs/US_ME6_NR1_CLAUDE_HANDBACK_20261029.md)) and zero-NaN US-MtB research ([handback](docs/US_MTB_CLAUDE_HANDBACK_20261029.md)); along with US-MMS, US-MOz, US-Mpj, US-NC2 these form 7/10 numerically complete research sources. Remaining: US-Kon 9; [US-NR3 238 humidity HH, Claude Stage08 evidence/alternatives but no forcing candidate approved](docs/US_NR3_CLAUDE_STAGE07_EVENT_DECISION_REPORT_20261029.md); [US-Me2 clock proven UTC-8, four humidity-science HOLDs and complete model source not yet established](docs/US_ME2_CLOCK_EVIDENCE_20261026.md). **Zero sites have global Post-v5/PFT/ZBOT/DATM/AD400 production signoff by this progress report**; no Slurm submitted.


> **2026-10-29 06:28 UTC US-Kon Stage14M ACTUAL TRUE QC0 PROVENANCE PASS:** [original US-Kon 2004–2019 280320HH, no material nonhumidity source difference, 184026 paired real QC0 source observations sitewide, 6/9 protected holds genuinely bracketed ±6h, 11 severe VPD>10hPa edges; exact nine-HOLD science classification](docs/US_KON_STAGE14M_ACTUAL_TRUE_QC0_EVIDENCE_AND_FINAL_3_CANDIDATE_RULE_20261029.md). **Next** [Stage14N only 3 source T-QC0/VPD-QC1 true-QC0-endpoint RH interpolations, check BOTH native halfhour joins and physically closed VPD/QBOT, keep other six missing and all 11 severe edges unchanged](scripts/stage14/14n_US_Kon_three_nearby_QC0_RH_candidates_ONEPASS.py). Other 3 of the 6 nearby-source holds are Feb22 2011 joint T inconsistencies and must NOT be auto interpolated. Current preferred Stage14K source **still has 9 actual missing, not DATM-ready**. Stage14N result unexecuted yet; no Post-v5/CIME/AD400/Slurm.


> **2026-10-29 04:57 UTC US-Kon Stage14L ACTUAL research result and final science-evidence step:** [7 extra original QC1/QC2 finite neighbours changed, 46→41 warnings across same 96 original routine-source contact edges but 44 warnings still across 103 expanded edges; 68 old numerical routine fills and 9 protected NaNs unchanged](docs/US_KON_STAGE14L_ACTUAL_7_FINITE_QC_EDITS_41_OF_96_EDGES_AND_FINAL_14M_QC0_EVIDENCE_20261029.md). **Keep Stage14K as the preferred least-modified *incomplete* research scenario**, Stage14L as an unapproved sensitivity. Do not iterate blind source smoothing. [Stage14M one-pass original truly paired tower QC0 support of all nine source hard HOLDs and 44 remaining flagged source edges](scripts/stage14/14m_US_Kon_QC0_evidence_for_9HOLD_and_44_edges_READONLY.py) is only READONLY original science, not new humidity repair or production DATM/AD400 approval.


> **2026-10-29 04:49 UTC US-Kon Stage14K ACTUAL PASS but science edge issues:** [all 68 routine missing source VPD/QBOT transferred from paired ERA RH, 9 hard science missing protected, 280320-site T/VPD/QBOT physics pass; however 62/112 original native source joins flagged, including 43 VPD>4hPa, 18 RH>20pp, 8 QBOT>0.003](docs/US_KON_STAGE14K_ACTUAL_68_NUMERIC_SUCCESS_62_BOUNDARY_WARNINGS_AND_14L_QC_POLICY_20261029.md). **Next isolated research-only [Stage14L QC1/QC2 bounded finite neighbour source sensitivity](scripts/stage14/14l_US_Kon_68_QC_neighbor_connected_ERA_RH_sensitivity.py):** actual published FLUXMET source grade, source unchanged finite QC1/QC2, original QC0 protected, signed 9 hard HOLDs untouched; compare warning counts before/after, no production Post-v5, DATM, AD400 or Slurm.


> **2026-10-29 04:44 UTC US-Kon Stage14J ACTUAL PASS:** [77 exact remaining paired humidity NaNs across 35 native events, 68 routine ERA-RH scenarios individually water/ice physically feasible, 9 independently protected hard source science holds retained, source SHA verified](docs/US_KON_STAGE14J_ACTUAL_77_SOURCE_AND_STAGE14K_NEXT_20261029.md). Next [Stage14K isolate exactly 68 low-confidence humidity reconstructions and keep 9 original NaNs, with all source/QA fields unchanged and all boundary diagnostics](scripts/stage14/14k_US_Kon_68_ERA_RH_only_9HOLD_isolated_onepass.py). The research output will remain **incomplete and not DATM / AD400-ready**; no Slurm jobs. US-MOz Stage14I numeric 49 source repairs completed separately; original Jan08 QC1 caution preserved.


> **2026-10-29 US-MOz Stage14I ACTUAL 49 QC1 dual variant PASS, meteorological numeric stage closed:** [49 FLUXNET-companion ERA primary vs existing CDS ERA5-Land sensitivity, original 27+1+40 source edits untouched and selected 315360 thermodynamics PASS](docs/US_MOZ_STAGE14I_ACTUAL_49QC1_TWO_SOURCE_CHOICE_20261029.md); two pre-existing Jan08 original QC1→QC1 T jumps retained as original-source warnings, not fabricated QC0 interpolation. **Next active workstream is US-Kon** [77 exact remaining source-native humidity gaps (68 routine, 9 protected hard scientific HOLDs) with full signed Stage12AY/FLUXMET original QC one-pass provenance and ERA-RH *candidates only*, no forcing writes](scripts/stage14/14j_US_Kon_77_missing_source_QC_onepass_decision_READONLY.py). Claude retains US-Me6/US-NR1, advanced model US-NR3. No Post-v5, DATM, AD400, Slurm approval.


> **2026-10-29 US-MOz actual Stage14H Jan09 final original-QC review:** [Original Jan09 45 QC1/3 QC2/0 measured QC0, 27 negative T−ERA >5°C QC1 anomalies, 10 Jan08–10 >4°C selected T jumps; current Stage14G stays intact](docs/US_MOZ_STAGE14H_ACTUAL_JAN09_FINAL_QC_AND_14I_TWO_SOURCE_20261029.md). Next [bounded one-run Stage14I original 49 QC1 (6+3+40) FLUXNET companion ERA versus previously downloaded CDS ERA5-Land dual isolated research scenarios](scripts/stage14/14i_US_MOz_Jan09_49QC1_two_source_isolated_onepass.py); explicitly protect Jan09 3 QC2/Jan10 original QC0 and earlier 27+1+40 source corrections. This is a research numerical alternative, no Post-v5, DATM, AD400 or Slurm authorization.


> **2026-10-29 US-MOz Stage14G ACTUAL PASS:** [One QC1→QC1 native 19:30 T/e interpolation succeeded; the 5.885°C boundary was split into two 2.886°C edges; actual 27 ERA5-Land research trial and 40 operator-approved source repairs preserved; full 315360 water/VPD/QBOT model numerics PASS](docs/US_MOZ_STAGE14G_ACTUAL_SUCCESS_JAN09_LAST_ONEPASS_20261029.md). Source-science remains unapproved: the remaining Jan09 original QC1 source-negative T/ERA divergence can be **classified once** through [Stage14H final original raw QC0/QC1/QC2 one-pass read-only script](scripts/stage14/14h_US_MOz_Jan09_original_QC_onepass_final_triage_READONLY.py). No Post-v5, DATM, AD400 or Slurm permission.


> **2026-10-29 US-NC2 actual Stage14E PASS; now US-MOz next:** [US-NC2 confirmed 367920 fully finite signed Stage11Q source, all four March2025 suspect VPD jumps below 4hPa; 11 RHwater<5% and 1003 ice RH>100% warnings retained, no Post-v5](docs/US_NC2_STAGE14E_ACTUAL_367920_ONEPASS_MANUAL_DECISION_20261029.md). Next [US-MOz first 27 original Jan2005 QC1 region isolated reanalysis numerical sensitivity, preserve existing 40 operator-approved Stage13L slots](docs/US_MOZ_NEXT_FIRST27_QC1_ONEPASS_EXPLORATORY_20261029.md) via [signed-data one-pass script](scripts/stage14/14f_US_MOz_27QC1_onepass_isolated_ERA5Land_sensitivity.py). This new method is research-only, unapproved as measured tower source; no automatic CIME/DATM/AD400 or Slurm.


> **2026-10-29 ten-site numeric state and next action:** [5 completed numerical research forcings, 4 with quantified remaining VPD/QBOT gaps, 1 (US-Me2) without comparable completed input; next easiest US-NC2, one SHA-signed complete 367920HH source/2025-March QC review](docs/BATCH03_TEN_SITE_PROGRESS_AND_US_NC2_NEXT_ONEPASS_20261029.md), [pinned one-pass source code](scripts/stage14/14e_US_NC2_next_onepass_site_march2025_QC_READONLY.py). Stage11Q is selected ONLY if its actual signed output exists; otherwise use verified Stage11L. Claude studies US-Me6/US-NR1; US-NR3 is reserved; no production Post-v5/DATM/AD400 approval.


> **2026-10-29 03:56 UTC US-Mpj actual Stage14D full-site result:** [315,360 native HH all finite, water VPD/QBOT and TBOT conversion PASS; 17 signed Stage13O 2014 source repairs preserved; 610 RHwater<5% provenance warnings and 3,791 subfreezing RHice>100% phase-model cautions retained WITHOUT mass-clipping or forcing edits](docs/US_MPJ_STAGE14D_ACTUAL_FULL_SITE_PASS_MANUAL_DECISION_20261029.md). **Manual disposition:** meteorology numerical source QC closed; Post-v5/DATM/AD400 not yet admitted pending PFT, native time, ZBOT and actual DATM saturation/cap compatibility. US-Me6 and US-NR1 delegated study documents remain available; US-NR3 separately reserved.


> **2026-10-29 new station ownership and next run:** **Claude** scientific-workstream handoffs: [US-Me6 45 missing HH / 19HH winter source-QC2](docs/US_ME6_CLAUDE_DIFFICULT_SITE_HANDOFF_20261029.md) and [US-NR1 234 missing HH after signed Stage13P](docs/US_NR1_CLAUDE_DIFFICULT_SITE_HANDOFF_20261029.md). **US-NR3** stays reserved for independent advanced-model review. **ChatGPT/operator** takes lowest-friction **US-Mpj**: [one-pass Stage13O signed 315360 full meteorology and model physics screen](docs/US_MPJ_FASTEST_ONEPASS_SCIENCE_GATE_20261029.md), with pinned [read-only executable](scripts/stage14/14d_US_Mpj_final_315360_science_gate_READONLY.py). **US-MMS** Stage14C and **US-MtB** MtB04 are now numerically complete isolated research candidates, still not admitted for Post-v5/DATM/AD400. Claude handoff documents are saved to GitHub, **not automatically sent** to any Claude service.


> **2026-10-29 fastest remaining site: US-MMS.** [One-pass 16 native hourly humidity gaps and 18 historic original ERA negative-e anomalies — manual read-only evidence package](docs/US_MMS_ONEPASS_MANUAL_16_HOURLY_HOLDS_20261029.md). Do **not** assume 16+18 distinct or that the 15 missing verified grid-source records are repair approvals. The code is committed, first IRIDIS6 run pending. No forcing, DATM, AD400 or Slurm modifications.

> **2026-10-29 advanced-model reserved workstream:** [US-NR3 alpine 3504m science handoff (238 selected gaps vs 1,484 original QC2 cold-source anomalies; NO forcing writes)](docs/US_NR3_ADVANCED_MODEL_SCIENTIFIC_HANDOFF_20261029.md). This is a separate unresolved advanced review task, not a model-input signoff. US-MtB remains Claude's separate workstream, US-Me6 retains its manual HOLD review.

> **2026-10-29 manual science/HOLD review (current checkpoint):** See [manual classification of US-Me6 19HH and ten-site status, including Claude US-MtB ownership](docs/MANUAL_HOLD_TRIAGE_AND_TEN_SITE_STATUS_20261029.md). Stage13AR actual original measured QC0 day/year source review PASS but does **not** approve missing winter 19HH or both QC2 border writes. Latest US-Me6 shadow remains 45 missing HH. The latest independently reported all-ten common snapshot is from 26 Oct, not a newly rerun IRIDIS6 inventory; no site is certified for Post-v5/DATM/AD400.


**Documentation and runnable code:** [docs/README.md](docs/README.md) records the verified US-Me2 Stage14a result, exact commands, source/report locations and remaining humidity work. A complete standalone [code copy is also archived under docs/code/](docs/code/14a_US_Me2_documented_clock_READONLY.py), byte-identical to [the maintained Stage14a script](scripts/stage14/14a_US_Me2_documented_clock_READONLY.py). The clock audit has already passed on IRIDIS6; repeat execution is optional. No humidity repair or DATM acceptance is implied.

> **US-Me2 Stage14a VERIFIED on IRIDIS6, 2026-10-26 19:35 UTC:** the operator's actual run passed script SHA256, self-test, both full original source hashes/time axes, Stage07 source pins, and exactly **4/4** sealed Stage11a event row/time matches. **UTC_OFFSET=-8, no DST** is documented by separate site BADM; the missing-clock-metadata gate is now **RESOLVED_WITH_SITE_BADM_SUPPLEMENT**. Original rows **227899–227902**, local 2014-12-31 20:30–22:30, map to UTC 2015-01-01 04:30–06:30. Report: `reports/stage14a_US_Me2_documented_clock_20261026T193531Z_985d2919/`. The four events now need humidity-source/physics/continuity review; **humidity repairs=0, DATM=FALSE, jobs=0**. [Verified evidence and remaining work](docs/US_ME2_CLOCK_EVIDENCE_20261026.md), [operator-reported result](docs/US_ME2_CLOCK_CLUSTER_OPERATOR_RESULT_20261026.json), [Stage14a script](scripts/stage14/14a_US_Me2_documented_clock_READONLY.py). This supersedes historical UTC−8-hypothesis-only and missing-clock statements below; previous sealed reports remain unchanged.

> **Latest scientific status (2026-10-24):** Stage11M successfully inspected **four residual US-NC2 VPD transitions** (three introduced by Stage11L humidity-only additions, one inherited from Stage11H), including all **40 exact source-context rows**. The user selected **11 additional Stage11L ERA-RH humidity-only trial targets** after the original Stage11F choices, but **none has formal Post-v5 production acceptance**. Stage07/Stage11H/Stage11L remain SHA-protected, EC-tower temperature unchanged, and no DATM/spinup approval. [Stage11M verified log and boundary ledger](docs/STAGE11M_VERIFIED_FOUR_RESIDUAL_BOUNDARY_CONTEXT_2026-10-24.md). [Stage11N check](docs/STAGE11N_VERIFIED_US_NC2_CLOCK_AND_2025_ERA5LAND_GAP_2026-10-24.md) verified original tower location (35.8030,-76.6685; 5 m), published UTC_OFFSET=-5 (unapproved for automatic alignment), 4/4 boundaries, and NO existing US-NC2 2025 ERA5-Land bundle at the standard path. [Stage11O independent March 2025 ERA5-Land request](scripts/stage11/11o_us_nc2_2025_march_era5land_evidence.py) is ready, not executed.


This separate batch follows [Batch02](../AmeriFlux_MultiSite_10_Batch02/) for
the ten exact operator-supplied releases in [sites.tsv](sites.tsv).
The operator has completed and verified Stage00–10d diagnostic execution on IRIDIS6 as of 2026-10-24. All 10 packages were transferred and extracted; 3/10 Stage07 numeric QC-v5 trials completed, 7/10 remain humidity-blocked; all 32 required ERA5-Land year-site products are present; 1,924 residual humidity records passed Stage10d evidence triage. These are **scientific investigations, not approved forcing repairs**. No Post-v5 acceptance, DATM or CLM-FATES spin-up is authorized. Refer to the **[Stage00–10d scientific status and decision ledger](docs/SCIENTIFIC_REVIEW_STATUS_2026-10-24.md)** for verified operator results and limitations.

| Site | Exact package | Release year labels |
| --- | --- | --- |
| US-Kon | `AMF_US-Kon_FLUXNET_2004-2019_v1.3_r1` | 2004–2019 |
| US-Me2 | `AMF_US-Me2_FLUXNET_FULLSET_2002-2022_4-6` | 2002–2022 |
| US-Me6 | `AMF_US-Me6_FLUXNET_2010-2025_v1.3_r1` | 2010–2025 |
| US-MMS | `AMF_US-MMS_FLUXNET_1999-2023_v1.3_r1` | 1999–2023 |
| US-MOz | `AMF_US-MOz_FLUXNET_2004-2021_v1.3_r1` | 2004–2021 |
| US-Mpj | `AMF_US-Mpj_FLUXNET_2008-2025_v1.3_r1` | 2008–2025 |
| US-MtB | `AMF_US-MtB_FLUXNET_2009-2024_v1.3_r1` | 2009–2024 |
| US-NC2 | `AMF_US-NC2_FLUXNET_2005-2025_v1.3_r1` | 2005–2025 |
| US-NR1 | `AMF_US-NR1_FLUXNET_1998-2025_v1.3_r1` | 1998–2025 |
| US-NR3 | `AMF_US-NR3_FLUXNET_2007-2024_v1.3_r1` | 2007–2024 |

Release labels do not establish actual data coverage, native time step or
meteorological quality. US-Me2 retains its FULLSET format and original 4-6
suffix. Nine v1.3 packages and one FULLSET package are handled separately.

## Stage00: upload in the LOCAL WSL terminal

Local Windows source: `D:\Fluxes_Tower_Experiment\Ameriflux`.
WSL source: `/mnt/d/Fluxes_Tower_Experiment/Ameriflux`.
Each exact package must be directly contained as `<package>.zip` (ZIP
extension case insensitive) or a `<package>/` folder. ZIP takes priority
when both exist. Originals are copied without repacking.

Run in **LOCAL WSL**, not in an IRIDIS SSH terminal or native PowerShell.
From PowerShell, first run `wsl`, then paste:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/ameriflux_batch03_transfer"
  mkdir -p "$BASE/scripts/stage00"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage00/00_upload_ameriflux_batch03.sh"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage00/00_upload_ameriflux_batch03.sh" -o "$SCRIPT"
  bash -n "$SCRIPT"
  LOCAL_ROOT='/mnt/d/Fluxes_Tower_Experiment/Ameriflux' \
    bash "$SCRIPT" 2>&1 | tee "$BASE/upload_$(date +%Y%m%d_%H%M%S).log"
)
```

Requirements: Bash, curl, OpenSSH, rsync, sha256sum, find, awk, mktemp and
head. The script preflights all ten releases before connecting. It opens
one SSH master to `ly3n24@iridis6.soton.ac.uk`; enter a password once if
requested. Host-key confirmation and additional factors remain subject
to the SSH service. No password is stored in scripts or logs.

Every subsequent operation reuses a private socket in `/tmp`, uses batch
mode and cannot open a replacement network connection. If the connection
fails, the script stops without repeated password prompts. Rerun the same
command to connect once and resume; keep WSL and the network open during
transfer. The master closes automatically at exit.

Destination:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/packages/<PACKAGE>.zip
```

Folders use `packages/<PACKAGE>/`. `REMOTE` and `REMOTE_ROOT` may be
overridden. Existing files are preserved with `rsync --ignore-existing`;
partial transfers can resume. Every ZIP is SHA256 checked; folder transfers
receive a recursive checksum dry-run including extra remote files. A
same-named file with different content stops the run for inspection.
No source or destination package files are deleted.

Only the following line establishes upload success:

```text
UPLOAD VERIFIED: 10/10 (AmeriFlux Batch 03). Originals retained. No extraction or model jobs started.
```

## Stage01: extract and inventory on IRIDIS

After verified upload, run in an **IRIDIS terminal**:

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage01"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage01/01_extract_ameriflux_batch03.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage01/01_extract_ameriflux_batch03.py" -o "$SCRIPT"
  python3 -B "$SCRIPT" \
    2>&1 | tee "$HOME/AmeriFlux_Batch03_stage01_$(date +%Y%m%d_%H%M%S).log"
)
```

No `git pull` is needed. Standard-library-only extraction supports Python3.9+.
The script preflights all selected packages, recursively reads nested ZIPs
(up to eight levels), flattens CSV basenames and skips `toc.csv`/`!toc.csv`.
It checks size/CRC32, skips identical existing CSVs and refuses to replace
different CSVs or conflicting basenames. Source packages remain intact.
An interrupted extraction may leave a `.partial`; inspect it before retrying.

Raw output and separate batch report:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<SITE>/forcing/raw/<PACKAGE>/*.csv
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage01_extraction_<UTC>_<ID>.json
```

Nine v1.3 releases require a site-specific BIF and FLUXMET_HH or FLUXMET_HR.
US-Me2 FULLSET requires a site-specific FULLSET_HH or FULLSET_HR; absent BIF
is a metadata follow-up. Separate ERA5 HH/HR products are inventoried.
Native hourly products are retained without resampling. The inventory
records headers and the first timestamp pair; it does not validate full
coverage or meteorological values.

Successful extraction summary:

```text
BATCH03 SUMMARY: 10/10 PASS (extraction/structure only); failures: none
```

Read-only recheck after extraction:

```bash
python3 -B "$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage01/01_extract_ameriflux_batch03.py" --audit-only
```

`--sites US-Me2`, `--sites-root`, `--incoming-dir` and `--reports-dir`
are available. Audit-only creates no report or raw files.

## Stage02: read-only metadata and source-interval preflight on IRIDIS

After Stage01 finishes with `BATCH03 SUMMARY: 10/10 PASS`, run this in an
**IRIDIS terminal** (no `git pull` required):

```bash
(
  set -euo pipefail
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage02"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  curl -fLsS --retry 3 "$RAW/$REL/metadata_fallbacks.tsv" -o "$BASE/metadata_fallbacks.tsv"
  curl -fLsS --retry 3 "$RAW/$REL/coordinate_decisions.tsv" -o "$BASE/coordinate_decisions.tsv"
  SCRIPT="$BASE/scripts/stage02/02_check_batch03_metadata.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage02/02_check_batch03_metadata.py" -o "$SCRIPT"
  python3 -B "$SCRIPT" 2>&1 | tee "$HOME/AmeriFlux_Batch03_stage02_$(date +%Y%m%d_%H%M%S).log"
)
```

Stage02 reads BIF coordinates/IGBP/height records for nine releases, honors\nexplicit GROUP_ID-paired site coordinate decisions in coordinate_decisions.tsv\nfor US-Mpj and US-MtB (preserving their source BIF), and reads
the explicit official AmeriFlux site-page fallback for US-Me2 (the FULLSET
without BIF), and verifies only the *first* HH/HR source interval. It
does not write site data, surfaces, forcing, model cases or Slurm jobs.
Expected summary is `STAGE02 SUMMARY: 10/10 coordinate + first-interval checks PASS; failures: none`
if the actual data match the checks.

**Scientific hold:** US-Me2's official site page reports the 20 August
2020 Green Ridge Fire, 2021 salvage logging and later tower changes;
the current ENF label is not proof of a stationary ENF land cover
through 2002–2022. Surface/PFT choices need an explicit disturbance
history review. Its site-page coordinates (44.4526, -121.5589) are an
external metadata fallback, not coordinates read from the FULLSET release.
US-MMS has native hourly meteorology; preserve HR in later workflows.
Do not use BIF height records as a final ZBOT decision; compare the
curated BASE_MeasurementHeight reference and site-specific evidence.

## Stage03: isolated CTSM year-2000 reference point surfaces

After Stage02 passes 10/10, fetch the Stage03 driver and its exact metadata
dependencies to IRIDIS. Run `--check` first; `--run` only after the preflight
passes. The script is adapted from Batch02 and creates outputs exclusively in
`sites/MY_EC_SITE/<SITE>/subset_data_batch03_surf2000/` with a SHA256 receipt
for each station. It uses `CTSM/tools/site_and_regional/subset_data point`
with `--surf-year 2000 --create-surface --create-user-mods --lon-type 180`
and **does not** use `--dompft`. It retains the documented ctsm5.3.0
surfdata/mesh reference settings. Site metadata and the explicit selected BIF
GROUP_ID for US-Mpj/US-MtB are read and rechecked on every attempt.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage02" "$BASE/scripts/stage03"
  for FILE in sites.tsv metadata_fallbacks.tsv coordinate_decisions.tsv \
    scripts/stage02/02_check_batch03_metadata.py \
    scripts/stage03/03_make_batch03_surfaces.py
  do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  "$PYTHON_BIN" -B "$BASE/scripts/stage03/03_make_batch03_surfaces.py" --check \
    2>&1 | tee "$HOME/AmeriFlux_Batch03_stage03_check.log"
)
```

If it prints `PREFLIGHT: 10 ready + 0 verified existing = 10/10`
(or ten total across ready and verified), generate the reference surfaces:

```bash
PYTHON_BIN="$CONDA_PREFIX/bin/python"
"$PYTHON_BIN" -B \
  "$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage03/03_make_batch03_surfaces.py" --run \
  2>&1 | tee "$HOME/AmeriFlux_Batch03_stage03_run_$(date +%Y%m%d_%H%M%S).log"
```

Successful fresh generation prints `STAGE03 SUMMARY: created=10
skipped_verified=0 total=10/10`. Any existing incomplete output is retained
and blocks unsafe automatic overwrite. These are **exploratory reference**
surfaces, not scientifically approved PFT configurations or model input.
Stage04a should subsequently audit actual landunit and PFT fractions;
specifically review US-Kon/US-NR3 grassland, US-Mpj mixed IGBP and US-Me2
disturbance history. No DATM, case or Slurm jobs are created.

## Stage04a: audit generated landunits and natural PFTs

The operator's Stage03 log confirms `created=10 skipped_verified=0 total=10/10`.
Run the independent [Stage04a surface audit](scripts/stage04/04a_audit_batch03_surfaces.py)
on IRIDIS. It verifies Stage03 file inventories/SHA256 receipts, NetCDF
structure, landunit sums, and natural CLM PFT fractions. It reports separate
`pct_of_natural` and `pct_of_grid` values without replacing natural PFTs
or asserting a FATES parameter mapping. US-Mpj is reviewed against the
current WSA listing while retaining all original ENF/OSH/WSA BIF labels.
US-Me2 disturbance and the US-Kon/US-NR3 grassland sites are explicit
science-review flags. Site-level review remains required even if all
structural checks pass.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  "$PYTHON_BIN" -c 'import numpy; from netCDF4 import Dataset'
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage04"
  SCRIPT="$BASE/scripts/stage04/04a_audit_batch03_surfaces.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage04/04a_audit_batch03_surfaces.py" -o "$SCRIPT"
  "$PYTHON_BIN" -B "$SCRIPT" \
    2>&1 | tee "$HOME/AmeriFlux_Batch03_stage04a_$(date +%Y%m%d_%H%M%S).log"
)
```

The report contains `surface_summary.csv`, `natural_pft_detail.csv`
and `surface_summary.json`, saved to
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage04a_surface_<UTC>_<ID>/`.
A complete structural run prints `STAGE04A SUMMARY: 10/10 structural passes; 0 structural failures`.
This **does not** approve the ecological representativeness of gridded PFT
fractions or establish time-invariant post-disturbance conditions.
No surface, DATM, forcing, case or Slurm job is modified.

## Stage04b: full native source meteorology and paired ERA5 screening

The operator's Stage04a log confirms **10/10 surface structural passes**.
Scientific vegetation representation remains unapproved, especially US-MOz,
US-MtB, US-Me2/US-Me6, US-Mpj and US-NR1. This does not block separate
meteorological source screening.

[Stage04b](scripts/stage04/04b_audit_batch03_met_sources.py) audits the
seven primary meteorological variables and the matching ERA5 products
for the exact Batch03 release windows. US-MMS is native **HR (60 min)**;
all other Batch03 primary series are **HH (30 min)**.
No source repairs, interpolation, DATM or model jobs occur.
The review bounds and liquid-water RH reconstruction are exploratory,
not scientific acceptance. Time conventions still require verification.

Run on IRIDIS, first with `--check`:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  "$PYTHON_BIN" -c 'import numpy, pandas'
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage04"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage04/04b_audit_batch03_met_sources.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage04/04b_audit_batch03_met_sources.py" -o "$SCRIPT"
  "$PYTHON_BIN" -B "$SCRIPT" --check
)
```

Only after `SOURCE PREFLIGHT: 20/20 sources; 0 failures`, run:

```bash
PYTHON_BIN="$CONDA_PREFIX/bin/python"
"$PYTHON_BIN" -B \
  "$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage04/04b_audit_batch03_met_sources.py" \
  2>&1 | tee "$HOME/AmeriFlux_Batch03_stage04b_$(date +%Y%m%d_%H%M%S).log"
```

Outputs are isolated under
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage04b_met_<UTC>_<ID>/`.
The target summary is 20/20 source audits with no source failures;
REVIEW flags are expected to need further evidence and site-specific decisions.

## Stage05: paired review of exact Stage04b anomalies

Operator results confirmed `STAGE04B SUMMARY: 20/20 sources audited;
0 source failures; 292 REVIEW source-years; 83082 flagged native records`.
The exact input directory is:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage04b_met_20261022T022701Z_d845a292
```

[Stage05](scripts/stage05/05_review_batch03_source_events.py) classifies the
83,082 flagged native source records into mutually exclusive priorities,
reconciles Stage04b annual and event counts, compares primary to paired
ERA5 on exact original site timestamps, checks raw source-row values and
hashes, and records source QC. US-MMS keeps its native hourly step. A
numerically clear counterpart is never automatic evidence for replacement.

On IRIDIS, download Stage04b helper and Stage05 script. Run `--check`
first; it verifies manifest/source identities and reconciles counts without
writing outputs. Full Stage05 writes a separate timestamped report.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage04" "$BASE/scripts/stage05"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  for FILE in scripts/stage04/04b_audit_batch03_met_sources.py \
              scripts/stage05/05_review_batch03_source_events.py; do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  REPORT='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage04b_met_20261022T022701Z_d845a292'
  SCRIPT="$BASE/scripts/stage05/05_review_batch03_source_events.py"
  "$PYTHON_BIN" -B "$SCRIPT" --source-report "$REPORT" --check
)
```

If Stage05 preflight passes, run the same downloaded script without
`--check`:

```bash
PYTHON_BIN="$CONDA_PREFIX/bin/python"
REPORT='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage04b_met_20261022T022701Z_d845a292'
SCRIPT="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage05/05_review_batch03_source_events.py"
"$PYTHON_BIN" -B "$SCRIPT" --source-report "$REPORT" \
  2>&1 | tee "$HOME/AmeriFlux_Batch03_stage05_$(date +%Y%m%d_%H%M%S).log"
```

A valid run should show `STAGE05 SUMMARY: events=83082` and
`ledger_mismatches=0`; complete success still requires examining
the event-priority/status reports. No source, surface, forcing, DATM,
case or Slurm job is changed.

## Stage06: primary repair-scope diagnosis (no edits)

Operator Stage05 verified all **83,082/83,082** flagged source rows with
**zero ledger mismatches**, grouped into 16,820 episodes. Its exact report
is `stage05_event_review_20261022T023135Z_32b20d9c`, paired with
`stage04b_met_20261022T022701Z_d845a292` (both in the Batch03
experiment `reports/` directory). Of the 83,082 source records,
42,892 are primary product records and 40,190 are companion ERA5 records.

[Stage06](scripts/stage06/06_diagnose_batch03_repair_scope.py)
cross-validates the Stage04b/Stage05 report snapshots and isolates **primary**
meteorological issues: numeric/humidity predicates, same-timestamp source
comparison, original source QC, contiguous episodes and missing-data
durations. Flags and companion screening are review evidence only, **not**
an automatic ERA5 replacement or candidate approval. An independent QCv5
candidate and Post-v5 science gate remain mandatory before DATM.

Run on IRIDIS:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage06"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage06/06_diagnose_batch03_repair_scope.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage06/06_diagnose_batch03_repair_scope.py" -o "$SCRIPT"
  REPORT_ROOT='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports'
  SOURCE="$REPORT_ROOT/stage04b_met_20261022T022701Z_d845a292"
  REVIEW="$REPORT_ROOT/stage05_event_review_20261022T023135Z_32b20d9c"
  "$PYTHON_BIN" -B "$SCRIPT" --source-report "$SOURCE" --review-report "$REVIEW" --check
)
```

After the check passes, execute the same script without `--check`:

```bash
PYTHON_BIN="$CONDA_PREFIX/bin/python"
REPORT_ROOT='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports'
SCRIPT="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage06/06_diagnose_batch03_repair_scope.py"
"$PYTHON_BIN" -B "$SCRIPT" \
  --source-report "$REPORT_ROOT/stage04b_met_20261022T022701Z_d845a292" \
  --review-report "$REPORT_ROOT/stage05_event_review_20261022T023135Z_32b20d9c" \
  2>&1 | tee "$HOME/AmeriFlux_Batch03_stage06_$(date +%Y%m%d_%H%M%S).log"
```

Stage06 creates only timestamped reports in `reports/stage06_repair_scope_...`;
no source files, surfaces, forcing, cases or Slurm jobs are modified.

## Stage07: checksum-gated native QCv5 candidate trial (NOT DATM-ready)

The operator Stage06 report `stage06_repair_scope_20261022T023738Z_0a4d314f`
confirms 42,892 primary and 40,190 paired-ERA source events,
10,469 primary P0 numeric-screen events, 31,732 P2/P3 low-positive-RH
events, and no missing primary source timestamps/variable gaps. These
screens do not establish which values are genuine sensor errors.

[Stage07 driver](scripts/stage07/07_build_batch03_qcv5_candidates.py)
and [historical native engine](scripts/stage07/qcv5_native.py) adapt the
Batch02 isolated trial. The former verifies pinned Stage06 report hashes,
manifest years, primary/ERA file hashes, and native HH/HR source identity.
US-MMS remains hourly, US-Me2 uses FULLSET_HH, and every other site uses
FLUXMET_HH. Run `--check` before any candidate construction.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage07"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  for FILE in scripts/stage07/qcv5_native.py \
              scripts/stage07/07_build_batch03_qcv5_candidates.py; do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  SCOPE='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage06_repair_scope_20261022T023738Z_0a4d314f'
  "$PYTHON_BIN" -B "$BASE/scripts/stage07/07_build_batch03_qcv5_candidates.py" \
    --scope-report "$SCOPE" --check
)
```

A successful preflight prints `PREFLIGHT: 10/10 exact releases, 20/20 raw
SHA256 verified` and `CHECK ONLY: no outputs created`. Do not use any
trial for DATM or spin-up until a full post-QCv5 independent science review
passes. For trial build, explicitly run the same driver with `--run`
instead of `--check`, after reviewing the preflight. A trial writes
only into a fresh `qcv5_native_trial_...` directory; no raw products,
original surfaces, cases or Slurm jobs are modified. The engine retains
the historical QCv5 treatment, including logged humidity reconstruction
and 1% ERA-RH floor events requiring manual review. It is **not** a
claim that the historical rules are optimal for arid Batch03 sites;
particularly inspect US-MtB, US-Mpj and US-NR3 outcomes.

## Stage08: same-release RH sensitivity for seven humidity-blocked sites

The operator's Stage07 live candidate trial:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/qcv5_native_trial_20261022T024559Z_36c46e58`
completed **3/10** numeric candidates (US-MOz, US-Mpj, US-NC2);
seven failed with **2,273** unresolved humidity pairs (US-Kon 359,
US-Me2 4, US-Me6 1, US-MMS 22, US-MtB 15, US-NR1 173, US-NR3 1699).
The original trial and incomplete marker must remain untouched.

[Stage08 sensitivity driver](scripts/stage08/08_resolve_blockers_with_raw_rh.py)
uses the [separate RH engine](scripts/stage08/qcv5_raw_rh.py) to preserve
the three successful Stage07 candidates by SHA256 and rerun only seven
blocked sites. Only exact replicated humidity blocker rows may use
same-release `RH` to reconstruct VPD while preserving the candidate's TA
and PA. Valid RH does not establish independent measurement provenance;
all reconstructions require manual QC0/RH provenance review. The driver
never changes the Stage07 trial or primary sources.

On IRIDIS, **first run the read-only check**:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage07" "$BASE/scripts/stage08"
  for FILE in scripts/stage07/qcv5_native.py \
              scripts/stage07/07_build_batch03_qcv5_candidates.py \
              scripts/stage08/qcv5_raw_rh.py \
              scripts/stage08/08_resolve_blockers_with_raw_rh.py; do
    curl -fLsS --retry 3 "$RAW/$REL/$FILE" -o "$BASE/$FILE"
  done
  TRIAL='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/qcv5_native_trial_20261022T024559Z_36c46e58'
  "$PYTHON_BIN" -B "$BASE/scripts/stage08/08_resolve_blockers_with_raw_rh.py" \
    --stage07-root "$TRIAL" --check
)
```

Expected `STAGE08 PREFLIGHT: preserved=3 blocked=7 unresolved_records=2273`
if all original trial and script hashes match. After reviewing this
result, `--run` can build the separate sensitivity trial; if any site
remains blocked, the incomplete marker is retained and a further
scientific decision is needed. A complete selection is still not
Post-v5 accepted and is never sufficient to start DATM/spin-up.

## Stage08b: residual RH blocker classification (no candidate edits)

Stage08 ended `preserved=3 sensitivity_pass=0 failed=7 selected=3/10
inputs_unchanged=True`. Among 2,273 original unresolved humidity pairs,
349 met same-release RH numerical criteria but **none of the seven
sensitivity runs completed**; 1,924 remained unresolved. Same-release
`RH_QC` was unavailable for all 349 numerically eligible records.

[Stage08b](scripts/stage08/08b_diagnose_remaining_rh.py) verifies the
unchanged preserved Stage08 output and classifies the 1,924 remaining rows
by documented hold reason, missing/out-of-range RH, cold temperatures,
negative implied vapor pressure, and ERA RH screen status. These counts
may overlap and are **not** independent repair approvals. The output
is evidence only, not revised QCv5 or Post-v5 acceptance.

Run in IRIDIS:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage08"
  SCRIPT="$BASE/scripts/stage08/08b_diagnose_remaining_rh.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage08/08b_diagnose_remaining_rh.py" -o "$SCRIPT"
  TRIAL='/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/raw_RH_sensitivity_20261022T025645Z_3c43eb8b'
  "$PYTHON_BIN" -B "$SCRIPT" --stage08-root "$TRIAL" --check
)
```

If the preflight passes, run the same command with `--run` in place of
`--check` to create a new isolated
`reports/stage08b_rh_cause_<timestamp>_<id>` report with
`site_hold_summary.csv`, `unresolved_rh_records.csv`, and
`unresolved_by_year_and_reason.csv`. No inputs are modified.

## Stage08c: ERA5 humidity rejections for 1,924 residual events

Stage08b confirmed that all **1,924** remaining Stage08 blockers have
`HOLD_RH_MISSING_OR_NONFINITE`. The next evidence-only audit,
[Stage08c](scripts/stage08/08c_diagnose_era_humidity_blockers.py),
classifies **why companion ERA5 humidity does not meet the existing
QCv5 numeric preconditions**, and compares water/ice saturation
formulations below freezing only as a sensitivity (not a repair).

IRIDIS read-only preflight:

```bash
(
  set -euo pipefail
  PYTHON_BIN="$CONDA_PREFIX/bin/python"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage08"
  SCRIPT="$BASE/scripts/stage08/08c_diagnose_era_humidity_blockers.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage08/08c_diagnose_era_humidity_blockers.py" -o "$SCRIPT"
  "$PYTHON_BIN" -B "$SCRIPT" --check
)
```

After a successful preflight, `"$PYTHON_BIN" -B "$SCRIPT" --run`
writes only isolated `reports/stage08c_era_humidity_...` files.
The prior Stage07 and Stage08 incomplete markers must remain in place;
no forcing, DATM, PFT/case changes or Slurm submissions are authorized.

## Stage08f: independent read-only MDS humidity-pair screen

Stage08e completed a SHA256-pinned inventory of all 1,924 residual humidity
blockers. It found both MDS TA and MDS VPD populated at 1,625 native
timestamps, while 299 lacked that pair. This is **availability only**,
not evidence of correct or independent humidity.

[Stage08f](scripts/stage08/08f_audit_mds_humidity_pairs.py) independently
checks physically consistent MDS TA/VPD pairing, the corresponding QC
fields, whether MDS VPD remains valid at retained TA, and numerical
similarity with the original F and ERA companions. It does not modify
forcing, prior trials, DATM, or jobs; a science review is still mandatory.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
  mkdir -p "$BASE/scripts/stage08"
  SCRIPT="$BASE/scripts/stage08/08f_audit_mds_humidity_pairs.py"
  curl -fLsS --retry 3 \
    "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage08/08f_audit_mds_humidity_pairs.py" \
    -o "$SCRIPT"
  "$CONDA_PREFIX/bin/python" -B "$SCRIPT" --check
)
```

After the read-only check, run `"$CONDA_PREFIX/bin/python" -B "$SCRIPT" --run`
for an isolated `reports/stage08f_mds_pairs_...` report. Successful
numerical screens are review cues, **not repair approvals**.

## Stage09a — external dewpoint evidence planning (read-only)

Stage08f finished: 1,535 physically valid MDS TA/VPD pairs (all QC2/3),
421 VPD values valid at retained TA, 90 physically inconsistent pairs
and 299 incomplete pairs. **None are approved substitutes.** The
[Stage09a plan script](scripts/stage09/09a_plan_external_dewpoint_evidence.py)
produces a 7-site/year CDS ERA5-Land hourly dewpoint/temperature/pressure
request manifest based on the 1,924 residual blockers. It also inventories
BIF `UTC_OFFSET` records and labels missing or inconsistent clock metadata
as unresolved, rather than assuming a timezone. It does not submit API
requests, interpolate, or change any forcing or model runs.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage09"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage09/09a_plan_external_dewpoint_evidence.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage09/09a_plan_external_dewpoint_evidence.py" -o "$SCRIPT"
  "$CONDA_PREFIX/bin/python" -B "$SCRIPT" --check
)
```

After successful check, use `"$CONDA_PREFIX/bin/python" -B "$SCRIPT" --run`
to produce an isolated `reports/stage09a_external_dewpoint_plan_...`
containing `era5land_request_plan.json`, `site_utc_offset_inventory.json`
and `request_summary.csv`. External series need actual time alignment
and source-evidence review before any further QCv5 candidate trials.

## Stage09b — one-site/year ERA5-Land pilot, not forcing

Stage09a returned 32 requested site-years spanning 7 sites and 1,924
source-event blockers. BIF UTC offsets are recorded for six stations but
require provenance validation; US-Me2 has no release BIF. The
[Stage09b pilot](scripts/stage09/09b_download_era5land_pilot.py) validates
the pinned Stage09a request receipt and offers one explicit CDS retrieval
(default **US-NR3 2022**) rather than automatically submitting all 32.
The US-NR3 2022 pilot returned 8,904 consecutive hourly observations per variable (2021-12-29 through 2023-01-03) using two date endpoints, so earlier concerns about two isolated dates were disproved. The verified CDS product for point hourly ERA5-Land is
`reanalysis-era5-land-timeseries`. Returned payload can be a NetCDF
or ZIP of NetCDF groups. The pilot preserves the raw response in isolated
`external_evidence/` storage, and SHA256-receipts both request and
response. No data are interpolated, aligned or used for any repair.

On IRIDIS6, first **read-only**:

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  REL='examples/AmeriFlux_MultiSite_10_Batch03'
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  mkdir -p "$BASE/scripts/stage09"
  curl -fLsS --retry 3 "$RAW/$REL/sites.tsv" -o "$BASE/sites.tsv"
  SCRIPT="$BASE/scripts/stage09/09b_download_era5land_pilot.py"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage09/09b_download_era5land_pilot.py" -o "$SCRIPT"
  "$CONDA_PREFIX/bin/python" -B "$SCRIPT" --site US-NR3 --year 2022 --check
)
```

The preflight reports whether `cdsapi` and credentials exist; it does not
print a token or initiate any API calls. Set up a Copernicus CDS account,
accept the dataset licence and configure `~/.cdsapirc` securely on the
cluster prior to explicitly selecting `--run`. Never commit the API token.
After confirming the request format on the live CDS dataset, a single
pilot can be run with `--site US-NR3 --year 2022 --run`. Inspect the
returned raw NetCDF/ZIP and UTC coverage before any expansion to the
remaining 31 requests. Six BIF clock offsets and the US-Me2 fallback
still need verified local-standard-time alignment before joining
downloaded evidence with the site series.

## Stage09c–d: verified US-NR3 2022 pilot and dewpoint evidence

Stage09c confirmed that the downloaded two-member ZIP contains exactly
8,904 hourly UTC values **per variable**, with `t2m`, `d2m`, `sp`,
each covering 2021-12-29 00:00 through 2023-01-03 23:00. The total
17,808 reported across two NetCDF time axes is **not** a count of
independent timestamps. Requested tower coordinates (40.052, −105.5864)
mapped to ERA5-Land grid (40.1, −105.6). The 2022 pilot does **not**
need redownloading. Date endpoints in Stage09a/09b were restored
to the empirically validated `["2021-12-29","2023-01-03"]` form.

The [Stage09d read-only comparison](scripts/stage09/09d_validate_nr3_2022_dewpoint.py)
confirms full unique UTC axes, grid coordinates, units and temperature/
dewpoint/pressure physical ranges and produces a **provisional** comparison
at the US-NR3 2022 blocked native timestamps, using the BIF local
standard UTC−7 offset only as a pending-verification assumption. This
does not authorize any source substitution.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  mkdir -p "$BASE/scripts/stage09"
  SCRIPT="$BASE/scripts/stage09/09d_validate_nr3_2022_dewpoint.py"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage09/09d_validate_nr3_2022_dewpoint.py" -o "$SCRIPT"
  "$CONDA_PREFIX/bin/python" -B "$SCRIPT" --check
)
```

After preflight, `--run` creates isolated diagnostic CSV/JSON
under `reports/stage09d_nr3_2022_dewpoint_...`, leaving the
original ZIP, tower data, candidate forcing, and model cases unchanged.

## Stage09e: external dewpoint at retained tower TA (evidence only)

Stage09d confirmed all **8,904 hourly UTC samples per variable** for
the US-NR3 2022 ERA5-Land pilot. The 295 blocked native records in 2022
have externally derived grid RH **47.10–84.60%** under provisional
UTC−7 alignment. This establishes usable comparison evidence, **not a
validated forcing replacement**.

[Stage09e](scripts/stage09/09e_nr3_dewpoint_tower_consistency.py)
compares two explicitly separate **sensitivities**: (A) external
dewpoint-derived vapor pressure combined with retained tower TA and
pressure; (B) transfer of the external grid RH to tower TA/pressure.
It evaluates relative tower/grid temperatures and pressures, includes
native-interval midpoint timing and ±1-hour time-offset sensitivity,
and reports previously screened MDS alternatives. UTC offset approval
and site/grid elevation differences remain open scientific checks.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  SCRIPT="$BASE/scripts/stage09/09e_nr3_dewpoint_tower_consistency.py"
  mkdir -p "$BASE/scripts/stage09"
  curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage09/09e_nr3_dewpoint_tower_consistency.py" -o "$SCRIPT"
  "$CONDA_PREFIX/bin/python" -B "$SCRIPT" --check
)
```

After preflight `--run` creates an isolated
`reports/stage09e_nr3_2022_tower_dewpoint_...` science-evidence
report, not a revised forcing. **Do not** remove existing
`INCOMPLETE` markers, edit sources, or start DATM/Spin-up.

## Stage09f: checkpointed, capped external dewpoint downloads

Following Stage09e's 295 US-NR3 2022 comparisons, preserve both
humidity-transfer sensitivities as evidence only: absolute vapor pressure
passed 278/295, RH transfer passed 295/295. Neither passes independent
scientific validation or authorizes forcing edits.

[Stage09f](scripts/stage09/09f_incremental_dewpoint_queue.py) audits
all existing ERA5-Land receipts, ZIP CRCs, full hourly UTC time axes,
units, gridded coordinates and T2m/D2m/SP numeric coverage before
choosing at most **three new site-years per invocation**. US-NR3 2022
is reused and not redownloaded. `--check` is strictly read-only;
`--run --max-new 1` downloads just one selected year, with a second
validation afterward. Keep the Stage09b file beside Stage09f.
Missing credentials or absent CDS resources stop execution rather
than bypassing the strict checks.

```bash
(
  set -euo pipefail
  conda activate clm_fates_env
  RAW='https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main'
  BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
  mkdir -p "$BASE/scripts/stage09"
  for name in 09b_download_era5land_pilot.py 09f_incremental_dewpoint_queue.py; do
    curl -fLsS --retry 3 "$RAW/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage09/$name" -o "$BASE/scripts/stage09/$name"
  done
  "$CONDA_PREFIX/bin/python" -B "$BASE/scripts/stage09/09f_incremental_dewpoint_queue.py" --check --max-new 1
)
```

The next optional command is `--run --max-new 1` (not automatic).
This does not approve UTC conversion, site-elevation adjustments,
RH or VPD replacement, DATM, or spin-up.

## Stage09g: one-command finish of remaining ERA5-Land evidence

After Stage09f successfully verified **20/32** site-years (1,868/1,924
blocked native timestamps covered by external evidence), the
[Stage09g runner](scripts/stage09/09g_download_all_remaining.py)
can finish **all 12 remaining** without repeated manual submissions.
It invokes the existing pinned Stage09f and Stage09b scripts in
**serial, ≤3-request batches**, re-checks all existing SHA256 receipts,
hourly UTC axes, NetCDF variables and grids before and after each
batch, refuses overwrites, and stops on the first failed download.
It does NOT modify QCv5, DATM, cases, or submit Slurm jobs.

On IRIDIS6, download the three versioned scripts to the established
Stage09 folder (do not `git pull` into a conflicted checkout).
First run `09g_download_all_remaining.py --check` for a
read-only audit, then explicitly run `--run` to finish the
queue. A persistent advisory lock prevents two Stage09g instances
from draining the same queue simultaneously. A failed or interrupted
CDS retrieval may retain a `.download.partial` file, which requires
manual inspection before retry; existing verified ZIP/receipt pairs
are never changed. Successful completion is `VERIFIED=32/32`.

This is **external evidence coverage only**, not scientific acceptance
of replacement RH, QBOT, or forcing. UTC offset and grid/site elevation
checks remain required before Post-v5 and spin-up.

## Next stages and scientific review

Continue from the actual Stage01 inventory, using Batch03-specific manifests
and outputs. Batch02 paths, coordinates, year selections and site-specific
humidity decisions must not be copied as Batch03 evidence.

1. Inspect BIF or official FULLSET metadata, coordinates, height and native
   coverage. Resolve missing US-Me2 metadata explicitly if necessary.
2. Generate isolated reference surfaces and inspect actual landunit/PFT
   fractions; review study inclusion and tower-footprint representation.
3. Audit all native source meteorology, paired ERA support and anomaly
   episodes before choosing repair scope.
4. Build isolated QCv5 candidates with original data, source QC and complete
   modification ledgers preserved.
5. Perform a separate **Post-QCv5** audit: reconcile QBOT and modifications,
   review QC0 changes, RH extremes, TA/PA jumps, ERA differences and hashes.
   Apply only justified site-specific revisions to new candidates and
   complete final acceptance. A numerical pass alone is not acceptance.
6. Establish ZBOT/PFT and forcing-loop settings, then generate DATM and
   prepare spin-up cases after those checks.

Stages00–10d now have repository scripts and operator-reported IRIDIS results. The updated [science status report](docs/SCIENTIFIC_REVIEW_STATUS_2026-10-24.md) supersedes earlier interim progress numbers in this historical README. All remaining 1,924 events require science review, and PFT/forcing/DATM/spin-up approval has not been granted. No forcing cycle, CO2 setting or spin-up length is selected.

## Implementation and validation

Stage00 and Stage01 are Batch02 adaptations with batch identifiers changed;
transfer, extraction and inventory behavior is retained. Source Git blobs:
`ba0f68310dd0f63be2a5f2a6eb67b23d7035cf89` (upload) and
`7942c235b0b2cc35d08284c94352ae5375c99ca1` (extraction).

Local validation passed Bash/Python syntax and isolated integration checks:

- Ten exact mixed ZIP/folder uploads with mock SSH, real local rsync and
  checksums, one master connection and an unchanged identical rerun.
- Conflicting remote ZIP preservation/rejection, missing-source preflight
  before SSH, and disconnection without a replacement connection.
- Ten nested synthetic releases, US-Me2 FULLSET without BIF, native HH/HR
  identity, exact output paths, unchanged packages and identical rerun.
- Read-only audit without writes, conflicting raw CSV preservation/rejection,
  and missing-source preflight without raw output creation.

These mocks and synthetic packages do not access the operator's D drive or
authenticate to IRIDIS. They are historical pre-deployment tests, **not** substitutes for the separately reported live IRIDIS6 Stage00–10d validations.
The [scientific decision ledger](docs/SCIENTIFIC_REVIEW_STATUS_2026-10-24.md) records subsequent operator results, including SHA-pinned reports and outstanding QC/clock/forcing holds.


## Current run status (2026-10-24): Stage09h–10d

The scripts for these additional stages are available in
[stage09](scripts/stage09) and [stage10](scripts/stage10): Stage09h BIF/time-axis
audit, Stage09i temperature-based offset sensitivity, Stage10a solar-radiation
clock cross-check, Stage10b 1,924-event two-transfer humidity sensitivity,
Stage10c independent water/ice thermodynamic verification, and Stage10d
SHA-pinned 183-episode manual review prioritization.

**Latest live IRIDIS6 results:** 32/32 ERA5-Land year-site products verified;
7/7 affected towers pass native timestamp checks; 6 published BIF UTC offsets
and US-Me2 UTC−8 hypothetical only; 1,924/1,924 humidity records audited.
Absolute-vapor-pressure transfer passed 1,897/1,924 water-physics screens;
grid-RH transfer passed 1,924/1,924. Stage10c found 27 absolute-transfer
water-physics failures, 170 A and 78 B ice-supersaturation cautions; Stage10d
identified 150 tower/grid temperature-difference cautions, 183 event clusters,
and 31 priority-P0 entries (27 failure events plus four US-Me2 clock holds).
**All repair approvals remain zero.**

Read the [full science and provenance status report](docs/SCIENTIFIC_REVIEW_STATUS_2026-10-24.md)
for exact existing IRIDIS directories, per-site breakdowns, decision gates,
recheck commands, and the distinction between scripts committed on GitHub and
full raw numerical evidence retained on IRIDIS. No new forcing, Post-v5,
DATM/CIME case or Slurm job has been created or approved by these stages.


## Latest observation-provenance audit (Stage10e–10h, 2026-10-24)

See the [Stage10e–10g verified quality evidence ledger](docs/STAGE10E_TO_10G_QC_EVIDENCE_2026-10-24.md) for
89 P0/P1 events in 19 clusters, corrected dual TA+VPD QC0 definitions,
6h/24h/72h/7d observation availability, and annual QC0 coverage.
US-NR3 showed zero source-labeled measured TA_F and VPD_F records in
2017, 2018 and 2023, despite nearly complete numeric meteorology.
The [Stage10h provenance script](scripts/stage10/10h_original_qc_source_provenance.py)
is the historical v1 attempt; it incorrectly required identical whole-file
source/ERA coverage and stopped without reports. The [Stage10h-v2 timestamp-keyed audit](scripts/stage10/10h_v2_timestamp_keyed_qc_provenance.py)
**completed on IRIDIS6**: 1,924/1,924 exact event matches, 1,866 VPD QC2
ERA-downscaled, 58 VPD QC1 gapfilled, zero VPD QC0; 100% of the selected
primary timestamps match the broader companion ERA native timeline.
The [Stage10i source ERA VPD saturation audit](scripts/stage10/10i_source_ERA_vpd_saturation_audit.py)
has since **passed** the actual IRIDIS6 `--check` and `--run`. See the current
Stage10i–j section below. No humidity, time-offset, Post-v5 or spinup approval has been granted.


### Stage10i verified and Stage10j next (2026-10-24)

[Stage10i](scripts/stage10/10i_source_ERA_vpd_saturation_audit.py) passed IRIDIS6
self-test/check/run: 1,924/1,924 event rows had original paired
`VPD_ERA > es_water(TA_ERA)`, corresponding to negative *implied* liquid-water
vapour pressure within the exact-release paired ERA source fields. The largest
site median overage was US-MtB (0.257 hPa); US-NR3 covered 1,484 records.
This **does not** establish that actual atmospheric water vapour pressure
was negative, or identify which upstream ERA/downscaling step is at fault.

[Stage10j — verified on IRIDIS6](scripts/stage10/10j_source_vs_grid_humidity_counterfactuals.py)
compared existing source ERA and ERA5-Land meteorology at the same 1,924 event
identities. A numerical VPD-only swap made implied vapour pressure nonnegative
in 1,922 events (99.90%), versus 188 under a temperature-only swap. The 2
VPD-only exceptions were both US-NR3. The swap is **not** a scientifically
approved correction and does not constitute independent validation.

[Stage10k — VERIFIED on IRIDIS6](scripts/stage10/10k_exception_provenance_science_gate.py)
passed self-test, read-only check and full report generation: the two US-NR3
exceptions are 2018-02-21 09:30/10:00 local native time, source rows
195333 and 195334, both VPD QC2. The audited Stage10j reconciliation remains
1,922/1,924 VPD-only algebraic sign changes and 188/1,924 temperature-only;
**these are not approved forcing replacements**. Full evidence and the formal
[Stage10k scientific decision gate](docs/STAGE10K_SCIENTIFIC_DECISION_GATE_2026-10-24.md)
are recorded with exact IRIDIS report location and proposed source/physics
acceptance criteria.
**All humidity and clock approvals remain zero; no Post-v5 or model runs.**


### Stage11a — VERIFIED scientific review matrix (2026-10-24)

The [Stage11a source-pinned review script](scripts/stage11/11a_science_decision_matrix.py)
uses SHA-receipted Stage10d event flags, Stage10h exact-source QC origins,
Stage10k exception classifications, Stage10g QC-window evidence, and the
Stage07 original input manifest. It **passed IRIDIS6 self-test/check/run**, recording 1,687 evidence-insufficient holds, 233 physical/temperature-conflict holds and 4 US-Me2 clock holds (1,924/1,924).

It is designed to create `1924_source_event_science_review.csv`,
`32_site_year_science_decision_matrix.csv`, and
`10_site_post_v5_readiness.csv` in a new isolated report folder; its
`--self-test` / `--check` modes do not write analysis reports. Event routing
distinguishes US-Me2 clock metadata holds, flagged humidity/temperature
physics conflicts and remaining absence of independent measurement evidence.
All repair/clock/Post-v5 approvals remain **FALSE**. The three Stage07 numeric
candidate sites are **not** Post-v5 certified; the other seven remain blocked.

Do **not** use the Stage11a review route or a source/grid counterfactual
pass percentage to start DATM, modify forcing, or submit a spinup. Scientific
signoff is a separately documented human review decision.

### Stage11b — three numeric candidates, Post-v5 Gate-0 (code committed)

[Stage11b script](scripts/stage11/11b_three_site_postv5_gate0_audit.py)
has **passed IRIDIS6 self-test, check and full report run**. It rechecks
the original SHA-pinned FLUXMET/ERA source and Stage07 `processed_v5` candidates
for **US-MOz, US-Mpj and US-NC2**, including complete NO_LEAP native
time steps, TBOT/QBOT/PSRF/PRECTmms physics and conversions, raw-to-v5
change ledger, changed original QC0 records, manual review and ERA-RH floor
counts. A successful Gate-0 is **numeric/provenance-only**, never official
Post-v5 approval; `--check` writes nothing, `--run` creates one isolated
read-only review report. The Stage07 INCOMPLETE marker is retained, no DATM
or spinup authorised.


### Stage11b verified and Stage11c change-level review (2026-10-24)

The [Stage11b numeric-only Post-v5 Gate-0 audit](scripts/stage11/11b_three_site_postv5_gate0_audit.py)
**passed on IRIDIS6** for US-MOz, US-Mpj and US-NC2. The three candidate
forcing CSVs cover 998,640 NO_LEAP native half-hour records combined, with
105 original-to-candidate variable changes, **6 changes to original QC0 values**,
18 manual-review rows, zero ERA RH clipping/floor records and **38 ERA-source
variable replacements at US-NC2**. The minimum water-relative RH was 2.2064%,
0.4392% and 0.0773% for US-MOz, US-Mpj and US-NC2 respectively. The full
[verified Stage11b scientific evidence record](docs/STAGE11B_GATE0_VERIFIED_2026-10-24.md)
includes exact IRIDIS report locations and outstanding Post-v5 holds.

The next source-event [Stage11c audit script](scripts/stage11/11c_qc0_manual_era_change_review.py)
has now **passed the IRIDIS6 self-test, check and report run**. It
reconciles all 105 source QC/ERA/processed-v5 changes by native source key,
extracts 6 measured-QC0 changes, preserves 18 manual review entries, and
audits RH<1% records. The script is evidence-only, not a repair generator.

**All humidity, clock, PFT/CO2 protocol, Post-v5, DATM and spinup gates remain
unapproved.** No original forcing, processed_v5 data, Stage07 incomplete marker,
CIME case or Slurm job may be changed based on these audit results.


### Stage11c verified and Stage11d evidence packet (2026-10-24)

[Stage11c](scripts/stage11/11c_qc0_manual_era_change_review.py) **passed**
on IRIDIS6 with 105 exact source-to-v5 variable changes, 6 originally
QC0-coded measured air-temperature modifications, 18 manual-review entries
(including 4 without final variable changes), 38 US-NC2
`secondary_era_replacement` variables and 5 preserved RH values
between 0 and 1%. Stage11c reported no originally missing values among
the 105 modified source records; the 38 later ERA-source replacements
therefore require an explicit `event_reason` analysis, not a claim of
original input missingness.

The six modified QC0 values all have
`isolated_spike_ERA_confirmed|short_gap_interpolated` event reason.
[Verified Stage11c data interpretation and event list](docs/STAGE11C_VERIFIED_QC0_MANUAL_REVIEW_2026-10-24.md).

[Stage11d](scripts/stage11/11d_priority_change_context_review.py) has now
**passed IRIDIS6 --self-test, --check and --run**. Its 62 distinct review
cases (US-MOz 1, US-Mpj 6, US-NC2 55) have 558 source-native +/-2h
context records. The 38 US-NC2 VPD source values were original
`VPD_F_QC=1` numerical gapfill values, and all carry reason
`TA_VPD_inconsistent_VPD_only|remaining_gap_filled_ERA` before secondary
ERA replacement. Six source QC0 air-temperature spikes, five RH<1% cases,
and four unchanged manual-review rows remain on science hold. See
[Stage11d verified source evidence](docs/STAGE11D_VERIFIED_PRIORITY_SOURCE_REVIEW_2026-10-24.md).

[Stage11e-v1](scripts/stage11/11e_priority_scientific_triage.py) **failed synthetic self-test before IRIDIS file checks**: a one-event simulation encountered an erroneously hardcoded 62-event join requirement. The historical v1 is preserved for auditing.

[Stage11e-v2 repaired source-physics triage](scripts/stage11/11e_v2_priority_scientific_triage.py)
has **PASSED IRIDIS6 syntax, self-test, read-only check and full audit**
on 2026-10-24, retaining the unchanged production 62-record/source SHA
guard. It confirmed **38/38 original US-NC2 `VPD_F_QC=1` values have
nonpositive paired-source implied vapour pressure** before Stage07's ERA
replacement; six QC0 temperature edits are exactly the average of immediate
30-minute source neighbours, but only US-MOz has both neighbour source QC0.
Five preserved extremely low positive RH records occur at positive air T.
No humidity changes or scientific approvals were made.

The [verified Stage11e outcome and provenance](docs/STAGE11E_VERIFIED_AND_STAGE11F_HUMAN_GATE_2026-10-24.md)
contains station statistics, native timestamps and report location.

[Stage11f unsigned human science review queue](scripts/stage11/11f_human_review_signoff_queue.py)
**PASSED IRIDIS6 self-test, --check and --run** on 2026-10-24.
It reports **62 distinct native event IDs** (US-MOz 1, US-Mpj 6,
US-NC2 55), **six QC0 temperature changes**, **38 US-NC2 originally
VPD QC1 source conflicts in four contiguous episodes (12/7/10/9 native
half-hours)**, **five positive RH <1%**, and four manual-review entries
preserved unchanged. The 62-record unsigned review worksheet and
independent SHA256 receipt are in
`reports/stage11f_human_science_review_20261024T074958Z_6ae6d5d7/`
on IRIDIS6. See [verified Stage11f evidence and human decision protocol]
(docs/STAGE11F_VERIFIED_HUMAN_REVIEW_QUEUE_2026-10-24.md).

Next action is **source-specific human scientific adjudication** using a
separate working copy of the unsigned queue, with documented measurement,
QC and uncertainty evidence. The Stage11f hash-sealed original must not
be edited. All corrections, time offsets, Post-v5/DATM/CIME, PFT/CO2 and
spinup authorizations remain ZERO; Stage07's INCOMPLETE marker remains.


### Stage11f human-directed selection (2026-10-24; NOT a new forcing release)

[User-directed decision ledger](docs/STAGE11F_USER_REVIEW_DECISIONS_2026-10-24.md)
records explicit review intentions for **59 of 62 distinct three-site Stage11f
targets**: keep the six existing Stage07 QC0-temperature interpolation
candidates, select an **ERA5-based candidate** for 49 originally
nonpositive-implied-vapour source humidity records and four additional
positive RH<1% candidates (five RH<1% total, one overlapping the 49).
The user's chosen ERA5 source/product and VPD/RH conversion are **not yet
fully specified**, so this is a requested method, not a replacement
applied on IRIDIS.

Exactly **three original positive-but-near-zero-vapour VPD review events
remain HOLD** for a separate decision: US-Mpj 201410210830, US-NC2
202503220130 and 202503270730 (source-native times).
All Stage11f sealed CSVs and source files remain unchanged; the separate
62-row working copy has not been updated from this GitHub documentation.
No approval to alter Post-v5, DATM, CIME, site PFT, CO2 or spinups.


### Stage11f 62/62 decisions CLOSED — ERA5 validation pending (2026-10-24)

The user explicitly selected to **retain all six already-interpolated
Stage07 source-QC0 TA candidates**, use an **ERA5-based humidity method** for
**53 distinct** source-nonpositive-implied-vapour or candidate water-RH<1%
VPD events, and **retain the existing Stage07 VPD** for the final **three**
original-positive but near-zero-water-vapour events:
US-Mpj 201410210830, US-NC2 202503220130 and 202503270730.
This yields a complete **62/62 user-selected method census**, but is **not**
scientific validation of those selected meteorological values.

[Final human-science decision ledger (Markdown)](docs/STAGE11F_FINAL_62_USER_DECISIONS_AND_ERA5_VALIDATION_2026-10-24.md)
and [machine-readable 62 native event choices (CSV)](docs/STAGE11F_ALL62_USER_DECISIONS_2026-10-24.csv)
are committed. The separate
[Stage11g ERA5 provenance/physical-method feasibility audit](scripts/stage11/11g_user62_ERA5_source_method_audit.py)
has **PASSED IRIDIS6 --self-test, --check and --run** on 2026-10-24.
Of 53 user-directed source-companion ERA humidity events, simply copying
companion `VPD_ERA` at Stage07 site TA passed numeric physics **46/53**,
whereas transferring source-companion ERA **RH** to retained Stage07 site
TA and recomputing VPD/QBOT passed **53/53**. Exact source/native
timestamps, three site SHA receipts and all 62 human decisions were
verified. **Independent ERA5-Land data were not evaluated**.

The [Stage11g verified interpretation and Stage11h shadow trial protocol](docs/STAGE11G_VERIFIED_AND_STAGE11H_SHADOW_TRIAL_2026-10-24.md)
is now documented. [Stage11h](scripts/stage11/11h_isolated_ERA_RH_three_site_science_trial.py)
**PASSED IRIDIS6 --self-test, --check and --run** on 2026-10-24.
Its *separate unapproved* shadow research forcing for US-MOz (315,360
half-hours), US-Mpj (315,360) and US-NC2 (367,920) retained 6 Stage07
TA and 3 Stage07 VPD decisions, and reconstructed paired-source ERA5 RH
at 53 selected VPD/QBOT event timestamps. Exactly **43 VPD values
actually differed** from Stage07 (US-MOz 0, US-Mpj 2, US-NC2 41).
Maximum original-to-shadow VPD changes were 0, 2.286140 and 9.761132
hPa. Minimum shadow RH was 2.206422%, 1.168592% and 1.439602%.
This is a science shadow trial, **not** a Post-v5 approved forcing.

Stage11h's new files and SHA receipt are under
`science_trials/stage11h_companion_ERA_RH_shadow_20261024T084110Z_78d963bd/`
on IRIDIS6, with its own INCOMPLETE marker retained.

[Stage11i independent 998,640-row shadow impact audit](scripts/stage11/11i_three_site_shadow_impact_audit.py)
**PASSED IRIDIS6 --self-test, --check and --run** on 2026-10-24.
It independently verified 6/53/3 user decisions, the 43 actual VPD/QBOT
changes (US-MOz 0, US-Mpj 2, US-NC2 41), 998,640 NO_LEAP forcing
half-hours, identical non-selected variables/timestamps and physically
consistent humidity/QBOT. Annual mean VPD change was -0.000244 hPa in
US-Mpj 2018 and -0.001140 hPa in US-NC2 2025, but annual metrics alone
cannot validate short-lived source anomalies.

Exactly **four event IDs introduced a >2 hPa adjacent VPD jump relative
to Stage07**, of which **two were >5 hPa**: US-NC2 native
202503231230 (+9.761132 hPa), 202503250900 (+8.227839 hPa),
202503181900 (+3.706716 hPa), and US-Mpj 201802021730 (+2.286140 hPa).
These are science review flags, not automatic proof the new humidity
is false. [Verified Stage11i analysis and four-event hold]
(docs/STAGE11I_VERIFIED_FOUR_HUMIDITY_JUMPS_2026-10-24.md).

[Stage11j targeted +/-3h source-context review](scripts/stage11/11j_four_jump_source_context_review.py)
**PASSED IRIDIS6 --self-test, --check and --run** on 2026-10-24.
It SHA-verified original source FLUXMET QC, companion site-downscaled
ERA5 RH, Stage07 and Stage11h across all **52 native half-hour context
records**, centered on four >2hPa introduced-jump events. It wrote only
`reports/stage11j_four_jump_original_ERA_context_20261024T092017Z_5fc4bfd6/`
review outputs with no changes to forcing.

The source contexts expose a scientific **event-mask boundary problem**:
after US-NC2 202503231230 was corrected to ERA RH 47.79%, the original
QC1 13:00-15:00 source humidity still implies ~2-8% water RH while
companion ERA indicates ~42-47%; at US-NC2 202503250900, the original
QC1 adjacent 08:00, 08:30, 09:30 and 10:00 timestamps also imply
~4-9% RH versus companion ERA ~33-64%. Comparing the entire four ±3h
windows yielded **11 additional unmodified source-native VPD records**
with original RH <10%, companion RH >=20% and discrepancy >=20 percentage
points, **plus three original source rows already corrected in Stage07**.
These are science-review candidates, NOT a user-approved expanded ERA
replacement mask. [Verified Stage11j four-event context](docs/STAGE11J_VERIFIED_FOUR_EVENT_CONTEXT_AND_UNREPAIRED_NEIGHBOURS_2026-10-24.md).

[Stage11k v1 read-only source-neighbour RH screening](scripts/stage11/11k_four_event_unrepaired_neighbour_RH_review.py)
passed Python syntax and self-test on IRIDIS6, but **STOPPED safely during
--check** on 2026-10-24: v1 incorrectly assumed 18 source-discrepancy
records instead of **25**. No --run, forcing write or model job occurred.
In fact the source-native ±3h contexts identify **11** original-VPD
neighbours still unchanged in Stage07/Stage11h, **3** already Stage07-only
corrected neighbours, and **11** Stage11h-changed context records, of
which **4** are the hotspot centres and **7** are additional already
modified source records. The 11 proposed new review targets remain
unchanged as per the verified Stage11j screen. This is only a science
review flag and not an automatic permission to replace RH.

The corrected [Stage11k v2 SHA-protected read-only reconciliation](scripts/stage11/11k_v2_four_event_unrepaired_neighbour_RH_review.py)
**PASSED IRIDIS6 --self-test and --check** on 2026-10-24. It verified
**25/25 source screening records = 11 untouched US-NC2 neighbour points
+ 3 Stage07-only repairs + 7 other Stage11h-changed neighbours + 4
Stage11h-centre points**; no forcing writes were performed.
[Documented historical v1 diagnostic failure and corrected v2 gate]
(docs/STAGE11K_V1_FAILURE_RECONCILED_AND_V2_REVIEW_GATE_2026-10-24.md).

The user then **explicitly approved all 11 remaining US-NC2 neighbours**
for companion ERA5 **RH-only** reconstruction, while **keeping every EC
tower candidate TA_USE/TBOT value unchanged**. The new human decisions
are separately recorded as [eleven SHA-verifiable native event choices]
(docs/STAGE11L_USER_APPROVED_11_US_NC2_NEIGHBOUR_RH_ADDITIONS_2026-10-24.csv).
The original 62-event user ledger remains untouched: **53 old + 11 new
= 64 ERA-RH target half-hours**, plus 6 existing Stage07 TA KEEP events
and 3 existing Stage07 VPD KEEP events.

[Stage11l isolated humidity-only successor]
(scripts/stage11/11l_us_nc2_11_neighbour_humidity_only_shadow.py)
**PASSED IRIDIS6 syntax, --self-test, --check and --run** on
2026-10-24. It SHA-verified the original 62 selections, then rebuilt
humidity for exactly 11 newly approved US-NC2 native half-hours,
achieving **64 ERA-RH target events** (53 earlier + 11 additional);
all **11 new VPD values changed** compared with Stage11h. The entire
367,920 half-hour US-NC2 EC tower air temperature `TA_USE` and `TBOT`
remained UNCHANGED; no ERA temperature was substituted. Only new target
`VPD_USE` and corresponding `QBOT` could change.
One new unapproved US-NC2 full-year shadow file was written to
`science_trials/stage11l_US-NC2_humidity_only_20261024T100319Z_31a4697e/`
on IRIDIS6, with SHA receipts and an INCOMPLETE marker; US-MOz/US-Mpj
remain SHA references to the previous Stage11h shadow.

The main previously introduced transitions improved: US-NC2
2025-03-23 12:30→13:00 now **0.598 hPa** (was 9.761), and
2025-03-25 09:00→09:30 now **2.145 hPa** (was 8.651).
However **four high-VPD boundary transitions remain**: 2025-03-23
08:30→09:00 (9.467 hPa, pre-existing); 2025-03-25 10:00→10:30
(5.859 hPa, +5.808 newly added); 2025-03-18 18:00→18:30
(4.997 hPa, +3.687); 2025-03-23 15:00→15:30
(4.813 hPa, +2.760). DO NOT automatically smooth or extend the mask.
[Verified Stage11l results and four boundary holds]
(docs/STAGE11L_VERIFIED_11_HUMIDITY_ONLY_AND_BOUNDARY_HOLDS_2026-10-24.md).

[Stage11m read-only four-boundary science source audit]
(scripts/stage11/11m_four_stage11l_boundary_source_science_audit.py)
is committed but **not yet executed on IRIDIS6**. It will SHA-verify
Stage11l/Stage11h/Stage07 + original FLUXMET and paired ERA5 source,
then display **40 native half-hour context rows** (±2h around the
four residual boundary transitions) including source QC, original
and ERA RH and Stage07/11h/11l VPD. It only creates optional separate
review reports and cannot modify or approve any forcing.

All original source, Stage07 and Stage11h files and INCOMPLETE markers
remain untouched. Stage11l and all others remain SCIENTIFIC HOLD.
Post-v5, DATM and spinup approvals remain ZERO.

The existing IRIDIS `62_human_review_WORKING_COPY.csv` and SHA-sealed
original Stage11f report have NOT been updated by GitHub commits.
No candidate forcing has been changed, and all Post-v5, DATM,
PFT/CO2 and spinup authorization flags stay at ZERO.

## Stage11M — verified four-boundary science HOLD (2026-10-24)

The operator ran `11m_four_stage11l_boundary_source_science_audit.py` on IRIDIS6 with verified source and Stage11L SHA receipts. `--self-test`, `--check`, and `--run` succeeded. Output: **367,920** US-NC2 NO_LEAP half-hours audited, 11/11 user-selected new Stage11L humidity events preserved, **four residual high-jump boundaries**, **40** exact original/source ERA/Stage07/11H/11L context rows, and **0** new repair approvals. Stage11M wrote **reports only**, not forcing, CIME or model jobs. The exact report directory and per-event evidence are in [Stage11M ledger](docs/STAGE11M_VERIFIED_FOUR_RESIDUAL_BOUNDARY_CONTEXT_2026-10-24.md).

Three boundaries worsened in Stage11L: March 18 18:00→18:30 (+3.687 hPa jump), March 23 15:00→15:30 (+2.760), and March 25 10:00→10:30 (+5.808); March 23 08:30→09:00 was already high in Stage11H (9.467 hPa) and is unchanged. **Do not reverse an ERA-RH selection merely to minimise VPD jumps**; the original source can imply negative actual vapour pressure, and the transitions can cross separate source provenance or QC categories. The 2025-03-25 10:30 right endpoint already has a Stage07 VPD correction and was **not** among the 11 additional Stage11L approved shadow events.

## Stage11N — US-NC2 original BIF clock and independent ERA5-Land availability preflight

[Read-only Stage11N script](scripts/stage11/11n_us_nc2_grid_clock_preflight.py) uses the original 2005–2025 US-NC2 release BIF to enumerate `UTC_OFFSET` and location metadata (including `GROUP_ID`) and confirms all eight exact original boundary endpoint timestamps. It checks whether a preexisting **US-NC2 2025** gridded ERA5-Land T2m/dewpoint/pressure source is present under the previously used external-evidence hierarchy. It **does not** download, assert UTC alignment, interpret a grid file as approved, select a time offset, reconstruct RH or write any data. The earlier Batch03 Stage09 external queue comprised **seven other named stations**, so US-NC2 grid coverage must not be assumed from a 32-site-year download count.

On IRIDIS6:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch03"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage11/11n_us_nc2_grid_clock_preflight.py"
  mkdir -p "$(dirname "$SCRIPT")"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage11/11n_us_nc2_grid_clock_preflight.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" 2>&1 | tee "$HOME/batch03_stage11n_US-NC2_$(date +%Y%m%d_%H%M%S).log"
)
```

If no usable 2025 gridded source is available, the next scientific step is to separately plan a source-verified, timestamp-aligned ERA5-Land/ERA5 point retrieval for US-NC2, not to alter the already-reviewed 11-event Stage11L mask. **No new automatic interpolation**, force balancing, arbitrary RH flooring, or Post-v5/DATM/spinup approval is authorised by Stage11M/N.

## Stage11N VERIFIED / Stage11O targeted external 2025-03 humidity evidence

Stage11N was executed by the operator and **PASS**: original BIF `GROUP_ID=12759` contains site coordinates **35.8030° N, 76.6685° W (signed longitude -76.6685)** and 5 m elevation; `GROUP_ID=12767` contains `UTC_OFFSET=-5`. All four Stage11M source-native boundaries correspond to exactly eight matched source timestamps. The usual 2025 US-NC2 ERA5-Land evidence directory has **no standard pre-existing bundle**. This does not establish that no unrelated or other external files exist. See the [verified Stage11N ledger](docs/STAGE11N_VERIFIED_US_NC2_CLOCK_AND_2025_ERA5LAND_GAP_2026-10-24.md). No clock or boundary repair was approved.

**Stage11O script:** [11o_us_nc2_2025_march_era5land_evidence.py](scripts/stage11/11o_us_nc2_2025_march_era5land_evidence.py). Uses the already-tested Batch03 Stage09b CDS point-timeseries request convention; independently retrieves ERA5-Land hourly *2 m temperature, 2 m dewpoint temperature, surface pressure* at the **original BIF site coordinates**, across UTC `2025-03-16` through `2025-03-27` (288 hours). Nearest-grid selection (0.1°) is verified from response metadata, and complete exact UTC coverage, units K/K/Pa, dewpoint<=T+0.1 K, gross pressure/temperature bounds and SHA256 provenance are checked. It never edits existing source, Stage07, Stage11H/L, repaired forcing, model cases or existing signed ledgers.

On the IRIDIS6 login node:

```bash
(
  set -euo pipefail
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main"
  REL="examples/AmeriFlux_MultiSite_10_Batch03"
  BASE="$HOME/CLM-FATES-single-site-workflows/$REL"
  SCRIPT="$BASE/scripts/stage11/11o_us_nc2_2025_march_era5land_evidence.py"
  mkdir -p "$(dirname "$SCRIPT")"
  curl -fLsS --retry 3 "$RAW/$REL/scripts/stage11/11o_us_nc2_2025_march_era5land_evidence.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --check
  python3 -B "$SCRIPT" --download 2>&1 | tee "$HOME/Batch03_Stage11O_US-NC2_2025March.log"
  python3 -B "$SCRIPT" --audit
)
```

A CDS credential and installed `cdsapi`, `numpy` and `netCDF4` are needed for actual download/audit. The command makes exactly **one** CDS query (the `--check` mode makes none). Do not run `--download` again after successful download; non-overwrite protection intentionally blocks it. If the CDS request fails and leaves a `.download.partial`, inspect it rather than deleting an original or bypassing checks. Report remains **scientific evidence only**: UTC-5 is a published offset but not an automatically approved tower clock shift, and this ERA5-derived data cannot independently prove tower RH truth. A separate future time-offset sensitivity comparison of the four Stage11M VPD discontinuities is required before any new change or Post-v5/DATM/CLM-FATES model approval.


### Stage11m verified and Stage11n sensitivity only (2026-10-24)

Stage11m on IRIDIS6 passed syntax, self-test, check and run. It SHA-verified four residual US-NC2 VPD transitions and 40 original source/companion ERA/Stage07/Stage11h/Stage11l native context rows. Remaining jumps in Stage11l: March 18 18:00-18:30 4.997141 hPa; March 23 08:30-09:00 9.467392 hPa; March 23 15:00-15:30 4.812737 hPa; March 25 10:00-10:30 5.859252 hPa.

[Stage11n](scripts/stage11/11n_seven_candidate_four_boundary_RH_sensitivity_READONLY.py) **PASSED** IRIDIS6 syntax, self-test, read-only check and report run on 2026-10-24. Seven UNAPPROVED source-companion ERA-RH what-if events were compared against Stage11l at retained site TA/TBOT; three of seven were previously Stage07 VPD-amended. Four residual jumps would improve from 4.997/9.467/4.813/5.859 to 2.443/0.851/0.130/1.227 hPa, respectively. However a new large jump MOVES to US-NC2 2025-03-25 10:30→11:00 (0.0515→4.6839 hPa), and 2025-03-18 17:30→18:00 increases 0.796→3.350 hPa. The five March23 source points are provisionally more event-coherent, but **none of the seven is yet user-approved**. Stage11n SHA-sealed READ-ONLY report lives under `reports/stage11n_seven_unapproved_RH_source_what_if_20261024T102858Z_4925810e/` on IRIDIS6.

[Stage11o two shifted-boundary sentinel read-only sensitivity](scripts/stage11/11o_two_shifted_boundary_sentinal_RH_READONLY.py) is committed but **NOT YET RUN ON IRIDIS6**. It compares original seven with two additional *unapproved* adjacent source-native records, US-NC2 202503181730 and 202503251100, across eight scenarios and ten event edges. It only reads Stage11m/11l SHA-locked inputs and optionally writes review reports, never forcing changes. [Stage11n verified report and Stage11o decision gate](docs/STAGE11N_VERIFIED_AND_STAGE11O_SENTINEL_REVIEW_2026-10-24.md). All Stage07/11h/11l incomplete markers remain, with Post-v5/DATM/spinup approvals zero.


### Stage11p: existing SHA-validated ERA5-Land versus nine unapproved US-NC2 RH targets (2026-10-24)

The **external ERA5-Land March 16–27 point-timeseries download is ALREADY PRESENT**, and its IRIDIS6 `--audit` PASSED original file SHA, correct 288 hourly UTC samples, matching original grid (35.8N, -76.7E), Kelvin T2M/D2M and Pa surface pressure physical/metadata tests. **This verifies source structure only**, not the user-tower clock hypothesis or RH repairs.

[Stage11p RH and clock-offset evidence audit](scripts/stage11/11p_us_nc2_era5land_nine_native_RH_offset_compare_READONLY.py) is **committed, NOT yet run on IRIDIS6**. It reuses the existing original CDS artifact without downloading again, SHA-verifies Stage11m 40-row source-native contexts and Stage11o read-only nine-sentinel report, then compares original source RH, paired FLUXNET site-downscaled ERA5 RH, Stage11l current RH, and **ERA5-Land RH computed from hourly T2M/D2M** for native-to-UTC offsets -6, -5, -4. ERA5-Land **hourly T/D2M** are interpolated in time to native half-hours, then RH is reconstructed over water. It reports **9 candidate native timestamps × 3 clock hypotheses = 27** detailed comparisons and **40 context samples × 3 = 120** comparison rows, including tower-versus-ERA5-Land T differences to detect clock/source inconsistencies. It does NOT choose the clock offset, alter EC tower `TA_USE/TBOT`, modify Stage07/Stage11h/Stage11l forcing or approve the nine new RH candidate timestamps. `--check` is strictly read-only; optional `--run` writes only new SHA-sealed **reports**. Existing Stage11l remains INCOMPLETE, Post-v5/DATM/spinup approvals ZERO. ERA5-Land remains ERA5-driven rather than an independent tower observation.


### Stage11p VERIFIED; Stage11q autonomous humidity-only research successor (2026-10-24)

**Stage11p PASSED IRIDIS6 --self-test, --check, --run:** 288 original ERA5-Land UTC hours, 9 native US-NC2 review targets x 3 UTC-offset hypotheses = 27 target RH comparisons, 40 contexts x 3 = 120. The nine-target RH MAE of gridded ERA5-Land vs *paired source-companion ERA* was 11.833/-6, 6.908/-5 and 3.922/-4 percentage points, versus Stage11l trial RH 35.450/36.041/37.162 percentage points. No UTC offset has been approved from this; do not shift tower native time or substitute ERA air temperature. The ERA5-driven gridded product is evidence distinct from the site-downscaled companion but not independent tower observation. SHA-sealed report: `reports/stage11p_us_nc2_era5land_nine_RH_three_offsets_20261024T110530Z_5f148814/` on IRIDIS6.

Responding to the operator's request for autonomous evidence-supported science QC rather than repeated event-by-event questions, the [**Stage11q nine-event US-NC2 evidence-gated research shadow script**](scripts/stage11/11q_auto9_us_nc2_humidity_only_successor.py) **PASSED IRIDIS6 syntax, --self-test, --check and --run on 2026-10-24**. New sealed research-only forcing is at `science_trials/stage11q_US-NC2_auto9_RH_only_20261024T112211Z_cd95c65a/` with exactly 9 new changed VPD/QBOT values, 13/13 affected half-hour boundaries satisfying no new absolute jumps >4 hPa or additive jumps >2 hPa, and all 367,920 preserved EC tower temperatures unchanged. It can create exactly ONE new isolated US-NC2 humidity-only candidate, transferring paired source ERA RH at existing Stage11l EC tower TA/PSRF to 9 precise 2025 native times (2 Mar18; 5 Mar23; 2 Mar25; 3 were already Stage07-modified). Prior 64 ERA-RH trial targets remain intact; resulting research trial would contain 73 in total, of which the extra 9 are automatically evidence-screened, **not individually human-signed and NOT approved for production**. Stage11q checks all source/ERA5-Land SHA evidence again, 367,920-row humidity/QBOT physics, all 13 affected 30-minute edges, all fixed tower temperatures and untouched nontarget values. It will STOP rather than write a candidate if QC fails. No Stage07, Stage11h or Stage11l originals are overwritten. Post-v5, DATM and spinup authorizations remain ZERO. [Stage11p results and Stage11q scientific scope](docs/STAGE11P_VERIFIED_AUTONOMOUS_STAGE11Q_NINE_RH_SHADOW_2026-10-24.md).


**Final verified Stage11q checkpoint:** 64 inherited + 9 automated research-only source-companion ERA-RH target times = **73 candidate targets**, 9 actual new VPD changes, 13 affected boundaries PASS, 0 numerical humidity/QBOT closure errors, US-MOz and US-Mpj remain original SHA-pinned Stage11h site files. This milestone does **NOT** resolve seven other Batch03 site's 1,924 Stage11a science-held RH records. Focus future bulk work on those seven sites, particularly US-NR3 (1,484), US-Kon (229) and US-NR1 (173); never mark a partly verified site Post-v5/DATM/spinup-ready.


### Stage12a — all ten site checkpoint after verified Stage11q (2026-10-24)

[Stage12a batch-wide 10-site scientific gate and seven-site priority code](scripts/stage12/12a_batch03_ten_site_gate_and_seven_blockers.py) **PASSED IRIDIS6 syntax, self-test, --check and --run** on 2026-10-24. SHA-sealed science status report: `reports/stage12a_batch03_post11q_ten_site_status_20261024T114422Z_73dd434c/`. All ten sites remain Post-v5/DATM/spinup HOLD. It SHA-validates the existing 3 numeric research shadows (US-MOz, US-Mpj, US-NC2), rechecks full NO_LEAP US-NC2 fixed TA/TBOT and exactly 9 Stage11q VPD/QBOT changes (73 combined ERA-RH candidate targets), and reloads the previously verified Stage11a source evidence for 7 unresolved stations. The previously source-sealed 1,924 original remaining humidity science holds partition into 1,687 evidence-insufficient, 233 water-physics/temperature-conflict and 4 US-Me2 clock-metadata holds, across 32 affected site-years. Prioritize *bulk* automation by station volume: US-NR3 1,484, US-Kon 229, US-NR1 173, US-MMS 18, US-MtB 15, US-Me2 4 and US-Me6 1. Stage12a --check does not write files; --run creates ONLY an isolated 10/7/32-row status and triage report, without any forcing, PFT/CO2, model or decisions. All 10 remain Post-v5, DATM and spinup HOLD until separate science release.


### Stage12b six-site bulk candidate patches (2026-10-24)

The [Stage12b bulk event-level six-site humidity patch tool](scripts/stage12/12b_bulk_six_site_ERA5Land_RH_patch_candidates.py) **PASSED IRIDIS6 syntax, self-test, --check and --run** on 2026-10-24: 1,687/1,687 source-native low-conflict RH-only candidate patches, ZERO extra numeric holds, and EXACTLY 233 physics/temperature/ice holds + 4 US-Me2 clock holds. It wrote an isolated SHA-receipted event ledger at `science_trials/stage12b_six_site_bulk_gridRH_numeric_patches_20261024T115336Z_baa77893/`; no site forcing was changed. It uses the original SHA-pinned Stage11a and Stage10b/10d source/science evidence and verified Stage12a: **1,687 of 1,924** record-events are lower-conflict, physically screened source-native *research humidity patch candidates* across US-NR3 (1,312), US-Kon (227), US-NR1 (116), US-MMS (17), US-MtB (14), US-Me6 (1). Explicitly **HOLD 233 physical/temperature/ice cases plus four US-Me2 unverified-clock records**. If any of the 1,687 fails re-computation or pressure/QBOT checks, move it to a numeric HOLD (do not force its repair). This script produces SOURCE-NATIVE EVENT PATCH TABLES ONLY and does not yet generate complete site forcing; Stage12c would use the verified patch table to build wholly new isolated site candidates. No tower temperature/time reassignments, source file overwrites, model runs or Post-v5 approvals. [Full Stage12a science partition and Stage12b scope](docs/STAGE12A_VERIFIED_STAGE12B_BULK_RH_PATCH_POLICY_2026-10-24.md).


### Stage12c — six complete native time-axis research-only site drafts (pending IRIDIS6)

The [Stage12c new six-site NO_LEAP chronology builder](scripts/stage12/12c_six_site_full_native_shadow_with_held_gaps.py) **PASSED IRIDIS6 syntax, self-test, --check and --run on 2026-10-24**. Six original native NO_LEAP scientific shadows at `science_trials/stage12c_six_site_noleap_hold_shadows_20261024T120618Z_f369a05e/`, 1687 inherited grid-RH patches, 233 original science physics holds and 8164 EXTRA raw-source humidity gaps. Across these six sites 8398 distinct rows lack at least one forcing field, including seven non-humidity source-gap instances. The Stage12c shadows are NOT model-ready. It rebuilds six unprocessed site *time-indexed* full-year CSV scaffolds from original SHA-protected FLUXMET and paired companion native ERA source, imports exactly 1,687 Stage12b humidity numeric events and applies grid-RH transfer to ORIGINAL site T/pressure only, and leaves 233 unresolved humidity source-physics conflicts as **explicit missing VPD_USE/QBOT**, not a numerical replacement. Any other source gaps are flagged, with provisional native clocks never shifted. The six resulting time-complete files are **NOT model-ready forcing**; keep their INCOMPLETE markers and Post-v5/DATM/spinup holds. [Stage12b scientific result and Stage12c limitations](docs/STAGE12B_VERIFIED_STAGE12C_SIX_SITE_NATIVE_SHADOW_PLAN_2026-10-24.md).


### Stage12d — guarded six-site companion RH-only recovery (pending IRIDIS6)

[Stage12d six-site original-timestamp ERA companion RH recovery](scripts/stage12/12d_native_companion_RH_bulk_gap_rescue.py) **PASSED IRIDIS6 syntax, --self-test, --check, --run on 2026-10-24**. It successfully added **3,792** original native companion ERA-RH numerical research repairs, preserving the original 1,687 gridded RH repairs and 233 physical holds. It left **4,372** other humidity holds, giving 4,606 records with some remaining missing forcing data across six sites. One SHA-sealed research-only successor is at `science_trials/stage12d_six_site_companion_RH_gap_recovery_20261024T121810Z_f1fa4cee/`. No model-ready approval. It SHA-checks Stage12c six site outputs and original FLUXMET / exact native paired ERA sources, then screens the 8164 additional humidity holes with QC1/QC2, physically valid paired ERA humidity, source/site temperature agreement <=5C, freezing/ice and new adjacent VPD jump checks. It preserves 233 originally held science source events as NaN VPD/QBOT, and preserves all TA_USE/TBOT/PSRF/time and earlier repaired values unchanged; QC0 humidity is NEVER auto-replaced. This writes ONLY fresh isolated science-trial shadows after a read-only pass, with remaining holds separately documented. Post-v5, DATM, spinup authorizations ZERO. [Stage12c verified results and Stage12d science scope](docs/STAGE12C_VERIFIED_STAGE12D_FULL_NATIVE_HUMIDITY_RECOVERY_2026-10-24.md).


### Stage12e — existing 32 yearly ERA5-Land source alternative for remaining 4372 gaps (2026-10-24)

[Stage12e six-site verified ERA5-Land gridded RH fallback](scripts/stage12/12e_six_site_independent_ERA5Land_gap_rescue.py) **PASSED IRIDIS6 syntax, --self-test, --check and --run** on 2026-10-24, adding 702 fixed-tower-T/P gridded RH numerical research repairs, preserving 1,687 Stage12b + 3,792 Stage12d and original 233 science holds. The isolated 6-site Stage12e research shadow was SHA-sealed at `science_trials/stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97/`. Exactly 3,670 extra RH holes and 3,904 total site-time rows with any missing remain. It attempts automatic evidence-screened humidity-only repairs on the 4372 remaining Stage12d new RH holes: uses existing SHA-pinned 32 site/year ERA5-Land products from Stage09f/Stage10b, the published native-offset time hypothesis WITHOUT authorising or altering station clocks, the unchanged EC tower TA/PSRF, original VPD QC1/2 and strict T/pressure/ice/boundary checks. It preserves all **233 original science holds**, **1687 old gridded RH patches**, **3792 paired ERA-RH patches**, and all prior Stage07/Stage11 forcing. Output, if checks pass, is a wholly NEW incomplete six-site research shadow, never an approved DATM or spinup input. Source/periods without verified gridded evidence remain held; no extra CDS downloads, no model job. [Stage12d verified results, 4372-category census and Stage12e method](docs/STAGE12D_VERIFIED_AND_STAGE12E_ALTERNATIVE_ERA5LAND_BULK_RECOVERY_2026-10-24.md).


### Stage12f — existing Stage12e 2810 year-source gaps priority evidence download queue

[Stage12f SHA-guarded year-source download queue](scripts/stage12/12f_missing_year_ERA5Land_download_queue.py) **PASSED IRIDIS6 syntax, regression self-test, --check and --download --max-new 3 on 2026-10-25**. Verified 42 original missing site-years / 2810 humidity rows; successfully downloaded 3 US-MtB site-year original ERA5-Land sources: **2024 (408 associated events, 8928 UTC hours), 2022 (328, 8904), 2020 (302, 8928)**, all SHA-receipted in new isolated Stage12f external evidence. **1,038 events now have a new year-specific gridded source; 1,772 across 39 remaining years do not.** No forcing writes, no time-zone approval, no new humidity science approval. Stage12e's 3,670 extra RH holds are precisely **2,810 NO_VERIFIED_ERA5LAND_SOURCE_FOR_SITE_YEAR** (US-MtB 2363; US-Kon 211; US-NR1 135; US-Me6 80; US-MMS 15; US-NR3 6), **791 site/ERA temperature differences >5°C**, **20 subzero water/ice humidity physics conflicts**, and **49 newly excessive VPD boundary jumps**. Stage12f reloads all original SHA source manifests and Stage12e's exactly 2,810 unpaired site-year events, lists verified missing years ranked by event coverage and optionally downloads at most 3 gridded T2M/D2M/SP point-year CDS timeseries per command. It uses existing original Stage09a site coordinates, Stage09b request and Stage10b hourly NetCDF/ZIP checker, NEW external-source-only storage with SHA receipts, NEVER downloads duplicate or overwrites source data and never shifts station clocks, EC TA, VPD/QBOT, or model files. [Stage12e verified results and Stage12f download policy](docs/STAGE12E_VERIFIED_STAGE12F_MISSING_YEAR_DOWNLOAD_GATE_2026-10-24.md). Post-v5/DATM/spinup = ZERO.


### Stage12g — new verified US-MtB year-source gridded RH shadow (pending IRIDIS6)

[Stage12g six-site SHA-protected RH-only new-source successor](scripts/stage12/12g_apply_new_year_ERA5Land_RH_shadow.py) **PASSED IRIDIS6 syntax, self-test, --check and --run**. Although three newly downloaded US-MtB ERA5-Land year sources covered 1,038 previously source-missing RH records, strict EC-tower T/P and physical screens accepted only **3** new research-only RH candidates: **1,031 original tower/ERA5-Land air temperature discrepancies >5°C** and 4 subfreezing ice RH conflicts remain. 1,772 other site-year rows remain without an external source; all six original Stage12g forcing shadows are still INCOMPLETE, with **3,901 rows having some missing forcing variable**. SHA-sealed trial: `science_trials/stage12g_six_site_new_year_gridRH_science_20261024T233640Z_b3d74fae/`. No originals, tower temperature, clock or jobs modified. Rather than downloading all remaining 39 site-year files blindly, it applies the **existing three new US-MtB 2024/2022/2020 ERA5-Land sources** as research humidity candidates ONLY at the 1,038 associated formerly missing-year source-native half-hours. It retains EC tower TA_USE/TBOT, PSRF, calendar timestamps, all existing Stage12b/12d/12e valid RH repairs, and all original 233 scientific hold events. All candidates face original VPD QC1/2, valid gridded temperature/dewpoint/surface pressure, site–grid T diff ≤5°C, ice-phase thermodynamics and added boundary jump ≤4 hPa tests. It may approve **fewer than 1,038** numerical candidates or zero; a source acquisition PASS alone is not a forcing scientific acceptance. Results remain new isolated SHA-receipted six-site NOLEAP **INCOMPLETE** research shadows, not Post-v5/DATM/spinup-ready. [Stage12f downloaded years and Stage12g science plan](docs/STAGE12F_VERIFIED_THREE_YEAR_CDS_AND_STAGE12G_RH_SOURCE_APPLY_2026-10-25.md).


### Stage12h — US-MtB temperature source and timestamp-offset diagnosis (pending IRIDIS6)

Following the Stage12g 3/1038 success, **do not blindly download the remaining US-MtB ERA5-Land years**; the dominant blocker is original tower-versus-gridded air temperature mismatch, not source absence. [Stage12h US-MtB source-native temperature/QC and exploratory clock-offset audit](scripts/stage12/12h_us_mtb_temperature_source_offset_diagnosis_READONLY.py) **PASSED IRIDIS6 source SHA, --self-test, --check, --run** with sealed original report at `reports/stage12h_US-MtB_temperature_and_clock_three_year_diagnostics_20261025T054717Z_58c34b41/`. Source original TA_F_QC=0 for ALL 1038 source-native RH targets. Across whole years 2020/2022/2024 tower TA was ~6.68/6.37/6.54 C colder than raw ERA5-Land grid T2m, versus native paired TA_ERA MAE ~2.80/2.71/2.79 C. On target events average tower minus grid -9.36/-8.70/-8.90 C; best provisional additional +6h time alignment still shows 7.44/7.43/7.62 C event MAE. No clock, measured TA or humidity revised. It rechecks SHA-sealed original three year sources (2020, 2022, 2024), full original FLUXMET tower TA_F/TA_F_QC, original paired native TA_ERA and gridded ERA5-Land T2m. It compares all-year and 1,038 event-only mean/median differences, original source QC, calendar-month structure, plus *13* purely exploratory integer-hour source-grid alignment hypotheses around the published BIF offset. Output is strictly an isolated scientific diagnostic report; no forcing, T, RH, P, source time or model jobs change. The 1,031 T mismatches, 4 ice-phase holds and original 233 physics holds are **still UNAPPROVED**. [Stage12g science results and Stage12h design](docs/STAGE12G_VERIFIED_AND_STAGE12H_US_MTB_TEMPERATURE_DIAGNOSIS_2026-10-25.md).


### Stage12i — Mt Bigelow 2573m site versus ERA5-Land grid pressure/orography diagnosis

AmeriFlux official US-MtB Mt Bigelow site metadata states **32.4160N, -110.7256E, 2573m elevation**. Its measured QC0 tower temperature differs from grid T2m consistently by >6C on annual average over 2020/2022/2024, raising a strong source *grid elevation/terrain representation* hypothesis (not yet proof of a particular issue). The [Stage12i SHA-pinned read-only source pressure and hypsometric grid-height diagnostic](scripts/stage12/12i_us_mtb_pressure_orography_READONLY.py) **PASSED IRIDIS6 --self-test, --check and --run** on 2026-10-25. SEALED report: `reports/stage12i_US-MtB_orography_pressure_20261025T064222Z_2944f5f6/`. Original tower pressure ~74.5kPa and ERA5-Land grid surface pressure ~84.5kPa imply ~1.06km approximate pressure-derived height difference (tower at 2573m, inferred grid proxy ~1510m), across 2020/2022/2024. A *diagnostic-only* 6.5K/km terrain temperature adjustment reduces the 1038 held source event mean abs grid-vs-tower temperature mismatch from ~8.70–9.36°C to ~2.23–2.79°C. No new source tower temperature, T/P/clock/RH/QBOT or forcing was changed. This supports, but does not prove alone, a grid elevation mismatch. It checks original source PA_F vs Stage12e PSRF, native paired PA_ERA, existing gridded ERA5-Land surface_pressure and T2m, and original source-native clock. It evaluates six year/scope median pressure-derived approximate relative height and full-year / 1038-event lapse diagnostic **4/6.5/9 K per km** with 36 monthly evidence rows. This height estimate is a *pressure-based PROXY*, not direct ERA5-Land geopotential/orography. All outputs are an isolated report; original measured TA, site pressure, RH, VPD, QBOT, source offsets, 1031 Stage12g T holds and 233 prior science holds remain unchanged. **No DATM/spinup.** [Stage12h verified results and scientific Stage12i plan](docs/STAGE12H_VERIFIED_US_MTB_HIGH_ELEVATION_STAGE12I_OROGRAPHY_TEST_2026-10-25.md).


### Stage12j — measured VPD QC0 cold-analogue validation before mountain humidity transfer

[Stage12j four-method US-MtB gridded humidity transfer QC0 cross-validation](scripts/stage12/12j_us_mtb_elevation_aware_QC0_humidity_crossvalidation.py) **PASSED IRIDIS6 --self-test, --check and --run on 2026-10-25, but ALL FOUR METHOD SCIENCE GATES FAILED**: best method GRID_RH gives measured-QC0 cold VPD MAE 1.105/0.994/1.139 hPa (2020/2022/2024), nearly zero bias, but 15.31% / 10.31% / 14.80% of valid source-observed QC0 cold analogues have |VPD error|>2hPa versus the PREDECLARED <=10% ceiling. Consequently selected method NONE and **zero new humidity repairs**. All 1,035 previous Stage12g US-MtB T/ice source holds remain untouched, and no original tower measured QC0 was modified. SHA-receipted science-only output: `science_trials/stage12j_US-MtB_QC0_elevation_aware_humidity_trial_20261025T065237Z_699cdb7f/`. It uses SHA-signed Stage12i/12h/12g and original measured site **VPD_F_QC=0 plus TA_F_QC=0** cold (TA<=5°C) to score four alternative hypothetical humidities at unmodified original tower temperature/pressure: grid RH, grid specific humidity, grid absolute vapor pressure, and grid dewpoint shifted by observed grid–tower source air-temperature difference. Only a model with predeclared science validation thresholds passing across *all three* previously downloaded years is even provisionally eligible for an isolated research-only US-MtB humidity shadow on the 1035 remaining (previously 1031 T mismatch + 4 ice) source time records. New adjacent >4hPa VPD jumps rejected; QC0 humidity, all 233 original physical holds, all previously valid VPD/QBOT, T, P, native clock, source releases untouched. No method pass => report/HOLD only. All results INCOMPLETE and not eligible for Post-v5/DATM/spinup. [Stage12i exact results and Stage12j science gates](docs/STAGE12I_VERIFIED_STAGE12J_QC0_HUMIDITY_VALIDATION_2026-10-25.md).


### Stage12k — measured QC0 GRID_RH error tails and analogue support, no new forcing

[Stage12k read-only US-MtB measured QC0 GRID_RH >2hPa error regime and 1035-target analogue diagnostics](scripts/stage12/12k_us_mtb_gridRH_QC0_error_regimes_READONLY.py) **v2 PASSED IRIDIS6 syntax, regression self-test, --check and --run** on 2026-10-25. It now correctly accounts for **1,035/1,035** held source events, including 15 with temperature >5°C. **323** of the 1,035 events lack >=20 measured QC0 cold analogues in their year/month/T bin; 313 contiguous measured QC0 source-error episodes exceed 2 hPa VPD. Original GRID_RH three-year source validation was numerically reproduced; **Stage12j remains FAILED and zero new humidity repairs were authorized**. SHA-sealed report: `reports/stage12k_US-MtB_GRID_RH_QC0_error_regime_20261025T070844Z_8ffe36dc/`. It SHA-verifies original Stage12j no-method science receipt, reproduces the exact prior cold measured-QC0 GRID_RH counts, MAE, bias, and 2hPa-error fractions, and characterizes excess-error episodes by year, calendar month, station air T and measured source VPD. It explicitly checks how many of the original 1,035 US-MtB held target source times have >=20 eligible cold QC0 source analogues in corresponding year/month/temperature bins, without using unobserved target truth or releasing model forcing. Strict no-write check, optional isolated science report; original failed Stage12j acceptance gate, all previous valid forcing and 233 Stage12b physical holds unchanged. No automatic threshold relaxation and Post-v5/DATM/spinup remain ZERO. [Stage12j verified result and Stage12k scope](docs/STAGE12J_VERIFIED_STAGE12K_QC0_GRID_RH_TAIL_ERROR_DIAGNOSIS_2026-10-25.md).


### Stage12l — five-site non-US-MtB ERA5-Land missing-year evidence priority (pending IRIDIS6)

[Stage12l five-site source-year queue](scripts/stage12/12l_five_site_non_MtB_year_source_priority.py) **PASSED IRIDIS6 syntax, self-test, SHA source audit --check and --download --max-new 3 on 2026-10-25**. It verified 3 new US-Kon gridded ERA5-Land years, **2008 (101 RH evidence rows, SHA256 ccffba5c84d9ce738036b29a7e23ed79b0ec55ceb2b2609fa5c6dca7693fbc32), 2011 (51, SHA256 d64de7ac23b11b40bf67485edb7ca3dfaf985fc567cab21110daecd452658cda), 2012 (44, SHA256 6067f72efd4a6499b69639a8fc752f0d01196b7dbb882d8a6f53180b9a9d6bbb)**. Across the five non-MtB sites **196 of original 447 missing-source native RH rows now have yearly external source evidence; 251 across 27 years still lack it**. Existing US-MtB 1035 science holds and rejected GRID_RH method remain held; no additional MtB sources, no forcing/model writes. It SHA-validates Stage12k's failed-QC0-method scientific hold and all original Stage12f/Stage09/Stage10 source receipts; it then **excludes US-MtB entirely** from additional automatic annual external evidence requests and ranks the **447** missing-year source-native records for US-Kon (211), US-NR1 (135), US-Me6 (80), US-MMS (15) and US-NR3 (6) by actual site-year event coverage. `--check` performs source audit and reports a ranked no-write queue, while `--download --max-new 3` invokes exactly the existing pinned Stage12f validated CDS yearly download logic for up to 3 highest-impact non-MtB source years. No input forcing, EC tower T, pressure, time axis, QA holds, Post-v5, DATM or spinup authorization changes. After seeing what new source years pass, the already committed Stage12g can be re-run to build new separate six-site **INCOMPLETE** research shadows; US-MtB prior 1035 held source times remain unchanged. [Stage12k verified findings and non-US-MtB science priority](docs/STAGE12J_VERIFIED_STAGE12K_QC0_GRID_RH_TAIL_ERROR_DIAGNOSIS_2026-10-25.md).


### Re-use original Stage12g after Stage12l US-Kon new source acquisition

**No script rewrite needed:** the [already IRIDIS-verified existing Stage12g script](scripts/stage12/12g_apply_new_year_ERA5Land_RH_shadow.py) dynamically discovers Stage12f SHA-verified new year-site source receipts. After 3 additional US-Kon Stage12l downloads, source evidence now spans **six new year-site sources** (US-MtB 2020/2022/2024 plus US-Kon 2008/2011/2012) and **1,234** original Stage12e missing-year native RH cases. **1,576** original cases still have no newly downloaded year-specific source (1,325 US-MtB, 251 five-other sites). Re-run Stage12g `--check` then `--run` on original SHA-pinned code: source QA will test the 196 new US-Kon native humidity cases under the original site-T, pressure, water/ice RH and boundary gates, and produce a NEW isolated six-site incomplete successor. The former 3 US-MtB accepted research values are included in Stage12g's cumulative `new_ERA5Land_RH_only_research_repairs` number, so the NEW US-Kon count is the site row, or the total minus 3. **Do not interpret source acquisition as actual RH fix.** Do not resume downloading US-MtB years without new scientific validation; do not release Post-v5/DATM/spinup. [Stage12l source receipts and reusable Stage12g operation](docs/STAGE12L_VERIFIED_FIVE_SITE_SOURCES_AND_STAGE12G_RECHECK_2026-10-25.md).


### Stage12g second SUCCESS — 121 new US-Kon original-native RH science repairs

**2026-10-25 08:02 UTC, IRIDIS6 full check and --run VERIFIED:** after Stage12l brought in US-Kon 2008/2011/2012 verified external year sources, the original SHA-pinned Stage12g was re-run unchanged (AST syntax, self-test, --check, --run all PASSED). **121/196 = 61.73% of newly covered US-Kon source-native humidity gaps passed numeric gridRH/QBOT screening** at unchanged original EC tower TA, PSRF, and time. **75** extra US-Kon site-year source events still held: **34** additional >4hPa adjacent VPD jump, **40** source/grid TA discrepancy >5C, **1** original source QC/site TA/P; another **15** US-Kon gaps await missing-year source evidence. Six-site total is now **124** newly source-verified Stage12g research repairs (121 new US-Kon + previously verified 3 US-MtB), **1,234** source-event evidence coverage, **1,576** original no-year-source events and **3,780** site-time rows still missing at least one forcing field. Non-US-MtB: 940 incomplete native time rows; US-MtB: 2,840 incomplete, all prior 1,035 T/ice holds remain sealed. Original 233 immutable physics holds, QC0 observations, Stage12e source and CIME/Slurm remain unchanged. Fresh SHA-sealed **INCOMPLETE** six-site research trial: `science_trials/stage12g_six_site_new_year_gridRH_science_20261025T080248Z_bb717f66/`. **No Post-v5/DATM/spinup approval**.

Next: existing [Stage12l SHA-pinned five-site year priority downloader](scripts/stage12/12l_five_site_non_MtB_year_source_priority.py) automatically skips verified US-Kon years and excludes US-MtB. Its expected next three source years, assuming no other downloads, are **US-Me6 2015 (42), US-Me6 2017 (36), US-NR1 2022 (22)**; run --check to verify, then --download --max-new 3. Subsequent original Stage12g --check and --run will discover the new receipts automatically; do not confuse download coverage with accepted humidity candidates. [Detailed Stage12g second-run science results and exact next-year queue](docs/STAGE12G_SECOND_VERIFIED_US_KON_121_REPAIRS_AND_NEXT_NON_MTB_DOWNLOAD_2026-10-25.md).


### Stage12l second check: 296 of 447 NON-US-MtB missing-source RH events verified

**2026-10-25 user IRIDIS6 Stage12l `--check` PASS:** US-Me6 **2015 (42 source events), 2017 (36)** and US-NR1 **2022 (22)** are already SHA-verified external year sources (100 further source events). Together with three US-Kon years (196), **296/447** original missing-year source RH events across **6** source site-years now have yearly ERA5-Land evidence; **151 source events across 24 unverified year/site combinations** remain. The previous shell's `verified_new_source_events=196` grep gate is obsolete and would stop benignly before downloading. **Do not fetch the already verified source years again.** Immediately re-run the original Git-blob-verified [Stage12g](scripts/stage12/12g_apply_new_year_ERA5Land_RH_shadow.py) `--check` then `--run`; it will discover **9** verified site-year sources across all six trial sites, expected **1,334** original source events covered and **1,476** remaining unverified source-event years, and test the **100** new US-Me6 and US-NR1 native humidity cases. No new source model-ready approval can be claimed until the Stage12g numerical results arrive. US-MtB remains scientifically held. [Full 296-source audit and revised Stage12g next action](docs/STAGE12L_SUBSEQUENT_296_FIVE_SITE_VERIFIED_SOURCES_2026-10-25.md).


### Stage12g nine-source-year SUCCESS — 14 new Me6 RH-only candidates; NR1 still 0

**2026-10-25 08:32 UTC IRIDIS6 SHA-verified Stage12g --check and --run PASS:** nine Stage12f verified site-years supplied **1,334** original missing-year source-native RH records. Stage12g created **138** screened numerical research RH/QBOT patches, including **121 US-Kon**, **3 US-MtB** previously accepted candidates, and **14 NEW US-Me6** patches. US-Me6: 78 newly covered native events, **14 passes, 35 VPD jump >4hPa holds, 29 tower/grid temperature >5C holds**, another 2 events still lack source years. US-NR1 2022: 22 covered events, **zero passes, 19 tower-grid T >5C and 3 VPD jump >4hPa holds**. All 233 original physics holds preserved; original US-MtB QC0 science gate still failed. Six-site year-source-missing events **1,476**, time rows with missing forcing variables **3,766** (926 among five non-MtB sites, 2,840 US-MtB). Output `science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f/` is a new **INCOMPLETE**, SHA-proven science shadow; no original source or model inputs changed, no Post-v5, DATM, spinup approval.

**Pause automatic US-NR1 2001/2021/2018 CDS source downloads** pending root-cause review of 0/22 physically passing. [Stage12m read-only signed US-NR1/US-Me6 temperature and VPD adjacency review](scripts/stage12/12m_us_nr1_me6_T_and_VPD_hold_diagnosis_READONLY.py) is GitHub committed but **not yet tested on IRIDIS6**. It reports exact original 86 T/neighbor-VPD science holds using the existing nine-source-year SHA receipts. No forcing changes, threshold relaxations, new repairs or model submissions. [Detailed Stage12g 9-year science findings and Stage12m diagnostic protocol](docs/STAGE12G_NINE_YEAR_138_REPAIRS_AND_STAGE12M_NON_MTB_HOLD_DIAGNOSIS_2026-10-25.md).


### Stage12m VERIFIED; Stage12n original raw QC and paired TA_ERA forensic diagnosis

**2026-10-25 08:43 UTC IRIDIS6: original Stage12m SHA, --self-test, --check and --run PASSED.** From the nine-source-year Stage12g six-site incomplete trial, source physics HOLD remains **86 / 100 native source events** among US-Me6 (29 site/grid T >5C, 35 VPD jump >4hPa) and US-NR1 (19 T, 3 VPD). Stage12m reproduced all **38** VPD jump rejected candidates with >4hPa disagreement from at least one surviving finite final neighbor, not proof of the original neighbor's sensor QC. Its original source pressure-based site-grid height proxy for the problematic US-NR1 2022 source events is ~**+237m** but site temperature is ~**7.8C colder** than grid. For US-Me6 2015 19 T holds, relative height is approximately **-65m** but site T ~**10.8C colder**; not comparable to the ~1.06km site-grid height mismatch at US-MtB. A simple altitude lapse correction cannot explain the full discrepancy. Source-only report: `reports/stage12m_nonMtB_NRI_Me6_original_T_VPD_HOLD_diagnosis_20261025T084300Z_b0d38d29/`.

[Stage12n raw tower TA_F_QC/VPD_F_QC versus paired TA_ERA and signed Stage12m grid temperature](scripts/stage12/12n_NR1_Me6_original_T_VPD_QC_source_audit_READONLY.py) is committed but **NOT YET run on IRIDIS6**. It verifies original Stage12m/Stage12g SHA receipts, compares all 86 held native events with raw measured tower source and paired ERA station temperature, and audits both adjacent native VPD source QC and existing Stage12e/Stage12g VPD values. Its --check has no writes; --run creates only a new separate provenance-backed science report. **No additional CDS source download, original source QC0/TA/P/native-clock modification, numeric RH approval, threshold relaxation, CIME/DATM/Slurm or spinup.** [Stage12m source diagnostics and Stage12n read-only plan](docs/STAGE12M_VERIFIED_AND_STAGE12N_ORIGINAL_T_VPD_QC_2026-10-25.md).


### Stage12n VERIFIED, Stage12o QC0 temperature episode and QC1 VPD-edge source study

**2026-10-25 08:52 UTC, IRIDIS6 Stage12n original-source SHA, --self-test, --check, and --run PASS.** All **86 original source HOLD native events** at US-Me6 2015/2017 and US-NR1 2022 have original **tower TA_F_QC=0**. For the 48 T discrepancy holds, native paired `TA_ERA` is also warmer than tower measured `TA_F`, with median station-minus-paired-ERA **-9.472C (Me6 2015, N=19)**, **-5.826C (Me6 2017, N=10)**, **-5.563C (NR1 2022, N=19)**. Grid ERA5-Land is not an independent EC instrument and none of this licenses overwriting raw tower observations. For the **38 originally held VPD jumps**, exactly **76 original native adjacent sides** were audited; **71** have original `VPD_F_QC=1`, and only **5** have original `VPD_F_QC=0` (Me6 65/5; NR1 6/0). This raises the need to audit already existing QC1 gap-filled humidity as a boundary comparator, NOT simply discard old VPD or accept new gridded candidate. Exact report `reports/stage12n_NR1_Me6_original_T_VPD_QC_and_companion_TA_ERA_20261025T085220Z_39e37c1b/`. Original 86 science holds and previous 14 numeric Me6 research candidates untouched, no source, forcing or model edits.

[Stage12o immutable source temperature QC0 multi-hour episode versus native TA_ERA and original QC1 VPD neighbor audit](scripts/stage12/12o_NR1_Me6_QC0_cold_episodes_and_QC1_VPD_edges_READONLY.py) is GitHub committed but **NOT yet executed on IRIDIS6**. It verifies Stage12n report/source SHA, counts original source QC0 tower temperature-minus-TA_ERA <=-5C multi-half-hour runs and ±6h context, and compares original QC1 VPD neighbor raw records with Stage12e original prior VPD and final Stage12g values; every original scientific HOLD remains. Source-only --check zero write; --run isolated report only, no model/forcing or thresholds changed. [Stage12n verified findings and Stage12o next protocol](docs/STAGE12N_VERIFIED_AND_STAGE12O_QC0_T_QC1_VPD_EDGES_2026-10-25.md).


### Stage12o VERIFIED — QC0 T episode persistence and QC1 VPD neighbor provenance

**2026-10-25 09:04 UTC IRIDIS6:** Stage12o source-pinned syntax, self-test, --check and --run **PASSED**, with a new isolated SHA-signed report `reports/stage12o_original_QC0_T_episodes_and_QC1_VPD_edges_20261025T090451Z_a15453b8/`. Among original **48 temperature (>5C tower-grid) held event times**, 41 have native source **QC0 tower TA_F <= paired TA_ERA by 5C** and overlap runs of >=4 consecutive original half-hours, with **24** overlapping runs >=12 consecutive half-hours (>=6 hours; event-aligned observations NOT unique episodes). US-Me6 2015 accounts for 18 such long-run event times among 19 T-held cases, QC0 native neighbor T median steps 0.1C/30min. US-NR1 2022 has 16/19 T-held times overlapping runs of >=4 half-hours but none >=12. This makes isolated one-off tower T replacement unscientific; sustained site microclimate/paired source provenance remain unresolved.

For the original **38 VPD neighbor jump held events**, two immediate source neighbors per event yielded **76 sides**, **71 original QC1** versus **5 QC0**; only **39 of 71 QC1** raw `VPD_F` sides numerically match preserved Stage12e VPD. The **32 nonmatching QC1 sides** need finite-vs-missing distinction; they are NOT necessarily errors. Stage12g predeclared 4hPa continuity guard and original 86 holds remain fully intact, no additional accepted VPD repairs, DATM or spinup.

[Stage12p source QC1-VPD neighbor value origin/provenance and three-source hypothetical 4hPa jump comparison](scripts/stage12/12p_NR1_Me6_QC1_neighbor_provenance_at_jump_edges_READONLY.py) has been committed to GitHub but **not yet tested on IRIDIS6**. It reads signed Stage12o/N scientific source receipts and checks exactly 38 original hold IDs/76 neighbor sides, distinguishes both-finite-but-different from only-source and only-Stage12e VPD cases, and records prior candidate-to-RAW/Stage12e/final Stage12g differences as **diagnostics only**. Strict --check no writes; --run only an isolated SHA-receipted report, with original QC0 tower T, QC1 VPD, source clock, Stage12e/g research shadows and 233 protected science holds unmodified. [Detailed Stage12o verification and Stage12p source provenance protocol](docs/STAGE12O_VERIFIED_86_QC0_T_EPISODES_71_QC1_VPD_NEIGHBORS_AND_STAGE12P_2026-10-25.md).


### Stage12p VERIFIED and Stage12q earlier-snapshot source lineage (2026-10-25)

**IRIDIS6 09:19 UTC:** Stage12p original blob, syntax, --self-test, --check and --run passed, signed report: `reports/stage12p_NR1_Me6_QC1_VPD_neighbor_origin_and_jump_sensitivity_20261025T091906Z_d349135a/`. Among 71 original QC1 immediate source neighbor sides (38 jump holds, 76 total sides), 39 raw-VPD/Stage12e agree, **24 differ while both finite** (Me6 22, NR1 2), and **8 original-raw-only finite** (all Me6; Stage12e is missing). Five QC0 sides match. Among 24 both-finite differing sides, 23 hypothetical candidate/raw jumps exceed 4hPa, but only 4 candidate/Stage12e jumps exceed 4hPa. These are references, NOT science approvals. Original 86 science holds and 233 protected physics holds remain unchanged; no Post-v5/DATM/spinup.

[Stage12p verified log and Stage12q protocol](docs/STAGE12P_VERIFIED_QC1_VPD_ORIGINS_AND_STAGE12Q_2026-10-25.md). [Stage12q C/D/E/G native VPD lineage audit](scripts/stage12/12q_NR1_Me6_76_edge_stage12c_d_e_g_VPD_lineage_READONLY.py) is GitHub committed **but not yet verified on IRIDIS6**. It verifies SHA-linked signed C/D/E/G original native files and identifies the actual introduced-or-retained Stage12e reference source; not a forcing repair, source clock correction, or threshold relaxation.

**Stage12q v1 IRIDIS6 first check (2026-10-25):** pinned SHA/syntax and `--self-test` PASS, but `--check` stopped on pandas indicator collision with Stage12p's existing `_merge` provenance column; no science findings or report from v1. [Stage12q v2](scripts/stage12/12q_NR1_Me6_76_edge_stage12c_d_e_g_VPD_lineage_READONLY.py) at commit `7618aa9574c8a46894bbadc163375c683400212d` (Git blob `f4ea423b09c93c38fdec8c9518baa6d97ea9c4fc`) preserves upstream `_merge`, creates/removes a separate transient stage join indicator and includes four-join plus missing-key regression tests. Await IRIDIS6 v2 `--check`/`--run`. All source/model holds unchanged. [Details](docs/STAGE12P_VERIFIED_QC1_VPD_ORIGINS_AND_STAGE12Q_2026-10-25.md).


### Stage12q v2 VERIFIED — 24 Stage12d companion ERA-RH source changes; Stage12r next

**2026-10-25 09:35 UTC verified IRIDIS6:** pinned Stage12q v2 SHA, syntax, self-test, --check and --run passed. New isolated source report: `reports/stage12q_76_original_VPD_edge_CDEG_lineage_20261025T093514Z_044390c3/`. Among 71 original QC1 neighbor sides at the 38 original VPD-jump held times, **24 both-finite source discrepancies arise from Stage12d native companion ERA-RH transfers** (US-Me6 22, US-NR1 2), **39 QC1 source values match Stage12c baseline**, and **8 original raw-finite US-Me6 sides remained Stage12e missing** (Stage12g later has finite VPD at 2 of those 8, not model approval). Five original QC0 sides matched the Stage12c baseline. The 76 sides include 3 repeated neighboring native timestamps; never interpret as 76 independent observations. SHA-sealed original 86 source holds, previous 233 physical holds, T/P/clock/forcing remain unchanged, no Post-v5/DATM/spinup.

[Verified Stage12q science report + Stage12r provenance and physical check](docs/STAGE12Q_VERIFIED_24_STAGE12D_ERA_RH_DIFFERENCES_8_RAW_ONLY_AND_STAGE12R_2026-10-25.md). [New read-only Stage12r native physics/ERA-RH/held-reason audit](scripts/stage12/12r_NR1_Me6_32_QC1_VPD_C_origin_and_D_E_hold_reasons_READONLY.py) is committed but **not yet tested on IRIDIS6**. It checks exact 32 original source QC1 discrepancy sides using Stage07 original SHA-pinned source/ERA companions, Stage12c original temperature/pressure, signed Stage12d candidate and Stage12d/e hold ledgers; no original data or model writes.


### Stage12r VERIFIED — all 32 original QC1 edge VPD values fail same-time Stage12c water saturation; Stage12s source context next

**IRIDIS6 2026-10-25 09:46 UTC:** pinned Stage12r SHA/syntax, --self-test, --check and --run PASS; isolated report `reports/stage12r_32_QC1_native_VPD_source_physics_and_ERA_RH_20261025T094639Z_a770eeb8/`. **32/32** original QC1 neighboring source VPD values exceeded or equaled water saturation `es_water(TA_USE)` in the Stage12c forcing reconstruction (22 US-Me6 Stage12d-adopted, 2 US-NR1 Stage12d-adopted, 8 US-Me6 raw-only). The 24 Stage12d retained values exactly reproduce companion ERA native `TA_ERA/VPD_ERA`-RH transfers at unchanged site T/P; these are numeric research candidates, not independent measured tower humidity. Among the 8 raw-finite-but-final-Stage12e-missing US-Me6 source sides, Stage12d reasons were **4 `COMPANION_ERA_T_MISMATCH_GT5C`** (2 later became Stage12g research-only finite neighbors) and **4 `NEW_EDGE_JUMP_GT4HPA_HOLD`** (none later finite). Stage12e snapshot lacked verified gridded source years for all 8. No original 86 or 233 science holds were released and original source T, P, VPD, clock, forcing, DATM, CIME, Slurm and spinup were unchanged.

[Stage12r verified source science report and Stage12s next plan](docs/STAGE12R_VERIFIED_32_QC1_VPD_SUPERSAT_AND_STAGE12S_CONTEXT_2026-10-25.md). [Stage12s original source ±6h QC0/QC1, VPD physical consistency and companion ERA context](scripts/stage12/12s_NR1_Me6_32_QC1_VPD_six_hour_native_context_READONLY.py) is on GitHub but **not yet verified on IRIDIS6**; source-only no-write --check and isolated report-only --run.


### Stage12s VERIFIED 2026-10-25 18:05 UTC — original QC1 VPD versus QC0 TA + Stage12t year-level audit

Stage12s SHA/syntax, self-test, check and run **PASS** on IRIDIS6 after activating `clm_fates_env`; first `(base)` attempt failed only because NumPy was unavailable. Sealed science-only report: `reports/stage12s_32_QC1_native_VPD_pm6h_source_context_20261025T180547Z_6a9cc5ab/`. All 32 original problematic VPD neighbors are **VPD_F_QC=1 with TA_F_QC=0** and physically invalid `VPD_F>=es_water(original TA_F)`; 800 ±6-hour half-hour rows represent **overlapping** windows, not independent observations. US-Me6: 22 Stage12d-changed sides and 8 still-missing Stage12e reference sides have median **6/25** physically invalid source half-hours per window; original native companion temperature median differences +1.347C and +3.564C, respectively. US-NR1: 2 Stage12d-changed sides have median **22/25** invalid half-hours with NO adjacent original physically valid source QC0 VPD reference in ±6h. Eight Me6 held raw-only sides remain 4 native-companion TA mismatches >5C and 4 new VPD jumps >4hPa. All original 86 plus separate prior 233 scientific HOLDs remain; 0 source/forcing changes, no Post-v5/DATM/spinup. [Stage12s detailed verified log, eight exact timestamps and QC reference limitations](docs/STAGE12S_VERIFIED_32_QC1_VPD_CONTEXT_AND_STAGE12T_FULL_YEAR_2026-10-25.md).

[Stage12t source-native original QC1 VPD annual physics/run audit](scripts/stage12/12t_NR1_Me6_original_VPD_QC1_full_year_episodes_READONLY.py) has been committed to GitHub but **not yet tested on IRIDIS6**. It reports year-wide original VPD QC vs tower T QC physics for US-Me6 2015/2017 and US-NR1 2022, connects all 32 sides to their source-native invalidity run and nearby genuinely valid source QC0 VPD+T anchors within 24h. Strict source SHA verification; no modifications or repairs.


### Stage12t VERIFIED — three-year QC1 VPD physical-conflict episode census; Stage12u pending

**IRIDIS6 2026-10-25 18:13 UTC:** Stage12t pinned Git blob/syntax, `--self-test`, `--check`, and `--run` all PASS, original-source science report: `reports/stage12t_original_VPD_QC1_full_year_physics_episodes_20261025T181302Z_7b987cae/`. Three source-years, 52,560 half-hour records (Me6 2015/2017, NR1 2022): QC1 source VPD `VPD_F >= es_water(TA_F)` at **115/3228 = 3.56%** (Me6 2015), **114/1608 = 7.09%** (Me6 2017), **126/614 = 20.52%** (NR1 2022), **355/5450 = 6.51% overall**; all 355 have source TA_F_QC0. In 45,388 QC0 VPD records there are **zero** such violations. Me6 2015 QC2 has 18/1680 (1.07%) invalid source records. Original QC1 VPD physical-invalid multi-half-hour episodes include NR1 2022 **45 HH=22.5 h** and **30 HH=15 h**, and Me6 2017 **23 HH=11.5 h**, **17 HH=8.5 h**. Original nearby QC0 valid anchors can be checked but not automatically interpolated across multi-hour gapfill conflicts.

**Official FLUXNET data-product meaning matters:** source `VPD_F_QC=0` measured; `=1` good-quality **MDS gapfilled**; `=2` downscaled ERA (see [FLUXNET FULLSET](https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/) and [ONEFlux documentation](https://pmc.ncbi.nlm.nih.gov/articles/PMC7347557/)). Therefore original VPD QC1 is **not** a sensor reading. The 355 QC1 versus measured QC0 T inconsistencies suggest an independent gapfill cross-variable physics problem, **not yet a proven generator/root cause**.

[Stage12t verified complete science report](docs/STAGE12T_VERIFIED_VPD_QC1_YEAR_EPISODES_STAGE12U_MDS_SOURCE_2026-10-25.md). [Stage12u signed MDS source / consolidated VPD and paired ERA-T sensitivity](scripts/stage12/12u_NR1_Me6_QC1_MDS_vs_consolidated_VPD_source_READONLY.py) is committed but **NOT IRIDIS6-tested**. It checks signed Stage12t 355 cases and 32 held-edge sides; detects whether component MDS fields are actually available in the original FLUXMET input, never invents absent columns, and explores physics under two alternative *reference* temperature/VPD sources without approving replacements. All original 86+233 science holds remain, no source/forcing/clock/PFT/DATM/Slurm/spinup modifications.



### Stage12u VERIFIED 2026-10-25 18:35 UTC — source MDS provenance of all 355 impossible QC1 VPD values

**IRIDIS6 Stage12u** pinned Git blob/syntax, --self-test, --check and --run PASS; immutable read-only source lineage report `reports/stage12u_original_MDS_QC1_VPD_cross_temperature_source_20261025T183511Z_57431d0b/`. **All 355/355** physically impossible original source QC1 `VPD_F` records exactly match finite `VPD_F_MDS` in their original signed FLUXMET (Me6 2015 115/115; Me6 2017 114/114; NR1 2022 126/126). All originals contain explicit `VPD_F_MDS`, `VPD_F_MDS_QC`, `TA_F_MDS`, `TA_F_MDS_QC` source fields; standalone measured `VPD` column absent. Alternative same-native-row `TA_ERA` makes only **132/355 (37.2%)** original MDS `VPD_F` values meet basic VPD < saturation physics; **223/355 (62.8%) still fail**. On the other hand native companion `VPD_ERA` passes this basic physics test against untouched tower `TA_F` for **355/355**, but this is **not** evidence of correct replacement or tower observational truth. Among original 32 VPD-jump-neighbor science-held QC1 sides, only 5 original MDS values become physically valid with paired `TA_ERA`; companion `VPD_ERA` is physically valid at the tower `TA_F` for all 32. The original 38 VPD / 48 temperature scientific HOLDs (86) plus separately protected earlier 233 holds remain unchanged; Post-v5/DATM/spinup are NOT approved.

[Detailed original Stage12u verification](docs/STAGE12U_VERIFIED_ALL_355_QC1_BAD_VPD_ARE_MDS_STAGE12V_2026-10-25.md). [Stage12v 355 record MDS VPD vs MDS air T and raw MDS QC values](scripts/stage12/12v_NR1_Me6_MDS_VPD_vs_MDS_T_and_QC_quality_READONLY.py) is GitHub committed, **not yet IRIDIS6 tested**. Test original MDS VPD against the MDS temperature itself, count physics consistency and MDS-vs-measured tower TA offsets, and report MDS quality-score values without conflating them with consolidated `*_F_QC` codes. SHA-sealed inputs, report only, no repairs or models.


### Stage12v VERIFIED 2026-10-25 18:48 UTC — 355 high-confidence MDS VPD remain physically invalid at MDS air temperature

Stage12v pinned SHA/syntax, --self-test, --check and --run **PASS** on IRIDIS6; sealed report: `reports/stage12v_MDS_VPD_temperature_and_QC_source_forensics_20261025T184859Z_bb353075/`. Of the 355 source QC1 VPD values that fail at measured `TA_F` (Me6 2015 115, Me6 2017 114, NR1 2022 126), **0/355 become valid under the paired `TA_F_MDS`**; all 32 preexisting signed held-VPD neighbor sides likewise remain invalid at MDS air T. Measured minus MDS air T has zero median difference in all three years (the output does not give per-row extrema in both directions). All 355 source `VPD_F_MDS_QC` values are exactly **1**, and all 355 `TA_F_MDS_QC` values exactly **0**. FLUXNET [FULLSET definitions](https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/) and [ONEFlux paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7347557/) confirm HH MDS 1=high-confidence gapfill, 0=measured; such a quality code does not ensure cross-variable physical consistency. [Verified Stage12v report](docs/STAGE12V_VERIFIED_MDS_QC1_VPD_PHYSICALLY_IMPOSSIBLE_AT_MDS_T_2026-10-25.md).

[Stage12w original-native ERA-RH science-only diagnostic](scripts/stage12/12w_NR1_Me6_355_MDS_VPD_native_ERA_RH_candidate_screen_READONLY.py) is committed with pinned revision but **NOT YET IRIDIS6 TESTED**. It screens original 355 invalid MDS VPD source timestamps with the companion ERA RH transferred to retained tower QC0 T and Stage12g PSRF; standard water RH/ice phase, `|Ttower-TERA|<=5°C`, QBOT closure and >4 hPa original QC0 and Stage12g immediate neighbor transitions, including explicit missing-neighbor uncertaintly. No forcing or previous source file changes, no original 86+233 science HOLD releases, and no Post-v5/DATM/spinup approval.



### Stage12w VERIFIED 2026-10-25 19:24 UTC — 355 original MDS VPD, 68 G missing & 13 historical finite warning

On IRIDIS6 the Stage12w pinned source SHA/parse, self-test, --check, and --run **all passed**; new SHA-sealed report only at `reports/stage12w_355_original_MDS_VPD_companion_ERA_RH_physics_triage_20261025T192422Z_10358cc7/`. Exactly **355/355** original source QC1 physically impossible MDS VPD have physically acceptable paired ERA-water RH, ice-phase screen, and basic recalculated candidate VPD/QBOT at unchanged original tower T / Stage12g native site P. Under original >5C companion/source T and >4hPa immediate Stage12g or source QC0 neighbor guards, Stage12w hypothetically classifies **275 available-edge diagnostic-pass (NOT APPROVED)**, **44 companion ERA temperature mismatch**, **36 hypothetical candidate jump >4 hPa**. Existing Stage12g has finite values for **287** of these 355 and remains missing at **68**. Of 275 passing this *new hypothetical original companion* diagnostic, 274 Stage12g already finite, **one US-Me6 2017 remains G missing**. Of 80 new-candidate warnings, **13 already have finite Stage12g values**: those earlier finite source values may derive from different sources, are not automatically wrong and must never be overwritten on the basis of a different candidate's warning. Missing 68 split as 32 temperature mismatch, 35 jump, one diagnostic pass but still G missing. All original 86+233 scientific HOLDs and Post-v5/DATM/spinup restrictions unchanged. [Stage12w verified report](docs/STAGE12W_VERIFIED_355_ORIGINAL_MDS_VPD_ERA_RH_TRIAGE_2026-10-25.md).

[Stage12x original source C/D/E/G history reconciliation](scripts/stage12/12x_NR1_Me6_68_missing_13_existing_history_reconciliation_READONLY.py) has been committed with pinned source SHA, **NOT yet executed on IRIDIS6**. It independently checks all G native statuses, first-finite stage, D/E/G original held reasons and prior source candidate logs, separately reports exactly 68 missing and 13 historical finite-but-different-candidate warnings, and prints source-only ±6h context for the sole candidate-pass-but-missing event. No source, historical research forcing, clocks, CIME or model edits.



### Stage12x VERIFIED 2026-10-25 19:35 UTC — 68 immutable missing, 13 first-finite Stage12g alternative-source cautions

**IRIDIS6 Stage12x v2** pinned SHA/AST, self-test, --check and --run PASS; isolated source-only report `reports/stage12x_68missing_13historic_finite_stage12w_cross_candidate_20261025T193514Z_fc1729a4/`. Of the original 355 source QC1 MDS physically impossible VPD values: **68 remain missing in signed Stage12g**, and all 68 retain original Stage12d, Stage12e and Stage12g science hold ledger entries; **13 already-finite Stage12g values warn against a different hypothetical Stage12w original native-companion ERA-RH candidate**, and all 13 were FIRST made finite under Stage12g, not Stage12c/d/e. **One original-native US-Me6 2017-07-04 07:00** has Stage12w trial VPD 5.154795 hPa/QBOT .008275 kg/kg and a local available-edge diagnostic pass, yet Stage12d retained `NEW_EDGE_JUMP_GT4HPA_HOLD` and Stage12g retained `HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA`; all C/D/E/G VPD values are still missing there. Stage12g 06:30 = 3.974495 hPa, next finite 08:00 = 21.391 hPa. This gap from 07:00 to 08:00 is **60min, not one 30min adjacent edge**; the missing intervening 07:30 must be checked explicitly before any continuum claim. The 13 Stage12g first-finite sources may be ERA5-Land gridded, not the same as Stage12w original paired ERA humidity. [Verified Stage12x detailed provenance report](docs/STAGE12X_VERIFIED_68_MISSING_13_EXISTING_AND_JULY04_BRIDGE_2026-10-25.md).

[Stage12y signed first-finite Stage12g grid source / July 04 four-point 30min bridge audit](scripts/stage12/12y_Me6_July04_two_gap_bridge_and_13_G_grid_provenance_READONLY.py) is committed and **NOT YET RUN on IRIDIS6**. It checks all 13 existing first-finite Stage12g candidate rows against SHA-protected original grid-source repair ledger, and all native times 06:30/07:00/07:30/08:00 against original source and hypothetical Stage12w, printing 3 actual 30-minute transitions. No data or forcing writes, no original 86 + separate 233 scientific HOLD releases, no Post-v5/DATM/spinup.



### Stage12aa VERIFIED 2026-10-25 23:05 UTC — original MDS QC1→ERA QC2 border; Stage12ab source-only math next

On IRIDIS6 Stage12aa pinned SHA/syntax, self-test, --check and --run PASS. Signed isolated science report `reports/stage12aa_20170704_original_QC1_QC2_native_ERA_RH_20261025T230548Z_3a2b96b6/`. Original native US-Me6 2017-07-04 06:00–09:00 seven HH source `VPD_F_QC` is five **1 = MDS QC1**, then two **2 = ERA QC2** at 08:30 and 09:00, with tower `TA_F_QC=0`. Original 08:00→08:30 VPD change `21.391→13.204` = **−8.187 hPa/30min**, inherited unchanged as a Stage12g 8.187hPa edge. A hypothetical consistently paired original-native companion ERA water RH at original tower T gives 08:00→08:30 VPD `12.292544→13.827916` = **+1.535372 hPa/30min**, suggesting original high-quality MDS to ERA filling switch as a source-discontinuity hypothesis, not source truth. Over all six candidate half-hours **5/6 ≤4 hPa**; **07:00→07:30 = 4.190815 hPa** remains 0.190815 hPa above original 4hPa candidate-edge guard. Symmetric exact VPD(T,RH) decomposition: **+1.054264 hPa (warming; 25.2%)**, **+3.136551 hPa (paired RH decline; 74.8%)**. RH falls about 17.035 percentage points and original tower temperature rises 2.32°C across that interval; neither independently validates observed humidity. No real source QC0 VPD+T anchors within ±24h. The two 07:00/07:30 original science-held gaps and older 08:00 Stage12g MDS QC1 remain unchanged. All original 86+233 scientific holds protected, production Post-v5/DATM/spinup still rejected. [Stage12aa verified source report](docs/STAGE12AA_VERIFIED_MDS_QC1_ERA_QC2_SOURCE_SWITCH_AND_SINGLE_RESIDUAL_30MIN_JUMP_2026-10-25.md).

[Stage12ab mathematical source-only exact decomposition](scripts/stage12/12ab_Me6_20170704_original_ERA_RH_jump_decomposition_READONLY.py) committed on GitHub but **NOT YET TESTED on IRIDIS6**. SHA-locks Stage12aa/z science receipts and signed seven rows/six edges, recomputes separate symmetric contributions of tower T and original-native companion ERA RH to the lone >4hPa VPD candidate jump. Check writes nothing; run writes only new isolated science report; never changes original source/forcing/clock or releases science holds.


### User-approved targeted direct humidity repair — US-Me6 2017-07-04 06:00–08:00 (five original HH), 2026-10-25

The operator **explicitly APPROVED the final ERA-RH replacement** at original native half-hours 06:00, 06:30, 07:00, 07:30, 08:00 inclusive, with original tower measured QC0 T and site PSRF left untouched. Calculate **both VPD_USE and QBOT** using paired original-native ERA `TA_ERA/VPD_ERA` RH. Exact VPD targets approx **3.205763, 3.974495, 5.154795, 9.345609, 12.292544 hPa**; do NOT change 08:30=13.204 hPa or any other native records. Original Stage12g has 07:00/07:30 missing; these 2 original holds are explicitly released **only** in an independently written user-approved derivative. Operator accepts only the particular 07:00→07:30 **4.190815 hPa** edge as exception to the 4hPa screening guard; other criteria remain unchanged. This is **approved application**, not another unapproved candidate experiment. Original source records, original Stage12g and signed science hold ledgers stay immutable; other 86 event/233 older physics hold protections not generally lifted. Full six-site Batch03, Post-v5, DATM, CIME and spinup remain **NOT approved**. [Signed operator decision and procedure](docs/STAGE12AC_OPERATOR_APPROVED_US_ME6_20170704_0600_0800_DIRECT_ERA_RH_2026-10-25.md); [new scoped script](scripts/stage12/12ac_apply_USER_APPROVED_Me6_20170704_0600_0800_ERA_RH.py), final Git commit `5e1cf77238a3cbc1a21622930f2eb13f7a9ff8c1`. **Script has not yet been executed on IRIDIS6.** `--check` only verifies source and repair, `--apply` creates a separate corrected US-Me6 NOLEAP derivative and immutable SHA manifest without overwriting source or Stage12g.
