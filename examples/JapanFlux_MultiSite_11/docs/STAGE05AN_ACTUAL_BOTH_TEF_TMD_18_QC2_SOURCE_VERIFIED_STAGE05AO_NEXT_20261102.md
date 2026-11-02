# Stage05AN — actual both JP-Tef/JP-Tmd original JPF HH release source audits PASS, 18/18 fields matched (2026-11-02)

## Direct source verification — actual IRIDIS6 results

The user executed the pinned Stage05AN scanner on **both original JPF nested ZIP releases**. Its read-only scan explicitly matched original source `TIMESTAMP_START/TIMESTAMP_END` and selected `*_F` / same-release `*_ERA` / `*_F_QC=2` at all 18 original Stage05AM flagged field records, without changing any source meteorological data.

| Actual original source ZIP | HH rows streamed | Source flagged QC2 variable records matched | Unique source native half-hours |
|---|---:|---:|---:|
| `JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1` | 403,200 | 4/4 (2011-12-17 LW_IN2, 2022-04-09 LW_IN2) | 4 |
| `JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1` | 333,072 | 14/14 (2005-08-12 LW_IN2/PA3/TA3; 2011-12-17 PA3; 2022-04-09 PA3) | 10 |
| **Total** | **736,272** | **18/18** | **14** |

Both original ZIPs independently revalidated exact original `README.txt` SHA256 `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5`, a different original release edition from the 85-line local-standard README used by JP-Fjy/Khw/Yms. The Tef/Tmd 75-line README **line 64 says native time is local solar time (without DST)**.

### JP-Tef actual terminal output (from earlier operator run)

```text
STAGE05AN ORIGINAL JPF JP-Tef SOURCE HH QC2 TIMESTAMP REVIEW PASS | NO CDS/UTC/SLURM/REPAIR
PACKAGE JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1 MEMBER JPF_JP-Tef_FLUXNET_FLUXMET_HH_2001-2023_v1.3_r1.csv
README_SHA256 17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5
SOURCE_HH_ROWS_SCANNED 403200
FIRST_SOURCE_TIME_SAMPLES [{'start': '200101010000', 'end': '200101010030'}, {'start': '200101010030', 'end': '200101010100'}, {'start': '200101010100', 'end': '200101010130'}]
LAST_SOURCE_TIME_SAMPLES [{'start': '202312312230', 'end': '202312312300'}, {'start': '202312312300', 'end': '202312312330'}, {'start': '202312312330', 'end': '202401010000'}]
SOURCE_ORIGINAL_QC2_FIELDS_MATCHED 4 NATIVE_SITE_HALFHOURS 4
SOURCE_EVENT_MATCH_TABLE /home/ly3n24/japanflux_stage05an/JP-Tef_20261102T214601Z/stage05an_JP_Tef_original_4or14_QC2_HH_source_match_NO_UTC.tsv
SOURCE_CLOCK_PROVENANCE_REPORT /home/ly3n24/japanflux_stage05an/JP-Tef_20261102T214601Z/stage05an_JP_Tef_original_HH_release_timestamp_READONLY.json
RETAIN_ORIGINAL_SOLAR_VS_STANDARD_CONFLICT UTC=UNRESOLVED; ALL 45 SOURCE QC2 FIELDS HOLD
```

### JP-Tmd actual terminal output (latest operator run)

