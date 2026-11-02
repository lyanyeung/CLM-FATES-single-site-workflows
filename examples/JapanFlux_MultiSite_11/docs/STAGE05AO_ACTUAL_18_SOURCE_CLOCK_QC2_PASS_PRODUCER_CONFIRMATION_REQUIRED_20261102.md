# JapanFlux Stage05AO — actual both source releases 18/18 QC2 provenance PASS, timebase NOT RESOLVED (2026-11-02)

## Real operator-executed result

Stage05AO actual pinned script successful on IRIDIS6. Inputs were the exact Stage05AN original JP-Tef and JP-Tmd nested JPF source HH metadata, Stage05AM 18 native-only original field records, and Stage05AL 45-field coverage and HOLD ledger.

```text
STAGE05AO SELF-TEST PASS | 403200+333072 original source HH Gregorian boundaries, 18 matched QC2 native-time records; NO UTC/CDS/REPAIR
STAGE05AO TEF/TMD ORIGINAL JPF SOURCE CLOCK PROVENANCE CROSS-REVIEW PASS | NO UTC/CDS/SLURM/REPAIR
SOURCE_HH_ROWS_PREVIOUSLY_VERIFIED 736272 ORIGINAL_QC2_FIELDS_EXACT 18
INDEPENDENT_CONTEXT 27 CLOCK_CONFLICT_HOLD 18
ICOS_PRODUCT_PLUS9_CONTEXT_NOT_NATIVE_CLOCK_PROOF
18_FIELD_NATIVE_ONLY_REPORT /home/ly3n24/japanflux_stage05ao/run_20261102T215834Z/stage05ao_18_Tef_Tmd_original_native_QC2_source_clock_UNRESOLVED.tsv
TIME_SOURCE_SCIENCE_HOLD_REPORT /home/ly3n24/japanflux_stage05ao/run_20261102T215834Z/stage05ao_45_source_field_clock_provenance_science_HOLD.json
REQUIRE_PRODUCER_TIME_CONVERSION_DOCUMENTATION; ALL_45_FIELDS_HOLD
```

**Established real evidence:**

- Original JP-Tef `JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1`: 403,200 source half-hour rows, all **4/4** selected original QC2 source variable fields matched, four distinct site-native halfhours.
- Original JP-Tmd `JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1`: 333,072 source half-hour rows, all **14/14** selected original QC2 source variable fields matched, 10 distinct site-native halfhours.
- Original two releases share 75-line README `README.txt` SHA256 `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5`, line 64: `time is expressed in local solar time (without DST)`. Original BIF separately declares `UTC_OFFSET=9`. **No source-specific record has proven that the raw original JPF packaged `TIMESTAMP_START` / `TIMESTAMP_END` are JST or were converted from mean/apparent local solar time**.
- Both source original half-hour sequences begin at nominal local wallclock `YYYY-01-01 00:00` and end next January `00:00`; complete regularized halfhour counts and source QC2 event matching do **not** distinguish solar-vs-JST wallclock conventions.
- Official FLUXNET/ONEFlux processing specification uses local standard time without DST (see [FLUXNET](https://fluxnet.org/data/aboutdata/data-variables/) and [Pastorello et al. 2020](https://doi.org/10.1038/s41597-020-0534-3)), but is not evidence of a particular original site's logger-to-release conversion.
- [ICOS exact JP-Tmd FLUXMET_HH 2005–2023 v1.3_r1](https://meta.icos-cp.eu/objects/bnc9Cg8Jxf1opT9_Fq8boBvS): **333,072 rows**, acquisition start **2004-12-31 15:00 UTC** and `TIMESTAMP_END` tagged local non-DST; publication authors **Takashi Hirano and Ryuichi Hirata**. The initial UTC timestamp matches `2005-01-01 00:00` at UTC+9. This is compelling **catalogue evidence for a processed-product JST representation**, but it does not independently prove the original input-to-output transformation; original source README conflicts. Never silently overwrite the explicit README claim.
- [JapanFlux2024 original methods](https://essd.copernicus.org/articles/17/3807/2025/) state data reformatting after site-team consultation, but that is **a different dataset from the exact JPF v1.3_r1 package**. Corresponding author [Masahito Ueyama](https://essd.copernicus.org/articles/17/3807/2025/) is a possible route to the appropriate original site/data producer, **not automatically the original JPF pipeline maintainer**.

## Current science classification

| Field class | Count | Status |
|---|---:|---|
| JP-Fjy6, JP-Khw11, JP-Yms5 | 22 | Independent hourly comparisons outside context; prior STRONG_CONTEXT evidence class; SOURCE QC2 flags HOLD |
| JP-Yms 2011 Dec LW_IN2 + PA3 | 5 | Independent hourly comparison outside context, explicit CONTEXT_ONLY; not auto-promoted to STRONG; SOURCE QC2 flags HOLD |
| JP-Tef LW_IN4, JP-Tmd LW_IN2+PA9+TA3 | 18 | Original source selected F=ERA QC2 physically suspect, but UTC=UNRESOLVED; no source-proven independent ERA5-Land hourly event comparison; SOURCE QC2 flags HOLD |
| TOTAL | 45 | All original field candidates HOLD; no actual forcing/AD400 edits |

The **9/9 validated ERA5-Land reference site×UTC days** apply only to the three JST-proven sites Fjy/Khw/Yms; they are not evidence that Tef/Tmd original clocks were resolved.

## Next non-redundant action: targeted original release timestamp inquiry

Seek primary provenance evidence for the exact archive revisions, preferably from **ICOS Ecosystem Thematic Centre** (product publisher) and/or site PI/data processor. Contact reference: https://meta.icos-cp.eu/objects/bnc9Cg8Jxf1opT9_Fq8boBvS ; general listed contact **info@icos-ri.eu**, requesting routing to the original 2023 JPF/ONEFlux product submission processor. Ask explicitly:

1. For `JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1` and `JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1`, are distributed `FLUXMET_HH` `TIMESTAMP_START` and `TIMESTAMP_END` **JST (UTC+9, no DST)**, **mean local solar time**, or **apparent local solar time**?
2. Does the **75-line original README** saying `local solar time (without DST)` describe the distributed `v1.3_r1` timestamps, or is it outdated/inherited prose? Provide confirmation based on the exact release, not only a generic FLUXNET specification.
3. If the site logger records were in solar time, did the **source processing pipeline convert them to JST** for `v1.3_r1`? Which calculation, reference meridian/equation-of-time, time interval START/END convention, and any rounding was applied? Request any processing log / version note / BADM/site PI confirmation.
4. If released as JST, may the source events safely be mapped by `UTC=TIMESTAMP_START -9h`? If released as solar time, what deterministic source-proven conversion applies?
5. Does the ICOS product's `2004-12-31 15:00 UTC` acquisition start represent a true timestamp conversion from original JPF site data, or only an **automatic catalog inference using BADM UTC_OFFSET=9**?

**Do not submit more ERA5-Land CDS requests for Tef/Tmd based on an unsupported UTC mapping.** Optional numerical solar-radiation daytime checks would be hypothesis-only and cannot substitute for producer confirmation. Source PFT configuration work was already updated per operator and is outside this issue.

Until such primary evidence arrives, maintain **27 context-reviewed / 18 source-clock HOLD, all 45 source field scientific HOLD; no source ZIP/forcing/model/Slurm/AD400 modification**.
