# JapanFlux MultiSite 11 — CLM-FATES single-site workflow (new experiment)

> **2026-11-02 ACTUAL Stage05O COMPLETED: provenance-gated 3/5 UTC source lookup for 27 fields / 21 distinct site×half-hours.** JP-Fjy/Khw/Yms original BIF+README +9 local STANDARD time permits derived native−9 UTC labels for independent reference checking. JP-Tef/Tmd original 75-line README explicitly says local SOLAR time despite BIF offset +9, so **18 candidate fields / 14 site×half-hours remain NATIVE-ONLY TIME HOLD**. Both outputs are saved on IRIDIS6 under `$HOME/japanflux_stage05o/run_20261102T020608Z/`. [Actual Stage05O report](docs/STAGE05O_ACTUAL_27_UTC_18_NATIVE_HOLD_STAGE05P_ERA5L_PLAN_20261102.md). [Stage05P bounded independent ERA5-Land hourly REQUEST PLAN only](scripts/stage05/05p_prepare_3site_ERA5Land_hourly_UTC_reference_request_NO_CDS.py) **PUBLISHED, NOT EXECUTED ON IRIDIS**: no CDS API calls until authoritative original site lat/lon, exact UTC hours, and licence/credential readiness are checked. All 45 field candidates /35 site-times remain scientific HOLD, no repairs, no original source or model writes, no Slurm.

> **2026-11-02 ACTUAL Stage05N: ORIGINAL README TIME STANDARD CONFLICT IS REAL.** JP-Tef & JP-Tmd share identical source SHA `17a886f5...`, **75 lines**, original README **line 64 explicitly says `local solar time (without DST)`**, not a missing excerpt. JP-Fjy/Khw/Yms share 85-line README `fe96face...`, line 69 `local standard time (without DST)`. All five original BIF metadata independently say **`UTC_OFFSET=9`** and all units/QC match. Official FLUXNET/ONEFlux processing specifications require local **standard** time without DST, but that conflicts with Tef/Tmd original README and does NOT automatically establish how that release handled timestamps. [Stage05N SHA-authenticated source and cross-standard interpretation](docs/STAGE05N_ACTUAL_SOLAR_VS_STANDARD_README_CONFLICT_STAGE05O_SCOPE_20261102.md). **Stage05L remains 3/5 metadata VERIFIED, 2/5 timebase HOLD.** [Stage05O conservative split](scripts/stage05/05o_scoped_3site_UTC_2site_solar_README_HOLD_NO_ZIP.py) **PUBLISHED, not run on actual operator files**: 27 candidate fields / 21 site-times Fjy/Khw/Yms can have derived UTC lookup; 18 fields / 14 site-times Tef/Tmd remain native-only. No original files/forcing edits, Slurm, repair or AD400.

> **2026-11-02 ACTUAL Stage05M confirms TWO ORIGINAL README RELEASE EDITIONS:** JP-Fjy/Khw/Yms have identical 85-line README SHA `fe96face...` and source line 69 explicitly states local standard time without DST. JP-Tef/Tmd have a DIFFERENT identical 75-line README SHA `17a886f5...`; Stage05K's saved source hints contain **no matched time-phrase**, despite no excerpt truncation. **All five BIF UTC offsets remain +9 and QC/units verify**, but Stage05L remains **3/5, no UTC join** because Tef/Tmd need authoritative time conventions. [Stage05M actual two-source-edition evidence](docs/STAGE05M_ACTUAL_TWO_DIFFERENT_READMES_20261102.md). [Stage05N read full 75-line original README once with saved source SHA checks](scripts/stage05/05n_full_alternate_Tef_Tmd_README_source_SHA_readonly.py) **PUBLISHED, NOT YET RUN**; no met CSV reads or Slurm, no source changes. No blanket time-gate override or 45-HOLD candidate repairs.

