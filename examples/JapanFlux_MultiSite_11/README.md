# JapanFlux MultiSite 11 — CLM-FATES single-site workflow (new experiment)

> **2026-11-01 Stage05E aggregation BLOCKED by malformed/empty local JSON.** Operator launched serial Stage05D on remaining six JPF sites but the original Stage05E failed at `json.loads` before cross-site aggregation. The exact bad site file is **not yet identified**, so do not count the six as fully verified 9/9. [Updated Stage05E](scripts/stage05/05e_summarize_ERA5_audits_from_JSON_NO_ZIP_NO_SLURM.py) supports `--check` for per-site valid/empty/invalid filenames; [recovery note](docs/STAGE05E_EMPTY_JSON_FAILURE_AND_SAFE_RECOVERY_20261101.md) explains non-destructive selective redo, **no Slurm and no original source edits**. 

> **2026-11-01 ACTUAL Stage05D: JP-Fjy, JP-Yms and JP-Tef each have 20 unique flagged ERA5_HH half-hours over full source periods.** All three have identically repeated annual anomaly counts in **1990, 1999, 2005, 2011 and 2022**: each year 3 `TA_ERA` values below −70°C and 2 `LW_IN_ERA` below 50 W/m²; PA flags at least 1 per year. This strongly motivates a shared processing/sentinel forensic; **not a claim about independently obtained ECMWF ERA5**. [Actual Stage05D three-site evidence](docs/STAGE05D_ACTUAL_3_SITE_REPEATED_ERA5_EVENTS_20261101.md). Next finish six remaining JPF standalone ERA5_HH screens **serially, without Slurm**, then run [Stage05E JSON-only summary](scripts/stage05/05e_summarize_ERA5_audits_from_JSON_NO_ZIP_NO_SLURM.py). No original edits, no approved forcing, no AD400.

> **2026-11-01 ACTUAL Stage05C: separate JPF `ERA5_HH` files match the embedded `FLUXMET_HH` `*_ERA` values, including impossible values, on JP-Khw and JP-Tmd (all 7 variables × 8 sampled half-hours per site).** E.g. 2005-08-12 03:00 Khw `TA_ERA=-268.276°C`, Tmd `TA_ERA=-284.222°C`, both `PA_ERA=0 kPa` in both source tables. This confirms the **downloaded JPF release's ERA5-derived companion tables** are affected; **NOT that independently obtained ECMWF ERA5 is affected**. [Actual Stage05C forensic](docs/STAGE05C_ACTUAL_KHW_TMD_RELEASE_ERA5_MATCH_20261101.md). [Stage05D separate ERA5_HH all-years screen](scripts/stage05/05d_scan_separate_ERA5_HH_all_years_READONLY.py) **PUBLISHED / synthetically tested, NOT RUN on real IRIDIS source**. One site at a time, no Slurm. No source edits or approved model forcing.

> **2026-11-01 ACTUAL Stage05B JP-Khw + JP-Tmd: common erroneous embedded ERA signatures and 30-minute interpolation confirmed.** 2005-08-12 03:00 native time: Khw `TA_ERA=TA_F=-268.276°C`, Tmd `-284.222°C`, both `PA_ERA=PA_F=0 kPa` with `_F_QC=2`; exactly interpolated near-neighbor negatives occur around the central cell. Same exact ERA extremes reappear on 2011-12-17 but measured `TA_F_QC=0` and `LW_IN_F_QC=0` protect source-selected tower values; PA remains unphysical. **Do not replace QC0 tower TA/LW with broken ERA, and do not assume `TA_F_MDS` is reliable: Khw's 2005 MDS is ~1°C whereas the unaffected adjacent ERA is ~23°C.** [Full actual Stage05B facts](docs/STAGE05B_ACTUAL_KHW_TMD_SHARED_ERA_ARTIFACTS_20261101.md). Next is [Stage05C same-release ERA5_HH vs FLUXMET ERA comparison](scripts/stage05/05c_compare_embedded_ERA_to_release_ERA5_HH_READONLY.py) — **PUBLISHED, NOT RUN on IRIDIS, no Slurm**. Still no source changes or approved forcing.

