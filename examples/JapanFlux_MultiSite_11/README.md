# JapanFlux MultiSite 11 — CLM-FATES single-site workflow (new experiment)

> **2026-11-01 ACTUAL Stage03: 11/11 native schema inventories PASSED (header-only).** The nine nested JPF archives each contain 18 source members including `FLUXMET_HH`, `ERA5_HH`, BIF and metadata. JP-Tom has 50-column hourly 1999–2003 + 50-column half-hourly 2003–2014 tables, JP-Tgf has a 62-column half-hourly 2002–2023 table. [Stage03 actual source schema report](docs/STAGE03_ACTUAL_11_SITE_NATIVE_SCHEMA_AND_STAGE04_20261101.md). Next is [Stage04 read-only full-row native timestamp and source QC screening](scripts/stage04/04_audit_native_timestamps_and_source_QC_READONLY.py), **NOT YET EXECUTED**. No DATM/surface/model/Slurm authorization or source repair.

> **2026-11-01 ACTUAL Stage02 OUTER STRUCTURE 11/11 INVENTORIED.** Nine original `JPF_JP-...zip` downloads are **double-layer ZIPs** (`outer.zip` contains identically named `inner.zip`, `!TOC.csv`, `!LICENCE.pdf`), so Stage01's lack of FLUXMET tags in outer members was expected. JP-Tom has CORE/ALLVARS hourly 1999–2003 + half-hourly 2003–2014; JP-Tgf has half-hourly 2002–2023; both offer separately labelled ERA5 1990–2024. These ranges are release labels, not validated complete forcing years. [Actual Stage02 source evidence](docs/STAGE02_ACTUAL_OUTER_ZIP_AND_STAGE03_PLAN_20261101.md). New [Stage03 read-only in-memory nested-archive inspection](scripts/stage03/03_inspect_nested_release_members_READONLY.py) is published and **synthetically tested**, but not yet run on IRIDIS6. **No real native time series/QC approval, no DATM or CIME jobs.**

> **2026-11-01 ACTUAL Stage00 + Stage01: 11/11 VERIFIED.** User-reported WSL uploads confirmed all eleven original ZIPs with local-to-IRIDIS SHA256 equality, and the IRIDIS Stage01 script inventoried all eleven outer archives. Nine JPF archives have exactly 3 members each with no conventional FLUXMET/ERA/BIF substrings in outer member names; JP-Tom has 29 and JP-Tgf has 27 (both names include ERA5_HH). This is not yet a CRC/scientific-QC/DATM approval. [Exact transfer hashes and evidence](docs/STAGE00_01_VERIFIED_TRANSFER_AND_ZIP_INVENTORY_20261101.md). **Next: inspect true outer member names, signatures and bounded source header previews using [Stage02](scripts/stage02/02_print_outer_members_and_headers_READONLY.py), without extraction or Slurm.**

**Current status (2026-11-01): Stage00, Stage01, Stage02 and Stage03 initial header/member checks EXECUTED 11/11.** Independent whole-record meteorological QC (Stage04), source-unit/timezone validation, forcing construction, PFT/soil, CIME/Slurm execution all remain pending.

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