> **2026-11-02 ACTUAL Stage05L METADATA GATE: 3/5 VERIFIED, 2/5 original README clock-phrase HOLD.** Five affected JPF sites **all have original BIF `UTC_OFFSET=9`** and passed source-specific variable unit/QC and ERA provenance checks. `JP-Fjy, JP-Khw, JP-Yms` passed the **README local standard time without DST** gate. `JP-Tef, JP-Tmd` hold ONLY because the saved Stage05K README excerpt did **not establish** the required statement, **not because offset/units conflict**. Stage05L deliberately generated **NO 45-row UTC lookup** until original source time provenance is confirmed. [Actual Stage05L 3/5 hold report](docs/STAGE05L_ACTUAL_3_OF_5_METADATA_GATE_TEF_TMD_README_HOLD_20261102.md). [Stage05M JSON-only saved README evidence debugger](scripts/stage05/05m_inspect_saved_stage05k_README_time_hints_NO_ZIP_NO_SLURM.py) **PUBLISHED, NOT YET RUN on IRIDIS**, inspect exact snippets/README SHA before loosening any gate. All 45/35 science candidates remain HOLD, no Slurm, no source edits, no AD400.

> **2026-11-01 ACTUAL Stage05K — JP-Khw native time and units resolved from original BIF/README.** `UTC_OFFSET=9`, `local standard time (without DST)`, `TA_F/TA_ERA=deg C`, `PA_F/PA_ERA=kPa`, `LW_IN_F/LW_IN_ERA=W m-2`, `VPD_F=hPa`; original QC0 measured, QC1 high-quality gapfilled, QC2 downscaled from ERA. The 2005-08-12 03:00 Khw anomaly in source clock maps to **2005-08-11 18:00 UTC**, not 03:00 UTC. [Original source Stage05K evidence](docs/STAGE05K_ACTUAL_KHW_SOURCE_QC_UNITS_UTC_PLUS9_20261101.md). Do **not** extrapolate these source-specific unit/time/QC findings to the other affected four JPF sites without original BIF cross-check. [Stage05L fail-closed five-site original metadata verification plus 45-row UTC mapping](scripts/stage05/05l_five_site_JPF_BIF_units_QC_native_UTC_45_HOLD_NO_ZIP.py) **PUBLISHED, NOT YET EXECUTED ON IRIDIS**; reads derived Stage05K JSONs + Stage05I TSV only, no Slurm/source ZIP and no independent ERA download. All 45 remain HOLD until independently sourced ERA5/ERA5-Land and observations are checked.

> **2026-11-01 ACTUAL Stage05J JP-Khw source-specific QC provenance is now established.** Original `BIFVARINFO_HH` documents `TA_F_QC/SW_IN_F_QC/LW_IN_F_QC/VPD_F_QC/PA_F_QC` as `0=measured, 1=good quality gapfill, 2=downscaled from ERA`, and `*_ERA` as **linearly regressed/downscaled ERA using measured-only site data**, not untouched ECMWF input. `VPD_F` selects MDS if `VPD_F_MDS_QC` is 0/1. Original site timestamp offset and exact BIF unit rows were **not verified by Stage05J printed excerpts**, so remain pending. [Stage05J actual original BIF lines](docs/STAGE05J_ACTUAL_JP_KHW_BIF_QC_DOWNSCALED_ERA_AND_STAGE05K_20261101.md). [Stage05K full small BIFVARINFO_HH fields and site time metadata extractor](scripts/stage05/05k_JPF_exact_BIFVARINFO_units_QC_time_excerpts_READONLY.py) **published, first IRIDIS real source test pending**. Stage05I 45 field/35 unique time HOLD remains unchanged. No original edits, Slurm or approved forcing.