> **2026-11-01 ACTUAL Stage05A: timestamp/QC candidate review completed (existing Stage04 JSON, no ZIP re-read).** Five JPF sites show **synchronous 2005-08-12 / 2011-12-17 anomalous pressure, temperature, longwave values**, mostly QC-labelled `2`: investigate shared data processing and same-file `*_ERA` provenance before any edits. JP-Tom and JP-Tgf have RH>100 and negative VPD events requiring linked time-by-time forensic, while minuscule negative precipitation is a roundoff candidate. JP-Tom HR ends at `200301010000` exactly when HH begins (native-clock continuity). [Actual Stage05A event ledger](docs/STAGE05A_ACTUAL_EVENT_TIMES_AND_JPF_STAGE05B_20261101.md). [Stage05B JPF exact-event source vs ERA script](scripts/stage05/05b_JPF_shared_timestamp_source_ERA_QC_READONLY.py) is **PUBLISHED, NOT YET RUN on IRIDIS**; one JPF site per invocation, read-only, **NO Slurm**. Model-forcing/PFT/soil/AD400 still blocked on science review.

> **2026-11-01 ACTUAL Stage04: native time-axis and basic numerical QC 11/11 completed.** All per-source time-axis screens returned zero recorded errors, but JPF contains 41 impossible/suspect source variable occurrences across five sites, and JP-Tom/Tgf have large RH>100% and VPD<0 hPa humidity-screen counts. Their tiny negative precipitation (<1e-9 in magnitude) is a numerical-noise candidate, not substantial negative rain. The nine JPF data streams have no `RH_F` source column, so humidity must be scientifically derived only after provenance/unit verification. [Actual Stage04 findings](docs/STAGE04_ACTUAL_FULL11_NATIVE_TIME_AND_QC_20261101.md). **Next use [Stage05A](scripts/stage05/05a_summarize_existing_stage04_QC_NO_ZIP_NO_SLURM.py) on existing Stage04 JSON, NO ZIP reads, NO Slurm.** No forcing is accepted or changed, and no model job is submitted.

> **2026-11-01 ACTUAL Stage03: 11/11 native schema inventories PASSED (header-only).** The nine nested JPF archives each contain 18 source members including `FLUXMET_HH`, `ERA5_HH`, BIF and metadata. JP-Tom has 50-column hourly 1999–2003 + 50-column half-hourly 2003–2014 tables, JP-Tgf has a 62-column half-hourly 2002–2023 table. [Stage03 actual source schema report](docs/STAGE03_ACTUAL_11_SITE_NATIVE_SCHEMA_AND_STAGE04_20261101.md). Next is [Stage04 read-only full-row native timestamp and source QC screening](scripts/stage04/04_audit_native_timestamps_and_source_QC_READONLY.py), **NOT YET EXECUTED**. No DATM/surface/model/Slurm authorization or source repair.

> **2026-11-01 ACTUAL Stage02 OUTER STRUCTURE 11/11 INVENTORIED.** Nine original `JPF_JP-...zip` downloads are **double-layer ZIPs** (`outer.zip` contains identically named `inner.zip`, `!TOC.csv`, `!LICENCE.pdf`), so Stage01's lack of FLUXMET tags in outer members was expected. JP-Tom has CORE/ALLVARS hourly 1999–2003 + half-hourly 2003–2014; JP-Tgf has half-hourly 2002–2023; both offer separately labelled ERA5 1990–2024. These ranges are release labels, not validated complete forcing years. [Actual Stage02 source evidence](docs/STAGE02_ACTUAL_OUTER_ZIP_AND_STAGE03_PLAN_20261101.md). New [Stage03 read-only in-memory nested-archive inspection](scripts/stage03/03_inspect_nested_release_members_READONLY.py) is published and **synthetically tested**, but not yet run on IRIDIS6. **No real native time series/QC approval, no DATM or CIME jobs.**

> **2026-11-01 ACTUAL Stage00 + Stage01: 11/11 VERIFIED.** User-reported WSL uploads confirmed all eleven original ZIPs with local-to-IRIDIS SHA256 equality, and the IRIDIS Stage01 script inventoried all eleven outer archives. Nine JPF archives have exactly 3 members each with no conventional FLUXMET/ERA/BIF substrings in outer member names; JP-Tom has 29 and JP-Tgf has 27 (both names include ERA5_HH). This is not yet a CRC/scientific-QC/DATM approval. [Exact transfer hashes and evidence](docs/STAGE00_01_VERIFIED_TRANSFER_AND_ZIP_INVENTORY_20261101.md). **Next: inspect true outer member names, signatures and bounded source header previews using [Stage02](scripts/stage02/02_print_outer_members_and_headers_READONLY.py), without extraction or Slurm.**

**Current status (2026-11-01): Stage00–03 structural checks, Stage04 full selected native temporal/numeric QC, Stage05A events, Stage05B selected source, Stage05C Khw/Tmd same-release ERA5 check, and Stage05D full ERA5 screens on Fjy/Yms/Tef completed.** Six JPF sites still need Stage05D, then Stage05E aggregation; Tom/Tgf humidity provenance, units/timezones, forcing, PFT/soil and model execution remain pending.

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
