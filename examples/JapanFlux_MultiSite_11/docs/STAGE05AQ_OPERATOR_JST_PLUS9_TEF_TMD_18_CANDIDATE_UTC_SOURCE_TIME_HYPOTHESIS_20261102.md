# JapanFlux Stage05AQ — operator selects JST (UTC+9) diagnostic hypothesis for remaining Tef/Tmd 18 source fields (2026-11-02)

## Decision and rationale (user-authorized assumption, not source documentation)

Operator explicitly stated that the original JPF FLUXNET sites are the same distributed product family and their original BIF timezone fields are all **UTC_OFFSET=9**; based on the previously verified JP-Fjy/Khw/Yms sources and ICOS JP-Tmd product metadata, the user selected **JST UTC+9** as the working interpretation for source-timestamp scientific diagnostics at JP-Tef/Tmd.

This authorizes a **new derived candidate UTC mapping and source-bounded independent ERA5-Land comparison plan**. It does **not** establish that the original JP-Tef/Tmd native data are definitively JST: the original SHA-verified 75-line JP-Tef/Tmd README still states **`local solar time (without DST)`** (SHA256 `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5`, line 64). The five sites belong to the same project family but have at least two distinct README editions (75-line solar vs 85-line standard); that is an unresolved material source conflict. Keep source timestamps unchanged and mark derived UTC explicitly as **operator JST+9 hypothesis**, not source-verified UTC.

Stage05AN and Stage05AO ACTUAL on IRIDIS:
- JP-Tef original 403,200 half-hour rows, 4/4 selected F=embedded-ERA/QC2 LW_IN original fields matched.
- JP-Tmd original 333,072 half-hour rows, 14/14 PA/TA/LW_IN original fields matched.
- 736,272 source HH rows, 18/18 original QC2 variable fields at 14 source-native halfhour timestamps; original source timebase still not independently established.
- Stage05AL previous 27 source QC2 fields at Fjy6/Khw11/Yms10 independently contextualized outside ERA5L hourly physical envelopes; previous 22 strong-class, latest five context-only. Nine reference site-days already source-verified for those three sites only.
- All **45** original source fields retain science HOLD; no 30-minute forcing replacement or AD400/Slurm approval.

## Stage05AQ source-only preview script

[Stage05AQ JST+9 operator-hypothesis exact original 18 QC2 fields to candidate UTC and independent CDS day-variable-hour PREVIEW ONLY](../scripts/stage05/05aq_Tef_Tmd_operator_JST_plus9_18_QC2_CANDIDATE_UTC_ERA5L_PLAN_NO_DOWNLOAD.py) is **committed but actual IRIDIS6 self-test/full run not yet observed**.

Inputs:
- Stage05AM exact actual original 18 source-native QC2 field TSV `/home/ly3n24/japanflux_stage05am/run_20261102T201525Z/stage05am_18_original_Tef_Tmd_native_QC2_local_solar_timebase_CONFLICT_HOLD.tsv`.
- Stage05AM science summary `stage05am_45_source_fields_27_context_18_clock_review.json`.
- Stage05AO actual full original 18 field clock cross-audit report `/home/ly3n24/japanflux_stage05ao/run_20261102T215834Z/stage05ao_45_source_field_clock_provenance_science_HOLD.json`.
- Stage05L original five BIF/source-clock gate report `/home/ly3n24/japanflux_stage05l/run_20261102T010150Z/stage05l_source_metadata_validation.json`.

**Required explicit flag:** `--operator-time-hypothesis JST_UTC_PLUS9_DIAGNOSTIC_ONLY`.

For each original Tef/Tmd QC2 source record, preserve original `native_halfhour_timestamp_NOT_UTC`, original selected F, embedded ERA, raw QC2, source units, original solar README evidence; append **`candidate_UTC_start = native_start - 9 hours`** and +30-minute end. Example **arithmetic only**: original native `200508120300` → candidate UTC `200508111800`; source native `201112170600` → candidate UTC `201112162100`. These examples do not replace exact source-row processing.

Group newly derived source-event reference hours by **actual resultant UTC day**, and exact variable: PA → `surface_pressure`, TA → `2m_temperature`, LW_IN → `surface_thermal_radiation_downwards`. Include conservative -3h to +4h hourly context around the candidate 30-min source time; this may produce additional neighbouring UTC dates as required by the original events. The resulting site×day/variable manifest is **not submitted**, uses no inferred tower coordinates, and does not certify the source timebase. No CDS/ZIP/source/forcing/model/Slurm/AD400 modifications, and all 45 source field QC2 science holds preserved.

Next after successful real Stage05AQ result: validate source-original JP-Tef/Tmd BIF tower lat/lon and altitude and source BIF SHA; build a **single-day, no-overwrite, explicit operator-request** Stage05AR ERA5-Land CSV source retrieval workflow, reusing existing CDS credentials/licence while keeping `JST_UTC_PLUS9_DIAGNOSTIC_ONLY` in every evidence record. Then independently compare original flagged selected F/QC2 pressure, TA, LW to hourly reference (for `strd` deaccumulated J m-2 /3600, no second difference), without pointwise half-hour replacements. If any physical evidence contradicts timing assumptions, report separately rather than silently changing original timebase. No automatic source approval.