> **2026-11-01 ACTUAL Stage05I: combined 45 unapproved variable-level HOLD candidates at 35 distinct station×native half-hours.** Operator's IRIDIS6 script output `STAGE05I SELF-TEST PASS` and `STAGE05I MERGE SUCCESS`, with PA=27, TA=6, LW_IN=12; affected JP-Fjy 6, JP-Khw 11, JP-Tef 4, JP-Tmd 14, JP-Yms 10. Source ledger remains on IRIDIS6 `$HOME/japanflux_stage05i/run_20261101T065709Z/` and original sources are untouched. The earlier **`sha1sum -c` FAILED line was an assistant-generated false check**, comparing the raw-file SHA1 to Git's blob SHA1. The fallback `git hash-object` check passed; future instructions use only the latter. [Actual Stage05I report](docs/STAGE05I_ACTUAL_45_HOLD_35_SITE_TIMES_20261101.md). **Next Stage05J** [read-only original JPF BIF/README metadata audit](scripts/stage05/05j_original_JPF_BIF_README_metadata_source_QC_time_READONLY.py) is published but NOT yet run on real packages. Check QC / units / original timestamp conventions one site at a time, no Slurm, no source mutation. Model forcing remains blocked on independent ERA and native source verification.

> **2026-11-01 ACTUAL Stage05H: four additional JP-Yms PA_F ~67.794–68.202 kPa, `QC=2`, `F=ERA`, ~69% of local flanking pressure.** They fall next to the same-release ERA5 central `PA_ERA=37.349` kPa defect in **2005-08-12** and **2011-12-17**, matching interpolation-contamination hypotheses. Stage05G had 41 physical field flags / 33 unique site×native half-hours; after four relative PA candidates, **45 review candidate field rows / 35 unique station×half-hours** (two of the four new PA rows overlap already LW-flagged half-hours). Five JPF sites remain affected. [Actual Stage05H and 45/35 decision scope](docs/STAGE05H_ACTUAL_FOUR_YMS_PRESSURE_SHOULDERS_AND_STAGE05I_20261101.md). [Stage05I strict ledger merger](scripts/stage05/05i_merge_41_absolute_plus_4_Yms_PA_shoulder_HOLD_NO_ZIP.py) **published, pending first IRIDIS execution**; one-shot audit-TSV merger with no source ZIP, Slurm, correction, forcing or model submission. Source time/QC provenance and independent ERA validation still required.

> **2026-11-01 ACTUAL Stage05G — 41 nonphysical selected-F field rows, 33 distinct station×native half-hours, five affected JPF stations.** All 41 listed `TA_F`, `PA_F` and `LW_IN_F` rows have `F=embedded ERA` and raw `F_QC=2` at three dates in 2005, 2011 and 2022. [Stage05G complete original-value ledger and source interpretation](docs/STAGE05G_ACTUAL_41_FLAGS_33_SITE_TIMES_AND_BOUNDARY_REVIEW_20261101.md). **Caution:** `PA_F<50 kPa` and `LW_IN_F<50 W m-2` catch definite problems but can miss interpolated half-pressure or extremely low LW shoulder values above these cutoffs. [Stage05H local flank/relative screen](scripts/stage05/05h_PA_LW_event_boundary_relative_screen_NO_ZIP_NO_SLURM.py) **PUBLISHED, NOT EXECUTED**; compare PA/LW using saved Stage05F and Stage05G outputs only, no ZIP and no Slurm, no repair. Standard FLUXNET QC flag definitions (0 measurement, 1 MDS, 2 ERA) documented, exact package BIF still to verify. No scientific approval for correction or AD400.

> **2026-11-01 ACTUAL Stage05F FINAL 8/8 JPF ERA-contamination source-impact audits complete.** Of 150 source ERA5 anomalous station×half-hours, **75 fall inside tower FLUXMET_HH years**; **41 selected-`*_F` field-specific nonphysical flags** (TA 6, PA 23, LW 12) are limited to **5 JPF sites**: JP-Fjy, JP-Khw, JP-Tef, JP-Tmd, JP-Yms. JP-Fhk, JP-Spp and JP-Tak have no selected F threshold flags at these event windows; JP-Api's standalone ERA5 screen had none. Affected F values match corrupted same-release ERA in raw `QC=2` contexts; other `QC=0` F values remain numerically different and do not trigger these thresholds. **41 is NOT 41 unique half-hour timestamps or a complete meteorological QC.** [Actual Stage05F eight-site report](docs/STAGE05F_ACTUAL_FINAL8_SELECTED_FORCING_IMPACT_20261101.md). [Stage05G exact per-event audit ledger](scripts/stage05/05g_aggregate_selected_forcing_source_impact_NO_ZIP_NO_SLURM.py) **PUBLISHED, synthetically tested, NOT YET RUN on operator 8 site JSONs**; use without re-reading ZIPs/Slurm. No accepted repair, forcing or model submission.

