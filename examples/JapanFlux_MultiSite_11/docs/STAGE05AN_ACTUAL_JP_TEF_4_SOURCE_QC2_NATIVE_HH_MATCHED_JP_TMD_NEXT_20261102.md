# JapanFlux Stage05AN — ACTUAL JP-Tef original JPF HH source timestamp/QC2 verification PASS (2026-11-02)

## Observed IRIDIS6 output — actual original source, not a new timebase conclusion

The operator executed the SHA-pinned [Stage05AN](../scripts/stage05/05an_original_Tef_Tmd_FLUXMET_HH_timestamp_product_vs_README_READONLY.py) read-only on the original nested JPF FLUXNET release **JP-Tef**. This source audit opened the exact source nested ZIP, verified the 75-line original README by SHA256 and scanned the native-time source **FLUXMET_HH** CSV for the original Stage05AM four QC2 source variables/events.

```text
STAGE05AN SELF-TEST PASS | exact JPF nested ZIP original README+FLUXMET_HH timestamp and event values only, NO SOURCE WRITES/UTC/CDS/REPAIR
STAGE05AN ORIGINAL JPF JP-Tef SOURCE HH QC2 TIMESTAMP REVIEW PASS | NO CDS/UTC/SLURM/REPAIR
PACKAGE JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1 MEMBER JPF_JP-Tef_FLUXNET_FLUXMET_HH_2001-2023_v1.3_r1.csv
README_SHA256 17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5
SOURCE_HH_ROWS_SCANNED 403200
FIRST_SOURCE_TIME_SAMPLES [{'start': '200101010000', 'end': '200101010030'}, {'start': '200101010030', 'end': '200101010100'}, {'start': '200101010100', 'end': '200101010130'}]
LAST_SOURCE_TIME_SAMPLES [{'start': '202312312230', 'end': '202312312300'}, {'start': '202312312300', 'end': '202312312330'}, {'start': '202312312330', 'end': '202401010000'}]
SOURCE_ORIGINAL_QC2_FIELDS_MATCHED 4 NATIVE_SITE_HALFHOURS 4
TIMESTAMP_COLUMN_NAMES TIMESTAMP_START,TIMESTAMP_END,TA_F_MDS,TA_F_MDS_QC,TA_ERA
SOURCE_EVENT_MATCH_TABLE /home/ly3n24/japanflux_stage05an/JP-Tef_20261102T214601Z/stage05an_JP_Tef_original_4or14_QC2_HH_source_match_NO_UTC.tsv
SOURCE_CLOCK_PROVENANCE_REPORT /home/ly3n24/japanflux_stage05an/JP-Tef_20261102T214601Z/stage05an_JP_Tef_original_HH_release_timestamp_READONLY.json
RETAIN_ORIGINAL_SOLAR_VS_STANDARD_CONFLICT UTC=UNRESOLVED; ALL 45 SOURCE QC2 FIELDS HOLD
```

The audit confirms **all four original JP-Tef LW_IN QC2 variable fields** are actually present in the original source half-hour CSV and their original selected `LW_IN_F`, same-release `LW_IN_ERA`, raw `LW_IN_F_QC=2`, and native start/end timestamps match Stage05AM exactly. Stage05AM placed the four source fields at original **2011-12-17 (two)** and **2022-04-09 (two)** native dates; these must not be labelled UTC.

**Important limitation:** the HH CSV has explicit consistent 30-minute `TIMESTAMP_START`/`TIMESTAMP_END` intervals; this by itself does **not** determine whether the source's wall clock is local solar or Japanese local standard time. The original *different-release* 75-line README (line 64) explicitly says `local solar time (without DST)`; the BIF `UTC_OFFSET=9` is station metadata, not a source-specific proven timestamp transform. Therefore the JP-Tef UTC reference lookup is still **UNRESOLVED/HOLD**. All 45 original QC2 variable fields remain HOLD with no scientifically authorized 30-minute replacements.

## Exact next operation

Use the **same unchanged GitHub-pinned Stage05AN script**, original 11-site `sites.tsv` and real Stage05AM 18-field native-only register/summary, but run **`--site JP-Tmd`** in a fresh output directory. This should read original `JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1` nested package, independently revalidate original 75-line README SHA and compare **14 QC2 fields** (2005-08-12 8 fields LW_IN2/PA3/TA3, 2011-12-17 PA3, 2022-04-09 PA3). Do **not** infer UTC, download CDS, modify forcing, or submit Slurm.

After both site original source-CSV checks pass, next scientifically valid milestone is the specific original release/data-producer `TIMESTAMP_START/TIMESTAMP_END` timebase processing provenance, distinct from generic FLUXNET/ICOS timezone conventions. No PFT work is required as part of this QC2 timebase review; user reports JapanFlux PFT is already updated.
