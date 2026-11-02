# JapanFlux Stage05AV — last eight original QC2 fields, final four user-JST-hypothesis candidate CDS site-days

**State 2026-11-02:** Script committed to GitHub; **first real IRIDIS run pending**. This is not a declaration that 45/45 fields have been independently compared, nor does it authorize repairs.

## Established prior results

Operator actually ran Stage05AU **PASS**, independent ERA5-Land CDS `reanalysis-era5-land-timeseries` JP-Tmd candidate UTC 2005-08-11 original tower BIF 42.735911N,141.523147E,117m. Returned ZIP is **1380B**, SHA256 **`cd722e173c24154ccb5d28a632683cb39473389ac163b12439cce8e870721fe6`**, 3 variables `t2m`, `sp`, `strd`, 24 UTC hours each, grid **42.700000000001175N,141.49999999999625E**, source SHA/CSV/CRC/time/units/physics validation PASS. Eight original source-JPF 2005-08-12 QC2 fields compared with 2005-08-11 14:00–22:00 UTC nine-hour nearby independent model grid reference:

- 3× original TA −132.399, −284.222, −132.688 °C vs reference **19.021–20.001 °C**.
- 3× original PA 49.502, 0, 49.506 kPa vs reference **99.658–99.738 kPa**.
- 2× original LW_IN 28.519 W m⁻² vs reference **387.743–400.675 W m⁻²**.
- **8/8 outside** independent reference 9-hour envelope. [Actual Stage05AU source evidence](STAGE05AU_ACTUAL_JP_TMD_20050811_8_QC2_THREE_VARIABLE_CDS_CONTEXT_PASS_20261102.md).

Previously independently reviewed original QC2 source fields: 27 at JP-Fjy/Khw/Yms and two JP-Tef Dec2011 LW fields in Stage05AT. Including the new eight Tmd2005 source fields: **37/45**, **8 remaining**. Previous strong-context evidence class = 22; other 15 of 37 are CONTEXT_ONLY (Yms5, Tef2011 two, Tmd2005 eight).

## Remaining original flagged source fields and exact required independent UTC-day payloads

| Original JPF station/native timestamp | Variable | Original source F=embedded ERA QC2 | Candidate UTC from user-selected JST−9 | Independent request date |
|---|---|---:|---|---|
| JP-Tef 2022-04-09 02:00,02:30 | LW_IN×2 | 26.164 W m⁻² ×2 | 2022-04-08 17:00,17:30 | JP-Tef 2022-04-08, `strd` |
| JP-Tmd 2011-12-17 06:30,07:00,07:30 | PA×3 | 49.448,0,49.514 kPa | 2011-12-16 21:30,22:00,22:30 | JP-Tmd 2011-12-16 **and** 2011-12-17, `sp`, for complete 18:00–02:00 UTC context |
| JP-Tmd 2022-04-09 02:30,03:00,03:30 | PA×3 | 49.616,0,49.579 kPa | 2022-04-08 17:30,18:00,18:30 | JP-Tmd 2022-04-08, `sp` |

Exactly **4** distinct site×UTC day independent CDS payloads, **8** source QC2 variable fields, **26** source-scoped gridded hourly contextual values (Tef2022 8h, Tmd2011 9h, Tmd2022 9h). CDS returns each full 24 UTC-hour day, not just the selected contextual hours.

The original Tef/Tmd 75-line JPF README SHA `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5` explicitly says **local solar time**, despite both original BIF UTC_OFFSET=9 and user-selected **JST_UTC_PLUS9_DIAGNOSTIC_ONLY** interpretation. All derived UTC labels remain hypothesis-scoped, not source-proven. Source 45/45 field science HOLD until scientific repair evaluation and any source time clarification.

## Reproducible Stage05AV plan

[Stage05AV source-locked final four site-day CDS ZIPs and 8 source fields](../scripts/stage05/05av_remaining_4_CDS_days_8_Tef_Tmd_QC2_hourly_CONTEXT_ONLY.py) supports:

- Default no flag: **READONLY PREFLIGHT**; verify actual Stage05AT and AU prior science reports, three existing original ERA5-Land source ZIP SHA256 values, original Stage05AR 7-day BIF coordinates/time/site request manifest and original Stage05AQ source native F=ERA QC2 18-field register; report source ZIP collisions or missing four days.
- `--submit-remaining`: operator explicit permission to retrieve up to four **missing** site×UTC-day independent `reanalysis-era5-land-timeseries` CSV ZIPs **sequentially**. Never erase or overwrite valid prior ZIPs, use existing Stage05AS downloads folder, `.zip.partial` for in-progress, verify CRC/24UTC/variables/grid/physics via pinned original Stage05AS checker. Valid already-downloaded source ZIPs are revalidated and reused; stop on invalid partial and preserve it.
- `--assess`: **NO CDS calls**, strictly requires all four newly verified ZIPs, converts hourly `strd/3600` W m⁻² and `sp/1000` kPa, and compares the **eight** exact original source JPF selected F=ERA QC2 fields to the 8h/9h/9h conservative nearest-grid hourly context. Includes cross-UTC-midnight Tmd2011 on **both** December 16/17 date responses with numerical grid check. Records OUTSIDE status per original field, source QC2, original native/JST candidate UTC, and all 45 science holds. Full coverage **45/45** can only be asserted after a REAL successful `--assess` run.

The 2011 original JPF JP-Tef 2× LW fields, and 2005 Tmd 8× TA/PA/LW fields are already evidenced, **do not re-download**. All 45 original field records remain **scientific HOLD**; independent grid-hourly values are **not** scientifically approved 30-minute tower replacement values and no source ZIP/forcing/model/PFT/Slurm/AD400 changes are made.