> **2026-11-01 ACTUAL Stage05F JP-Khw + JP-Tmd: source-ERA anomalies traced into selected forcing values.** Khw source ERA flag overlaps tower years at **8/20** native half-hours, Tmd **12/20**; selected anomalous `TA_F` **3/3**, `PA_F` **6/9**, `LW_IN_F` **2/2** per site (Khw/Tmd respectively). The remaining affected ERA `TA`/`LW` samples have different, plausible source-selected `*_F` with `QC=0`, but all examined flagged ERA `PA_F` exactly matches defective `PA_ERA` with `QC=2`. [Actual Stage05F detailed facts](docs/STAGE05F_ACTUAL_KHW_TMD_SELECTED_FORCING_IMPACT_20261101.md). Finish remaining six JPF sites serially, no Slurm, no file edits. **No numerical replacements or AD400 science approvals.**

> **2026-11-01 ACTUAL Stage05E FINAL: 9/9 JPF ERA5_HH sources audited and saved JSON reports aggregated.** JP-Api has **0** threshold anomalies; the other **8/9** show exactly five **same-date, same-native-hour recurring source anomalies** (1990-04-03; 1999-01-19; 2005-08-12; 2011-12-17; 2022-04-09), totalling **150 station×half-hour flagged intervals** / **248 field-specific threshold flags** (120 TA, 68 PA, 60 LW). Original JPF release's ERA5 products contain repeated site-specific impossible/extreme values; independently downloaded ECMWF ERA5 **not verified**. [Stage05E actual complete data ledger](docs/STAGE05E_ACTUAL_9_SITE_SHARED_ERA5_ARTIFACT_LEDGER_20261101.md). [Stage05F targeted selected FLUXMET F vs embedded ERA source-impact review](scripts/stage05/05f_source_event_selected_forcing_impact_READONLY.py) **PUBLISHED, NOT YET EXECUTED**; pilot one site, then process each in isolation without Slurm. No original data edits, no approved forcing/model runs.

> **2026-11-01 Stage05E previously encountered a 0-byte JP-Api JSON, but operator recovered it and subsequently posted the verified full 9/9 Stage05E output.** [Recovery incident record](docs/STAGE05E_EMPTY_JSON_FAILURE_AND_SAFE_RECOVERY_20261101.md). 

> **2026-11-01 ACTUAL Stage05D: JP-Fjy, JP-Yms and JP-Tef each have 20 unique flagged ERA5_HH half-hours over full source periods.** All three have identically repeated annual anomaly counts in **1990, 1999, 2005, 2011 and 2022**: each year 3 `TA_ERA` values below −70°C and 2 `LW_IN_ERA` below 50 W/m²; PA flags at least 1 per year. This strongly motivates a shared processing/sentinel forensic; **not a claim about independently obtained ECMWF ERA5**. [Actual Stage05D three-site evidence](docs/STAGE05D_ACTUAL_3_SITE_REPEATED_ERA5_EVENTS_20261101.md). Next finish six remaining JPF standalone ERA5_HH screens **serially, without Slurm**, then run [Stage05E JSON-only summary](scripts/stage05/05e_summarize_ERA5_audits_from_JSON_NO_ZIP_NO_SLURM.py). No original edits, no approved forcing, no AD400.

