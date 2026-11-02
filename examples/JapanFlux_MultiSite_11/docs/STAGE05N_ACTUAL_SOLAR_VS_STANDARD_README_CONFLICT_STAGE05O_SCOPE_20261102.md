# JapanFlux Stage05N — complete SHA-verified alternate README confirms LOCAL SOLAR TIME (2026-11-02)

## Operator actual result (NOT inferred)

The operator executed `05n_full_alternate_Tef_Tmd_README_source_SHA_readonly.py` on original **JP-Tef** nested release ZIP and posted the **entire exact 75-line README**. The operation reported `STAGE05N SELF-TEST PASS`, `STAGE05N SOURCE README BYTE VALIDATION PASS`, and identical saved original README byte SHA for JP-Tef and JP-Tmd:

- Original internal member: `README.txt`
- Source-verified SHA256: `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5`
- Original line count: **75**
- Original README **line 64**: `The data are in ASCII format, comma delimited, with first row as header. Missing data are indicated as -9999 and time is expressed in local solar time (without DST). Metadata about the measurements are reported in the VAR_INFO BIF files.`

The **identical SHA** between Tef/Tmd saved Stage05K source metadata establishes that both contain the same original README contents in the already verified releases; only JP-Tef original ZIP was reopened during Stage05N. No meteorological CSV rows, Slurm, source edits or model runs.

This **direct original evidence changes the prior Stage05L interpretation**: the 75-line README does not merely lack temporal metadata, and extraction was not a bug. It **explicitly says local solar time**, whereas the three other selected JPF station releases (JP-Fjy, JP-Khw, JP-Yms) share the 85-line README with original **line 69: local standard time (without DST)**, SHA256 `fe96facec6fafc57b126e850140152a540a16d97c3bfde8adfa090a3747598f9`.

## Source-standard inconsistency — do not silently normalize

All five selected source BIFs separately report `GRP_UTC_OFFSET,UTC_OFFSET,9` and Stage05L validated units, QC and ERA downscaling metadata. Therefore the present original-source evidence is **in tension** for Tef/Tmd:

| Evidence | JP-Fjy / JP-Khw / JP-Yms | JP-Tef / JP-Tmd |
|---|---|---|
| README wording | local **standard** time (without DST) | local **solar** time (without DST) |
| BIF `UTC_OFFSET` | +9 | +9 |
| Stage05L metadata gate | 3/3 VERIFIED | 2/2 HOLD |
| Native→UTC per-half-hour join | `native−9h` can be used for reference lookup | **BLOCKED** pending independent time-basis clarification |

Independent method literature and FLUXNET guidelines **strongly favor local STANDARD time** for processed FLUXNET/ONEFlux output, but they do not prove that the distinct 75-line JPF release did or did not transform the native tower timestamps:

- FLUXNET official data-variable/time convention: https://fluxnet.org/data/aboutdata/data-variables/ — timestamps in local standard time without DST; offset supplied by BADM.
- Pastorello et al. (2020), ONEFlux processing paper: https://www.nature.com/articles/s41597-020-0534-3 — processed time variables in local standard time, no DST, site metadata gives UTC relationship.
- ONEFlux project documentation: https://github.com/fluxnet/ONEFlux — time zone adopted for timestamps is required station metadata.
- A related **JapanFlux2024 (separately distributed, not the same JPF FLUXNET ZIP)** JP-Tef catalog covers `2000-12-31T15:00:00Z` onwards, consistent with `2001-01-01 00:00 JST` for that independently distributed product (https://cir.nii.ac.jp/crid/1820583944696778112). This is supporting context only; not an exact JPF timestamp source match.

One must distinguish **mean local solar clock**, **apparent/true solar clock**, and **civil standard clock**; possible longitude/equation-of-time differences mean **do not invent a conversion formula** from the README phrase alone. No declared scientific correction or time shift is authorized, and **do not treat the separate JapanFlux2024 dataset as the same JPF output provenance**.

## Exact impacts on ongoing source forensics

- Stage05I remains **45 candidate variable records** at **35 distinct station × native half-hour times**, all **HOLD**.
- Among them **27 field records** at **21 unique station×half-hour times** belong to the three original verified local-standard-time sites: JP-Fjy (6 field records), JP-Khw (11), JP-Yms (10).
- The remaining **18 field records** at **14 unique station×half-hour times** belong to Tef (4) and Tmd (14), whose native→UTC conversion should remain **unresolved**.
- As noted in Stage05G, all source-selected flags are source-matched `F=ERA`, raw QC2, and no forcing corrections made.

### Stage05O conservative next step

[Stage05O source-gated scoped native/UTC lookup](../scripts/stage05/05o_scoped_3site_UTC_2site_solar_README_HOLD_NO_ZIP.py) reads the already produced **Stage05L JSON result**, **Stage05N full original README terminal log**, and **Stage05I HOLD TSV**. It fails closed unless Stage05L still says 3/5, all source BIF offsets match +9, Stage05N hash confirms the two original README editions, and the 45/35 candidate keys and QC2 selection are unchanged. It emits **two derived, separate TSV files**: 27 fields with certified BIF+README local-standard UTC lookup for Fjy/Khw/Yms only, and 18 Tef/Tmd native-only time conflict HOLD fields with **UTC explicitly UNRESOLVED**. It also writes a JSON summary. It reads **NO ZIP**, makes **NO Slurm/model/forcing/source writes**, does **not** fetch independent ERA and does **not** approve science repairs. The code is committed but **has not yet been executed on IRIDIS6**.

Next scientific resolution: obtain explicit release-version source processing provenance or confirmation from producer/ONEFlux for Tef/Tmd, and/or cross-check source clock against independent radiation-time series while treating this as supporting evidence rather than proof. Retain Stage05L 3/5 until resolved.

JP-Tom/Tgf non-JPF original humidity/VPD checks remain separate and pending. No AD400/Normal400 approved.
