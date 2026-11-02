# JapanFlux Stage05AM actual Tef/Tmd 18 native time-source conflict records — Stage05AN next exact original HH source timestamp audit (2026-11-02)

## Actual operator-run Stage05AM source native-only science audit

```text
STAGE05AM SELF-TEST PASS | Tef4/Tmd14 local-solar README versus BIF UTC_OFFSET=9 science conflict, 27/45 completed, no UTC/CDS/REPAIR/WRITES
STAGE05AM ORIGINAL TEF/TMD 18 NATIVE-SOURCE CLOCK CONFLICT REVIEW PASS | NO UTC/CDS/SLURM/REPAIR
ORIGINAL_QC2_FIELDS 45 INDEPENDENTLY_COMPARED 27 STRONG_LABEL 22 NEW_CONTEXT_ONLY 5
CLOCK_HOLD_FIELDS 18 BY_SITE {'JP-Tef': 4, 'JP-Tmd': 14} DISTINCT_NATIVE_SITE_HALFHOURS 14
NATIVE_SOURCE_DATE_NOT_UTC JP-Tef 2011-12-17 FIELDS 2 VARS {'LW_IN': 2}
NATIVE_SOURCE_DATE_NOT_UTC JP-Tef 2022-04-09 FIELDS 2 VARS {'LW_IN': 2}
NATIVE_SOURCE_DATE_NOT_UTC JP-Tmd 2005-08-12 FIELDS 8 VARS {'LW_IN': 2, 'PA': 3, 'TA': 3}
NATIVE_SOURCE_DATE_NOT_UTC JP-Tmd 2011-12-17 FIELDS 3 VARS {'PA': 3}
NATIVE_SOURCE_DATE_NOT_UTC JP-Tmd 2022-04-09 FIELDS 3 VARS {'PA': 3}
SOURCE_NATIVE_EVENT_REGISTER /home/ly3n24/japanflux_stage05am/run_20261102T201525Z/stage05am_18_original_Tef_Tmd_native_QC2_local_solar_timebase_CONFLICT_HOLD.tsv
NATIVE_DAY_SUMMARY /home/ly3n24/japanflux_stage05am/run_20261102T201525Z/stage05am_original_native_site_days_VARIABLE_COUNTS_READONLY.tsv
TIMEBASE_DECISION_HOLD /home/ly3n24/japanflux_stage05am/run_20261102T201525Z/stage05am_45_source_fields_27_context_18_clock_review.json
NO Tef/Tmd UTC MAPPING OR CDS REQUEST AUTHORIZED; ALL 45 QC2 SOURCE FIELDS HOLD
```

The user independently confirmed JapanFlux PFT configurations have been completed/updated in GitHub. **No more PFT audits are required for this particular meteorological QC2 source time investigation**. PFT status itself is independent of the forcing data QC/HOLD, not authorization to run AD400.

The actual evidence population is still 45 original source-selected F=ERA QC2 variable records across 35 station×native-halfhours. **27** standard-time BIF+README-verified flagged variables (Fjy6/Khw11/Yms10) have independent physical context at 21 unique original station×native halfhours (22 prior strong-class + five Yms context-only). **18** native-only flagged variables at 14 unique source site×native-halfhours remain Tef4/Tmd14.

## Further direct institutional metadata — Tmd original exact release version

ICOS [Tomakomai Flux Research Site Disturbed FLUXNET product](https://meta.icos-cp.eu/objects/bnc9Cg8Jxf1opT9_Fq8boBvS) displays original FLUXMET file name `JPF_JP-Tmd_FLUXNET_FLUXMET_HH_2005-2023_v1.3_r1.zip`, corresponding to the same site, years and release tag as the original `JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1` source package. This ICOS catalog lists: `TIMESTAMP` as time instant **UTC**, `TIMESTAMP_END` as time instant **local non-DST time**, an acquisition start **2004-12-31 15:00 UTC**, and a FLUXNET/ONEFlux processing description. ICOS independently lists [JP-Tef station UTC_OFFSET=9](https://meta.icos-cp.eu/resources/stations/ES_JP-Tef), with Tef source product 2001–2023. The [FLUXNET convention](https://fluxnet.org/data/aboutdata/data-variables/) is local standard time without DST and half-hour interval-end timestamps.

These are **strong reasons to investigate the actual source product's timestamp columns**, not permission to declare original Tef/Tmd UTC. The exact SHA-validated original JPF Tef/Tmd nested ZIPs share a **75-line README** SHA256 `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5`; original line 64 explicitly says *local solar time (without DST)*. Other JPF releases have a different, 85-line README explicitly saying local standard time. The original BIF `UTC_OFFSET=9` is station timezone metadata and does **not** prove that local-solar text was normalized to JST in the original published CSV. The ICOS web description is not an original logger-time transformation ledger.

## Next original-source-only Stage05AN

[Stage05AN original double-archive `FLUXMET_HH` timestamp and exact 18 source QC2 values check](../scripts/stage05/05an_original_Tef_Tmd_FLUXMET_HH_timestamp_product_vs_README_READONLY.py) is **committed, but first real IRIDIS execution pending**.

Inputs:
- Existing source 11-site site/package manifest `sites.tsv`; exactly JPF `JP-Tef` package `2001-2023_v1.3_r1` or JPF `JP-Tmd` package `2005-2023_v1.3_r1`.
- Original nested JPF package `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/{site}/forcing/packages/{package}.zip`, containing the original `{package}.zip`. Script reads **one site/run**, memory-bound to 320 MiB, does not extract original package to disk.
- Actual Stage05AM 18 native-time source-QC2 variable records and 45-field source timebase-HOLD summary.
- Original source README verified by SHA/line 64, exact HH CSV metadata, `TIMESTAMP_START/TIMESTAMP_END` pairs, original HH beginning/end year boundary sample, and exact QA-flagged original variable records `PA_F/PA_ERA/PA_F_QC`, `TA_F/TA_ERA/TA_F_QC`, `LW_IN_F/LW_IN_ERA/LW_IN_F_QC`, as applicable.

Expected only a read-only descriptive timestamp/provenance report under a fresh derived output folder. If source timestamp or field-name assumptions fail, report and stop without changing source data. **DO NOT** equate an apparently aligned `TIMESTAMP_START` with a proof of JST rather than local solar time. No CDS request, automatic field replacement, original source write, model submission, Slurm or AD400; all 45 original source records remain HOLD.

After Stage05AN, next source-clock evidence may include site author / data producer release-specific processing notes or raw logger UTC offset specification; a statistical SW_IN vs clear-sky astronomy shift check can be adjunct evidence only, not override the original 75-line source README alone.