> **2026-11-01 ACTUAL Stage05C: separate JPF `ERA5_HH` files match the embedded `FLUXMET_HH` `*_ERA` values, including impossible values, on JP-Khw and JP-Tmd (all 7 variables × 8 sampled half-hours per site).** E.g. 2005-08-12 03:00 Khw `TA_ERA=-268.276°C`, Tmd `TA_ERA=-284.222°C`, both `PA_ERA=0 kPa` in both source tables. This confirms the **downloaded JPF release's ERA5-derived companion tables** are affected; **NOT that independently obtained ECMWF ERA5 is affected**. [Actual Stage05C forensic](docs/STAGE05C_ACTUAL_KHW_TMD_RELEASE_ERA5_MATCH_20261101.md). [Stage05D separate ERA5_HH all-years screen](scripts/stage05/05d_scan_separate_ERA5_HH_all_years_READONLY.py) **PUBLISHED / synthetically tested, NOT RUN on real IRIDIS source**. One site at a time, no Slurm. No source edits or approved model forcing.

> **2026-11-01 ACTUAL Stage05B JP-Khw + JP-Tmd: common erroneous embedded ERA signatures and 30-minute interpolation confirmed.** 2005-08-12 03:00 native time: Khw `TA_ERA=TA_F=-268.276°C`, Tmd `-284.222°C`, both `PA_ERA=PA_F=0 kPa` with `_F_QC=2`; exactly interpolated near-neighbor negatives occur around the central cell. Same exact ERA extremes reappear on 2011-12-17 but measured `TA_F_QC=0` and `LW_IN_F_QC=0` protect source-selected tower values; PA remains unphysical. **Do not replace QC0 tower TA/LW with broken ERA, and do not assume `TA_F_MDS` is reliable: Khw's 2005 MDS is ~1°C whereas the unaffected adjacent ERA is ~23°C.** [Full actual Stage05B facts](docs/STAGE05B_ACTUAL_KHW_TMD_SHARED_ERA_ARTIFACTS_20261101.md). Next is [Stage05C same-release ERA5_HH vs FLUXMET ERA comparison](scripts/stage05/05c_compare_embedded_ERA_to_release_ERA5_HH_READONLY.py) — **PUBLISHED, NOT RUN on IRIDIS, no Slurm**. Still no source changes or approved forcing.

> **2026-11-01 ACTUAL Stage05A: timestamp/QC candidate review completed (existing Stage04 JSON, no ZIP re-read).** Five JPF sites show **synchronous 2005-08-12 / 2011-12-17 anomalous pressure, temperature, longwave values**, mostly QC-labelled `2`: investigate shared data processing and same-file `*_ERA` provenance before any edits. JP-Tom and JP-Tgf have RH>100 and negative VPD events requiring linked time-by-time forensic, while minuscule negative precipitation is a roundoff candidate. JP-Tom HR ends at `200301010000` exactly when HH begins (native-clock continuity). [Actual Stage05A event ledger](docs/STAGE05A_ACTUAL_EVENT_TIMES_AND_JPF_STAGE05B_20261101.md). [Stage05B JPF exact-event source vs ERA script](scripts/stage05/05b_JPF_shared_timestamp_source_ERA_QC_READONLY.py) is **PUBLISHED, NOT YET RUN on IRIDIS**; one JPF site per invocation, read-only, **NO Slurm**. Model-forcing/PFT/soil/AD400 still blocked on science review.

> **2026-11-01 ACTUAL Stage04: native time-axis and basic numerical QC 11/11 completed.** All per-source time-axis screens returned zero recorded errors, but JPF contains 41 impossible/suspect source variable occurrences across five sites, and JP-Tom/Tgf have large RH>100% and VPD<0 hPa humidity-screen counts. Their tiny negative precipitation (<1e-9 in magnitude) is a numerical-noise candidate, not substantial negative rain. The nine JPF data streams have no `RH_F` source column, so humidity must be scientifically derived only after provenance/unit verification. [Actual Stage04 findings](docs/STAGE04_ACTUAL_FULL11_NATIVE_TIME_AND_QC_20261101.md). **Next use [Stage05A](scripts/stage05/05a_summarize_existing_stage04_QC_NO_ZIP_NO_SLURM.py) on existing Stage04 JSON, NO ZIP reads, NO Slurm.** No forcing is accepted or changed, and no model job is submitted.