```text
STAGE05AN SELF-TEST PASS | exact JPF nested ZIP original README+FLUXMET_HH timestamp and event values only, NO SOURCE WRITES/UTC/CDS/REPAIR
STAGE05AN ORIGINAL JPF JP-Tmd SOURCE HH QC2 TIMESTAMP REVIEW PASS | NO CDS/UTC/SLURM/REPAIR
PACKAGE JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1 MEMBER JPF_JP-Tmd_FLUXNET_FLUXMET_HH_2005-2023_v1.3_r1.csv
README_SHA256 17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5
SOURCE_HH_ROWS_SCANNED 333072
FIRST_SOURCE_TIME_SAMPLES [{'start': '200501010000', 'end': '200501010030'}, {'start': '200501010030', 'end': '200501010100'}, {'start': '200501010100', 'end': '200501010130'}]
LAST_SOURCE_TIME_SAMPLES [{'start': '202312312230', 'end': '202312312300'}, {'start': '202312312300', 'end': '202312312330'}, {'start': '202312312330', 'end': '202401010000'}]
SOURCE_ORIGINAL_QC2_FIELDS_MATCHED 14 NATIVE_SITE_HALFHOURS 10
TIMESTAMP_COLUMN_NAMES TIMESTAMP_START,TIMESTAMP_END,TA_F_MDS,TA_F_MDS_QC,TA_ERA
SOURCE_EVENT_MATCH_TABLE /home/ly3n24/japanflux_stage05an/JP-Tmd_20261102T215050Z/stage05an_JP_Tmd_original_4or14_QC2_HH_source_match_NO_UTC.tsv
SOURCE_CLOCK_PROVENANCE_REPORT /home/ly3n24/japanflux_stage05an/JP-Tmd_20261102T215050Z/stage05an_JP_Tmd_original_HH_release_timestamp_READONLY.json
RETAIN_ORIGINAL_SOLAR_VS_STANDARD_CONFLICT UTC=UNRESOLVED; ALL 45 SOURCE QC2 FIELDS HOLD
```

**Timebase science HOLD is NOT resolved.** The original 30-minute timestamp sequence is compatible with either a regularized site standard clock or a regularized solar clock. The original BIF `UTC_OFFSET=9` identifies station time zone but does not certify the timestamp normalization procedure.

## Stronger public external metadata, separate from original ZIP provenance

- [Original JP-Tmd same version `JPF_JP-Tmd_FLUXNET_FLUXMET_HH_2005-2023_v1.3_r1.zip` in ICOS](https://meta.icos-cp.eu/objects/bnc9Cg8Jxf1opT9_Fq8boBvS) lists 333,072 data rows matching actual source CSV, acquisition start 2004-12-31 15:00 **UTC**, which is 2005-01-01 00:00 at UTC+9, and `TIMESTAMP_END` local non-DST time. This is external *processed-product metadata* consistent with JST, not an original logger or release processing transformation log.
- [FLUXNET Data Variables](https://fluxnet.org/data/aboutdata/data-variables/) requires local standard time without DST and half-hour interval end stamps. This is normative processing guidance rather than proof for the exact original 75-line README.
- [JapanFlux2024 product methods](https://essd.copernicus.org/articles/17/3807/2025/) describe formatting site data into a FLUXNET-compatible structure after consultation with site teams, but JapanFlux2024 is a **different product** and cannot automatically settle original JPF archive clocks.

## Stage05AO scientific decision step

The [Stage05AO read-only cross-audit](../scripts/stage05/05ao_reconcile_Tef_Tmd_original_HH_timebase_vs_ICOS_READONLY.py) joins both actual original Stage05AN source HH JSONs, Stage05AM original native-only events, and Stage05AL whole 45-field science status. It verifies exact original QC2 values and 736,272 previous HH scan provenance, Gregorian start/end/date alignment, and the limited interpretation of public ICOS same-release timing. It outputs only a fresh derived source evidence TSV + science decision JSON.

Stage05AO script is **committed to GitHub, but a real IRIDIS6 run has NOT been observed**. It must **preserve** all 18 Tef/Tmd UTC=UNRESOLVED, retain prior 22 strong-context +5 context-only independent results, all 45 original source fields HOLD; no CDS, source ZIP, forcing, AD400, Slurm or 30-min repair.

After this cross-audit, the remaining requirement to authorize clock mapping is **site/release-specific primary evidence from data producers** describing whether `TIMESTAMP_START/TIMESTAMP_END` were corrected from local solar to JST before publishing JPF 1.3 r1, and how any solar correction (mean/apparent) was applied.