> **2026-11-01 ACTUAL Stage03: 11/11 native schema inventories PASSED (header-only).** The nine nested JPF archives each contain 18 source members including `FLUXMET_HH`, `ERA5_HH`, BIF and metadata. JP-Tom has 50-column hourly 1999–2003 + 50-column half-hourly 2003–2014 tables, JP-Tgf has a 62-column half-hourly 2002–2023 table. [Stage03 actual source schema report](docs/STAGE03_ACTUAL_11_SITE_NATIVE_SCHEMA_AND_STAGE04_20261101.md). Next is [Stage04 read-only full-row native timestamp and source QC screening](scripts/stage04/04_audit_native_timestamps_and_source_QC_READONLY.py), **NOT YET EXECUTED**. No DATM/surface/model/Slurm authorization or source repair.

> **2026-11-01 ACTUAL Stage02 OUTER STRUCTURE 11/11 INVENTORIED.** Nine original `JPF_JP-...zip` downloads are **double-layer ZIPs** (`outer.zip` contains identically named `inner.zip`, `!TOC.csv`, `!LICENCE.pdf`), so Stage01's lack of FLUXMET tags in outer members was expected. JP-Tom has CORE/ALLVARS hourly 1999–2003 + half-hourly 2003–2014; JP-Tgf has half-hourly 2002–2023; both offer separately labelled ERA5 1990–2024. These ranges are release labels, not validated complete forcing years. [Actual Stage02 source evidence](docs/STAGE02_ACTUAL_OUTER_ZIP_AND_STAGE03_PLAN_20261101.md). New [Stage03 read-only in-memory nested-archive inspection](scripts/stage03/03_inspect_nested_release_members_READONLY.py) is published and **synthetically tested**, but not yet run on IRIDIS6. **No real native time series/QC approval, no DATM or CIME jobs.**

> **2026-11-01 ACTUAL Stage00 + Stage01: 11/11 VERIFIED.** User-reported WSL uploads confirmed all eleven original ZIPs with local-to-IRIDIS SHA256 equality, and the IRIDIS Stage01 script inventoried all eleven outer archives. Nine JPF archives have exactly 3 members each with no conventional FLUXMET/ERA/BIF substrings in outer member names; JP-Tom has 29 and JP-Tgf has 27 (both names include ERA5_HH). This is not yet a CRC/scientific-QC/DATM approval. [Exact transfer hashes and evidence](docs/STAGE00_01_VERIFIED_TRANSFER_AND_ZIP_INVENTORY_20261101.md). **Next: inspect true outer member names, signatures and bounded source header previews using [Stage02](scripts/stage02/02_print_outer_members_and_headers_READONLY.py), without extraction or Slurm.**

**Current status (2026-11-02): Stage00–03 original structure; Stage04 native selected QC; Stage05A–05E ERA source forensics; Stage05F 8/8 source impact; Stage05G/H 41+4=45 flagged fields; Stage05I 45 field/35 site×time HOLD; Stage05J/K original BIF units/QC/UTC+9; Stage05L metadata gate 3/5 verified; Stage05M/N original local solar/standard README conflict confirmed; Stage05O 27 field/21 half-hour UTC lookup plus 18 field/14 half-hour native-only HOLD COMPLETED.** Stage05P independent ERA5-Land request plan, site coordinate source validation, Tef/Tmd true clock, independently sourced ECMWF numbers, JP-Tom/Tgf RH/VPD, forcing and model runs remain pending; no approved repairs.

This is a separate JapanFlux cohort following the source-preserving workflow pattern in [AmeriFlux Batch03](../AmeriFlux_MultiSite_10_Batch03/) and [AmeriFlux Batch05](../AmeriFlux_MultiSite_10_Batch05/), NOT a copy of those campaigns' site-specific science decisions.

## 1. Exact local source locations

All paths below are relative to **`D:\Fluxes_Tower_Experiment\`**, using one directory per site. The source manifest is [`sites.tsv`](sites.tsv); `package` stores the **original archive basename without .zip**, or (if ZIP is unavailable) the exact-name extracted folder. Zip files take precedence. Names inside archives must be discovered independently.

| Site | D: site directory | Expected archive (exact filename) | Release-label years |
| --- | --- | --- | --- |
| JP-Api | `JapanFlux\JP-Api` | `JPF_JP-Api_FLUXNET_2000-2022_v1.3_r2.zip` | 2000–2022 |
| JP-Fhk | `JapanFlux\JP-Fhk` | `JPF_JP-Fhk_FLUXNET_2006-2023_v1.3_r1.zip` | 2006–2023 |
| JP-Fjy | `JapanFlux\JP-Fjy` | `JPF_JP-Fjy_FLUXNET_2001-2021_v1.3_r1.zip` | 2001–2021 |
| JP-Khw | `JapanFlux\JP-Khw` | `JPF_JP-Khw_FLUXNET_2000-2021_v1.3_r1.zip` | 2000–2021 |
| JP-Spp | `JapanFlux\JP-Spp` | `JPF_JP-Spp_FLUXNET_2000-2018_v1.3_r1.zip` | 2000–2018 |
| JP-Tak | `JapanFlux\JP-Tak` | `JPF_JP-Tak_FLUXNET_1998-2021_v1.3_r1.zip` | 1998–2021 |
| JP-Tef | `JapanFlux\JP-Tef` | `JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1.zip` | 2001–2023 |
| JP-Tmd | `JapanFlux\JP-Tmd` | `JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1.zip` | 2005–2023 |
| JP-Yms | `JapanFlux\JP-Yms` | `JPF_JP-Yms_FLUXNET_2000-2023_v1.3_r1.zip` | 2000–2023 |
| JP-Tom | `JapanFlux\JP-Tom` | **`A20241210-015v200.zip`** | **UNKNOWN** |
| JP-Tgf | `JapanFlux\JP-Tgf` | **`A20241210-013_2.00_selected.zip`** | **UNKNOWN** |

Release-label years are **not verified actual continuous tower measurement years**; the last two package names have no defensible coverage years until source metadata are inspected. ZIP members need not follow FLUXNET naming.

## 2. Stage00 — upload originals from Windows WSL to IRIDIS6

Run in **Ubuntu/WSL on your own Windows machine**, not in an IRIDIS login shell. The local root `D:\Fluxes_Tower_Experiment\JapanFlux` is usually mounted as `/mnt/d/Fluxes_Tower_Experiment/JapanFlux`. Requires `git`, `ssh`, `rsync`, `sha256sum`, `find`, `awk`, `mktemp` and `head`.

```bash
# In your Windows WSL/Ubuntu terminal
ls -ld /mnt/d/Fluxes_Tower_Experiment/JapanFlux
command -v git ssh rsync sha256sum
git clone --depth 1 https://github.com/lyanyeung/CLM-FATES-single-site-workflows.git \
  "$HOME/CLM-FATES-JapanFlux-upload"
set -o pipefail
bash "$HOME/CLM-FATES-JapanFlux-upload/examples/JapanFlux_MultiSite_11/scripts/stage00/00_upload_japanflux.sh" \
  2>&1 | tee "$HOME/japanflux_stage00_upload.log"
```

If that clone directory already exists, use `git -C "$HOME/CLM-FATES-JapanFlux-upload" pull --ff-only` rather than cloning again.

The script does a **complete local 11/11 preflight before transferring anything**, then uses one SSH master connection, `rsync --ignore-existing` with resumable partial files, and independent **local-versus-remote SHA256** for each ZIP. Exact-name extracted folders are also supported with a checksum dry-run. No existing remote archive is overwritten; a mismatch **stops** for inspection. Original local files are never modified or removed.

Remote location for each site:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<JP-SITE>/forcing/packages/<ORIGINAL_PACKAGE>.zip
```

For example, JP-Api is expected at:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/JP-Api/forcing/packages/JPF_JP-Api_FLUXNET_2000-2022_v1.3_r2.zip
```

Success requires the terminal line **`UPLOAD VERIFIED: 11/11 (JapanFlux)`**. A successful transfer verifies bytes, **not** archive content, source quality or scientific suitability.

## 3. Stage01 — read-only inventory of ZIP members, sample headers and unusual formats

After a verified transfer, log into IRIDIS6 and run:

```bash
set -euo pipefail
DIR="$HOME/japanflux_stage01"
BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/JapanFlux_MultiSite_11"
mkdir -p "$DIR"
curl -fLsS "$BASE/sites.tsv" -o "$DIR/sites.tsv"
curl -fLsS "$BASE/scripts/stage01/01_inspect_japanflux_packages.py" -o "$DIR/inspect.py"
python3 -B "$DIR/inspect.py" --manifest "$DIR/sites.tsv" > "$DIR/inventory.json"
python3 - "$DIR/inventory.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
for s in x["sites"]:
    print(s["site"],s["status"],s.get("kind","?"),
          s.get("members_total","?"),"members",
          "tags="+",".join(s.get("tags_in_member_names",[])))
print("INVENTORIED",x["inventoried_count"],"/11")
PY
```

This inspector **does not extract or write any site dataset**. It inventories member names, suspicious path components and duplicate names, likely FLUXMET/ERA/BIF tags where present, and up to eight data-file first-line previews. Japanese text encoding may differ (`utf-8`, `cp932`, `shift_jis`). `--test-crc` optionally streams full ZIP CRC checks. If a ZIP is not a FLUXNET-formatted source, inventory is still valid, but the forcing converter must be built for that source schema.

Preserve `$HOME/japanflux_stage01/inventory.json` and the Stage00 upload log for the next source-science stage. Do not claim a PASS for all eleven until the operator's actual output is reviewed.

## 4. Remaining scientific stages (not yet authorized/executed)

1. **Stage02: native source audit.** Verify actual in-ZIP files, clock convention (JST versus UTC; timestamp start/end and DST behavior if any), coverage, interval (30-minute/hourly), missing-value codes, duplicate/missing timestamps, units, BIF/tower coordinates and sensor-height metadata. Inspect JP-Tom/JP-Tgf separately; never infer their years or variable names from filename.
2. **Stage03: meteorological provenance and physical QC.** Derive consistent seven-field DATM candidate inputs (`FSDS`, `FLDS`, `TBOT`, `PRECTmms`, `WIND`, `PSRF`, `QBOT`) and `ZBOT`, only when source variables, conversions, observed QC and ERA fallback are justified. Preserve original files and source-mapping/QC decision ledger. No automatic ERA substitutions for unresolved science HOLDs.
3. **Stage04: vegetation/PFT, soil and surface.** Source-specific site PFT hypotheses (including bare ground), soil layers, coordinates and measurement height; validate CTSM/FATES grid and parameter assumptions, not inherited blindly from AmeriFlux or ICOS.
4. **Stage05: prepare and independently audit CIME/DATM inputs** using correct UTC/native chronology and NOLEAP calendar. Only after approval, consider the established 5-year segment / repeated AD400 scheme and separate Normal400. No automatic AD400 submissions from these scripts.

**Safety rules:** no source overwrites; no deletion; no unreviewed meteorological fill; no Slurm submission in Stage00/01. Archive hashes and independent source metadata precede forcing/QC decisions. GitHub contains only scripts, manifest and documentation — **never raw tower ZIPs or generated NetCDF/model outputs**.

## Provenance

- Workflow structure adapted from existing [Batch03 Stage00 uploader](../AmeriFlux_MultiSite_10_Batch03/scripts/stage00/00_upload_ameriflux_batch03.sh) and [Batch05 Stage00 uploader](../AmeriFlux_MultiSite_10_Batch05/scripts/stage00/00_upload_ameriflux_batch05.sh).
- Eleven local archive names and paths provided by the experiment operator on 2026-11-01.
- Actual IRIDIS transfer, contents and meteorological suitability remain **unverified** until operator outputs are supplied.
